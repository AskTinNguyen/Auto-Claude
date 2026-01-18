#!/usr/bin/env python3
"""
Example: Using Auto Claude Monitoring Systems
==============================================

This script demonstrates how to use all three monitoring systems
in a realistic agent session scenario.

Run with:
    python monitoring/example.py
"""

import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from monitoring import CostTracker, EventLogger, HeartbeatMonitor
from monitoring.cost_tracker import TokenUsage
from monitoring.event_logger import EventType


class BudgetExceededError(Exception):
    """Raised when API budget is exceeded."""

    pass


def simulate_agent_session():
    """
    Simulate a complete agent session with monitoring.

    This demonstrates:
    1. Heartbeat monitoring for stall detection
    2. Cost tracking with budget enforcement
    3. Event logging for debugging and analytics
    """
    # Setup
    spec_dir = Path(".auto-claude/specs/example-monitoring")
    spec_dir.mkdir(parents=True, exist_ok=True)

    session_id = 1
    budget_usd = 10.0  # $10 budget for this session

    print(f"Starting monitored agent session...")
    print(f"Spec directory: {spec_dir}")
    print(f"Budget: ${budget_usd}")
    print("-" * 60)

    # Initialize all monitoring systems
    heartbeat = HeartbeatMonitor(
        spec_dir=spec_dir,
        session_id=session_id,
        on_stall=lambda: handle_stall_detection(),
    )

    cost_tracker = CostTracker(
        spec_dir=spec_dir, budget_usd=budget_usd, warning_threshold=0.8  # 80%
    )

    event_logger = EventLogger(spec_dir=spec_dir)

    # Start monitoring
    heartbeat.start()
    event_logger.set_context(session_id=session_id)
    event_logger.session_start(session_id=session_id)

    try:
        # Phase 1: Planning
        print("\n[PHASE 1] Planning")
        event_logger.set_context(phase="planning")
        heartbeat.update(phase="planning", activity="analyzing codebase")
        event_logger.info("Starting planning phase")

        planning_tokens = simulate_planning_phase(heartbeat, event_logger)
        track_cost(
            cost_tracker,
            event_logger,
            session_id,
            "planning",
            planning_tokens,
            budget_usd,
        )

        # Phase 2: Coding
        print("\n[PHASE 2] Coding")
        event_logger.set_context(phase="coding")
        heartbeat.update(phase="coding", activity="implementing features")
        event_logger.info("Starting coding phase")

        coding_tokens = simulate_coding_phase(heartbeat, event_logger)
        track_cost(
            cost_tracker, event_logger, session_id, "coding", coding_tokens, budget_usd
        )

        # Phase 3: Validation
        print("\n[PHASE 3] Validation")
        event_logger.set_context(phase="validation")
        heartbeat.update(phase="validation", activity="running QA checks")
        event_logger.info("Starting validation phase")

        validation_tokens = simulate_validation_phase(heartbeat, event_logger)
        track_cost(
            cost_tracker,
            event_logger,
            session_id,
            "validation",
            validation_tokens,
            budget_usd,
        )

        # Success!
        event_logger.session_end(
            session_id=session_id, metadata={"success": True, "total_phases": 3}
        )

        print("\n" + "=" * 60)
        print("SESSION COMPLETE!")
        print("=" * 60)

        # Print summary
        print_summary(cost_tracker, event_logger, spec_dir)

    except BudgetExceededError as e:
        print(f"\n❌ ERROR: {e}")
        event_logger.session_end(
            session_id=session_id,
            metadata={"success": False, "error": "budget_exceeded"},
        )

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        event_logger.error(f"Session failed: {e}", metadata={"exception": str(e)})
        event_logger.session_end(
            session_id=session_id, metadata={"success": False, "error": str(e)}
        )

    finally:
        # Stop monitoring
        heartbeat.stop()


def simulate_planning_phase(heartbeat, logger):
    """Simulate planning phase with typical token usage."""
    print("  → Analyzing project structure...")
    heartbeat.update(activity="analyzing project structure")
    time.sleep(0.5)

    print("  → Gathering context...")
    heartbeat.update(activity="gathering context")
    logger.info("Gathered codebase context", metadata={"files_analyzed": 42})
    time.sleep(0.5)

    print("  → Creating implementation plan...")
    heartbeat.update(activity="creating implementation plan")
    logger.info("Generated implementation plan", metadata={"subtasks": 3})
    time.sleep(0.5)

    # Planning typically uses moderate tokens
    return TokenUsage(input_tokens=15_000, output_tokens=8_000)


