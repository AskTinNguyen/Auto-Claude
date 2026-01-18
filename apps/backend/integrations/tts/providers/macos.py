"""
macOS 'say' TTS provider - Native macOS text-to-speech.
"""

import platform
import shutil
import subprocess
import logging
import re
from typing import Optional, List

from ..voice_info import VoiceInfo

logger = logging.getLogger(__name__)


class MacOSProvider:
    """macOS native 'say' command TTS provider."""

    def __init__(self, voice: str = "Samantha", rate: int = 200):
        """
        Initialize macOS TTS provider.

        Args:
            voice: Voice name (Samantha, Alex, Victoria, etc.)
            rate: Speaking rate in words per minute
        """
        self.voice = voice
        self.rate = rate
        self.available = self._check_availability()

        if self.available:
            logger.info(f"macOS TTS initialized: voice={voice}, rate={rate}")
        else:
            logger.warning("macOS TTS not available (not macOS or 'say' not found)")

    def _check_availability(self) -> bool:
        """Check if macOS 'say' command is available."""
        if platform.system() != "Darwin":
            return False

        return shutil.which("say") is not None

    def is_available(self) -> bool:
        """Check if provider is available."""
        return self.available

    def speak(self, text: str) -> bool:
        """
        Speak text using macOS 'say' command.

        Args:
            text: Text to speak

        Returns:
            True if successful, False otherwise
        """
        if not self.available:
            return False

        if not text or not text.strip():
            return False

        try:
            cmd = [
                "say",
                "-v", self.voice,
                "-r", str(self.rate),
                text,
            ]

            result = subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                timeout=30,
            )

            if result.returncode != 0:
                logger.error(f"macOS say failed: {result.stderr.decode()}")
                return False

            return True

        except subprocess.TimeoutExpired:
            logger.error("macOS TTS timed out")
            return False
        except Exception as e:
            logger.error(f"macOS TTS error: {e}")
            return False

    def get_voices(self) -> List[VoiceInfo]:
        """
        Get list of available voices on macOS.

        Returns:
            List of VoiceInfo objects
        """
        if not self.available:
            return []

        voices: List[VoiceInfo] = []

        try:
            result = subprocess.run(
                ["say", "-v", "?"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if not line:
                        continue

                    # Format: "Name language # Description"
                    # Example: "Samantha en_US # Hello, my name is Samantha..."
                    parts = line.split('#', 1)
                    if not parts:
                        continue

                    # Parse voice name and language
                    voice_part = parts[0].strip()
                    voice_parts = voice_part.split()

                    if not voice_parts:
                        continue

                    voice_name = voice_parts[0]
                    language = voice_parts[1] if len(voice_parts) > 1 else 'unknown'

                    # Parse description if available
                    description = parts[1].strip() if len(parts) > 1 else ''

                    # Create VoiceInfo
                    voice_info = VoiceInfo(
                        id=voice_name,
                        name=voice_name,
                        language=language,
                        provider='macos',
                        quality=None,
                        installed=True,
                        filename=None,
                        metadata={'description': description} if description else {}
                    )

                    voices.append(voice_info)

                logger.info(f"Found {len(voices)} macOS voices")

        except Exception as e:
            logger.error(f"Failed to list macOS voices: {e}")

        return voices

    def get_name(self) -> str:
        """Get provider name."""
        return "macos"

    def get_info(self) -> str:
        """Get provider information."""
        if self.available:
            return f"macOS say (voice: {self.voice}, rate: {self.rate} wpm)"
        return "macOS say (not available)"
