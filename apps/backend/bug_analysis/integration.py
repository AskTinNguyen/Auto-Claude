"""
QA Loop Integration - Helpers for integrating with the QA workflow
===================================================================

Provides utilities for extracting bug data from QA iteration results
and feeding them into the Bug Wikipedia system.
"""

import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .models import BugData, CategorizedBug, BugCategory

logger = logging.getLogger(__name__)


def extract_bugs_from_iteration(
    issues: list[dict],
    spec_dir: Path,
) -> list[BugData]:
    """
    Convert QA issues to BugData format for Bug Wikipedia tracking.

    This function bridges the QA loop output with the Bug Wikipedia
    system, allowing bugs found during QA iterations to be tracked,
    categorized, and analyzed for patterns.

    Args:
        issues: List of QA issues from an iteration. Each issue dict
               should contain:
               - id: Unique issue identifier
               - title: Short description of the issue
               - description: Full error message or details
               - file: Comma-separated list of affected files (optional)
               - severity: Issue severity level (optional)
        spec_dir: Spec directory for git operations

    Returns:
        List of BugData objects ready for Bug Wikipedia storage

    Example:
        >>> issues = [
        ...     {
        ...         "id": "qa-001",
        ...         "title": "TypeError in user validation",
        ...         "description": "NoneType has no attribute 'email'",
        ...         "file": "src/validators/user.py",
        ...     }
        ... ]
        >>> bugs = extract_bugs_from_iteration(issues, Path(".auto-claude/specs/my-spec"))
        >>> for bug in bugs:
        ...     bug.save(Path(".auto-claude/bug-wikipedia/raw"))
    """
    bugs: list[BugData] = []
    now = datetime.now(timezone.utc)

    for issue in issues:
        # Generate bug ID from issue ID
        issue_id = issue.get("id", "unknown")
        bug_id = f"bug-qa-{issue_id}"

        # Try to get current git commit SHA
        commit_sha = "qa-issue"  # Default if git fails
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=spec_dir,
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            commit_sha = result.stdout.strip()[:8]
        except (subprocess.SubprocessError, OSError) as e:
            logger.debug(f"Could not get git commit SHA: {e}")

        # Parse files from comma-separated string or list
        files_raw = issue.get("file", "")
        if isinstance(files_raw, str):
            files_changed = [f.strip() for f in files_raw.split(",") if f.strip()]
        elif isinstance(files_raw, list):
            files_changed = [str(f) for f in files_raw if f]
        else:
            files_changed = []

        # Create BugData instance
        bug = BugData(
            id=bug_id,
            commit_sha=commit_sha,
            commit_message=issue.get("title", "QA Issue"),
            author_name="QA Agent",
            author_email="qa@auto-claude",
            date_fixed=now,
            files_changed=files_changed,
            diff="",  # QA issues typically don't have diffs
            related_issues=[],
            github_url=None,
            error_message=issue.get("description", ""),
            scanned_at=now,
        )
        bugs.append(bug)

    return bugs


def save_qa_bugs_to_wikipedia(
    issues: list[dict],
    spec_dir: Path,
    bug_wikipedia_dir: Path | None = None,
) -> int:
    """
    Extract bugs from QA issues and save them to Bug Wikipedia.

    This is a convenience function that extracts bugs and saves them
    in a single call.

    Args:
        issues: List of QA issues from an iteration
        spec_dir: Spec directory for git operations
        bug_wikipedia_dir: Directory for Bug Wikipedia storage.
                          Defaults to spec_dir / "bug-wikipedia"

    Returns:
        Number of bugs saved
    """
    if not issues:
        return 0

    if bug_wikipedia_dir is None:
        bug_wikipedia_dir = spec_dir / "bug-wikipedia"

    raw_dir = bug_wikipedia_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    bugs = extract_bugs_from_iteration(issues, spec_dir)

    saved_count = 0
    for bug in bugs:
        try:
            bug.save(raw_dir)
            saved_count += 1
            logger.debug(f"Saved QA bug to Wikipedia: {bug.id}")
        except Exception as e:
            logger.warning(f"Failed to save bug {bug.id}: {e}")

    return saved_count


