"""
Piper TTS provider - High-quality neural text-to-speech.
https://github.com/rhasspy/piper
"""

import os
import shutil
import subprocess
import tempfile
import json
import time
from pathlib import Path
from typing import Optional, List, Tuple
import logging

from ..voice_info import VoiceInfo

logger = logging.getLogger(__name__)

# Default Piper voice directory
_VOICE_DIR = Path.home() / ".local" / "share" / "piper-voices"

# Voice cache (30 second TTL)
_voice_cache: Optional[List[VoiceInfo]] = None
_cache_time: float = 0
_CACHE_TTL = 30.0


class PiperProvider:
    """Piper TTS provider using neural voices."""

    def __init__(self, executable: Optional[str] = None, model: str = "en_US-lessac-medium"):
        """
        Initialize Piper provider.

        Args:
            executable: Path to piper executable (auto-detect if None)
            model: Voice model to use
        """
        self.executable = executable or self._find_piper()
        self.model = model
        self.available = self.executable is not None

        if self.available:
            logger.info(f"Piper TTS initialized: {self.executable} (model: {model})")
        else:
            logger.warning("Piper TTS not available")

    def _find_piper(self) -> Optional[str]:
        """Find piper executable in PATH or common locations."""
        # Check PATH first
        piper = shutil.which("piper")
        if piper:
            return piper

        # Check common installation locations
        common_paths = [
            "/usr/local/bin/piper",
            "/opt/homebrew/bin/piper",
            os.path.expanduser("~/.local/bin/piper"),
            os.path.expanduser("~/bin/piper"),
        ]

        for path in common_paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path

        return None

    def is_available(self) -> bool:
        """Check if Piper is available."""
        return self.available

    def speak(self, text: str) -> bool:
        """
        Speak text using Piper TTS.

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
            # Create temporary WAV file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as wav_file:
                wav_path = wav_file.name

            try:
                # Generate WAV file using --output_file (creates proper WAV format)
                piper_cmd = [
                    self.executable,
                    "--model", self.model,
                    "--data-dir", str(_VOICE_DIR),
                    "--output_file", wav_path
                ]

                result = subprocess.run(
                    piper_cmd,
                    input=text.encode('utf-8'),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=10,
                )

                if result.returncode != 0:
                    logger.error(f"Piper failed: {result.stderr.decode()}")
                    return False

                # Determine audio player
                player_cmd = self._get_audio_player()
                if not player_cmd:
                    logger.warning("No audio player found for Piper output")
                    return False

                # Play WAV file
                play_result = subprocess.run(
                    player_cmd + [wav_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=30,
                )

                return play_result.returncode == 0

            finally:
                # Clean up WAV file
                try:
                    os.unlink(wav_path)
                except:
                    pass

        except subprocess.TimeoutExpired:
            logger.error("Piper TTS timed out")
            return False
        except Exception as e:
            logger.error(f"Piper TTS error: {e}")
            return False

    def _get_audio_player(self) -> Optional[list]:
        """Get appropriate audio player command for platform."""
        import platform

        system = platform.system()

        if system == "Darwin":  # macOS
            if shutil.which("afplay"):
                return ["afplay"]
        elif system == "Linux":
            if shutil.which("aplay"):
                return ["aplay", "-q"]
            if shutil.which("paplay"):
                return ["paplay"]
            if shutil.which("ffplay"):
                return ["ffplay", "-nodisp", "-autoexit"]
        elif system == "Windows":
            # Windows can use powershell to play WAV
            return [
                "powershell",
                "-c",
                "(New-Object Media.SoundPlayer",
            ]

        return None

    def get_name(self) -> str:
        """Get provider name."""
        return "piper"

    def get_info(self) -> str:
        """Get provider information."""
        if self.available:
            return f"Piper TTS ({self.model})"
        return "Piper TTS (not available)"

    @staticmethod
    def _parse_voice_filename(filename: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Parse Piper voice filename to extract language, voice, and quality.

        Format: {language}-{voice}-{quality}.onnx
        Examples:
            - en_US-lessac-medium.onnx -> ("en_US", "lessac", "medium")
            - en_GB-alba-medium.onnx -> ("en_GB", "alba", "medium")

        Args:
            filename: Voice filename (e.g., "en_US-lessac-medium.onnx")

        Returns:
            Tuple of (language, voice, quality) or (None, None, None) if parsing fails
        """
        if not filename.endswith('.onnx'):
            return (None, None, None)

        # Remove .onnx extension
        name = filename[:-5]

        # Split by hyphen
        parts = name.split('-')

        if len(parts) >= 3:
            # Format: language-voice-quality
            language = parts[0]
            voice = parts[1]
            quality = parts[2]
            return (language, voice, quality)
        elif len(parts) == 2:
            # Format: language-voice (no quality)
            return (parts[0], parts[1], None)
        else:
            # Fallback: use filename as voice ID
            return (None, name, None)

    @staticmethod
    def _load_voice_metadata(onnx_path: Path) -> Optional[dict]:
        """
        Load metadata from companion .onnx.json file.

        Args:
            onnx_path: Path to .onnx file

        Returns:
            Dictionary of metadata or None if file doesn't exist
        """
        json_path = Path(str(onnx_path) + '.json')

        if not json_path.exists():
            return None

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load metadata from {json_path}: {e}")
            return None

    def _discover_voices(self) -> List[VoiceInfo]:
        """
        Discover installed Piper voices by scanning voice directory.

        Returns:
            List of VoiceInfo objects for discovered voices
        """
        voices: List[VoiceInfo] = []

        if not _VOICE_DIR.exists():
            logger.debug(f"Piper voice directory does not exist: {_VOICE_DIR}")
            return voices

        try:
            # Find all .onnx files
            onnx_files = list(_VOICE_DIR.glob("*.onnx"))

            for onnx_file in onnx_files:
                filename = onnx_file.name
                language, voice_id, quality = self._parse_voice_filename(filename)

                if not voice_id:
                    logger.warning(f"Could not parse Piper voice filename: {filename}")
                    continue

                # Load metadata if available
                metadata = self._load_voice_metadata(onnx_file)

                # Build display name
                if language:
                    # Convert language code to readable format
                    # e.g., en_US -> English US, en_GB -> English GB
                    lang_parts = language.replace('_', ' ')
                    display_name = f"{lang_parts.title()} ({voice_id.title()})"
                else:
                    display_name = voice_id.title()

                # Add quality suffix if available
                if quality:
                    display_name += f" [{quality}]"

                voice_info = VoiceInfo(
                    id=voice_id,
                    name=display_name,
                    language=language or 'unknown',
                    provider='piper',
                    quality=quality,
                    installed=True,
                    filename=str(onnx_file),
                    metadata=metadata or {}
                )

                voices.append(voice_info)

            logger.info(f"Discovered {len(voices)} Piper voices in {_VOICE_DIR}")

        except Exception as e:
            logger.error(f"Error discovering Piper voices: {e}")

        return voices

    def get_voices(self) -> List[VoiceInfo]:
        """
        Get list of installed Piper voices with caching.

        Returns:
            List of VoiceInfo objects
        """
        global _voice_cache, _cache_time

        # Check cache
        current_time = time.time()
        if _voice_cache is not None and (current_time - _cache_time) < _CACHE_TTL:
            logger.debug(f"Returning {len(_voice_cache)} cached Piper voices")
            return _voice_cache

        # Discover voices
        voices = self._discover_voices()

        # Update cache
        _voice_cache = voices
        _cache_time = current_time

        return voices

    @staticmethod
    def clear_cache():
        """Clear the voice discovery cache."""
        global _voice_cache, _cache_time
        _voice_cache = None
        _cache_time = 0
        logger.info("Cleared Piper voice cache")
