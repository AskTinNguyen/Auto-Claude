"""
Unit tests for TTS voice listing functionality.

Tests voice discovery, caching, and management across all providers.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import TTS components
from apps.backend.integrations.tts.voice_info import VoiceInfo
from apps.backend.integrations.tts.providers.piper import PiperProvider, _VOICE_DIR
from apps.backend.integrations.tts.providers.macos import MacOSProvider
from apps.backend.integrations.tts.providers.system import SystemProvider
from apps.backend.integrations.tts.manager import TTSManager


class TestVoiceInfo:
    """Test VoiceInfo dataclass."""

    def test_voice_info_creation(self):
        """Test creating a VoiceInfo object."""
        voice = VoiceInfo(
            id="test-voice",
            name="Test Voice",
            language="en_US",
            provider="piper",
            quality="medium",
        )

        assert voice.id == "test-voice"
        assert voice.name == "Test Voice"
        assert voice.language == "en_US"
        assert voice.provider == "piper"
        assert voice.quality == "medium"
        assert voice.installed is True
        assert voice.filename is None

    def test_voice_info_to_dict(self):
        """Test converting VoiceInfo to dictionary."""
        voice = VoiceInfo(
            id="test",
            name="Test",
            language="en",
            provider="piper",
        )

        data = voice.to_dict()

        assert data['id'] == "test"
        assert data['name'] == "Test"
        assert data['language'] == "en"
        assert data['provider'] == "piper"
        assert data['installed'] is True

    def test_voice_info_from_dict(self):
        """Test creating VoiceInfo from dictionary."""
        data = {
            'id': 'test',
            'name': 'Test',
            'language': 'en',
            'provider': 'piper',
            'quality': 'high',
        }

        voice = VoiceInfo.from_dict(data)

        assert voice.id == 'test'
        assert voice.name == 'Test'
        assert voice.quality == 'high'


class TestPiperProvider:
    """Test Piper provider voice discovery."""

    def test_parse_voice_filename_standard(self):
        """Test parsing standard Piper voice filename."""
        filename = "en_US-lessac-medium.onnx"

        language, voice, quality = PiperProvider._parse_voice_filename(filename)

        assert language == "en_US"
        assert voice == "lessac"
        assert quality == "medium"

    def test_parse_voice_filename_no_quality(self):
        """Test parsing filename without quality."""
        filename = "en_GB-alba.onnx"

        language, voice, quality = PiperProvider._parse_voice_filename(filename)

        assert language == "en_GB"
        assert voice == "alba"
        assert quality is None

    def test_parse_voice_filename_invalid(self):
        """Test parsing invalid filename (no .onnx extension)."""
        filename = "invalid"

        language, voice, quality = PiperProvider._parse_voice_filename(filename)

        # Should return all None for files without .onnx extension
        assert language is None
        assert voice is None
        assert quality is None

    def test_parse_voice_filename_single_part(self):
        """Test parsing filename with single part."""
        filename = "single.onnx"

        language, voice, quality = PiperProvider._parse_voice_filename(filename)

        # Fallback case: use filename as voice ID
        assert language is None
        assert voice == "single"
        assert quality is None

    def test_load_voice_metadata(self):
        """Test loading voice metadata from JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            onnx_path = Path(tmpdir) / "test-voice.onnx"
            json_path = Path(tmpdir) / "test-voice.onnx.json"

            # Create dummy ONNX file
            onnx_path.touch()

            # Create metadata file
            metadata = {
                "key": "test_voice",
                "speaker_id_map": {"default": 0},
                "language": {"code": "en_US"},
            }

            with open(json_path, 'w') as f:
                json.dump(metadata, f)

            # Load metadata
            loaded = PiperProvider._load_voice_metadata(onnx_path)

            assert loaded is not None
            assert loaded['key'] == 'test_voice'
            assert 'speaker_id_map' in loaded

    def test_load_voice_metadata_missing(self):
        """Test loading metadata when file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            onnx_path = Path(tmpdir) / "test-voice.onnx"

            metadata = PiperProvider._load_voice_metadata(onnx_path)

            assert metadata is None

    @patch('apps.backend.integrations.tts.providers.piper._VOICE_DIR')
    def test_discover_voices(self, mock_voice_dir):
        """Test discovering Piper voices."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            mock_voice_dir.__truediv__ = tmpdir_path.__truediv__
            mock_voice_dir.exists.return_value = True
            mock_voice_dir.glob = tmpdir_path.glob

            # Create test voice files
            (tmpdir_path / "en_US-lessac-medium.onnx").touch()
            (tmpdir_path / "en_GB-alba-medium.onnx").touch()
            (tmpdir_path / "fr_FR-siwis-medium.onnx").touch()

            provider = PiperProvider()
            voices = provider._discover_voices()

            # Should find 3 voices
            assert len(voices) == 3

            # Check first voice
            lessac = next(v for v in voices if v.id == 'lessac')
            assert lessac.language == 'en_US'
            assert lessac.quality == 'medium'
            assert lessac.provider == 'piper'

    def test_get_voices_caching(self):
        """Test voice discovery caching mechanism."""
        with patch.object(PiperProvider, '_discover_voices') as mock_discover:
            mock_discover.return_value = [
                VoiceInfo(id="test", name="Test", language="en", provider="piper")
            ]

            provider = PiperProvider()

            # Clear cache first
            PiperProvider.clear_cache()

            # First call should discover
            voices1 = provider.get_voices()
            assert mock_discover.call_count == 1

            # Second call should use cache
            voices2 = provider.get_voices()
            assert mock_discover.call_count == 1  # Not called again

            # Results should be the same
            assert len(voices1) == len(voices2)
            assert voices1[0].id == voices2[0].id

    def test_clear_cache(self):
        """Test clearing voice cache."""
        with patch.object(PiperProvider, '_discover_voices') as mock_discover:
            mock_discover.return_value = [
                VoiceInfo(id="test", name="Test", language="en", provider="piper")
            ]

            provider = PiperProvider()

            # Populate cache
            PiperProvider.clear_cache()
            voices1 = provider.get_voices()
            assert mock_discover.call_count == 1

            # Clear cache
            PiperProvider.clear_cache()

            # Should discover again
            voices2 = provider.get_voices()
            assert mock_discover.call_count == 2


