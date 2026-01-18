"""
Ralph CLI wrapper for Auto-Claude.
Calls Ralph CLI commands as subprocesses, shares .auto-claude/ directory.
"""
import subprocess
import asyncio
import json
from pathlib import Path
from typing import Optional


class RalphCLI:
    """Wrapper for Ralph CLI commands."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.ralph_executable = self._find_ralph_executable()

    def _find_ralph_executable(self) -> str:
        """Find ralph CLI executable in PATH or local installation."""
        # Check if ralph is in PATH
        try:
            result = subprocess.run(
                ["ralph", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return "ralph"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Check local installation (apps/backend/ralph_cli/)
        local_ralph = self.project_dir / "apps" / "backend" / "ralph_cli" / "main.py"
        if local_ralph.exists():
            return f"python {local_ralph}"

        raise FileNotFoundError(
            "Ralph CLI not found. Install with: pip install ralph-cli or check local installation"
        )

    async def build(
        self,
        spec_name: str,
        model: Optional[str] = None,
        budget: Optional[float] = None,
        verbose: bool = False
    ) -> int:
        """
        Run ralph build command.

        Args:
            spec_name: Spec directory name (e.g., "001-feature")
            model: Model to use (sonnet, opus, haiku)
            budget: Budget limit in USD
            verbose: Enable verbose output

        Returns:
            Exit code (0 = success)
        """
        cmd = self.ralph_executable.split() + ["build", spec_name]

        if model:
            cmd.extend(["--model", model])
        if budget:
            cmd.extend(["--budget", str(budget)])
        if verbose:
            cmd.append("--verbose")

        # Run in project directory
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=self.project_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Stream output in real-time
        async def stream_output(stream, prefix):
            async for line in stream:
                print(f"{prefix}{line.decode().rstrip()}")

        await asyncio.gather(
            stream_output(process.stdout, ""),
            stream_output(process.stderr, "[stderr] ")
        )

        await process.wait()
        return process.returncode

    async def stream_create(self, spec_name: str, stream_name: str) -> int:
        """Create a new Ralph stream (isolated worktree)."""
        cmd = self.ralph_executable.split() + ["stream", "new", stream_name, "--spec", spec_name]
        result = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=self.project_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await result.wait()
        return result.returncode

    async def stream_merge(self, stream_name: str, delete: bool = True) -> int:
        """Merge a Ralph stream back to main branch."""
        cmd = self.ralph_executable.split() + ["stream", "merge", stream_name]
        if delete:
            cmd.append("--delete")
        result = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=self.project_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await result.wait()
        return result.returncode

    def budget_set(self, amount: float, spec: Optional[str] = None) -> int:
        """Set budget limit."""
        cmd = self.ralph_executable.split() + ["budget", "set", str(amount)]
        if spec:
            cmd.extend(["--spec", spec])
        result = subprocess.run(cmd, cwd=self.project_dir, capture_output=True)
        return result.returncode

    def stats(self) -> dict:
        """Get Ralph CLI stats (cost, success rate, etc.)."""
        result = subprocess.run(
            self.ralph_executable.split() + ["stats", "--json"],
            cwd=self.project_dir,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        return {}
