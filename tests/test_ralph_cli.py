"""
Tests for Ralph CLI
==================

Tests for all ralph CLI commands.
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "backend"))

from ralph_cli.main import cli
from ralph_cli.config import RalphConfig, CLIConfig, BudgetConfig


@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner()


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project structure."""
    # Initialize git repo (needed for stream commands)
    import subprocess
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, capture_output=True)
    # Create initial commit so HEAD exists
    (tmp_path / "README.md").write_text("# Test Project\n")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=tmp_path, capture_output=True)

    # Create .auto-claude directory structure
    auto_claude_dir = tmp_path / ".auto-claude"
    specs_dir = auto_claude_dir / "specs"
    specs_dir.mkdir(parents=True)

    # Create a sample spec
    spec_dir = specs_dir / "001-test-feature"
    spec_dir.mkdir()

    # spec.md
    (spec_dir / "spec.md").write_text("""
# Test Feature

## Overview
This is a test feature for the CLI.

## Acceptance Criteria
- [ ] Feature works correctly
- [ ] Tests pass
""")

    # context.json
    (spec_dir / "context.json").write_text(json.dumps({
        "files_analyzed": 10,
        "dependencies": ["click", "rich"],
    }))

    # implementation_plan.json
    (spec_dir / "implementation_plan.json").write_text(json.dumps({
        "subtasks": [
            {"id": 1, "name": "Task 1", "status": "completed"},
            {"id": 2, "name": "Task 2", "status": "pending"},
        ]
    }))

    # cost_report.json
    (spec_dir / "cost_report.json").write_text(json.dumps({
        "total_cost_usd": 1.25,
        "total_input_tokens": 5000,
        "total_output_tokens": 3000,
        "sessions": [{"id": "session-1"}],
        "created_at": "2026-01-01T00:00:00Z",
        "last_updated": "2026-01-18T00:00:00Z",
    }))

    # qa_report.md
    (spec_dir / "qa_report.md").write_text("""
# QA Report

## Summary
All tests passed. APPROVED.

## Criteria
✓ Feature works correctly
✓ Tests pass
""")

    return tmp_path


class TestCLIBasics:
    """Test basic CLI functionality."""

    def test_cli_help(self, runner):
        """Test that CLI shows help."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Ralph CLI" in result.output

    def test_cli_version(self, runner):
        """Test that CLI shows version."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "1.0.0" in result.output


class TestDoctorCommand:
    """Test the doctor command."""

    def test_doctor_basic(self, runner, temp_project):
        """Test doctor command runs."""
        result = runner.invoke(cli, ["doctor"], catch_exceptions=False)
        # Doctor may fail some checks, but should run
        assert "Ralph Environment Check" in result.output

    def test_doctor_json_output(self, runner, temp_project):
        """Test doctor JSON output."""
        result = runner.invoke(cli, ["doctor", "--json"])
        # Should produce JSON
        assert "checks" in result.output


class TestStatsCommand:
    """Test the stats command."""

    def test_stats_basic(self, runner, temp_project):
        """Test stats command with project data."""
        os.chdir(temp_project)
        result = runner.invoke(cli, ["stats"])
        # Should show some stats
        assert result.exit_code == 0 or "No specs" in result.output

    def test_stats_no_specs(self, runner, tmp_path):
        """Test stats with no specs directory."""
        os.chdir(tmp_path)
        result = runner.invoke(cli, ["stats"])
        assert result.exit_code != 0 or "No specs" in result.output


class TestBudgetCommand:
    """Test the budget command."""

    def test_budget_set(self, runner, temp_project):
        """Test setting a budget."""
        os.chdir(temp_project)
        result = runner.invoke(cli, ["budget", "set", "10.00"])
        assert result.exit_code == 0
        assert "Budget set" in result.output or "10.00" in result.output

    def test_budget_show(self, runner, temp_project):
        """Test showing budget status."""
        os.chdir(temp_project)
        # First set a budget
        runner.invoke(cli, ["budget", "set", "10.00"])
        # Then show it
        result = runner.invoke(cli, ["budget", "show"])
        assert result.exit_code == 0

    def test_budget_clear(self, runner, temp_project):
        """Test clearing a budget."""
        os.chdir(temp_project)
        # Set then clear
        runner.invoke(cli, ["budget", "set", "10.00"])
        result = runner.invoke(cli, ["budget", "clear"])
        assert result.exit_code == 0
        assert "cleared" in result.output.lower()