def map_qa_severity_to_bug_severity(qa_severity: str) -> str:
    """
    Map QA severity levels to Bug Wikipedia severity levels.

    Args:
        qa_severity: QA severity string (e.g., "critical", "major", "minor")

    Returns:
        Bug Wikipedia severity: "critical", "high", "medium", or "low"
    """
    severity_map = {
        # QA severities
        "critical": "critical",
        "blocker": "critical",
        "major": "high",
        "significant": "high",
        "moderate": "medium",
        "normal": "medium",
        "minor": "low",
        "trivial": "low",
        "cosmetic": "low",
        # Numeric severities
        "1": "critical",
        "2": "high",
        "3": "medium",
        "4": "low",
        "5": "low",
    }

    normalized = qa_severity.lower().strip() if qa_severity else "medium"
    return severity_map.get(normalized, "medium")


def infer_bug_category_from_issue(issue: dict) -> BugCategory | None:
    """
    Attempt to infer a bug category from QA issue content.

    This provides a heuristic initial categorization before
    the AI-powered categorizer runs.

    Args:
        issue: QA issue dictionary

    Returns:
        Inferred BugCategory or None if not determinable
    """
    title = (issue.get("title", "") or "").lower()
    description = (issue.get("description", "") or "").lower()
    combined = f"{title} {description}"

    # Simple keyword-based heuristics
    category_keywords = {
        BugCategory.LOGIC_ERROR: [
            "logic", "incorrect", "wrong", "calculation", "off-by-one",
            "infinite loop", "boundary",
        ],
        BugCategory.RACE_CONDITION: [
            "race", "concurrent", "deadlock", "async", "await",
            "threading", "parallel", "timing",
        ],
        BugCategory.REQUIREMENTS_MISUNDERSTANDING: [
            "requirement", "spec", "expected", "should", "misunderstand",
        ],
        BugCategory.INTEGRATION_ISSUE: [
            "integration", "api", "interface", "incompatible", "mismatch",
            "contract",
        ],
        BugCategory.ENVIRONMENT_SPECIFIC: [
            "environment", "platform", "os", "windows", "linux", "macos",
            "production", "staging",
        ],
        BugCategory.DEPENDENCY_ISSUE: [
            "dependency", "package", "version", "npm", "pip", "library",
            "module not found",
        ],
        BugCategory.PERFORMANCE_DEGRADATION: [
            "slow", "performance", "memory", "leak", "timeout", "latency",
            "cpu", "resource",
        ],
        BugCategory.SECURITY_VULNERABILITY: [
            "security", "vulnerability", "injection", "xss", "csrf",
            "authentication", "authorization", "permission",
        ],
        BugCategory.DATA_CORRUPTION: [
            "corrupt", "data", "state", "integrity", "invalid state",
            "inconsistent",
        ],
        BugCategory.USER_INPUT_VALIDATION: [
            "validation", "input", "sanitize", "edge case", "null",
            "none", "undefined", "empty",
        ],
    }

    # Score each category
    best_category = None
    best_score = 0

    for category, keywords in category_keywords.items():
        score = sum(1 for kw in keywords if kw in combined)
        if score > best_score:
            best_score = score
            best_category = category

    # Only return if we have reasonable confidence
    if best_score >= 2:
        return best_category

    return None


def create_categorized_bug_from_qa_issue(
    issue: dict,
    spec_dir: Path,
) -> CategorizedBug | None:
    """
    Create a pre-categorized bug from a QA issue.

    This uses heuristic categorization for immediate tracking,
    with the expectation that AI categorization will refine it later.

    Args:
        issue: QA issue dictionary
        spec_dir: Spec directory for context

    Returns:
        CategorizedBug if categorizable, None otherwise
    """
    bugs = extract_bugs_from_iteration([issue], spec_dir)
    if not bugs:
        return None

    bug_data = bugs[0]

    # Infer category
    category = infer_bug_category_from_issue(issue)
    if category is None:
        category = BugCategory.LOGIC_ERROR  # Default fallback

    # Map severity
    severity = map_qa_severity_to_bug_severity(issue.get("severity", "medium"))

    return CategorizedBug.from_bug_data(
        bug_data,
        primary_category=category,
        secondary_categories=[],
        severity=severity,
        reasoning="Auto-categorized from QA issue (pending AI review)",
        prevention_tips="",
    )
