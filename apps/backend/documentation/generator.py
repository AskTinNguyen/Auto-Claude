"""
Documentation Generator with Claude SDK Integration
====================================================

Main documentation generator that uses Claude AI to generate high-quality
documentation for code.

Features:
- AI-powered docstring generation for Python and TypeScript
- Context-aware documentation from code structure
- Multiple output formats (docstrings, JSDoc, Markdown)
- Integration with Claude SDK for natural language generation
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from documentation.parsers import ClassInfo, FunctionInfo

logger = logging.getLogger(__name__)

# System prompt for documentation generation
DOCSTRING_SYSTEM_PROMPT = """You are a technical documentation expert who writes clear, comprehensive docstrings and code documentation.

Rules:
1. Write clear, concise descriptions that explain WHAT the code does and WHY
2. Document all parameters with their types and purpose
3. Document return values and their types
4. Include examples when helpful for understanding
5. Document exceptions/errors that may be raised
6. Follow the project's documentation style (Google-style for Python, JSDoc for TypeScript)
7. Be specific about behavior, not generic
8. Use proper technical terminology
9. Keep descriptions brief but complete

Your output should be ONLY the documentation content (description, parameter descriptions, return description, examples), formatted as JSON."""

README_SYSTEM_PROMPT = """You are a technical writer who creates clear, user-focused README documentation.

Rules:
1. Write for the target audience (developers, end-users, or both)
2. Include practical examples and use cases
3. Explain complex concepts simply
4. Structure content logically with clear headings
5. Focus on what users need to know to use the feature
6. Include setup instructions, usage examples, and troubleshooting if relevant
7. Be concise but thorough
8. Use markdown formatting effectively

Your output should be well-formatted markdown content."""

CHANGELOG_SYSTEM_PROMPT = """You are a technical writer who creates clear changelog entries following Keep a Changelog format.

Rules:
1. Categorize changes: Added, Changed, Deprecated, Removed, Fixed, Security
2. Write from the user's perspective (what changed for them)
3. Be specific about what changed, not how it was implemented
4. Group related changes together
5. Use imperative mood ("Add feature" not "Added feature")
6. Reference issue numbers when relevant
7. Highlight breaking changes clearly

Your output should be categorized changes in JSON format with keys: Added, Changed, Deprecated, Removed, Fixed, Security."""


class DocumentationGenerator:
    """
    Main documentation generator using Claude SDK.

    Generates documentation for code using AI to understand context and intent.
    Integrates with parsers to extract code structure and formatters to produce
    output in various formats.
    """

    def __init__(
        self,
        project_dir: Path,
        doc_style: str | None = None,
    ):
        """
        Initialize the documentation generator.

        Args:
            project_dir: Path to the project directory
            doc_style: Documentation style to use (e.g., 'sphinx', 'jsdoc')
                      If None, will be auto-detected from project
        """
        self.project_dir = project_dir.resolve()
        self.doc_style = doc_style

        # Lazy-import formatters to avoid circular dependencies
        self._formatters_loaded = False
        self._docstring_formatter = None
        self._jsdoc_formatter = None
        self._markdown_formatter = None

    def _load_formatters(self):
        """Lazy-load formatters to avoid circular imports."""
        if not self._formatters_loaded:
            from documentation.formatters import (
                DocstringFormatter,
                JSDocFormatter,
                MarkdownFormatter,
            )

            self._docstring_formatter = DocstringFormatter()
            self._jsdoc_formatter = JSDocFormatter()
            self._markdown_formatter = MarkdownFormatter()
            self._formatters_loaded = True

    async def generate_function_docstring(
        self,
        func_info: FunctionInfo,
        file_content: str | None = None,
        language: Literal["python", "typescript"] = "python",
    ) -> str:
        """
        Generate a docstring for a function using Claude AI.

        Args:
            func_info: Function information from parser
            file_content: Full file content for context (optional)
            language: Programming language ('python' or 'typescript')

        Returns:
            Generated docstring in the appropriate format

        Raises:
            RuntimeError: If Claude SDK call fails
        """
        self._load_formatters()

        # Build context for AI
        context_parts = [
            f"Function: {func_info.name}",
            f"Signature: {func_info.signature}",
        ]

        if func_info.params:
            context_parts.append(f"Parameters: {', '.join(func_info.params)}")

        if func_info.return_type:
            context_parts.append(f"Return type: {func_info.return_type}")

        if func_info.is_async:
            context_parts.append("This is an async function")

        if func_info.is_method:
            context_parts.append("This is a class method")

        if func_info.docstring:
            context_parts.append(f"Existing docstring: {func_info.docstring}")

        # Add surrounding code context if available
        if file_content:
            context_parts.append(
                "\nSurrounding code context:\n"
                + _get_code_context(file_content, func_info.line_number)
            )

        context = "\n".join(context_parts)

        # Build prompt
        prompt = f"""Generate documentation for this {language} function.

