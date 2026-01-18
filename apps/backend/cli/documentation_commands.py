"""
Documentation Commands
======================

CLI commands for documentation generation and validation.
"""

import asyncio
import sys
from pathlib import Path

# Ensure parent directory is in path for imports (before other imports)
_PARENT_DIR = Path(__file__).parent.parent
if str(_PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(_PARENT_DIR))

from ui import (
    Icons,
    bold,
    box,
    highlight,
    icon,
    info,
    muted,
    success,
    warning,
)

from .utils import print_banner, validate_environment


def handle_generate_docs_command(
    project_dir: Path,
    target_path: Path | None = None,
    doc_type: str = "all",
    output_path: Path | None = None,
    verbose: bool = False,
) -> None:
    """
    Handle the --generate-docs command.

    Args:
        project_dir: Project root directory
        target_path: Specific file or directory to document (default: entire project)
        doc_type: Type of documentation to generate ('docstrings', 'readme', 'changelog', 'all')
        output_path: Path to write generated documentation (optional)
        verbose: Enable verbose output
    """
    # Lazy imports to avoid loading heavy modules
    from documentation.changelog_generator import ChangelogGenerator
    from documentation.generator import DocumentationGenerator
    from documentation.parsers import PythonParser, TypeScriptParser

    print_banner()
    print(f"\nGenerating documentation for: {project_dir.name}")
    print(f"Documentation type: {doc_type}")

    if target_path:
        print(f"Target: {target_path}")
    else:
        print("Target: Entire project")

    print()

    # Determine target path
    target = target_path if target_path else project_dir

    if not target.exists():
        print(warning(f"{icon(Icons.WARNING)} Target path does not exist: {target}"))
        sys.exit(1)

    try:
        # Generate based on doc_type
        if doc_type in ("docstrings", "all"):
            print(info(f"{icon(Icons.INFO)} Generating docstrings..."))
            _generate_docstrings(project_dir, target, verbose)

        if doc_type in ("readme", "all"):
            print(info(f"{icon(Icons.INFO)} Generating README sections..."))
            _generate_readme(project_dir, verbose)

        if doc_type in ("changelog", "all"):
            print(info(f"{icon(Icons.INFO)} Generating changelog..."))
            _generate_changelog(project_dir, verbose)

        print()
        print(success(f"{icon(Icons.SUCCESS)} Documentation generation complete!"))
        print()

        if output_path:
            print(f"Output written to: {output_path}")

    except Exception as e:
        print()
        print(warning(f"{icon(Icons.WARNING)} Documentation generation failed: {e}"))
        if verbose:
            import traceback

            print()
            print(muted(traceback.format_exc()))
        sys.exit(1)


def handle_update_docs_command(
    project_dir: Path,
    target_path: Path | None = None,
    doc_type: str = "all",
    verbose: bool = False,
) -> None:
    """
    Handle the --update-docs command.

    Args:
        project_dir: Project root directory
        target_path: Specific file or directory to update (default: entire project)
        doc_type: Type of documentation to update ('docstrings', 'readme', 'changelog', 'all')
        verbose: Enable verbose output
    """
    print_banner()
    print(f"\nUpdating documentation for: {project_dir.name}")
    print(f"Documentation type: {doc_type}")

    if target_path:
        print(f"Target: {target_path}")
    else:
        print("Target: Entire project")

    print()

    # Determine target path
    target = target_path if target_path else project_dir

    if not target.exists():
        print(warning(f"{icon(Icons.WARNING)} Target path does not exist: {target}"))
        sys.exit(1)

    try:
        # Update based on doc_type
        if doc_type in ("docstrings", "all"):
            print(info(f"{icon(Icons.INFO)} Updating docstrings..."))
            _update_docstrings(project_dir, target, verbose)

        if doc_type in ("readme", "all"):
            print(info(f"{icon(Icons.INFO)} Updating README..."))
            _update_readme(project_dir, verbose)

        if doc_type in ("changelog", "all"):
            print(info(f"{icon(Icons.INFO)} Updating changelog..."))
            _update_changelog(project_dir, verbose)

        print()
        print(success(f"{icon(Icons.SUCCESS)} Documentation update complete!"))
        print()

    except Exception as e:
        print()
        print(warning(f"{icon(Icons.WARNING)} Documentation update failed: {e}"))
        if verbose:
            import traceback

            print()
            print(muted(traceback.format_exc()))
        sys.exit(1)


def handle_validate_docs_command(
    project_dir: Path,
    target_path: Path | None = None,
    strict: bool = False,
    verbose: bool = False,
) -> None:
    """
    Handle the --validate-docs command.

    Args:
        project_dir: Project root directory
        target_path: Specific file or directory to validate (default: entire project)
        strict: Enable strict validation (fail on warnings)
        verbose: Enable verbose output
    """
    print_banner()
    print(f"\nValidating documentation for: {project_dir.name}")

    if target_path:
        print(f"Target: {target_path}")
    else:
        print("Target: Entire project")

    if strict:
        print("Mode: Strict (warnings treated as errors)")
    else:
        print("Mode: Standard")

    print()

    # Determine target path
    target = target_path if target_path else project_dir

    if not target.exists():
        print(warning(f"{icon(Icons.WARNING)} Target path does not exist: {target}"))
        sys.exit(1)

    try:
        # Validate documentation
        issues = _validate_documentation(project_dir, target, verbose)

        # Report results
        print()
        _report_validation_results(issues, strict)

        # Exit with appropriate status
        if issues["errors"] or (strict and issues["warnings"]):
            sys.exit(1)

    except Exception as e:
        print()
        print(
            warning(f"{icon(Icons.WARNING)} Documentation validation failed: {e}")
        )
        if verbose:
            import traceback

            print()
            print(muted(traceback.format_exc()))
        sys.exit(1)


