"""
Pattern Extraction Agent Module
=================================

Analyzes completed code to extract reusable patterns automatically.
Uses AI to identify patterns, categorize them, and save to the pattern library.
"""

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from core.client import create_client
from pattern_service.models import CodePattern, PatternCategory, PatternMetadata
from services.pattern_library import PatternLibrary, categorize_pattern
from ui import (
    Icons,
    bold,
    box,
    highlight,
    icon,
    muted,
    print_status,
)

logger = logging.getLogger(__name__)


async def extract_patterns_from_task(
    project_dir: Path,
    spec_dir: Path,
    task_id: str,
    model: str = "claude-sonnet-4",
    verbose: bool = False,
) -> list[CodePattern]:
    """
    Extract reusable patterns from a completed task.

    Analyzes the code changes, identifies patterns, categorizes them,
    and saves them to the pattern library.

    Args:
        project_dir: Root directory for the project
        spec_dir: Directory containing the spec
        task_id: ID of the completed task/spec
        model: Claude model to use for pattern extraction
        verbose: Whether to show detailed output

    Returns:
        List of extracted CodePattern instances
    """
    # Show extraction header
    content = [
        bold(f"{icon(Icons.GEAR)} PATTERN EXTRACTION"),
        "",
        f"Task: {highlight(task_id)}",
        muted("Analyzing code to extract reusable patterns..."),
    ]
    print()
    print(box(content, width=70, style="heavy"))
    print()

    try:
        # Initialize pattern library
        library = PatternLibrary(project_dir)

        # Get files changed in this task
        changed_files = await _get_changed_files(project_dir, spec_dir)
        if not changed_files:
            print_status("No code changes found to analyze", "warning")
            return []

        # Analyze code with AI to extract patterns
        patterns = await _analyze_code_for_patterns(
            project_dir,
            spec_dir,
            task_id,
            changed_files,
            model,
            verbose,
        )

        if not patterns:
            print_status("No reusable patterns identified", "info")
            return []

        # Save patterns to library
        saved_patterns = []
        for pattern in patterns:
            try:
                library.add_pattern(pattern)
                saved_patterns.append(pattern)
                logger.info(f"Saved pattern: {pattern.name} ({pattern.category.value})")
            except ValueError as e:
                logger.warning(f"Pattern already exists: {e}")

        # Save to Graphiti memory for semantic search
        await _save_to_graphiti(spec_dir, project_dir, saved_patterns)

        # Show summary
        if saved_patterns:
            print()
            content = [
                bold(f"{icon(Icons.SUCCESS)} PATTERN EXTRACTION COMPLETE"),
                "",
                f"Extracted patterns: {highlight(str(len(saved_patterns)))}",
                "",
                muted("Patterns saved to library and memory."),
            ]
            print(box(content, width=70, style="heavy"))
            print()

        return saved_patterns

    except Exception as e:
        logger.error(f"Pattern extraction failed: {e}")
        print_status(f"Pattern extraction failed: {e}", "error")
        return []


async def _get_changed_files(project_dir: Path, spec_dir: Path) -> list[dict]:
    """
    Get list of files changed in this task.

    Returns:
        List of dicts with 'path' and 'content' keys
    """
    import subprocess

    try:
        # Get git diff stats to find changed files
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~5..HEAD"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            logger.warning("Could not get git diff")
            return []

        files = []
        for file_path in result.stdout.strip().split("\n"):
            if not file_path:
                continue

            full_path = project_dir / file_path
            if not full_path.exists():
                continue

            # Skip non-code files
            if not _is_code_file(file_path):
                continue

            try:
                content = full_path.read_text(errors="ignore")
                files.append({
                    "path": file_path,
                    "content": content[:5000],  # Limit content size
                })
            except (OSError, UnicodeDecodeError):
                continue

        return files[:10]  # Limit to 10 files

    except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
        logger.warning(f"Failed to get changed files: {e}")
        return []


def _is_code_file(file_path: str) -> bool:
    """Check if file is a code file worth analyzing."""
    code_extensions = {
        ".py", ".js", ".ts", ".tsx", ".jsx",
        ".go", ".rs", ".java", ".cpp", ".c",
        ".rb", ".php", ".swift", ".kt",
    }
    path = Path(file_path)
    return path.suffix in code_extensions


async def _analyze_code_for_patterns(
    project_dir: Path,
    spec_dir: Path,
    task_id: str,
    changed_files: list[dict],
    model: str,
    verbose: bool,
) -> list[CodePattern]:
    """
    Use AI to analyze code and identify reusable patterns.

    Args:
        project_dir: Project root directory
        spec_dir: Spec directory
        task_id: Task ID
        changed_files: List of changed files with content
        model: Claude model to use
        verbose: Show detailed output

    Returns:
        List of CodePattern instances
    """
    from prompts import get_pattern_extraction_prompt

    print_status("Analyzing code with AI...", "progress")

    try:
        # Create SDK client for pattern extraction
        client = create_client(
            project_dir,
            spec_dir,
            model,
            agent_type="planner",  # Use planner permissions (read-only analysis)
            max_thinking_tokens=5000,
        )

        # Generate extraction prompt
        prompt = get_pattern_extraction_prompt(task_id, changed_files)

        # Run analysis session
        async with client:
            response = await client.create_agent_session(
                name="pattern-extraction",
                starting_message=prompt,
            )

        # Parse AI response to extract patterns
        patterns = _parse_pattern_response(response, task_id, changed_files)

        return patterns

    except Exception as e:
        logger.error(f"AI pattern analysis failed: {e}")
        return []