{context}

Provide the documentation in JSON format with these keys:
- description: Brief description of what the function does (1-2 sentences)
- param_descriptions: Object mapping parameter names to their descriptions
- return_description: Description of the return value (if applicable)
- examples: Array of code examples showing usage (optional)
- raises: Object mapping exception types to descriptions (if applicable)

Example output:
{{{{
  "description": "Calculates the sum of two numbers",
  "param_descriptions": {{{{
    "a": "First number to add",
    "b": "Second number to add"
  }}}},
  "return_description": "The sum of a and b",
  "examples": ["result = add(5, 3)  # Returns 8"],
  "raises": {{{{}}}}
}}}}

Generate ONLY the JSON, no other text."""

        # Call Claude SDK
        try:
            doc_data = await _call_claude_for_docs(
                prompt, system_prompt=DOCSTRING_SYSTEM_PROMPT
            )

            # Parse response
            if isinstance(doc_data, str):
                # Try to extract JSON from response
                doc_data = _extract_json_from_response(doc_data)

            # Format using appropriate formatter
            if language == "python":
                return self._docstring_formatter.format_function_docstring(
                    func_info,
                    description=doc_data.get("description"),
                    param_descriptions=doc_data.get("param_descriptions"),
                    return_description=doc_data.get("return_description"),
                    examples=doc_data.get("examples"),
                    raises=doc_data.get("raises"),
                )
            else:  # typescript
                return self._jsdoc_formatter.format_function_jsdoc(
                    func_info,
                    description=doc_data.get("description"),
                    param_descriptions=doc_data.get("param_descriptions"),
                    return_description=doc_data.get("return_description"),
                    examples=doc_data.get("examples"),
                    throws=doc_data.get("raises"),
                )

        except Exception as e:
            logger.error(f"Failed to generate docstring for {func_info.name}: {e}")
            raise RuntimeError(
                f"Failed to generate docstring for {func_info.name}"
            ) from e

    async def generate_class_docstring(
        self,
        class_info: ClassInfo,
        file_content: str | None = None,
        language: Literal["python", "typescript"] = "python",
    ) -> str:
        """
        Generate a docstring for a class using Claude AI.

        Args:
            class_info: Class information from parser
            file_content: Full file content for context (optional)
            language: Programming language ('python' or 'typescript')

        Returns:
            Generated docstring in the appropriate format

        Raises:
            RuntimeError: If Claude SDK call fails
        """
        self._load_formatters()

        # Build context for AI
        context_parts = [
            f"Class: {class_info.name}",
        ]

        if class_info.bases:
            context_parts.append(f"Inherits from: {', '.join(class_info.bases)}")

        if class_info.methods:
            method_names = [m.name for m in class_info.methods]
            context_parts.append(f"Methods: {', '.join(method_names)}")

        if class_info.docstring:
            context_parts.append(f"Existing docstring: {class_info.docstring}")

        # Add surrounding code context if available
        if file_content:
            context_parts.append(
                "\nSurrounding code context:\n"
                + _get_code_context(file_content, class_info.line_number)
            )

        context = "\n".join(context_parts)

        # Build prompt
        prompt = f"""Generate documentation for this {language} class.

{context}

