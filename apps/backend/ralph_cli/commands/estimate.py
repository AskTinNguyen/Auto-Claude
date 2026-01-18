"""
Ralph Estimate Command
=====================

Cost and time estimation for builds.
"""

import json
from pathlib import Path

import click

from ..utils.output import (
    console,
    print_error,
    print_warning,
    print_header,
    create_table,
    format_cost,
    format_tokens,
)


# Token pricing (as of 2025) - USD per 1M tokens
MODEL_PRICING = {
    "claude-sonnet-4-5-20250929": {"input": 3.00, "output": 15.00},
    "claude-opus-4-5-20250929": {"input": 15.00, "output": 75.00},
    "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
    "claude-3-5-haiku-20241022": {"input": 0.80, "output": 4.00},
}


def estimate_tokens_from_spec(spec_dir: Path) -> dict:
    """Estimate token usage from spec files."""
    estimates = {
        "input_tokens": 0,
        "output_tokens": 0,
        "files_analyzed": [],
    }

    # Analyze spec.md
    spec_file = spec_dir / "spec.md"
    if spec_file.exists():
        content = spec_file.read_text(encoding="utf-8")
        # Rough estimate: 4 chars per token
        token_count = len(content) // 4
        estimates["input_tokens"] += token_count
        estimates["files_analyzed"].append(("spec.md", token_count))

    # Analyze context.json
    context_file = spec_dir / "context.json"
    if context_file.exists():
        try:
            content = context_file.read_text(encoding="utf-8")
            token_count = len(content) // 4
            estimates["input_tokens"] += token_count
            estimates["files_analyzed"].append(("context.json", token_count))
        except (json.JSONDecodeError, OSError):
            pass

    # Analyze implementation_plan.json
    plan_file = spec_dir / "implementation_plan.json"
    if plan_file.exists():
        try:
            content = plan_file.read_text(encoding="utf-8")
            data = json.loads(content)
            token_count = len(content) // 4
            estimates["input_tokens"] += token_count
            estimates["files_analyzed"].append(("implementation_plan.json", token_count))

            # Estimate output based on subtask count
            subtask_count = len(data.get("subtasks", []))
            # Each subtask typically generates 500-2000 tokens of code/changes
            estimates["output_tokens"] = subtask_count * 1500
            estimates["subtask_count"] = subtask_count
        except (json.JSONDecodeError, OSError):
            pass

    # If no plan, estimate based on spec complexity
    if estimates["output_tokens"] == 0:
        # Estimate output as 2x input for typical builds
        estimates["output_tokens"] = estimates["input_tokens"] * 2

    return estimates


def calculate_cost(input_tokens: int, output_tokens: int, model: str) -> float:
    """Calculate cost for given token counts and model."""
    pricing = MODEL_PRICING.get(model, MODEL_PRICING["claude-sonnet-4-5-20250929"])

    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]

    return input_cost + output_cost


@click.command()
@click.option("--spec", help="Spec name or ID to estimate")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.option("--model", default="claude-sonnet-4-5-20250929", help="Model to use for pricing")
@click.pass_context
def estimate(ctx, spec: str | None, json_output: bool, model: str) -> None:
    """
    Estimate cost and tokens for a build.

    Analyzes spec files to predict token usage and cost before running a build.

    Examples:
        ralph estimate --spec 001-auth
        ralph estimate --spec 002 --model claude-opus-4-5-20250929
    """
    config = ctx.obj.get("config") if ctx.obj else None
    project_dir = config.project_dir if config else Path.cwd()
    specs_dir = project_dir / ".auto-claude" / "specs"

    if not specs_dir.exists():
        print_error("No specs directory found. Create a spec first!")
        raise SystemExit(1)

    # Find spec directory
    if spec:
        # Try exact match first
        spec_dir = specs_dir / spec
        if not spec_dir.exists():
            # Try prefix match
            matches = [d for d in specs_dir.iterdir() if d.is_dir() and d.name.startswith(spec)]
            if len(matches) == 1:
                spec_dir = matches[0]
            elif len(matches) > 1:
                print_error(f"Multiple specs match '{spec}': {[m.name for m in matches]}")
                raise SystemExit(1)
            else:
                print_error(f"Spec not found: {spec}")
                raise SystemExit(1)
    else:
        # Use most recent spec
        specs = sorted(specs_dir.iterdir(), key=lambda d: d.stat().st_mtime, reverse=True)
        specs = [s for s in specs if s.is_dir()]
        if not specs:
            print_error("No specs found!")
            raise SystemExit(1)
        spec_dir = specs[0]
        print_warning(f"No spec specified, using most recent: {spec_dir.name}")

    # Get estimates
    estimates = estimate_tokens_from_spec(spec_dir)

    # Calculate costs for different models
    costs = {}
    for model_name, pricing in MODEL_PRICING.items():
        costs[model_name] = calculate_cost(
            estimates["input_tokens"],
            estimates["output_tokens"],
            model_name,
        )

    result = {
        "spec_id": spec_dir.name,
        "estimated_input_tokens": estimates["input_tokens"],
        "estimated_output_tokens": estimates["output_tokens"],
        "estimated_total_tokens": estimates["input_tokens"] + estimates["output_tokens"],
        "estimated_cost_usd": costs.get(model, costs["claude-sonnet-4-5-20250929"]),
        "model": model,
        "costs_by_model": costs,
        "files_analyzed": estimates["files_analyzed"],
        "subtask_count": estimates.get("subtask_count", "unknown"),
        "confidence": "medium" if estimates.get("subtask_count") else "low",
    }

    if json_output:
        console.print_json(data=result)
        return

    print_header(f"Cost Estimate: {spec_dir.name}")

    # Token estimates table
    token_table = create_table("Token Estimates")
    token_table.add_column("Type", style="cyan")
    token_table.add_column("Tokens", justify="right")

    token_table.add_row("Input Tokens", format_tokens(estimates["input_tokens"]))
    token_table.add_row("Output Tokens (est)", format_tokens(estimates["output_tokens"]))
    token_table.add_row("Total Tokens", format_tokens(estimates["input_tokens"] + estimates["output_tokens"]))

    console.print(token_table)

    # Cost estimates table
    console.print()
    cost_table = create_table("Cost Estimates by Model")
    cost_table.add_column("Model", style="cyan")
    cost_table.add_column("Estimated Cost", justify="right")

    for model_name in ["claude-3-5-haiku-20241022", "claude-sonnet-4-5-20250929", "claude-opus-4-5-20250929"]:
        cost = costs.get(model_name, 0)
        style = ""
        if model_name == model:
            style = "[bold]"
            model_display = f"{model_name} (selected)"
        else:
            model_display = model_name
        cost_table.add_row(f"{style}{model_display}[/]" if style else model_display, format_cost(cost))

    console.print(cost_table)

    # Files analyzed
    if estimates["files_analyzed"]:
        console.print()
        console.print("[dim]Files analyzed:[/dim]")
        for filename, tokens in estimates["files_analyzed"]:
            console.print(f"  - {filename}: {format_tokens(tokens)} tokens")

    # Confidence note
    console.print()
    if result["confidence"] == "low":
        print_warning("Low confidence estimate (no implementation plan found)")
    else:
        console.print(f"[dim]Confidence: {result['confidence']} ({estimates.get('subtask_count', 0)} subtasks)[/dim]")