def _parse_pattern_response(
    response: str,
    task_id: str,
    changed_files: list[dict],
) -> list[CodePattern]:
    """
    Parse AI response to extract CodePattern instances.

    Expected format from AI:
    PATTERN: <name>
    DESCRIPTION: <description>
    TYPE: <type>
    CODE:
    ```
    <code example>
    ```
    CONTEXT: <usage context>
    KEYWORDS: <comma-separated keywords>
    ---

    Args:
        response: AI response text
        task_id: Source task ID
        changed_files: Files that were changed

    Returns:
        List of CodePattern instances
    """
    patterns = []
    current_pattern = {}
    in_code_block = False
    code_lines = []

    for line in response.split("\n"):
        line_stripped = line.strip()

        # Parse pattern fields
        if line_stripped.startswith("PATTERN:"):
            if current_pattern:
                # Save previous pattern
                pattern = _create_pattern_from_dict(
                    current_pattern, task_id, changed_files
                )
                if pattern:
                    patterns.append(pattern)
            current_pattern = {"name": line_stripped[8:].strip()}
            code_lines = []

        elif line_stripped.startswith("DESCRIPTION:"):
            current_pattern["description"] = line_stripped[12:].strip()

        elif line_stripped.startswith("TYPE:"):
            current_pattern["pattern_type"] = line_stripped[5:].strip()

        elif line_stripped.startswith("CONTEXT:"):
            current_pattern["usage_context"] = line_stripped[8:].strip()

        elif line_stripped.startswith("KEYWORDS:"):
            keywords_str = line_stripped[9:].strip()
            current_pattern["keywords"] = [
                kw.strip() for kw in keywords_str.split(",")
            ]

        elif line_stripped.startswith("```"):
            if in_code_block:
                # End of code block
                current_pattern["code_example"] = "\n".join(code_lines)
                code_lines = []
            in_code_block = not in_code_block

        elif in_code_block:
            code_lines.append(line)

        elif line_stripped == "---":
            # Pattern separator
            if current_pattern:
                pattern = _create_pattern_from_dict(
                    current_pattern, task_id, changed_files
                )
                if pattern:
                    patterns.append(pattern)
                current_pattern = {}

    # Save last pattern
    if current_pattern:
        pattern = _create_pattern_from_dict(
            current_pattern, task_id, changed_files
        )
        if pattern:
            patterns.append(pattern)

    return patterns


def _create_pattern_from_dict(
    data: dict,
    task_id: str,
    changed_files: list[dict],
) -> Optional[CodePattern]:
    """
    Create a CodePattern instance from parsed data.

    Args:
        data: Pattern data dictionary
        task_id: Source task ID
        changed_files: Files changed in the task

    Returns:
        CodePattern instance or None if data is invalid
    """
    try:
        # Validate required fields
        required = ["name", "description", "pattern_type", "code_example"]
        if not all(field in data for field in required):
            logger.warning(f"Pattern missing required fields: {data.get('name', 'unknown')}")
            return None

        # Generate pattern ID
        pattern_id = f"pattern-{uuid.uuid4().hex[:8]}"

        # Categorize pattern
        category = categorize_pattern(
            pattern_type=data["pattern_type"],
            description=data["description"],
            code_example=data["code_example"],
            keywords=data.get("keywords", []),
            files_involved=[f["path"] for f in changed_files],
        )

        # Create metadata
        now = datetime.utcnow().isoformat()
        metadata = PatternMetadata(
            created_at=now,
            updated_at=now,
            author="auto-claude",
            usage_count=0,
            success_rate=1.0,
            last_used=None,
            source_task_id=task_id,
            tags=data.get("keywords", []),
        )

        # Create pattern
        pattern = CodePattern(
            id=pattern_id,
            name=data["name"],
            description=data["description"],
            category=category,
            pattern_type=data["pattern_type"],
            code_example=data["code_example"],
            usage_context=data.get("usage_context", ""),
            metadata=metadata,
            files_involved=[f["path"] for f in changed_files],
            related_patterns=[],
            keywords=data.get("keywords", []),
        )

        return pattern

    except (KeyError, ValueError) as e:
        logger.error(f"Failed to create pattern: {e}")
        return None


async def _save_to_graphiti(
    spec_dir: Path,
    project_dir: Path,
    patterns: list[CodePattern],
) -> None:
    """
    Save patterns to Graphiti memory for semantic search.

    Args:
        spec_dir: Spec directory
        project_dir: Project directory
        patterns: List of patterns to save
    """
    try:
        from integrations.graphiti.memory import get_graphiti_memory

        memory = get_graphiti_memory(spec_dir, project_dir)
        if not memory:
            logger.debug("Graphiti not enabled, skipping memory save")
            return

        for pattern in patterns:
            await memory.save_code_pattern(
                name=pattern.name,
                description=pattern.description,
                pattern_type=pattern.pattern_type,
                category=pattern.category.value,
                code_example=pattern.code_example,
                usage_context=pattern.usage_context,
                keywords=pattern.keywords,
            )

        logger.info(f"Saved {len(patterns)} patterns to Graphiti memory")

    except Exception as e:
        logger.warning(f"Failed to save patterns to Graphiti: {e}")
