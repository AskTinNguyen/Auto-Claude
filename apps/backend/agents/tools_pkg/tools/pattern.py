"""
Pattern Suggestion Tools
========================

Tools for suggesting relevant code patterns to agents during task planning.
Integrates with the pattern library and Graphiti semantic search.
"""

import logging
from pathlib import Path
from typing import Any

try:
    from claude_agent_sdk import tool

    SDK_TOOLS_AVAILABLE = True
except ImportError:
    SDK_TOOLS_AVAILABLE = False
    tool = None

logger = logging.getLogger(__name__)


def create_pattern_tools(
    spec_dir: Path,
    project_dir: Path,
) -> list:
    """
    Create pattern suggestion tools for the agent.

    Args:
        spec_dir: Directory containing the spec files
        project_dir: Project root directory

    Returns:
        List of pattern tool functions
    """
    if not SDK_TOOLS_AVAILABLE or tool is None:
        return []

    tools = []

    # -------------------------------------------------------------------------
    # Tool: suggest_patterns
    # -------------------------------------------------------------------------
    @tool(
        "suggest_patterns",
        "Search for relevant code patterns based on task description. Use this during planning to find reusable patterns.",
        {"query": str, "category": str, "limit": int},
    )
    async def suggest_patterns(args: dict[str, Any]) -> dict[str, Any]:
        """
        Suggest relevant patterns based on query.

        Args:
            query: Description of what you're trying to implement
            category: Optional category filter (component, api, database, etc.)
            limit: Maximum number of patterns to return (default 5)
        """
        query = args["query"]
        category = args.get("category", "")
        limit = args.get("limit", 5)

        try:
            # Import pattern library
            from services.pattern_library import PatternLibrary, get_popular_patterns

            library = PatternLibrary(project_dir)

            # Try semantic search first (Graphiti)
            patterns = []
            try:
                from memory.patterns import search_patterns_semantic

                patterns = await search_patterns_semantic(
                    spec_dir=spec_dir,
                    project_dir=project_dir,
                    query=query,
                    category=category if category else None,
                    limit=limit,
                )
            except Exception as e:
                logger.debug(f"Semantic search not available: {e}")

            # Fallback to keyword search if semantic search failed
            if not patterns:
                from services.pattern_library import search_patterns_by_keywords

                # Extract keywords from query
                keywords = [w.lower() for w in query.split() if len(w) > 3]
                patterns = search_patterns_by_keywords(
                    project_dir=project_dir,
                    keywords=keywords,
                    limit=limit,
                )

            # Format results
            if not patterns:
                # Suggest popular patterns as fallback
                popular = get_popular_patterns(project_dir, limit=3)
                if popular:
                    result = "No exact matches found. Here are some popular patterns:\n\n"
                    for pattern in popular:
                        result += f"**{pattern.name}** ({pattern.category.value})\n"
                        result += f"{pattern.description}\n\n"
                    return {"content": [{"type": "text", "text": result}]}
                else:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": "No patterns found. Consider adding patterns as you work.",
                            }
                        ]
                    }

            # Format pattern suggestions
            result = f"Found {len(patterns)} relevant pattern(s):\n\n"

            for i, pattern in enumerate(patterns, 1):
                result += f"## {i}. {pattern.name}\n\n"
                result += f"**Category:** {pattern.category.value}\n"
                result += f"**Type:** {pattern.pattern_type}\n\n"
                result += f"{pattern.description}\n\n"

                if pattern.usage_context:
                    result += f"**When to use:** {pattern.usage_context}\n\n"

                if pattern.code_example:
                    # Show abbreviated code example
                    code = pattern.code_example
                    if len(code) > 500:
                        code = code[:500] + "\n\n[... truncated ...]"
                    result += f"**Example:**\n```\n{code}\n```\n\n"

                if pattern.keywords:
                    result += f"**Keywords:** {', '.join(pattern.keywords)}\n\n"

                # Show usage stats
                if pattern.metadata.usage_count > 0:
                    result += (
                        f"**Usage:** {pattern.metadata.usage_count} times, "
                        f"{pattern.metadata.success_rate:.0%} success rate\n\n"
                    )

                result += "---\n\n"

            return {"content": [{"type": "text", "text": result}]}

        except Exception as e:
            logger.error(f"Pattern suggestion failed: {e}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error suggesting patterns: {e}",
                    }
                ]
            }

    tools.append(suggest_patterns)

    # -------------------------------------------------------------------------
    # Tool: search_patterns
    # -------------------------------------------------------------------------
    @tool(
        "search_patterns",
        "Search patterns by keywords or category. Use this to find specific types of patterns.",
        {"keywords": list[str], "category": str},
    )
    async def search_patterns(args: dict[str, Any]) -> dict[str, Any]:
        """
        Search patterns by keywords or category.

        Args:
            keywords: List of keywords to search for
            category: Optional category filter
        """
        keywords = args.get("keywords", [])
        category = args.get("category", "")

        if not keywords and not category:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "Please provide either keywords or category to search.",
                    }
                ]
            }

        try:
            from services.pattern_library import (
                PatternCategory,
                get_patterns_by_category,
                search_patterns_by_keywords,
            )

            patterns = []

            # Search by category if specified
            if category:
                try:
                    cat_enum = PatternCategory(category.lower())
                    patterns = get_patterns_by_category(project_dir, cat_enum)
                except ValueError:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Invalid category: {category}. Valid categories: component, api, database, state-management, error-handling, testing, ui-pattern, integration, workflow, utility",
                            }
                        ]
                    }

            # Search by keywords if specified
            elif keywords:
                patterns = search_patterns_by_keywords(
                    project_dir=project_dir,
                    keywords=keywords,
                    limit=10,
                )

            if not patterns:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": "No patterns found matching your criteria.",
                        }
                    ]
                }

            # Format results
            result = f"Found {len(patterns)} pattern(s):\n\n"
            for pattern in patterns:
                result += f"- **{pattern.name}** ({pattern.category.value}): {pattern.description}\n"

            return {"content": [{"type": "text", "text": result}]}

        except Exception as e:
            logger.error(f"Pattern search failed: {e}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error searching patterns: {e}",
                    }
                ]
            }

    tools.append(search_patterns)

    return tools
