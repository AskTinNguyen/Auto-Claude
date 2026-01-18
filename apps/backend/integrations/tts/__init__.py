"""
TTS (Text-to-Speech) integration for Auto Claude.

Provides voice feedback during autonomous builds with:
- Multi-provider support (Piper, macOS, system)
- Output filtering (code blocks, markdown, file paths)
- Phase announcements and status updates
"""

from .manager import TTSManager, get_tts_manager
from .config import TTSConfig
from .voice_info import VoiceInfo

__all__ = ["TTSManager", "TTSConfig", "VoiceInfo", "get_tts_manager"]
