"""
Merge Completion Tracking Module
==================================

Data models and storage for tracking merge completion events.

This module provides:
- MergeCompletion: Data model for merge completion metadata
- MergeCompletionStorage: JSON persistence for merge history
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)


@dataclass
class MergeCompletion:
    """
    Represents a completed merge operation with full metadata.

    Tracks all aspects of a merge including conflict resolution,
    AI assistance, and merge strategy used.
    """

    # Identification
    merge_id: str
    spec_name: str
    timestamp: datetime

    # Files involved
    resolved_files: list[str] = field(default_factory=list)

    # Conflict statistics
    conflicts_resolved: int = 0
    ai_assisted_count: int = 0
    auto_merged_count: int = 0
    git_conflicts: int = 0

    # Merge metadata
    merge_strategy: Literal["fast-forward", "3-way", "ai-assisted", "manual"] = "3-way"
    success: bool = True

    # Optional context
    error_message: str | None = None
    duration_seconds: float | None = None

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON storage."""
        return {
            "merge_id": self.merge_id,
            "spec_name": self.spec_name,
            "timestamp": self.timestamp.isoformat(),
            "resolved_files": self.resolved_files,
            "conflicts_resolved": self.conflicts_resolved,
            "ai_assisted_count": self.ai_assisted_count,
            "auto_merged_count": self.auto_merged_count,
            "git_conflicts": self.git_conflicts,
            "merge_strategy": self.merge_strategy,
            "success": self.success,
            "error_message": self.error_message,
            "duration_seconds": self.duration_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict) -> MergeCompletion:
        """Deserialize from dictionary."""
        return cls(
            merge_id=data["merge_id"],
            spec_name=data["spec_name"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            resolved_files=data.get("resolved_files", []),
            conflicts_resolved=data.get("conflicts_resolved", 0),
            ai_assisted_count=data.get("ai_assisted_count", 0),
            auto_merged_count=data.get("auto_merged_count", 0),
            git_conflicts=data.get("git_conflicts", 0),
            merge_strategy=data.get("merge_strategy", "3-way"),
            success=data.get("success", True),
            error_message=data.get("error_message"),
            duration_seconds=data.get("duration_seconds"),
        )


class MergeCompletionStorage:
    """
    Manages persistence of merge completion records.

    Responsibilities:
    - Store merge completion events to JSON
    - Query merge history by spec or globally
    - Provide merge statistics and summaries
    """

    def __init__(
        self,
        project_dir: Path | None = None,
        storage_dir: Path | None = None,
    ):
        """
        Initialize merge completion storage.

        Args:
            project_dir: Root directory of the project (optional)
            storage_dir: Directory for merge history (.auto-claude/merge-history/)
                        If not provided, uses project_dir/.auto-claude/merge-history
        """
        if storage_dir is None:
            if project_dir is None:
                # Default to current directory if nothing provided
                project_dir = Path.cwd()
            self.storage_dir = Path(project_dir) / ".auto-claude" / "merge-history"
        else:
            self.storage_dir = Path(storage_dir)

        # Ensure storage directory exists
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.storage_dir / "merge_history.json"

    def record_merge(self, merge: MergeCompletion) -> None:
        """
        Record a merge completion event.

        Args:
            merge: MergeCompletion object to persist
        """
        try:
            # Load existing history
            history = self._load_history()

            # Add new merge record
            history.append(merge.to_dict())

            # Save updated history
            self._save_history(history)

            logger.info(
                f"Recorded merge completion for {merge.spec_name} "
                f"(ID: {merge.merge_id}, success: {merge.success})"
            )

        except Exception as e:
            logger.error(f"Failed to record merge completion: {e}")
            raise

    def get_merge_history(self, spec_name: str | None = None) -> list[MergeCompletion]:
        """
        Get merge history, optionally filtered by spec.

        Args:
            spec_name: Optional spec name to filter by

        Returns:
            List of MergeCompletion objects, sorted by timestamp (newest first)
        """
        try:
            history = self._load_history()

            # Filter by spec if provided
            if spec_name:
                history = [m for m in history if m.get("spec_name") == spec_name]

            # Convert to MergeCompletion objects
            merges = [MergeCompletion.from_dict(m) for m in history]

            # Sort by timestamp, newest first
            merges.sort(key=lambda m: m.timestamp, reverse=True)

            return merges

        except Exception as e:
            logger.error(f"Failed to load merge history: {e}")
            return []

    def get_recent_merges(self, limit: int = 10) -> list[MergeCompletion]:
        """
        Get most recent merge completions.

        Args:
            limit: Maximum number of merges to return

        Returns:
            List of recent MergeCompletion objects
        """
        all_merges = self.get_merge_history()
        return all_merges[:limit]

    def get_merge_by_id(self, merge_id: str) -> MergeCompletion | None:
        """
        Get a specific merge by ID.

        Args:
            merge_id: Unique merge identifier

        Returns:
            MergeCompletion object or None if not found
        """
        try:
            history = self._load_history()
            for merge_data in history:
                if merge_data.get("merge_id") == merge_id:
                    return MergeCompletion.from_dict(merge_data)
            return None

        except Exception as e:
            logger.error(f"Failed to get merge by ID: {e}")
            return None

    def get_merge_stats_summary(self, spec_name: str | None = None) -> dict:
        """
        Get summary statistics for merges.

        Args:
            spec_name: Optional spec name to filter by

        Returns:
            Dictionary with aggregate statistics
        """
        merges = self.get_merge_history(spec_name)

        if not merges:
            return {
                "total_merges": 0,
                "successful_merges": 0,
                "failed_merges": 0,
                "total_conflicts_resolved": 0,
                "total_ai_assisted": 0,
                "total_files_merged": 0,
                "average_duration": None,
            }

        successful = [m for m in merges if m.success]
        failed = [m for m in merges if not m.success]

        # Calculate average duration (only for merges with duration data)
        durations = [m.duration_seconds for m in merges if m.duration_seconds is not None]
        avg_duration = sum(durations) / len(durations) if durations else None

        # Count unique files
        all_files = set()
        for merge in merges:
            all_files.update(merge.resolved_files)

        return {
            "total_merges": len(merges),
            "successful_merges": len(successful),
            "failed_merges": len(failed),
            "total_conflicts_resolved": sum(m.conflicts_resolved for m in merges),
            "total_ai_assisted": sum(m.ai_assisted_count for m in merges),
            "total_files_merged": len(all_files),
            "average_duration": avg_duration,
        }

    def _load_history(self) -> list[dict]:
        """
        Load merge history from JSON file.

        Returns:
            List of merge dictionaries
        """
        if not self.history_file.exists():
            return []

        try:
            with open(self.history_file) as f:
                data = json.load(f)
                return data if isinstance(data, list) else []

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in merge history file: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to load merge history: {e}")
            return []

    def _save_history(self, history: list[dict]) -> None:
        """
        Save merge history to JSON file.

        Args:
            history: List of merge dictionaries
        """
        try:
            with open(self.history_file, "w") as f:
                json.dump(history, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save merge history: {e}")
            raise


def create_merge_completion(
    spec_name: str,
    resolved_files: list[str],
    stats: dict,
    success: bool = True,
    error_message: str | None = None,
) -> MergeCompletion:
    """
    Factory function to create a MergeCompletion record.

    Args:
        spec_name: Name of the spec being merged
        resolved_files: List of file paths that were merged
        stats: Dictionary with merge statistics (conflicts_resolved, ai_assisted_count, etc.)
        success: Whether the merge succeeded
        error_message: Optional error message if failed

    Returns:
        MergeCompletion object ready to be persisted
    """
    return MergeCompletion(
        merge_id=str(uuid.uuid4()),
        spec_name=spec_name,
        timestamp=datetime.now(),
        resolved_files=resolved_files,
        conflicts_resolved=stats.get("conflicts_resolved", 0),
        ai_assisted_count=stats.get("ai_assisted_count", 0),
        auto_merged_count=stats.get("auto_merged_count", 0),
        git_conflicts=stats.get("git_conflicts", 0),
        merge_strategy=stats.get("merge_strategy", "3-way"),
        success=success,
        error_message=error_message,
        duration_seconds=stats.get("duration_seconds"),
    )
