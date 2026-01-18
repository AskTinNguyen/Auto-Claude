"""
Ralph Stream Command
===================

Worktree/stream management for parallel execution.
"""

import subprocess
import sys
from pathlib import Path

import click

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ..utils.output import (
    console,
    print_success,
    print_error,
    print_warning,
    print_info,
    print_header,
    create_table,
    format_duration,
)


def get_worktree_manager(project_dir: Path):
    """Get WorktreeManager instance."""
    try:
        from core.worktree import WorktreeManager
        return WorktreeManager(project_dir)
    except ImportError:
        print_error("WorktreeManager not available. Make sure you're in an Auto-Claude project.")
        raise SystemExit(1)


@click.group()
@click.pass_context
def stream(ctx) -> None:
    """
    Manage build streams (worktrees).

    Streams allow parallel spec development with isolated git worktrees.

    Examples:
        ralph stream list          # List all streams
        ralph stream new auth      # Create new stream
        ralph stream status        # Show stream status
        ralph stream build auth 5  # Run 5 iterations
        ralph stream merge auth    # Merge to main
        ralph stream cleanup auth  # Remove stream
    """
    pass


@stream.command("list")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.pass_context
def stream_list(ctx, json_output: bool) -> None:
    """
    List all active streams (worktrees).

    Shows all spec worktrees with their status and statistics.
    """
    config = ctx.obj.get("config") if ctx.obj else None
    project_dir = config.project_dir if config else Path.cwd()

    manager = get_worktree_manager(project_dir)
    worktrees = manager.list_all_worktrees()

    if json_output:
        import json
        data = [
            {
                "spec_name": w.spec_name,
                "branch": w.branch,
                "path": str(w.path),
                "commit_count": w.commit_count,
                "files_changed": w.files_changed,
                "additions": w.additions,
                "deletions": w.deletions,
                "days_since_last_commit": w.days_since_last_commit,
            }
            for w in worktrees
        ]
        console.print_json(json.dumps(data))
        return

    print_header("Active Streams", f"Project: {project_dir.name}")

    if not worktrees:
        print_info("No active streams. Create one with 'ralph stream new <name>'")
        return

    table = create_table()
    table.add_column("Stream", style="cyan")
    table.add_column("Branch", style="dim")
    table.add_column("Commits", justify="right")
    table.add_column("Changes", justify="right")
    table.add_column("Age", justify="right")

    for w in sorted(worktrees, key=lambda x: x.spec_name):
        changes = f"+{w.additions}/-{w.deletions}"
        age = f"{w.days_since_last_commit}d" if w.days_since_last_commit is not None else "?"

        table.add_row(
            w.spec_name,
            w.branch,
            str(w.commit_count),
            changes,
            age,
        )

    console.print(table)

    # Check for old worktrees
    warning = manager.get_worktree_count_warning()
    if warning:
        console.print()
        print_warning(warning)


@stream.command("new")
@click.argument("name")
@click.pass_context
def stream_new(ctx, name: str) -> None:
    """
    Create a new stream (worktree).

    NAME is the stream/spec name (e.g., 'auth-feature').

    The stream will be created at:
        .auto-claude/worktrees/tasks/{name}/

    With a branch named:
        auto-claude/{name}
    """
    config = ctx.obj.get("config") if ctx.obj else None
    project_dir = config.project_dir if config else Path.cwd()

    manager = get_worktree_manager(project_dir)

    try:
        info = manager.create_worktree(name)
        print_success(f"Created stream: {info.spec_name}")
        console.print(f"  Path: {info.path}")
        console.print(f"  Branch: {info.branch}")
        console.print()
        console.print("To work in this stream:")
        console.print(f"  cd {info.path}")
    except Exception as e:
        print_error(f"Failed to create stream: {e}")
        raise SystemExit(1)


