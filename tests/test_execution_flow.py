"""
Tests for execution flow configuration and routing.
"""
import json
import os
import pytest
from pathlib import Path
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "backend"))

from phase_config import get_execution_flow, load_task_metadata


class TestExecutionFlow:
    """Tests for execution flow configuration logic."""

    def test_execution_flow_default(self, tmp_path):
        """Test execution flow defaults to auto_claude."""
        spec_dir = tmp_path / "specs" / "001-test"
        spec_dir.mkdir(parents=True)

        flow = get_execution_flow(spec_dir, cli_flow=None)
        assert flow == "auto_claude"

    def test_execution_flow_cli_override(self, tmp_path):
        """Test CLI argument takes precedence."""
        spec_dir = tmp_path / "specs" / "001-test"
        spec_dir.mkdir(parents=True)

        # Create metadata with auto_claude
        metadata = {"executionFlow": "auto_claude"}
        (spec_dir / "task_metadata.json").write_text(json.dumps(metadata))

        # CLI should override metadata
        flow = get_execution_flow(spec_dir, cli_flow="ralph")
        assert flow == "ralph"

    def test_execution_flow_from_metadata(self, tmp_path):
        """Test execution flow reads from task metadata."""
        spec_dir = tmp_path / "specs" / "001-test"
        spec_dir.mkdir(parents=True)

        # Create metadata with ralph
        metadata = {"executionFlow": "ralph", "budget": 10.0}
        (spec_dir / "task_metadata.json").write_text(json.dumps(metadata))

        flow = get_execution_flow(spec_dir, cli_flow=None)
        assert flow == "ralph"

    def test_execution_flow_from_env(self, tmp_path, monkeypatch):
        """Test execution flow falls back to environment variable."""
        spec_dir = tmp_path / "specs" / "001-test"
        spec_dir.mkdir(parents=True)

        # Set environment variable
        monkeypatch.setenv("EXECUTION_FLOW", "ralph")

        flow = get_execution_flow(spec_dir, cli_flow=None)
        assert flow == "ralph"

    def test_execution_flow_priority(self, tmp_path, monkeypatch):
        """Test configuration priority: CLI > metadata > env > default."""
        spec_dir = tmp_path / "specs" / "001-test"
        spec_dir.mkdir(parents=True)

        # Set env var
        monkeypatch.setenv("EXECUTION_FLOW", "ralph")

        # Set metadata
        metadata = {"executionFlow": "auto_claude"}
        (spec_dir / "task_metadata.json").write_text(json.dumps(metadata))

        # CLI should override everything
        flow = get_execution_flow(spec_dir, cli_flow="ralph")
        assert flow == "ralph"

        # Without CLI, metadata should override env
        flow = get_execution_flow(spec_dir, cli_flow=None)
        assert flow == "auto_claude"

        # Without metadata, should use env
        (spec_dir / "task_metadata.json").unlink()
        flow = get_execution_flow(spec_dir, cli_flow=None)
        assert flow == "ralph"

    def test_task_metadata_storage(self, tmp_path):
        """Test executionFlow and budget are saved to task_metadata.json."""
        spec_dir = tmp_path / "specs" / "001-test"
        spec_dir.mkdir(parents=True)

        # Create metadata with execution flow and budget
        metadata = {
            "executionFlow": "ralph",
            "budget": 15.5,
            "sourceType": "manual",
            "model": "sonnet",
        }
        (spec_dir / "task_metadata.json").write_text(json.dumps(metadata))

        # Load and verify
        loaded = load_task_metadata(spec_dir)
        assert loaded is not None
        assert loaded["executionFlow"] == "ralph"
        assert loaded["budget"] == 15.5

    def test_invalid_execution_flow_env(self, tmp_path, monkeypatch):
        """Test invalid env var is ignored."""
        spec_dir = tmp_path / "specs" / "001-test"
        spec_dir.mkdir(parents=True)

        # Set invalid environment variable
        monkeypatch.setenv("EXECUTION_FLOW", "invalid_flow")

        # Should fall back to default
        flow = get_execution_flow(spec_dir, cli_flow=None)
        assert flow == "auto_claude"

    def test_execution_flow_case_insensitive_env(self, tmp_path, monkeypatch):
        """Test environment variable is case-insensitive."""
        spec_dir = tmp_path / "specs" / "001-test"
        spec_dir.mkdir(parents=True)

        # Set uppercase environment variable
        monkeypatch.setenv("EXECUTION_FLOW", "RALPH")

        flow = get_execution_flow(spec_dir, cli_flow=None)
        assert flow == "ralph"


class TestExecutionFlowRouting:
    """Tests for execution flow routing in build commands."""

    def test_auto_claude_flow_routing(self, tmp_path):
        """Test Auto-Claude flow is selected by default."""
        spec_dir = tmp_path / "specs" / "001-test"
        spec_dir.mkdir(parents=True)

        flow = get_execution_flow(spec_dir, cli_flow=None)
        assert flow == "auto_claude"

    def test_ralph_flow_routing(self, tmp_path):
        """Test Ralph CLI flow is selected when configured."""
        spec_dir = tmp_path / "specs" / "001-test"
        spec_dir.mkdir(parents=True)

        # Create metadata with ralph flow
        metadata = {"executionFlow": "ralph"}
        (spec_dir / "task_metadata.json").write_text(json.dumps(metadata))

        flow = get_execution_flow(spec_dir, cli_flow=None)
        assert flow == "ralph"

    def test_budget_only_used_with_ralph(self, tmp_path):
        """Test budget is only relevant when using Ralph flow."""
        spec_dir = tmp_path / "specs" / "001-test"
        spec_dir.mkdir(parents=True)

        # Create metadata with auto_claude flow and budget
        metadata = {"executionFlow": "auto_claude", "budget": 10.0}
        (spec_dir / "task_metadata.json").write_text(json.dumps(metadata))

        loaded = load_task_metadata(spec_dir)
        flow = loaded.get("executionFlow")

        # Budget exists but should be ignored for auto_claude
        assert flow == "auto_claude"
        assert loaded.get("budget") == 10.0  # Present but ignored