Provide the documentation in JSON format with these keys:
- description: Brief description of what the class does and its purpose (1-3 sentences)
- attributes: Object mapping attribute names to their descriptions (if any)
- examples: Array of code examples showing usage (optional)

Example output:
{{{{
  "description": "Manages user authentication and session handling",
  "attributes": {{{{
    "user": "Currently authenticated user object",
    "session": "Active session data"
  }}}},
  "examples": ["auth = AuthManager()\\nauth.login(username, password)"]
}}}}

Generate ONLY the JSON, no other text."""

        # Call Claude SDK
        try:
            doc_data = await _call_claude_for_docs(
                prompt, system_prompt=DOCSTRING_SYSTEM_PROMPT
            )

            # Parse response
            if isinstance(doc_data, str):
                doc_data = _extract_json_from_response(doc_data)

            # Format using appropriate formatter
            if language == "python":
                return self._docstring_formatter.format_class_docstring(
                    class_info,
                    description=doc_data.get("description"),
                    attributes=doc_data.get("attributes"),
                    examples=doc_data.get("examples"),
                )
            else:  # typescript
                return self._jsdoc_formatter.format_class_jsdoc(
                    class_info,
                    description=doc_data.get("description"),
                    examples=doc_data.get("examples"),
                )

        except Exception as e:
            logger.error(f"Failed to generate docstring for {class_info.name}: {e}")
            raise RuntimeError(
                f"Failed to generate docstring for {class_info.name}"
            ) from e

    async def generate_readme_section(
        self,
        section_name: str,
        context: str,
        existing_content: str | None = None,
    ) -> str:
        """
        Generate a README section using Claude AI.

        Args:
            section_name: Name of the section (e.g., "Installation", "Usage")
            context: Context about what should be documented
            existing_content: Existing section content to update (optional)

        Returns:
            Generated markdown content for the section

        Raises:
            RuntimeError: If Claude SDK call fails
        """
        # Build prompt
        prompt = f"""Generate a README section for: {section_name}

Context:
{context}
"""

        if existing_content:
            prompt += f"""

Existing content to update:
{existing_content}

Please update and improve the existing content based on the new context."""
        else:
            prompt += "\n\nGenerate new content for this section."

        prompt += "\n\nProvide well-formatted markdown content."

        # Call Claude SDK
        try:
            content = await _call_claude_for_docs(
                prompt, system_prompt=README_SYSTEM_PROMPT
            )

            if isinstance(content, dict):
                # If Claude returned JSON, extract the content
                content = content.get("content", str(content))

            return content

        except Exception as e:
            logger.error(f"Failed to generate README section {section_name}: {e}")
            raise RuntimeError(
                f"Failed to generate README section {section_name}"
            ) from e

    async def generate_changelog_entry(
        self,
        version: str,
        changes_context: str,
    ) -> dict[str, list[str]]:
        """
        Generate a changelog entry using Claude AI.

        Args:
            version: Version number for this release
            changes_context: Context about changes (commit messages, PR descriptions, etc.)

        Returns:
            Dictionary mapping change categories to lists of changes
            Categories: Added, Changed, Deprecated, Removed, Fixed, Security

        Raises:
            RuntimeError: If Claude SDK call fails
        """
        # Build prompt
        prompt = f"""Generate a changelog entry for version {version}.

Changes to document:
{changes_context}

Analyze the changes and categorize them into:
- Added: New features
- Changed: Changes to existing functionality
- Deprecated: Features marked for removal
- Removed: Removed features
- Fixed: Bug fixes
- Security: Security improvements

Provide the output in JSON format with these category keys, each containing an array of change descriptions.

Example output:
{{{{
  "Added": ["New authentication system with OAuth2 support"],
  "Fixed": ["Memory leak in background worker"],
  "Security": ["Updated dependencies to patch CVE-2024-1234"]
}}}}

