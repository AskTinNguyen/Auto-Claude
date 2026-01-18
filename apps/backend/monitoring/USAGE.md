# Monitoring Systems - Usage Guide

This guide demonstrates how to use the three monitoring systems in Auto Claude: Heartbeat Monitor, Cost Tracker, and Event Logger.

## Overview

The monitoring package provides production-ready observability for autonomous builds:

- **HeartbeatMonitor**: Detects stalled builds and triggers recovery
- **CostTracker**: Tracks token usage and enforces budget limits
- **EventLogger**: Structured logging for debugging and analytics

All three systems are designed to work together and provide comprehensive monitoring for agent sessions.

## Quick Start

```python
from pathlib import Path
from monitoring import HeartbeatMonitor, CostTracker, EventLogger
from monitoring.cost_tracker import TokenUsage

# Initialize all monitors
spec_dir = Path(".auto-claude/specs/001-feature")
spec_dir.mkdir(parents=True, exist_ok=True)

heartbeat = HeartbeatMonitor(spec_dir=spec_dir, session_id=1)
cost_tracker = CostTracker(spec_dir=spec_dir, budget_usd=50.0)
event_logger = EventLogger(spec_dir=spec_dir)

# Start monitoring
heartbeat.start()
event_logger.session_start(session_id=1)

# ... do work ...

# Stop monitoring
heartbeat.stop()
event_logger.session_end(session_id=1)
```

## Heartbeat Monitor

### Basic Usage

```python
from monitoring import HeartbeatMonitor

# Initialize monitor
monitor = HeartbeatMonitor(
    spec_dir=spec_dir,
    session_id=1,
    on_stall=lambda: print("Build has stalled!")
)

# Start monitoring in background
monitor.start()

# Update state as work progresses
monitor.update(
    subtask_id="task-001",
    phase="coding",
    activity="implementing authentication"
)

# Check for stalls
if monitor.check_for_stall():
    print("Build appears to be stalled")

# Get current status
status = monitor.get_status()
print(f"Last heartbeat: {status['time_since_heartbeat_seconds']}s ago")

# Stop monitoring
monitor.stop()
```

### Context Manager

```python
with HeartbeatMonitor(spec_dir=spec_dir, session_id=1) as monitor:
    monitor.update(activity="starting work")
    # ... do work ...
    monitor.update(activity="finishing work")
# Automatically stops on exit
```

### Integration with Recovery

```python
def trigger_recovery():
    """Called when build stalls."""
    print("Stall detected! Triggering recovery...")
    # Implement recovery logic here

monitor = HeartbeatMonitor(
    spec_dir=spec_dir,
    session_id=1,
    on_stall=trigger_recovery
)

monitor.start()
```

### Files Created

- `.heartbeat` - JSON file with current state:
  ```json
  {
    "timestamp": "2025-01-18T10:30:45.123456",
    "session_id": 1,
    "subtask_id": "task-001",
    "phase": "coding",
    "activity": "implementing authentication",
    "pid": 12345
  }
  ```

## Cost Tracker

### Basic Usage

```python
from monitoring import CostTracker
from monitoring.cost_tracker import TokenUsage

# Initialize tracker with budget
tracker = CostTracker(
    spec_dir=spec_dir,
    budget_usd=50.0,        # Optional budget limit
    warning_threshold=0.8    # Warn at 80% of budget
)

# Record token usage for a session
usage = TokenUsage(
    input_tokens=10_000,
    output_tokens=5_000,
    cache_creation_input_tokens=2_000,
    cache_read_input_tokens=8_000
)

result = tracker.record_session(
    session_id=1,
    model="claude-sonnet-4-5-20250929",
    usage=usage,
    subtask_id="task-001",
    phase="coding"
)

# Check result
print(f"Session cost: ${result['session_cost_usd']:.4f}")
print(f"Total cost: ${result['total_cost_usd']:.4f}")

if result['budget_warning']:
    print("WARNING: Approaching budget limit!")

if result['budget_exceeded']:
    print("ERROR: Budget exceeded!")
    # Halt execution or take other action
```

### Cost Calculation

```python
# Calculate cost without recording
usage = TokenUsage(input_tokens=1_000_000, output_tokens=500_000)
cost = tracker.calculate_cost("claude-sonnet-4-5-20250929", usage)
print(f"Estimated cost: ${cost:.4f}")
```

### Cost Summary

