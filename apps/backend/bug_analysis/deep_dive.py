"""
Deep Dive Analysis - Root Cause Analysis using Auto-Claude Agents
===================================================================

Trigger root cause analysis for recurring bug patterns using the Auto-Claude
planner agent system. Creates structured deep-dive reports with recommendations.

NOT a port from Ralph CLI - this is new Auto-Claude-specific code.
"""

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path

from .models import BugPattern, CategorizedBug

logger = logging.getLogger(__name__)


def format_bug_timeline(bugs: list[CategorizedBug]) -> str:
    """
    Format a list of bugs as a timeline for the analysis prompt.

    Args:
        bugs: List of categorized bugs in the pattern

    Returns:
        Formatted timeline string
    """
    if not bugs:
        return "No bugs in pattern"

    lines = []
    for i, bug in enumerate(bugs[:10], 1):  # Limit to 10 bugs
        date_str = bug.date_fixed.strftime("%Y-%m-%d") if bug.date_fixed else "Unknown"
        message = bug.commit_message[:80] if bug.commit_message else "No message"
        if len(bug.commit_message or "") > 80:
            message += "..."

        files = ", ".join(bug.files_changed[:3]) if bug.files_changed else "No files"
        if len(bug.files_changed) > 3:
            files += f" (+{len(bug.files_changed) - 3} more)"

        lines.append(f"{i}. [{date_str}] {message}")
        lines.append(f"   Files: {files}")
        if bug.error_message:
            error_preview = bug.error_message[:100]
            if len(bug.error_message) > 100:
                error_preview += "..."
            lines.append(f"   Error: {error_preview}")
        lines.append("")

    if len(bugs) > 10:
        lines.append(f"... and {len(bugs) - 10} more bugs")

    return "\n".join(lines)


def build_deep_dive_prompt(pattern: BugPattern) -> str:
    """
    Build the prompt for deep dive root cause analysis.

    Args:
        pattern: Bug pattern with recurring bugs

    Returns:
        Formatted prompt string
    """
    timeline = format_bug_timeline(pattern.bugs)

    # Collect unique files across all bugs
    all_files: set[str] = set()
    for bug in pattern.bugs:
        all_files.update(bug.files_changed or [])

    files_list = sorted(all_files)[:20]  # Limit to 20 files
    files_section = "\n".join(f"- {f}" for f in files_list)
    if len(all_files) > 20:
        files_section += f"\n... and {len(all_files) - 20} more files"

    return f"""Analyze this recurring bug pattern and provide a deep dive root cause analysis.

## Pattern Summary

- **Category**: {pattern.category.value}
- **Module**: {pattern.module}
- **Occurrences**: {pattern.bug_count} bugs in the last 30 days
- **First occurrence**: {pattern.first_occurrence.strftime("%Y-%m-%d")}
- **Latest occurrence**: {pattern.latest_occurrence.strftime("%Y-%m-%d")}

## Bug Timeline

{timeline}

## Affected Files

{files_section}

## Analysis Requirements

Please provide a comprehensive root cause analysis covering:

### 1. Root Cause Analysis
- Why does this bug pattern keep recurring?
- What is the fundamental issue (code structure, missing abstractions, unclear interfaces)?
- Are there architectural weaknesses contributing to this pattern?

### 2. Recommended Refactoring
- What specific code changes would prevent this class of bugs permanently?
- Which files need restructuring?
- Suggest specific refactoring patterns (e.g., Extract Method, Introduce Parameter Object)

### 3. Prevention Strategy
- What tests should be added to catch these bugs earlier?
- What code review checklist items would help?
- Are there linting rules or static analysis that could detect this pattern?

### 4. Implementation Plan
- Prioritized list of changes
- Estimated effort for each change
- Dependencies between changes

## Output Format

Provide your analysis in clear markdown format with the sections above.
Be specific with file names, code patterns, and actionable recommendations.
"""


