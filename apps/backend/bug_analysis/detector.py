"""
Bug Pattern Detector
====================

Detects recurring bug patterns and triggers deep dive analysis.

Ported from Ralph CLI: scripts/bug-pattern-detector.js

Features:
- Detects patterns: 3+ bugs in same category + module within 30 days
- Auto-creates GitHub issue when pattern detected
- Title: "[Bug Pattern] {category} in {module}"
- Labels: "bug-pattern", "needs-analysis", "deep-dive"
- Body includes: pattern summary, similar bugs, recommended actions, timeline
- Tracks pattern resolution: auto-close when pattern stops (no new bugs in 60 days)

Configuration:
- pattern_threshold: Minimum bugs to trigger pattern (default: 3)
- pattern_window_days: Time window for recent bugs (default: 30)
- pattern_resolution_days: Days without new bugs before auto-closing (default: 60)
- auto_create_issues: Whether to create GitHub issues (default: True)

Usage:
    from bug_analysis.detector import detect_bug_patterns

    patterns = detect_bug_patterns(
        bug_wikipedia_dir=Path(".ralph/bug-wikipedia"),
        config={
            "pattern_threshold": 3,
            "pattern_window_days": 30,
            "pattern_resolution_days": 60,
            "auto_create_issues": True,
        }
    )
"""

import json
import logging
import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import requests

from .models import BugCategory, BugPattern, CategorizedBug


# Configure logging
logger = logging.getLogger(__name__)

# GitHub issue labels
GITHUB_ISSUE_LABELS = ["bug-pattern", "needs-analysis", "deep-dive"]


@dataclass
class TrackedPattern:
    """Tracked pattern for persistence"""

    key: str
    category: str
    module: str
    bug_count: int
    first_detected: datetime
    github_issue_number: int | None = None
    github_issue_url: str | None = None
    factory_run: str | None = None
    status: str = "open"  # "open", "closed"
    resolved_at: datetime | None = None
    resolution_note: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "key": self.key,
            "category": self.category,
            "module": self.module,
            "bug_count": self.bug_count,
            "first_detected": self.first_detected.isoformat(),
            "github_issue_number": self.github_issue_number,
            "github_issue_url": self.github_issue_url,
            "factory_run": self.factory_run,
            "status": self.status,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_note": self.resolution_note,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TrackedPattern":
        """Create TrackedPattern from dictionary"""
        first_detected = data.get("first_detected")
        if isinstance(first_detected, str):
            first_detected = datetime.fromisoformat(first_detected)

        resolved_at = data.get("resolved_at")
        if isinstance(resolved_at, str):
            resolved_at = datetime.fromisoformat(resolved_at)

        return cls(
            key=data.get("key", ""),
            category=data.get("category", ""),
            module=data.get("module", ""),
            bug_count=data.get("bug_count", 0),
            first_detected=first_detected or datetime.now(),
            github_issue_number=data.get("github_issue_number"),
            github_issue_url=data.get("github_issue_url"),
            factory_run=data.get("factory_run"),
            status=data.get("status", "open"),
            resolved_at=resolved_at,
            resolution_note=data.get("resolution_note"),
        )


def extract_module_from_files(files: list[str]) -> str:
    """
    Extract primary module name from file paths.

    Returns first 2 directory levels (e.g., "src/auth" from "src/auth/login.py").
    If no directories, returns "root".
    """
    if not files:
        return "unknown"

    # Use first file to determine module
    file_path = files[0]
    parts = file_path.split("/")

    if len(parts) <= 1:
        return "root"

    return "/".join(parts[:2])


def _is_within_window(bug_date: datetime, window_days: int) -> bool:
    """Check if a bug is within the pattern window (last N days)"""
    now = datetime.now()
    diff = now - bug_date
    return diff.days <= window_days


def _format_date(dt: datetime) -> str:
    """Format datetime as YYYY-MM-DD"""
    return dt.strftime("%Y-%m-%d")


