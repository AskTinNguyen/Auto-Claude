"""
Ralph Review Command
===================

Quality review and scoring for specs.
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
    create_table,
    format_percentage,
)


def get_grade(score: float) -> tuple[str, str]:
    """Get letter grade and color for a score."""
    if score >= 90:
        return "A", "green"
    elif score >= 80:
        return "B", "green"
    elif score >= 70:
        return "C", "yellow"
    elif score >= 60:
        return "D", "yellow"
    else:
        return "F", "red"


def get_scorer():
    """Get Ralph scorer instance."""
    try:
        from spec.validate_pkg.scoring.ralph_scorer import RalphScorer
        return RalphScorer()
    except ImportError:
        return None


def review_spec_manual(spec_dir: Path) -> dict:
    """
    Perform manual review without the scorer.

    Returns a review dict with basic metrics.
    """
    review = {
        "spec_name": spec_dir.name,
        "score": 0,
        "checks": [],
        "issues": [],
    }

    total_checks = 0
    passed_checks = 0

    # Check spec.md exists and has content
    spec_file = spec_dir / "spec.md"
    if spec_file.exists():
        content = spec_file.read_text(encoding="utf-8")
        if len(content) > 100:
            review["checks"].append(("Spec document", True, "Found with content"))
            passed_checks += 1
        else:
            review["checks"].append(("Spec document", False, "Too short"))
            review["issues"].append("Spec document is too short")
    else:
        review["checks"].append(("Spec document", False, "Not found"))
        review["issues"].append("spec.md not found")
    total_checks += 1

    # Check context.json
    context_file = spec_dir / "context.json"
    if context_file.exists():
        try:
            data = json.loads(context_file.read_text(encoding="utf-8"))
            if data:
                review["checks"].append(("Context file", True, f"{len(data)} entries"))
                passed_checks += 1
            else:
                review["checks"].append(("Context file", False, "Empty"))
                review["issues"].append("context.json is empty")
        except json.JSONDecodeError:
            review["checks"].append(("Context file", False, "Invalid JSON"))
            review["issues"].append("context.json is not valid JSON")
    else:
        review["checks"].append(("Context file", False, "Not found"))
        review["issues"].append("context.json not found")
    total_checks += 1

    # Check implementation_plan.json
    plan_file = spec_dir / "implementation_plan.json"
    if plan_file.exists():
        try:
            plan = json.loads(plan_file.read_text(encoding="utf-8"))
            subtasks = plan.get("subtasks", [])
            if subtasks:
                review["checks"].append(("Implementation plan", True, f"{len(subtasks)} subtasks"))
                passed_checks += 1
            else:
                review["checks"].append(("Implementation plan", False, "No subtasks"))
                review["issues"].append("Implementation plan has no subtasks")
        except json.JSONDecodeError:
            review["checks"].append(("Implementation plan", False, "Invalid JSON"))
            review["issues"].append("implementation_plan.json is not valid JSON")
    else:
        review["checks"].append(("Implementation plan", False, "Not found"))
    total_checks += 1

    # Check QA report
    qa_file = spec_dir / "qa_report.md"
    if qa_file.exists():
        content = qa_file.read_text(encoding="utf-8")
        if "APPROVED" in content or "✓" in content:
            review["checks"].append(("QA Report", True, "Approved"))
            passed_checks += 1
        elif "REJECTED" in content:
            review["checks"].append(("QA Report", False, "Rejected"))
            review["issues"].append("QA report shows rejection")
        else:
            review["checks"].append(("QA Report", True, "Pending review"))
            passed_checks += 0.5  # Partial credit
    else:
        review["checks"].append(("QA Report", False, "Not found"))
    total_checks += 1

    # Check for acceptance criteria in spec
    if spec_file.exists():
        content = spec_file.read_text(encoding="utf-8").lower()
        if "acceptance criteria" in content or "## criteria" in content:
            review["checks"].append(("Acceptance Criteria", True, "Found"))
            passed_checks += 1
        else:
            review["checks"].append(("Acceptance Criteria", False, "Not found"))
            review["issues"].append("No acceptance criteria defined")
        total_checks += 1

    # Calculate score
    review["score"] = (passed_checks / total_checks) * 100 if total_checks > 0 else 0

    return review


@click.command()
@click.argument("spec", required=False)
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.option("--all", "review_all", is_flag=True, help="Review all specs")
@click.option("--fix", is_flag=True, help="Show fix suggestions")
@click.pass_context
def review(ctx, spec: str | None, json_output: bool, review_all: bool, fix: bool) -> None:
    """
    Run quality review on specs.

    Reviews spec quality and provides a score (0-100) with letter grade (A-F).

    Examples:
        ralph review 001-auth     # Review specific spec
        ralph review --all        # Review all specs
        ralph review --fix        # Show fix suggestions
    """
    config = ctx.obj.get("config") if ctx.obj else None
    project_dir = config.project_dir if config else Path.cwd()
    specs_dir = project_dir / ".auto-claude" / "specs"

    if not specs_dir.exists():
        print_error("No specs directory found!")
        raise SystemExit(1)

    # Determine which specs to review
    if review_all:
        spec_dirs = [d for d in specs_dir.iterdir() if d.is_dir()]
    elif spec:
        spec_dir = specs_dir / spec
        if not spec_dir.exists():
            # Try prefix match
            matches = [d for d in specs_dir.iterdir() if d.is_dir() and d.name.startswith(spec)]
            if len(matches) == 1:
                spec_dirs = matches
            elif len(matches) > 1:
                print_error(f"Multiple specs match '{spec}': {[m.name for m in matches]}")
                raise SystemExit(1)
            else:
                print_error(f"Spec not found: {spec}")
                raise SystemExit(1)
        else:
            spec_dirs = [spec_dir]
    else:
        # Review most recent spec
        spec_dirs = sorted(
            [d for d in specs_dir.iterdir() if d.is_dir()],
            key=lambda d: d.stat().st_mtime,
            reverse=True,
        )[:1]
        if spec_dirs:
            print_info(f"Reviewing most recent spec: {spec_dirs[0].name}")

    if not spec_dirs:
        print_warning("No specs to review")
        return

    # Run reviews
    results = []
    scorer = get_scorer()

    for spec_dir in spec_dirs:
        if scorer:
            try:
                result = scorer.score_spec(spec_dir)
                results.append({
                    "spec_name": spec_dir.name,
                    "score": result.get("total_score", 0),
                    "grade": result.get("grade", "?"),
                    "categories": result.get("categories", {}),
                    "issues": result.get("issues", []),
                })
            except Exception as e:
                # Fall back to manual review
                results.append(review_spec_manual(spec_dir))
        else:
            results.append(review_spec_manual(spec_dir))

    # Output results
    if json_output:
        console.print_json(data=results)
        return

    # Display results
    for result in results:
        print_header(f"Review: {result['spec_name']}")

        score = result["score"]
        grade, color = get_grade(score)

        console.print(f"[bold]Score:[/bold] [{color}]{score:.0f}/100 ({grade})[/]")
        console.print()

        # Checks table
        if "checks" in result:
            table = create_table("Quality Checks")
            table.add_column("Check", style="cyan")
            table.add_column("Status", justify="center")
            table.add_column("Details", style="dim")

            for name, passed, details in result["checks"]:
                status = "[green]✓[/green]" if passed else "[red]✗[/red]"
                table.add_row(name, status, details)

            console.print(table)

        # Categories (if using scorer)
        if "categories" in result and result["categories"]:
            console.print()
            cat_table = create_table("Category Scores")
            cat_table.add_column("Category", style="cyan")
            cat_table.add_column("Score", justify="right")

            for category, cat_score in result["categories"].items():
                cat_grade, cat_color = get_grade(cat_score)
                cat_table.add_row(category, f"[{cat_color}]{cat_score:.0f}[/]")

            console.print(cat_table)

        # Issues
        if result.get("issues"):
            console.print()
            console.print("[bold]Issues Found:[/bold]")
            for issue in result["issues"]:
                console.print(f"  [red]•[/red] {issue}")

        # Fix suggestions
        if fix and result.get("issues"):
            console.print()
            console.print("[bold]Suggested Fixes:[/bold]")
            for issue in result["issues"]:
                suggestion = get_fix_suggestion(issue)
                console.print(f"  [yellow]→[/yellow] {suggestion}")

    # Summary for multiple specs
    if len(results) > 1:
        console.print()
        print_header("Summary")

        avg_score = sum(r["score"] for r in results) / len(results)
        avg_grade, avg_color = get_grade(avg_score)

        console.print(f"Specs Reviewed: {len(results)}")
        console.print(f"Average Score: [{avg_color}]{avg_score:.0f}/100 ({avg_grade})[/]")

        # Grade distribution
        grades = {}
        for r in results:
            g, _ = get_grade(r["score"])
            grades[g] = grades.get(g, 0) + 1

        console.print(f"Grade Distribution: {grades}")


def get_fix_suggestion(issue: str) -> str:
    """Get a fix suggestion for an issue."""
    suggestions = {
        "spec.md not found": "Create spec.md with feature description, user stories, and acceptance criteria",
        "Spec document is too short": "Add more detail: user stories, acceptance criteria, technical requirements",
        "context.json is empty": "Re-run spec creation to gather codebase context",
        "context.json is not valid JSON": "Check and fix JSON syntax in context.json",
        "context.json not found": "Run context gathering phase to analyze codebase",
        "Implementation plan has no subtasks": "Re-run planning phase to generate subtasks",
        "implementation_plan.json is not valid JSON": "Check and fix JSON syntax in implementation_plan.json",
        "QA report shows rejection": "Review QA_FIX_REQUEST.md and address the issues",
        "No acceptance criteria defined": "Add '## Acceptance Criteria' section to spec.md with testable criteria",
    }

    for key, suggestion in suggestions.items():
        if key.lower() in issue.lower():
            return suggestion

    return "Review and address this issue manually"
