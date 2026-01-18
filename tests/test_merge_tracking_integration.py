#!/usr/bin/env python3
"""
Integration Tests for Merge Tracking Flow
==========================================

Tests the end-to-end merge completion tracking system, from merge
execution through persistence and querying.

Covers:
- Merge completion recording during merge operations
- Persistence of merge history to storage
- Querying merge history by spec and globally
- Statistics aggregation across multiple merges
- Integration with workspace merge functions
"""

import sys
from pathlib import Path

import pytest

# Add auto-claude directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "backend"))
# Add tests directory to path for test_fixtures
sys.path.insert(0, str(Path(__file__).parent))

from core.workspace.merge_completion import (
    MergeCompletion,
    MergeCompletionStorage,
    create_merge_completion,
)
from test_fixtures import (
    SAMPLE_PYTHON_MODULE,
    SAMPLE_PYTHON_WITH_NEW_FUNCTION,
    SAMPLE_PYTHON_WITH_NEW_IMPORT,
)


class TestMergeTrackingIntegration:
    """Integration tests for complete merge tracking flow."""

    def test_merge_creates_completion_record(self, temp_project):
        """Merge operation creates and persists completion record."""
        storage = MergeCompletionStorage(temp_project)

        # Simulate a merge operation
        merge = create_merge_completion(
            spec_name="task-001",
            resolved_files=["src/utils.py", "src/App.tsx"],
            stats={
                "conflicts_resolved": 2,
                "ai_assisted_count": 1,
                "auto_merged_count": 1,
                "git_conflicts": 0,
                "merge_strategy": "ai-assisted",
            },
        )

        # Record the merge
        storage.record_merge(merge)

        # Verify persistence
        history = storage.get_merge_history()
        assert len(history) == 1
        assert history[0].spec_name == "task-001"
        assert len(history[0].resolved_files) == 2

    def test_multiple_merges_tracked_separately(self, temp_project):
        """Multiple merge operations are tracked independently."""
        storage = MergeCompletionStorage(temp_project)

        # Record two merges for different specs
        merge1 = create_merge_completion(
            spec_name="task-001",
            resolved_files=["src/utils.py"],
            stats={
                "conflicts_resolved": 1,
                "ai_assisted_count": 0,
                "auto_merged_count": 1,
                "merge_strategy": "3-way",
            },
        )
        storage.record_merge(merge1)

        merge2 = create_merge_completion(
            spec_name="task-002",
            resolved_files=["src/App.tsx"],
            stats={
                "conflicts_resolved": 1,
                "ai_assisted_count": 1,
                "auto_merged_count": 0,
                "merge_strategy": "ai-assisted",
            },
        )
        storage.record_merge(merge2)

        # Verify both are tracked
        history = storage.get_merge_history()
        assert len(history) == 2

        # Verify spec-specific queries
        task1_history = storage.get_merge_history("task-001")
        assert len(task1_history) == 1
        assert task1_history[0].spec_name == "task-001"

        task2_history = storage.get_merge_history("task-002")
        assert len(task2_history) == 1
        assert task2_history[0].spec_name == "task-002"

    def test_merge_history_query_by_strategy(self, temp_project):
        """Merge history can be queried by merge strategy."""
        storage = MergeCompletionStorage(temp_project)

        # Record merges with different strategies
        for i, strategy in enumerate(["3-way", "ai-assisted", "fast-forward"]):
            merge = create_merge_completion(
                spec_name=f"task-{i:03d}",
                resolved_files=[f"file{i}.py"],
                stats={"merge_strategy": strategy},
            )
            storage.record_merge(merge)

        # Query by strategy
        ai_merges = storage.get_merges_by_strategy("ai-assisted")
        assert len(ai_merges) == 1
        assert ai_merges[0].merge_strategy == "ai-assisted"

        three_way_merges = storage.get_merges_by_strategy("3-way")
        assert len(three_way_merges) == 1
        assert three_way_merges[0].merge_strategy == "3-way"

    def test_merge_statistics_aggregation(self, temp_project):
        """Merge statistics aggregate correctly across multiple merges."""
        storage = MergeCompletionStorage(temp_project)

        # Record three merges with different characteristics
        merges_data = [
            {
                "spec_name": "task-001",
                "files": ["file1.py", "file2.py"],
                "conflicts": 2,
                "ai_assisted": 1,
            },
            {
                "spec_name": "task-002",
                "files": ["file3.py"],
                "conflicts": 1,
                "ai_assisted": 0,
            },
            {
                "spec_name": "task-003",
                "files": ["file1.py", "file4.py"],
                "conflicts": 3,
                "ai_assisted": 2,
            },
        ]

        for data in merges_data:
            merge = create_merge_completion(
                spec_name=data["spec_name"],
                resolved_files=data["files"],
                stats={
                    "conflicts_resolved": data["conflicts"],
                    "ai_assisted_count": data["ai_assisted"],
                },
            )
            storage.record_merge(merge)

        # Get aggregate statistics
        stats = storage.get_merge_stats_summary()

        assert stats["total_merges"] == 3
        assert stats["successful_merges"] == 3
        assert stats["total_conflicts_resolved"] == 6  # 2 + 1 + 3
        assert stats["total_ai_assisted"] == 3  # 1 + 0 + 2
        # Unique files: file1.py, file2.py, file3.py, file4.py
        assert stats["total_files_merged"] == 4

    def test_failed_merge_tracking(self, temp_project):
        """Failed merges are tracked with error information."""
        storage = MergeCompletionStorage(temp_project)

        # Record a failed merge
        merge = create_merge_completion(
            spec_name="task-001",
            resolved_files=["src/utils.py"],
            stats={"conflicts_resolved": 0},
            success=False,
            error_message="Git conflict could not be resolved",
        )
        storage.record_merge(merge)

        # Verify failed merge tracking
        history = storage.get_merge_history()
        assert len(history) == 1
        assert history[0].success is False
        assert history[0].error_message == "Git conflict could not be resolved"

        # Verify query methods
        failed_merges = storage.get_failed_merges()
        assert len(failed_merges) == 1

        successful_merges = storage.get_successful_merges()
        assert len(successful_merges) == 0

    def test_merge_with_conflicts_tracking(self, temp_project):
        """Merges with conflicts are properly tracked."""
        storage = MergeCompletionStorage(temp_project)

        # Record merges with and without conflicts
        merge_with_conflicts = create_merge_completion(
            spec_name="task-001",
            resolved_files=["src/utils.py"],
            stats={
                "conflicts_resolved": 3,
                "ai_assisted_count": 2,
            },
        )
        storage.record_merge(merge_with_conflicts)

        merge_no_conflicts = create_merge_completion(
            spec_name="task-002",
            resolved_files=["src/other.py"],
            stats={
                "conflicts_resolved": 0,
                "auto_merged_count": 1,
            },
        )
        storage.record_merge(merge_no_conflicts)

        # Query merges with conflicts
        conflict_merges = storage.get_merges_with_conflicts()
        assert len(conflict_merges) == 1
        assert conflict_merges[0].conflicts_resolved == 3

        # Query AI-assisted merges
        ai_merges = storage.get_ai_assisted_merges()
        assert len(ai_merges) == 1
        assert ai_merges[0].ai_assisted_count == 2

    def test_file_merge_frequency_tracking(self, temp_project):
        """Files merged multiple times are tracked correctly."""
        storage = MergeCompletionStorage(temp_project)

        # Record multiple merges touching some common files
        merges_data = [
            {"spec": "task-001", "files": ["src/utils.py", "src/App.tsx"]},
            {"spec": "task-002", "files": ["src/utils.py", "src/helpers.py"]},
            {"spec": "task-003", "files": ["src/utils.py"]},
        ]

        for data in merges_data:
            merge = create_merge_completion(
                spec_name=data["spec"],
                resolved_files=data["files"],
                stats={},
            )
            storage.record_merge(merge)

        # Get files merged multiple times
        multi_merged = storage.get_files_merged_multiple_times()
        assert "src/utils.py" in multi_merged
        assert len(multi_merged["src/utils.py"]) == 3  # Merged in all 3 tasks

        # Get most merged files
        most_merged = storage.get_most_merged_files(limit=5)
        assert len(most_merged) > 0
        # src/utils.py should be first (merged 3 times)
        assert most_merged[0][0] == "src/utils.py"
        assert most_merged[0][1] == 3

    def test_spec_merge_count(self, temp_project):
        """Spec merge count tracks multiple merges of same spec."""
        storage = MergeCompletionStorage(temp_project)

        # Record multiple merges for the same spec
        for i in range(3):
            merge = create_merge_completion(
                spec_name="task-001",
                resolved_files=[f"file{i}.py"],
                stats={},
            )
            storage.record_merge(merge)

        # Verify count
        count = storage.get_spec_merge_count("task-001")
        assert count == 3

        # Different spec should have 0
        count = storage.get_spec_merge_count("task-002")
        assert count == 0

    def test_all_specs_merged_list(self, temp_project):
        """Get list of all specs that have been merged."""
        storage = MergeCompletionStorage(temp_project)

        # Record merges for different specs
        spec_names = ["task-001", "task-002", "feature-003"]
        for spec in spec_names:
            merge = create_merge_completion(
                spec_name=spec,
                resolved_files=["file.py"],
                stats={},
            )
            storage.record_merge(merge)

        # Get all specs
        all_specs = storage.get_all_specs_merged()
        assert len(all_specs) == 3
        assert set(all_specs) == set(spec_names)
        # Should be sorted
        assert all_specs == sorted(spec_names)

    def test_merge_history_persistence_across_instances(self, temp_project):
        """Merge history persists across storage instances."""
        # Create first storage instance and record merge
        storage1 = MergeCompletionStorage(temp_project)
        merge = create_merge_completion(
            spec_name="task-001",
            resolved_files=["src/utils.py"],
            stats={"conflicts_resolved": 1},
        )
        storage1.record_merge(merge)

        # Create new storage instance (simulates new process)
        storage2 = MergeCompletionStorage(temp_project)
        history = storage2.get_merge_history()

        # Should have same merge record
        assert len(history) == 1
        assert history[0].spec_name == "task-001"
        assert len(history[0].resolved_files) == 1

    def test_storage_directory_creation(self, temp_dir):
        """Storage directory is created if it doesn't exist."""
        # Use a non-existent directory
        project_dir = temp_dir / "nonexistent"

        # Creating storage should create the directory
        storage = MergeCompletionStorage(project_dir)

        # Verify directory was created
        assert storage.storage_dir.exists()
        assert storage.storage_dir.is_dir()


