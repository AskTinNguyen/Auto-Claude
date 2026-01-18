"""
Tests for monitoring systems.

Tests heartbeat monitoring, cost tracking, and event logging.
"""

import json
import time
from pathlib import Path

import pytest

from apps.backend.monitoring import CostTracker, EventLogger, HeartbeatMonitor
from apps.backend.monitoring.cost_tracker import TokenUsage
from apps.backend.monitoring.event_logger import EventType


@pytest.fixture
def temp_spec_dir(tmp_path):
    """Create a temporary spec directory for testing."""
    spec_dir = tmp_path / "spec"
    spec_dir.mkdir()
    return spec_dir


class TestHeartbeatMonitor:
    """Test heartbeat monitoring system."""

    def test_heartbeat_creation(self, temp_spec_dir):
        """Test heartbeat monitor creates heartbeat file."""
        monitor = HeartbeatMonitor(spec_dir=temp_spec_dir, session_id=1)

        # Write one heartbeat manually
        monitor._write_heartbeat()

        # Check file exists
        heartbeat_file = temp_spec_dir / ".heartbeat"
        assert heartbeat_file.exists()

        # Check file contents
        with open(heartbeat_file, encoding="utf-8") as f:
            data = json.load(f)

        assert data["session_id"] == 1
        assert data["phase"] == "unknown"
        assert data["activity"] == "initializing"
        assert "timestamp" in data
        assert "pid" in data

    def test_heartbeat_update(self, temp_spec_dir):
        """Test heartbeat state updates."""
        monitor = HeartbeatMonitor(spec_dir=temp_spec_dir, session_id=1)

        # Update state
        monitor.update(
            subtask_id="task-1",
            phase="coding",
            activity="implementing feature"
        )

        # Write heartbeat
        monitor._write_heartbeat()

        # Check updated state
        heartbeat_file = temp_spec_dir / ".heartbeat"
        with open(heartbeat_file, encoding="utf-8") as f:
            data = json.load(f)

        assert data["subtask_id"] == "task-1"
        assert data["phase"] == "coding"
        assert data["activity"] == "implementing feature"

    def test_heartbeat_context_manager(self, temp_spec_dir):
        """Test heartbeat monitor works as context manager."""
        with HeartbeatMonitor(spec_dir=temp_spec_dir, session_id=1) as monitor:
            # Give thread time to write first heartbeat
            time.sleep(0.1)
            monitor.update(activity="testing context manager")

        # Monitor should be stopped after exiting context
        assert not monitor.running

    def test_stall_detection(self, temp_spec_dir):
        """Test stall detection logic."""
        monitor = HeartbeatMonitor(spec_dir=temp_spec_dir, session_id=1)

        # Fresh heartbeat - should not be stalled
        monitor._write_heartbeat()
        assert not monitor.check_for_stall()

        # Get status
        status = monitor.get_status()
        assert status["exists"]
        assert not status["stalled"]
        assert status["time_since_heartbeat_seconds"] < 10

    def test_stall_callback(self, temp_spec_dir):
        """Test stall callback is triggered."""
        stall_detected = {"value": False}

        def on_stall():
            stall_detected["value"] = True

        monitor = HeartbeatMonitor(
            spec_dir=temp_spec_dir,
            session_id=1,
            on_stall=on_stall
        )

        # Write old heartbeat (manually edit timestamp to simulate stall)
        monitor._write_heartbeat()
        heartbeat_file = temp_spec_dir / ".heartbeat"
        with open(heartbeat_file, encoding="utf-8") as f:
            data = json.load(f)

        # Set timestamp to 31 minutes ago
        from datetime import datetime, timedelta
        old_time = datetime.now() - timedelta(minutes=31)
        data["timestamp"] = old_time.isoformat()

        with open(heartbeat_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

        # Check for stall
        is_stalled = monitor.check_for_stall()
        assert is_stalled
        assert stall_detected["value"]


class TestCostTracker:
    """Test cost tracking system."""

    def test_cost_calculation(self, temp_spec_dir):
        """Test cost calculation for token usage."""
        tracker = CostTracker(spec_dir=temp_spec_dir)

        usage = TokenUsage(
            input_tokens=1_000_000,  # 1M tokens
            output_tokens=500_000,   # 500k tokens
        )

        cost = tracker.calculate_cost("claude-sonnet-4-5-20250929", usage)

        # 1M input @ $3.00/M = $3.00
        # 500k output @ $15.00/M = $7.50
        # Total = $10.50
        assert cost == pytest.approx(10.50, rel=0.01)

    def test_cache_pricing(self, temp_spec_dir):
        """Test cache creation and read pricing."""
        tracker = CostTracker(spec_dir=temp_spec_dir)

        usage = TokenUsage(
            input_tokens=0,
            output_tokens=0,
            cache_creation_input_tokens=1_000_000,  # 1M cache creation
            cache_read_input_tokens=1_000_000,      # 1M cache reads
        )

        cost = tracker.calculate_cost("claude-sonnet-4-5-20250929", usage)

        # 1M cache creation @ $3.75/M = $3.75
        # 1M cache reads @ $0.30/M = $0.30
        # Total = $4.05
        assert cost == pytest.approx(4.05, rel=0.01)

    def test_session_recording(self, temp_spec_dir):
        """Test recording session costs."""
        tracker = CostTracker(spec_dir=temp_spec_dir)

        usage = TokenUsage(
            input_tokens=10_000,
            output_tokens=5_000,
        )

        result = tracker.record_session(
            session_id=1,
            model="claude-sonnet-4-5-20250929",
            usage=usage,
            subtask_id="task-1",
            phase="coding"
        )

        assert "session_cost_usd" in result
        assert "total_cost_usd" in result
        assert not result["budget_exceeded"]
        assert not result["budget_warning"]

        # Check cost file was created
        cost_file = temp_spec_dir / "cost_report.json"
        assert cost_file.exists()

    def test_budget_warning(self, temp_spec_dir):
        """Test budget warning when threshold is reached."""
        tracker = CostTracker(
            spec_dir=temp_spec_dir,
            budget_usd=10.0,
            warning_threshold=0.8  # Warn at 80%
        )

        # Use 8.5 USD (85% of budget)
        usage = TokenUsage(
            input_tokens=1_000_000,  # $3.00
            output_tokens=366_667,   # ~$5.50
        )

        result = tracker.record_session(
            session_id=1,
            model="claude-sonnet-4-5-20250929",
            usage=usage
        )

        assert result["budget_warning"]
        assert not result["budget_exceeded"]

    def test_budget_exceeded(self, temp_spec_dir):
        """Test budget exceeded detection."""
        tracker = CostTracker(
            spec_dir=temp_spec_dir,
            budget_usd=5.0
        )

        # Use 10.50 USD (over budget)
        usage = TokenUsage(
            input_tokens=1_000_000,  # $3.00
            output_tokens=500_000,   # $7.50
        )

        result = tracker.record_session(
            session_id=1,
            model="claude-sonnet-4-5-20250929",
            usage=usage
        )

        assert result["budget_exceeded"]
        assert result["total_cost_usd"] > 5.0

    def test_cost_report_persistence(self, temp_spec_dir):
        """Test cost report is persisted across instances."""
        # First tracker
        tracker1 = CostTracker(spec_dir=temp_spec_dir)
        usage = TokenUsage(input_tokens=10_000, output_tokens=5_000)
        tracker1.record_session(1, "claude-sonnet-4-5-20250929", usage)

        # Create new tracker (should load existing report)
        tracker2 = CostTracker(spec_dir=temp_spec_dir)
        report = tracker2.get_report()

        assert len(report.sessions) == 1
        assert report.total_input_tokens == 10_000
        assert report.total_output_tokens == 5_000

    def test_get_summary(self, temp_spec_dir):
        """Test cost summary generation."""
        tracker = CostTracker(spec_dir=temp_spec_dir, budget_usd=100.0)

        # Record a few sessions
        for i in range(3):
            usage = TokenUsage(input_tokens=10_000, output_tokens=5_000)
            tracker.record_session(i, "claude-sonnet-4-5-20250929", usage)

        summary = tracker.get_summary()

        assert summary["total_sessions"] == 3
        assert summary["total_input_tokens"] == 30_000
        assert summary["total_output_tokens"] == 15_000
        assert "total_cost_usd" in summary
        assert "budget_usd" in summary
        assert "budget_remaining_usd" in summary
        assert "budget_usage_percent" in summary


class TestEventLogger:
    """Test event logging system."""

    def test_log_event(self, temp_spec_dir):
        """Test logging a basic event."""
        logger = EventLogger(spec_dir=temp_spec_dir)

        logger.log_event(
            EventType.INFO,
            "Test event",
            metadata={"key": "value"}
        )

        # Check event file exists
        event_file = temp_spec_dir / ".auto-claude-events.jsonl"
        assert event_file.exists()

        # Read event
        with open(event_file, encoding="utf-8") as f:
            line = f.readline()
            event = json.loads(line)

        assert event["event_type"] == "INFO"
        assert event["message"] == "Test event"
        assert event["metadata"]["key"] == "value"
        assert "timestamp" in event

    def test_context_inheritance(self, temp_spec_dir):
        """Test event context is inherited from logger state."""
        logger = EventLogger(spec_dir=temp_spec_dir)

        # Set context
        logger.set_context(session_id=1, subtask_id="task-1", phase="coding")

        # Log event without specifying context
        logger.info("Test message")

        # Read event
        events = logger.query_events()
        assert len(events) == 1
        assert events[0]["session_id"] == 1
        assert events[0]["subtask_id"] == "task-1"
        assert events[0]["phase"] == "coding"

    def test_convenience_methods(self, temp_spec_dir):
        """Test convenience logging methods."""
        logger = EventLogger(spec_dir=temp_spec_dir)

        logger.error("Error message")
        logger.warn("Warning message")
        logger.info("Info message")
        logger.retry("Retry message")
        logger.recovery("Recovery message")

        # Query events
        errors = logger.get_errors()
        warnings = logger.get_warnings()
        retries = logger.get_retries()

        assert len(errors) == 1
        assert len(warnings) == 1
        assert len(retries) == 1

    def test_session_events(self, temp_spec_dir):
        """Test session-specific event logging."""
        logger = EventLogger(spec_dir=temp_spec_dir)

        logger.session_start(session_id=1)
        logger.set_context(session_id=1)
        logger.info("Session is running")
        logger.session_end(session_id=1)

        # Query session events
        events = logger.get_session_events(session_id=1)
        assert len(events) == 3
        assert events[0]["event_type"] == "SESSION_END"  # Most recent first
        assert events[1]["event_type"] == "INFO"
        assert events[2]["event_type"] == "SESSION_START"

    def test_subtask_events(self, temp_spec_dir):
        """Test subtask-specific event logging."""
        logger = EventLogger(spec_dir=temp_spec_dir)

        logger.subtask_start(subtask_id="task-1")
        logger.set_context(subtask_id="task-1")
        logger.info("Working on subtask")
        logger.subtask_complete(subtask_id="task-1")

        # Query subtask events
        events = logger.get_subtask_events(subtask_id="task-1")
        assert len(events) == 3

    def test_query_with_filters(self, temp_spec_dir):
        """Test querying events with multiple filters."""
        logger = EventLogger(spec_dir=temp_spec_dir)

        # Log events for different sessions/phases
        logger.log_event(EventType.INFO, "Session 1 planning", session_id=1, phase="planning")
        logger.log_event(EventType.INFO, "Session 1 coding", session_id=1, phase="coding")
        logger.log_event(EventType.INFO, "Session 2 coding", session_id=2, phase="coding")
        logger.log_event(EventType.ERROR, "Session 1 error", session_id=1, phase="coding")

        # Query by session
        session1_events = logger.query_events(session_id=1)
        assert len(session1_events) == 3

        # Query by phase
        coding_events = logger.query_events(phase="coding")
        assert len(coding_events) == 3

        # Query by event type
        errors = logger.query_events(event_type=EventType.ERROR)
        assert len(errors) == 1

        # Query with multiple filters
        session1_coding = logger.query_events(session_id=1, phase="coding")
        assert len(session1_coding) == 2

    def test_query_limit(self, temp_spec_dir):
        """Test query result limiting."""
        logger = EventLogger(spec_dir=temp_spec_dir)

        # Log 10 events
        for i in range(10):
            logger.info(f"Event {i}")

        # Query with limit
        events = logger.query_events(limit=5)
        assert len(events) == 5

        # Should get most recent events first
        assert "Event 9" in events[0]["message"]
        assert "Event 5" in events[4]["message"]

    def test_cost_events(self, temp_spec_dir):
        """Test cost-related event logging."""
        logger = EventLogger(spec_dir=temp_spec_dir)

        logger.cost_warning("Approaching budget limit", metadata={"usage_percent": 85})
        logger.cost_exceeded("Budget exceeded", metadata={"total_cost": 105.50})

        # Query cost events
        warnings = logger.query_events(event_type=EventType.COST_WARNING)
        exceeded = logger.query_events(event_type=EventType.COST_EXCEEDED)

        assert len(warnings) == 1
        assert len(exceeded) == 1
        assert warnings[0]["metadata"]["usage_percent"] == 85

    def test_stall_detection_events(self, temp_spec_dir):
        """Test stall detection event logging."""
        logger = EventLogger(spec_dir=temp_spec_dir)

        logger.stall_detected(
            "Build stalled for 30 minutes",
            metadata={"last_activity": "implementing feature"}
        )

        events = logger.query_events(event_type=EventType.STALL_DETECTED)
        assert len(events) == 1

    def test_thread_safety(self, temp_spec_dir):
        """Test that logging is thread-safe."""
        import threading

        logger = EventLogger(spec_dir=temp_spec_dir)

        def log_events(thread_id):
            for i in range(10):
                logger.info(f"Thread {thread_id} event {i}")

        # Create multiple threads
        threads = [threading.Thread(target=log_events, args=(i,)) for i in range(5)]

        # Start all threads
        for t in threads:
            t.start()

        # Wait for completion
        for t in threads:
            t.join()

        # Should have 50 events total (5 threads * 10 events each)
        events = logger.query_events()
        assert len(events) == 50

    def test_clear_events(self, temp_spec_dir):
        """Test clearing all events."""
        logger = EventLogger(spec_dir=temp_spec_dir)

        # Log some events
        logger.info("Event 1")
        logger.info("Event 2")

        # Clear
        logger.clear()

        # Should have no events
        events = logger.query_events()
        assert len(events) == 0


class TestIntegration:
    """Test integration of all monitoring systems together."""

    def test_combined_monitoring(self, temp_spec_dir):
        """Test using all monitoring systems together."""
        # Initialize all monitors
        heartbeat = HeartbeatMonitor(spec_dir=temp_spec_dir, session_id=1)
        cost_tracker = CostTracker(spec_dir=temp_spec_dir, budget_usd=100.0)
        event_logger = EventLogger(spec_dir=temp_spec_dir)

        # Set context
        event_logger.set_context(session_id=1, phase="coding")
        heartbeat.update(phase="coding", activity="implementing feature")

        # Log session start
        event_logger.session_start(session_id=1)

        # Simulate some work
        heartbeat._write_heartbeat()

        usage = TokenUsage(input_tokens=10_000, output_tokens=5_000)
        cost_result = cost_tracker.record_session(
            session_id=1,
            model="claude-sonnet-4-5-20250929",
            usage=usage,
            phase="coding"
        )

        # Log cost info
        event_logger.info(
            f"Session cost: ${cost_result['session_cost_usd']:.4f}",
            metadata=cost_result
        )

        # Log session end
        event_logger.session_end(session_id=1)

        # Verify all systems recorded data
        assert (temp_spec_dir / ".heartbeat").exists()
        assert (temp_spec_dir / "cost_report.json").exists()
        assert (temp_spec_dir / ".auto-claude-events.jsonl").exists()

        # Verify event log captured everything
        events = event_logger.query_events(session_id=1)
        assert len(events) == 3  # session_start, info, session_end