@stream.command("status")
@click.argument("name", required=False)
@click.pass_context
def stream_status(ctx, name: str | None) -> None:
    """
    Show detailed status of a stream.

    If NAME is not provided, shows status of all streams.
    """
    config = ctx.obj.get("config") if ctx.obj else None
    project_dir = config.project_dir if config else Path.cwd()

    manager = get_worktree_manager(project_dir)

    if name:
        info = manager.get_worktree_info(name)
        if not info:
            print_error(f"Stream not found: {name}")
            raise SystemExit(1)

        print_header(f"Stream: {info.spec_name}")

        table = create_table()
        table.add_column("Property", style="cyan")
        table.add_column("Value")

        table.add_row("Path", str(info.path))
        table.add_row("Branch", info.branch)
        table.add_row("Base Branch", info.base_branch)
        table.add_row("Commits", str(info.commit_count))
        table.add_row("Files Changed", str(info.files_changed))
        table.add_row("Additions", f"+{info.additions}")
        table.add_row("Deletions", f"-{info.deletions}")

        if info.days_since_last_commit is not None:
            table.add_row("Last Activity", f"{info.days_since_last_commit} days ago")

        console.print(table)

        # Show changed files
        files = manager.get_changed_files(name)
        if files:
            console.print()
            console.print("[bold]Changed Files:[/bold]")
            for status, filepath in files[:20]:  # Limit to 20 files
                status_color = {
                    "A": "green",
                    "M": "yellow",
                    "D": "red",
                }.get(status, "white")
                console.print(f"  [{status_color}]{status}[/] {filepath}")
            if len(files) > 20:
                console.print(f"  ... and {len(files) - 20} more files")

    else:
        # Show all streams summary
        manager.print_worktree_summary()


@stream.command("build")
@click.argument("name")
@click.argument("iterations", type=int, default=5)
@click.option("--resume", is_flag=True, help="Resume from last checkpoint")
@click.pass_context
def stream_build(ctx, name: str, iterations: int, resume: bool) -> None:
    """
    Run build iterations in a stream.

    NAME is the stream/spec name.
    ITERATIONS is the number of build iterations (default: 5).

    Example:
        ralph stream build auth 5
    """
    config = ctx.obj.get("config") if ctx.obj else None
    project_dir = config.project_dir if config else Path.cwd()

    manager = get_worktree_manager(project_dir)
    info = manager.get_worktree_info(name)

    if not info:
        print_error(f"Stream not found: {name}")
        raise SystemExit(1)

    print_header(f"Building: {info.spec_name}", f"{iterations} iterations")

    # Find the spec directory
    spec_dir = project_dir / ".auto-claude" / "specs" / name
    if not spec_dir.exists():
        # Try to find matching spec
        specs_dir = project_dir / ".auto-claude" / "specs"
        matches = [d for d in specs_dir.iterdir() if d.is_dir() and name in d.name]
        if matches:
            spec_dir = matches[0]
        else:
            print_error(f"No spec found for stream: {name}")
            raise SystemExit(1)

    # Build the run command
    run_script = project_dir / "apps" / "backend" / "run.py"
    if not run_script.exists():
        print_error("run.py not found. Are you in an Auto-Claude project?")
        raise SystemExit(1)

    cmd = [
        sys.executable,
        str(run_script),
        "--spec", spec_dir.name,
        "--iterations", str(iterations),
    ]

    if resume:
        cmd.append("--resume")

    console.print(f"[dim]Running: {' '.join(cmd)}[/dim]")
    console.print()

    try:
        result = subprocess.run(cmd, cwd=project_dir)
        if result.returncode == 0:
            print_success(f"Build completed for {name}")
        else:
            print_error(f"Build failed with exit code {result.returncode}")
    except KeyboardInterrupt:
        print_warning("Build interrupted")
        raise SystemExit(130)


