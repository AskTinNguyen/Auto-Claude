"""
Bug Wikipedia CLI Commands
==========================

CLI command handlers for Bug Wikipedia functionality:
- Scan git history for bugs
- Categorize bugs with AI
- Generate Bug Wikipedia markdown
- Detect recurring patterns
- Deep dive analysis on patterns
"""

import asyncio
import json
import sys
from pathlib import Path

# Ensure parent directory is in path for imports (before other imports)
_PARENT_DIR = Path(__file__).parent.parent
if str(_PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(_PARENT_DIR))


# =============================================================================
# CONFIGURATION
# =============================================================================


def load_bug_wikipedia_config() -> dict:
    """
    Load bug-wikipedia-config.json or return defaults.

    Returns:
        Configuration dictionary with bug Wikipedia settings
    """
    config_file = Path(".auto-claude/bug-wikipedia-config.json")
    if config_file.exists():
        try:
            return json.loads(config_file.read_text())
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: Failed to load bug-wikipedia-config.json: {e}")

    return {
        "enabled": True,
        "scan_mode": "project",
        "pattern_threshold": 3,
        "pattern_window_days": 30,
        "pattern_resolution_days": 60,
        "auto_create_issues": True,
        "deep_dive_enabled": True,
        "categorization_model": "claude-3-5-haiku-20241022",
    }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_bug_wikipedia_dir(mode: str) -> Path:
    """
    Get the bug Wikipedia directory based on scan mode.

    Args:
        mode: Either "auto-claude" or "project"

    Returns:
        Path to the bug Wikipedia directory
    """
    if mode == "auto-claude":
        # Auto-Claude mode: use the Auto-Claude project's bug-wikipedia
        auto_claude_root = Path(__file__).parent.parent.parent.parent.resolve()
        return auto_claude_root / ".auto-claude" / "bug-wikipedia"
    else:
        # Project mode: use the current project's bug-wikipedia
        return Path.cwd() / ".auto-claude" / "bug-wikipedia"


def get_project_dir(mode: str) -> Path:
    """
    Get the project directory based on scan mode.

    Args:
        mode: Either "auto-claude" or "project"

    Returns:
        Path to the project directory to scan
    """
    if mode == "auto-claude":
        # Auto-Claude mode: scan the Auto-Claude project itself
        return Path(__file__).parent.parent.parent.parent.resolve()
    else:
        # Project mode: scan the current project
        return Path.cwd()


def print_bug_status(bug_wikipedia_dir: Path) -> None:
    """
    Print bug Wikipedia statistics.

    Args:
        bug_wikipedia_dir: Path to the bug Wikipedia directory
    """
    raw_dir = bug_wikipedia_dir / "raw"
    categorized_dir = bug_wikipedia_dir / "categorized"
    patterns_dir = bug_wikipedia_dir / "patterns"
    deep_dive_dir = bug_wikipedia_dir / "deep-dive"

    # Count raw bugs
    raw_count = len(list(raw_dir.glob("*.json"))) if raw_dir.exists() else 0

    # Count categorized bugs
    categorized_count = len(list(categorized_dir.glob("*.json"))) if categorized_dir.exists() else 0

    # Count patterns
    pattern_count = len(list(patterns_dir.glob("pattern-*.json"))) if patterns_dir.exists() else 0

    # Count deep dives
    deep_dive_count = len(list(deep_dive_dir.glob("*.md"))) if deep_dive_dir.exists() else 0

    # Count categories
    categories = set()
    if categorized_dir.exists():
        for cat_file in categorized_dir.glob("*.json"):
            try:
                data = json.loads(cat_file.read_text())
                if data.get("primary_category"):
                    categories.add(data["primary_category"])
            except (json.JSONDecodeError, OSError):
                pass

    print("\n" + "=" * 50)
    print("  BUG WIKIPEDIA STATUS")
    print("=" * 50)
    print(f"\n  Directory: {bug_wikipedia_dir}")
    print(f"\n  Raw bugs scanned:    {raw_count}")
    print(f"  Categorized bugs:    {categorized_count}")
    print(f"  Uncategorized:       {raw_count - categorized_count}")
    print(f"  Patterns detected:   {pattern_count}")
    print(f"  Deep dive analyses:  {deep_dive_count}")
    print(f"  Categories found:    {len(categories)}")

    if categories:
        print("\n  Categories:")
        for cat in sorted(categories):
            print(f"    - {cat}")

    print()


# =============================================================================
# COMMAND HANDLERS
# =============================================================================


