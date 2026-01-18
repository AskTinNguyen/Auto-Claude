"""
Tests for Ralph CLI wrapper module.
"""
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "backend"))

from integrations.ralph_cli import RalphCLI


class TestRalphCLI:
    """Tests for RalphCLI wrapper class."""

    def test_find_ralph_executable_in_path(self, tmp_path):
        """Test Ralph CLI executable discovery in PATH."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            ralph = RalphCLI(tmp_path)
            assert ralph.ralph_executable == "ralph"

    def test_find_ralph_executable_local(self, tmp_path):
        """Test Ralph CLI executable discovery in local installation."""
        # Create local ralph installation
        local_ralph_dir = tmp_path / "apps" / "backend" / "ralph_cli"
        local_ralph_dir.mkdir(parents=True)
        local_ralph_path = local_ralph_dir / "main.py"
        local_ralph_path.touch()

        with patch("subprocess.run") as mock_run:
            # Simulate ralph not in PATH
            mock_run.side_effect = FileNotFoundError()

            ralph = RalphCLI(tmp_path)
            assert "main.py" in ralph.ralph_executable

    def test_find_ralph_executable_not_found(self, tmp_path):
        """Test Ralph CLI executable not found raises error."""
        with patch("subprocess.run") as mock_run:
            # Simulate ralph not in PATH
            mock_run.side_effect = FileNotFoundError()

            with pytest.raises(FileNotFoundError, match="Ralph CLI not found"):
                RalphCLI(tmp_path)

    @pytest.mark.asyncio
    async def test_ralph_build_command(self, tmp_path):
        """Test Ralph build wrapper calls subprocess correctly."""
        with patch("subprocess.run") as mock_run:
            # Mock ralph in PATH
            mock_run.return_value = MagicMock(returncode=0)
            ralph = RalphCLI(tmp_path)

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            # Create mock process
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.stdout = AsyncMock()
            mock_process.stderr = AsyncMock()
            mock_process.wait = AsyncMock(return_value=None)

            # Configure async iterators for stdout/stderr
            async def async_iter_empty(self):
                return
                yield  # Make it an async generator

            mock_process.stdout.__aiter__ = async_iter_empty
            mock_process.stderr.__aiter__ = async_iter_empty

            mock_subprocess.return_value = mock_process

            exit_code = await ralph.build(
                spec_name="001-test", model="sonnet", budget=10.0, verbose=True
            )

            assert exit_code == 0
            # Verify subprocess was called
            mock_subprocess.assert_called_once()
            call_args = mock_subprocess.call_args
            # Verify command includes expected parts
            assert "build" in call_args[0]
            assert "001-test" in call_args[0]

    @pytest.mark.asyncio
    async def test_ralph_build_with_budget(self, tmp_path):
        """Test Ralph build with budget parameter."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            ralph = RalphCLI(tmp_path)

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.stdout = AsyncMock()
            mock_process.stderr = AsyncMock()
            mock_process.wait = AsyncMock(return_value=None)

            async def async_iter_empty(self):
                return
                yield

            mock_process.stdout.__aiter__ = async_iter_empty
            mock_process.stderr.__aiter__ = async_iter_empty

            mock_subprocess.return_value = mock_process

            exit_code = await ralph.build(
                spec_name="001-test", model="sonnet", budget=5.0
            )

            assert exit_code == 0
            call_args = mock_subprocess.call_args
            # Verify budget is in command
            assert "--budget" in call_args[0]
            assert "5.0" in call_args[0]

    def test_ralph_budget_set(self, tmp_path):
        """Test budget setting command."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            ralph = RalphCLI(tmp_path)

            # Mock budget set command
            mock_run.return_value = MagicMock(returncode=0)
            exit_code = ralph.budget_set(amount=10.0, spec="001-test")

            assert exit_code == 0
            # Verify subprocess.run was called with budget command
            assert mock_run.called

    def test_ralph_stats(self, tmp_path):
        """Test Ralph CLI stats retrieval."""
        with patch("subprocess.run") as mock_run:
            # Mock ralph in PATH
            mock_run.return_value = MagicMock(returncode=0)
            ralph = RalphCLI(tmp_path)

            # Mock stats command with JSON output
            mock_run.return_value = MagicMock(
                returncode=0, stdout='{"cost": 1.23, "success_rate": 0.95}'
            )
            stats = ralph.stats()

            assert isinstance(stats, dict)