class TestMacOSProvider:
    """Test macOS provider voice listing."""

    @patch('subprocess.run')
    @patch('platform.system')
    @patch('shutil.which')
    def test_get_voices(self, mock_which, mock_platform, mock_run):
        """Test listing macOS voices."""
        # Mock macOS environment
        mock_platform.return_value = "Darwin"
        mock_which.return_value = "/usr/bin/say"

        # Mock say -v ? output
        mock_output = """Samantha en_US # Hello, my name is Samantha...
Alex en_US # Most people recognize me...
Victoria en_GB # Isn't it nice..."""

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = mock_output
        mock_run.return_value = mock_result

        provider = MacOSProvider()
        voices = provider.get_voices()

        # Should find 3 voices
        assert len(voices) == 3

        # Check Samantha
        samantha = next(v for v in voices if v.id == 'Samantha')
        assert samantha.name == 'Samantha'
        assert samantha.language == 'en_US'
        assert samantha.provider == 'macos'


class TestSystemProvider:
    """Test system provider voice listing."""

    @patch('subprocess.run')
    @patch('platform.system')
    @patch('shutil.which')
    def test_get_linux_voices(self, mock_which, mock_platform, mock_run):
        """Test listing espeak voices on Linux."""
        # Mock Linux environment
        mock_platform.return_value = "Linux"
        mock_which.side_effect = lambda cmd: "/usr/bin/espeak" if cmd == "espeak" else None

        # Mock espeak --voices output
        mock_output = """Pty Language Age/Gender VoiceName          File          Other Languages
 5  en-GB          f  en-gb                en-gb
 5  en-US          M  en-us                en-us
 5  fr-FR          M  fr-fr                fr-fr"""

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = mock_output
        mock_run.return_value = mock_result

        provider = SystemProvider()
        voices = provider.get_voices()

        # Should find 3 voices
        assert len(voices) == 3

        # Check first voice
        en_gb = next(v for v in voices if v.id == 'en-gb')
        assert en_gb.language == 'en-GB'
        assert en_gb.provider == 'system'


