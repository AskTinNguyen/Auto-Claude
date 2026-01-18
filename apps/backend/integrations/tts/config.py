"""
TTS configuration management.
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


# Default Piper voice directory
_PIPER_VOICE_DIR = Path.home() / ".local" / "share" / "piper-voices"


def _get_original_project_root(project_dir: Path) -> Path:
    """
    Get the original project root, even if running in a worktree.

    Worktrees are located at: <project>/.auto-claude/worktrees/tasks/<spec>/
    This function detects if we're in a worktree and returns the original root.

    Args:
        project_dir: Current project directory (may be a worktree)

    Returns:
        Original project root directory
    """
    # Convert to absolute path
    project_dir = project_dir.resolve()

    # Check if we're in a worktree by looking for the pattern
    # .auto-claude/worktrees/tasks/<spec-name>
    parts = project_dir.parts
    for i, part in enumerate(parts):
        if part == ".auto-claude" and i + 2 < len(parts):
            if parts[i + 1] == "worktrees" and parts[i + 2] == "tasks":
                # Found worktree pattern - return the parent of .auto-claude
                return Path(*parts[:i])

    # Not in a worktree, return as-is
    return project_dir


def _resolve_piper_voice_name(short_name: str) -> str:
    """
    Resolve old-format short voice name to full model name.

    Args:
        short_name: Short voice name like "ryan", "lessac"

    Returns:
        Full model name like "en_US-ryan-medium" if found, otherwise returns the input
    """
    if not _PIPER_VOICE_DIR.exists():
        return short_name

    try:
        # Search for matching .onnx file
        for onnx_file in _PIPER_VOICE_DIR.glob("*.onnx"):
            filename = onnx_file.name
            model_name = filename[:-5]  # Remove .onnx
            parts = model_name.split('-')
            if len(parts) >= 2 and parts[1].lower() == short_name.lower():
                return model_name
    except Exception:
        pass

    return short_name


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
    max_length: int = 500  # Max characters to speak (legacy - use mode-based now)
    announce_phases: bool = True  # Announce phase transitions
    announce_subtasks: bool = True  # Announce subtask completions
    announce_qa: bool = True  # Announce QA results

    # Filtering
    filter_code_blocks: bool = True
    filter_markdown: bool = True
    filter_file_paths: bool = True
    filter_urls: bool = True

    # AI Summarization (Ollama)
    summarization_mode: str = "adaptive"  # 'adaptive', 'short', 'medium', 'full'
    fallback_mode: str = "short"  # Mode to use if adaptive detection fails
    ollama_url: str = "http://localhost:11434"  # Ollama API endpoint
    ollama_model: str = "qwen2.5:1.5b"  # Ollama model for summarization
    enable_ai_summarization: bool = True  # Use AI summarization vs simple truncation

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
            # AI Summarization settings
            summarization_mode=os.getenv("TTS_SUMMARIZATION_MODE", "adaptive"),
            fallback_mode=os.getenv("TTS_FALLBACK_MODE", "short"),
            ollama_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
            ollama_model=os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b"),
            enable_ai_summarization=os.getenv("TTS_ENABLE_AI_SUMMARIZATION", "true").lower() == "true",
        )

        # Override with voice-config.json if available (for auto-speak integration)
        # Always read from original project root, not worktree
        if project_dir:
            original_root = _get_original_project_root(Path(project_dir))
            voice_config_path = original_root / ".ralph" / "voice-config.json"
            if voice_config_path.exists():
                try:
                    with open(voice_config_path, 'r') as f:
                        voice_config = json.load(f)

                    # Enable TTS if autoSpeak is enabled
                    if voice_config.get("autoSpeak", {}).get("enabled"):
                        config.enabled = True

                    # Override provider if specified in voice config
                    if voice_config.get("voice", {}).get("provider"):
                        config.preferred_provider = voice_config["voice"]["provider"]

                    # Override voice selection if specified
                    if voice_config.get("voice", {}).get("selectedVoice"):
                        selected_voice = voice_config["voice"]["selectedVoice"]

                        # Update provider-specific voice settings
                        if config.preferred_provider == "piper":
                            # Piper voice format is like "en_US-ryan-medium"
                            # Handle backward compatibility for old short format (e.g., "ryan")
                            if '-' not in selected_voice:
                                selected_voice = _resolve_piper_voice_name(selected_voice)
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
