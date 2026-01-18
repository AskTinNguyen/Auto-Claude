#!/usr/bin/env python3
"""
Ralph CLI Main Entry Point
=========================

Main dispatcher for all ralph commands.

Usage:
    ralph doctor          # Environment diagnostics
    ralph stats           # Performance metrics
    ralph budget set 10   # Budget management
    ralph estimate        # Cost estimation
    ralph stream list     # Worktree management
    ralph speak "Hello"   # TTS control
    ralph recap           # Summarize and speak
    ralph review          # Quality review
"""

import sys
from pathlib import Path

import click

from .config import RalphConfig
from .commands import doctor, stats, budget, estimate, stream, speak, recap, review
from .utils.output import console, print_header


@click.group()
@click.version_option(version="1.0.0", prog_name="ralph")
@click.option("--project", "-p", type=click.Path(exists=True), help="Project directory")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def cli(ctx: click.Context, project: str | None, verbose: bool) -> None:
    """
    Ralph CLI - Autonomous coding workflow automation.

    Ralph helps you manage specs, builds, budgets, and quality for Auto-Claude projects.
    """
    ctx.ensure_object(dict)

    # Load configuration
    project_dir = Path(project) if project else Path.cwd()
    config = RalphConfig.load(project_dir)
    config.cli.verbose = verbose or config.cli.verbose

    ctx.obj["config"] = config
    ctx.obj["project_dir"] = project_dir


# Register all commands
cli.add_command(doctor)
cli.add_command(stats)
cli.add_command(budget)
cli.add_command(estimate)
cli.add_command(stream)
cli.add_command(speak)
cli.add_command(recap)
cli.add_command(review)


@cli.command()
@click.pass_context
def init(ctx: click.Context) -> None:
    """
    Initialize Ralph in the current project.

    Creates .ralph-config.yaml with default settings.
    """
    config = ctx.obj.get("config")
    project_dir = ctx.obj.get("project_dir", Path.cwd())

    config_file = project_dir / ".ralph-config.yaml"
    if config_file.exists():
        console.print("[yellow]Configuration already exists:[/yellow]")
        console.print(f"  {config_file}")
        return

    # Create default config
    config.save()
    console.print("[green]✓[/green] Created .ralph-config.yaml")
    console.print()
    console.print("Edit the config file to customize Ralph settings.")


@cli.command()
@click.pass_context
def ping(ctx: click.Context) -> None:
    """
    Verify connection to Claude and Auto-Claude services.

    Quick health check to ensure everything is working.
    """
    import subprocess

    print_header("Ralph Ping", "Checking service connections")

    checks = []

    # Check Claude CLI
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            checks.append(("Claude CLI", True, result.stdout.strip().split("\n")[0]))
        else:
            checks.append(("Claude CLI", False, "Not responding"))
    except FileNotFoundError:
        checks.append(("Claude CLI", False, "Not installed"))
    except subprocess.TimeoutExpired:
        checks.append(("Claude CLI", False, "Timeout"))

    # Check project structure
    config = ctx.obj.get("config")
    project_dir = ctx.obj.get("project_dir", Path.cwd())

    auto_claude_dir = project_dir / ".auto-claude"
    if auto_claude_dir.exists():
        specs_count = len(list((auto_claude_dir / "specs").iterdir())) if (auto_claude_dir / "specs").exists() else 0
        checks.append((".auto-claude", True, f"{specs_count} spec(s)"))
    else:
        checks.append((".auto-claude", False, "Not initialized"))

    # Check config file
    config_file = project_dir / ".ralph-config.yaml"
    if config_file.exists():
        checks.append(("Ralph Config", True, "Found"))
    else:
        checks.append(("Ralph Config", False, "Not found (using defaults)"))

    # Display results
    for name, passed, info in checks:
        if passed:
            console.print(f"[green]✓[/green] {name}: {info}")
        else:
            console.print(f"[red]✗[/red] {name}: {info}")

    console.print()
    if all(c[1] for c in checks):
        console.print("[green]All systems operational![/green]")
    else:
        console.print("[yellow]Some checks failed. Run 'ralph doctor' for details.[/yellow]")


def main() -> None:
    """Main entry point for the ralph CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
