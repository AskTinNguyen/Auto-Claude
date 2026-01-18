#!/usr/bin/env python3
"""
Test script to verify TTS voice configuration integration.

This script:
1. Updates voice-config.json with test voice selection
2. Initializes TTS manager with project directory
3. Verifies the selected voice is correctly loaded
"""

import json
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables from .env
load_dotenv()

from integrations.tts.manager import TTSManager
from integrations.tts.config import TTSConfig

def test_voice_config():
    """Test that voice-config.json is correctly read by TTS manager."""

    # Get project directory (two levels up from backend/)
    project_dir = Path(__file__).parent.parent.parent
    ralph_dir = project_dir / ".ralph"
    config_path = ralph_dir / "voice-config.json"

    print(f"Project directory: {project_dir}")
    print(f"Config path: {config_path}")

    # Ensure .ralph directory exists
    ralph_dir.mkdir(exist_ok=True)

    # Read existing config or create new one
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
        print(f"\nExisting config: {json.dumps(config, indent=2)}")
    else:
        config = {}

    # Add test voice selection (Piper Ryan)
    test_config = {
        **config,
        "voice": {
            "provider": "piper",
            "selectedVoice": "en_US-ryan-medium"
        }
    }

    # Write test config
    with open(config_path, 'w') as f:
        json.dump(test_config, f, indent=2)
    print(f"\nUpdated config with test voice: {json.dumps(test_config, indent=2)}")

    # Initialize TTS manager with project directory
    print("\n" + "="*60)
    print("Initializing TTS Manager...")
    print("="*60)

    tts_manager = TTSManager(project_dir=project_dir)

    # Check configuration
    print(f"\nTTS Configuration:")
    print(f"  Enabled: {tts_manager.config.is_enabled()}")
    print(f"  Preferred Provider: {tts_manager.config.preferred_provider}")
    print(f"  Piper Model: {tts_manager.config.piper_model}")
    print(f"  macOS Voice: {tts_manager.config.macos_voice}")

    # Check active provider
    if tts_manager.active_provider:
        print(f"\nActive Provider: {tts_manager.active_provider.get_name()}")
        print(f"Provider Info: {tts_manager.active_provider.get_info()}")
    else:
        print("\nNo active provider (TTS may be disabled in .env)")

    # Verify voice selection
    print("\n" + "="*60)
    print("Verification Results:")
    print("="*60)

    success = True

    # Check if preferred provider matches
    if tts_manager.config.preferred_provider != "piper":
        print(f"❌ Expected preferred_provider='piper', got '{tts_manager.config.preferred_provider}'")
        success = False
    else:
        print(f"✅ Preferred provider correctly set to 'piper'")

    # Check if piper model matches
    if tts_manager.config.piper_model != "en_US-ryan-medium":
        print(f"❌ Expected piper_model='en_US-ryan-medium', got '{tts_manager.config.piper_model}'")
        success = False
    else:
        print(f"✅ Piper model correctly set to 'en_US-ryan-medium'")

    # Check if active provider is piper (if TTS enabled)
    if tts_manager.is_enabled():
        if tts_manager.active_provider and tts_manager.active_provider.get_name() != "piper":
            print(f"⚠️  Active provider is '{tts_manager.active_provider.get_name()}', not 'piper'")
            print("   (This may be due to Piper not being available)")
        elif tts_manager.active_provider:
            print(f"✅ Active provider is 'piper' as expected")
    else:
        print("ℹ️  TTS is disabled (TTS_ENABLED=false in .env)")

    print("\n" + "="*60)
    if success:
        print("✅ Voice configuration integration test PASSED")
    else:
        print("❌ Voice configuration integration test FAILED")
    print("="*60)

    return success

if __name__ == "__main__":
    success = test_voice_config()
    sys.exit(0 if success else 1)