class TestTTSManager:
    """Test TTS Manager voice listing."""

    def test_list_all_voices(self):
        """Test listing all voices from all providers."""
        with patch('apps.backend.integrations.tts.manager.PiperProvider') as MockPiper, \
             patch('apps.backend.integrations.tts.manager.MacOSProvider') as MockMacOS, \
             patch('apps.backend.integrations.tts.manager.SystemProvider') as MockSystem:

            # Mock Piper provider
            piper_instance = Mock()
            piper_instance.is_available.return_value = True
            piper_instance.get_name.return_value = 'piper'
            piper_instance.get_voices.return_value = [
                VoiceInfo(id="lessac", name="Lessac", language="en_US", provider="piper")
            ]
            MockPiper.return_value = piper_instance

            # Mock macOS provider
            macos_instance = Mock()
            macos_instance.is_available.return_value = True
            macos_instance.get_name.return_value = 'macos'
            macos_instance.get_voices.return_value = [
                VoiceInfo(id="Samantha", name="Samantha", language="en_US", provider="macos")
            ]
            MockMacOS.return_value = macos_instance

            # Mock system provider
            system_instance = Mock()
            system_instance.is_available.return_value = False
            MockSystem.return_value = system_instance

            # Create manager
            manager = TTSManager()

            # List all voices
            voices = manager.list_all_voices()

            assert 'piper' in voices
            assert 'macos' in voices
            assert len(voices['piper']) == 1
            assert len(voices['macos']) == 1

    def test_list_voices_with_filter(self):
        """Test listing voices with provider filter."""
        with patch('apps.backend.integrations.tts.manager.PiperProvider') as MockPiper, \
             patch('apps.backend.integrations.tts.manager.MacOSProvider') as MockMacOS, \
             patch('apps.backend.integrations.tts.manager.SystemProvider') as MockSystem:

            # Mock providers
            piper_instance = Mock()
            piper_instance.is_available.return_value = True
            piper_instance.get_name.return_value = 'piper'
            piper_instance.get_voices.return_value = [
                VoiceInfo(id="lessac", name="Lessac", language="en_US", provider="piper")
            ]
            MockPiper.return_value = piper_instance

            macos_instance = Mock()
            macos_instance.is_available.return_value = True
            macos_instance.get_name.return_value = 'macos'
            macos_instance.get_voices.return_value = []
            MockMacOS.return_value = macos_instance

            system_instance = Mock()
            system_instance.is_available.return_value = False
            MockSystem.return_value = system_instance

            # Create manager
            manager = TTSManager()

            # Filter by piper only
            voices = manager.list_all_voices(provider_filter='piper')

            assert 'piper' in voices
            assert 'macos' not in voices

    def test_get_voice_info(self):
        """Test getting info for specific voice."""
        with patch('apps.backend.integrations.tts.manager.PiperProvider') as MockPiper, \
             patch('apps.backend.integrations.tts.manager.MacOSProvider') as MockMacOS, \
             patch('apps.backend.integrations.tts.manager.SystemProvider') as MockSystem:

            # Mock Piper provider
            piper_instance = Mock()
            piper_instance.is_available.return_value = True
            piper_instance.get_name.return_value = 'piper'
            piper_instance.get_voices.return_value = [
                VoiceInfo(id="lessac", name="Lessac", language="en_US", provider="piper", quality="medium")
            ]
            MockPiper.return_value = piper_instance

            macos_instance = Mock()
            macos_instance.is_available.return_value = False
            MockMacOS.return_value = macos_instance

            system_instance = Mock()
            system_instance.is_available.return_value = False
            MockSystem.return_value = system_instance

            # Create manager
            manager = TTSManager()

            # Get voice info
            voice = manager.get_voice_info("lessac")

            assert voice is not None
            assert voice.id == "lessac"
            assert voice.quality == "medium"

    def test_get_voice_info_not_found(self):
        """Test getting info for non-existent voice."""
        with patch('apps.backend.integrations.tts.manager.PiperProvider') as MockPiper, \
             patch('apps.backend.integrations.tts.manager.MacOSProvider') as MockMacOS, \
             patch('apps.backend.integrations.tts.manager.SystemProvider') as MockSystem:

            piper_instance = Mock()
            piper_instance.is_available.return_value = True
            piper_instance.get_name.return_value = 'piper'
            piper_instance.get_voices.return_value = []
            MockPiper.return_value = piper_instance

            macos_instance = Mock()
            macos_instance.is_available.return_value = False
            MockMacOS.return_value = macos_instance

            system_instance = Mock()
            system_instance.is_available.return_value = False
            MockSystem.return_value = system_instance

            manager = TTSManager()

            # Get voice info
            voice = manager.get_voice_info("nonexistent")

            assert voice is None

    def test_status_includes_voice_counts(self):
        """Test that status includes voice counts."""
        with patch('apps.backend.integrations.tts.manager.PiperProvider') as MockPiper, \
             patch('apps.backend.integrations.tts.manager.MacOSProvider') as MockMacOS, \
             patch('apps.backend.integrations.tts.manager.SystemProvider') as MockSystem:

            # Mock Piper with 2 voices
            piper_instance = Mock()
            piper_instance.is_available.return_value = True
            piper_instance.get_name.return_value = 'piper'
            piper_instance.get_info.return_value = 'Piper TTS'
            piper_instance.get_voices.return_value = [
                VoiceInfo(id="v1", name="V1", language="en", provider="piper"),
                VoiceInfo(id="v2", name="V2", language="en", provider="piper"),
            ]
            MockPiper.return_value = piper_instance

            # Mock macOS with 1 voice
            macos_instance = Mock()
            macos_instance.is_available.return_value = True
            macos_instance.get_name.return_value = 'macos'
            macos_instance.get_info.return_value = 'macOS TTS'
            macos_instance.get_voices.return_value = [
                VoiceInfo(id="v1", name="V1", language="en", provider="macos"),
            ]
            MockMacOS.return_value = macos_instance

            system_instance = Mock()
            system_instance.is_available.return_value = False
            MockSystem.return_value = system_instance

            manager = TTSManager()
            status = manager.get_status()

            assert 'voice_counts' in status
            assert status['voice_counts']['piper'] == 2
            assert status['voice_counts']['macos'] == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
