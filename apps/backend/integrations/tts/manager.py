"""
TTS Manager - Main interface for text-to-speech functionality.

Provides high-level methods for speaking various types of content
with automatic filtering and provider fallback.
"""

import logging
from pathlib import Path
from typing import Optional, List, Dict, Union

from .config import TTSConfig
from .filters import OutputFilter
from .voice_info import VoiceInfo
from .voice_lock import VoiceLock
from .providers.piper import PiperProvider
from .providers.macos import MacOSProvider
from .providers.system import SystemProvider
from .summarizer import summarize_for_tts

logger = logging.getLogger(__name__)


class TTSManager:
    """
    Manages TTS operations with multi-provider support and content filtering.

    Features:
    - Automatic provider fallback (Piper -> macOS -> System)
    - Content filtering (code blocks, markdown, paths, URLs)
    - Specialized methods for different announcement types
    """

    def __init__(self, config: Optional[TTSConfig] = None, project_dir: Optional[Union[str, Path]] = None):
        """
        Initialize TTS manager.

        Args:
            config: TTS configuration (uses env vars if None)
            project_dir: Optional project directory to read voice-config.json from
        """
        if config:
            self.config = config
        else:
            # Convert project_dir to Path if provided
            proj_path = Path(project_dir) if project_dir else None
            self.config = TTSConfig.from_env(project_dir=proj_path)
        self.filter = OutputFilter(
            filter_code=self.config.filter_code_blocks,
            filter_markdown=self.config.filter_markdown,
            filter_paths=self.config.filter_file_paths,
            filter_urls=self.config.filter_urls,
        )

        # Initialize providers
        self.providers = self._initialize_providers()
        self.active_provider = None

        if self.config.is_enabled():
            self._select_provider()

    def _initialize_providers(self) -> List:
        """Initialize all TTS providers."""
        providers = []

        # Initialize Piper
        piper = PiperProvider(
            executable=self.config.piper_executable,
            model=self.config.piper_model,
        )
        if piper.is_available():
            providers.append(piper)

        # Initialize macOS
        macos = MacOSProvider(
            voice=self.config.macos_voice,
            rate=self.config.macos_rate,
        )
        if macos.is_available():
            providers.append(macos)

        # Initialize system fallback
        system = SystemProvider()
        if system.is_available():
            providers.append(system)

        return providers

    def _select_provider(self):
        """Select active provider based on preference and availability."""
        if not self.providers:
            logger.warning("No TTS providers available")
            return

        # If specific provider requested, try to use it
        if self.config.preferred_provider:
            for provider in self.providers:
                if provider.get_name() == self.config.preferred_provider:
                    self.active_provider = provider
                    logger.info(f"Using preferred TTS provider: {provider.get_info()}")
                    return

            logger.warning(
                f"Preferred provider '{self.config.preferred_provider}' not available, "
                f"falling back to first available"
            )

        # Use first available provider
        self.active_provider = self.providers[0]
        logger.info(f"Using TTS provider: {self.active_provider.get_info()}")

    def is_enabled(self) -> bool:
        """Check if TTS is enabled and available."""
        return self.config.is_enabled() and self.active_provider is not None

    def speak(self, text: str, filter_content: bool = True, skip_lock: bool = False, user_question: Optional[str] = None) -> bool:
        """
        Speak arbitrary text with cross-process coordination.

        Args:
            text: Text to speak
            filter_content: Whether to filter code blocks, markdown, etc.
            skip_lock: Skip voice lock (use with caution - may cause overlapping audio)
            user_question: Optional user question for context-aware summarization

        Returns:
            True if successful, False otherwise
        """
        if not self.is_enabled():
            return False

        if not text or not text.strip():
            return False

        # Process text based on summarization settings
        if filter_content:
            if self.config.enable_ai_summarization:
                # Use AI-powered summarization with context awareness
                text, mode_used = summarize_for_tts(
                    response_text=text,
                    user_question=user_question,
                    mode=self.config.summarization_mode,
                    fallback_mode=self.config.fallback_mode
                )
                logger.debug(f"AI summarization used mode: {mode_used}")
            else:
                # Legacy: basic filtering + truncation
                text = self.filter.filter(text)
                if len(text) > self.config.max_length:
                    text = self.filter.truncate(text, self.config.max_length)

        # Skip if nothing left after filtering/summarization
        if not text or not text.strip():
            logger.debug("Text filtered to empty string, skipping TTS")
            return False

        # Acquire voice lock unless skipped
        if not skip_lock:
            logger.debug("Checking voice queue...")
            lock = VoiceLock()
            lock_result = lock.wait_for_lock(timeout_seconds=10.0)

            if not lock_result["success"]:
                if lock_result.get("timeout"):
                    logger.warning("Timeout waiting for voice access")
                    if lock_result.get("holder"):
                        holder = lock_result["holder"]
                        logger.warning(f"Lock held by: {holder['cli_id']} (PID: {holder['pid']})")
                elif lock_result.get("holder"):
                    holder = lock_result["holder"]
                    logger.warning(f"Voice busy - held by {holder['cli_id']}")
                return False

            try:
                # Try active provider first
                if self.active_provider and self.active_provider.speak(text):
                    return True

                # Try fallback providers
                for provider in self.providers:
                    if provider != self.active_provider:
                        logger.info(f"Trying fallback provider: {provider.get_name()}")
                        if provider.speak(text):
                            # Update active provider on success
                            self.active_provider = provider
                            return True

                logger.error("All TTS providers failed")
                return False

            finally:
                # Always release lock when done
                lock.release()
        else:
            # Skip lock - direct execution (may overlap)
            # Try active provider first
            if self.active_provider and self.active_provider.speak(text):
                return True

            # Try fallback providers
            for provider in self.providers:
                if provider != self.active_provider:
                    logger.info(f"Trying fallback provider: {provider.get_name()}")
                    if provider.speak(text):
                        # Update active provider on success
                        self.active_provider = provider
                        return True

            logger.error("All TTS providers failed")
            return False

    def speak_phase(self, phase_name: str, description: Optional[str] = None) -> bool:
        """
        Announce phase transition.

        Args:
            phase_name: Name of the phase (e.g., "Planning", "Implementation")
            description: Optional phase description

        Returns:
            True if successful, False otherwise
        """
        if not self.config.announce_phases:
            return False

        if description:
            text = f"Starting {phase_name}: {description}"
        else:
            text = f"Starting {phase_name}"

        return self.speak(text, filter_content=False)

    def speak_subtask_start(self, subtask_name: str) -> bool:
        """
        Announce subtask start.

        Args:
            subtask_name: Name of the subtask

        Returns:
            True if successful, False otherwise
        """
        if not self.config.announce_subtasks:
            return False

        # Filter the subtask name to remove technical content
        filtered_name = self.filter.filter(subtask_name)
        if not filtered_name:
            filtered_name = "next subtask"

        text = f"Working on: {filtered_name}"
        return self.speak(text, filter_content=False)

    def speak_subtask_complete(self, subtask_name: str, success: bool = True) -> bool:
        """
        Announce subtask completion.

        Args:
            subtask_name: Name of the subtask
            success: Whether subtask completed successfully

        Returns:
            True if successful, False otherwise
        """
        if not self.config.announce_subtasks:
            return False

        # Filter the subtask name
        filtered_name = self.filter.filter(subtask_name)
        if not filtered_name:
            filtered_name = "subtask"

        if success:
            text = f"Completed: {filtered_name}"
        else:
            text = f"Failed: {filtered_name}"

        return self.speak(text, filter_content=False)

    def speak_qa_result(self, passed: bool, issue_count: Optional[int] = None) -> bool:
        """
        Announce QA validation result.

        Args:
            passed: Whether QA passed
            issue_count: Number of issues found (if not passed)

        Returns:
            True if successful, False otherwise
        """
        if not self.config.announce_qa:
            return False

        if passed:
            text = "Quality assurance passed. All acceptance criteria met."
        else:
            if issue_count and issue_count > 0:
                text = f"Quality assurance found {issue_count} issue{'s' if issue_count != 1 else ''}. Starting fixes."
            else:
                text = "Quality assurance found issues. Starting fixes."

        return self.speak(text, filter_content=False)

    def speak_build_complete(self, success: bool) -> bool:
        """
        Announce build completion.

        Args:
            success: Whether build completed successfully

        Returns:
            True if successful, False otherwise
        """
        if success:
            text = "Build completed successfully. Ready for review."
        else:
            text = "Build failed. Please review the errors."

        return self.speak(text, filter_content=False)

    def speak_error(self, error_message: str) -> bool:
        """
        Announce error message.

        Args:
            error_message: Error message to speak

        Returns:
            True if successful, False otherwise
        """
        # Filter technical content from error
        filtered = self.filter.filter(error_message)

        if not filtered or len(filtered) < 10:
            # If filtering removes too much, use generic message
            text = "An error occurred. Check the console for details."
        else:
            text = f"Error: {filtered}"

        return self.speak(text, filter_content=False)

    def list_all_voices(self, provider_filter: Optional[str] = None) -> Dict[str, List[VoiceInfo]]:
        """
        List all available voices grouped by provider.

        Args:
            provider_filter: Optional provider name to filter by (e.g., "piper", "macos", "system")

        Returns:
            Dictionary mapping provider name to list of VoiceInfo objects
            Example: {"piper": [VoiceInfo(...), ...], "macos": [...]}
        """
        voices_by_provider: Dict[str, List[VoiceInfo]] = {}

        for provider in self.providers:
            provider_name = provider.get_name()

            # Apply filter if specified
            if provider_filter and provider_name != provider_filter:
                continue

            # Get voices from provider (if method exists)
            if hasattr(provider, 'get_voices'):
                voices = provider.get_voices()
                voices_by_provider[provider_name] = voices
            else:
                voices_by_provider[provider_name] = []

        return voices_by_provider

    def get_voice_info(self, voice_id: str, provider: Optional[str] = None) -> Optional[VoiceInfo]:
        """
        Get detailed information about a specific voice.

        Args:
            voice_id: Voice identifier to search for
            provider: Optional provider name to search within

        Returns:
            VoiceInfo object if found, None otherwise
        """
        # Search in all providers or specific provider
        providers_to_search = self.providers

        if provider:
            providers_to_search = [p for p in self.providers if p.get_name() == provider]

        for prov in providers_to_search:
            if hasattr(prov, 'get_voices'):
                voices = prov.get_voices()
                for voice in voices:
                    if voice.id == voice_id:
                        return voice

        return None

    def get_status(self) -> dict:
        """
        Get TTS manager status.

        Returns:
            Dictionary with status information
        """
        # Get voice counts per provider
        voice_counts = {}
        for provider in self.providers:
            provider_name = provider.get_name()
            if hasattr(provider, 'get_voices'):
                voices = provider.get_voices()
                voice_counts[provider_name] = len(voices)
            else:
                voice_counts[provider_name] = 0

        return {
            "enabled": self.is_enabled(),
            "active_provider": self.active_provider.get_name() if self.active_provider else None,
            "active_provider_info": self.active_provider.get_info() if self.active_provider else None,
            "available_providers": [p.get_name() for p in self.providers],
            "voice_counts": voice_counts,
            "config": {
                "max_length": self.config.max_length,
                "announce_phases": self.config.announce_phases,
                "announce_subtasks": self.config.announce_subtasks,
                "announce_qa": self.config.announce_qa,
                "filter_code_blocks": self.config.filter_code_blocks,
                "filter_markdown": self.config.filter_markdown,
                "filter_file_paths": self.config.filter_file_paths,
                "filter_urls": self.config.filter_urls,
                "enable_ai_summarization": self.config.enable_ai_summarization,
                "summarization_mode": self.config.summarization_mode,
                "fallback_mode": self.config.fallback_mode,
                "ollama_url": self.config.ollama_url,
                "ollama_model": self.config.ollama_model,
            }
        }


# Global instance (optional - can also create per-session)
_global_tts_manager: Optional[TTSManager] = None


def get_tts_manager(config: Optional[TTSConfig] = None, project_dir: Optional[Union[str, Path]] = None) -> TTSManager:
    """
    Get TTS manager instance.

    When project_dir is provided, always creates a fresh manager to ensure
    the latest voice-config.json settings are used. This is important because
    users may change voice settings in the UI between calls.

    Args:
        config: Optional configuration (uses env vars if None)
        project_dir: Optional project directory to read voice-config.json from

    Returns:
        TTSManager instance
    """
    global _global_tts_manager

    # If project_dir is provided, always create fresh manager to pick up config changes
    if project_dir is not None:
        proj_path = Path(project_dir) if isinstance(project_dir, str) else project_dir
        # Always recreate to ensure we read the latest voice-config.json
        _global_tts_manager = TTSManager(config, project_dir=proj_path)
        return _global_tts_manager

    # No project_dir - use cached global if available
    if _global_tts_manager is None:
        _global_tts_manager = TTSManager(config, project_dir=None)

    return _global_tts_manager


def reset_tts_manager():
    """Reset global TTS manager (useful for testing or config changes)."""
    global _global_tts_manager
    _global_tts_manager = None
