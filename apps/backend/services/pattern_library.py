#!/usr/bin/env python3
"""
Pattern Library Service
========================

Service for managing code patterns with CRUD operations, categorization, and analytics.
Integrates with the memory system to store and retrieve reusable code patterns.

Usage:
    from services.pattern_library import PatternLibrary, get_pattern_analytics

    lib = PatternLibrary(project_dir)

    # Add a pattern
    pattern = CodePattern(...)
    lib.add_pattern(pattern)

    # Get a pattern
    pattern = lib.get_pattern(pattern_id)

    # Update a pattern
    lib.update_pattern(pattern_id, updated_pattern)

    # Delete a pattern
    lib.delete_pattern(pattern_id)

    # Get all patterns
    all_patterns = lib.get_all_patterns()

    # Track pattern usage
    lib.record_pattern_usage(pattern_id, success=True)

    # Get analytics
    popular = lib.get_popular_patterns(limit=5)
    trending = lib.get_trending_patterns(days=30)
    analytics = lib.get_library_analytics()

    # Convenience function for analytics
    analytics = get_pattern_analytics(project_dir)
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from models.pattern import CodePattern, PatternCategory, PatternMetadata

logger = logging.getLogger(__name__)


class PatternLibrary:
    """Manages a library of reusable code patterns."""

    def __init__(self, project_dir: str | Path):
        """
        Initialize pattern library.

        Args:
            project_dir: Path to project directory (used for memory storage)
        """
        self.project_dir = Path(project_dir).resolve()
        self.patterns_file = self._get_patterns_file()
        self._ensure_patterns_file()

    def _get_patterns_file(self) -> Path:
        """
        Get the patterns library file path.

        Returns:
            Path to patterns.json file
        """
        # Store in .auto-claude/patterns/ directory at project root
        patterns_dir = self.project_dir / ".auto-claude" / "patterns"
        patterns_dir.mkdir(parents=True, exist_ok=True)
        return patterns_dir / "patterns.json"

    def _ensure_patterns_file(self) -> None:
        """Ensure patterns file exists with valid JSON."""
        if not self.patterns_file.exists():
            self._save_patterns({})

    def _load_patterns(self) -> dict[str, dict]:
        """
        Load all patterns from storage.

        Returns:
            Dictionary mapping pattern IDs to pattern data
        """
        try:
            with open(self.patterns_file) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to load patterns: {e}")
            return {}

    def _save_patterns(self, patterns: dict[str, dict]) -> None:
        """
        Save patterns to storage.

        Args:
            patterns: Dictionary mapping pattern IDs to pattern data
        """
        try:
            with open(self.patterns_file, "w") as f:
                json.dump(patterns, f, indent=2)
        except OSError as e:
            logger.error(f"Failed to save patterns: {e}")
            raise

    def add_pattern(self, pattern: CodePattern) -> None:
        """
        Add a new pattern to the library.

        Args:
            pattern: CodePattern instance to add

        Raises:
            ValueError: If pattern with same ID already exists
        """
        patterns = self._load_patterns()

        if pattern.id in patterns:
            raise ValueError(f"Pattern with ID '{pattern.id}' already exists")

        patterns[pattern.id] = pattern.to_dict()
        self._save_patterns(patterns)
        logger.info(f"Added pattern: {pattern.id} ({pattern.name})")

    def get_pattern(self, pattern_id: str) -> Optional[CodePattern]:
        """
        Get a pattern by ID.

        Args:
            pattern_id: Pattern identifier

        Returns:
            CodePattern instance or None if not found
        """
        patterns = self._load_patterns()
        pattern_data = patterns.get(pattern_id)

        if pattern_data is None:
            return None

        try:
            return CodePattern.from_dict(pattern_data)
        except (KeyError, ValueError) as e:
            logger.error(f"Failed to parse pattern {pattern_id}: {e}")
            return None

    def update_pattern(self, pattern_id: str, pattern: CodePattern) -> bool:
        """
        Update an existing pattern.

        Args:
            pattern_id: ID of pattern to update
            pattern: Updated CodePattern instance

        Returns:
            True if updated successfully, False if pattern not found

        Raises:
            ValueError: If pattern_id doesn't match pattern.id
        """
        if pattern_id != pattern.id:
            raise ValueError(f"Pattern ID mismatch: {pattern_id} != {pattern.id}")

        patterns = self._load_patterns()

        if pattern_id not in patterns:
            return False

        # Update the updated_at timestamp
        pattern.metadata.updated_at = datetime.utcnow().isoformat()

        patterns[pattern_id] = pattern.to_dict()
        self._save_patterns(patterns)
        logger.info(f"Updated pattern: {pattern_id}")
        return True

    def delete_pattern(self, pattern_id: str) -> bool:
        """
        Delete a pattern by ID.

        Args:
            pattern_id: ID of pattern to delete

        Returns:
            True if deleted successfully, False if pattern not found
        """
        patterns = self._load_patterns()

        if pattern_id not in patterns:
            return False

        del patterns[pattern_id]
        self._save_patterns(patterns)
        logger.info(f"Deleted pattern: {pattern_id}")
        return True

    def get_all_patterns(self) -> list[CodePattern]:
        """
        Get all patterns in the library.

        Returns:
            List of CodePattern instances
        """
        patterns = self._load_patterns()
        result = []

        for pattern_id, pattern_data in patterns.items():
            try:
                result.append(CodePattern.from_dict(pattern_data))
            except (KeyError, ValueError) as e:
                logger.warning(f"Skipping invalid pattern {pattern_id}: {e}")

        return result

    def get_patterns_by_category(self, category: PatternCategory) -> list[CodePattern]:
        """
        Get all patterns in a specific category.

        Args:
            category: Pattern category to filter by

        Returns:
            List of CodePattern instances in the category
        """
        all_patterns = self.get_all_patterns()
        return [p for p in all_patterns if p.category == category]

    def get_patterns_by_type(self, pattern_type: str) -> list[CodePattern]:
        """
        Get all patterns of a specific type.

        Args:
            pattern_type: Pattern type to filter by (e.g., "react-component")

        Returns:
            List of CodePattern instances with matching type
        """
        all_patterns = self.get_all_patterns()
        return [p for p in all_patterns if p.pattern_type == pattern_type]

    def search_patterns(self, query: str) -> list[CodePattern]:
        """
        Search patterns by keyword (case-insensitive).

        Searches in name, description, keywords, and usage_context.

        Args:
            query: Search query string

        Returns:
            List of matching CodePattern instances
        """
        query_lower = query.lower()
        all_patterns = self.get_all_patterns()
        results = []

        for pattern in all_patterns:
            # Check name
            if query_lower in pattern.name.lower():
                results.append(pattern)
                continue

            # Check description
            if query_lower in pattern.description.lower():
                results.append(pattern)
                continue

            # Check keywords
            if any(query_lower in kw.lower() for kw in pattern.keywords):
                results.append(pattern)
                continue

            # Check usage context
            if query_lower in pattern.usage_context.lower():
                results.append(pattern)
                continue

        return results

    def pattern_exists(self, pattern_id: str) -> bool:
        """
        Check if a pattern exists.

        Args:
            pattern_id: Pattern identifier

        Returns:
            True if pattern exists, False otherwise
        """
        patterns = self._load_patterns()
        return pattern_id in patterns

    def get_pattern_count(self) -> int:
        """
        Get total number of patterns in the library.

        Returns:
            Number of patterns
        """
        patterns = self._load_patterns()
        return len(patterns)

    def record_pattern_usage(self, pattern_id: str, success: bool = True) -> bool:
        """
        Record usage of a pattern and update analytics.

        Args:
            pattern_id: ID of the pattern that was used
            success: Whether the pattern was successfully applied

        Returns:
            True if recorded successfully, False if pattern not found
        """
        pattern = self.get_pattern(pattern_id)
        if pattern is None:
            return False

        # Update usage count
        pattern.metadata.usage_count += 1

        # Update last used timestamp
        pattern.metadata.last_used = datetime.utcnow().isoformat()

        # Update success rate using exponential moving average
        # This gives more weight to recent usage
        alpha = 0.2  # Smoothing factor
        current_success = 1.0 if success else 0.0
        pattern.metadata.success_rate = (
            alpha * current_success + (1 - alpha) * pattern.metadata.success_rate
        )

        # Save the updated pattern
        self.update_pattern(pattern_id, pattern)
        logger.info(
            f"Recorded usage for pattern {pattern_id}: "
            f"count={pattern.metadata.usage_count}, "
            f"success_rate={pattern.metadata.success_rate:.2f}"
        )
        return True

    def get_popular_patterns(self, limit: int = 10) -> list[CodePattern]:
        """
        Get the most popular patterns by usage count.

        Args:
            limit: Maximum number of patterns to return

        Returns:
            List of CodePattern instances sorted by usage count (descending)
        """
        all_patterns = self.get_all_patterns()
        sorted_patterns = sorted(
            all_patterns,
            key=lambda p: p.metadata.usage_count,
            reverse=True
        )
        return sorted_patterns[:limit]

    def get_successful_patterns(self, min_usage: int = 5, limit: int = 10) -> list[CodePattern]:
        """
        Get patterns with highest success rates.

        Args:
            min_usage: Minimum usage count to be considered (filters out patterns with too few uses)
            limit: Maximum number of patterns to return

        Returns:
            List of CodePattern instances sorted by success rate (descending)
        """
        all_patterns = self.get_all_patterns()
        # Filter patterns with minimum usage
        filtered_patterns = [
            p for p in all_patterns
            if p.metadata.usage_count >= min_usage
        ]
        sorted_patterns = sorted(
            filtered_patterns,
            key=lambda p: p.metadata.success_rate,
            reverse=True
        )
        return sorted_patterns[:limit]

    def get_trending_patterns(self, days: int = 30, limit: int = 10) -> list[CodePattern]:
        """
        Get trending patterns (recently used and popular).

        Args:
            days: Number of days to consider for "recent" usage
            limit: Maximum number of patterns to return

        Returns:
            List of CodePattern instances sorted by recent usage and popularity
        """
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)
        all_patterns = self.get_all_patterns()
        recent_patterns = []

        for pattern in all_patterns:
            if pattern.metadata.last_used:
                try:
                    last_used = datetime.fromisoformat(pattern.metadata.last_used)
                    if last_used >= cutoff_date:
                        recent_patterns.append(pattern)
                except (ValueError, TypeError):
                    continue

        # Sort by combination of usage count and success rate
        sorted_patterns = sorted(
            recent_patterns,
            key=lambda p: (p.metadata.usage_count * p.metadata.success_rate),
            reverse=True
        )
        return sorted_patterns[:limit]

    def get_pattern_analytics(self, pattern_id: str) -> Optional[dict]:
        """
        Get detailed analytics for a specific pattern.

        Args:
            pattern_id: ID of the pattern

        Returns:
            Dictionary with analytics data or None if pattern not found
        """
        pattern = self.get_pattern(pattern_id)
        if pattern is None:
            return None

        return {
            "pattern_id": pattern.id,
            "name": pattern.name,
            "category": pattern.category.value,
            "usage_count": pattern.metadata.usage_count,
            "success_rate": pattern.metadata.success_rate,
            "last_used": pattern.metadata.last_used,
            "created_at": pattern.metadata.created_at,
            "updated_at": pattern.metadata.updated_at,
            "tags": pattern.metadata.tags,
        }

    def get_library_analytics(self) -> dict:
        """
        Get overall library analytics.

        Returns:
            Dictionary with library-wide statistics
        """
        all_patterns = self.get_all_patterns()
        total_patterns = len(all_patterns)

        if total_patterns == 0:
            return {
                "total_patterns": 0,
                "total_usage": 0,
                "average_success_rate": 0.0,
                "patterns_by_category": {},
                "most_popular_pattern": None,
                "most_successful_pattern": None,
            }

        total_usage = sum(p.metadata.usage_count for p in all_patterns)
        avg_success_rate = sum(p.metadata.success_rate for p in all_patterns) / total_patterns

        # Count patterns by category
        patterns_by_category = {}
        for pattern in all_patterns:
            category = pattern.category.value
            patterns_by_category[category] = patterns_by_category.get(category, 0) + 1

        # Find most popular pattern
        most_popular = max(all_patterns, key=lambda p: p.metadata.usage_count)

        # Find most successful pattern (with at least 1 usage)
        used_patterns = [p for p in all_patterns if p.metadata.usage_count > 0]
        most_successful = None
        if used_patterns:
            most_successful = max(used_patterns, key=lambda p: p.metadata.success_rate)

        return {
            "total_patterns": total_patterns,
            "total_usage": total_usage,
            "average_success_rate": avg_success_rate,
            "patterns_by_category": patterns_by_category,
            "most_popular_pattern": {
                "id": most_popular.id,
                "name": most_popular.name,
                "usage_count": most_popular.metadata.usage_count,
            } if most_popular else None,
            "most_successful_pattern": {
                "id": most_successful.id,
                "name": most_successful.name,
                "success_rate": most_successful.metadata.success_rate,
            } if most_successful else None,
        }


def categorize_pattern(
    pattern_type: str,
    description: str = "",
    code_example: str = "",
    keywords: list[str] | None = None,
    files_involved: list[str] | None = None,
) -> PatternCategory:
    """
    Categorize a pattern based on its characteristics.

    Args:
        pattern_type: Type of the pattern (e.g., "react-component", "express-middleware")
        description: Pattern description
        code_example: Code example content
        keywords: List of keywords associated with the pattern
        files_involved: List of files involved in the pattern

    Returns:
        PatternCategory enum value

    Example:
        >>> categorize_pattern("react-component", description="Login form component")
        <PatternCategory.COMPONENT: 'component'>
        >>> categorize_pattern("express-middleware", code_example="app.use(authenticate)")
        <PatternCategory.AUTHENTICATION: 'authentication'>
    """
    if keywords is None:
        keywords = []
    if files_involved is None:
        files_involved = []

    # Combine all text for analysis
    all_text = f"{pattern_type} {description} {code_example} {' '.join(keywords)}".lower()

    # Check file extensions
    file_extensions = {Path(f).suffix for f in files_involved}

    # Component patterns
    component_keywords = ["component", "react", "vue", "angular", "widget", "ui", "jsx", "tsx"]
    if any(kw in all_text for kw in component_keywords):
        return PatternCategory.COMPONENT

    # Authentication patterns
    auth_keywords = [
        "auth",
        "login",
        "logout",
        "password",
        "token",
        "jwt",
        "session",
        "oauth",
        "credential",
    ]
    if any(kw in all_text for kw in auth_keywords):
        return PatternCategory.AUTHENTICATION

    # Database patterns
    db_keywords = [
        "database",
        "db",
        "sql",
        "query",
        "model",
        "schema",
        "migration",
        "sequelize",
        "mongoose",
        "typeorm",
        "prisma",
    ]
    if any(kw in all_text for kw in db_keywords):
        return PatternCategory.DATABASE

    # API patterns
    api_keywords = [
        "api",
        "endpoint",
        "route",
        "controller",
        "express",
        "fastapi",
        "flask",
        "http",
        "rest",
        "graphql",
    ]
    if any(kw in all_text for kw in api_keywords):
        return PatternCategory.API

    # State management patterns
    state_keywords = [
        "state",
        "redux",
        "zustand",
        "mobx",
        "context",
        "store",
        "reducer",
        "action",
    ]
    if any(kw in all_text for kw in state_keywords):
        return PatternCategory.STATE_MANAGEMENT

    # Error handling patterns
    error_keywords = [
        "error",
        "exception",
        "try",
        "catch",
        "finally",
        "throw",
        "raise",
        "handling",
    ]
    if any(kw in all_text for kw in error_keywords):
        return PatternCategory.ERROR_HANDLING

    # Testing patterns
    test_keywords = [
        "test",
        "jest",
        "mocha",
        "pytest",
        "unittest",
        "spec",
        "mock",
        "assert",
    ]
    if any(kw in all_text for kw in test_keywords) or any(
        ext in {".test.js", ".test.ts", ".spec.js", ".spec.ts", "_test.py"}
        for ext in file_extensions
    ):
        return PatternCategory.TESTING

    # Security patterns
    security_keywords = [
        "security",
        "encrypt",
        "decrypt",
        "hash",
        "sanitize",
        "xss",
        "csrf",
        "injection",
        "validation",
    ]
    if any(kw in all_text for kw in security_keywords):
        return PatternCategory.SECURITY

    # Performance patterns
    perf_keywords = [
        "performance",
        "optimize",
        "cache",
        "memo",
        "lazy",
        "throttle",
        "debounce",
        "async",
    ]
    if any(kw in all_text for kw in perf_keywords):
        return PatternCategory.PERFORMANCE

    # Integration patterns
    integration_keywords = [
        "integration",
        "webhook",
        "external",
        "third-party",
        "service",
        "client",
        "sdk",
    ]
    if any(kw in all_text for kw in integration_keywords):
        return PatternCategory.INTEGRATION

    # Utility patterns
    utility_keywords = ["util", "helper", "common", "shared", "tool"]
    if any(kw in all_text for kw in utility_keywords):
        return PatternCategory.UTILITY

    # Default to OTHER if no match
    return PatternCategory.OTHER


def get_pattern_analytics(project_dir: str | Path, pattern_id: Optional[str] = None) -> dict:
    """
    Get analytics for a specific pattern or the entire library.

    This is a convenience function that creates a PatternLibrary instance
    and retrieves analytics.

    Args:
        project_dir: Path to project directory
        pattern_id: Optional pattern ID to get analytics for. If None, returns library-wide analytics.

    Returns:
        Dictionary with analytics data

    Example:
        >>> # Get library-wide analytics
        >>> analytics = get_pattern_analytics("/path/to/project")
        >>> print(analytics["total_patterns"])

        >>> # Get analytics for specific pattern
        >>> analytics = get_pattern_analytics("/path/to/project", "pattern-001")
        >>> print(analytics["usage_count"])
    """
    library = PatternLibrary(project_dir)

    if pattern_id is None:
        return library.get_library_analytics()
    else:
        result = library.get_pattern_analytics(pattern_id)
        if result is None:
            raise ValueError(f"Pattern '{pattern_id}' not found")
        return result
