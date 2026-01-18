"""
Ralph Doctor Command
===================

Environment diagnostics and setup verification.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import click

from ralph_cli.utils.output import (
    console,
    print_success,
    print_error,
    print_warning,
    print_info,
    print_header,
    create_table,
)


def check_python_version() -> tuple[bool, str]:
    """Check Python version (3.12+ required)."""
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    if version.major >= 3 and version.minor >= 12:
        return True, version_str
    return False, version_str


def check_executable(name: str, version_flag: str = "--version") -> tuple[bool, str]:
    """Check if an executable is available and get its version."""
    try:
        result = subprocess.run(
            [name, version_flag],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            # Extract first line of version output
            version = result.stdout.strip().split("\n")[0]
            return True, version
        return False, "Not found"
    except FileNotFoundError:
        return False, "Not installed"
    except subprocess.TimeoutExpired:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)


def check_claude_cli() -> tuple[bool, str]:
    """Check if Claude CLI is installed and authenticated."""
    # Check if claude is available
    available, version = check_executable("claude", "--version")
    if not available:
        return False, "Claude CLI not installed"

    # Check authentication (claude auth status)
    try:
        result = subprocess.run(
            ["claude", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and "authenticated" in result.stdout.lower():
            return True, f"{version} (authenticated)"
        return False, f"{version} (not authenticated)"
    except Exception:
        return True, version  # Assume OK if auth check fails


def check_git_repo(project_dir: Path) -> tuple[bool, str]:
    """Check if directory is a git repository."""
    git_dir = project_dir / ".git"
    if git_dir.exists():
        # Get current branch
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                branch = result.stdout.strip()
                return True, f"On branch: {branch}"
        except Exception:
            pass
        return True, "Initialized"
    return False, "Not a git repository"


def check_auto_claude_dir(project_dir: Path) -> tuple[bool, str]:
    """Check if .auto-claude directory structure exists."""
    auto_claude_dir = project_dir / ".auto-claude"
    if not auto_claude_dir.exists():
        return False, "Directory not found"

    # Check for specs directory
    specs_dir = auto_claude_dir / "specs"
    if specs_dir.exists():
        spec_count = len(list(specs_dir.iterdir())) if specs_dir.is_dir() else 0
        return True, f"{spec_count} spec(s)"

    return True, "Empty (no specs)"


def check_env_file(project_dir: Path) -> tuple[bool, str]:
    """Check if .env file exists in backend."""
    env_file = project_dir / "apps" / "backend" / ".env"
    if env_file.exists():
        # Check for required variables
        content = env_file.read_text()
        missing = []
        if "CLAUDE_CODE_OAUTH_TOKEN" not in content:
            missing.append("CLAUDE_CODE_OAUTH_TOKEN")
        if missing:
            return False, f"Missing: {', '.join(missing)}"
        return True, "Configured"

    # Check for .env.example
    example_file = project_dir / "apps" / "backend" / ".env.example"
    if example_file.exists():
        return False, "Not configured (copy from .env.example)"
    return False, "Not found"


def check_tts_availability() -> tuple[bool, str]:
    """Check if TTS providers are available."""
    providers = []

    # Check Piper
    piper_available, _ = check_executable("piper", "--help")
    if piper_available:
        providers.append("Piper")

    # Check macOS say
    if sys.platform == "darwin":
        say_available, _ = check_executable("say", "--help")
        if say_available:
            providers.append("macOS")

    # Check espeak (Linux)
    if sys.platform == "linux":
        espeak_available, _ = check_executable("espeak", "--help")
        if espeak_available:
            providers.append("espeak")

    if providers:
        return True, ", ".join(providers)
    return False, "No TTS providers found"


def check_node_version() -> tuple[bool, str]:
    """Check Node.js version."""
    available, version = check_executable("node", "--version")
    if available:
        # Parse version (v20.10.0 -> 20.10.0)
        ver = version.replace("v", "").strip()
        try:
            major = int(ver.split(".")[0])
            if major >= 18:
                return True, version
            return False, f"{version} (18+ required)"
        except ValueError:
            return True, version
    return False, "Not installed"


def check_uv_available() -> tuple[bool, str]:
    """Check if uv is available."""
    return check_executable("uv", "--version")


@click.command()
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
@click.option("--fix", is_flag=True, help="Attempt to fix issues automatically")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def doctor(verbose: bool, fix: bool, output_json: bool) -> None:
    """
    Run environment diagnostics.

    Checks Python version, dependencies, configuration, and tool availability.
    """
    project_dir = Path.cwd()
    checks: list[tuple[str, bool, str]] = []

    print_header("Ralph Environment Check", "Diagnosing your Auto-Claude setup")

    # Run all checks
    with console.status("[bold blue]Running diagnostics...[/bold blue]"):
        # Python version
        passed, info = check_python_version()
        checks.append(("Python 3.12+", passed, info))

        # Claude CLI
        passed, info = check_claude_cli()
        checks.append(("Claude CLI", passed, info))

        # uv
        passed, info = check_uv_available()
        checks.append(("uv (package manager)", passed, info))

        # Node.js
        passed, info = check_node_version()
        checks.append(("Node.js 18+", passed, info))

        # Git repository
        passed, info = check_git_repo(project_dir)
        checks.append(("Git Repository", passed, info))

        # .auto-claude directory
        passed, info = check_auto_claude_dir(project_dir)
        checks.append((".auto-claude directory", passed, info))

        # .env file
        passed, info = check_env_file(project_dir)
        checks.append(("Environment (.env)", passed, info))

        # TTS
        passed, info = check_tts_availability()
        checks.append(("TTS Providers", passed, info))

        # Git executable
        passed, info = check_executable("git", "--version")
        checks.append(("Git", passed, info))

        # gh CLI (optional)
        passed, info = check_executable("gh", "--version")
        checks.append(("GitHub CLI (gh)", passed, info))

    # Output results
    if output_json:
        import json
        result = {
            "passed": all(c[1] for c in checks if c[0] not in ["TTS Providers", "GitHub CLI (gh)"]),
            "checks": [
                {"name": name, "passed": passed, "info": info}
                for name, passed, info in checks
            ]
        }
        console.print_json(json.dumps(result))
        return

    # Display results table
    table = create_table("Check Results")
    table.add_column("Check", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Details", style="dim")

    passed_count = 0
    failed_count = 0
    warning_count = 0

    for name, passed, info in checks:
        # Some checks are optional
        is_optional = name in ["TTS Providers", "GitHub CLI (gh)"]

        if passed:
            status = "[green]✓ Pass[/green]"
            passed_count += 1
        elif is_optional:
            status = "[yellow]○ Optional[/yellow]"
            warning_count += 1
        else:
            status = "[red]✗ Fail[/red]"
            failed_count += 1

        table.add_row(name, status, info)

    console.print(table)
    console.print()

    # Summary
    if failed_count == 0:
        print_success(f"All required checks passed! ({passed_count} passed, {warning_count} optional)")
    else:
        print_error(f"{failed_count} check(s) failed, {passed_count} passed, {warning_count} optional")

    # Fix suggestions
    if fix and failed_count > 0:
        console.print()
        print_header("Attempting Fixes", "Running automatic repairs")

        for name, passed, info in checks:
            if passed:
                continue

            if name == ".auto-claude directory":
                auto_claude_dir = project_dir / ".auto-claude"
                specs_dir = auto_claude_dir / "specs"
                try:
                    specs_dir.mkdir(parents=True, exist_ok=True)
                    print_success(f"Created {auto_claude_dir}")
                except Exception as e:
                    print_error(f"Could not create directory: {e}")

            elif name == "Environment (.env)":
                env_file = project_dir / "apps" / "backend" / ".env"
                example_file = project_dir / "apps" / "backend" / ".env.example"
                if example_file.exists() and not env_file.exists():
                    try:
                        shutil.copy(example_file, env_file)
                        print_success(f"Copied .env.example to .env")
                        print_warning("Please edit .env and add your CLAUDE_CODE_OAUTH_TOKEN")
                    except Exception as e:
                        print_error(f"Could not copy .env: {e}")

    elif failed_count > 0 and not fix:
        console.print()
        print_info("Run with --fix to attempt automatic repairs")

    # Verbose output
    if verbose:
        console.print()
        print_header("System Information")
        console.print(f"  Platform: {sys.platform}")
        console.print(f"  Python: {sys.executable}")
        console.print(f"  Working Directory: {project_dir}")
        console.print(f"  PATH: {os.environ.get('PATH', 'N/A')[:100]}...")


if __name__ == "__main__":
    doctor()
