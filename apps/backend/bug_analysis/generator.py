"""
Bug Wikipedia Generator - Builds markdown documentation from categorized bugs
=============================================================================

Port of Ralph CLI bug-wikipedia-generator.js to Python.

Features:
- Generates index.md with table of contents
- Creates category markdown files (logic-errors.md, race-conditions.md, etc.)
- Creates by-developer markdown files
- Creates by-module markdown files
- Calculates metrics (summary.json)
- Updates daily as new bugs are scanned

Directory Structure:
.auto-claude/bug-wikipedia/
├── index.md                          # Table of contents
├── categories/
│   ├── logic-errors.md
│   ├── race-conditions.md
│   └── ...
├── by-developer/
│   ├── developer-alice.md
│   └── developer-bob.md
├── by-module/
│   ├── authentication.md
│   └── payment-processing.md
├── patterns/
│   └── recurring-issues.md
└── metrics/
    └── summary.json
"""

import json
import re
from datetime import datetime
from pathlib import Path

from .models import CategorizedBug, BugCategory, BugData

# =============================================================================
# CONFIGURATION CONSTANTS
# =============================================================================

BUG_CATEGORIES = [
    "logic-error",
    "race-condition",
    "requirements-misunderstanding",
    "integration-issue",
    "environment-specific",
    "dependency-issue",
    "performance-degradation",
    "security-vulnerability",
    "data-corruption",
    "user-input-validation",
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def format_date(date_str: str | datetime | None) -> str:
    """
    Format date as YYYY-MM-DD.

    Args:
        date_str: Date string or datetime object

    Returns:
        Formatted date string
    """
    if date_str is None:
        return "Unknown"

    try:
        if isinstance(date_str, datetime):
            return date_str.strftime("%Y-%m-%d")
        elif isinstance(date_str, str):
            # Try to parse ISO format
            date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return date.strftime("%Y-%m-%d")
        return str(date_str)
    except (ValueError, TypeError):
        return str(date_str) if date_str else "Unknown"


def days_between(date1: str | datetime | None, date2: str | datetime | None) -> int | None:
    """
    Calculate days between two dates.

    Args:
        date1: First date (string or datetime)
        date2: Second date (string or datetime)

    Returns:
        Number of days between dates, or None if dates are invalid
    """
    if date1 is None or date2 is None:
        return None

    try:
        if isinstance(date1, str):
            d1 = datetime.fromisoformat(date1.replace("Z", "+00:00"))
        else:
            d1 = date1

        if isinstance(date2, str):
            d2 = datetime.fromisoformat(date2.replace("Z", "+00:00"))
        else:
            d2 = date2

        diff = abs((d2 - d1).days)
        return diff
    except (ValueError, TypeError):
        return None


def extract_module(file_path: str | None) -> str:
    """
    Extract module name from file path.

    Args:
        file_path: Full file path (e.g., "src/auth/session.ts")

    Returns:
        Module path (e.g., "src/auth")
    """
    if not file_path:
        return "unknown"

    # Extract directory path
    parts = file_path.split("/")
    if len(parts) <= 1:
        return "root"

    # Return first two directory levels
    return "/".join(parts[:2])


def format_category_name(category_id: str) -> str:
    """
    Format category ID to display name.

    Args:
        category_id: Category ID (e.g., "race-condition")

    Returns:
        Display name (e.g., "Race Condition")
    """
    return " ".join(word.capitalize() for word in category_id.split("-"))


def sanitize_developer_name(name: str) -> str:
    """
    Sanitize developer name for filename.

    Args:
        name: Developer name

    Returns:
        Sanitized name for filename
    """
    sanitized = name.lower()
    sanitized = re.sub(r"\s+", "-", sanitized)
    sanitized = re.sub(r"[^a-z0-9-]", "", sanitized)
    return sanitized


def sanitize_module_name(module: str) -> str:
    """
    Sanitize module name for filename.

    Args:
        module: Module path

    Returns:
        Sanitized name for filename
    """
    sanitized = module.lower()
    sanitized = sanitized.replace("/", "-")
    sanitized = re.sub(r"[^a-z0-9-]", "", sanitized)
    return sanitized


# =============================================================================
# DATA LOADING FUNCTIONS
# =============================================================================


def load_raw_bugs(bug_wikipedia_dir: Path) -> list[dict]:
    """
    Load all raw bugs from bug-wikipedia/raw/ directory.

    Args:
        bug_wikipedia_dir: Base bug Wikipedia directory

    Returns:
        List of raw bug dictionaries
    """
    raw_dir = bug_wikipedia_dir / "raw"

    if not raw_dir.exists():
        print(f"  Warning: Raw bugs directory not found: {raw_dir}")
        return []

    bugs = []
    for file_path in raw_dir.glob("*.json"):
        try:
            with open(file_path) as f:
                bug = json.load(f)
                bugs.append(bug)
        except (json.JSONDecodeError, OSError) as e:
            print(f"  Error: Failed to parse {file_path.name}: {e}")

    return bugs


def load_categorized_bugs(bug_wikipedia_dir: Path) -> list[CategorizedBug]:
    """
    Load all categorized bugs from bug-wikipedia/categorized/ directory.

    Args:
        bug_wikipedia_dir: Base bug Wikipedia directory

    Returns:
        List of CategorizedBug instances
    """
    categorized_dir = bug_wikipedia_dir / "categorized"

    if not categorized_dir.exists():
        print(f"  Warning: Categorized bugs directory not found: {categorized_dir}")
        return []

    bugs = []
    for file_path in categorized_dir.glob("*.json"):
        try:
            bug = CategorizedBug.load(file_path)
            bugs.append(bug)
        except (json.JSONDecodeError, OSError, ValueError) as e:
            print(f"  Error: Failed to parse categorized {file_path.name}: {e}")

    return bugs


# =============================================================================
# MARKDOWN GENERATION FUNCTIONS
# =============================================================================


def generate_index_md(raw_bugs: list[dict], categorized_bugs: list[CategorizedBug]) -> str:
    """
    Generate index.md (table of contents).

    Args:
        raw_bugs: List of raw bug dictionaries
        categorized_bugs: List of CategorizedBug instances

    Returns:
        Markdown content for index.md
    """
    category_counts: dict[str, int] = {}
    developer_counts: dict[str, int] = {}
    module_counts: dict[str, int] = {}

    # Count bugs by category
    for bug in categorized_bugs:
        category = bug.primary_category.value if bug.primary_category else "uncategorized"
        category_counts[category] = category_counts.get(category, 0) + 1

    # Count bugs by developer
    for bug in raw_bugs:
        author = bug.get("author", {})
        dev = author.get("name", "Unknown") if isinstance(author, dict) else "Unknown"
        developer_counts[dev] = developer_counts.get(dev, 0) + 1

    # Count bugs by module
    for bug in raw_bugs:
        files = bug.get("files_changed", [])
        for file in files:
            module = extract_module(file)
            module_counts[module] = module_counts.get(module, 0) + 1

    md = "# Bug Wikipedia - Table of Contents\n\n"
    md += f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d')}\n\n"
    md += f"**Total Bugs:** {len(raw_bugs)} ({len(categorized_bugs)} categorized)\n\n"
    md += "---\n\n"

    # Categories section
    md += "## By Category\n\n"
    sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
    for category, count in sorted_categories:
        filename = f"{category}.md"
        md += f"- [{format_category_name(category)}](categories/{filename}) - {count} bugs\n"
    md += "\n"

    # Developers section
    md += "## By Developer\n\n"
    sorted_developers = sorted(developer_counts.items(), key=lambda x: x[1], reverse=True)
    for dev, count in sorted_developers:
        filename = f"developer-{sanitize_developer_name(dev)}.md"
        md += f"- [{dev}](by-developer/{filename}) - {count} bugs\n"
    md += "\n"

    # Modules section (limit to top 20)
    md += "## By Module\n\n"
    sorted_modules = sorted(module_counts.items(), key=lambda x: x[1], reverse=True)
    for module, count in sorted_modules[:20]:
        filename = f"{sanitize_module_name(module)}.md"
        md += f"- [{module}](by-module/{filename}) - {count} bugs\n"
    md += "\n"

    # Metrics section
    md += "## Metrics\n\n"
    md += "- [Summary Metrics](metrics/summary.json)\n"
    md += "- [Recurring Patterns](patterns/recurring-issues.md)\n"

    return md


def generate_category_md(category: str, categorized_bugs: list[CategorizedBug]) -> str | None:
    """
    Generate category markdown file (e.g., categories/race-conditions.md).

    Args:
        category: Category ID
        categorized_bugs: List of all categorized bugs

    Returns:
        Markdown content for category file, or None if no bugs in category
    """
    category_bugs = [
        b for b in categorized_bugs
        if b.primary_category and b.primary_category.value == category
    ]

    if not category_bugs:
        return None

    md = f"# {format_category_name(category)} Bugs\n\n"

    # Summary section
    severity_counts = {"high": 0, "medium": 0, "low": 0, "critical": 0}
    module_counts: dict[str, int] = {}
    total_time_to_fix = 0
    time_to_fix_count = 0

    for bug in category_bugs:
        severity = bug.severity or "medium"
        severity_counts[severity] = severity_counts.get(severity, 0) + 1

        # Count modules
        files = bug.files_changed or []
        for file in files:
            module = extract_module(file)
            module_counts[module] = module_counts.get(module, 0) + 1

        # Calculate time to fix (if available)
        # Note: date_introduced is not in our model, but we keep structure for future
        # For now, we skip time-to-fix calculations unless we add introduced_commit tracking

    avg_time_to_fix = (
        f"{total_time_to_fix / time_to_fix_count:.1f}" if time_to_fix_count > 0 else "N/A"
    )
    most_affected_module = (
        sorted(module_counts.items(), key=lambda x: x[1], reverse=True)[0][0]
        if module_counts else "N/A"
    )

    md += "## Summary\n"
    md += f"- **Total:** {len(category_bugs)} bugs\n"
    md += f"- **Severity:** {severity_counts.get('high', 0)} high, {severity_counts.get('medium', 0)} medium, {severity_counts.get('low', 0)} low\n"
    md += f"- **Avg time to fix:** {avg_time_to_fix} days\n"
    md += f"- **Most affected module:** {most_affected_module}\n"
    md += "\n"

    # Bugs section
    md += "## Bugs\n\n"

    for bug in category_bugs:
        short_sha = bug.commit_sha[:7] if bug.commit_sha else bug.id
        md += f"### Bug-{short_sha}: {bug.commit_message}\n"
        md += f"- **Fixed:** {format_date(bug.date_fixed)} by @{bug.author_name or 'Unknown'}\n"

        files = bug.files_changed or []
        if files:
            md += f"- **Files:** {', '.join(files)}\n"

        if bug.prevention_tips:
            md += f"- **Prevention tip:** {bug.prevention_tips}\n"

        if bug.github_url:
            md += f"- [Commit]({bug.github_url})\n"

        md += "\n"

    return md


def generate_developer_md(
    developer: str,
    raw_bugs: list[dict],
    categorized_bugs: list[CategorizedBug],
) -> str | None:
    """
    Generate by-developer markdown file.

    Args:
        developer: Developer name
        raw_bugs: List of raw bug dictionaries
        categorized_bugs: List of CategorizedBug instances

    Returns:
        Markdown content for developer file, or None if no bugs
    """
    dev_bugs = [
        b for b in raw_bugs
        if b.get("author", {}).get("name") == developer
    ]

    if not dev_bugs:
        return None

    md = f"# Bugs - {developer}\n\n"

    # Get categorized bugs for this developer
    dev_categorized_bugs = [
        b for b in categorized_bugs
        if b.author_name == developer
    ]

    # Summary
    md += "## Summary\n"
    md += f"- **Total bugs:** {len(dev_bugs)}\n"
    md += f"- **Categorized:** {len(dev_categorized_bugs)}\n"

    # Count by category
    category_counts: dict[str, int] = {}
    for bug in dev_categorized_bugs:
        category = bug.primary_category.value if bug.primary_category else "uncategorized"
        category_counts[category] = category_counts.get(category, 0) + 1

    md += "\n### By Category\n"
    sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
    for category, count in sorted_categories:
        md += f"- {format_category_name(category)}: {count}\n"
    md += "\n"

    # Recent bugs (sorted by date, limited to 10)
    md += "## Recent Bugs\n\n"

    def get_date_fixed(bug: dict) -> datetime:
        date_str = bug.get("date_fixed", "")
        if not date_str:
            return datetime.min
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return datetime.min

    sorted_bugs = sorted(dev_bugs, key=get_date_fixed, reverse=True)[:10]

    for bug in sorted_bugs:
        short_sha = bug.get("commit_sha", "")[:7] or bug.get("id", "unknown")
        md += f"### Bug-{short_sha}: {bug.get('commit_message', 'No message')}\n"
        md += f"- **Fixed:** {format_date(bug.get('date_fixed'))}\n"

        files = bug.get("files_changed", [])
        if files:
            md += f"- **Files:** {', '.join(files)}\n"

        github_url = bug.get("github_url")
        if github_url:
            md += f"- [Commit]({github_url})\n"

        md += "\n"

    return md


def generate_module_md(
    module: str,
    raw_bugs: list[dict],
    categorized_bugs: list[CategorizedBug],
) -> str | None:
    """
    Generate by-module markdown file.

    Args:
        module: Module path
        raw_bugs: List of raw bug dictionaries
        categorized_bugs: List of CategorizedBug instances

    Returns:
        Markdown content for module file, or None if no bugs
    """
    module_bugs = [
        b for b in raw_bugs
        if any(extract_module(f) == module for f in b.get("files_changed", []))
    ]

    if not module_bugs:
        return None

    md = f"# Bugs - {module}\n\n"

    # Get categorized bugs for this module
    module_categorized_bugs = [
        b for b in categorized_bugs
        if any(extract_module(f) == module for f in (b.files_changed or []))
    ]

    # Summary
    md += "## Summary\n"
    md += f"- **Total bugs:** {len(module_bugs)}\n"
    md += f"- **Categorized:** {len(module_categorized_bugs)}\n"

    # Count by category
    category_counts: dict[str, int] = {}
    for bug in module_categorized_bugs:
        category = bug.primary_category.value if bug.primary_category else "uncategorized"
        category_counts[category] = category_counts.get(category, 0) + 1

    md += "\n### By Category\n"
    sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
    for category, count in sorted_categories:
        md += f"- {format_category_name(category)}: {count}\n"
    md += "\n"

    # Recent bugs (sorted by date, limited to 10)
    md += "## Recent Bugs\n\n"

    def get_date_fixed(bug: dict) -> datetime:
        date_str = bug.get("date_fixed", "")
        if not date_str:
            return datetime.min
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return datetime.min

    sorted_bugs = sorted(module_bugs, key=get_date_fixed, reverse=True)[:10]

    for bug in sorted_bugs:
        short_sha = bug.get("commit_sha", "")[:7] or bug.get("id", "unknown")
        author = bug.get("author", {})
        author_name = author.get("name", "Unknown") if isinstance(author, dict) else "Unknown"

        md += f"### Bug-{short_sha}: {bug.get('commit_message', 'No message')}\n"
        md += f"- **Fixed:** {format_date(bug.get('date_fixed'))} by @{author_name}\n"

        files = bug.get("files_changed", [])
        if files:
            md += f"- **Files:** {', '.join(files)}\n"

        github_url = bug.get("github_url")
        if github_url:
            md += f"- [Commit]({github_url})\n"

        md += "\n"

    return md


def generate_metrics(raw_bugs: list[dict], categorized_bugs: list[CategorizedBug]) -> dict:
    """
    Generate metrics summary.json.

    Args:
        raw_bugs: List of raw bug dictionaries
        categorized_bugs: List of CategorizedBug instances

    Returns:
        Metrics dictionary
    """
    metrics = {
        "generated_at": datetime.now().isoformat(),
        "total_bugs": len(raw_bugs),
        "categorized_bugs": len(categorized_bugs),
        "by_category": {},
        "by_severity": {"high": 0, "medium": 0, "low": 0, "critical": 0},
        "by_developer": {},
        "by_module": {},
        "avg_time_to_detect_days": None,
        "avg_time_to_fix_days": None,
    }

    # Count by category
    for bug in categorized_bugs:
        category = bug.primary_category.value if bug.primary_category else "uncategorized"
        metrics["by_category"][category] = metrics["by_category"].get(category, 0) + 1

        severity = bug.severity or "medium"
        metrics["by_severity"][severity] = metrics["by_severity"].get(severity, 0) + 1

    # Count by developer
    for bug in raw_bugs:
        author = bug.get("author", {})
        dev = author.get("name", "Unknown") if isinstance(author, dict) else "Unknown"
        metrics["by_developer"][dev] = metrics["by_developer"].get(dev, 0) + 1

    # Count by module
    for bug in raw_bugs:
        files = bug.get("files_changed", [])
        for file in files:
            module = extract_module(file)
            metrics["by_module"][module] = metrics["by_module"].get(module, 0) + 1

    # Calculate average time to fix (placeholder - needs date_introduced tracking)
    # For now, we skip this calculation
    total_time_to_fix = 0
    time_to_fix_count = 0

    if time_to_fix_count > 0:
        metrics["avg_time_to_fix_days"] = round(total_time_to_fix / time_to_fix_count, 1)

    return metrics


# =============================================================================
# MAIN GENERATION FUNCTION
# =============================================================================


def generate_bug_wikipedia(bug_wikipedia_dir: Path, dry_run: bool = False) -> None:
    """
    Main function - generates all Bug Wikipedia files.

    Args:
        bug_wikipedia_dir: Base bug Wikipedia directory
        dry_run: If True, preview changes without writing files
    """
    print("[1/6] Loading bug data...")
    raw_bugs = load_raw_bugs(bug_wikipedia_dir)
    categorized_bugs = load_categorized_bugs(bug_wikipedia_dir)

    print(f"  Loaded {len(raw_bugs)} raw bugs, {len(categorized_bugs)} categorized")

    if not raw_bugs:
        print("  Warning: No bugs found. Run bug scanner first.")
        return

    # Create output directories
    categories_dir = bug_wikipedia_dir / "categories"
    by_developer_dir = bug_wikipedia_dir / "by-developer"
    by_module_dir = bug_wikipedia_dir / "by-module"
    patterns_dir = bug_wikipedia_dir / "patterns"
    metrics_dir = bug_wikipedia_dir / "metrics"

    if not dry_run:
        categories_dir.mkdir(parents=True, exist_ok=True)
        by_developer_dir.mkdir(parents=True, exist_ok=True)
        by_module_dir.mkdir(parents=True, exist_ok=True)
        patterns_dir.mkdir(parents=True, exist_ok=True)
        metrics_dir.mkdir(parents=True, exist_ok=True)

    print("[2/6] Generating index.md...")
    index_md = generate_index_md(raw_bugs, categorized_bugs)
    if not dry_run:
        (bug_wikipedia_dir / "index.md").write_text(index_md)
    print("  Generated index.md")

    print("[3/6] Generating category markdown files...")
    category_count = 0
    for category in BUG_CATEGORIES:
        md = generate_category_md(category, categorized_bugs)
        if md:
            filename = f"{category}.md"
            if not dry_run:
                (categories_dir / filename).write_text(md)
            category_count += 1
    print(f"  Generated {category_count} category files")

    print("[4/6] Generating by-developer markdown files...")
    developers = set()
    for bug in raw_bugs:
        author = bug.get("author", {})
        name = author.get("name") if isinstance(author, dict) else None
        if name:
            developers.add(name)

    developer_count = 0
    for dev in sorted(developers):
        md = generate_developer_md(dev, raw_bugs, categorized_bugs)
        if md:
            filename = f"developer-{sanitize_developer_name(dev)}.md"
            if not dry_run:
                (by_developer_dir / filename).write_text(md)
            developer_count += 1
    print(f"  Generated {developer_count} developer files")

    print("[5/6] Generating by-module markdown files...")
    modules = set()
    for bug in raw_bugs:
        files = bug.get("files_changed", [])
        for file in files:
            modules.add(extract_module(file))

    module_count = 0
    for module in sorted(modules):
        md = generate_module_md(module, raw_bugs, categorized_bugs)
        if md:
            filename = f"{sanitize_module_name(module)}.md"
            if not dry_run:
                (by_module_dir / filename).write_text(md)
            module_count += 1
    print(f"  Generated {module_count} module files")

    print("[6/6] Generating metrics/summary.json...")
    metrics = generate_metrics(raw_bugs, categorized_bugs)
    if not dry_run:
        with open(metrics_dir / "summary.json", "w") as f:
            json.dump(metrics, f, indent=2)
    print("  Generated summary.json")

    print("")
    print("Bug Wikipedia generation complete!")
    print("")
    print("Summary:")
    print(f"  - Total bugs: {len(raw_bugs)}")
    print(f"  - Categorized: {len(categorized_bugs)}")
    print(f"  - Category files: {category_count}")
    print(f"  - Developer files: {developer_count}")
    print(f"  - Module files: {module_count}")

    if dry_run:
        print("")
        print("  Dry run mode - no files written")
