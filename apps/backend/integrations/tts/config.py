"""
TTS configuration management.
"""

import os
import json
from pathlib import Path
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
    def from_env(cls, project_dir: Optional[Path] = None) -> "TTSConfig":
        """Create configuration from environment variables and voice-config.json."""
        # Read from environment variables
        config = cls(
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

        # Override with voice-config.json if available (for auto-speak integration)
        if project_dir:
            voice_config_path = project_dir / ".ralph" / "voice-config.json"
            if voice_config_path.exists():
                try:
                    with open(voice_config_path, 'r') as f:
                        voice_config = json.load(f)

                    # Override provider if specified in voice config
                    if voice_config.get("voice", {}).get("provider"):
                        config.preferred_provider = voice_config["voice"]["provider"]

                    # Override voice selection if specified
                    if voice_config.get("voice", {}).get("selectedVoice"):
                        selected_voice = voice_config["voice"]["selectedVoice"]

                        # Update provider-specific voice settings
                        if config.preferred_provider == "piper":
                            # Piper voice format is like "en_US-ryan-medium"
                            config.piper_model = selected_voice
                        elif config.preferred_provider == "macos":
                            # macOS voice is just the name like "Ryan"
                            config.macos_voice = selected_voice

                except (json.JSONDecodeError, OSError) as e:
                    # Silently ignore errors - fall back to env var config
                    pass

        return config

    def is_enabled(self) -> bool:
        """Check if TTS is enabled."""
        return self.enabled