def _load_categorized_bugs(categorized_dir: Path) -> list[CategorizedBug]:
    """Load all categorized bugs from the directory"""
    if not categorized_dir.exists():
        logger.warning(f"Categorized bugs directory not found: {categorized_dir}")
        return []

    bugs = []
    for file_path in categorized_dir.glob("*.json"):
        try:
            bug = CategorizedBug.load(file_path)
            bugs.append(bug)
        except Exception as e:
            logger.error(f"Failed to parse {file_path.name}: {e}")

    return bugs


def _load_tracked_patterns(tracking_file: Path) -> list[TrackedPattern]:
    """Load tracked patterns from JSON file"""
    if not tracking_file.exists():
        return []

    try:
        with open(tracking_file) as f:
            data = json.load(f)
        return [TrackedPattern.from_dict(item) for item in data]
    except Exception as e:
        logger.error(f"Failed to parse tracked patterns: {e}")
        return []


def _save_tracked_patterns(patterns: list[TrackedPattern], tracking_file: Path) -> None:
    """Save tracked patterns to JSON file"""
    tracking_file.parent.mkdir(parents=True, exist_ok=True)

    with open(tracking_file, "w") as f:
        json.dump([p.to_dict() for p in patterns], f, indent=2)

    logger.info(f"Saved {len(patterns)} tracked patterns")


def _get_repo_info() -> dict[str, str] | None:
    """Get GitHub owner/repo from git remote"""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
        )
        remote_url = result.stdout.strip()

        # Parse GitHub URL (https or ssh)
        import re

        match = re.search(r"github\.com[:/](.+?)/(.+?)(?:\.git)?$", remote_url)
        if match:
            return {"owner": match.group(1), "repo": match.group(2)}

        logger.error("Could not parse GitHub repo from remote URL")
        return None
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get GitHub repo info: {e}")
        return None


def detect_patterns(
    bugs: list[CategorizedBug],
    threshold: int = 3,
    window_days: int = 30,
) -> list[BugPattern]:
    """
    Detect recurring bug patterns.

    Groups bugs by (category, module) and finds patterns with threshold+ bugs
    within the window period.

    Args:
        bugs: List of categorized bugs
        threshold: Minimum bugs to trigger pattern (default: 3)
        window_days: Time window in days for recent bugs (default: 30)

    Returns:
        List of detected BugPattern instances
    """
    logger.info(f"Detecting patterns (threshold: {threshold}, window: {window_days} days)")

    # Group bugs by (category, module)
    grouped: dict[str, dict[str, Any]] = {}

    for bug in bugs:
        category = bug.primary_category.value if bug.primary_category else "uncategorized"
        files = bug.files_changed or []

        # Handle each file separately to avoid missing patterns across files
        for file_path in files:
            parts = file_path.split("/")
            module = "/".join(parts[:2]) if len(parts) > 1 else "root"
            key = f"{category}-{module}"

            if key not in grouped:
                grouped[key] = {
                    "category": category,
                    "module": module,
                    "bugs": [],
                }

            # Avoid duplicates
            if not any(b.id == bug.id for b in grouped[key]["bugs"]):
                grouped[key]["bugs"].append(bug)

    # Find patterns: groups with threshold+ bugs in the window
    patterns = []

    for key, group in grouped.items():
        # Filter bugs within time window
        recent_bugs = [
            bug for bug in group["bugs"] if _is_within_window(bug.date_fixed, window_days)
        ]

        if len(recent_bugs) >= threshold:
            # Sort by date (oldest first)
            recent_bugs.sort(key=lambda b: b.date_fixed)

            # Parse category
            try:
                category = BugCategory.from_string(group["category"])
            except ValueError:
                # Handle uncategorized or unknown categories
                category = BugCategory.LOGIC_ERROR

            pattern = BugPattern(
                key=key,
                category=category,
                module=group["module"],
                bug_count=len(recent_bugs),
                first_occurrence=recent_bugs[0].date_fixed,
                latest_occurrence=recent_bugs[-1].date_fixed,
                bugs=recent_bugs,
                status="open",
            )
            patterns.append(pattern)

    logger.info(f"Detected {len(patterns)} patterns")
    return patterns


