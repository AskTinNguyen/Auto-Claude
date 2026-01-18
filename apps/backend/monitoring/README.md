# Auto Claude Monitoring Systems

Production-ready monitoring infrastructure for Auto Claude autonomous builds. Adapted from Ralph-CLI for comprehensive observability and cost control.

## Overview

The monitoring package provides three core systems that work together to ensure reliable, observable, and cost-controlled agent sessions:

| System | Purpose | Output File |
|--------|---------|-------------|
| **HeartbeatMonitor** | Detects stalled builds and triggers recovery | `.heartbeat` |
| **CostTracker** | Tracks token usage and enforces budget limits | `cost_report.json` |
| **EventLogger** | Structured logging for debugging and analytics | `.auto-claude-events.jsonl` |

## Quick Start

```python
from pathlib import Path
from monitoring import HeartbeatMonitor, CostTracker, EventLogger
from monitoring.cost_tracker import TokenUsage

# Initialize monitors
spec_dir = Path(".auto-claude/specs/001-feature")
heartbeat = HeartbeatMonitor(spec_dir=spec_dir, session_id=1)
cost_tracker = CostTracker(spec_dir=spec_dir, budget_usd=50.0)
event_logger = EventLogger(spec_dir=spec_dir)

# Start monitoring
heartbeat.start()
event_logger.session_start(session_id=1)

# Update state during work
heartbeat.update(phase="coding", activity="implementing feature")
event_logger.info("Making progress on feature")

# Track costs
usage = TokenUsage(input_tokens=10_000, output_tokens=5_000)
result = cost_tracker.record_session(
    session_id=1,
    model="claude-sonnet-4-5-20250929",
    usage=usage,
    phase="coding"
)

# Stop monitoring
heartbeat.stop()
event_logger.session_end(session_id=1)
```

## Components

### 1. Heartbeat Monitor

Writes periodic heartbeats to detect build stalls and trigger recovery.

**Features:**
- Writes `.heartbeat` file every 60 seconds
- Detects stalls after 30 minutes of inactivity
- Tracks session_id, subtask_id, phase, activity
- Triggers callback on stall detection
- Runs in background thread

**Key Methods:**
```python
monitor = HeartbeatMonitor(spec_dir, session_id, on_stall=callback)
monitor.start()                           # Start background monitoring
monitor.update(phase, activity)           # Update current state
monitor.check_for_stall()                 # Check for stall
monitor.get_status()                      # Get current status
monitor.stop()                            # Stop monitoring
```

**Output:** `.heartbeat`
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

### 2. Cost Tracker

Tracks token usage and API costs with budget enforcement.

**Features:**
- Track input/output tokens per session
- Calculate costs based on Claude pricing
- Support for prompt caching (creation + read tokens)
- Enforce budget limits with warnings
- Persistent cost reports
- Multiple Claude model pricing support

**Pricing (per 1M tokens):**
| Model | Input | Output | Cache Creation | Cache Read |
|-------|-------|--------|----------------|------------|
| Sonnet 4.5 | $3.00 | $15.00 | $3.75 | $0.30 |
| Opus 3.5 | $15.00 | $75.00 | $18.75 | $1.50 |

**Key Methods:**
```python
tracker = CostTracker(spec_dir, budget_usd=50.0, warning_threshold=0.8)
result = tracker.record_session(session_id, model, usage, phase)
tracker.calculate_cost(model, usage)      # Calculate cost only
tracker.get_summary()                     # Get cost summary
tracker.get_report()                      # Get full report
```

**Output:** `cost_report.json`
```json
{
  "total_input_tokens": 50000,
  "total_output_tokens": 25000,
  "total_cost_usd": 2.35,
  "sessions": [
    {
      "session_id": 1,
      "phase": "coding",
      "model": "claude-sonnet-4-5-20250929",
      "timestamp": "2025-01-18T10:30:45.123456",
      "input_tokens": 10000,
      "output_tokens": 5000,
      "cost_usd": 0.47
    }
  ],
  "created_at": "2025-01-18T10:00:00.000000",
  "last_updated": "2025-01-18T10:30:45.123456"
}
```

