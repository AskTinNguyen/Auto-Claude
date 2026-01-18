"""
Ralph CLI wrapper for Auto-Claude.
Calls Ralph CLI commands as subprocesses, shares .auto-claude/ directory.

Ralph CLI uses a PRD-based workflow:
  - `ralph prd` - Generate a PRD
  - `ralph plan` - Create implementation plan
  - `ralph build [n]` - Execute n build iterations

This wrapper bridges Auto-Claude specs to Ralph's PRD system by:
1. Creating prd.md from spec.md (symlink or copy)
2. Syncing progress.md back to implementation_plan.json for Kanban visibility
"""
import subprocess
import asyncio
import json
import re
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime


def sync_spec_to_prd(spec_dir: Path) -> bool:
    """
    Ensure Ralph can find PRD files in the Auto-Claude spec directory.

    Creates prd.md from spec.md if it doesn't exist.

    Args:
        spec_dir: Path to the Auto-Claude spec directory

    Returns:
        True if prd.md is available, False otherwise
    """
    prd_file = spec_dir / "prd.md"
    spec_file = spec_dir / "spec.md"

    # If prd.md already exists, we're good
    if prd_file.exists():
        return True

    # Create prd.md from spec.md
    if spec_file.exists():
        try:
            # Create a symlink so changes are reflected in both
            prd_file.symlink_to(spec_file.name)
            return True
        except OSError:
            # If symlink fails (e.g., Windows), copy the file
            shutil.copy2(spec_file, prd_file)
            return True

    return False


def sync_progress_to_plan(spec_dir: Path) -> bool:
    """
    Sync Ralph's progress.md to Auto-Claude's implementation_plan.json.

    This makes Ralph builds visible in the Kanban view.

    Args:
        spec_dir: Path to the spec directory

    Returns:
        True if sync was successful, False otherwise
    """
    progress_file = spec_dir / "progress.md"
    plan_file = spec_dir / "implementation_plan.json"

    if not progress_file.exists():
        return False

    try:
        progress_content = progress_file.read_text()

        # Load existing plan or create new one
        if plan_file.exists():
            plan = json.loads(plan_file.read_text())
        else:
            plan = {
                "subtasks": [],
                "created_at": datetime.now().isoformat(),
                "status": "in_progress"
            }

        # Parse Ralph's progress.md format
        # Ralph uses checkboxes: - [x] Story 1, - [ ] Story 2
        completed_stories = []
        pending_stories = []

        for line in progress_content.split("\n"):
            line = line.strip()
            if line.startswith("- [x]") or line.startswith("- [X]"):
                story_text = line[5:].strip()
                completed_stories.append(story_text)
            elif line.startswith("- [ ]"):
                story_text = line[5:].strip()
                pending_stories.append(story_text)

        # Extract commit info if present
        commit_pattern = r"Commit:\s*([a-f0-9]{7,40})"
        commits = re.findall(commit_pattern, progress_content)

        # Update plan with Ralph's progress
        plan["ralph_progress"] = {
            "completed_stories": len(completed_stories),
            "pending_stories": len(pending_stories),
            "total_stories": len(completed_stories) + len(pending_stories),
            "last_sync": datetime.now().isoformat(),
            "commits": commits[:10]  # Keep last 10 commits
        }

        # Update subtask statuses if they match story names
        for subtask in plan.get("subtasks", []):
            subtask_title = subtask.get("title", "").lower()
            for story in completed_stories:
                if story.lower() in subtask_title or subtask_title in story.lower():
                    subtask["status"] = "completed"
                    break

        # Update overall status
        if len(pending_stories) == 0 and len(completed_stories) > 0:
            plan["status"] = "completed"
        elif len(completed_stories) > 0:
            plan["status"] = "in_progress"

        plan_file.write_text(json.dumps(plan, indent=2))
        return True

    except Exception as e:
        print(f"[warn] Failed to sync progress: {e}")
        return False


def ensure_ralph_files(spec_dir: Path) -> None:
    """
    Ensure Ralph's required files exist in the spec directory.

    Creates empty progress.md, errors.log, activity.log if missing.
    """
    (spec_dir / "progress.md").touch()
    (spec_dir / "errors.log").touch()
    (spec_dir / "activity.log").touch()