def build_github_issue_body(pattern: BugPattern) -> str:
    """
    Build GitHub issue body for a pattern.

    Args:
        pattern: The BugPattern to format

    Returns:
        Formatted markdown string for GitHub issue body
    """
    body = "# Bug Pattern Detected\n\n"
    body += f"**Category:** {pattern.category.value}\n"
    body += f"**Module:** {pattern.module}\n"
    body += f"**Occurrences:** {pattern.bug_count} bugs in last 30 days\n"
    body += f"**First occurrence:** {_format_date(pattern.first_occurrence)}\n"
    body += f"**Latest occurrence:** {_format_date(pattern.latest_occurrence)}\n\n"

    body += "---\n\n"
    body += "## Pattern Summary\n\n"
    body += (
        f"This bug pattern has been detected in **{pattern.module}** with "
        f"**{pattern.bug_count}** similar bugs in the **{pattern.category.value}** "
        f"category over the last 30 days.\n\n"
    )

    # Trend analysis
    trend = "increasing" if pattern.bug_count >= 5 else "stable"
    body += f"**Trend:** {trend}\n\n"

    body += "---\n\n"
    body += "## Similar Bugs\n\n"

    for bug in pattern.bugs:
        body += f"### {bug.id}\n"
        body += f"- **Date:** {_format_date(bug.date_fixed)}\n"
        body += f"- **Author:** {bug.author_name or 'Unknown'}\n"
        body += f"- **Message:** {bug.commit_message}\n"
        body += f"- **Severity:** {bug.severity or 'N/A'}\n"
        if bug.github_url:
            short_sha = bug.commit_sha[:7] if bug.commit_sha else "link"
            body += f"- **Commit:** [{short_sha}]({bug.github_url})\n"
        if bug.prevention_tips:
            body += f"- **Prevention tip:** {bug.prevention_tips}\n"
        body += "\n"

    body += "---\n\n"
    body += "## Recommended Actions\n\n"
    body += "### Immediate Actions\n"
    body += "1. Review the similar bugs listed above\n"
    body += "2. Identify common root causes\n"
    body += "3. Check if recent fixes actually addressed the underlying issue\n\n"

    body += "### Long-term Actions\n"
    body += (
        f"1. Consider refactoring **{pattern.module}** to prevent "
        f"**{pattern.category.value}** bugs\n"
    )
    body += "2. Add automated tests to catch this pattern earlier\n"
    body += "3. Document prevention strategies in team knowledge base\n\n"

    body += "---\n\n"
    body += "## Timeline\n\n"
    body += "| Date | Bug ID | Author |\n"
    body += "|------|--------|--------|\n"
    for bug in pattern.bugs:
        body += f"| {_format_date(bug.date_fixed)} | {bug.id} | {bug.author_name or 'Unknown'} |\n"

    body += "\n---\n\n"
    body += "**Auto-generated by Ralph Bug Pattern Detector**\n"
    body += "**Deep dive analysis:** See factory run results in `.ralph/factory/runs/`\n"

    return body


def create_github_issue(pattern: BugPattern) -> dict[str, Any] | None:
    """
    Create GitHub issue for a pattern via REST API.

    Uses GITHUB_TOKEN environment variable for authentication.

    Args:
        pattern: The BugPattern to create an issue for

    Returns:
        Dictionary with issue number and URL, or None if failed
    """
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        logger.error("GITHUB_TOKEN not set, cannot create issue")
        return None

    repo_info = _get_repo_info()
    if not repo_info:
        return None

    title = f"[Bug Pattern] {pattern.category.value} in {pattern.module}"
    body = build_github_issue_body(pattern)

    try:
        response = requests.post(
            f"https://api.github.com/repos/{repo_info['owner']}/{repo_info['repo']}/issues",
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "Ralph-Bug-Pattern-Detector",
            },
            json={
                "title": title,
                "body": body,
                "labels": GITHUB_ISSUE_LABELS,
            },
            timeout=30,
        )

        if response.status_code == 201:
            issue = response.json()
            logger.info(f"Created GitHub issue #{issue['number']}: {title}")
            return {
                "number": issue["number"],
                "url": issue["html_url"],
            }
        else:
            logger.error(f"Failed to create issue: HTTP {response.status_code}")
            logger.error(response.text)
            return None

    except requests.RequestException as e:
        logger.error(f"Failed to create GitHub issue: {e}")
        return None


