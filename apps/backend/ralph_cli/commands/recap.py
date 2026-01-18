"""
Ralph Recap Command
==================

Summarize and speak recent activity or agent responses.
"""

import json
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
)


def get_tts_manager():
    """Get TTS manager instance."""
    try:
        from integrations.tts.manager import TTSManager
        return TTSManager()
    except ImportError:
        print_error("TTS module not available. Make sure you're in an Auto-Claude project.")
        raise SystemExit(1)


def summarize_text(text: str, max_words: int) -> str:
    """Summarize text to a maximum number of words."""
    words = text.split()
    if len(words) <= max_words:
        return text

    # Take first N words and add ellipsis
    return " ".join(words[:max_words]) + "..."


def get_latest_activity(project_dir: Path, spec_name: str | None = None) -> dict | None:
    """Get the latest activity from spec directories."""
    specs_dir = project_dir / ".auto-claude" / "specs"

    if not specs_dir.exists():
        return None

    # Find spec to summarize
    if spec_name:
        spec_dirs = [specs_dir / spec_name]
        if not spec_dirs[0].exists():
            # Try prefix match
            matches = [d for d in specs_dir.iterdir() if d.is_dir() and d.name.startswith(spec_name)]
            if matches:
                spec_dirs = matches
            else:
                return None
    else:
        # Get most recent spec by modification time
        spec_dirs = sorted(
            [d for d in specs_dir.iterdir() if d.is_dir()],
            key=lambda d: d.stat().st_mtime,
            reverse=True,
        )

    if not spec_dirs:
        return None

    spec_dir = spec_dirs[0]

    activity = {
        "spec_name": spec_dir.name,
        "summary": None,
        "qa_status": None,
        "subtasks_complete": 0,
        "subtasks_total": 0,
        "cost": 0.0,
    }

    # Check QA report
    qa_file = spec_dir / "qa_report.md"
    if qa_file.exists():
        content = qa_file.read_text(encoding="utf-8")
        if "APPROVED" in content or "✓" in content:
            activity["qa_status"] = "passed"
        elif "REJECTED" in content or "✗" in content:
            activity["qa_status"] = "failed"
        else:
            activity["qa_status"] = "pending"

        # Extract summary from QA report
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if "summary" in line.lower() or "## " in line:
                # Get next few lines as summary
                summary_lines = lines[i+1:i+5]
                activity["summary"] = " ".join(summary_lines).strip()[:500]
                break

    # Check implementation plan for progress
    plan_file = spec_dir / "implementation_plan.json"
    if plan_file.exists():
        try:
            plan = json.loads(plan_file.read_text(encoding="utf-8"))
            subtasks = plan.get("subtasks", [])
            activity["subtasks_total"] = len(subtasks)
            activity["subtasks_complete"] = sum(
                1 for s in subtasks if s.get("status") == "completed"
            )
        except (json.JSONDecodeError, OSError):
            pass

    # Check cost report
    cost_file = spec_dir / "cost_report.json"
    if cost_file.exists():
        try:
            cost_data = json.loads(cost_file.read_text(encoding="utf-8"))
            activity["cost"] = cost_data.get("total_cost_usd", 0)
        except (json.JSONDecodeError, OSError):
            pass

    # Generate summary if not found
    if not activity["summary"]:
        spec_file = spec_dir / "spec.md"
        if spec_file.exists():
            content = spec_file.read_text(encoding="utf-8")
            # Get first paragraph after title
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if line.strip() and not line.startswith("#"):
                    activity["summary"] = " ".join(lines[i:i+3]).strip()[:500]
                    break

    return activity


@click.command()
@click.option("--full", is_flag=True, help="Full recap (200 words)")
@click.option("--short", is_flag=True, help="Short recap (30 words)")
@click.option("--preview", is_flag=True, help="Show without speaking")
@click.option("--spec", help="Specific spec to recap")
@click.pass_context
def recap(ctx, full: bool, short: bool, preview: bool, spec: str | None) -> None:
    """
    Summarize and speak recent activity.

    Generates a summary of the latest spec activity and speaks it using TTS.

    Examples:
        ralph recap              # Default recap (100 words)
        ralph recap --short      # Brief recap (30 words)
        ralph recap --full       # Full recap (200 words)
        ralph recap --preview    # Show summary without speaking
        ralph recap --spec 001   # Recap specific spec
    """
    config = ctx.obj.get("config") if ctx.obj else None
    project_dir = config.project_dir if config else Path.cwd()

    # Get latest activity
    activity = get_latest_activity(project_dir, spec)

    if not activity:
        print_warning("No recent activity found")
        return

    # Determine word limit
    if full:
        max_words = 200
    elif short:
        max_words = 30
    else:
        max_words = 100

    # Build recap text
    parts = []

    parts.append(f"Recap for {activity['spec_name']}.")

    # Progress
    if activity["subtasks_total"] > 0:
        parts.append(
            f"Progress: {activity['subtasks_complete']} of {activity['subtasks_total']} subtasks complete."
        )

    # QA status
    if activity["qa_status"]:
        if activity["qa_status"] == "passed":
            parts.append("Quality assurance passed.")
        elif activity["qa_status"] == "failed":
            parts.append("Quality assurance found issues.")
        else:
            parts.append("Quality assurance pending.")

    # Cost
    if activity["cost"] > 0:
        parts.append(f"Cost so far: ${activity['cost']:.2f}.")

    # Summary
    if activity["summary"]:
        parts.append(summarize_text(activity["summary"], max_words // 2))

    recap_text = " ".join(parts)
    recap_text = summarize_text(recap_text, max_words)

    # Display header
    print_header(f"Recap: {activity['spec_name']}")

    # Display status
    if activity["subtasks_total"] > 0:
        progress_pct = (activity["subtasks_complete"] / activity["subtasks_total"]) * 100
        console.print(f"Progress: {activity['subtasks_complete']}/{activity['subtasks_total']} ({progress_pct:.0f}%)")

    if activity["qa_status"]:
        qa_colors = {
            "passed": "green",
            "failed": "red",
            "pending": "yellow",
        }
        color = qa_colors.get(activity["qa_status"], "white")
        console.print(f"QA Status: [{color}]{activity['qa_status']}[/]")

    if activity["cost"] > 0:
        console.print(f"Cost: ${activity['cost']:.2f}")

    console.print()
    console.print("[bold]Summary:[/bold]")
    console.print(recap_text)

    # Speak unless preview
    if not preview:
        console.print()
        tts = get_tts_manager()
        if tts.speak(recap_text):
            print_success("Recap spoken")
        else:
            print_warning("Could not speak recap. Check TTS status with 'ralph speak --status'")
