"""
Documentation Formatters
========================

Formatters for generating documentation in various styles.

Features:
- Google-style Python docstrings
- JSDoc comments for TypeScript/JavaScript
- Markdown documentation (API docs, README sections)
- Parameter and return type formatting
- Example generation support
"""

from __future__ import annotations

import logging
import textwrap
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from documentation.parsers import ClassInfo, FunctionInfo

logger = logging.getLogger(__name__)


class DocstringFormatter:
    """
    Formatter for Google-style Python docstrings.

    Generates well-formatted docstrings following Google's Python style guide,
    including function/method descriptions, parameters, return values, and examples.
    """

    def __init__(self, indent: int = 4):
        """
        Initialize the docstring formatter.

        Args:
            indent: Number of spaces for indentation (default: 4)
        """
        self.indent = indent

    def format_function_docstring(
        self,
        func_info: FunctionInfo,
        description: str | None = None,
        param_descriptions: dict[str, str] | None = None,
        return_description: str | None = None,
        examples: list[str] | None = None,
        raises: dict[str, str] | None = None,
    ) -> str:
        """
        Format a Google-style docstring for a function.

        Args:
            func_info: Function information from parser
            description: Brief description of what the function does
            param_descriptions: Dictionary mapping parameter names to descriptions
            return_description: Description of return value
            examples: List of example usage strings
            raises: Dictionary mapping exception types to descriptions

        Returns:
            Formatted docstring with proper indentation
        """
        lines = []

        # Add description
        if description:
            lines.append(description.strip())
            lines.append("")

        # Add parameters section
        if func_info.params and param_descriptions:
            lines.append("Args:")
            for param in func_info.params:
                # Extract parameter name (handle type annotations)
                param_name = param.split(":")[0].strip()
                if param_name in param_descriptions:
                    param_desc = param_descriptions[param_name]
                    lines.append(f"    {param_name}: {param_desc}")
            lines.append("")

        # Add return section
        if func_info.return_type and return_description:
            lines.append("Returns:")
            lines.append(f"    {return_description}")
            lines.append("")

        # Add raises section
        if raises:
            lines.append("Raises:")
            for exc_type, exc_desc in raises.items():
                lines.append(f"    {exc_type}: {exc_desc}")
            lines.append("")

        # Add examples section
        if examples:
            lines.append("Examples:")
            for example in examples:
                # Indent example code
                example_lines = example.strip().split("\n")
                for ex_line in example_lines:
                    lines.append(f"    {ex_line}")
            lines.append("")

        # Remove trailing empty line
        while lines and lines[-1] == "":
            lines.pop()

        # Create docstring with triple quotes and indentation
        docstring = '    """\n'
        for line in lines:
            if line:
                docstring += f"    {line}\n"
            else:
                docstring += "\n"
        docstring += '    """'

        return docstring

    def format_class_docstring(
        self,
        class_info: ClassInfo,
        description: str | None = None,
        attributes: dict[str, str] | None = None,
        examples: list[str] | None = None,
    ) -> str:
        """
        Format a Google-style docstring for a class.

        Args:
            class_info: Class information from parser
            description: Brief description of what the class does
            attributes: Dictionary mapping attribute names to descriptions
            examples: List of example usage strings

        Returns:
            Formatted class docstring
        """
        lines = []

        # Add description
        if description:
            lines.append(description.strip())
            lines.append("")

        # Add attributes section
        if attributes:
            lines.append("Attributes:")
            for attr_name, attr_desc in attributes.items():
                lines.append(f"    {attr_name}: {attr_desc}")
            lines.append("")

        # Add examples section
        if examples:
            lines.append("Examples:")
            for example in examples:
                # Indent example code
                example_lines = example.strip().split("\n")
                for ex_line in example_lines:
                    lines.append(f"    {ex_line}")
            lines.append("")

        # Remove trailing empty line
        while lines and lines[-1] == "":
            lines.pop()

        # Create docstring with triple quotes and indentation
        docstring = '    """\n'
        for line in lines:
            if line:
                docstring += f"    {line}\n"
            else:
                docstring += "\n"
        docstring += '    """'

        return docstring


