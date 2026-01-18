"""
TTS configuration management.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class TTSConfig:
    """Configuration for TTS system."""

    # Enable/disable TTS
    enabled: bool = False

    # Provider preference order
    preferred_provider: Optional[str] = None  # 'piper', 'macos', 'system', or None for auto

    # Piper-specific settings
    piper_model: str = "en_US-lessac-medium"
    piper_executable: Optional[str] = None  # Auto-detect if None

    # macOS say settings
    macos_voice: str = "Samantha"
    macos_rate: int = 200  # Words per minute

    # General settings
    max_length: int = 500  # Max characters to speak
    announce_phases: bool = True  # Announce phase transitions
    announce_subtasks: bool = True  # Announce subtask completions
    announce_qa: bool = True  # Announce QA results

    # Filtering
    filter_code_blocks: bool = True
    filter_markdown: bool = True
    filter_file_paths: bool = True
    filter_urls: bool = True

    @classmethod
    def from_env(cls) -> "TTSConfig":
        """Create configuration from environment variables."""
        return cls(
            enabled=os.getenv("TTS_ENABLED", "false").lower() == "true",
            preferred_provider=os.getenv("TTS_PROVIDER"),
            piper_model=os.getenv("TTS_PIPER_MODEL", "en_US-lessac-medium"),
            piper_executable=os.getenv("TTS_PIPER_PATH"),
            macos_voice=os.getenv("TTS_MACOS_VOICE", "Samantha"),
            macos_rate=int(os.getenv("TTS_MACOS_RATE", "200")),
            max_length=int(os.getenv("TTS_MAX_LENGTH", "500")),
            announce_phases=os.getenv("TTS_ANNOUNCE_PHASES", "true").lower() == "true",
            announce_subtasks=os.getenv("TTS_ANNOUNCE_SUBTASKS", "true").lower() == "true",
            announce_qa=os.getenv("TTS_ANNOUNCE_QA", "true").lower() == "true",
            filter_code_blocks=os.getenv("TTS_FILTER_CODE", "true").lower() == "true",
            filter_markdown=os.getenv("TTS_FILTER_MARKDOWN", "true").lower() == "true",
            filter_file_paths=os.getenv("TTS_FILTER_PATHS", "true").lower() == "true",
            filter_urls=os.getenv("TTS_FILTER_URLS", "true").lower() == "true",
        )

    def is_enabled(self) -> bool:
        """Check if TTS is enabled."""
        return self.enabled
