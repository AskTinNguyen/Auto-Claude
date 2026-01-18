# Monitoring Systems - Quick Reference

## Import

```python
from monitoring import HeartbeatMonitor, CostTracker, EventLogger
from monitoring.cost_tracker import TokenUsage
from monitoring.event_logger import EventType
```

## Initialization

```python
spec_dir = Path(".auto-claude/specs/001-feature")

# Heartbeat (with optional stall callback)
heartbeat = HeartbeatMonitor(
    spec_dir=spec_dir,
    session_id=1,
    on_stall=lambda: trigger_recovery()
)

# Cost Tracker (with optional budget)
cost_tracker = CostTracker(
    spec_dir=spec_dir,
    budget_usd=50.0,           # Optional
    warning_threshold=0.8       # Warn at 80%
)

# Event Logger
event_logger = EventLogger(spec_dir=spec_dir)
```

## Heartbeat Monitor

```python
# Start/stop
heartbeat.start()                                    # Start background monitoring
heartbeat.stop()                                     # Stop monitoring

# Update state
heartbeat.update(
    subtask_id="task-001",
    phase="coding",
    activity="implementing feature"
)

# Check status
if heartbeat.check_for_stall():                      # Check for stall
    print("Build stalled!")

status = heartbeat.get_status()                      # Get current status

# Context manager
with HeartbeatMonitor(spec_dir, session_id) as hb:
    hb.update(activity="working...")
```

**Output:** `.heartbeat` (JSON)

## Cost Tracker

```python
# Record token usage
usage = TokenUsage(
    input_tokens=10_000,
    output_tokens=5_000,
    cache_creation_input_tokens=2_000,               # Optional
    cache_read_input_tokens=8_000                    # Optional
)

result = cost_tracker.record_session(
    session_id=1,
    model="claude-sonnet-4-5-20250929",
    usage=usage,
    subtask_id="task-001",                           # Optional
    phase="coding"                                   # Optional
)

# Check result
if result['budget_warning']:
    print(f"Warning: {result['budget_usage_percent']:.1f}% used")

if result['budget_exceeded']:
    print("Budget exceeded!")
    raise BudgetExceededError()

# Calculate cost without recording
cost = cost_tracker.calculate_cost(model, usage)

# Get summary
summary = cost_tracker.get_summary()
print(f"Total cost: ${summary['total_cost_usd']:.4f}")
```

**Output:** `cost_report.json`

## Event Logger

```python
# Set context (optional but recommended)
event_logger.set_context(
    session_id=1,
    subtask_id="task-001",
    phase="coding"
)

# Log events
event_logger.info("Starting work")
event_logger.error("API failed", metadata={"status": 500})
event_logger.warn("High token usage")
event_logger.retry("Retrying request", metadata={"attempt": 2})

# Session lifecycle
event_logger.session_start(session_id=1)
event_logger.session_end(session_id=1)

# Subtask tracking
event_logger.subtask_start(subtask_id="task-001")
event_logger.subtask_complete(subtask_id="task-001")
event_logger.subtask_failed(subtask_id="task-001")

# Cost events
event_logger.cost_warning("Approaching budget limit")
event_logger.cost_exceeded("Budget exceeded")

# Stall detection
event_logger.stall_detected("Build stalled for 30 minutes")

# Query events
errors = event_logger.get_errors(limit=10)
warnings = event_logger.get_warnings()
retries = event_logger.get_retries()
session_events = event_logger.get_session_events(session_id=1)
subtask_events = event_logger.get_subtask_events(subtask_id="task-001")

# Custom query
events = event_logger.query_events(
    event_type=EventType.ERROR,
    session_id=1,
    phase="coding",
    limit=5
)
```

**Output:** `.auto-claude-events.jsonl` (JSONL)

## Complete Example

```python
from pathlib import Path
from monitoring import HeartbeatMonitor, CostTracker, EventLogger
from monitoring.cost_tracker import TokenUsage

def run_monitored_session(spec_dir, session_id, budget_usd=50.0):
    # Initialize
    heartbeat = HeartbeatMonitor(spec_dir, session_id)
    cost_tracker = CostTracker(spec_dir, budget_usd=budget_usd)
    event_logger = EventLogger(spec_dir)

    # Start
    heartbeat.start()
    event_logger.session_start(session_id)

    try:
        # Do work
        heartbeat.update(phase="coding", activity="implementing feature")
        event_logger.info("Starting implementation")

        # Track cost
        usage = TokenUsage(input_tokens=10_000, output_tokens=5_000)
        result = cost_tracker.record_session(
            session_id, "claude-sonnet-4-5-20250929", usage
        )

        if result['budget_exceeded']:
            event_logger.cost_exceeded("Budget exceeded")
            raise BudgetExceededError()

        event_logger.session_end(session_id)

    finally:
        heartbeat.stop()
```

## Event Types

- `ERROR` - Error events
- `WARN` - Warning events
- `INFO` - Informational events
- `RETRY` - Retry attempts
- `RECOVERY` - Recovery actions
- `COST_WARNING` - Budget warnings
- `COST_EXCEEDED` - Budget exceeded
- `STALL_DETECTED` - Build stalls
- `SESSION_START` - Session started
- `SESSION_END` - Session ended
- `SUBTASK_START` - Subtask started
- `SUBTASK_COMPLETE` - Subtask completed
- `SUBTASK_FAILED` - Subtask failed

## Model Pricing (per 1M tokens)

| Model | Input | Output | Cache Create | Cache Read |
|-------|-------|--------|--------------|------------|
| **Sonnet 4.5** | $3.00 | $15.00 | $3.75 | $0.30 |
| **Opus 3.5** | $15.00 | $75.00 | $18.75 | $1.50 |
| **Sonnet 3.5** | $3.00 | $15.00 | $3.75 | $0.30 |

## Configuration

```python
# Heartbeat interval (default: 60s)
HeartbeatMonitor.HEARTBEAT_INTERVAL_SECONDS = 30

# Stall threshold (default: 30 minutes)
HeartbeatMonitor.STALL_THRESHOLD_SECONDS = 15 * 60

# Custom model pricing
CostTracker.PRICING["my-model"] = {
    "input": 5.00,
    "output": 20.00,
    "cache_creation": 6.25,
    "cache_read": 0.50,
}
```

## Output Files

| System | File | Format |
|--------|------|--------|
| Heartbeat | `.heartbeat` | JSON |
| Cost Tracker | `cost_report.json` | JSON |
| Event Logger | `.auto-claude-events.jsonl` | JSONL |

## Command-Line Usage

```bash
# View events
cat .auto-claude/specs/001/.auto-claude-events.jsonl | jq

# View recent errors
cat .auto-claude/specs/001/.auto-claude-events.jsonl | \
  jq 'select(.event_type == "ERROR")' | tail -n 10

# View cost summary
cat .auto-claude/specs/001/cost_report.json | jq '.total_cost_usd'

# Check heartbeat
cat .auto-claude/specs/001/.heartbeat | jq
```

## Testing

```bash
# Run tests
apps/backend/.venv/bin/pytest tests/test_monitoring.py -v

# Run example
cd apps/backend
python3 monitoring/example.py
```

## Documentation

- `README.md` - Package overview and API reference
- `USAGE.md` - Detailed usage guide with examples
- `SUMMARY.md` - Implementation summary
- `QUICKREF.md` - This file

## Import Paths

```python
# Package
from monitoring import HeartbeatMonitor, CostTracker, EventLogger

# Data types
from monitoring.cost_tracker import TokenUsage, SessionCost, CostReport
from monitoring.event_logger import EventType, Event
from monitoring.heartbeat import HeartbeatData
```