class JSDocFormatter:
    """
    Formatter for JSDoc comments for TypeScript/JavaScript.

    Generates well-formatted JSDoc comments including function/method descriptions,
    parameters, return values, and examples.
    """

    def __init__(self, indent: int = 2):
        """
        Initialize the JSDoc formatter.

        Args:
            indent: Number of spaces for indentation (default: 2)
        """
        self.indent = indent

    def format_function_jsdoc(
        self,
        func_info: FunctionInfo,
        description: str | None = None,
        param_descriptions: dict[str, str] | None = None,
        return_description: str | None = None,
        examples: list[str] | None = None,
        throws: dict[str, str] | None = None,
    ) -> str:
        """
        Format a JSDoc comment for a function.

        Args:
            func_info: Function information from parser
            description: Brief description of what the function does
            param_descriptions: Dictionary mapping parameter names to descriptions
            return_description: Description of return value
            examples: List of example usage strings
            throws: Dictionary mapping exception types to descriptions

        Returns:
            Formatted JSDoc comment with proper indentation
        """
        indent_str = " " * self.indent
        lines = []

        # Start JSDoc comment
        lines.append("/**")

        # Add description
        if description:
            desc_lines = description.strip().split("\n")
            for desc_line in desc_lines:
                lines.append(f" * {desc_line}")

        # Add empty line if there's more content
        if param_descriptions or return_description or examples or throws:
            lines.append(" *")

        # Add parameters
        if func_info.params and param_descriptions:
            for param in func_info.params:
                # Extract parameter name and type
                param_parts = param.split(":")
                param_name = param_parts[0].strip()

                # Try to extract type from TypeScript annotation or use any
                param_type = "any"
                if len(param_parts) > 1:
                    param_type = param_parts[1].strip()

                if param_name in param_descriptions:
                    param_desc = param_descriptions[param_name]
                    lines.append(f" * @param {{{param_type}}} {param_name} - {param_desc}")

        # Add return value
        if return_description:
            return_type = func_info.return_type or "void"
            lines.append(f" * @returns {{{return_type}}} {return_description}")

        # Add throws section
        if throws:
            for exc_type, exc_desc in throws.items():
                lines.append(f" * @throws {{{exc_type}}} {exc_desc}")

        # Add examples
        if examples:
            lines.append(" * @example")
            for example in examples:
                example_lines = example.strip().split("\n")
                for ex_line in example_lines:
                    lines.append(f" * {ex_line}")

        # Close JSDoc comment
        lines.append(" */")

        # Add indentation to all lines
        indented_lines = [indent_str + line for line in lines]

        return "\n".join(indented_lines)

    def format_class_jsdoc(
        self,
        class_info: ClassInfo,
        description: str | None = None,
        examples: list[str] | None = None,
    ) -> str:
        """
        Format a JSDoc comment for a class.

        Args:
            class_info: Class information from parser
            description: Brief description of what the class does
            examples: List of example usage strings

        Returns:
            Formatted JSDoc comment
        """
        indent_str = " " * self.indent
        lines = []

        # Start JSDoc comment
        lines.append("/**")

        # Add description
        if description:
            desc_lines = description.strip().split("\n")
            for desc_line in desc_lines:
                lines.append(f" * {desc_line}")

        # Add empty line if there's more content
        if class_info.bases or examples:
            lines.append(" *")

        # Add extends information
        if class_info.bases:
            for base in class_info.bases:
                lines.append(f" * @extends {base}")

        # Add examples
        if examples:
            lines.append(" * @example")
            for example in examples:
                example_lines = example.strip().split("\n")
                for ex_line in example_lines:
                    lines.append(f" * {ex_line}")

        # Close JSDoc comment
        lines.append(" */")

        # Add indentation to all lines
        indented_lines = [indent_str + line for line in lines]

        return "\n".join(indented_lines)

    def format_interface_jsdoc(
        self,
        interface_name: str,
        description: str | None = None,
        examples: list[str] | None = None,
    ) -> str:
        """
        Format a JSDoc comment for an interface.

        Args:
            interface_name: Name of the interface
            description: Brief description of what the interface represents
            examples: List of example usage strings

        Returns:
            Formatted JSDoc comment
        """
        indent_str = " " * self.indent
        lines = []

        # Start JSDoc comment
        lines.append("/**")

        # Add description
        if description:
            desc_lines = description.strip().split("\n")
            for desc_line in desc_lines:
                lines.append(f" * {desc_line}")

        # Add empty line if there's more content
        if examples:
            lines.append(" *")

        # Add examples
        if examples:
            lines.append(" * @example")
            for example in examples:
                example_lines = example.strip().split("\n")
                for ex_line in example_lines:
                    lines.append(f" * {ex_line}")

        # Close JSDoc comment
        lines.append(" */")

        # Add indentation to all lines
        indented_lines = [indent_str + line for line in lines]

        return "\n".join(indented_lines)


