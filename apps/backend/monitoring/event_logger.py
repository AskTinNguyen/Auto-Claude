"""
Event Logger
============

Structured event logging for debugging and analytics.
Writes events to .auto-claude-events.jsonl in the spec directory.

Features:
- Structured logging: ERROR, WARN, INFO, RETRY events
- Write to .auto-claude-events.jsonl
- Track timestamps, iteration, subtask_id
- Support event querying and filtering
- Thread-safe for concurrent writes
"""

import json
import threading
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path


class EventType(str, Enum):
    """Types of events that can be logged."""

    ERROR = "ERROR"
    WARN = "WARN"
    INFO = "INFO"
    RETRY = "RETRY"
    RECOVERY = "RECOVERY"
    COST_WARNING = "COST_WARNING"
    COST_EXCEEDED = "COST_EXCEEDED"
    STALL_DETECTED = "STALL_DETECTED"
    SESSION_START = "SESSION_START"
    SESSION_END = "SESSION_END"
    SUBTASK_START = "SUBTASK_START"
    SUBTASK_COMPLETE = "SUBTASK_COMPLETE"
    SUBTASK_FAILED = "SUBTASK_FAILED"


@dataclass
class Event:
    """A single event entry."""

    timestamp: str
    event_type: str
    message: str
    session_id: int | None = None
    subtask_id: str | None = None
    phase: str | None = None
    metadata: dict | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