@stream.command("merge")
@click.argument("name")
@click.option("--delete", is_flag=True, help="Delete stream after merge")
@click.option("--no-commit", is_flag=True, help="Stage changes without committing")
@click.pass_context
def stream_merge(ctx, name: str, delete: bool, no_commit: bool) -> None:
    """
    Merge a stream back to the base branch.

    NAME is the stream/spec name to merge.

    Example:
        ralph stream merge auth --delete
    """
    config = ctx.obj.get("config") if ctx.obj else None
    project_dir = config.project_dir if config else Path.cwd()

    manager = get_worktree_manager(project_dir)
    info = manager.get_worktree_info(name)

    if not info:
        print_error(f"Stream not found: {name}")
        raise SystemExit(1)

    console.print(f"Merging [cyan]{info.branch}[/cyan] into [cyan]{info.base_branch}[/cyan]...")

    success = manager.merge_worktree(name, delete_after=delete, no_commit=no_commit)

    if success:
        print_success(f"Successfully merged {name}")
        if delete:
            print_info(f"Stream {name} has been cleaned up")
    else:
        print_error("Merge failed. Check for conflicts.")
        raise SystemExit(1)


@stream.command("cleanup")
@click.argument("name", required=False)
@click.option("--all", "cleanup_all", is_flag=True, help="Clean up all streams")
@click.option("--old", type=int, help="Clean up streams older than N days")
@click.option("--dry-run", is_flag=True, help="Show what would be removed")
@click.pass_context
def stream_cleanup(ctx, name: str | None, cleanup_all: bool, old: int | None, dry_run: bool) -> None:
    """
    Remove a stream (worktree and branch).

    NAME is the stream/spec name to remove.

    Examples:
        ralph stream cleanup auth          # Remove specific stream
        ralph stream cleanup --all         # Remove all streams
        ralph stream cleanup --old 30      # Remove streams 30+ days old
    """
    config = ctx.obj.get("config") if ctx.obj else None
    project_dir = config.project_dir if config else Path.cwd()

    manager = get_worktree_manager(project_dir)

    if cleanup_all:
        if dry_run:
            worktrees = manager.list_all_worktrees()
            console.print(f"[yellow]Would remove {len(worktrees)} stream(s):[/yellow]")
            for w in worktrees:
                console.print(f"  - {w.spec_name}")
        else:
            if not click.confirm("Remove ALL streams? This cannot be undone."):
                return
            manager.cleanup_all()
            print_success("All streams cleaned up")

    elif old:
        removed, failed = manager.cleanup_old_worktrees(days_threshold=old, dry_run=dry_run)
        if not dry_run:
            if removed:
                print_success(f"Removed {len(removed)} old stream(s)")
            if failed:
                print_warning(f"Failed to remove {len(failed)} stream(s)")

    elif name:
        info = manager.get_worktree_info(name)
        if not info:
            print_error(f"Stream not found: {name}")
            raise SystemExit(1)

        if dry_run:
            console.print(f"[yellow]Would remove:[/yellow] {name}")
            console.print(f"  Path: {info.path}")
            console.print(f"  Branch: {info.branch}")
        else:
            manager.remove_worktree(name, delete_branch=True)
            print_success(f"Removed stream: {name}")

    else:
        print_error("Specify a stream name, --all, or --old <days>")
        raise SystemExit(1)


@stream.command("pr")
@click.argument("name")
@click.option("--title", help="PR title")
@click.option("--draft", is_flag=True, help="Create as draft PR")
@click.pass_context
def stream_pr(ctx, name: str, title: str | None, draft: bool) -> None:
    """
    Push stream and create a pull request.

    NAME is the stream/spec name.

    Example:
        ralph stream pr auth --title "Add authentication"
    """
    config = ctx.obj.get("config") if ctx.obj else None
    project_dir = config.project_dir if config else Path.cwd()

    manager = get_worktree_manager(project_dir)
    info = manager.get_worktree_info(name)

    if not info:
        print_error(f"Stream not found: {name}")
        raise SystemExit(1)

    console.print(f"Creating PR for [cyan]{info.branch}[/cyan]...")

    result = manager.push_and_create_pr(
        spec_name=name,
        title=title,
        draft=draft,
    )

    if result.get("success"):
        if result.get("already_exists"):
            print_info(f"PR already exists: {result.get('pr_url', 'URL not available')}")
        else:
            print_success(f"PR created: {result.get('pr_url', 'URL not available')}")
    else:
        print_error(f"Failed to create PR: {result.get('error', 'Unknown error')}")
        raise SystemExit(1)