```python
# Get summary of all costs
summary = tracker.get_summary()

print(f"Total sessions: {summary['total_sessions']}")
print(f"Total tokens: {summary['total_tokens']:,}")
print(f"Total cost: ${summary['total_cost_usd']:.4f}")

if 'budget_remaining_usd' in summary:
    print(f"Budget remaining: ${summary['budget_remaining_usd']:.2f}")
    print(f"Budget usage: {summary['budget_usage_percent']:.1f}%")
```

### Pricing Models

The tracker includes pricing for multiple Claude models:

```python
# Get pricing for a specific model
pricing = tracker.get_pricing("claude-sonnet-4-5-20250929")
print(f"Input: ${pricing['input']}/M tokens")
print(f"Output: ${pricing['output']}/M tokens")
print(f"Cache creation: ${pricing['cache_creation']}/M tokens")
print(f"Cache read: ${pricing['cache_read']}/M tokens")
```

Supported models:
- `claude-sonnet-4-5-20250929` - Sonnet 4.5 (latest)
- `claude-opus-3-5-20241022` - Opus 3.5
- `claude-3-5-sonnet-20241022` - Sonnet 3.5
- And more...

### Files Created

- `cost_report.json` - Persistent cost tracking:
  ```json
  {
    "total_input_tokens": 50000,
    "total_output_tokens": 25000,
    "total_cache_creation_tokens": 10000,
    "total_cache_read_tokens": 40000,
    "total_cost_usd": 2.35,
    "sessions": [
      {
        "session_id": 1,
        "subtask_id": "task-001",
        "phase": "coding",
        "model": "claude-sonnet-4-5-20250929",
        "timestamp": "2025-01-18T10:30:45.123456",
        "input_tokens": 10000,
        "output_tokens": 5000,
        "cache_creation_input_tokens": 2000,
        "cache_read_input_tokens": 8000,
        "cost_usd": 0.47
      }
    ],
    "created_at": "2025-01-18T10:00:00.000000",
    "last_updated": "2025-01-18T10:30:45.123456"
  }
  ```

## Event Logger

### Basic Usage

```python
from monitoring import EventLogger
from monitoring.event_logger import EventType

# Initialize logger
logger = EventLogger(spec_dir=spec_dir)

# Set context (optional, but recommended)
logger.set_context(
    session_id=1,
    subtask_id="task-001",
    phase="coding"
)

# Log events
logger.info("Starting implementation")
logger.error("API call failed", metadata={"status_code": 500})
logger.warn("Approaching token limit", metadata={"tokens_used": 45000})
logger.retry("Retrying API call", metadata={"attempt": 2})
```

### Session Lifecycle

```python
# Log session lifecycle
logger.session_start(session_id=1, metadata={"model": "claude-sonnet-4-5-20250929"})

# ... do work ...

logger.session_end(session_id=1, metadata={"success": True})
```

### Subtask Tracking

```python
# Track subtask progress
logger.subtask_start(subtask_id="task-001")
logger.set_context(subtask_id="task-001")

try:
    # ... implement subtask ...
    logger.info("Subtask making progress")
    logger.subtask_complete(subtask_id="task-001")
except Exception as e:
    logger.subtask_failed(subtask_id="task-001", metadata={"error": str(e)})
```

### Cost Events

```python
# Log cost-related events
logger.cost_warning(
    "Approaching budget limit",
    metadata={"usage_percent": 85, "total_cost": 42.50}
)

logger.cost_exceeded(
    "Budget limit exceeded",
    metadata={"budget": 50.0, "total_cost": 52.30}
)
```

### Stall Detection Events

```python
# Log stall detection
logger.stall_detected(
    "Build stalled for 30 minutes",
    metadata={"last_activity": "implementing feature", "last_heartbeat": "2025-01-18T10:00:00"}
)
```

### Querying Events

```python
# Get all errors
errors = logger.get_errors(limit=10)
for error in errors:
    print(f"{error['timestamp']}: {error['message']}")

# Get all warnings
warnings = logger.get_warnings()

# Get all retries
retries = logger.get_retries()

# Get events for a specific session
session_events = logger.get_session_events(session_id=1)

# Get events for a specific subtask
subtask_events = logger.get_subtask_events(subtask_id="task-001")

# Custom query with filters
coding_errors = logger.query_events(
    event_type=EventType.ERROR,
    phase="coding",
    limit=5
)
```

### Files Created