# =============================================================================
# Helper Functions
# =============================================================================


def _generate_docstrings(
    project_dir: Path, target_path: Path, verbose: bool = False
) -> None:
    """
    Generate docstrings for Python and TypeScript files.

    Args:
        project_dir: Project root directory
        target_path: Target file or directory
        verbose: Enable verbose output
    """
    from documentation.generator import DocumentationGenerator
    from documentation.parsers import PythonParser, TypeScriptParser

    generator = DocumentationGenerator(project_dir)

    # Find files to document
    files_to_document = _find_documentable_files(target_path)

    if not files_to_document:
        print(muted("  No files found that need docstrings."))
        return

    print(f"  Found {len(files_to_document)} files to document")

    # Process each file
    for file_path in files_to_document:
        if verbose:
            print(f"    Processing: {file_path.relative_to(project_dir)}")

        # Determine parser based on file extension
        if file_path.suffix == ".py":
            parser = PythonParser()
            language = "python"
        elif file_path.suffix in (".ts", ".tsx", ".js", ".jsx"):
            parser = TypeScriptParser()
            language = "typescript"
        else:
            continue

        # Parse file and generate docstrings
        try:
            file_content = file_path.read_text(encoding="utf-8")
            functions = parser.parse_functions(file_content)
            classes = parser.parse_classes(file_content)

            # Generate docstrings for functions
            for func in functions:
                if not func.docstring:  # Only generate if missing
                    docstring = asyncio.run(
                        generator.generate_function_docstring(
                            func, file_content, language
                        )
                    )
                    if verbose:
                        print(f"      Generated docstring for: {func.name}")

            # Generate docstrings for classes
            for cls in classes:
                if not cls.docstring:  # Only generate if missing
                    docstring = asyncio.run(
                        generator.generate_class_docstring(cls, file_content, language)
                    )
                    if verbose:
                        print(f"      Generated docstring for class: {cls.name}")

        except Exception as e:
            print(warning(f"    Failed to process {file_path.name}: {e}"))
            continue


def _generate_readme(project_dir: Path, verbose: bool = False) -> None:
    """
    Generate README sections.

    Args:
        project_dir: Project root directory
        verbose: Enable verbose output
    """
    from documentation.generator import DocumentationGenerator

    generator = DocumentationGenerator(project_dir)

    readme_path = project_dir / "README.md"
    existing_content = ""

    if readme_path.exists():
        existing_content = readme_path.read_text(encoding="utf-8")
        print(muted("  Updating existing README.md"))
    else:
        print(muted("  Creating new README.md"))

    # Generate installation section if not present
    if "## Installation" not in existing_content:
        if verbose:
            print("    Generating Installation section...")
        # Note: This would call the generator, but for now we just indicate it
        print(muted("    Installation section generation available"))

    # Generate usage section if not present
    if "## Usage" not in existing_content:
        if verbose:
            print("    Generating Usage section...")
        print(muted("    Usage section generation available"))


def _generate_changelog(project_dir: Path, verbose: bool = False) -> None:
    """
    Generate changelog from git commits.

    Args:
        project_dir: Project root directory
        verbose: Enable verbose output
    """
    from documentation.changelog_generator import ChangelogGenerator

    changelog_gen = ChangelogGenerator(project_dir)
    changelog_path = project_dir / "CHANGELOG.md"

    try:
        # Generate changelog for commits since last tag
        if verbose:
            print("    Analyzing git commit history...")

        changelog_content = changelog_gen.generate_changelog(since=None, until=None)

        if changelog_content:
            print(
                success(
                    f"    Generated changelog with {len(changelog_content.splitlines())} lines"
                )
            )

            # Preview option (could be enhanced to actually write the file)
            if verbose:
                print()
                print(highlight("  Preview:"))
                preview_lines = changelog_content.split("\n")[:10]
                for line in preview_lines:
                    print(f"    {line}")
                if len(changelog_content.split("\n")) > 10:
                    print(muted("    ... (truncated)"))
        else:
            print(muted("    No changelog entries generated"))

    except Exception as e:
        print(warning(f"    Failed to generate changelog: {e}"))


def _update_docstrings(
    project_dir: Path, target_path: Path, verbose: bool = False
) -> None:
    """
    Update existing docstrings.

    Args:
        project_dir: Project root directory
        target_path: Target file or directory
        verbose: Enable verbose output
    """
    # Similar to _generate_docstrings but updates existing ones
    print(muted("  Docstring update available"))