async def handle_bug_scan_command(args) -> None:
    """
    Handle --bug-scan command.

    Scans git history for bug-related commits and stores raw bug data.

    Args:
        args: Parsed command line arguments with:
            - bug_mode: "auto-claude" or "project"
    """
    from bug_analysis.scanner import scan_bugs

    mode = getattr(args, "bug_mode", "project") or "project"

    project_dir = get_project_dir(mode)
    bug_wikipedia_dir = get_bug_wikipedia_dir(mode)

    print(f"\nScanning for bugs in: {project_dir}")
    print(f"Output directory: {bug_wikipedia_dir}")
    print(f"Mode: {mode}")
    print()

    total_bugs, new_bugs = scan_bugs(
        project_dir=project_dir,
        bug_wikipedia_dir=bug_wikipedia_dir,
        scan_mode=mode,
    )

    print(f"\nScan complete!")
    print(f"  Total bug-related commits: {total_bugs}")
    print(f"  New bugs processed: {new_bugs}")
    print()


async def handle_bug_categorize_command(args) -> None:
    """
    Handle --bug-categorize command.

    Categorizes uncategorized bugs using Claude Haiku.

    Args:
        args: Parsed command line arguments with:
            - limit: Maximum number of bugs to process (default: 10)
            - dry_run: Preview mode without API calls
            - bug_mode: "auto-claude" or "project"
    """
    from bug_analysis.categorizer import categorize_bugs

    mode = getattr(args, "bug_mode", "project") or "project"
    limit = getattr(args, "limit", 10) or 10
    dry_run = getattr(args, "dry_run", False)

    bug_wikipedia_dir = get_bug_wikipedia_dir(mode)

    print(f"\nCategorizing bugs in: {bug_wikipedia_dir}")
    print(f"Mode: {mode}")
    print(f"Batch limit: {limit}")
    if dry_run:
        print("DRY RUN - No API calls will be made")

    success_count, fail_count = await categorize_bugs(
        bug_wikipedia_dir=bug_wikipedia_dir,
        limit=limit,
        dry_run=dry_run,
    )

    print(f"\nCategorization complete!")
    print(f"  Successfully categorized: {success_count}")
    if fail_count > 0:
        print(f"  Failed to categorize: {fail_count}")
    print()


async def handle_bug_generate_command(args) -> None:
    """
    Handle --bug-wiki command.

    Generates Bug Wikipedia markdown documentation from categorized bugs.

    Args:
        args: Parsed command line arguments with:
            - bug_mode: "auto-claude" or "project"
    """
    from bug_analysis.generator import generate_bug_wikipedia

    mode = getattr(args, "bug_mode", "project") or "project"
    bug_wikipedia_dir = get_bug_wikipedia_dir(mode)

    print(f"\nGenerating Bug Wikipedia from: {bug_wikipedia_dir}")
    print(f"Mode: {mode}")
    print()

    output_files = await generate_bug_wikipedia(bug_wikipedia_dir)

    print(f"\nGeneration complete!")
    print(f"  Output files created: {len(output_files)}")
    for output_file in output_files:
        print(f"    - {output_file}")
    print()


async def handle_bug_detect_command(args) -> None:
    """
    Handle --bug-detect command.

    Detects recurring bug patterns and optionally creates GitHub issues.

    Args:
        args: Parsed command line arguments with:
            - bug_mode: "auto-claude" or "project"
    """
    from bug_analysis.detector import detect_bug_patterns

    mode = getattr(args, "bug_mode", "project") or "project"
    config = load_bug_wikipedia_config()
    bug_wikipedia_dir = get_bug_wikipedia_dir(mode)

    print(f"\nDetecting bug patterns in: {bug_wikipedia_dir}")
    print(f"Mode: {mode}")
    print(f"Pattern threshold: {config.get('pattern_threshold', 3)} bugs")
    print(f"Pattern window: {config.get('pattern_window_days', 30)} days")
    print()

    patterns = await detect_bug_patterns(
        bug_wikipedia_dir=bug_wikipedia_dir,
        threshold=config.get("pattern_threshold", 3),
        window_days=config.get("pattern_window_days", 30),
        auto_create_issues=config.get("auto_create_issues", True),
    )

    print(f"\nPattern detection complete!")
    print(f"  Patterns found: {len(patterns)}")
    for pattern in patterns:
        status_icon = "[ISSUE CREATED]" if pattern.get("github_issue_url") else "[PENDING]"
        print(f"    - {pattern.get('key', 'unknown')}: {pattern.get('bug_count', 0)} bugs {status_icon}")
    print()


