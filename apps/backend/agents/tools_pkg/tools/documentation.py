"""
Documentation Generation Tools
==============================

Tools for generating documentation automatically during agent builds.
"""

import json
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


def generate_documentation_tool(spec_dir: Path, project_dir: Path) -> list:
    """
    Create documentation generation tools for agents.

    Args:
        spec_dir: Path to the spec directory
        project_dir: Path to the project root

    Returns:
        List of documentation tool functions
    """
    if not SDK_TOOLS_AVAILABLE:
        return []

    tools = []

    # -------------------------------------------------------------------------
    # Tool: generate_docstring
    # -------------------------------------------------------------------------
    @tool(
        "generate_docstring",
        "Generate a docstring or JSDoc comment for a function or class. Use this when you create new functions/classes without documentation.",
        {"file_path": str, "target_name": str, "doc_type": str, "language": str},
    )
    async def generate_docstring(args: dict[str, Any]) -> dict[str, Any]:
        """Generate docstring for a function or class."""
        file_path = args["file_path"]
        target_name = args["target_name"]
        doc_type = args.get("doc_type", "function")  # 'function' or 'class'
        language = args.get("language", "python")  # 'python' or 'typescript'

        valid_doc_types = ["function", "class"]
        valid_languages = ["python", "typescript"]

        if doc_type not in valid_doc_types:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: Invalid doc_type '{doc_type}'. Must be one of: {valid_doc_types}",
                    }
                ]
            }

        if language not in valid_languages:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: Invalid language '{language}'. Must be one of: {valid_languages}",
                    }
                ]
            }

        # Resolve file path relative to project directory
        target_file = project_dir / file_path
        if not target_file.exists():
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: File '{file_path}' not found in project",
                    }
                ]
            }

        try:
            # Import dependencies
            from documentation.generator import DocumentationGenerator
            from documentation.parsers import PythonParser, TypeScriptParser

            # Read file content
            with open(target_file) as f:
                file_content = f.read()

            # Parse file to find target function/class
            if language == "python":
                parser = PythonParser()
                parsed = parser.parse_file(target_file)
            else:
                parser = TypeScriptParser()
                parsed = parser.parse_file(target_file)

            # Find the target element
            target_info = None
            if doc_type == "function":
                target_info = next(
                    (f for f in parsed.get("functions", []) if f.name == target_name),
                    None,
                )
            else:  # class
                target_info = next(
                    (c for c in parsed.get("classes", []) if c.name == target_name),
                    None,
                )

            if not target_info:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error: {doc_type.capitalize()} '{target_name}' not found in {file_path}",
                        }
                    ]
                }

            # Generate documentation
            generator = DocumentationGenerator(project_dir)

            if doc_type == "function":
                docstring = await generator.generate_function_docstring(
                    target_info, file_content, language
                )
            else:  # class
                docstring = await generator.generate_class_docstring(
                    target_info, file_content, language
                )

            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Generated {doc_type} documentation for '{target_name}':\n\n{docstring}",
                    }
                ]
            }

        except Exception as e:
            logger.error(f"Failed to generate docstring for {target_name}: {e}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error generating documentation: {e}",
                    }
                ]
            }

    tools.append(generate_docstring)

    # -------------------------------------------------------------------------
    # Tool: generate_readme_section
    # -------------------------------------------------------------------------
    @tool(
        "generate_readme_section",
        "Generate or update a README section. Use this when adding new features that need documentation.",
        {"section_name": str, "context": str, "existing_content": str},
    )
    async def generate_readme_section(args: dict[str, Any]) -> dict[str, Any]:
        """Generate a README section."""
        section_name = args["section_name"]
        context = args["context"]
        existing_content = args.get("existing_content")

        try:
            from documentation.generator import DocumentationGenerator

            generator = DocumentationGenerator(project_dir)

            # Generate README section
            content = await generator.generate_readme_section(
                section_name, context, existing_content
            )

            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Generated README section '{section_name}':\n\n{content}",
                    }
                ]
            }

        except Exception as e:
            logger.error(f"Failed to generate README section {section_name}: {e}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error generating README section: {e}",
                    }
                ]
            }

    tools.append(generate_readme_section)

    # -------------------------------------------------------------------------
    # Tool: generate_changelog_entry
    # -------------------------------------------------------------------------
    @tool(
        "generate_changelog_entry",
        "Generate a changelog entry from recent changes. Use this when completing a feature to document what changed.",
        {"version": str, "changes_context": str},
    )
    async def generate_changelog_entry(args: dict[str, Any]) -> dict[str, Any]:
        """Generate a changelog entry."""
        version = args["version"]
        changes_context = args["changes_context"]

        try:
            from documentation.generator import DocumentationGenerator
            from documentation.formatters import MarkdownFormatter

            generator = DocumentationGenerator(project_dir)
            formatter = MarkdownFormatter()

            # Generate changelog data
            changes = await generator.generate_changelog_entry(
                version, changes_context
            )

            # Format as markdown
            changelog_md = formatter.format_changelog_entry(version, changes)

            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Generated changelog entry for version {version}:\n\n{changelog_md}",
                    }
                ]
            }

        except Exception as e:
            logger.error(f"Failed to generate changelog entry for {version}: {e}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error generating changelog entry: {e}",
                    }
                ]
            }

    tools.append(generate_changelog_entry)

    # -------------------------------------------------------------------------
    # Tool: update_documentation
    # -------------------------------------------------------------------------
    @tool(
        "update_documentation",
        "Update existing documentation when code changes. Use this to keep docs in sync with code modifications.",
        {"file_path": str, "change_description": str},
    )
    async def update_documentation(args: dict[str, Any]) -> dict[str, Any]:
        """Update documentation for modified code."""
        file_path = args["file_path"]
        change_description = args["change_description"]

        # Resolve file path relative to project directory
        target_file = project_dir / file_path
        if not target_file.exists():
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: File '{file_path}' not found in project",
                    }
                ]
            }

        try:
            # Detect language from file extension
            suffix = target_file.suffix.lower()
            if suffix == ".py":
                language = "python"
            elif suffix in [".ts", ".tsx", ".js", ".jsx"]:
                language = "typescript"
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error: Unsupported file type '{suffix}'. Only .py, .ts, .tsx, .js, .jsx are supported.",
                        }
                    ]
                }

            # Import dependencies
            from documentation.parsers import PythonParser, TypeScriptParser

            # Parse file to get all functions and classes
            if language == "python":
                parser = PythonParser()
            else:
                parser = TypeScriptParser()

            parsed = parser.parse_file(target_file)

            # Count items that need documentation updates
            function_count = len(parsed.get("functions", []))
            class_count = len(parsed.get("classes", []))

            suggestions = []
            if function_count > 0:
                suggestions.append(
                    f"- Found {function_count} function(s) that may need updated docstrings"
                )
            if class_count > 0:
                suggestions.append(
                    f"- Found {class_count} class(es) that may need updated docstrings"
                )

            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"""Documentation update needed for '{file_path}':

Change: {change_description}

Suggestions:
{chr(10).join(suggestions) if suggestions else "- No functions or classes found requiring documentation"}

Use 'generate_docstring' tool to update individual function/class documentation.""",
                    }
                ]
            }

        except Exception as e:
            logger.error(f"Failed to analyze documentation for {file_path}: {e}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error analyzing documentation: {e}",
                    }
                ]
            }

    tools.append(update_documentation)

    return tools
