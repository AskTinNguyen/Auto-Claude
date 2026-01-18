"""
Bug Analysis Data Models
=========================

Data classes and enums for bug tracking, categorization, and pattern detection.
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class BugCategory(Enum):
    """Bug categories based on root cause analysis"""

    LOGIC_ERROR = "logic-error"
    RACE_CONDITION = "race-condition"
    REQUIREMENTS_MISUNDERSTANDING = "requirements-misunderstanding"
    INTEGRATION_ISSUE = "integration-issue"
    ENVIRONMENT_SPECIFIC = "environment-specific"
    DEPENDENCY_ISSUE = "dependency-issue"
    PERFORMANCE_DEGRADATION = "performance-degradation"
    SECURITY_VULNERABILITY = "security-vulnerability"
    DATA_CORRUPTION = "data-corruption"
    USER_INPUT_VALIDATION = "user-input-validation"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_string(cls, value: str) -> "BugCategory":
        """Convert string to BugCategory enum"""
        for category in cls:
            if category.value == value:
                return category
        raise ValueError(f"Unknown bug category: {value}")


@dataclass
class BugData:
    """Raw bug data extracted from git history"""

    id: str  # bug-{sha[:8]}
    commit_sha: str
    commit_message: str
    author_name: str
    author_email: str
    date_fixed: datetime
    files_changed: list[str]
    diff: str  # Limited to 2000 chars
    related_issues: list[str]  # #123, PRD-45
    github_url: str | None
    error_message: str
    scanned_at: datetime

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "commit_sha": self.commit_sha,
            "commit_message": self.commit_message,
            "author": {
                "name": self.author_name,
                "email": self.author_email,
            },
            "date_fixed": self.date_fixed.isoformat(),
            "files_changed": self.files_changed,
            "diff": self.diff,
            "related_issues": self.related_issues,
            "github_url": self.github_url,
            "error_message": self.error_message,
            "scanned_at": self.scanned_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BugData":
        """Create BugData from dictionary"""
        # Handle nested author structure
        author = data.get("author", {})
        author_name = author.get("name", "")
        author_email = author.get("email", "")

        # Parse datetime strings
        date_fixed = data.get("date_fixed")
        if isinstance(date_fixed, str):
            date_fixed = datetime.fromisoformat(date_fixed)

        scanned_at = data.get("scanned_at")
        if isinstance(scanned_at, str):
            scanned_at = datetime.fromisoformat(scanned_at)

        return cls(
            id=data.get("id", ""),
            commit_sha=data.get("commit_sha", ""),
            commit_message=data.get("commit_message", ""),
            author_name=author_name,
            author_email=author_email,
            date_fixed=date_fixed or datetime.now(),
            files_changed=data.get("files_changed", []),
            diff=data.get("diff", ""),
            related_issues=data.get("related_issues", []),
            github_url=data.get("github_url"),
            error_message=data.get("error_message", ""),
            scanned_at=scanned_at or datetime.now(),
        )

    def save(self, output_dir: Path) -> None:
        """Save bug data to JSON file"""
        output_file = output_dir / f"{self.id}.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, file_path: Path) -> "BugData":
        """Load bug data from JSON file"""
        with open(file_path) as f:
            data = json.load(f)
        return cls.from_dict(data)


@dataclass
class CategorizedBug(BugData):
    """Bug data with AI categorization"""

    primary_category: BugCategory | None = None
    secondary_categories: list[BugCategory] = field(default_factory=list)
    severity: str = "medium"  # "low", "medium", "high", "critical"
    reasoning: str = ""
    prevention_tips: str = ""
    categorized_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        base_dict = super().to_dict()
        base_dict.update(
            {
                "primary_category": (
                    self.primary_category.value if self.primary_category else None
                ),
                "secondary_categories": [c.value for c in self.secondary_categories],
                "severity": self.severity,
                "reasoning": self.reasoning,
                "prevention_tips": self.prevention_tips,
                "categorized_at": (
                    self.categorized_at.isoformat() if self.categorized_at else None
                ),
            }
        )
        return base_dict

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CategorizedBug":
        """Create CategorizedBug from dictionary"""
        # Parse base BugData fields
        bug_data = BugData.from_dict(data)

        # Parse categorization fields
        primary_category = data.get("primary_category")
        if primary_category and isinstance(primary_category, str):
            primary_category = BugCategory.from_string(primary_category)

        secondary_categories = []
        for cat in data.get("secondary_categories", []):
            if isinstance(cat, str):
                secondary_categories.append(BugCategory.from_string(cat))

        categorized_at = data.get("categorized_at")
        if isinstance(categorized_at, str):
            categorized_at = datetime.fromisoformat(categorized_at)

        return cls(
            id=bug_data.id,
            commit_sha=bug_data.commit_sha,
            commit_message=bug_data.commit_message,
            author_name=bug_data.author_name,
            author_email=bug_data.author_email,
            date_fixed=bug_data.date_fixed,
            files_changed=bug_data.files_changed,
            diff=bug_data.diff,
            related_issues=bug_data.related_issues,
            github_url=bug_data.github_url,
            error_message=bug_data.error_message,
            scanned_at=bug_data.scanned_at,
            primary_category=primary_category,
            secondary_categories=secondary_categories,
            severity=data.get("severity", "medium"),
            reasoning=data.get("reasoning", ""),
            prevention_tips=data.get("prevention_tips", ""),
            categorized_at=categorized_at,
        )

    @classmethod
    def from_bug_data(
        cls,
        bug_data: BugData,
        primary_category: BugCategory | None = None,
        secondary_categories: list[BugCategory] | None = None,
        severity: str = "medium",
        reasoning: str = "",
        prevention_tips: str = "",
    ) -> "CategorizedBug":
        """Create CategorizedBug from BugData with categorization info"""
        return cls(
            id=bug_data.id,
            commit_sha=bug_data.commit_sha,
            commit_message=bug_data.commit_message,
            author_name=bug_data.author_name,
            author_email=bug_data.author_email,
            date_fixed=bug_data.date_fixed,
            files_changed=bug_data.files_changed,
            diff=bug_data.diff,
            related_issues=bug_data.related_issues,
            github_url=bug_data.github_url,
            error_message=bug_data.error_message,
            scanned_at=bug_data.scanned_at,
            primary_category=primary_category,
            secondary_categories=secondary_categories or [],
            severity=severity,
            reasoning=reasoning,
            prevention_tips=prevention_tips,
            categorized_at=datetime.now(),
        )


@dataclass
class BugPattern:
    """Detected pattern of recurring bugs"""

    key: str  # "{category}-{module}"
    category: BugCategory
    module: str
    bug_count: int
    first_occurrence: datetime
    latest_occurrence: datetime
    bugs: list[CategorizedBug]
    status: str = "open"  # "open", "closed"
    github_issue_number: int | None = None
    github_issue_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "key": self.key,
            "category": self.category.value,
            "module": self.module,
            "bug_count": self.bug_count,
            "first_occurrence": self.first_occurrence.isoformat(),
            "latest_occurrence": self.latest_occurrence.isoformat(),
            "bugs": [bug.to_dict() for bug in self.bugs],
            "status": self.status,
            "github_issue_number": self.github_issue_number,
            "github_issue_url": self.github_issue_url,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BugPattern":
        """Create BugPattern from dictionary"""
        category = BugCategory.from_string(data.get("category", "logic-error"))

        first_occurrence = data.get("first_occurrence")
        if isinstance(first_occurrence, str):
            first_occurrence = datetime.fromisoformat(first_occurrence)

        latest_occurrence = data.get("latest_occurrence")
        if isinstance(latest_occurrence, str):
            latest_occurrence = datetime.fromisoformat(latest_occurrence)

        bugs = [CategorizedBug.from_dict(bug) for bug in data.get("bugs", [])]

        return cls(
            key=data.get("key", ""),
            category=category,
            module=data.get("module", ""),
            bug_count=data.get("bug_count", 0),
            first_occurrence=first_occurrence or datetime.now(),
            latest_occurrence=latest_occurrence or datetime.now(),
            bugs=bugs,
            status=data.get("status", "open"),
            github_issue_number=data.get("github_issue_number"),
            github_issue_url=data.get("github_issue_url"),
        )

    def save(self, output_dir: Path) -> None:
        """Save pattern data to JSON file"""
        output_file = output_dir / f"pattern-{self.key}.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, file_path: Path) -> "BugPattern":
        """Load pattern data from JSON file"""
        with open(file_path) as f:
            data = json.load(f)
        return cls.from_dict(data)
