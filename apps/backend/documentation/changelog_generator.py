"""
Changelog Generator from Git Commits
======================================

Generates changelog entries from git commit history.

Features:
- Parses conventional commit messages (feat/fix/refactor/etc)
- Groups commits by type for organized changelog
- Extracts breaking changes and GitHub issue references
- Supports version tagging and date ranges
- Markdown formatting for CHANGELOG.md
"""

from __future__ import annotations

import logging
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Conventional commit type mapping to changelog sections
COMMIT_TYPE_SECTIONS = {
    "feat": "✨ Features",
    "fix": "🐛 Bug Fixes",
    "refactor": "♻️ Refactoring",
    "perf": "⚡ Performance",
    "docs": "📝 Documentation",
    "test": "✅ Tests",
    "build": "🏗️ Build System",
    "ci": "👷 CI/CD",
    "chore": "🔧 Chore",
    "style": "💄 Style",
    "security": "🔒 Security",
}

# Order of sections in the changelog (highest priority first)
SECTION_ORDER = [
    "security",
    "feat",
    "fix",
    "perf",
    "refactor",
    "docs",
    "test",
    "build",
    "ci",
    "style",
    "chore",
]


@dataclass
class CommitInfo:
    """Information about a single commit."""

    hash: str
    type: str
    scope: str | None
    description: str
    body: str | None
    breaking: bool
    issues: list[int]
    author: str
    date: datetime