def simulate_coding_phase(heartbeat, logger):
    """Simulate coding phase with typical token usage."""
    subtasks = ["task-001-auth", "task-002-api", "task-003-ui"]
    total_tokens = TokenUsage(0, 0)

    for subtask_id in subtasks:
        print(f"  → Implementing {subtask_id}...")
        logger.subtask_start(subtask_id=subtask_id)
        logger.set_context(subtask_id=subtask_id)
        heartbeat.update(subtask_id=subtask_id, activity=f"implementing {subtask_id}")

        # Simulate implementation work
        time.sleep(0.5)

        # Simulate occasional retry
        if subtask_id == "task-002-api":
            logger.retry(
                f"Retrying {subtask_id} after API error",
                metadata={"attempt": 2, "error": "timeout"},
            )
            time.sleep(0.3)

        logger.info(f"Completed {subtask_id}")
        logger.subtask_complete(subtask_id=subtask_id)

        # Each subtask uses tokens
        total_tokens.input_tokens += 25_000
        total_tokens.output_tokens += 18_000

    # Coding is the most expensive phase
    return total_tokens


def simulate_validation_phase(heartbeat, logger):
    """Simulate validation phase with typical token usage."""
    print("  → Running QA checks...")
    heartbeat.update(activity="running QA validation")
    logger.info("Starting QA validation")
    time.sleep(0.5)

    print("  → Verifying acceptance criteria...")
    heartbeat.update(activity="verifying acceptance criteria")
    logger.info(
        "All acceptance criteria met", metadata={"criteria_checked": 5, "passed": 5}
    )
    time.sleep(0.5)

    # Validation uses moderate tokens
    return TokenUsage(input_tokens=12_000, output_tokens=6_000)


def track_cost(cost_tracker, event_logger, session_id, phase, usage, budget_usd):
    """Track cost and check budget."""
    result = cost_tracker.record_session(
        session_id=session_id,
        model="claude-sonnet-4-5-20250929",
        usage=usage,
        phase=phase,
    )

    session_cost = result["session_cost_usd"]
    total_cost = result["total_cost_usd"]

    print(f"  💰 Phase cost: ${session_cost:.4f} (Total: ${total_cost:.4f})")

    # Log cost info
    event_logger.info(
        f"{phase.title()} phase complete - Cost: ${session_cost:.4f}", metadata=result
    )

    # Check for budget warnings
    if result.get("budget_warning"):
        usage_pct = result["budget_usage_percent"]
        print(f"  ⚠️  WARNING: {usage_pct:.1f}% of budget used")
        event_logger.cost_warning(
            f"Approaching budget limit: {usage_pct:.1f}% used", metadata=result
        )

    # Check for budget exceeded
    if result.get("budget_exceeded"):
        print(f"  ❌ ERROR: Budget of ${budget_usd} exceeded!")
        event_logger.cost_exceeded(
            f"Budget of ${budget_usd} exceeded - Total: ${total_cost:.2f}",
            metadata=result,
        )
        raise BudgetExceededError(
            f"Session cost ${total_cost:.2f} exceeds budget of ${budget_usd}"
        )


def handle_stall_detection():
    """Handle stall detection callback."""
    print("\n⚠️  WARNING: Build appears to be stalled (no activity for 30 minutes)")
    print("Consider triggering recovery or manual intervention")


def print_summary(cost_tracker, event_logger, spec_dir):
    """Print final summary."""
    # Cost summary
    summary = cost_tracker.get_summary()

    print("\n📊 COST SUMMARY")
    print("-" * 60)
    print(f"Total sessions:     {summary['total_sessions']}")
    print(f"Total tokens:       {summary['total_tokens']:,}")
    print(f"  - Input tokens:   {summary['total_input_tokens']:,}")
    print(f"  - Output tokens:  {summary['total_output_tokens']:,}")
    print(f"Total cost:         ${summary['total_cost_usd']:.4f}")

    if "budget_usd" in summary:
        print(f"Budget:             ${summary['budget_usd']:.2f}")
        print(
            f"Budget remaining:   ${summary['budget_remaining_usd']:.2f} ({100 - summary['budget_usage_percent']:.1f}% left)"
        )

    # Event summary
    errors = event_logger.get_errors()
    warnings = event_logger.get_warnings()
    retries = event_logger.get_retries()

    print(f"\n📝 EVENT SUMMARY")
    print("-" * 60)
    print(f"Errors:    {len(errors)}")
    print(f"Warnings:  {len(warnings)}")
    print(f"Retries:   {len(retries)}")

    # Files created
    print(f"\n📁 FILES CREATED")
    print("-" * 60)
    print(f"Heartbeat:   {spec_dir / '.heartbeat'}")
    print(f"Cost report: {spec_dir / 'cost_report.json'}")
    print(f"Event log:   {spec_dir / '.auto-claude-events.jsonl'}")

    # Show recent events
    print(f"\n📋 RECENT EVENTS (last 5)")
    print("-" * 60)
    recent_events = event_logger.query_events(limit=5)
    for event in reversed(recent_events):  # Show oldest first
        timestamp = event["timestamp"].split("T")[1][:8]  # Just HH:MM:SS
        event_type = event["event_type"]
        message = event["message"]
        print(f"  [{timestamp}] {event_type:15s} {message}")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Auto Claude Monitoring System - Example")
    print("=" * 60)

    simulate_agent_session()

    print(
        "\n💡 TIP: Check the .auto-claude/specs/example-monitoring/ directory"
    )
    print("   for the generated monitoring files.")
    print()