class RalphCLI:
    """Wrapper for Ralph CLI commands."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.ralph_executable = self._find_ralph_executable()

    def _find_ralph_executable(self) -> str:
        """Find ralph CLI executable in PATH."""
        # Check if ralph is in PATH by running help command
        try:
            result = subprocess.run(
                ["ralph", "help"],
                capture_output=True,
                text=True,
                timeout=5
            )
            # Ralph CLI returns 0 for help command
            if result.returncode == 0 and "ralph <command>" in result.stdout:
                return "ralph"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        raise FileNotFoundError(
            "Ralph CLI not found. Install from: https://github.com/tinnguyen/ralph-cli\n"
            "Or run: cd /path/to/ralph-cli && npm link"
        )

    async def build(
        self,
        spec_dir: Path,
        iterations: int = 5,
        model: Optional[str] = None,
        budget: Optional[float] = None,
        resume: bool = False,
        auto_fix: Optional[str] = None
    ) -> int:
        """
        Run ralph build command.

        Args:
            spec_dir: Path to the spec directory (used as --prd path)
            iterations: Number of build iterations (default: 5)
            model: Model to use (sonnet, opus, haiku) for cost calculation
            budget: Budget limit in USD (set before build)
            resume: Resume from last checkpoint
            auto_fix: Auto-fix mode (none, safe, all)

        Returns:
            Exit code (0 = success)
        """
        # Prepare spec directory for Ralph CLI
        # 1. Create prd.md from spec.md (symlink)
        if not sync_spec_to_prd(spec_dir):
            print("[warn] Could not create prd.md from spec.md")

        # 2. Ensure Ralph's required files exist
        ensure_ralph_files(spec_dir)

        # Set budget first if specified
        if budget:
            budget_result = self.budget_set(budget, prd_path=spec_dir)
            if budget_result != 0:
                print(f"[warn] Failed to set budget: {budget}")

        # Build command: ralph build [n] --prd=<path>
        cmd = [self.ralph_executable, "build", str(iterations)]
        cmd.extend(["--prd", str(spec_dir)])

        if model:
            cmd.extend(["--model", model])
        if resume:
            cmd.append("--resume")
        if auto_fix:
            cmd.extend(["--auto-fix", auto_fix])

        # Run in project directory
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=self.project_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Stream output in real-time and sync progress periodically
        last_sync = 0
        sync_interval = 10  # Sync every 10 lines of output

        async def stream_output(stream, prefix):
            nonlocal last_sync
            line_count = 0
            async for line in stream:
                print(f"{prefix}{line.decode().rstrip()}")
                line_count += 1

                # Periodically sync progress for Kanban visibility
                if line_count - last_sync >= sync_interval:
                    sync_progress_to_plan(spec_dir)
                    last_sync = line_count

        await asyncio.gather(
            stream_output(process.stdout, ""),
            stream_output(process.stderr, "[stderr] ")
        )

        await process.wait()

        # Final sync after build completes
        sync_progress_to_plan(spec_dir)

        return process.returncode

    async def plan(self, spec_dir: Path, iterations: int = 1) -> int:
        """
        Create implementation plan from PRD.

        Args:
            spec_dir: Path to the spec directory (used as --prd path)
            iterations: Number of planning iterations

        Returns:
            Exit code (0 = success)
        """
        cmd = [self.ralph_executable, "plan", str(iterations)]
        cmd.extend(["--prd", str(spec_dir)])

        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=self.project_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        async def stream_output(stream, prefix):
            async for line in stream:
                print(f"{prefix}{line.decode().rstrip()}")

        await asyncio.gather(
            stream_output(process.stdout, ""),
            stream_output(process.stderr, "[stderr] ")
        )

        await process.wait()
        return process.returncode

    async def stream_init(self, stream_number: int) -> int:
        """Initialize a Ralph stream worktree for parallel work."""
        cmd = [self.ralph_executable, "stream", "init", str(stream_number)]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=self.project_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.wait()
        return process.returncode

    async def stream_build(
        self,
        stream_number: int,
        iterations: int = 5,
        prd_path: Optional[Path] = None
    ) -> int:
        """Run build iterations in a specific stream."""
        cmd = [self.ralph_executable, "stream", "build", str(stream_number), str(iterations)]
        if prd_path:
            cmd.extend(["--prd", str(prd_path)])

        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=self.project_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        async def stream_output(stream, prefix):
            async for line in stream:
                print(f"{prefix}{line.decode().rstrip()}")

        await asyncio.gather(
            stream_output(process.stdout, ""),
            stream_output(process.stderr, "[stderr] ")
        )

        await process.wait()
        return process.returncode

    async def stream_merge(self, stream_number: int) -> int:
        """Merge a completed stream back to main branch."""
        cmd = [self.ralph_executable, "stream", "merge", str(stream_number)]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=self.project_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.wait()
        return process.returncode

    async def stream_cleanup(self, stream_number: int) -> int:
        """Remove a stream worktree."""
        cmd = [self.ralph_executable, "stream", "cleanup", str(stream_number)]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=self.project_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.wait()
        return process.returncode

    def budget_set(self, amount: float, prd_path: Optional[Path] = None) -> int:
        """Set budget limit for builds."""
        cmd = [self.ralph_executable, "budget", "set", str(amount)]
        if prd_path:
            cmd.extend(["--prd", str(prd_path)])
        result = subprocess.run(cmd, cwd=self.project_dir, capture_output=True)
        return result.returncode

    def budget_show(self, prd_path: Optional[Path] = None) -> dict:
        """Show budget status."""
        cmd = [self.ralph_executable, "budget", "show"]
        if prd_path:
            cmd.extend(["--prd", str(prd_path)])
        result = subprocess.run(
            cmd,
            cwd=self.project_dir,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return {"output": result.stdout, "status": "ok"}
        return {"output": result.stderr, "status": "error"}

    def stats(self, global_stats: bool = False, json_output: bool = True) -> dict:
        """Get Ralph CLI stats (cost, success rate, etc.)."""
        cmd = [self.ralph_executable, "stats"]
        if global_stats:
            cmd.append("--global")
        if json_output:
            cmd.append("--json")

        result = subprocess.run(
            cmd,
            cwd=self.project_dir,
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and json_output:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {"raw": result.stdout}
        return {"raw": result.stdout if result.returncode == 0 else result.stderr}

    def estimate(self, prd_path: Optional[Path] = None) -> dict:
        """Estimate time and cost for a PRD."""
        cmd = [self.ralph_executable, "estimate", "--json"]
        if prd_path:
            cmd.extend(["--prd", str(prd_path)])

        result = subprocess.run(
            cmd,
            cwd=self.project_dir,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {"raw": result.stdout}
        return {"error": result.stderr}