### 3. Event Logger

Structured event logging for debugging and analytics.

**Features:**
- Thread-safe JSONL logging
- Multiple event types (ERROR, WARN, INFO, RETRY, etc.)
- Context inheritance (session_id, subtask_id, phase)
- Event querying and filtering
- Support for metadata attachments
- No-crash error handling

**Event Types:**
- `ERROR` - Error events
- `WARN` - Warning events
- `INFO` - Informational events
- `RETRY` - Retry attempts
- `RECOVERY` - Recovery actions
- `COST_WARNING` - Budget warnings
- `COST_EXCEEDED` - Budget exceeded
- `STALL_DETECTED` - Build stalls
- `SESSION_START/END` - Session lifecycle
- `SUBTASK_START/COMPLETE/FAILED` - Subtask tracking

**Key Methods:**
```python
logger = EventLogger(spec_dir)
logger.set_context(session_id, subtask_id, phase)
logger.info("message", metadata={...})    # Log INFO event
logger.error("message", metadata={...})   # Log ERROR event
logger.warn("message", metadata={...})    # Log WARN event
logger.retry("message", metadata={...})   # Log RETRY event
logger.query_events(event_type, limit)    # Query events
logger.get_errors()                       # Get all errors
logger.get_session_events(session_id)     # Get session events
```

**Output:** `.auto-claude-events.jsonl`
```jsonl
{"timestamp": "2025-01-18T10:30:45.123456", "event_type": "SESSION_START", "message": "Session 1 started", "session_id": 1}
{"timestamp": "2025-01-18T10:30:46.234567", "event_type": "INFO", "message": "Starting implementation", "session_id": 1, "phase": "coding"}
{"timestamp": "2025-01-18T10:30:50.345678", "event_type": "ERROR", "message": "API call failed", "session_id": 1, "metadata": {"status_code": 500}}
```

## Files

- `__init__.py` - Package exports
- `heartbeat.py` - Heartbeat monitoring implementation
- `cost_tracker.py` - Cost tracking implementation
- `event_logger.py` - Event logging implementation
- `example.py` - Complete working example
- `USAGE.md` - Detailed usage guide
- `README.md` - This file

## Example

Run the included example to see all systems in action:

```bash
cd apps/backend
python3 monitoring/example.py
```

This simulates a complete agent session with:
- Planning phase (15k input, 8k output tokens)
- Coding phase with 3 subtasks (75k input, 54k output tokens)
- Validation phase (12k input, 6k output tokens)
- Budget tracking ($10 limit)
- Event logging for all activities
- Heartbeat monitoring

**Output:**
```
============================================================
Auto Claude Monitoring System - Example
============================================================
Starting monitored agent session...
Spec directory: .auto-claude/specs/example-monitoring
Budget: $10.0
------------------------------------------------------------

[PHASE 1] Planning
  → Analyzing project structure...
  → Gathering context...
  → Creating implementation plan...
  💰 Phase cost: $0.1650 (Total: $0.1650)

[PHASE 2] Coding
  → Implementing task-001-auth...
  → Implementing task-002-api...
  → Implementing task-003-ui...
  💰 Phase cost: $1.0350 (Total: $1.2000)

[PHASE 3] Validation
  → Running QA checks...
  → Verifying acceptance criteria...
  💰 Phase cost: $0.1260 (Total: $1.3260)

============================================================
SESSION COMPLETE!
============================================================

📊 COST SUMMARY
------------------------------------------------------------
Total sessions:     3
Total tokens:       170,000
  - Input tokens:   102,000
  - Output tokens:  68,000
Total cost:         $1.3260
Budget:             $10.00
Budget remaining:   $8.67 (86.7% left)

📝 EVENT SUMMARY
------------------------------------------------------------
Errors:    0
Warnings:  0
Retries:   1
```

## Testing

Run the comprehensive test suite:

```bash
cd /path/to/Auto-Claude
apps/backend/.venv/bin/pytest tests/test_monitoring.py -v
```

