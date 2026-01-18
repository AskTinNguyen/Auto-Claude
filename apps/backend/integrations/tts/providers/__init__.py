"""
TTS provider implementations.

Supports multiple TTS backends with automatic fallback:
- Piper: High-quality neural TTS
- macOS: Native 'say' command
- System: Platform-specific fallback
"""

from .piper import PiperProvider
from .macos import MacOSProvider
from .system import SystemProvider

__all__ = ["PiperProvider", "MacOSProvider", "SystemProvider"]