- `.auto-claude-events.jsonl` - JSONL file (one JSON per line):
  ```jsonl
  {"timestamp": "2025-01-18T10:30:45.123456", "event_type": "SESSION_START", "message": "Session 1 started", "session_id": 1}
  {"timestamp": "2025-01-18T10:30:46.234567", "event_type": "INFO", "message": "Starting implementation", "session_id": 1, "subtask_id": "task-001", "phase": "coding"}
  {"timestamp": "2025-01-18T10:30:50.345678", "event_type": "ERROR", "message": "API call failed", "session_id": 1, "subtask_id": "task-001", "phase": "coding", "metadata": {"status_code": 500}}
  ```

## Complete Example: Agent Session

Here's a complete example integrating all three monitoring systems in an agent session:

```python
from pathlib import Path
from monitoring import HeartbeatMonitor, CostTracker, EventLogger
from monitoring.cost_tracker import TokenUsage
from monitoring.event_logger import EventType

def run_agent_session(spec_dir: Path, session_id: int, budget_usd: float = 50.0):
    """Run an agent session with full monitoring."""

    # Initialize monitors
    heartbeat = HeartbeatMonitor(
        spec_dir=spec_dir,
        session_id=session_id,
        on_stall=lambda: handle_stall(event_logger)
    )

    cost_tracker = CostTracker(
        spec_dir=spec_dir,
        budget_usd=budget_usd,
        warning_threshold=0.8
    )

    event_logger = EventLogger(spec_dir=spec_dir)
    event_logger.set_context(session_id=session_id, phase="planning")

    # Start monitoring
    heartbeat.start()
    event_logger.session_start(session_id=session_id)
    heartbeat.update(phase="planning", activity="creating implementation plan")

    try:
        # Planning phase
        event_logger.info("Starting planning phase")
        plan_cost = execute_planning(heartbeat, event_logger)

        # Record planning cost
        result = cost_tracker.record_session(
            session_id=session_id,
            model="claude-sonnet-4-5-20250929",
            usage=plan_cost,
            phase="planning"
        )

        # Check budget
        if result['budget_warning']:
            event_logger.cost_warning(
                f"Budget warning: {result['budget_usage_percent']:.1f}% used",
                metadata=result
            )

        if result['budget_exceeded']:
            event_logger.cost_exceeded("Budget exceeded!", metadata=result)
            raise BudgetExceededError(f"Budget of ${budget_usd} exceeded")

        # Coding phase
        event_logger.set_context(phase="coding")
        heartbeat.update(phase="coding", activity="implementing features")
        event_logger.info("Starting coding phase")

        coding_cost = execute_coding(heartbeat, event_logger)
        cost_tracker.record_session(
            session_id=session_id,
            model="claude-sonnet-4-5-20250929",
            usage=coding_cost,
            phase="coding"
        )

        # Validation phase
        event_logger.set_context(phase="validation")
        heartbeat.update(phase="validation", activity="running QA")
        event_logger.info("Starting validation phase")

        validation_cost = execute_validation(heartbeat, event_logger)
        cost_tracker.record_session(
            session_id=session_id,
            model="claude-sonnet-4-5-20250929",
            usage=validation_cost,
            phase="validation"
        )

        # Success!
        event_logger.session_end(session_id=session_id, metadata={"success": True})

        # Print summary
        summary = cost_tracker.get_summary()
        print(f"\nSession {session_id} Complete!")
        print(f"Total cost: ${summary['total_cost_usd']:.4f}")
        print(f"Budget remaining: ${summary['budget_remaining_usd']:.2f}")

    except Exception as e:
        event_logger.error(f"Session failed: {e}", metadata={"exception": str(e)})
        event_logger.session_end(session_id=session_id, metadata={"success": False})
        raise

    finally:
        # Stop monitoring
        heartbeat.stop()


def execute_planning(heartbeat, logger):
    """Execute planning phase with monitoring."""
    logger.info("Analyzing codebase")
    heartbeat.update(activity="analyzing codebase")

    # Simulate work...
    time.sleep(1)

    logger.info("Creating implementation plan")
    heartbeat.update(activity="creating plan")

    # Return token usage
    return TokenUsage(input_tokens=5_000, output_tokens=3_000)


def execute_coding(heartbeat, logger):
    """Execute coding phase with monitoring."""
    subtasks = ["task-001", "task-002", "task-003"]

    for subtask_id in subtasks:
        logger.subtask_start(subtask_id=subtask_id)
        logger.set_context(subtask_id=subtask_id)
        heartbeat.update(subtask_id=subtask_id, activity=f"implementing {subtask_id}")

        try:
            # Simulate work...
            time.sleep(1)
            logger.info(f"Completed {subtask_id}")
            logger.subtask_complete(subtask_id=subtask_id)
        except Exception as e:
            logger.subtask_failed(subtask_id=subtask_id, metadata={"error": str(e)})
            raise

    # Return token usage
    return TokenUsage(input_tokens=20_000, output_tokens=15_000)


def execute_validation(heartbeat, logger):
    """Execute validation phase with monitoring."""
    logger.info("Running QA checks")
    heartbeat.update(activity="running QA")

    # Simulate work...
    time.sleep(1)

    # Return token usage
    return TokenUsage(input_tokens=8_000, output_tokens=5_000)


def handle_stall(logger):
    """Handle stall detection."""
    logger.stall_detected("Build stalled for 30 minutes")
    print("WARNING: Build appears to be stalled!")
    # Implement recovery logic here...


class BudgetExceededError(Exception):
    """Raised when budget is exceeded."""
    pass


if __name__ == "__main__":
    import time

    spec_dir = Path(".auto-claude/specs/001-example")
    spec_dir.mkdir(parents=True, exist_ok=True)

    run_agent_session(spec_dir, session_id=1, budget_usd=50.0)
```