class ChangelogGenerator:
    """
    Generator for creating changelog entries from git commit history.

    Parses git log output, groups commits by type using conventional commits
    format, and generates formatted markdown changelog.
    """

    # Regex for parsing conventional commit messages
    CONVENTIONAL_COMMIT_PATTERN = re.compile(
        r"^(?P<type>\w+)(?:\((?P<scope>[^)]+)\))?(?P<breaking>!)?: (?P<description>.+)$"
    )

    # Regex for finding GitHub issue references
    ISSUE_PATTERN = re.compile(r"#(\d+)")

    # Regex for finding breaking changes in commit body
    BREAKING_CHANGE_PATTERN = re.compile(
        r"BREAKING CHANGE:\s*(.+)", re.IGNORECASE | re.MULTILINE
    )

    def __init__(self, repo_path: Path):
        """
        Initialize the changelog generator.

        Args:
            repo_path: Path to the git repository
        """
        self.repo_path = repo_path.resolve()

    def generate_changelog(
        self,
        since: str | None = None,
        until: str | None = None,
        version: str | None = None,
    ) -> str:
        """
        Generate a changelog from git commits.

        Args:
            since: Start reference (tag, commit hash, or date like "2024-01-01")
            until: End reference (tag, commit hash, or date)
            version: Version number to use in the changelog header

        Returns:
            Formatted markdown changelog

        Raises:
            subprocess.CalledProcessError: If git command fails
        """
        commits = self._get_commits(since, until)

        if not commits:
            logger.warning("No commits found for changelog generation")
            return ""

        # Group commits by type
        grouped_commits = self._group_commits_by_type(commits)

        # Generate markdown
        changelog = self._format_changelog(grouped_commits, version)

        return changelog

    def _get_commits(
        self, since: str | None = None, until: str | None = None
    ) -> list[CommitInfo]:
        """
        Retrieve commits from git log.

        Args:
            since: Start reference
            until: End reference

        Returns:
            List of parsed commit information
        """
        # Build git log command
        cmd = [
            "git",
            "log",
            "--format=%H%n%s%n%b%n%an%n%aI%n---COMMIT-END---",
        ]

        # Add range if specified
        if since and until:
            cmd.append(f"{since}..{until}")
        elif since:
            cmd.append(f"{since}..HEAD")
        elif until:
            cmd.append(until)

        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"Git log command failed: {e}")
            logger.error(f"stderr: {e.stderr}")
            raise

        # Parse output
        commits = []
        raw_commits = result.stdout.split("---COMMIT-END---")

        for raw_commit in raw_commits:
            raw_commit = raw_commit.strip()
            if not raw_commit:
                continue

            try:
                commit_info = self._parse_commit(raw_commit)
                if commit_info:
                    commits.append(commit_info)
            except Exception as e:
                logger.warning(f"Failed to parse commit: {e}")
                continue

        logger.info(f"Parsed {len(commits)} commits for changelog")
        return commits

    def _parse_commit(self, raw_commit: str) -> CommitInfo | None:
        """
        Parse a raw git commit into a CommitInfo object.

        Args:
            raw_commit: Raw commit text from git log

        Returns:
            Parsed commit info or None if invalid
        """
        lines = raw_commit.split("\n")
        if len(lines) < 5:
            return None

        commit_hash = lines[0].strip()
        subject = lines[1].strip()
        author = lines[-2].strip()
        date_str = lines[-1].strip()

        # Parse date
        try:
            date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, IndexError):
            logger.warning(f"Could not parse date: {date_str}")
            date = datetime.now()

        # Body is everything between subject and author (excluding empty lines)
        body_lines = [line for line in lines[2:-2] if line.strip()]
        body = "\n".join(body_lines) if body_lines else None

        # Parse conventional commit format
        match = self.CONVENTIONAL_COMMIT_PATTERN.match(subject)
        if not match:
            # Not a conventional commit - treat as "chore"
            logger.debug(f"Non-conventional commit: {subject}")
            return CommitInfo(
                hash=commit_hash,
                type="chore",
                scope=None,
                description=subject,
                body=body,
                breaking=False,
                issues=self._extract_issues(subject, body),
                author=author,
                date=date,
            )

        # Extract commit info
        commit_type = match.group("type").lower()
        scope = match.group("scope")
        description = match.group("description").strip()
        breaking = match.group("breaking") == "!"

        # Check for breaking changes in body
        if body and self.BREAKING_CHANGE_PATTERN.search(body):
            breaking = True

        # Extract issue references
        issues = self._extract_issues(description, body)

        return CommitInfo(
            hash=commit_hash,
            type=commit_type,
            scope=scope,
            description=description,
            body=body,
            breaking=breaking,
            issues=issues,
            author=author,
            date=date,
        )

    def _extract_issues(self, subject: str, body: str | None) -> list[int]:
        """
        Extract GitHub issue numbers from commit message.

        Args:
            subject: Commit subject line
            body: Commit body

        Returns:
            List of issue numbers
        """
        issues = []
        text = subject + ("\n" + body if body else "")

        for match in self.ISSUE_PATTERN.finditer(text):
            try:
                issue_num = int(match.group(1))
                if issue_num not in issues:
                    issues.append(issue_num)
            except ValueError:
                continue

        return issues

    def _group_commits_by_type(
        self, commits: list[CommitInfo]
    ) -> dict[str, list[CommitInfo]]:
        """
        Group commits by their type.

        Args:
            commits: List of commit info objects

        Returns:
            Dictionary mapping commit type to list of commits
        """
        grouped: dict[str, list[CommitInfo]] = {}

        for commit in commits:
            commit_type = commit.type
            if commit_type not in grouped:
                grouped[commit_type] = []
            grouped[commit_type].append(commit)

        return grouped

    def _format_changelog(
        self, grouped_commits: dict[str, list[CommitInfo]], version: str | None = None
    ) -> str:
        """
        Format grouped commits into markdown changelog.

        Args:
            grouped_commits: Commits grouped by type
            version: Version number for header

        Returns:
            Formatted markdown changelog
        """
        lines = []

        # Header
        if version:
            lines.append(f"## [{version}] - {datetime.now().strftime('%Y-%m-%d')}")
        else:
            lines.append(f"## Unreleased - {datetime.now().strftime('%Y-%m-%d')}")
        lines.append("")

        # Breaking changes section (if any)
        breaking_commits = [
            c
            for commits in grouped_commits.values()
            for c in commits
            if c.breaking
        ]
        if breaking_commits:
            lines.append("### ⚠️ BREAKING CHANGES")
            lines.append("")
            for commit in breaking_commits:
                lines.append(f"- **{commit.description}** ({commit.hash[:7]})")
                if commit.body:
                    breaking_match = self.BREAKING_CHANGE_PATTERN.search(commit.body)
                    if breaking_match:
                        lines.append(f"  {breaking_match.group(1)}")
            lines.append("")

        # Regular sections
        for commit_type in SECTION_ORDER:
            if commit_type not in grouped_commits:
                continue

            commits = grouped_commits[commit_type]
            section_title = COMMIT_TYPE_SECTIONS.get(
                commit_type, commit_type.capitalize()
            )

            lines.append(f"### {section_title}")
            lines.append("")

            for commit in commits:
                # Skip if already shown in breaking changes
                if commit.breaking:
                    continue

                # Format: - description (scope) [#123] (hash)
                line = f"- {commit.description}"

                if commit.scope:
                    line += f" **({commit.scope})**"

                if commit.issues:
                    issue_refs = ", ".join(f"[#{issue}]" for issue in commit.issues)
                    line += f" {issue_refs}"

                line += f" ({commit.hash[:7]})"

                lines.append(line)

            lines.append("")

        return "\n".join(lines)

    def append_to_changelog_file(
        self,
        changelog_path: Path,
        since: str | None = None,
        until: str | None = None,
        version: str | None = None,
    ) -> None:
        """
        Generate changelog and append to CHANGELOG.md file.

        Args:
            changelog_path: Path to CHANGELOG.md file
            since: Start reference for commits
            until: End reference for commits
            version: Version number for the release

        Raises:
            subprocess.CalledProcessError: If git command fails
        """
        new_content = self.generate_changelog(since, until, version)

        if not new_content:
            logger.warning("No changelog content to append")
            return

        # Read existing content if file exists
        existing_content = ""
        if changelog_path.exists():
            try:
                existing_content = changelog_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as e:
                logger.error(f"Failed to read existing changelog: {e}")
                existing_content = ""

        # If file is empty or doesn't exist, add header
        if not existing_content.strip():
            existing_content = "# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n"

        # Insert new content after the header
        header_end = existing_content.find("\n\n") + 2
        if header_end < 2:
            # No header found, prepend
            updated_content = new_content + "\n\n" + existing_content
        else:
            updated_content = (
                existing_content[:header_end]
                + new_content
                + "\n\n"
                + existing_content[header_end:]
            )

        # Write back to file
        try:
            changelog_path.write_text(updated_content, encoding="utf-8")
            logger.info(f"Changelog updated: {changelog_path}")
        except OSError as e:
            logger.error(f"Failed to write changelog: {e}")
            raise
