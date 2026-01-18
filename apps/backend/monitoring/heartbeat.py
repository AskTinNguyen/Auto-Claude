"""
Heartbeat Monitor
=================

Detects stalled builds and triggers recovery.
Writes heartbeat file every 60 seconds to track liveness.

Features:
- Write .heartbeat file with timestamp + metadata
- Detect stalls after 30 minutes of inactivity
- Track session_id, subtask_id, phase, activity
- Trigger recovery callback on stall detection
"""

import json
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable


@dataclass
class HeartbeatData:
    """Data written to heartbeat file."""

    timestamp: str
    session_id: int
    subtask_id: str | None
    phase: str
    activity: str
    pid: int


class HeartbeatMonitor:
    """
    Monitor build liveness and detect stalls.

    Writes periodic heartbeats to track build progress.
    Can detect when the build has stalled (no activity for >30 minutes)
    and trigger recovery actions.
    """

    # Write heartbeat every 60 seconds
    HEARTBEAT_INTERVAL_SECONDS = 60

    # Consider build stalled after 30 minutes of no updates
    STALL_THRESHOLD_SECONDS = 30 * 60  # 30 minutes

    def __init__(
        self,
        spec_dir: Path,
        session_id: int = 0,
        on_stall: Callable[[], None] | None = None,
    ):
        """
        Initialize heartbeat monitor.

        Args:
            spec_dir: Spec directory for storing .heartbeat file
            session_id: Current session ID
            on_stall: Optional callback to trigger on stall detection
        """
        self.spec_dir = spec_dir
        self.session_id = session_id
        self.on_stall = on_stall

        self.heartbeat_file = spec_dir / ".heartbeat"
        self.running = False
        self.thread: threading.Thread | None = None
        self.lock = threading.Lock()

        # Current state
        self.subtask_id: str | None = None
        self.phase: str = "unknown"
        self.activity: str = "initializing"

    def start(self) -> None:
        """Start the heartbeat monitor in a background thread."""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        """Stop the heartbeat monitor."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
            self.thread = None

    def update(
        self,
        subtask_id: str | None = None,
        phase: str | None = None,
        activity: str | None = None,
    ) -> None:
        """
        Update heartbeat state.

        Call this whenever the build makes progress to update activity tracking.

        Args:
            subtask_id: Current subtask being worked on
            phase: Current phase (planning, coding, validation)
            activity: Description of current activity
        """
        with self.lock:
            if subtask_id is not None:
                self.subtask_id = subtask_id
            if phase is not None:
                self.phase = phase
            if activity is not None:
                self.activity = activity

    def _write_heartbeat(self) -> None:
        """Write heartbeat file with current state."""
        import os

        with self.lock:
            data = HeartbeatData(
                timestamp=datetime.now().isoformat(),
                session_id=self.session_id,
                subtask_id=self.subtask_id,
                phase=self.phase,
                activity=self.activity,
                pid=os.getpid(),
            )

        try:
            with open(self.heartbeat_file, "w", encoding="utf-8") as f:
                json.dump(asdict(data), f, indent=2)
        except OSError as e:
            # Don't crash if heartbeat write fails
            pass

    def _heartbeat_loop(self) -> None:
        """Background thread that writes heartbeat periodically."""
        while self.running:
            self._write_heartbeat()
            time.sleep(self.HEARTBEAT_INTERVAL_SECONDS)

    def check_for_stall(self) -> bool:
        """
        Check if the build has stalled based on heartbeat file.

        Returns:
            True if build appears to be stalled
        """
        if not self.heartbeat_file.exists():
            return False

        try:
            with open(self.heartbeat_file, encoding="utf-8") as f:
                data = json.load(f)

            timestamp_str = data.get("timestamp")
            if not timestamp_str:
                return False

            last_heartbeat = datetime.fromisoformat(timestamp_str)
            time_since_heartbeat = (datetime.now() - last_heartbeat).total_seconds()

            if time_since_heartbeat > self.STALL_THRESHOLD_SECONDS:
                # Stall detected - trigger callback if provided
                if self.on_stall:
                    self.on_stall()
                return True

            return False
        except (OSError, json.JSONDecodeError, ValueError):
            return False

    def get_status(self) -> dict:
        """
        Get current heartbeat status.

        Returns:
            Dict with heartbeat data and stall status
        """
        if not self.heartbeat_file.exists():
            return {
                "exists": False,
                "stalled": False,
            }

        try:
            with open(self.heartbeat_file, encoding="utf-8") as f:
                data = json.load(f)

            timestamp_str = data.get("timestamp")
            if timestamp_str:
                last_heartbeat = datetime.fromisoformat(timestamp_str)
                time_since_heartbeat = (datetime.now() - last_heartbeat).total_seconds()
                stalled = time_since_heartbeat > self.STALL_THRESHOLD_SECONDS
            else:
                time_since_heartbeat = None
                stalled = False

            return {
                "exists": True,
                "data": data,
                "time_since_heartbeat_seconds": time_since_heartbeat,
                "stalled": stalled,
            }
        except (OSError, json.JSONDecodeError, ValueError):
            return {
                "exists": True,
                "error": "Failed to parse heartbeat file",
                "stalled": False,
            }

    def __enter__(self):
        """Context manager support."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        self.stop()
