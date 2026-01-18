"""
Bug Scanner - Scan Git History for Bug-Related Commits
=======================================================

Port of Ralph CLI bug-scanner.js to Python.

Features:
- Scans git history for bug-related keywords: fix, bug, issue, hotfix, patch
- Extracts commit data: message, author, date, files changed, diff
- Identifies related PRs/issues via commit message references (#123, PRD-45)
- Stores raw bug data in .auto-claude/bug-wikipedia/raw/bug-{sha}.json
- Links to original commit: git SHA, GitHub URL
- Supports both "auto-claude" and "project" scan modes
"""

import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from .models import BugData

# Configuration Constants
BUG_KEYWORDS = ["fix", "bug", "issue", "hotfix", "patch"]
ISSUE_PATTERN = re.compile(r"#(\d+)|([A-Z]+-\d+)", re.IGNORECASE)
DEFAULT_DIFF_LIMIT = 2000  # Characters


# =============================================================================
# GIT OPERATIONS
# =============================================================================


def scan_git_history(
    project_dir: Path,
    scan_mode: Literal["auto-claude", "project"] = "project",
) -> list[dict]:
    """
    Scan git history for bug-related commits.

    Args:
        project_dir: Project directory to scan
        scan_mode: "auto-claude" scans Auto-Claude repo, "project" scans user project

    Returns:
        List of commit dictionaries with bug-related information
    """
    try:
        # Run git log to get all commits
        output = subprocess.run(
            [
                "git",
                "log",
                "--format=%H%n%an%n%ae%n%ai%n%s%n%b%n---END---",
                "--all",
            ],
            cwd=project_dir,
            capture_output=True,
            text=True,
            check=True,
        ).stdout

        all_commits = _parse_git_log_output(output)

        # Filter for bug-related keywords
        bug_commits = []
        for commit in all_commits:
            text = (commit["message"] + " " + commit["body"]).lower()
            if any(keyword in text for keyword in BUG_KEYWORDS):
                bug_commits.append(commit)

        return bug_commits

    except subprocess.CalledProcessError as e:
        print(f"⚠️  Git log search failed: {e}")
        return []


def _parse_git_log_output(output: str) -> list[dict]:
    """
    Parse git log output into commit objects.

    Args:
        output: Raw git log output

    Returns:
        List of parsed commit dictionaries
    """
    commits = []
    commit_blocks = [block.strip() for block in output.split("---END---") if block.strip()]

    for block in commit_blocks:
        lines = block.split("\n")
        if len(lines) < 4:
            continue

        commit = {
            "sha": lines[0].strip(),
            "author_name": lines[1].strip(),
            "author_email": lines[2].strip(),
            "date": lines[3].strip(),
            "message": lines[4].strip() if len(lines) > 4 else "",
            "body": "\n".join(lines[5:]).strip() if len(lines) > 5 else "",
        }

        if commit["sha"]:
            commits.append(commit)

    return commits


def get_files_changed(sha: str, project_dir: Path) -> list[str]:
    """
    Extract files changed in a commit.

    Args:
        sha: Commit SHA
        project_dir: Project directory

    Returns:
        List of file paths
    """
    try:
        output = subprocess.run(
            ["git", "show", "--name-only", "--format=", sha],
            cwd=project_dir,
            capture_output=True,
            text=True,
            check=True,
        ).stdout

        return [line.strip() for line in output.split("\n") if line.strip()]

    except subprocess.CalledProcessError:
        return []


def get_diff(sha: str, project_dir: Path, limit: int = DEFAULT_DIFF_LIMIT) -> str:
    """
    Extract diff for a commit.

    Args:
        sha: Commit SHA
        project_dir: Project directory
        limit: Maximum characters to return

    Returns:
        Diff output (limited to specified chars)
    """
    try:
        output = subprocess.run(
            ["git", "show", "--no-patch", "--format=", "--unified=1", sha],
            cwd=project_dir,
            capture_output=True,
            text=True,
            check=True,
        ).stdout

        # Limit diff to keep JSON files manageable
        return output[:limit]

    except subprocess.CalledProcessError:
        return ""


def extract_related_issues(message: str, body: str) -> list[str]:
    """
    Extract related issue references from commit message/body.

    Args:
        message: Commit message
        body: Commit body

    Returns:
        List of issue references (e.g., ["#123", "PRD-45"])
    """
    full_text = f"{message}\n{body}"
    issues = set()

    for match in ISSUE_PATTERN.finditer(full_text):
        if match.group(1):  # #123 format
            issues.add(f"#{match.group(1)}")
        elif match.group(2):  # PRD-45 format
            issues.add(match.group(2))

    return sorted(issues)


def get_github_repo_info(project_dir: Path) -> dict | None:
    """
    Get GitHub repository info from git remote.

    Args:
        project_dir: Project directory

    Returns:
        Dictionary with owner, repo, baseUrl or None if not a GitHub repo
    """
    try:
        remote_url = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

        # Parse GitHub URLs
        # HTTPS: https://github.com/owner/repo.git
        # SSH: git@github.com:owner/repo.git
        https_match = re.match(r"https://([^/]+)/([^/]+)/(.+?)(?:\.git)?$", remote_url)
        ssh_match = re.match(r"git@([^:]+):([^/]+)/(.+?)(?:\.git)?$", remote_url)

        if https_match:
            host, owner, repo = https_match.groups()
        elif ssh_match:
            host, owner, repo = ssh_match.groups()
        else:
            return None

        return {
            "owner": owner,
            "repo": repo,
            "baseUrl": f"https://{host}",
        }

    except subprocess.CalledProcessError:
        return None