async def handle_bug_status_command(args) -> None:
    """
    Handle --bug-status command.

    Shows bug Wikipedia status and statistics.

    Args:
        args: Parsed command line arguments with:
            - bug_mode: "auto-claude" or "project"
    """
    mode = getattr(args, "bug_mode", "project") or "project"
    bug_wikipedia_dir = get_bug_wikipedia_dir(mode)

    if not bug_wikipedia_dir.exists():
        print(f"\nBug Wikipedia not initialized at: {bug_wikipedia_dir}")
        print("\nRun --bug-scan first to initialize.")
        return

    print_bug_status(bug_wikipedia_dir)


async def handle_bug_deep_dive_command(args) -> None:
    """
    Handle --bug-deep-dive <pattern-key> command.

    Performs deep dive root cause analysis on a specific bug pattern
    using Auto-Claude agents.

    Args:
        args: Parsed command line arguments with:
            - pattern_key: Key of the pattern to analyze (e.g., "logic-error-auth")
            - bug_mode: "auto-claude" or "project"
    """
    from bug_analysis.deep_dive import analyze_bug_pattern
    from bug_analysis.models import BugPattern

    pattern_key = getattr(args, "pattern_key", None)
    if not pattern_key:
        print("\nError: Pattern key is required for deep dive analysis.")
        print("Usage: --bug-deep-dive <pattern-key>")
        print("\nRun --bug-detect first to find patterns, then use their keys.")
        return

    mode = getattr(args, "bug_mode", "project") or "project"
    config = load_bug_wikipedia_config()
    bug_wikipedia_dir = get_bug_wikipedia_dir(mode)

    if not config.get("deep_dive_enabled", True):
        print("\nDeep dive analysis is disabled in configuration.")
        print("Set 'deep_dive_enabled': true in bug-wikipedia-config.json to enable.")
        return

    # Load the pattern
    pattern_file = bug_wikipedia_dir / "patterns" / f"pattern-{pattern_key}.json"
    if not pattern_file.exists():
        print(f"\nError: Pattern '{pattern_key}' not found.")
        print(f"Expected file: {pattern_file}")
        print("\nAvailable patterns:")
        patterns_dir = bug_wikipedia_dir / "patterns"
        if patterns_dir.exists():
            for pf in patterns_dir.glob("pattern-*.json"):
                key = pf.stem.replace("pattern-", "")
                print(f"  - {key}")
        else:
            print("  (none - run --bug-detect first)")
        return

    try:
        pattern = BugPattern.load(pattern_file)
    except (json.JSONDecodeError, OSError) as e:
        print(f"\nError loading pattern: {e}")
        return

    print(f"\nDeep dive analysis for pattern: {pattern_key}")
    print(f"  Category: {pattern.category.value}")
    print(f"  Module: {pattern.module}")
    print(f"  Bug count: {pattern.bug_count}")
    print()

    project_dir = get_project_dir(mode)

    result = await analyze_bug_pattern(
        pattern=pattern,
        bug_wikipedia_dir=bug_wikipedia_dir,
        project_dir=project_dir,
    )

    print(f"\nDeep dive complete!")
    if result.get("output_file"):
        print(f"  Analysis saved to: {result['output_file']}")
    if result.get("spec_created"):
        print(f"  Fix spec created: {result['spec_created']}")
    print()


# =============================================================================
# SYNC WRAPPER FUNCTIONS
# =============================================================================


def run_bug_scan_command(args) -> None:
    """Synchronous wrapper for handle_bug_scan_command."""
    asyncio.run(handle_bug_scan_command(args))


def run_bug_categorize_command(args) -> None:
    """Synchronous wrapper for handle_bug_categorize_command."""
    asyncio.run(handle_bug_categorize_command(args))


def run_bug_generate_command(args) -> None:
    """Synchronous wrapper for handle_bug_generate_command."""
    asyncio.run(handle_bug_generate_command(args))


def run_bug_detect_command(args) -> None:
    """Synchronous wrapper for handle_bug_detect_command."""
    asyncio.run(handle_bug_detect_command(args))


def run_bug_status_command(args) -> None:
    """Synchronous wrapper for handle_bug_status_command."""
    asyncio.run(handle_bug_status_command(args))


def run_bug_deep_dive_command(args) -> None:
    """Synchronous wrapper for handle_bug_deep_dive_command."""
    asyncio.run(handle_bug_deep_dive_command(args))
