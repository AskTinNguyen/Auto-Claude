"""
System fallback TTS provider - Platform-specific TTS commands.
"""

import platform
import shutil
import subprocess
import logging
from typing import Optional, List

from ..voice_info import VoiceInfo

logger = logging.getLogger(__name__)


class SystemProvider:
    """
    System fallback TTS provider.

    Attempts to use platform-specific TTS commands:
    - Linux: espeak, spd-say, or festival
    - Windows: PowerShell Add-Type System.Speech
    - macOS: Falls back to 'say' (same as MacOSProvider)
    """

    def __init__(self):
        """Initialize system TTS provider."""
        self.system = platform.system()
        self.command = self._find_command()
        self.available = self.command is not None

        if self.available:
            logger.info(f"System TTS initialized: {self.command[0]}")
        else:
            logger.warning(f"No system TTS found for {self.system}")

    def _find_command(self) -> Optional[list]:
        """Find appropriate TTS command for the system."""
        if self.system == "Linux":
            return self._find_linux_command()
        elif self.system == "Windows":
            return self._find_windows_command()
        elif self.system == "Darwin":
            return self._find_macos_command()

        return None

    def _find_linux_command(self) -> Optional[list]:
        """Find TTS command for Linux."""
        # Try espeak-ng first (better quality)
        if shutil.which("espeak-ng"):
            return ["espeak-ng"]

        # Try espeak
        if shutil.which("espeak"):
            return ["espeak"]

        # Try spd-say (speech-dispatcher)
        if shutil.which("spd-say"):
            return ["spd-say"]

        # Try festival
        if shutil.which("festival"):
            return ["festival", "--tts"]

        # Try flite (lightweight)
        if shutil.which("flite"):
            return ["flite"]

        return None

    def _find_windows_command(self) -> Optional[list]:
        """Find TTS command for Windows."""
        # PowerShell is always available on modern Windows
        if shutil.which("powershell"):
            return [
                "powershell",
                "-Command",
                "Add-Type -AssemblyName System.Speech; "
                "$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                "$synth.Speak($args[0])",
            ]

        return None

    def _find_macos_command(self) -> Optional[list]:
        """Find TTS command for macOS."""
        if shutil.which("say"):
            return ["say"]

        return None

    def is_available(self) -> bool:
        """Check if provider is available."""
        return self.available

    def speak(self, text: str) -> bool:
        """
        Speak text using system TTS command.

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
            cmd = self.command.copy()

            # Handle different command formats
            if cmd[0] == "powershell":
                # PowerShell expects text as argument to the script
                cmd.append(text)
            else:
                # Most commands accept text as final argument
                cmd.append(text)

            result = subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                timeout=30,
            )

            if result.returncode != 0:
                logger.error(f"System TTS failed: {result.stderr.decode()}")
                return False

            return True

        except subprocess.TimeoutExpired:
            logger.error("System TTS timed out")
            return False
        except Exception as e:
            logger.error(f"System TTS error: {e}")
            return False

    def get_name(self) -> str:
        """Get provider name."""
        return "system"

    def get_info(self) -> str:
        """Get provider information."""
        if self.available:
            return f"System TTS ({self.command[0]} on {self.system})"
        return f"System TTS (not available on {self.system})"

    def _get_linux_voices(self) -> List[VoiceInfo]:
        """Get voices for Linux (espeak/espeak-ng)."""
        voices: List[VoiceInfo] = []

        # Try espeak-ng first, then espeak
        espeak_cmd = None
        if shutil.which("espeak-ng"):
            espeak_cmd = "espeak-ng"
        elif shutil.which("espeak"):
            espeak_cmd = "espeak"

        if not espeak_cmd:
            return voices

        try:
            result = subprocess.run(
                [espeak_cmd, "--voices"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                lines = result.stdout.split('\n')
                # Skip header line
                for line in lines[1:]:
                    line = line.strip()
                    if not line:
                        continue

                    # Format: "Pty Language Age/Gender VoiceName File Other Languages"
                    # Example: "5  en-GB          f  en-gb          en-gb"
                    parts = line.split()

                    if len(parts) >= 4:
                        language = parts[1]
                        voice_name = parts[3]

                        voice_info = VoiceInfo(
                            id=voice_name,
                            name=f"{language} ({voice_name})",
                            language=language,
                            provider='system',
                            quality=None,
                            installed=True,
                            filename=None,
                            metadata={'engine': espeak_cmd}
                        )

                        voices.append(voice_info)

                logger.info(f"Found {len(voices)} espeak voices")

        except Exception as e:
            logger.error(f"Failed to list espeak voices: {e}")

        return voices

    def _get_windows_voices(self) -> List[VoiceInfo]:
        """Get voices for Windows (SAPI)."""
        voices: List[VoiceInfo] = []

        if not shutil.which("powershell"):
            return voices

        try:
            # PowerShell script to list installed voices
            ps_script = (
                "Add-Type -AssemblyName System.Speech; "
                "$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                "$synth.GetInstalledVoices() | ForEach-Object { "
                "$_.VoiceInfo.Name + '|' + $_.VoiceInfo.Culture.Name "
                "}"
            )

            result = subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if not line or '|' not in line:
                        continue

                    # Parse: "VoiceName|Culture"
                    parts = line.split('|')
                    if len(parts) == 2:
                        voice_name = parts[0].strip()
                        culture = parts[1].strip()

                        voice_info = VoiceInfo(
                            id=voice_name,
                            name=voice_name,
                            language=culture,
                            provider='system',
                            quality=None,
                            installed=True,
                            filename=None,
                            metadata={'engine': 'SAPI'}
                        )

                        voices.append(voice_info)

                logger.info(f"Found {len(voices)} Windows SAPI voices")

        except Exception as e:
            logger.error(f"Failed to list Windows voices: {e}")

        return voices

    def _get_macos_voices(self) -> List[VoiceInfo]:
        """Get voices for macOS (say)."""
        voices: List[VoiceInfo] = []

        if not shutil.which("say"):
            return voices

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
                    parts = line.split('#', 1)
                    if not parts:
                        continue

                    voice_part = parts[0].strip()
                    voice_parts = voice_part.split()

                    if not voice_parts:
                        continue

                    voice_name = voice_parts[0]
                    language = voice_parts[1] if len(voice_parts) > 1 else 'unknown'

                    voice_info = VoiceInfo(
                        id=voice_name,
                        name=voice_name,
                        language=language,
                        provider='system',
                        quality=None,
                        installed=True,
                        filename=None,
                        metadata={'engine': 'say'}
                    )

                    voices.append(voice_info)

                logger.info(f"Found {len(voices)} macOS say voices")

        except Exception as e:
            logger.error(f"Failed to list macOS voices: {e}")

        return voices

    def get_voices(self) -> List[VoiceInfo]:
        """
        Get list of available system voices.

        Returns:
            List of VoiceInfo objects
        """
        if not self.available:
            return []

        if self.system == "Linux":
            return self._get_linux_voices()
        elif self.system == "Windows":
            return self._get_windows_voices()
        elif self.system == "Darwin":
            return self._get_macos_voices()

        return []