def get_github_commit_url(sha: str, project_dir: Path) -> str | None:
    """
    Generate GitHub commit URL.

    Args:
        sha: Commit SHA
        project_dir: Project directory

    Returns:
        GitHub commit URL or None
    """
    repo_info = get_github_repo_info(project_dir)
    if not repo_info:
        return None

    return f"{repo_info['baseUrl']}/{repo_info['owner']}/{repo_info['repo']}/commit/{sha}"


# =============================================================================
# BUG DATA CREATION
# =============================================================================


def create_bug_id(sha: str) -> str:
    """
    Create short ID from SHA (first 8 characters).

    Args:
        sha: Full commit SHA

    Returns:
        Short bug ID (e.g., "bug-abc123de")
    """
    return f"bug-{sha[:8]}"


def create_bug_data(commit: dict, project_dir: Path) -> BugData:
    """
    Create BugData object from commit.

    Args:
        commit: Commit dictionary from git log
        project_dir: Project directory

    Returns:
        BugData instance
    """
    files_changed = get_files_changed(commit["sha"], project_dir)
    diff = get_diff(commit["sha"], project_dir)
    related_issues = extract_related_issues(commit["message"], commit["body"])
    github_url = get_github_commit_url(commit["sha"], project_dir)

    # Extract error message from body if available
    error_message = ""
    if "Error:" in commit["body"]:
        error_match = re.search(r"Error:\s*(.+?)(?:\n|$)", commit["body"], re.IGNORECASE)
        if error_match:
            error_message = error_match.group(1).strip()

    bug_id = create_bug_id(commit["sha"])

    # Parse date
    try:
        date_fixed = datetime.fromisoformat(commit["date"].replace(" ", "T"))
    except (ValueError, AttributeError):
        date_fixed = datetime.now(timezone.utc)

    return BugData(
        id=bug_id,
        commit_sha=commit["sha"],
        commit_message=commit["message"],
        author_name=commit["author_name"],
        author_email=commit["author_email"],
        date_fixed=date_fixed,
        files_changed=files_changed,
        diff=diff,
        related_issues=related_issues,
        github_url=github_url,
        error_message=error_message,
        scanned_at=datetime.now(timezone.utc),
    )


# =============================================================================
# PROCESSED COMMITS TRACKING
# =============================================================================


def get_processed_commits(bug_wikipedia_dir: Path) -> set[str]:
    """
    Get list of already processed commits.

    Args:
        bug_wikipedia_dir: Bug Wikipedia directory

    Returns:
        Set of commit SHAs already processed
    """
    processed_file = bug_wikipedia_dir / ".processed-commits"

    if not processed_file.exists():
        return set()

    try:
        content = processed_file.read_text().strip()
        if not content:
            return set()
        return set(line.strip() for line in content.split("\n") if line.strip())
    except OSError:
        return set()


def mark_commit_as_processed(sha: str, bug_wikipedia_dir: Path) -> None:
    """
    Save processed commit SHA.

    Args:
        sha: Commit SHA to mark as processed
        bug_wikipedia_dir: Bug Wikipedia directory
    """
    processed_file = bug_wikipedia_dir / ".processed-commits"
    bug_wikipedia_dir.mkdir(parents=True, exist_ok=True)

    try:
        with open(processed_file, "a") as f:
            f.write(sha + "\n")
    except OSError as e:
        print(f"❌ Failed to mark commit as processed: {e}")


# =============================================================================
# DIRECTORY MANAGEMENT
# =============================================================================


def create_bug_wikipedia_directories(bug_wikipedia_dir: Path) -> None:
    """
    Create bug Wikipedia directory structure.

    Args:
        bug_wikipedia_dir: Base bug Wikipedia directory
    """
    subdirs = [
        bug_wikipedia_dir / "raw",
        bug_wikipedia_dir / "categorized",
        bug_wikipedia_dir / "categories",
        bug_wikipedia_dir / "by-developer",
        bug_wikipedia_dir / "by-module",
        bug_wikipedia_dir / "patterns",
        bug_wikipedia_dir / "metrics",
        bug_wikipedia_dir / "deep-dive",
    ]

    for subdir in subdirs:
        subdir.mkdir(parents=True, exist_ok=True)


# =============================================================================
# MAIN SCAN FUNCTION
# =============================================================================


def scan_bugs(
    project_dir: Path,
    bug_wikipedia_dir: Path,
    scan_mode: Literal["auto-claude", "project"] = "project",
) -> tuple[int, int]:
    """
    Scan git history for bugs and save to bug-wikipedia directory.

    Args:
        project_dir: Project directory to scan
        bug_wikipedia_dir: Output directory for bug data
        scan_mode: "auto-claude" or "project"

    Returns:
        Tuple of (total_bugs_found, new_bugs_processed)
    """
    print("ℹ️  Starting bug scanner...")

    # Create directory structure
    create_bug_wikipedia_directories(bug_wikipedia_dir)

    # Get processed commits
    processed_commits = get_processed_commits(bug_wikipedia_dir)
    print(f"ℹ️  Previously processed: {len(processed_commits)} commits")

    # Scan git history
    commits = scan_git_history(project_dir, scan_mode)
    print(f"✅ Found {len(commits)} bug-related commits")

    if not commits:
        return 0, 0

    # Process new commits
    raw_dir = bug_wikipedia_dir / "raw"
    new_bugs_count = 0

    for commit in commits:
        if commit["sha"] in processed_commits:
            continue

        # Create and save bug data
        bug_data = create_bug_data(commit, project_dir)
        bug_data.save(raw_dir)
        mark_commit_as_processed(commit["sha"], bug_wikipedia_dir)
        new_bugs_count += 1

    print(f"✅ Processed {new_bugs_count} new bugs")
    return len(commits), new_bugs_count
