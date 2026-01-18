"""
Voice Lock - Cross-process TTS coordination for Auto-Claude.

Prevents concurrent TTS playback across multiple terminals/sessions using
atomic file-based locking with stale lock detection.

Based on ralph-cli's voice lock implementation (speak.js + tts-manager.sh).
"""

import os
import time
import socket
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class VoiceLock:
    """
    Voice lock for coordinating TTS across multiple processes.

    Features:
    - Atomic lock acquisition using O_EXCL flag
    - Stale lock cleanup (detects dead processes)
    - Timeout-based waiting with polling
    - Session-based identification

    Locking Strategy:
    - Lock file: .auto-claude/locks/voice/voice.lock
    - Contains: CLI_ID, PID, ACQUIRED_AT
    - Uses atomic file creation (O_EXCL) to prevent races
    """

    def __init__(self, lock_dir: Optional[Path] = None):
        """
        Initialize voice lock.

        Args:
            lock_dir: Optional directory for lock files (defaults to .auto-claude/locks/voice)
        """
        # Find lock directory
        if lock_dir:
            self.lock_dir = Path(lock_dir)
        else:
            self.lock_dir = self._find_lock_dir()

        self.lock_file = self.lock_dir / "voice.lock"

        # Generate CLI identifier
        hostname = socket.gethostname()[:8]
        self.pid = os.getpid()
        # Use timestamp for uniqueness (better than random for reproducibility)
        timestamp = str(int(time.time() * 1000))[-8:]
        self.cli_id = f"speak-{hostname}-{self.pid}-{timestamp}"

    def _find_lock_dir(self) -> Path:
        """Find or create lock directory."""
        # Check RALPH_ROOT environment variable first
        if os.getenv("RALPH_ROOT"):
            base_dir = Path(os.getenv("RALPH_ROOT"))
            lock_dir = base_dir / "locks" / "voice"
        else:
            # Walk up from current directory to find .auto-claude or .ralph
            current = Path.cwd()
            found = False

            while current != current.parent:
                # Check for .auto-claude first
                auto_claude_dir = current / ".auto-claude"
                if auto_claude_dir.exists():
                    lock_dir = auto_claude_dir / "locks" / "voice"
                    found = True
                    break

                # Fallback to .ralph
                ralph_dir = current / ".ralph"
                if ralph_dir.exists():
                    lock_dir = ralph_dir / "locks" / "voice"
                    found = True
                    break

                current = current.parent

            if not found:
                # Last resort: use home directory
                lock_dir = Path.home() / ".auto-claude" / "locks" / "voice"

        # Ensure directory exists
        lock_dir.mkdir(parents=True, exist_ok=True)
        return lock_dir

    def is_process_alive(self, pid: int) -> bool:
        """
        Check if a process is alive.

        Args:
            pid: Process ID to check

        Returns:
            True if process is alive, False otherwise
        """
        try:
            # Sending signal 0 doesn't kill the process, just checks existence
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False

    def get_lock_holder(self) -> Optional[Dict[str, str]]:
        """
        Read lock file and get holder information.

        Returns:
            Dictionary with CLI_ID, PID, ACQUIRED_AT if lock exists, None otherwise
        """
        if not self.lock_file.exists():
            return None

        try:
            content = self.lock_file.read_text()
            lines = content.strip().split("\n")
            data = {}

            for line in lines:
                if "=" in line:
                    key, value = line.split("=", 1)
                    data[key.strip()] = value.strip()

            if "CLI_ID" not in data or "PID" not in data:
                return None

            return {
                "cli_id": data["CLI_ID"],
                "pid": int(data["PID"]),
                "acquired_at": data.get("ACQUIRED_AT", "unknown"),
            }
        except Exception as e:
            logger.warning(f"Failed to read lock file: {e}")
            return None

    def cleanup_stale_lock(self) -> bool:
        """
        Remove lock file if held by dead process.

        Returns:
            True if stale lock was removed, False otherwise
        """
        holder = self.get_lock_holder()
        if holder and not self.is_process_alive(holder["pid"]):
            try:
                self.lock_file.unlink()
                logger.info(f"Cleaned up stale lock from dead process {holder['pid']}")
                return True
            except Exception as e:
                logger.warning(f"Failed to clean up stale lock: {e}")
                return False
        return False

    def try_acquire(self) -> Dict[str, any]:
        """
        Try to acquire lock atomically.

        Returns:
            Dictionary with:
            - success: bool - whether lock was acquired
            - holder: dict - current holder info (if lock failed)
            - error: str - error message (if any)
        """
        # Ensure lock directory exists
        self.lock_dir.mkdir(parents=True, exist_ok=True)

        # Lock content
        content = "\n".join([
            f"CLI_ID={self.cli_id}",
            f"PID={self.pid}",
            f"ACQUIRED_AT={datetime.now().isoformat()}",
        ])

        try:
            # Atomic lock acquisition using O_EXCL (exclusive create)
            # This fails atomically if file already exists
            fd = os.open(
                str(self.lock_file),
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                0o644
            )

            # Write content and close
            os.write(fd, content.encode())
            os.close(fd)

            logger.debug(f"Acquired voice lock: {self.cli_id}")
            return {"success": True, "holder": None, "error": None}

        except FileExistsError:
            # Lock file exists - check if it's stale
            holder = self.get_lock_holder()

            if holder and not self.is_process_alive(holder["pid"]):
                # Stale lock from dead process - clean up and retry
                try:
                    self.lock_file.unlink()
                    logger.info(f"Removed stale lock from dead process {holder['pid']}")
                    # Recursive retry after cleanup
                    return self.try_acquire()
                except Exception as e:
                    logger.warning(f"Failed to clean stale lock: {e}")

            return {
                "success": False,
                "holder": holder,
                "error": "Lock already held"
            }

        except Exception as e:
            logger.error(f"Failed to acquire lock: {e}")
            return {
                "success": False,
                "holder": None,
                "error": str(e)
            }

    def release(self):
        """Release lock if we hold it."""
        holder = self.get_lock_holder()

        if holder and holder["cli_id"] == self.cli_id:
            try:
                self.lock_file.unlink()
                logger.debug(f"Released voice lock: {self.cli_id}")
            except FileNotFoundError:
                # Already removed
                pass
            except Exception as e:
                logger.warning(f"Failed to release lock: {e}")

    def wait_for_lock(self, timeout_seconds: float = 10.0, poll_interval: float = 0.2) -> Dict[str, any]:
        """
        Wait for lock with timeout.

        Args:
            timeout_seconds: Maximum time to wait (default: 10s)
            poll_interval: Time between retry attempts (default: 200ms)

        Returns:
            Dictionary with:
            - success: bool - whether lock was acquired
            - holder: dict - current holder info (if timeout)
            - timeout: bool - whether timeout occurred
        """
        start_time = time.time()
        iterations = 0

        logger.debug(f"Waiting for voice lock (timeout: {timeout_seconds}s)...")

        while (time.time() - start_time) < timeout_seconds:
            result = self.try_acquire()

            if result["success"]:
                elapsed = time.time() - start_time
                logger.debug(f"Lock acquired after {elapsed:.1f}s ({iterations} iterations)")
                return {"success": True, "holder": None, "timeout": False}

            # Sleep before retry
            time.sleep(poll_interval)
            iterations += 1

            # Log progress every ~3 seconds
            if iterations % 15 == 0:
                elapsed = time.time() - start_time
                logger.debug(f"Still waiting for lock... ({elapsed:.1f}s elapsed)")

        # Timeout
        holder = self.get_lock_holder()
        logger.warning(f"Timeout waiting for voice lock after {timeout_seconds}s")
        if holder:
            logger.warning(f"Lock held by: {holder['cli_id']} (PID: {holder['pid']})")

        return {
            "success": False,
            "holder": holder,
            "timeout": True
        }

    def __enter__(self):
        """Context manager entry - acquire lock."""
        result = self.wait_for_lock()
        if not result["success"]:
            raise TimeoutError(f"Failed to acquire voice lock: {result}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - release lock."""
        self.release()
        return False  # Don't suppress exceptions
