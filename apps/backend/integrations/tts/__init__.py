"""
TTS (Text-to-Speech) integration for Auto Claude.

Provides voice feedback during autonomous builds with:
- Multi-provider support (Piper, macOS, system)
- AI-powered summarization (Ollama integration)
- Adaptive mode detection (short/medium/full)
- Output filtering (code blocks, markdown, file paths)
- Phase announcements and status updates
- Cross-process voice coordination (prevents overlapping TTS)
"""

from .manager import TTSManager, get_tts_manager
from .config import TTSConfig
from .voice_info import VoiceInfo
from .voice_lock import VoiceLock
from .summarizer import summarize_for_tts
from .tts_modes import detect_optimal_mode, get_mode_config, ModeConfig, ModeDetectionResult

__all__ = [
    "TTSManager",
    "TTSConfig",
    "VoiceInfo",
    "VoiceLock",
    "get_tts_manager",
    "summarize_for_tts",
    "detect_optimal_mode",
    "get_mode_config",
    "ModeConfig",
    "ModeDetectionResult",
]