async def analyze_bug_pattern(pattern: BugPattern, spec_dir: Path) -> Path:
    """
    Trigger root cause analysis using Auto-Claude planner agent.

    This function creates a deep dive analysis for recurring bug patterns,
    using the Auto-Claude agent system to provide thorough root cause
    analysis and prevention recommendations.

    Args:
        pattern: BugPattern with recurring bugs
        spec_dir: Spec directory for agent context

    Returns:
        Path to deep dive output directory containing analysis results

    Raises:
        RuntimeError: If the analysis fails to produce results
    """
    from core.client import create_client
    from agents.session import run_agent_session
    from task_logger import LogPhase

    logger.info(f"Starting deep dive analysis for pattern: {pattern.key}")

    # Create output directory
    output_dir = spec_dir / "bug-wikipedia" / "deep-dive" / pattern.key
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build the analysis prompt
    prompt = build_deep_dive_prompt(pattern)

    # Get project directory (parent of spec_dir)
    project_dir = spec_dir.parent
    if not project_dir.exists():
        project_dir = spec_dir

    # Create a client configured for analysis
    # Using planner agent type as it's designed for analysis tasks
    model = "claude-sonnet-4-5-20250929"  # Use Sonnet for deep analysis

    try:
        client = create_client(
            project_dir=project_dir,
            spec_dir=spec_dir,
            model=model,
            agent_type="planner",  # Planner is suited for analysis
            max_thinking_tokens=5000,  # Enable extended thinking for analysis
        )

        # Run the analysis session
        async with client:
            status, response = await run_agent_session(
                client,
                prompt,
                spec_dir,
                verbose=False,
                phase=LogPhase.PLANNING,
            )

        if status == "error":
            logger.error(f"Deep dive analysis failed for pattern {pattern.key}")
            raise RuntimeError(f"Analysis session failed: {response}")

        # Save results
        analysis_file = output_dir / "root_cause_analysis.md"

        # Build the analysis document
        analysis_content = f"""# Deep Dive: {pattern.key}

## Pattern Information

- **Category**: {pattern.category.value}
- **Module**: {pattern.module}
- **Bug Count**: {pattern.bug_count}
- **Analysis Date**: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}

---

{response}

---

## Appendix: Bug Details

{format_bug_timeline(pattern.bugs)}
"""

        analysis_file.write_text(analysis_content, encoding="utf-8")
        logger.info(f"Deep dive analysis saved to: {analysis_file}")

        # Save pattern metadata
        metadata_file = output_dir / "pattern_metadata.json"
        import json
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump({
                "pattern_key": pattern.key,
                "category": pattern.category.value,
                "module": pattern.module,
                "bug_count": pattern.bug_count,
                "first_occurrence": pattern.first_occurrence.isoformat(),
                "latest_occurrence": pattern.latest_occurrence.isoformat(),
                "analysis_date": datetime.now(timezone.utc).isoformat(),
                "model_used": model,
            }, f, indent=2)

        return output_dir

    except ImportError as e:
        # Handle case where agent system is not available
        logger.warning(f"Agent system not available: {e}")

        # Create a placeholder analysis
        analysis_file = output_dir / "root_cause_analysis.md"
        analysis_content = f"""# Deep Dive: {pattern.key}

## Pattern Information

- **Category**: {pattern.category.value}
- **Module**: {pattern.module}
- **Bug Count**: {pattern.bug_count}
- **Analysis Date**: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}

---

## Analysis Pending

Deep dive analysis requires the Auto-Claude agent system to be available.
Please ensure the following are properly configured:
- core.client module is accessible
- agents.session module is accessible
- A valid Claude API token is configured

### Bug Timeline (for manual review)

{format_bug_timeline(pattern.bugs)}
"""
        analysis_file.write_text(analysis_content, encoding="utf-8")

        return output_dir


async def run_deep_dive_batch(
    patterns: list[BugPattern],
    spec_dir: Path,
    max_concurrent: int = 1,
) -> dict[str, Path]:
    """
    Run deep dive analysis on multiple patterns.

    Args:
        patterns: List of bug patterns to analyze
        spec_dir: Spec directory for agent context
        max_concurrent: Maximum concurrent analyses (default: 1 to avoid rate limits)

    Returns:
        Dict mapping pattern keys to output directories
    """
    results: dict[str, Path] = {}

    # Process patterns with concurrency limit
    semaphore = asyncio.Semaphore(max_concurrent)

    async def analyze_with_limit(pattern: BugPattern) -> tuple[str, Path | None]:
        async with semaphore:
            try:
                output_dir = await analyze_bug_pattern(pattern, spec_dir)
                return pattern.key, output_dir
            except Exception as e:
                logger.error(f"Failed to analyze pattern {pattern.key}: {e}")
                return pattern.key, None

    tasks = [analyze_with_limit(p) for p in patterns]
    completed = await asyncio.gather(*tasks)

    for key, output_dir in completed:
        if output_dir:
            results[key] = output_dir

    return results
