"""
Ralph Budget Command
===================

Budget management and cost limits.
"""

import json
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
    format_percentage,
)


def load_budget_config(project_dir: Path) -> dict:
    """Load budget configuration from .auto-claude/budget.json."""
    budget_file = project_dir / ".auto-claude" / "budget.json"

    if budget_file.exists():
        try:
            with open(budget_file, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass

    return {
        "global_limit_usd": None,
        "warning_threshold": 0.8,
        "spec_budgets": {},
    }


def save_budget_config(project_dir: Path, config: dict) -> None:
    """Save budget configuration to .auto-claude/budget.json."""
    budget_file = project_dir / ".auto-claude" / "budget.json"
    budget_file.parent.mkdir(parents=True, exist_ok=True)

    with open(budget_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def get_total_spent(project_dir: Path) -> float:
    """Calculate total amount spent across all specs."""
    specs_dir = project_dir / ".auto-claude" / "specs"
    total = 0.0

    if not specs_dir.exists():
        return total

    for spec_dir in specs_dir.iterdir():
        if not spec_dir.is_dir():
            continue

        cost_file = spec_dir / "cost_report.json"
        if cost_file.exists():
            try:
                with open(cost_file, encoding="utf-8") as f:
                    data = json.load(f)
                    total += data.get("total_cost_usd", 0)
            except (json.JSONDecodeError, OSError):
                continue

    return total


def get_spec_spent(project_dir: Path, spec_name: str) -> float:
    """Get amount spent for a specific spec."""
    cost_file = project_dir / ".auto-claude" / "specs" / spec_name / "cost_report.json"

    if cost_file.exists():
        try:
            with open(cost_file, encoding="utf-8") as f:
                data = json.load(f)
                return data.get("total_cost_usd", 0)
        except (json.JSONDecodeError, OSError):
            pass

    return 0.0


@click.group()
@click.pass_context
def budget(ctx) -> None:
    """
    Manage cost budgets and limits.

    Set spending limits to prevent runaway costs during builds.
    """
    pass


@budget.command("set")
@click.argument("amount", type=float)
@click.option("--spec", help="Set budget for specific spec")
@click.pass_context
def budget_set(ctx, amount: float, spec: str | None) -> None:
    """
    Set a budget limit.

    AMOUNT is the budget limit in USD.

    Examples:
        ralph budget set 10.00           # Set global budget to $10
        ralph budget set 5.00 --spec 001 # Set budget for spec 001 to $5
    """
    config = ctx.obj.get("config") if ctx.obj else None
    project_dir = config.project_dir if config else Path.cwd()

    budget_config = load_budget_config(project_dir)

    if spec:
        budget_config.setdefault("spec_budgets", {})[spec] = amount
        save_budget_config(project_dir, budget_config)
        print_success(f"Budget set: {format_cost(amount)} for spec {spec}")
    else:
        budget_config["global_limit_usd"] = amount
        save_budget_config(project_dir, budget_config)
        print_success(f"Global budget set: {format_cost(amount)}")


@budget.command("show")
@click.option("--spec", help="Show budget for specific spec")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.pass_context
def budget_show(ctx, spec: str | None, json_output: bool) -> None:
    """
    Show current budget status.

    Displays budget limits and current spending.
    """
    config = ctx.obj.get("config") if ctx.obj else None
    project_dir = config.project_dir if config else Path.cwd()

    budget_config = load_budget_config(project_dir)

    if spec:
        # Show spec-specific budget
        spec_budget = budget_config.get("spec_budgets", {}).get(spec)
        spec_spent = get_spec_spent(project_dir, spec)

        if json_output:
            console.print_json(data={
                "spec": spec,
                "budget_usd": spec_budget,
                "spent_usd": spec_spent,
                "remaining_usd": (spec_budget - spec_spent) if spec_budget else None,
            })
            return

        print_header(f"Budget: {spec}")

        if spec_budget is None:
            print_warning(f"No budget set for spec {spec}")
            print_info(f"Current spending: {format_cost(spec_spent)}")
        else:
            remaining = spec_budget - spec_spent
            usage_pct = (spec_spent / spec_budget * 100) if spec_budget > 0 else 0

            table = create_table()
            table.add_column("Metric", style="cyan")
            table.add_column("Value", justify="right")

            table.add_row("Budget Limit", format_cost(spec_budget))
            table.add_row("Spent", format_cost(spec_spent))
            table.add_row("Remaining", format_cost(remaining))
            table.add_row("Usage", format_percentage(usage_pct))

            console.print(table)

            if usage_pct >= 100:
                print_error("Budget exceeded!")
            elif usage_pct >= budget_config.get("warning_threshold", 0.8) * 100:
                print_warning("Budget warning threshold reached")

    else:
        # Show global budget
        global_budget = budget_config.get("global_limit_usd")
        total_spent = get_total_spent(project_dir)

        if json_output:
            console.print_json(data={
                "global_budget_usd": global_budget,
                "total_spent_usd": total_spent,
                "remaining_usd": (global_budget - total_spent) if global_budget else None,
                "spec_budgets": budget_config.get("spec_budgets", {}),
                "warning_threshold": budget_config.get("warning_threshold", 0.8),
            })
            return

        print_header("Budget Status")

        # Global budget table
        table = create_table("Global Budget")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")

        if global_budget is None:
            table.add_row("Budget Limit", "[dim]not set[/dim]")
        else:
            table.add_row("Budget Limit", format_cost(global_budget))

        table.add_row("Total Spent", format_cost(total_spent))

        if global_budget:
            remaining = global_budget - total_spent
            usage_pct = (total_spent / global_budget * 100) if global_budget > 0 else 0
            table.add_row("Remaining", format_cost(remaining))
            table.add_row("Usage", format_percentage(usage_pct))

        console.print(table)

        # Spec budgets
        spec_budgets = budget_config.get("spec_budgets", {})
        if spec_budgets:
            console.print()
            spec_table = create_table("Spec Budgets")
            spec_table.add_column("Spec", style="cyan")
            spec_table.add_column("Budget", justify="right")
            spec_table.add_column("Spent", justify="right")
            spec_table.add_column("Usage", justify="right")

            for spec_name, spec_limit in spec_budgets.items():
                spec_spent = get_spec_spent(project_dir, spec_name)
                usage_pct = (spec_spent / spec_limit * 100) if spec_limit > 0 else 0

                usage_style = ""
                if usage_pct >= 100:
                    usage_style = "[red]"
                elif usage_pct >= budget_config.get("warning_threshold", 0.8) * 100:
                    usage_style = "[yellow]"

                spec_table.add_row(
                    spec_name,
                    format_cost(spec_limit),
                    format_cost(spec_spent),
                    f"{usage_style}{format_percentage(usage_pct)}[/]" if usage_style else format_percentage(usage_pct),
                )

            console.print(spec_table)

        # Warnings
        if global_budget:
            usage_pct = (total_spent / global_budget * 100) if global_budget > 0 else 0
            if usage_pct >= 100:
                print_error("Global budget exceeded!")
            elif usage_pct >= budget_config.get("warning_threshold", 0.8) * 100:
                print_warning("Global budget warning threshold reached")


@budget.command("clear")
@click.option("--spec", help="Clear budget for specific spec")
@click.option("--all", "clear_all", is_flag=True, help="Clear all budgets")
@click.pass_context
def budget_clear(ctx, spec: str | None, clear_all: bool) -> None:
    """
    Remove budget limits.

    Examples:
        ralph budget clear              # Clear global budget
        ralph budget clear --spec 001   # Clear budget for spec 001
        ralph budget clear --all        # Clear all budgets
    """
    config = ctx.obj.get("config") if ctx.obj else None
    project_dir = config.project_dir if config else Path.cwd()

    budget_config = load_budget_config(project_dir)

    if clear_all:
        budget_config["global_limit_usd"] = None
        budget_config["spec_budgets"] = {}
        save_budget_config(project_dir, budget_config)
        print_success("All budgets cleared")
    elif spec:
        if spec in budget_config.get("spec_budgets", {}):
            del budget_config["spec_budgets"][spec]
            save_budget_config(project_dir, budget_config)
            print_success(f"Budget cleared for spec {spec}")
        else:
            print_warning(f"No budget was set for spec {spec}")
    else:
        budget_config["global_limit_usd"] = None
        save_budget_config(project_dir, budget_config)
        print_success("Global budget cleared")


@budget.command("threshold")
@click.argument("percentage", type=float)
@click.pass_context
def budget_threshold(ctx, percentage: float) -> None:
    """
    Set warning threshold percentage.

    PERCENTAGE is the warning threshold (0-100).

    Example:
        ralph budget threshold 80  # Warn at 80% usage
    """
    config = ctx.obj.get("config") if ctx.obj else None
    project_dir = config.project_dir if config else Path.cwd()

    if percentage < 0 or percentage > 100:
        print_error("Percentage must be between 0 and 100")
        raise SystemExit(1)

    budget_config = load_budget_config(project_dir)
    budget_config["warning_threshold"] = percentage / 100
    save_budget_config(project_dir, budget_config)

    print_success(f"Warning threshold set to {percentage}%")
