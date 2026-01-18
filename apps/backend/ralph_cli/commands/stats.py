"""
Ralph Stats Command
==================

Performance metrics and analytics dashboard.
"""

import json
from datetime import datetime
from pathlib import Path

import click

from ..utils.output import (
    console,
    print_success,
    print_error,
    print_warning,
    print_info,
    print_header,
    create_table,
    format_cost,
    format_tokens,
    format_percentage,
)


def load_cost_reports(specs_dir: Path) -> list[dict]:
    """Load all cost reports from spec directories."""
    reports = []

    if not specs_dir.exists():
        return reports

    for spec_dir in specs_dir.iterdir():
        if not spec_dir.is_dir():
            continue

        cost_file = spec_dir / "cost_report.json"
        if cost_file.exists():
            try:
                with open(cost_file, encoding="utf-8") as f:
                    data = json.load(f)
                    data["spec_name"] = spec_dir.name
                    reports.append(data)
            except (json.JSONDecodeError, OSError):
                continue

    return reports


def load_qa_reports(specs_dir: Path) -> list[dict]:
    """Load all QA reports from spec directories."""
    reports = []

    if not specs_dir.exists():
        return reports

    for spec_dir in specs_dir.iterdir():
        if not spec_dir.is_dir():
            continue

        qa_file = spec_dir / "qa_report.md"
        if qa_file.exists():
            try:
                content = qa_file.read_text(encoding="utf-8")
                # Parse basic info from QA report
                passed = "APPROVED" in content or "✓" in content
                reports.append({
                    "spec_name": spec_dir.name,
                    "passed": passed,
                })
            except OSError:
                continue

    return reports


def calculate_aggregate_stats(cost_reports: list[dict], qa_reports: list[dict]) -> dict:
    """Calculate aggregate statistics from reports."""
    total_cost = 0.0
    total_input_tokens = 0
    total_output_tokens = 0
    total_sessions = 0

    for report in cost_reports:
        total_cost += report.get("total_cost_usd", 0)
        total_input_tokens += report.get("total_input_tokens", 0)
        total_output_tokens += report.get("total_output_tokens", 0)
        total_sessions += len(report.get("sessions", []))

    # Calculate QA stats
    qa_passed = sum(1 for r in qa_reports if r.get("passed"))
    qa_total = len(qa_reports)
    success_rate = (qa_passed / qa_total * 100) if qa_total > 0 else 0

    # Calculate averages
    spec_count = len(cost_reports)
    avg_cost = total_cost / spec_count if spec_count > 0 else 0

    return {
        "total_specs": spec_count,
        "total_sessions": total_sessions,
        "total_cost_usd": total_cost,
        "avg_cost_per_spec": avg_cost,
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "total_tokens": total_input_tokens + total_output_tokens,
        "qa_passed": qa_passed,
        "qa_total": qa_total,
        "success_rate": success_rate,
    }


@click.command()
@click.option("--global", "global_stats", is_flag=True, help="Show stats across all projects")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.option("--tokens", is_flag=True, help="Show detailed token breakdown")
@click.option("--spec", help="Show stats for specific spec")
@click.pass_context
def stats(ctx, global_stats: bool, json_output: bool, tokens: bool, spec: str | None) -> None:
    """
    Show performance metrics and analytics.

    Displays statistics about builds, costs, token usage, and success rates.
    """
    config = ctx.obj.get("config") if ctx.obj else None
    project_dir = config.project_dir if config else Path.cwd()
    specs_dir = project_dir / ".auto-claude" / "specs"

    if not specs_dir.exists():
        print_error("No specs directory found. Run some builds first!")
        raise SystemExit(1)

    # Load reports
    cost_reports = load_cost_reports(specs_dir)
    qa_reports = load_qa_reports(specs_dir)

    if not cost_reports:
        print_warning("No cost reports found. Run some builds first!")
        return

    # Single spec stats
    if spec:
        spec_report = next((r for r in cost_reports if r["spec_name"] == spec), None)
        if not spec_report:
            print_error(f"No stats found for spec: {spec}")
            raise SystemExit(1)

        if json_output:
            console.print_json(data=spec_report)
            return

        print_header(f"Stats: {spec}")

        table = create_table()
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")

        table.add_row("Total Cost", format_cost(spec_report.get("total_cost_usd", 0)))
        table.add_row("Input Tokens", format_tokens(spec_report.get("total_input_tokens", 0)))
        table.add_row("Output Tokens", format_tokens(spec_report.get("total_output_tokens", 0)))
        table.add_row("Sessions", str(len(spec_report.get("sessions", []))))
        table.add_row("Created", spec_report.get("created_at", "unknown")[:10])
        table.add_row("Last Updated", spec_report.get("last_updated", "unknown")[:10])

        console.print(table)
        return

    # Aggregate stats
    aggregate = calculate_aggregate_stats(cost_reports, qa_reports)

    if json_output:
        console.print_json(data=aggregate)
        return

    print_header("Ralph Performance Dashboard", f"Project: {project_dir.name}")

    # Overview table
    overview_table = create_table("Overview")
    overview_table.add_column("Metric", style="cyan")
    overview_table.add_column("Value", justify="right")

    overview_table.add_row("Total Specs", str(aggregate["total_specs"]))
    overview_table.add_row("Total Sessions", str(aggregate["total_sessions"]))
    overview_table.add_row("Total Cost", format_cost(aggregate["total_cost_usd"]))
    overview_table.add_row("Avg Cost/Spec", format_cost(aggregate["avg_cost_per_spec"]))
    overview_table.add_row("Success Rate", format_percentage(aggregate["success_rate"]))

    console.print(overview_table)

    # Token breakdown
    if tokens:
        console.print()
        token_table = create_table("Token Usage")
        token_table.add_column("Type", style="cyan")
        token_table.add_column("Count", justify="right")
        token_table.add_column("% of Total", justify="right")

        total = aggregate["total_tokens"]
        input_pct = (aggregate["total_input_tokens"] / total * 100) if total > 0 else 0
        output_pct = (aggregate["total_output_tokens"] / total * 100) if total > 0 else 0

        token_table.add_row("Input Tokens", format_tokens(aggregate["total_input_tokens"]), format_percentage(input_pct))
        token_table.add_row("Output Tokens", format_tokens(aggregate["total_output_tokens"]), format_percentage(output_pct))
        token_table.add_row("Total Tokens", format_tokens(total), "100.0%")

        console.print(token_table)

    # Recent specs table
    console.print()
    recent_table = create_table("Recent Specs")
    recent_table.add_column("Spec", style="cyan")
    recent_table.add_column("Cost", justify="right")
    recent_table.add_column("Tokens", justify="right")
    recent_table.add_column("Sessions", justify="right")
    recent_table.add_column("Last Updated", style="dim")

    # Sort by last_updated and take top 10
    sorted_reports = sorted(
        cost_reports,
        key=lambda r: r.get("last_updated", ""),
        reverse=True
    )[:10]

    for report in sorted_reports:
        recent_table.add_row(
            report["spec_name"],
            format_cost(report.get("total_cost_usd", 0)),
            format_tokens(report.get("total_input_tokens", 0) + report.get("total_output_tokens", 0)),
            str(len(report.get("sessions", []))),
            report.get("last_updated", "unknown")[:10],
        )

    console.print(recent_table)

    # QA summary
    if qa_reports:
        console.print()
        print_info(f"QA Results: {aggregate['qa_passed']}/{aggregate['qa_total']} passed ({format_percentage(aggregate['success_rate'])})")