Only include categories that have changes. Generate ONLY the JSON, no other text."""

        # Call Claude SDK
        try:
            changes = await _call_claude_for_docs(
                prompt, system_prompt=CHANGELOG_SYSTEM_PROMPT
            )

            # Parse response
            if isinstance(changes, str):
                changes = _extract_json_from_response(changes)

            # Ensure all expected keys exist
            categories = ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"]
            for category in categories:
                if category not in changes:
                    changes[category] = []

            return changes

        except Exception as e:
            logger.error(f"Failed to generate changelog entry for {version}: {e}")
            raise RuntimeError(
                f"Failed to generate changelog entry for {version}"
            ) from e


# =============================================================================
# Helper Functions
# =============================================================================


def _get_code_context(file_content: str, line_number: int, context_lines: int = 10) -> str:
    """
    Extract code context around a specific line.

    Args:
        file_content: Full file content
        line_number: Target line number (1-indexed)
        context_lines: Number of lines to include before and after

    Returns:
        Code snippet with context
    """
    lines = file_content.split("\n")
    start = max(0, line_number - context_lines - 1)
    end = min(len(lines), line_number + context_lines)

    context_lines_list = lines[start:end]
    return "\n".join(context_lines_list)


def _extract_json_from_response(response: str) -> dict:
    """
    Extract JSON from Claude's response, handling markdown code blocks.

    Args:
        response: Raw response from Claude

    Returns:
        Parsed JSON object

    Raises:
        json.JSONDecodeError: If JSON cannot be parsed
    """
    # Remove markdown code blocks if present
    response = response.strip()

    # Try to find JSON in code block
    if "```json" in response:
        start = response.find("```json") + 7
        end = response.find("```", start)
        response = response[start:end].strip()
    elif "```" in response:
        start = response.find("```") + 3
        end = response.find("```", start)
        response = response[start:end].strip()

    # Parse JSON
    return json.loads(response)


async def _call_claude_for_docs(
    prompt: str,
    system_prompt: str = DOCSTRING_SYSTEM_PROMPT,
) -> dict | str:
    """
    Call Claude SDK for documentation generation.

    Reads model/thinking settings from environment variables:
    - UTILITY_MODEL_ID: Full model ID (e.g., "claude-haiku-4-5-20251001")
    - UTILITY_THINKING_BUDGET: Thinking budget tokens (e.g., "1024")

    Args:
        prompt: The prompt to send to Claude
        system_prompt: System prompt defining Claude's role

    Returns:
        Claude's response (parsed JSON or raw string)

    Raises:
        RuntimeError: If authentication fails or API call fails
    """
    from core.auth import ensure_claude_code_oauth_token, get_auth_token
    from core.model_config import get_utility_model_config

    # Ensure authentication
    if not get_auth_token():
        logger.warning("No authentication token found")
        ensure_claude_code_oauth_token()

    if not get_auth_token():
        raise RuntimeError(
            "No authentication token available. Run 'claude setup-token' to configure."
        )

    # Get model configuration
    model_config = get_utility_model_config()
    model = model_config["model"]
    thinking_budget = model_config.get("thinking_budget")

    logger.debug(
        f"Calling Claude for documentation generation (model={model}, thinking_budget={thinking_budget})"
    )

    try:
        # Import Claude Agent SDK
        from claude_agent_sdk import ClaudeSDKClient

        # Create SDK client for simple message call
        # For documentation generation, we don't need full agent sessions,
        # just simple request/response
        client = ClaudeSDKClient(
            sandbox={"enabled": False},  # No sandbox needed for doc generation
        )

        # Build messages
        messages = [
            {
                "role": "user",
                "content": prompt,
            }
        ]

        # Prepare request parameters
        request_params = {
            "model": model,
            "messages": messages,
            "system": system_prompt,
            "max_tokens": 4096,
        }

        # Add thinking budget if configured
        if thinking_budget is not None:
            request_params["thinking"] = {"type": "enabled", "budget_tokens": thinking_budget}

        # Make API call using SDK
        response = await client.messages.create(**request_params)

        # Extract content from response
        content = ""
        for block in response.content:
            if hasattr(block, "type") and block.type == "text":
                content += block.text

        # Try to parse as JSON, fall back to raw string
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return content

    except Exception as e:
        logger.error(f"Claude SDK call failed: {e}", exc_info=True)
        raise RuntimeError(f"Claude SDK call failed: {e}") from e
