"""
Base Documentation Module
==========================

Provides base functionality and utilities for documentation generation.
"""

from __future__ import annotations

import json
from pathlib import Path

# Directories to skip during documentation analysis
SKIP_DIRS = {
    "node_modules",
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    ".env",
    "env",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "target",
    "vendor",
    ".idea",
    ".vscode",
    ".pytest_cache",
    ".mypy_cache",
    "coverage",
    ".coverage",
    "htmlcov",
    "eggs",
    "*.egg-info",
    ".turbo",
    ".cache",
    ".worktrees",  # Skip git worktrees directory
    ".auto-claude",  # Skip auto-claude metadata directory
}

# Documentation style indicators
DOC_STYLE_FILES = {
    "conf.py": "sphinx",  # Sphinx documentation
    "jsdoc.json": "jsdoc",  # JSDoc
    "typedoc.json": "typedoc",  # TypeDoc
    "mkdocs.yml": "mkdocs",  # MkDocs
    "docsify": "docsify",  # Docsify
    "docusaurus.config.js": "docusaurus",  # Docusaurus
}

# File extensions that need docstrings
DOCSTRING_EXTENSIONS = {
    ".py",  # Python
    ".js",  # JavaScript
    ".ts",  # TypeScript
    ".jsx",  # React JavaScript
    ".tsx",  # React TypeScript
    ".java",  # Java
    ".go",  # Go
    ".rs",  # Rust
    ".rb",  # Ruby
    ".php",  # PHP
}


class DocumentationGenerator:
    """Base class for documentation generation."""

    def __init__(self, path: Path):
        """
        Initialize the documentation generator.

        Args:
            path: Path to the project or file to document
        """
        self.path = path.resolve()

    def _exists(self, path: str) -> bool:
        """Check if a file exists relative to the generator's path."""
        return (self.path / path).exists()

    def _read_file(self, path: str) -> str:
        """Read a file relative to the generator's path."""
        try:
            return (self.path / path).read_text()
        except (OSError, UnicodeDecodeError):
            return ""

    def _read_json(self, path: str) -> dict | None:
        """Read and parse a JSON file relative to the generator's path."""
        content = self._read_file(path)
        if content:
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return None
        return None

    def _detect_doc_style(self) -> str | None:
        """
        Detect the documentation style used by the project.

        Returns:
            The detected documentation style (e.g., 'sphinx', 'jsdoc') or None
        """
        for file, style in DOC_STYLE_FILES.items():
            if self._exists(file):
                return style
        return None

    def _should_skip_dir(self, dir_path: Path) -> bool:
        """
        Check if a directory should be skipped during documentation.

        Args:
            dir_path: Path to the directory

        Returns:
            True if the directory should be skipped
        """
        return dir_path.name in SKIP_DIRS

    def _needs_docstring(self, file_path: Path) -> bool:
        """
        Check if a file needs docstring documentation.

        Args:
            file_path: Path to the file

        Returns:
            True if the file extension indicates it needs docstrings
        """
        return file_path.suffix in DOCSTRING_EXTENSIONS
