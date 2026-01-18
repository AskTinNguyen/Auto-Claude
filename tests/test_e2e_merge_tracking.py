"""
End-to-End Merge Tracking Verification Test

This test verifies the complete merge tracking flow:
1. Create a test spec with code changes
2. Trigger a merge with conflicts
3. Verify _record_merge_completion is called
4. Check merge completion is persisted to .auto-claude/merge-history/
5. Verify merge history can be queried via backend API
"""

import json
import shutil
import tempfile
from pathlib import Path
from datetime import datetime

import pytest

from apps.backend.core.workspace import _record_merge_completion, get_merge_history
from apps.backend.core.workspace.merge_completion import (
    MergeCompletion,
    MergeCompletionStorage,
    create_merge_completion,
)


class TestE2EMergeTracking:
    """End-to-end tests for merge completion tracking."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory with .auto-claude structure."""
        temp_dir = Path(tempfile.mkdtemp())

        # Create .auto-claude structure
        auto_claude_dir = temp_dir / ".auto-claude"
        auto_claude_dir.mkdir(parents=True, exist_ok=True)

        # Create merge-history directory
        merge_history_dir = auto_claude_dir / "merge-history"
        merge_history_dir.mkdir(parents=True, exist_ok=True)

        yield temp_dir

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_e2e_merge_tracking_flow(self, temp_project_dir):
        """Test complete flow from merge to UI display."""

        # Step 1: Simulate a merge with code changes
        spec_name = "test-feature-001"
        resolved_files = [
            "apps/backend/core/workspace.py",
            "apps/backend/core/workspace/merge_completion.py",
            "apps/frontend/src/components/MergeHistory.tsx",
        ]

        stats = {
            "conflicts_resolved": 3,
            "ai_assisted": 2,
            "auto_merged": 1,
            "git_conflicts": 3,
            "merge_strategy": "ai-assisted",
            "duration_seconds": 45.5,
        }

        # Step 2: Trigger merge completion recording
        _record_merge_completion(
            project_dir=temp_project_dir,
            spec_name=spec_name,
            resolved_files=resolved_files,
            stats=stats,
        )

        # Step 3: Verify merge completion is persisted
        merge_history_file = temp_project_dir / ".auto-claude" / "merge-history" / "merge_history.json"
        assert merge_history_file.exists(), "Merge history file should be created"

        # Load and verify JSON structure
        with open(merge_history_file) as f:
            history_data = json.load(f)

        assert isinstance(history_data, list), "History should be a list"
        assert len(history_data) == 1, "Should have one merge record"

        merge_record = history_data[0]

        # Step 4: Verify all metadata is correctly stored
        assert merge_record["spec_name"] == spec_name
        assert merge_record["resolved_files"] == resolved_files
        assert merge_record["conflicts_resolved"] == 3
        assert merge_record["ai_assisted_count"] == 2
        assert merge_record["auto_merged_count"] == 1
        assert merge_record["git_conflicts"] == 3
        assert merge_record["merge_strategy"] == "ai-assisted"
        assert merge_record["success"] is True
        assert merge_record["duration_seconds"] == 45.5
        assert "merge_id" in merge_record
        assert "timestamp" in merge_record

        # Step 5: Verify merge history can be queried via backend API
        merge_history = get_merge_history(
            spec_name=spec_name,
            project_dir=str(temp_project_dir),
        )

        assert isinstance(merge_history, list)
        assert len(merge_history) == 1

        returned_merge = merge_history[0]
        assert returned_merge["spec_name"] == spec_name
        assert returned_merge["conflicts_resolved"] == 3
        assert returned_merge["ai_assisted_count"] == 2

        # Step 6: Verify storage layer queries work correctly
        storage = MergeCompletionStorage(project_dir=temp_project_dir)

        # Query by spec name
        spec_merges = storage.get_merge_history(spec_name=spec_name)
        assert len(spec_merges) == 1
        assert spec_merges[0].spec_name == spec_name

        # Query recent merges
        recent = storage.get_recent_merges(limit=10)
        assert len(recent) == 1

        # Query by strategy
        ai_assisted = storage.get_merges_by_strategy("ai-assisted")
        assert len(ai_assisted) == 1

        # Get stats summary
        stats_summary = storage.get_merge_stats_summary(spec_name)
        assert stats_summary["total_merges"] == 1
        assert stats_summary["successful_merges"] == 1
        assert stats_summary["total_conflicts_resolved"] == 3
        assert stats_summary["total_ai_assisted"] == 2
        assert stats_summary["average_duration"] == 45.5
        assert stats_summary["merge_strategies"]["ai-assisted"] == 1

    def test_multiple_merges_for_same_spec(self, temp_project_dir):
        """Test that multiple merges for the same spec are all tracked."""

        spec_name = "test-feature-002"

        # First merge
        _record_merge_completion(
            project_dir=temp_project_dir,
            spec_name=spec_name,
            resolved_files=["file1.py", "file2.py"],
            stats={
                "conflicts_resolved": 2,
                "ai_assisted": 1,
                "auto_merged": 1,
            },
        )

        # Second merge (e.g., after fixing issues)
        _record_merge_completion(
            project_dir=temp_project_dir,
            spec_name=spec_name,
            resolved_files=["file3.py"],
            stats={
                "conflicts_resolved": 1,
                "ai_assisted": 0,
                "auto_merged": 1,
            },
        )

        # Verify both merges are tracked
        merge_history = get_merge_history(
            spec_name=spec_name,
            project_dir=str(temp_project_dir),
        )

        assert len(merge_history) == 2

        # Verify they're sorted by timestamp (newest first)
        timestamps = [m["timestamp"] for m in merge_history]
        # First in list should be newer than second
        assert timestamps[0] >= timestamps[1]

    def test_merge_tracking_with_conflicts(self, temp_project_dir):
        """Test merge tracking when conflicts occur."""

        spec_name = "test-feature-with-conflicts"

        # Merge with git conflicts
        _record_merge_completion(
            project_dir=temp_project_dir,
            spec_name=spec_name,
            resolved_files=["conflicted_file.py"],
            stats={
                "conflicts_resolved": 5,
                "ai_assisted": 5,
                "auto_merged": 0,
                "git_conflicts": 5,
                "merge_strategy": "ai-assisted",
            },
        )

        storage = MergeCompletionStorage(project_dir=temp_project_dir)

        # Query merges with conflicts
        merges_with_conflicts = storage.get_merges_with_conflicts()
        assert len(merges_with_conflicts) == 1
        assert merges_with_conflicts[0].conflicts_resolved == 5

        # Query AI-assisted merges
        ai_merges = storage.get_ai_assisted_merges()
        assert len(ai_merges) == 1
        assert ai_merges[0].ai_assisted_count == 5

    def test_merge_tracking_fast_forward(self, temp_project_dir):
        """Test merge tracking for fast-forward merges (no conflicts)."""

        spec_name = "test-fast-forward"

        # Fast-forward merge (no conflicts)
        _record_merge_completion(
            project_dir=temp_project_dir,
            spec_name=spec_name,
            resolved_files=["new_feature.py"],
            stats={
                "conflicts_resolved": 0,
                "ai_assisted": 0,
                "auto_merged": 0,
            },
        )

        storage = MergeCompletionStorage(project_dir=temp_project_dir)
        merges = storage.get_merge_history(spec_name)

        assert len(merges) == 1
        assert merges[0].merge_strategy == "fast-forward"
        assert merges[0].conflicts_resolved == 0

    def test_query_merge_history_across_specs(self, temp_project_dir):
        """Test querying merge history across multiple specs."""

        # Create merges for different specs
        specs = ["spec-A", "spec-B", "spec-C"]

        for spec in specs:
            _record_merge_completion(
                project_dir=temp_project_dir,
                spec_name=spec,
                resolved_files=[f"{spec}_file.py"],
                stats={"conflicts_resolved": 1, "ai_assisted": 0},
            )

        # Query all merge history (no spec filter)
        all_merges = get_merge_history(project_dir=str(temp_project_dir))
        assert len(all_merges) == 3

        # Query specific spec
        spec_a_merges = get_merge_history(
            spec_name="spec-A",
            project_dir=str(temp_project_dir),
        )
        assert len(spec_a_merges) == 1
        assert spec_a_merges[0]["spec_name"] == "spec-A"

        # Verify all specs are tracked
        storage = MergeCompletionStorage(project_dir=temp_project_dir)
        all_specs = storage.get_all_specs_merged()
        assert set(all_specs) == set(specs)

    def test_merge_stats_summary(self, temp_project_dir):
        """Test merge statistics summary generation."""

        spec_name = "test-stats"

        # Create multiple merges with different outcomes
        _record_merge_completion(
            project_dir=temp_project_dir,
            spec_name=spec_name,
            resolved_files=["file1.py", "file2.py"],
            stats={
                "conflicts_resolved": 3,
                "ai_assisted": 2,
                "duration_seconds": 30.0,
            },
        )

        _record_merge_completion(
            project_dir=temp_project_dir,
            spec_name=spec_name,
            resolved_files=["file3.py"],
            stats={
                "conflicts_resolved": 1,
                "ai_assisted": 1,
                "duration_seconds": 15.0,
            },
        )

        storage = MergeCompletionStorage(project_dir=temp_project_dir)
        stats = storage.get_merge_stats_summary(spec_name)

        assert stats["total_merges"] == 2
        assert stats["successful_merges"] == 2
        assert stats["total_conflicts_resolved"] == 4
        assert stats["total_ai_assisted"] == 3
        assert stats["total_files_merged"] == 3  # Unique files
        assert stats["average_duration"] == 22.5  # (30 + 15) / 2

    def test_merge_completion_data_model(self, temp_project_dir):
        """Test MergeCompletion data model serialization."""

        # Create merge completion record
        merge = create_merge_completion(
            spec_name="test-model",
            resolved_files=["file1.py", "file2.py"],
            stats={
                "conflicts_resolved": 2,
                "ai_assisted_count": 1,
                "auto_merged_count": 1,
                "git_conflicts": 2,
                "merge_strategy": "ai-assisted",
                "duration_seconds": 42.0,
            },
            success=True,
        )

        # Verify object properties
        assert merge.spec_name == "test-model"
        assert merge.resolved_files == ["file1.py", "file2.py"]
        assert merge.conflicts_resolved == 2
        assert merge.ai_assisted_count == 1
        assert merge.success is True

        # Test serialization
        merge_dict = merge.to_dict()
        assert merge_dict["spec_name"] == "test-model"
        assert merge_dict["conflicts_resolved"] == 2

        # Test deserialization
        restored = MergeCompletion.from_dict(merge_dict)
        assert restored.spec_name == merge.spec_name
        assert restored.conflicts_resolved == merge.conflicts_resolved
        assert restored.timestamp == merge.timestamp

    def test_frontend_ipc_data_format(self, temp_project_dir):
        """Test that merge history data format matches frontend expectations."""

        spec_name = "test-frontend-format"

        # Create a merge
        _record_merge_completion(
            project_dir=temp_project_dir,
            spec_name=spec_name,
            resolved_files=["app.tsx", "styles.css"],
            stats={
                "conflicts_resolved": 2,
                "ai_assisted": 1,
                "auto_merged": 1,
                "git_conflicts": 2,
                "merge_strategy": "ai-assisted",
                "duration_seconds": 30.5,
            },
        )

        # Get merge history via API (as frontend would)
        merge_history = get_merge_history(
            spec_name=spec_name,
            project_dir=str(temp_project_dir),
        )

        # Verify format matches frontend MergeHistoryRecord interface
        assert len(merge_history) == 1
        record = merge_history[0]

        # Required fields for frontend
        required_fields = [
            "merge_id",
            "spec_name",
            "timestamp",
            "resolved_files",
            "conflicts_resolved",
            "ai_assisted_count",
            "auto_merged_count",
            "git_conflicts",
            "merge_strategy",
            "success",
        ]

        for field in required_fields:
            assert field in record, f"Missing required field: {field}"

        # Verify data types
        assert isinstance(record["merge_id"], str)
        assert isinstance(record["spec_name"], str)
        assert isinstance(record["timestamp"], str)  # ISO format
        assert isinstance(record["resolved_files"], list)
        assert isinstance(record["conflicts_resolved"], int)
        assert isinstance(record["ai_assisted_count"], int)
        assert isinstance(record["success"], bool)
        assert record["merge_strategy"] in ["fast-forward", "3-way", "ai-assisted", "manual"]

        # Optional fields
        assert "error_message" in record
        assert "duration_seconds" in record
        assert record["duration_seconds"] == 30.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