## Command-Line Tools

### View Events

```bash
# View all events
cat .auto-claude/specs/001-feature/.auto-claude-events.jsonl

# View recent errors (using jq)
cat .auto-claude/specs/001-feature/.auto-claude-events.jsonl | \
  jq 'select(.event_type == "ERROR")' | \
  tail -n 10

# View session 1 events
cat .auto-claude/specs/001-feature/.auto-claude-events.jsonl | \
  jq 'select(.session_id == 1)'

# Count events by type
cat .auto-claude/specs/001-feature/.auto-claude-events.jsonl | \
  jq -r '.event_type' | \
  sort | \
  uniq -c
```

### View Cost Report

```bash
# View cost report
cat .auto-claude/specs/001-feature/cost_report.json | jq

# View total cost
cat .auto-claude/specs/001-feature/cost_report.json | jq '.total_cost_usd'

# View cost by session
cat .auto-claude/specs/001-feature/cost_report.json | \
  jq '.sessions[] | {session_id, phase, cost_usd}'
```

### View Heartbeat

```bash
# View current heartbeat
cat .auto-claude/specs/001-feature/.heartbeat | jq

# Check time since last heartbeat
python3 -c "
import json
from datetime import datetime
with open('.auto-claude/specs/001-feature/.heartbeat') as f:
    data = json.load(f)
last = datetime.fromisoformat(data['timestamp'])
elapsed = (datetime.now() - last).total_seconds()
print(f'Last heartbeat: {elapsed:.0f}s ago')
"
```

## Best Practices

1. **Always start monitoring early** - Initialize monitors before agent work begins
2. **Update heartbeat frequently** - Call `heartbeat.update()` whenever state changes
3. **Set event context** - Use `logger.set_context()` to avoid repetition
4. **Check budget regularly** - Monitor cost results and halt if exceeded
5. **Use context managers** - Use `with HeartbeatMonitor(...)` for automatic cleanup
6. **Query events for debugging** - Use event queries to troubleshoot issues
7. **Archive old logs** - Periodically archive or clean up old event files

## Configuration

### Environment Variables

```bash
# Set default budget for all sessions
export AUTO_CLAUDE_BUDGET=50.0

# Set stall threshold (in seconds)
export AUTO_CLAUDE_STALL_THRESHOLD=1800  # 30 minutes

# Set heartbeat interval (in seconds)
export AUTO_CLAUDE_HEARTBEAT_INTERVAL=60  # 1 minute
```

### Custom Pricing

```python
# Add custom model pricing
CostTracker.PRICING["my-custom-model"] = {
    "input": 5.00,
    "output": 20.00,
    "cache_creation": 6.25,
    "cache_read": 0.50,
}
```

## Troubleshooting

### Heartbeat Not Updating

```python
# Check if monitor is running
if not heartbeat.running:
    print("Heartbeat monitor is not running!")
    heartbeat.start()

# Check status
status = heartbeat.get_status()
print(f"Heartbeat status: {status}")
```

### Event File Too Large

```python
# Archive old events
import shutil
from datetime import datetime

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
archive_path = spec_dir / f".auto-claude-events.{timestamp}.jsonl"
shutil.move(
    spec_dir / ".auto-claude-events.jsonl",
    archive_path
)
print(f"Archived events to {archive_path}")
```

### Cost Report Corrupted

```python
# Reset cost tracker
tracker = CostTracker(spec_dir=spec_dir)
tracker.reset()  # WARNING: This deletes all cost history!
```
