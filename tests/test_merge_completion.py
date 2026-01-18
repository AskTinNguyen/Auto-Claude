#!/usr/bin/env python3
"""
Tests for Merge Completion Tracking
=====================================

Tests the merge_completion module functionality including:
- MergeCompletion data model
- MergeCompletionStorage persistence and querying
- Merge statistics and analytics
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

# Add auto-claude directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "backend"))

from core.workspace.merge_completion import (
    MergeCompletion,
    MergeCompletionStorage,
    create_merge_completion,
)


class TestMergeCompletion:
    """Tests for MergeCompletion data model."""

    def test_create_merge_completion(self):
        """Can create a MergeCompletion instance."""
        merge = MergeCompletion(
            merge_id="test-123",
            spec_name="test-spec",
            timestamp=datetime.now(),
            resolved_files=["file1.py", "file2.py"],
            conflicts_resolved=2,
            ai_assisted_count=1,
            merge_strategy="ai-assisted",
        )

        assert merge.merge_id == "test-123"
        assert merge.spec_name == "test-spec"
        assert len(merge.resolved_files) == 2
        assert merge.conflicts_resolved == 2
        assert merge.ai_assisted_count == 1
        assert merge.merge_strategy == "ai-assisted"
        assert merge.success is True

    def test_merge_completion_defaults(self):
        """MergeCompletion has correct default values."""
        merge = MergeCompletion(
            merge_id="test-123",
            spec_name="test-spec",
            timestamp=datetime.now(),
        )

        assert merge.resolved_files == []
        assert merge.conflicts_resolved == 0
        assert merge.ai_assisted_count == 0
        assert merge.auto_merged_count == 0
        assert merge.git_conflicts == 0
        assert merge.merge_strategy == "3-way"
        assert merge.success is True
        assert merge.error_message is None
        assert merge.duration_seconds is None

    def test_to_dict_serialization(self):
        """Can serialize MergeCompletion to dictionary."""
        timestamp = datetime.now()
        merge = MergeCompletion(
            merge_id="test-123",
            spec_name="test-spec",
            timestamp=timestamp,
            resolved_files=["file1.py"],
            conflicts_resolved=1,
            merge_strategy="fast-forward",
        )

        data = merge.to_dict()

        assert data["merge_id"] == "test-123"
        assert data["spec_name"] == "test-spec"
        assert data["timestamp"] == timestamp.isoformat()
        assert data["resolved_files"] == ["file1.py"]
        assert data["conflicts_resolved"] == 1
        assert data["merge_strategy"] == "fast-forward"

    def test_from_dict_deserialization(self):
        """Can deserialize MergeCompletion from dictionary."""
        timestamp = datetime.now()
        data = {
            "merge_id": "test-123",
            "spec_name": "test-spec",
            "timestamp": timestamp.isoformat(),
            "resolved_files": ["file1.py", "file2.py"],
            "conflicts_resolved": 2,
            "ai_assisted_count": 1,
            "auto_merged_count": 1,
            "git_conflicts": 0,
            "merge_strategy": "ai-assisted",
            "success": True,
            "error_message": None,
            "duration_seconds": 45.5,
        }

        merge = MergeCompletion.from_dict(data)

        assert merge.merge_id == "test-123"
        assert merge.spec_name == "test-spec"
        assert merge.timestamp == timestamp
        assert merge.resolved_files == ["file1.py", "file2.py"]
        assert merge.conflicts_resolved == 2
        assert merge.ai_assisted_count == 1
        assert merge.merge_strategy == "ai-assisted"
        assert merge.duration_seconds == 45.5

    def test_round_trip_serialization(self):
        """Serialization round-trip preserves data."""
        original = MergeCompletion(
            merge_id="test-123",
            spec_name="test-spec",
            timestamp=datetime.now(),
            resolved_files=["file1.py", "file2.py"],
            conflicts_resolved=3,
            ai_assisted_count=2,
            merge_strategy="manual",
            duration_seconds=120.0,
        )

        data = original.to_dict()
        restored = MergeCompletion.from_dict(data)

        assert restored.merge_id == original.merge_id
        assert restored.spec_name == original.spec_name
        assert restored.resolved_files == original.resolved_files
        assert restored.conflicts_resolved == original.conflicts_resolved
        assert restored.ai_assisted_count == original.ai_assisted_count
        assert restored.merge_strategy == original.merge_strategy
        assert restored.duration_seconds == original.duration_seconds


class TestMergeCompletionStorage:
    """Tests for MergeCompletionStorage persistence."""

    def test_storage_initialization(self, temp_dir):
        """Storage creates directory structure."""
        storage = MergeCompletionStorage(project_dir=temp_dir)

        assert storage.storage_dir.exists()
        assert storage.storage_dir == temp_dir / ".auto-claude" / "merge-history"
        assert storage.history_file == storage.storage_dir / "merge_history.json"

    def test_storage_with_custom_directory(self, temp_dir):
        """Can initialize with custom storage directory."""
        custom_dir = temp_dir / "custom" / "merge-storage"
        storage = MergeCompletionStorage(storage_dir=custom_dir)

        assert storage.storage_dir == custom_dir
        assert storage.storage_dir.exists()

    def test_record_merge(self, temp_dir):
        """Can record a merge completion."""
        storage = MergeCompletionStorage(project_dir=temp_dir)

        merge = MergeCompletion(
            merge_id="test-123",
            spec_name="test-spec",
            timestamp=datetime.now(),
            resolved_files=["file1.py"],
            conflicts_resolved=1,
        )

        storage.record_merge(merge)

        # Verify file was created and contains data
        assert storage.history_file.exists()
        history = storage.get_merge_history()
        assert len(history) == 1
        assert history[0].merge_id == "test-123"

    def test_record_multiple_merges(self, temp_dir):
        """Can record multiple merge completions."""
        storage = MergeCompletionStorage(project_dir=temp_dir)

        for i in range(3):
            merge = MergeCompletion(
                merge_id=f"test-{i}",
                spec_name=f"spec-{i}",
                timestamp=datetime.now(),
            )
            storage.record_merge(merge)

        history = storage.get_merge_history()
        assert len(history) == 3

    def test_get_merge_history_empty(self, temp_dir):
        """Returns empty list when no history exists."""
        storage = MergeCompletionStorage(project_dir=temp_dir)

        history = storage.get_merge_history()
        assert history == []

    def test_get_merge_history_sorted_by_timestamp(self, temp_dir):
        """Merge history is sorted by timestamp, newest first."""
        storage = MergeCompletionStorage(project_dir=temp_dir)

        # Create merges with different timestamps
        base_time = datetime.now()
        for i in range(3):
            merge = MergeCompletion(
                merge_id=f"test-{i}",
                spec_name=f"spec-{i}",
                timestamp=base_time + timedelta(hours=i),
            )
            storage.record_merge(merge)

        history = storage.get_merge_history()

        # Newest first (test-2, test-1, test-0)
        assert history[0].merge_id == "test-2"
        assert history[1].merge_id == "test-1"
        assert history[2].merge_id == "test-0"

    def test_get_merge_history_by_spec(self, temp_dir):
        """Can filter merge history by spec name."""
        storage = MergeCompletionStorage(project_dir=temp_dir)

        # Create merges for different specs
        for i in range(3):
            spec_name = "spec-a" if i % 2 == 0 else "spec-b"
            merge = MergeCompletion(
                merge_id=f"test-{i}",
                spec_name=spec_name,
                timestamp=datetime.now(),
            )
            storage.record_merge(merge)

        # Get history for spec-a only
        history = storage.get_merge_history(spec_name="spec-a")

        assert len(history) == 2  # test-0 and test-2
        assert all(m.spec_name == "spec-a" for m in history)

    def test_get_recent_merges(self, temp_dir):
        """Can retrieve recent merges with limit."""
        storage = MergeCompletionStorage(project_dir=temp_dir)

        # Create 5 merges
        for i in range(5):
            merge = MergeCompletion(
                merge_id=f"test-{i}",
                spec_name=f"spec-{i}",
                timestamp=datetime.now() + timedelta(seconds=i),
            )
            storage.record_merge(merge)

        # Get only 3 most recent
        recent = storage.get_recent_merges(limit=3)

        assert len(recent) == 3
        # Most recent first
        assert recent[0].merge_id == "test-4"
        assert recent[1].merge_id == "test-3"
        assert recent[2].merge_id == "test-2"

    def test_get_merge_by_id(self, temp_dir):
        """Can retrieve a specific merge by ID."""
        storage = MergeCompletionStorage(project_dir=temp_dir)

        merge = MergeCompletion(
            merge_id="unique-123",
            spec_name="test-spec",
            timestamp=datetime.now(),
        )
        storage.record_merge(merge)

        retrieved = storage.get_merge_by_id("unique-123")

        assert retrieved is not None
        assert retrieved.merge_id == "unique-123"
        assert retrieved.spec_name == "test-spec"

    def test_get_merge_by_id_not_found(self, temp_dir):
        """Returns None when merge ID not found."""
        storage = MergeCompletionStorage(project_dir=temp_dir)

        retrieved = storage.get_merge_by_id("nonexistent")
        assert retrieved is None

    def test_get_merges_by_strategy(self, temp_dir):
        """Can filter merges by merge strategy."""
        storage = MergeCompletionStorage(project_dir=temp_dir)

        strategies = ["fast-forward", "3-way", "ai-assisted", "3-way"]
        for i, strategy in enumerate(strategies):
            merge = MergeCompletion(
                merge_id=f"test-{i}",
                spec_name=f"spec-{i}",
                timestamp=datetime.now(),
                merge_strategy=strategy,
            )
            storage.record_merge(merge)

        ai_assisted = storage.get_merges_by_strategy("ai-assisted")
        three_way = storage.get_merges_by_strategy("3-way")

        assert len(ai_assisted) == 1
        assert ai_assisted[0].merge_strategy == "ai-assisted"
        assert len(three_way) == 2
        assert all(m.merge_strategy == "3-way" for m in three_way)

    def test_get_merges_by_date_range(self, temp_dir):
        """Can filter merges by date range."""
        storage = MergeCompletionStorage(project_dir=temp_dir)

        base_time = datetime.now()

        # Create merges across 5 days
        for i in range(5):
            merge = MergeCompletion(
                merge_id=f"test-{i}",
                spec_name=f"spec-{i}",
                timestamp=base_time + timedelta(days=i),
            )
            storage.record_merge(merge)

        # Get merges from day 1 to day 3
        start = base_time + timedelta(days=1)
        end = base_time + timedelta(days=3)
        filtered = storage.get_merges_by_date_range(start, end)

        assert len(filtered) == 3  # Days 1, 2, 3
        merge_ids = {m.merge_id for m in filtered}
        assert merge_ids == {"test-1", "test-2", "test-3"}

    def test_get_successful_merges(self, temp_dir):
        """Can filter for successful merges only."""
        storage = MergeCompletionStorage(project_dir=temp_dir)

        # Create mix of successful and failed merges
        for i in range(4):
            merge = MergeCompletion(
                merge_id=f"test-{i}",
                spec_name=f"spec-{i}",
                timestamp=datetime.now(),
                success=(i % 2 == 0),  # 0 and 2 succeed
            )
            storage.record_merge(merge)

        successful = storage.get_successful_merges()

        assert len(successful) == 2
        assert all(m.success for m in successful)
        assert {m.merge_id for m in successful} == {"test-0", "test-2"}

    def test_get_failed_merges(self, temp_dir):
        """Can filter for failed merges only."""
        storage = MergeCompletionStorage(project_dir=temp_dir)

        # Create mix of successful and failed merges
        for i in range(4):
            merge = MergeCompletion(
                merge_id=f"test-{i}",
                spec_name=f"spec-{i}",
                timestamp=datetime.now(),
                success=(i % 2 == 0),  # 1 and 3 fail
                error_message="Test error" if i % 2 == 1 else None,
            )
            storage.record_merge(merge)

        failed = storage.get_failed_merges()

        assert len(failed) == 2
        assert all(not m.success for m in failed)
        assert {m.merge_id for m in failed} == {"test-1", "test-3"}

    def test_get_merges_with_conflicts(self, temp_dir):
        """Can filter for merges that had conflicts."""
        storage = MergeCompletionStorage(project_dir=temp_dir)

        # Create merges with and without conflicts
        for i in range(4):
            merge = MergeCompletion(
                merge_id=f"test-{i}",
                spec_name=f"spec-{i}",
                timestamp=datetime.now(),
                conflicts_resolved=i,  # 0 has no conflicts, 1-3 have conflicts
            )
            storage.record_merge(merge)

        with_conflicts = storage.get_merges_with_conflicts()

        assert len(with_conflicts) == 3
        assert all(m.conflicts_resolved > 0 for m in with_conflicts)
        assert {m.merge_id for m in with_conflicts} == {"test-1", "test-2", "test-3"}

    def test_get_ai_assisted_merges(self, temp_dir):
        """Can filter for AI-assisted merges."""
        storage = MergeCompletionStorage(project_dir=temp_dir)

        # Create merges with and without AI assistance
        for i in range(4):
            merge = MergeCompletion(
                merge_id=f"test-{i}",
                spec_name=f"spec-{i}",
                timestamp=datetime.now(),
                ai_assisted_count=i,  # 0 has no AI, 1-3 have AI
            )
            storage.record_merge(merge)

        ai_assisted = storage.get_ai_assisted_merges()

        assert len(ai_assisted) == 3
        assert all(m.ai_assisted_count > 0 for m in ai_assisted)
        assert {m.merge_id for m in ai_assisted} == {"test-1", "test-2", "test-3"}

    def test_get_files_merged_multiple_times(self, temp_dir):
        """Can identify files merged multiple times."""
        storage = MergeCompletionStorage(project_dir=temp_dir)

        # Create merges with overlapping files
        merges_data = [
            (["file1.py", "file2.py"], "test-1"),
            (["file2.py", "file3.py"], "test-2"),
            (["file2.py", "file4.py"], "test-3"),
            (["file5.py"], "test-4"),
        ]

        for files, merge_id in merges_data:
            merge = MergeCompletion(
                merge_id=merge_id,
                spec_name="test-spec",
                timestamp=datetime.now(),
                resolved_files=files,
            )
            storage.record_merge(merge)

        multi_merged = storage.get_files_merged_multiple_times()

        # Only file2.py was merged 3 times (appears in test-1, test-2, test-3)
        assert "file2.py" in multi_merged
        assert len(multi_merged["file2.py"]) == 3
        assert set(multi_merged["file2.py"]) == {"test-1", "test-2", "test-3"}

        # Files merged only once should not appear
        assert "file1.py" not in multi_merged
        assert "file5.py" not in multi_merged

    def test_get_most_merged_files(self, temp_dir):
        """Can get files most frequently involved in merges."""
        storage = MergeCompletionStorage(project_dir=temp_dir)

        # Create merges with different file frequencies
        merges_data = [
            ["fileA.py", "fileB.py"],  # fileA: 1, fileB: 1
            ["fileA.py", "fileC.py"],  # fileA: 2, fileC: 1
            ["fileA.py", "fileB.py"],  # fileA: 3, fileB: 2
            ["fileB.py", "fileD.py"],  # fileB: 3, fileD: 1
        ]

        for i, files in enumerate(merges_data):
            merge = MergeCompletion(
                merge_id=f"test-{i}",
                spec_name=f"spec-{i}",
                timestamp=datetime.now(),
                resolved_files=files,
            )
            storage.record_merge(merge)

        most_merged = storage.get_most_merged_files(limit=3)

        # fileA: 3, fileB: 3, fileC: 1, fileD: 1
        # Should return fileA and fileB first (both count 3), then one of C/D
        assert len(most_merged) == 3
        assert most_merged[0] in [("fileA.py", 3), ("fileB.py", 3)]
        assert most_merged[1] in [("fileA.py", 3), ("fileB.py", 3)]

    def test_get_spec_merge_count(self, temp_dir):
        """Can count merges for a specific spec."""
        storage = MergeCompletionStorage(project_dir=temp_dir)

        # Create multiple merges for same spec
        for i in range(3):
            merge = MergeCompletion(
                merge_id=f"test-{i}",
                spec_name="popular-spec",
                timestamp=datetime.now(),
            )
            storage.record_merge(merge)

        # Create one merge for different spec
        merge = MergeCompletion(
            merge_id="test-other",
            spec_name="other-spec",
            timestamp=datetime.now(),
        )
        storage.record_merge(merge)

        count = storage.get_spec_merge_count("popular-spec")
        other_count = storage.get_spec_merge_count("other-spec")

        assert count == 3
        assert other_count == 1

    def test_get_all_specs_merged(self, temp_dir):
        """Can get list of all unique specs that have been merged."""
        storage = MergeCompletionStorage(project_dir=temp_dir)

        specs = ["spec-a", "spec-b", "spec-a", "spec-c", "spec-b"]

        for i, spec_name in enumerate(specs):
            merge = MergeCompletion(
                merge_id=f"test-{i}",
                spec_name=spec_name,
                timestamp=datetime.now(),
            )
            storage.record_merge(merge)

        all_specs = storage.get_all_specs_merged()

        # Should return sorted unique specs
        assert all_specs == ["spec-a", "spec-b", "spec-c"]

    def test_get_merge_stats_summary_empty(self, temp_dir):
        """Returns correct summary for empty history."""
        storage = MergeCompletionStorage(project_dir=temp_dir)

        stats = storage.get_merge_stats_summary()

        assert stats["total_merges"] == 0
        assert stats["successful_merges"] == 0
        assert stats["failed_merges"] == 0
        assert stats["total_conflicts_resolved"] == 0
        assert stats["total_ai_assisted"] == 0
        assert stats["total_files_merged"] == 0
        assert stats["average_duration"] is None
        assert stats["merge_strategies"] == {}

    def test_get_merge_stats_summary(self, temp_dir):
        """Returns correct aggregate statistics."""
        storage = MergeCompletionStorage(project_dir=temp_dir)

        # Create diverse merge history
        merges_data = [
            {
                "success": True,
                "conflicts": 2,
                "ai_assisted": 1,
                "files": ["file1.py", "file2.py"],
                "strategy": "ai-assisted",
                "duration": 30.0,
            },
            {
                "success": True,
                "conflicts": 0,
                "ai_assisted": 0,
                "files": ["file3.py"],
                "strategy": "fast-forward",
                "duration": 10.0,
            },
            {
                "success": False,
                "conflicts": 1,
                "ai_assisted": 0,
                "files": ["file4.py"],
                "strategy": "manual",
                "duration": 60.0,
            },
        ]

        for i, data in enumerate(merges_data):
            merge = MergeCompletion(
                merge_id=f"test-{i}",
                spec_name=f"spec-{i}",
                timestamp=datetime.now(),
                success=data["success"],
                conflicts_resolved=data["conflicts"],
                ai_assisted_count=data["ai_assisted"],
                resolved_files=data["files"],
                merge_strategy=data["strategy"],
                duration_seconds=data["duration"],
            )
            storage.record_merge(merge)

        stats = storage.get_merge_stats_summary()

        assert stats["total_merges"] == 3
        assert stats["successful_merges"] == 2
        assert stats["failed_merges"] == 1
        assert stats["total_conflicts_resolved"] == 3  # 2 + 0 + 1
        assert stats["total_ai_assisted"] == 1
        assert stats["total_files_merged"] == 4  # Unique files
        assert abs(stats["average_duration"] - 33.33) < 0.01  # (30 + 10 + 60) / 3
        assert stats["merge_strategies"]["ai-assisted"] == 1
        assert stats["merge_strategies"]["fast-forward"] == 1
        assert stats["merge_strategies"]["manual"] == 1

    def test_get_merge_stats_summary_by_spec(self, temp_dir):
        """Can get statistics filtered by spec."""
        storage = MergeCompletionStorage(project_dir=temp_dir)

        # Create merges for different specs
        for i in range(4):
            spec_name = "spec-a" if i < 2 else "spec-b"
            merge = MergeCompletion(
                merge_id=f"test-{i}",
                spec_name=spec_name,
                timestamp=datetime.now(),
                conflicts_resolved=i,
            )
            storage.record_merge(merge)

        stats_a = storage.get_merge_stats_summary(spec_name="spec-a")
        stats_b = storage.get_merge_stats_summary(spec_name="spec-b")

        assert stats_a["total_merges"] == 2
        assert stats_a["total_conflicts_resolved"] == 1  # 0 + 1
        assert stats_b["total_merges"] == 2
        assert stats_b["total_conflicts_resolved"] == 5  # 2 + 3


class TestCreateMergeCompletion:
    """Tests for create_merge_completion factory function."""

    def test_create_merge_completion_basic(self):
        """Factory creates valid MergeCompletion."""
        merge = create_merge_completion(
            spec_name="test-spec",
            resolved_files=["file1.py"],
            stats={
                "conflicts_resolved": 1,
                "ai_assisted_count": 0,
                "merge_strategy": "3-way",
            },
        )

        assert merge.spec_name == "test-spec"
        assert merge.resolved_files == ["file1.py"]
        assert merge.conflicts_resolved == 1
        assert merge.ai_assisted_count == 0
        assert merge.merge_strategy == "3-way"
        assert merge.success is True
        assert merge.error_message is None

    def test_create_merge_completion_generates_id(self):
        """Factory generates unique merge ID."""
        merge1 = create_merge_completion(
            spec_name="test-spec",
            resolved_files=[],
            stats={},
        )
        merge2 = create_merge_completion(
            spec_name="test-spec",
            resolved_files=[],
            stats={},
        )

        assert merge1.merge_id != merge2.merge_id
        assert len(merge1.merge_id) > 0
        assert len(merge2.merge_id) > 0

    def test_create_merge_completion_with_failure(self):
        """Factory can create failed merge record."""
        merge = create_merge_completion(
            spec_name="failed-spec",
            resolved_files=[],
            stats={},
            success=False,
            error_message="Merge failed due to conflicts",
        )

        assert merge.success is False
        assert merge.error_message == "Merge failed due to conflicts"

    def test_create_merge_completion_extracts_stats(self):
        """Factory correctly extracts all stats from dict."""
        stats = {
            "conflicts_resolved": 5,
            "ai_assisted_count": 3,
            "auto_merged_count": 2,
            "git_conflicts": 1,
            "merge_strategy": "ai-assisted",
            "duration_seconds": 45.7,
        }

        merge = create_merge_completion(
            spec_name="test-spec",
            resolved_files=["file1.py", "file2.py"],
            stats=stats,
        )

        assert merge.conflicts_resolved == 5
        assert merge.ai_assisted_count == 3
        assert merge.auto_merged_count == 2
        assert merge.git_conflicts == 1
        assert merge.merge_strategy == "ai-assisted"
        assert merge.duration_seconds == 45.7

    def test_create_merge_completion_defaults_missing_stats(self):
        """Factory uses defaults for missing stats."""
        merge = create_merge_completion(
            spec_name="test-spec",
            resolved_files=[],
            stats={},  # Empty stats
        )

        assert merge.conflicts_resolved == 0
        assert merge.ai_assisted_count == 0
        assert merge.auto_merged_count == 0
        assert merge.git_conflicts == 0
        assert merge.merge_strategy == "3-way"  # Default strategy
        assert merge.duration_seconds is None


class TestMergeCompletionIntegration:
    """Integration tests for merge completion tracking."""

    def test_full_workflow(self, temp_dir):
        """Test complete workflow from creation to querying."""
        storage = MergeCompletionStorage(project_dir=temp_dir)

        # Create and record a merge
        stats = {
            "conflicts_resolved": 2,
            "ai_assisted_count": 1,
            "auto_merged_count": 1,
            "merge_strategy": "ai-assisted",
            "duration_seconds": 30.5,
        }

        merge = create_merge_completion(
            spec_name="integration-test",
            resolved_files=["file1.py", "file2.py"],
            stats=stats,
            success=True,
        )

        storage.record_merge(merge)

        # Query it back
        retrieved = storage.get_merge_by_id(merge.merge_id)

        assert retrieved is not None
        assert retrieved.spec_name == "integration-test"
        assert retrieved.conflicts_resolved == 2
        assert retrieved.ai_assisted_count == 1
        assert retrieved.merge_strategy == "ai-assisted"

        # Check it appears in various queries
        all_merges = storage.get_merge_history()
        assert len(all_merges) == 1

        ai_assisted = storage.get_ai_assisted_merges()
        assert len(ai_assisted) == 1

        stats_summary = storage.get_merge_stats_summary()
        assert stats_summary["total_merges"] == 1
        assert stats_summary["successful_merges"] == 1

    def test_multiple_specs_workflow(self, temp_dir):
        """Test tracking merges across multiple specs."""
        storage = MergeCompletionStorage(project_dir=temp_dir)

        # Create merges for different specs
        specs = ["feature-auth", "bugfix-validation", "feature-auth"]

        for i, spec_name in enumerate(specs):
            merge = create_merge_completion(
                spec_name=spec_name,
                resolved_files=[f"file{i}.py"],
                stats={"conflicts_resolved": i},
            )
            storage.record_merge(merge)

        # Verify spec-specific queries
        auth_merges = storage.get_merge_history(spec_name="feature-auth")
        assert len(auth_merges) == 2

        bugfix_merges = storage.get_merge_history(spec_name="bugfix-validation")
        assert len(bugfix_merges) == 1

        all_specs = storage.get_all_specs_merged()
        assert set(all_specs) == {"bugfix-validation", "feature-auth"}

    def test_analytics_workflow(self, temp_dir):
        """Test analytics and reporting queries."""
        storage = MergeCompletionStorage(project_dir=temp_dir)

        # Create diverse merge history
        base_time = datetime.now()

        for i in range(10):
            merge = create_merge_completion(
                spec_name=f"spec-{i % 3}",  # 3 different specs
                resolved_files=[f"file{i}.py"],
                stats={
                    "conflicts_resolved": i % 2,  # Some with conflicts
                    "ai_assisted_count": 1 if i % 3 == 0 else 0,  # Some AI-assisted
                    "merge_strategy": ["fast-forward", "3-way", "ai-assisted"][i % 3],
                },
                success=i % 5 != 0,  # Some failures
            )
            # Manually set timestamp for time-based queries
            merge.timestamp = base_time + timedelta(hours=i)
            storage.record_merge(merge)

        # Analytics queries
        stats = storage.get_merge_stats_summary()
        assert stats["total_merges"] == 10
        assert stats["successful_merges"] == 8  # 2 failures (i=0, i=5)
        assert stats["failed_merges"] == 2

        with_conflicts = storage.get_merges_with_conflicts()
        assert len(with_conflicts) == 5  # i=1,3,5,7,9

        ai_assisted = storage.get_ai_assisted_merges()
        assert len(ai_assisted) == 4  # i=0,3,6,9

        # Strategy distribution
        assert stats["merge_strategies"]["fast-forward"] == 4  # i=0,3,6,9
        assert stats["merge_strategies"]["3-way"] == 3  # i=1,4,7
        assert stats["merge_strategies"]["ai-assisted"] == 3  # i=2,5,8
