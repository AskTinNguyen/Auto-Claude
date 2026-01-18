"""
Data models for code pattern library.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class PatternCategory(str, Enum):
    """Categories for code patterns."""

    COMPONENT = "component"
    API = "api"
    DATABASE = "database"
    AUTHENTICATION = "authentication"
    STATE_MANAGEMENT = "state_management"
    ERROR_HANDLING = "error_handling"
    TESTING = "testing"
    UTILITY = "utility"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    SECURITY = "security"
    OTHER = "other"


@dataclass
class PatternMetadata:
    """Metadata for a code pattern."""

    created_at: str
    updated_at: str
    author: str = "auto-claude"
    usage_count: int = 0
    success_rate: float = 1.0
    last_used: Optional[str] = None
    source_task_id: Optional[str] = None
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "author": self.author,
            "usage_count": self.usage_count,
            "success_rate": self.success_rate,
            "last_used": self.last_used,
            "source_task_id": self.source_task_id,
            "tags": self.tags,
        }


@dataclass
class CodePattern:
    """A reusable code pattern learned from completed tasks."""

    id: str
    name: str
    description: str
    category: PatternCategory
    pattern_type: str  # e.g., "react-component", "express-middleware", "sql-query"
    code_example: str
    usage_context: str
    metadata: PatternMetadata
    files_involved: list[str] = field(default_factory=list)
    related_patterns: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value if isinstance(self.category, PatternCategory) else self.category,
            "pattern_type": self.pattern_type,
            "code_example": self.code_example,
            "usage_context": self.usage_context,
            "metadata": self.metadata.to_dict() if hasattr(self.metadata, 'to_dict') else self.metadata,
            "files_involved": self.files_involved,
            "related_patterns": self.related_patterns,
            "keywords": self.keywords,
        }

    @staticmethod
    def from_dict(data: dict) -> "CodePattern":
        """Create CodePattern from dictionary."""
        metadata_data = data.get("metadata", {})
        metadata = PatternMetadata(**metadata_data) if isinstance(metadata_data, dict) else metadata_data

        category = data.get("category")
        if isinstance(category, str):
            category = PatternCategory(category)

        return CodePattern(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            category=category,
            pattern_type=data["pattern_type"],
            code_example=data["code_example"],
            usage_context=data["usage_context"],
            metadata=metadata,
            files_involved=data.get("files_involved", []),
            related_patterns=data.get("related_patterns", []),
            keywords=data.get("keywords", []),
        )