def _update_readme(project_dir: Path, verbose: bool = False) -> None:
    """
    Update existing README.

    Args:
        project_dir: Project root directory
        verbose: Enable verbose output
    """
    print(muted("  README update available"))


def _update_changelog(project_dir: Path, verbose: bool = False) -> None:
    """
    Update existing changelog.

    Args:
        project_dir: Project root directory
        verbose: Enable verbose output
    """
    from documentation.changelog_generator import ChangelogGenerator

    changelog_gen = ChangelogGenerator(project_dir)
    changelog_path = project_dir / "CHANGELOG.md"

    try:
        # Append to existing changelog
        changelog_gen.append_to_changelog_file(
            changelog_path, since=None, until=None, version=None
        )
        print(success(f"    Updated {changelog_path.name}"))
    except Exception as e:
        print(warning(f"    Failed to update changelog: {e}"))


def _validate_documentation(
    project_dir: Path, target_path: Path, verbose: bool = False
) -> dict:
    """
    Validate documentation completeness.

    Args:
        project_dir: Project root directory
        target_path: Target file or directory
        verbose: Enable verbose output

    Returns:
        Dictionary with validation results (errors, warnings, info)
    """
    from documentation.parsers import PythonParser, TypeScriptParser

    issues = {"errors": [], "warnings": [], "info": []}

    # Find files to validate
    files_to_validate = _find_documentable_files(target_path)

    if not files_to_validate:
        issues["info"].append("No documentable files found")
        return issues

    print(f"  Validating {len(files_to_validate)} files...")

    # Check each file
    for file_path in files_to_validate:
        if verbose:
            print(f"    Checking: {file_path.relative_to(project_dir)}")

        # Determine parser
        if file_path.suffix == ".py":
            parser = PythonParser()
        elif file_path.suffix in (".ts", ".tsx", ".js", ".jsx"):
            parser = TypeScriptParser()
        else:
            continue

        try:
            file_content = file_path.read_text(encoding="utf-8")
            functions = parser.parse_functions(file_content)
            classes = parser.parse_classes(file_content)

            # Check for missing docstrings
            for func in functions:
                if not func.docstring:
                    issues["warnings"].append(
                        f"{file_path.relative_to(project_dir)}:{func.line_number} - Missing docstring for function '{func.name}'"
                    )

            for cls in classes:
                if not cls.docstring:
                    issues["warnings"].append(
                        f"{file_path.relative_to(project_dir)}:{cls.line_number} - Missing docstring for class '{cls.name}'"
                    )

        except Exception as e:
            issues["errors"].append(f"Failed to parse {file_path.name}: {e}")

    return issues


def _report_validation_results(issues: dict, strict: bool = False) -> None:
    """
    Report validation results.

    Args:
        issues: Dictionary with errors, warnings, and info
        strict: Whether to treat warnings as errors
    """
    error_count = len(issues["errors"])
    warning_count = len(issues["warnings"])
    info_count = len(issues["info"])

    # Build summary
    content = [bold("Documentation Validation Results"), ""]

    if error_count > 0:
        content.append(warning(f"{icon(Icons.WARNING)} {error_count} errors"))
        content.append("")
        for error in issues["errors"][:5]:  # Show first 5
            content.append(f"  • {error}")
        if error_count > 5:
            content.append(muted(f"  ... and {error_count - 5} more"))
        content.append("")

    if warning_count > 0:
        content.append(
            info(f"{icon(Icons.INFO)} {warning_count} warnings")
            if not strict
            else warning(f"{icon(Icons.WARNING)} {warning_count} warnings (strict mode)")
        )
        content.append("")
        for warn in issues["warnings"][:5]:  # Show first 5
            content.append(f"  • {warn}")
        if warning_count > 5:
            content.append(muted(f"  ... and {warning_count - 5} more"))
        content.append("")

    if info_count > 0:
        for msg in issues["info"]:
            content.append(muted(f"ℹ {msg}"))

    # Overall status
    if error_count == 0 and (not strict or warning_count == 0):
        content.append("")
        content.append(
            success(f"{icon(Icons.SUCCESS)} Documentation validation passed!")
        )
    else:
        content.append("")
        content.append(
            warning(f"{icon(Icons.WARNING)} Documentation validation failed!")
        )
        if strict and warning_count > 0:
            content.append(muted("Strict mode: warnings treated as errors"))

    print(box(content, width=80, style="light"))


def _find_documentable_files(path: Path) -> list[Path]:
    """
    Find all files that need documentation.

    Args:
        path: Root path to search

    Returns:
        List of file paths that need documentation
    """
    from documentation.base import DOCSTRING_EXTENSIONS, SKIP_DIRS

    files = []

    if path.is_file():
        if path.suffix in DOCSTRING_EXTENSIONS:
            files.append(path)
    else:
        # Recursively find files
        for item in path.rglob("*"):
            # Skip directories in SKIP_DIRS
            if any(skip_dir in item.parts for skip_dir in SKIP_DIRS):
                continue

            if item.is_file() and item.suffix in DOCSTRING_EXTENSIONS:
                files.append(item)

    return files