def close_github_issue(
    issue_number: int,
    resolution_note: str = "Pattern resolved automatically",
) -> bool:
    """
    Close GitHub issue with resolution comment.

    Args:
        issue_number: The issue number to close
        resolution_note: Note explaining why the issue is being closed

    Returns:
        True if successful, False otherwise
    """
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        logger.warning("GITHUB_TOKEN not set, cannot close issue")
        return False

    repo_info = _get_repo_info()
    if not repo_info:
        return False

    try:
        # Close the issue
        close_response = requests.patch(
            f"https://api.github.com/repos/{repo_info['owner']}/{repo_info['repo']}/issues/{issue_number}",
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "Ralph-Bug-Pattern-Detector",
            },
            json={"state": "closed"},
            timeout=30,
        )

        if close_response.status_code == 200:
            logger.info(f"Closed GitHub issue #{issue_number}")
        else:
            logger.error(f"Failed to close issue: HTTP {close_response.status_code}")
            return False

        # Add resolution comment
        comment_body = (
            f"## Pattern Resolved\n\n{resolution_note}\n\n"
            "This pattern has been automatically closed by Ralph Bug Pattern Detector."
        )
        requests.post(
            f"https://api.github.com/repos/{repo_info['owner']}/{repo_info['repo']}/issues/{issue_number}/comments",
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "Ralph-Bug-Pattern-Detector",
            },
            json={"body": comment_body},
            timeout=30,
        )

        return True

    except requests.RequestException as e:
        logger.error(f"Failed to close issue: {e}")
        return False


def check_pattern_resolution(
    tracked_patterns: list[TrackedPattern],
    current_bugs: list[CategorizedBug],
    resolution_days: int = 60,
) -> list[TrackedPattern]:
    """
    Check if patterns should be auto-closed (no new bugs in resolution_days).

    Args:
        tracked_patterns: List of currently tracked patterns
        current_bugs: List of all categorized bugs
        resolution_days: Days without new bugs before auto-closing (default: 60)

    Returns:
        List of patterns that were closed
    """
    now = datetime.now()
    closed_patterns = []

    for tracked in tracked_patterns:
        if tracked.status == "closed":
            continue  # Already closed

        # Find bugs matching this pattern
        matching_bugs = []
        for bug in current_bugs:
            category = bug.primary_category.value if bug.primary_category else "uncategorized"
            files = bug.files_changed or []

            for file_path in files:
                parts = file_path.split("/")
                module = "/".join(parts[:2]) if len(parts) > 1 else "root"
                key = f"{category}-{module}"
                if key == tracked.key:
                    matching_bugs.append(bug)
                    break  # Only count once per bug

        # Find latest bug date
        if not matching_bugs:
            continue  # No bugs (shouldn't happen for tracked patterns)

        matching_bugs.sort(key=lambda b: b.date_fixed, reverse=True)
        latest_bug_date = matching_bugs[0].date_fixed
        days_since_last_bug = (now - latest_bug_date).days

        if days_since_last_bug >= resolution_days:
            logger.info(
                f"Pattern {tracked.key} resolved ({days_since_last_bug} days since last bug)"
            )

            tracked.status = "closed"
            tracked.resolved_at = now
            tracked.resolution_note = f"No new bugs in {resolution_days} days"

            # Close GitHub issue if exists
            if tracked.github_issue_number:
                close_github_issue(
                    tracked.github_issue_number, tracked.resolution_note
                )

            closed_patterns.append(tracked)

    return closed_patterns