class TestMergeTrackingWithRealMerges:
    """Integration tests using real merge scenarios."""

    def test_compatible_changes_merge_tracking(self, temp_project):
        """Compatible changes from different tasks are tracked."""
        storage = MergeCompletionStorage(temp_project)

        # Simulate two compatible merges
        merge1 = create_merge_completion(
            spec_name="task-001",
            resolved_files=["src/utils.py"],
            stats={
                "conflicts_resolved": 0,
                "auto_merged_count": 1,
                "merge_strategy": "3-way",
            },
        )
        storage.record_merge(merge1)

        merge2 = create_merge_completion(
            spec_name="task-002",
            resolved_files=["src/utils.py"],
            stats={
                "conflicts_resolved": 0,
                "auto_merged_count": 1,
                "merge_strategy": "3-way",
            },
        )
        storage.record_merge(merge2)

        # Both should be tracked
        history = storage.get_merge_history()
        assert len(history) == 2

        # Verify statistics
        stats = storage.get_merge_stats_summary()
        assert stats["total_merges"] == 2
        assert stats["merge_strategies"]["3-way"] == 2

    def test_conflicting_changes_merge_tracking(self, temp_project):
        """Conflicting changes requiring AI are tracked."""
        storage = MergeCompletionStorage(temp_project)

        # Simulate merge with conflicts resolved by AI
        merge = create_merge_completion(
            spec_name="task-001",
            resolved_files=["src/utils.py"],
            stats={
                "conflicts_resolved": 1,
                "ai_assisted_count": 1,
                "auto_merged_count": 0,
                "git_conflicts": 0,
                "merge_strategy": "ai-assisted",
            },
        )
        storage.record_merge(merge)

        # Verify tracking
        history = storage.get_merge_history()
        assert len(history) == 1
        assert history[0].merge_strategy == "ai-assisted"
        assert history[0].ai_assisted_count == 1

        # Verify query methods
        ai_merges = storage.get_ai_assisted_merges()
        assert len(ai_merges) == 1

        conflict_merges = storage.get_merges_with_conflicts()
        assert len(conflict_merges) == 1