class MarkdownFormatter:
    """
    Formatter for Markdown documentation.

    Generates markdown documentation for API references, README sections,
    and changelog entries.
    """

    def format_function_markdown(
        self,
        func_info: FunctionInfo,
        description: str | None = None,
        param_descriptions: dict[str, str] | None = None,
        return_description: str | None = None,
        examples: list[str] | None = None,
    ) -> str:
        """
        Format a function as Markdown documentation.

        Args:
            func_info: Function information from parser
            description: Brief description of what the function does
            param_descriptions: Dictionary mapping parameter names to descriptions
            return_description: Description of return value
            examples: List of example usage strings

        Returns:
            Formatted markdown string
        """
        lines = []

        # Function signature as header
        lines.append(f"### `{func_info.name}()`")
        lines.append("")

        # Add description
        if description:
            lines.append(description.strip())
            lines.append("")

        # Add signature code block
        lines.append("```python" if not func_info.is_method else "```typescript")
        lines.append(func_info.signature)
        lines.append("```")
        lines.append("")

        # Add parameters table
        if func_info.params and param_descriptions:
            lines.append("**Parameters:**")
            lines.append("")
            lines.append("| Parameter | Type | Description |")
            lines.append("|-----------|------|-------------|")
            for param in func_info.params:
                # Extract parameter name and type
                param_parts = param.split(":")
                param_name = param_parts[0].strip()
                param_type = param_parts[1].strip() if len(param_parts) > 1 else "any"

                if param_name in param_descriptions:
                    param_desc = param_descriptions[param_name]
                    lines.append(f"| `{param_name}` | `{param_type}` | {param_desc} |")
            lines.append("")

        # Add return value
        if func_info.return_type and return_description:
            lines.append("**Returns:**")
            lines.append("")
            lines.append(f"- `{func_info.return_type}`: {return_description}")
            lines.append("")

        # Add examples
        if examples:
            lines.append("**Examples:**")
            lines.append("")
            for example in examples:
                lines.append("```python" if not func_info.is_method else "```typescript")
                lines.append(example.strip())
                lines.append("```")
                lines.append("")

        return "\n".join(lines)

    def format_class_markdown(
        self,
        class_info: ClassInfo,
        description: str | None = None,
        attributes: dict[str, str] | None = None,
        examples: list[str] | None = None,
    ) -> str:
        """
        Format a class as Markdown documentation.

        Args:
            class_info: Class information from parser
            description: Brief description of what the class does
            attributes: Dictionary mapping attribute names to descriptions
            examples: List of example usage strings

        Returns:
            Formatted markdown string
        """
        lines = []

        # Class name as header
        lines.append(f"## `{class_info.name}`")
        lines.append("")

        # Add description
        if description:
            lines.append(description.strip())
            lines.append("")

        # Add inheritance info
        if class_info.bases:
            lines.append(f"**Inherits from:** `{', '.join(class_info.bases)}`")
            lines.append("")

        # Add attributes table
        if attributes:
            lines.append("**Attributes:**")
            lines.append("")
            lines.append("| Attribute | Description |")
            lines.append("|-----------|-------------|")
            for attr_name, attr_desc in attributes.items():
                lines.append(f"| `{attr_name}` | {attr_desc} |")
            lines.append("")

        # Add methods section
        if class_info.methods:
            lines.append("**Methods:**")
            lines.append("")
            for method in class_info.methods:
                lines.append(f"- [`{method.name}()`](#{method.name.lower()})")
            lines.append("")

        # Add examples
        if examples:
            lines.append("**Examples:**")
            lines.append("")
            for example in examples:
                lines.append("```python")
                lines.append(example.strip())
                lines.append("```")
                lines.append("")

        return "\n".join(lines)

    def format_module_markdown(
        self,
        module_name: str,
        description: str | None = None,
        functions: list[FunctionInfo] | None = None,
        classes: list[ClassInfo] | None = None,
    ) -> str:
        """
        Format a module overview as Markdown documentation.

        Args:
            module_name: Name of the module
            description: Brief description of the module
            functions: List of functions in the module
            classes: List of classes in the module

        Returns:
            Formatted markdown string
        """
        lines = []

        # Module name as header
        lines.append(f"# {module_name}")
        lines.append("")

        # Add description
        if description:
            lines.append(description.strip())
            lines.append("")

        # Add table of contents
        if functions or classes:
            lines.append("## Table of Contents")
            lines.append("")

            if classes:
                lines.append("### Classes")
                lines.append("")
                for cls in classes:
                    lines.append(f"- [`{cls.name}`](#{cls.name.lower()})")
                lines.append("")

            if functions:
                lines.append("### Functions")
                lines.append("")
                for func in functions:
                    lines.append(f"- [`{func.name}()`](#{func.name.lower()})")
                lines.append("")

        return "\n".join(lines)

    def format_changelog_entry(
        self,
        version: str,
        date: str,
        changes: dict[str, list[str]],
    ) -> str:
        """
        Format a changelog entry in Keep a Changelog format.

        Args:
            version: Version number (e.g., "1.0.0")
            date: Release date (e.g., "2024-01-18")
            changes: Dictionary mapping change categories to lists of changes
                    Categories: Added, Changed, Deprecated, Removed, Fixed, Security

        Returns:
            Formatted changelog entry
        """
        lines = []

        # Version header
        lines.append(f"## [{version}] - {date}")
        lines.append("")

        # Change categories in order
        categories = ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"]

        for category in categories:
            if category in changes and changes[category]:
                lines.append(f"### {category}")
                lines.append("")
                for change in changes[category]:
                    lines.append(f"- {change}")
                lines.append("")

        return "\n".join(lines)