def detect_bug_patterns(
    bug_wikipedia_dir: Path,
    config: dict[str, Any] | None = None,
) -> list[BugPattern]:
    """
    Main function: Detect bug patterns and manage GitHub issues.

    Args:
        bug_wikipedia_dir: Path to the bug wikipedia directory
        config: Configuration dictionary with optional keys:
            - pattern_threshold: Minimum bugs to trigger pattern (default: 3)
            - pattern_window_days: Time window in days (default: 30)
            - pattern_resolution_days: Days before auto-closing (default: 60)
            - auto_create_issues: Whether to create GitHub issues (default: True)

    Returns:
        List of detected BugPattern instances
    """
    config = config or {}

    # Configuration defaults
    threshold = config.get("pattern_threshold", 3)
    window_days = config.get("pattern_window_days", 30)
    resolution_days = config.get("pattern_resolution_days", 60)
    auto_create_issues = config.get("auto_create_issues", True)

    logger.info("=" * 44)
    logger.info("Bug Pattern Detector")
    logger.info("=" * 44)

    # Setup paths
    categorized_dir = bug_wikipedia_dir / "categorized"
    patterns_dir = bug_wikipedia_dir / "patterns"
    tracking_file = patterns_dir / "tracked-patterns.json"

    # Load categorized bugs
    logger.info("Loading categorized bugs...")
    bugs = _load_categorized_bugs(categorized_dir)
    logger.info(f"Loaded {len(bugs)} categorized bugs")

    if not bugs:
        logger.warning("No categorized bugs found")
        return []

    # Detect patterns
    patterns = detect_patterns(bugs, threshold=threshold, window_days=window_days)

    if not patterns:
        logger.info("No patterns detected")
    else:
        logger.info(f"Found {len(patterns)} patterns to analyze")

    # Load tracked patterns
    tracked_patterns = _load_tracked_patterns(tracking_file)
    logger.info(f"Loaded {len(tracked_patterns)} tracked patterns")

    # Check pattern resolution (auto-close old patterns)
    closed_patterns = check_pattern_resolution(
        tracked_patterns, bugs, resolution_days=resolution_days
    )
    if closed_patterns:
        logger.info(f"Closed {len(closed_patterns)} resolved patterns")

    # Process new patterns
    for pattern in patterns:
        # Check if already tracked
        existing = next(
            (t for t in tracked_patterns if t.key == pattern.key), None
        )

        if existing and existing.status != "closed":
            logger.info(
                f"Pattern {pattern.key} already tracked "
                f"(issue #{existing.github_issue_number or 'N/A'})"
            )
            continue

        logger.info(f"Processing new pattern: {pattern.key}")

        # Create GitHub issue
        github_issue = None
        if auto_create_issues:
            github_issue = create_github_issue(pattern)
            if github_issue:
                pattern.github_issue_number = github_issue["number"]
                pattern.github_issue_url = github_issue["url"]

        # Save pattern summary
        patterns_dir.mkdir(parents=True, exist_ok=True)
        pattern.save(patterns_dir)

        # Track this pattern
        tracked_patterns.append(
            TrackedPattern(
                key=pattern.key,
                category=pattern.category.value,
                module=pattern.module,
                bug_count=pattern.bug_count,
                first_detected=datetime.now(),
                github_issue_number=github_issue["number"] if github_issue else None,
                github_issue_url=github_issue["url"] if github_issue else None,
                status="open",
            )
        )

        logger.info(f"Pattern {pattern.key} tracked")

    # Save updated tracked patterns
    _save_tracked_patterns(tracked_patterns, tracking_file)

    logger.info("=" * 44)
    logger.info("Bug pattern detection complete")
    logger.info("=" * 44)

    return patterns
