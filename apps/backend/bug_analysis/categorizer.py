"""
Bug Categorizer - AI-powered categorization using Claude Haiku
===============================================================

Port of Ralph CLI bug-categorizer.js to Python.

Features:
- Uses Claude Haiku to analyze each bug commit
- Input: commit message, diff, error message, files changed
- Output: JSON with primary category, secondary categories, severity, reasoning
- Stores categorization in .auto-claude/bug-wikipedia/categorized/bug-{sha}.json
- Includes prevention tips in output
- Batch processes bugs with rate limiting
"""

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from .models import BugData, CategorizedBug, BugCategory

# Configuration Constants
MAX_RETRIES = 3
RETRY_DELAY_MS = 1000
MAX_DIFF_LENGTH = 500
DEFAULT_BATCH_SIZE = 10
RATE_LIMIT_DELAY = 0.2  # 200ms between API calls
CATEGORIZATION_MODEL = "claude-3-5-haiku-20241022"

# Bug categories with descriptions
BUG_CATEGORIES = [
    {"id": "logic-error", "description": "Wrong algorithm, off-by-one errors, incorrect logic"},
    {"id": "race-condition", "description": "Concurrency issues, race conditions, deadlocks"},
    {
        "id": "requirements-misunderstanding",
        "description": "Misinterpretation of requirements",
    },
    {"id": "integration-issue", "description": "API mismatch, interface incompatibility"},
    {
        "id": "environment-specific",
        "description": "Platform-specific bugs, environment issues",
    },
    {
        "id": "dependency-issue",
        "description": "Third-party library bugs, version conflicts",
    },
    {
        "id": "performance-degradation",
        "description": "Slowness, memory leaks, resource exhaustion",
    },
    {
        "id": "security-vulnerability",
        "description": "Security flaws, injection, authentication issues",
    },
    {"id": "data-corruption", "description": "Data integrity issues, incorrect state"},
    {
        "id": "user-input-validation",
        "description": "Input validation failures, edge cases",
    },
]


# =============================================================================
# PROMPT BUILDING
# =============================================================================


def build_categorization_prompt(bug: BugData) -> str:
    """
    Build the prompt for Claude Haiku categorization.

    Args:
        bug: Raw bug data

    Returns:
        Formatted prompt string
    """
    # Truncate diff to manage token costs
    diff_snippet = bug.diff[:MAX_DIFF_LENGTH]
    if len(bug.diff) > MAX_DIFF_LENGTH:
        diff_snippet += "..."

    if not diff_snippet:
        diff_snippet = "No diff available"

    categories_list = "\n".join(
        f"- {cat['id']}: {cat['description']}" for cat in BUG_CATEGORIES
    )

    files_changed = ", ".join(bug.files_changed) if bug.files_changed else "Unknown"

    return f"""Analyze this bug fix commit and categorize its root cause.

## Bug Information

**Commit Message:** {bug.commit_message or "No message"}
**Files Changed:** {files_changed}
**Error Message:** {bug.error_message or "No error message captured"}
**Diff Snippet:**
```
{diff_snippet}
```

## Available Categories

{categories_list}

## Instructions

1. Analyze the commit message, files changed, and diff to determine the root cause
2. Select a primary_category from the list above
3. Optionally select secondary_categories if multiple apply
4. Determine severity: "critical", "high", "medium", or "low"
5. Explain your reasoning briefly
6. Provide actionable prevention_tips

## Output Format

Respond with ONLY a valid JSON object (no markdown code fences, no explanation outside the JSON):

{{
  "primary_category": "<category-id>",
  "secondary_categories": ["<category-id>", ...],
  "severity": "<critical|high|medium|low>",
  "reasoning": "<1-2 sentence explanation>",
  "prevention_tips": "<actionable tip to prevent this bug type>",
  "similar_bugs": []
}}"""


# =============================================================================
# API INTEGRATION
# =============================================================================