class TestEstimateCommand:
    """Test the estimate command."""

    def test_estimate_basic(self, runner, temp_project):
        """Test estimate command with spec."""
        os.chdir(temp_project)
        result = runner.invoke(cli, ["estimate", "--spec", "001-test-feature"])
        # Should show cost estimate
        assert result.exit_code == 0
        assert "Cost Estimate" in result.output or "Token" in result.output

    def test_estimate_json(self, runner, temp_project):
        """Test estimate JSON output."""
        os.chdir(temp_project)
        result = runner.invoke(cli, ["estimate", "--spec", "001-test-feature", "--json"])
        assert result.exit_code == 0
        # Should be valid JSON
        data = json.loads(result.output)
        assert "estimated_cost_usd" in data


class TestStreamCommand:
    """Test the stream command."""

    def test_stream_list(self, runner, temp_project):
        """Test listing streams."""
        os.chdir(temp_project)
        result = runner.invoke(cli, ["stream", "list"])
        # May have no streams, but should run
        assert result.exit_code == 0

    def test_stream_help(self, runner):
        """Test stream help."""
        result = runner.invoke(cli, ["stream", "--help"])
        assert result.exit_code == 0
        assert "worktree" in result.output.lower() or "stream" in result.output.lower()


class TestSpeakCommand:
    """Test the speak command."""

    def test_speak_status(self, runner, temp_project):
        """Test speak status."""
        os.chdir(temp_project)
        result = runner.invoke(cli, ["speak", "--status"])
        # Should show TTS status (may fail if TTS not available)
        assert "TTS" in result.output or "Status" in result.output

    def test_speak_list_voices(self, runner):
        """Test listing voices."""
        result = runner.invoke(cli, ["speak", "--list-voices"])
        assert result.exit_code == 0
        assert "voice" in result.output.lower()


class TestRecapCommand:
    """Test the recap command."""

    def test_recap_preview(self, runner, temp_project):
        """Test recap with preview (no speaking)."""
        os.chdir(temp_project)
        result = runner.invoke(cli, ["recap", "--preview"])
        # Should show recap text
        assert "Recap" in result.output or "001-test-feature" in result.output


class TestReviewCommand:
    """Test the review command."""

    def test_review_basic(self, runner, temp_project):
        """Test review command."""
        os.chdir(temp_project)
        result = runner.invoke(cli, ["review", "001-test-feature"])
        assert result.exit_code == 0
        assert "Review" in result.output or "Score" in result.output

    def test_review_json(self, runner, temp_project):
        """Test review JSON output."""
        os.chdir(temp_project)
        result = runner.invoke(cli, ["review", "001-test-feature", "--json"])
        assert result.exit_code == 0
        # Should be valid JSON
        data = json.loads(result.output)
        assert "score" in data[0] or "spec_name" in data[0]


class TestInitCommand:
    """Test the init command."""

    def test_init_creates_config(self, runner, tmp_path):
        """Test init creates config file."""
        os.chdir(tmp_path)
        result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0
        assert (tmp_path / ".ralph-config.yaml").exists()


class TestPingCommand:
    """Test the ping command."""

    def test_ping_basic(self, runner, temp_project):
        """Test ping command."""
        os.chdir(temp_project)
        result = runner.invoke(cli, ["ping"])
        # Should run and show some status
        assert "Ralph Ping" in result.output or "Claude" in result.output


class TestConfig:
    """Test configuration loading."""

    def test_config_defaults(self, tmp_path):
        """Test default configuration."""
        config = RalphConfig.load(tmp_path)
        assert config.cli.enabled is True
        assert config.cli.color is True
        assert config.defaults.model == "claude-sonnet-4-5-20250929"

    def test_config_save_load(self, tmp_path):
        """Test saving and loading configuration."""
        config = RalphConfig.load(tmp_path)
        config.budget.global_limit_usd = 50.0
        config.tts.auto_speak = True
        config.save()

        # Reload and verify
        config2 = RalphConfig.load(tmp_path)
        assert config2.budget.global_limit_usd == 50.0
        assert config2.tts.auto_speak is True

    def test_config_env_override(self, tmp_path, monkeypatch):
        """Test environment variable overrides."""
        monkeypatch.setenv("RALPH_CLI_VERBOSE", "true")
        monkeypatch.setenv("RALPH_DEFAULT_MODEL", "claude-opus-4-5-20250929")
        monkeypatch.setenv("RALPH_BUDGET_LIMIT", "100.0")

        config = RalphConfig.load(tmp_path)
        assert config.cli.verbose is True
        assert config.defaults.model == "claude-opus-4-5-20250929"
        assert config.budget.global_limit_usd == 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