class EventLogger:
    """
    Thread-safe structured event logger.

    Writes events to a JSONL file (one JSON object per line).
    This format is easy to parse and stream, and works well with
    log aggregation tools like jq, grep, etc.
    """

    def __init__(self, spec_dir: Path):
        """
        Initialize event logger.

        Args:
            spec_dir: Spec directory for storing event log
        """
        self.spec_dir = spec_dir
        self.event_file = spec_dir / ".auto-claude-events.jsonl"
        self.lock = threading.Lock()

        # Current context (can be updated as build progresses)
        self.session_id: int | None = None
        self.subtask_id: str | None = None
        self.phase: str | None = None

    def set_context(
        self,
        session_id: int | None = None,
        subtask_id: str | None = None,
        phase: str | None = None,
    ) -> None:
        """
        Set the current context for subsequent events.

        This avoids having to pass session_id/subtask_id to every log call.

        Args:
            session_id: Current session ID
            subtask_id: Current subtask ID
            phase: Current phase (planning, coding, validation)
        """
        if session_id is not None:
            self.session_id = session_id
        if subtask_id is not None:
            self.subtask_id = subtask_id
        if phase is not None:
            self.phase = phase

    def log_event(
        self,
        event_type: EventType | str,
        message: str,
        metadata: dict | None = None,
        session_id: int | None = None,
        subtask_id: str | None = None,
        phase: str | None = None,
    ) -> None:
        """
        Log an event.

        Args:
            event_type: Type of event
            message: Human-readable message
            metadata: Optional additional data
            session_id: Override current session ID
            subtask_id: Override current subtask ID
            phase: Override current phase
        """
        # Use context values if not overridden
        final_session_id = session_id if session_id is not None else self.session_id
        final_subtask_id = subtask_id if subtask_id is not None else self.subtask_id
        final_phase = phase if phase is not None else self.phase

        event = Event(
            timestamp=datetime.now().isoformat(),
            event_type=str(event_type.value if isinstance(event_type, EventType) else event_type),
            message=message,
            session_id=final_session_id,
            subtask_id=final_subtask_id,
            phase=final_phase,
            metadata=metadata,
        )

        # Write to JSONL file (one JSON object per line)
        # Use lock to ensure thread safety
        with self.lock:
            try:
                with open(self.event_file, "a", encoding="utf-8") as f:
                    json.dump(event.to_dict(), f)
                    f.write("\n")
            except OSError:
                # Don't crash if logging fails
                pass

    def error(self, message: str, **kwargs) -> None:
        """Log an ERROR event."""
        self.log_event(EventType.ERROR, message, **kwargs)

    def warn(self, message: str, **kwargs) -> None:
        """Log a WARN event."""
        self.log_event(EventType.WARN, message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log an INFO event."""
        self.log_event(EventType.INFO, message, **kwargs)

    def retry(self, message: str, **kwargs) -> None:
        """Log a RETRY event."""
        self.log_event(EventType.RETRY, message, **kwargs)

    def recovery(self, message: str, **kwargs) -> None:
        """Log a RECOVERY event."""
        self.log_event(EventType.RECOVERY, message, **kwargs)

    def cost_warning(self, message: str, **kwargs) -> None:
        """Log a COST_WARNING event."""
        self.log_event(EventType.COST_WARNING, message, **kwargs)

    def cost_exceeded(self, message: str, **kwargs) -> None:
        """Log a COST_EXCEEDED event."""
        self.log_event(EventType.COST_EXCEEDED, message, **kwargs)

    def stall_detected(self, message: str, **kwargs) -> None:
        """Log a STALL_DETECTED event."""
        self.log_event(EventType.STALL_DETECTED, message, **kwargs)

    def session_start(self, session_id: int, **kwargs) -> None:
        """Log a SESSION_START event."""
        self.log_event(EventType.SESSION_START, f"Session {session_id} started", session_id=session_id, **kwargs)

    def session_end(self, session_id: int, **kwargs) -> None:
        """Log a SESSION_END event."""
        self.log_event(EventType.SESSION_END, f"Session {session_id} ended", session_id=session_id, **kwargs)

    def subtask_start(self, subtask_id: str, **kwargs) -> None:
        """Log a SUBTASK_START event."""
        self.log_event(EventType.SUBTASK_START, f"Subtask {subtask_id} started", subtask_id=subtask_id, **kwargs)

    def subtask_complete(self, subtask_id: str, **kwargs) -> None:
        """Log a SUBTASK_COMPLETE event."""
        self.log_event(EventType.SUBTASK_COMPLETE, f"Subtask {subtask_id} completed", subtask_id=subtask_id, **kwargs)

    def subtask_failed(self, subtask_id: str, **kwargs) -> None:
        """Log a SUBTASK_FAILED event."""
        self.log_event(EventType.SUBTASK_FAILED, f"Subtask {subtask_id} failed", subtask_id=subtask_id, **kwargs)

    def query_events(
        self,
        event_type: EventType | str | None = None,
        session_id: int | None = None,
        subtask_id: str | None = None,
        phase: str | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        """
        Query events with filters.

        Args:
            event_type: Filter by event type
            session_id: Filter by session ID
            subtask_id: Filter by subtask ID
            phase: Filter by phase
            limit: Maximum number of events to return (most recent first)

        Returns:
            List of event dictionaries
        """
        if not self.event_file.exists():
            return []

        events = []

        try:
            with open(self.event_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        event = json.loads(line)

                        # Apply filters
                        if event_type and event.get("event_type") != str(event_type.value if isinstance(event_type, EventType) else event_type):
                            continue
                        if session_id is not None and event.get("session_id") != session_id:
                            continue
                        if subtask_id and event.get("subtask_id") != subtask_id:
                            continue
                        if phase and event.get("phase") != phase:
                            continue

                        events.append(event)
                    except json.JSONDecodeError:
                        # Skip malformed lines
                        continue

            # Return most recent events first
            events.reverse()

            # Apply limit
            if limit:
                events = events[:limit]

            return events
        except OSError:
            return []

    def get_errors(self, limit: int | None = None) -> list[dict]:
        """Get all ERROR events."""
        return self.query_events(event_type=EventType.ERROR, limit=limit)

    def get_warnings(self, limit: int | None = None) -> list[dict]:
        """Get all WARN events."""
        return self.query_events(event_type=EventType.WARN, limit=limit)

    def get_retries(self, limit: int | None = None) -> list[dict]:
        """Get all RETRY events."""
        return self.query_events(event_type=EventType.RETRY, limit=limit)

    def get_session_events(self, session_id: int) -> list[dict]:
        """Get all events for a specific session."""
        return self.query_events(session_id=session_id)

    def get_subtask_events(self, subtask_id: str) -> list[dict]:
        """Get all events for a specific subtask."""
        return self.query_events(subtask_id=subtask_id)

    def clear(self) -> None:
        """Clear all events (use with caution)."""
        if self.event_file.exists():
            try:
                self.event_file.unlink()
            except OSError:
                pass