**Test Coverage:**
- ✅ Heartbeat creation and updates
- ✅ Stall detection and callbacks
- ✅ Cost calculation and tracking
- ✅ Budget warnings and enforcement
- ✅ Event logging and querying
- ✅ Thread safety
- ✅ Full integration scenarios

All 24 tests pass successfully.

## Integration with Auto Claude

These monitoring systems are designed to integrate with Auto Claude's agent sessions:

```python
# In planner.py, coder.py, qa_reviewer.py, etc.
from monitoring import HeartbeatMonitor, CostTracker, EventLogger

def run_agent(spec_dir, session_id, budget_usd=None):
    # Initialize monitoring
    heartbeat = HeartbeatMonitor(spec_dir, session_id, on_stall=trigger_recovery)
    cost_tracker = CostTracker(spec_dir, budget_usd=budget_usd) if budget_usd else None
    event_logger = EventLogger(spec_dir)

    # Start monitoring
    heartbeat.start()
    event_logger.session_start(session_id)

    try:
        # Run agent work...
        heartbeat.update(phase="planning", activity="analyzing codebase")
        event_logger.info("Starting planning phase")

        # Track costs after each API call
        if cost_tracker:
            result = cost_tracker.record_session(
                session_id, model, usage, phase="planning"
            )
            if result.get("budget_exceeded"):
                event_logger.cost_exceeded("Budget limit exceeded")
                raise BudgetExceededError()

        # Continue with work...

    finally:
        heartbeat.stop()
        event_logger.session_end(session_id)
```

## Command-Line Usage

View monitoring data using standard Unix tools:

```bash
# View recent events
tail -n 20 .auto-claude/specs/001-feature/.auto-claude-events.jsonl

# View errors only (with jq)
cat .auto-claude/specs/001-feature/.auto-claude-events.jsonl | \
  jq 'select(.event_type == "ERROR")'

# Count events by type
cat .auto-claude/specs/001-feature/.auto-claude-events.jsonl | \
  jq -r '.event_type' | sort | uniq -c

# View cost summary
cat .auto-claude/specs/001-feature/cost_report.json | jq '.total_cost_usd'

# Check heartbeat status
cat .auto-claude/specs/001-feature/.heartbeat | jq
```

## Best Practices

1. **Always initialize monitors at the start of agent sessions**
2. **Update heartbeat frequently** - Call `update()` whenever state changes
3. **Set event context early** - Use `set_context()` to avoid repetition
4. **Check budget results** - Handle `budget_exceeded` appropriately
5. **Use context managers** - Use `with HeartbeatMonitor(...)` when possible
6. **Query events for debugging** - Use event queries to troubleshoot issues
7. **Archive old logs periodically** - Keep event files from growing too large

## Configuration

### Heartbeat Settings

```python
# Change heartbeat interval (default: 60s)
HeartbeatMonitor.HEARTBEAT_INTERVAL_SECONDS = 30

# Change stall threshold (default: 30 minutes)
HeartbeatMonitor.STALL_THRESHOLD_SECONDS = 15 * 60  # 15 minutes
```

### Cost Tracker Settings

```python
# Add custom model pricing
CostTracker.PRICING["my-custom-model"] = {
    "input": 5.00,
    "output": 20.00,
    "cache_creation": 6.25,
    "cache_read": 0.50,
}

# Change default budget
tracker = CostTracker(spec_dir, budget_usd=100.0, warning_threshold=0.9)
```

## Architecture

All three systems are:
- **Thread-safe** - Safe for concurrent use
- **Non-blocking** - Won't slow down agent sessions
- **Resilient** - Won't crash on I/O errors
- **Persistent** - Data survives process restarts
- **Queryable** - Easy to analyze and debug

## Performance

- Heartbeat monitoring runs in background thread (negligible overhead)
- Cost tracking is in-memory with periodic disk writes
- Event logging uses append-only JSONL (fast writes, easy parsing)
- All file operations use atomic writes with error handling

## Credits

Adapted from [Ralph-CLI](https://github.com/ralphcli/ralph) monitoring systems for use in Auto Claude.

## License

Same as Auto Claude project license.