async def categorize_bug_with_haiku(bug: BugData) -> dict | None:
    """
    Call Claude Haiku API for bug categorization with retries.

    Args:
        bug: Raw bug data

    Returns:
        Categorization dictionary or None on failure
    """
    from core.simple_client import create_simple_client

    prompt = build_categorization_prompt(bug)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            client = await create_simple_client()

            response = await client.messages.create(
                model=CATEGORIZATION_MODEL,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract text content
            response_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    response_text += block.text

            # Parse JSON response
            categorization = parse_categorization_response(response_text)
            if categorization:
                return categorization

            print(f"⚠️  Invalid response format on attempt {attempt}")

        except Exception as e:
            print(f"⚠️  API call failed on attempt {attempt}: {e}")

            if attempt < MAX_RETRIES:
                # Exponential backoff
                delay = (RETRY_DELAY_MS / 1000) * (2 ** (attempt - 1))
                await asyncio.sleep(delay)

    return None


def parse_categorization_response(response_text: str) -> dict | None:
    """
    Parse categorization response from Claude.

    Args:
        response_text: Raw response text

    Returns:
        Parsed categorization dict or None
    """
    try:
        # Remove markdown code fences if present
        json_str = response_text.strip()

        if json_str.startswith("```"):
            lines = json_str.split("\n")
            lines.pop(0)  # Remove first line (```json or ```)
            if lines and lines[-1].strip() == "```":
                lines.pop()  # Remove last line (```)
            json_str = "\n".join(lines)

        result = json.loads(json_str)

        # Validate required fields
        if not result.get("primary_category") or not result.get("severity") or not result.get("reasoning"):
            print("⚠️  Missing required fields in categorization response")
            return None

        # Validate primary_category
        valid_categories = [cat["id"] for cat in BUG_CATEGORIES]
        if result["primary_category"] not in valid_categories:
            print(f"⚠️  Invalid primary_category: {result['primary_category']}")
            return None

        # Ensure arrays exist
        result.setdefault("secondary_categories", [])
        result.setdefault("similar_bugs", [])

        return result

    except (json.JSONDecodeError, KeyError) as e:
        print(f"⚠️  Failed to parse categorization response: {e}")
        return None


# =============================================================================
# BUG FILE OPERATIONS
# =============================================================================


def get_uncategorized_bugs(bug_wikipedia_dir: Path) -> list[Path]:
    """
    Get list of raw bug files that haven't been categorized yet.

    Args:
        bug_wikipedia_dir: Bug Wikipedia directory

    Returns:
        List of uncategorized bug file paths
    """
    raw_dir = bug_wikipedia_dir / "raw"
    categorized_dir = bug_wikipedia_dir / "categorized"

    if not raw_dir.exists():
        return []

    # Create categorized directory if needed
    categorized_dir.mkdir(parents=True, exist_ok=True)

    # Get all raw and categorized bug files
    raw_files = set(f.name for f in raw_dir.glob("*.json"))
    categorized_files = set(f.name for f in categorized_dir.glob("*.json"))

    # Filter out already categorized
    uncategorized = raw_files - categorized_files

    return [raw_dir / filename for filename in sorted(uncategorized)]


# =============================================================================
# MAIN CATEGORIZATION FUNCTION
# =============================================================================


async def categorize_bugs(
    bug_wikipedia_dir: Path,
    limit: int = DEFAULT_BATCH_SIZE,
    dry_run: bool = False,
) -> tuple[int, int]:
    """
    Categorize uncategorized bugs.

    Args:
        bug_wikipedia_dir: Bug Wikipedia directory
        limit: Maximum number of bugs to process
        dry_run: Preview mode - don't call API

    Returns:
        Tuple of (success_count, fail_count)
    """
    print("\nℹ️  Starting bug categorizer...\n")

    # Get uncategorized bugs
    uncategorized_paths = get_uncategorized_bugs(bug_wikipedia_dir)

    if not uncategorized_paths:
        print("✅ No uncategorized bugs found")
        return 0, 0

    print(f"ℹ️  Found {len(uncategorized_paths)} uncategorized bugs")

    # Limit to batch size
    bugs_to_process = uncategorized_paths[:limit]
    print(f"ℹ️  Processing {len(bugs_to_process)} bugs this run")

    # Dry run mode
    if dry_run:
        print("\nℹ️  DRY RUN - Would categorize the following bugs:")
        for bug_path in bugs_to_process:
            bug = BugData.load(bug_path)
            message_preview = bug.commit_message[:60] + "..." if bug.commit_message else "No message"
            print(f"  - {bug.id}: {message_preview}")
        print("\nℹ️  Dry run complete. No API calls made.")
        return 0, 0

    # Process bugs
    success_count = 0
    fail_count = 0

    categorized_dir = bug_wikipedia_dir / "categorized"
    categorized_dir.mkdir(parents=True, exist_ok=True)

    print()
    for bug_path in bugs_to_process:
        try:
            raw_bug = BugData.load(bug_path)
        except Exception as e:
            print(f"❌ Failed to load {bug_path.name}: {e}")
            fail_count += 1
            continue

        print(f"ℹ️  Categorizing {raw_bug.id}...")

        categorization = await categorize_bug_with_haiku(raw_bug)

        if categorization:
            # Create categorized bug
            primary_category = BugCategory.from_string(categorization["primary_category"])
            secondary_categories = [
                BugCategory.from_string(cat) for cat in categorization.get("secondary_categories", [])
            ]

            categorized_bug = CategorizedBug.from_bug_data(
                raw_bug,
                primary_category=primary_category,
                secondary_categories=secondary_categories,
                severity=categorization["severity"],
                reasoning=categorization["reasoning"],
                prevention_tips=categorization.get("prevention_tips", ""),
            )

            # Save categorized bug
            categorized_bug.save(categorized_dir)
            print(f"✅ {raw_bug.id} -> {categorization['primary_category']} ({categorization['severity']})")
            success_count += 1
        else:
            print(f"❌ Failed to categorize {raw_bug.id}")
            fail_count += 1

        # Rate limiting
        await asyncio.sleep(RATE_LIMIT_DELAY)

    # Summary
    print("\nℹ️  Categorization complete")
    print(f"✅ Successfully categorized: {success_count}")
    if fail_count > 0:
        print(f"⚠️  Failed to categorize: {fail_count}")

    remaining_count = len(uncategorized_paths) - len(bugs_to_process)
    if remaining_count > 0:
        print(f"ℹ️  Remaining uncategorized: {remaining_count} (run again to process more)")

    print()
    return success_count, fail_count
