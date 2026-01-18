#!/usr/bin/env python3
"""
TTS IPC Bridge - JSON CLI for Electron IPC handlers

This script provides a JSON-based CLI interface for Electron's IPC handlers
to interact with the TTS system.

Usage:
    python -m integrations.tts.ipc_bridge list-voices [--provider PROVIDER]
    python -m integrations.tts.ipc_bridge test-voice --provider PROVIDER --voice VOICE_ID [--text TEXT]
    python -m integrations.tts.ipc_bridge get-status
"""

import sys
import json
import argparse
from typing import Dict, List, Any

# Import TTS components
from .manager import get_tts_manager
from .voice_info import VoiceInfo


def serialize_voice(voice: VoiceInfo) -> Dict[str, Any]:
    """Serialize VoiceInfo to JSON-compatible dict."""
    return voice.to_dict()


def list_voices_command(args) -> Dict[str, Any]:
    """List available voices."""
    try:
        manager = get_tts_manager()
        voices_by_provider = manager.list_all_voices(provider_filter=args.provider)

        # Convert to serializable format
        result = {}
        for provider_name, voices in voices_by_provider.items():
            result[provider_name] = [serialize_voice(v) for v in voices]

        return {
            "success": True,
            "voices": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def test_voice_command(args) -> Dict[str, Any]:
    """Test a voice by speaking text."""
    try:
        manager = get_tts_manager()

        # Get voice info
        voice = manager.get_voice_info(args.voice, provider=args.provider)

        if not voice:
            return {
                "success": False,
                "error": f"Voice '{args.voice}' not found"
            }

        # For Piper, we need to set the model
        if voice.provider == "piper":
            from pathlib import Path
            from .providers.piper import PiperProvider

            if not voice.filename:
                return {
                    "success": False,
                    "error": "Piper voice has no filename"
                }

            # Get model name from filename
            model_name = Path(voice.filename).stem

            # Create Piper provider with specific model
            piper = PiperProvider(model=model_name)

            if not piper.is_available():
                return {
                    "success": False,
                    "error": "Piper is not available"
                }

            success = piper.speak(args.text or "This is a test of the selected voice.")
        else:
            # Use manager for other providers
            success = manager.speak(
                args.text or "This is a test of the selected voice.",
                filter_content=False
            )

        if success:
            return {
                "success": True,
                "message": f"Successfully tested voice '{voice.name}'"
            }
        else:
            return {
                "success": False,
                "error": "Failed to speak text"
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_status_command(args) -> Dict[str, Any]:
    """Get TTS manager status."""
    try:
        manager = get_tts_manager()
        status = manager.get_status()

        return {
            "success": True,
            "status": status
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="TTS IPC Bridge - JSON CLI for Electron"
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # List voices command
    list_parser = subparsers.add_parser('list-voices', help='List available voices')
    list_parser.add_argument(
        '--provider',
        choices=['piper', 'macos', 'system'],
        help='Filter by provider'
    )

    # Test voice command
    test_parser = subparsers.add_parser('test-voice', help='Test a voice')
    test_parser.add_argument('--provider', required=True, help='Provider name')
    test_parser.add_argument('--voice', required=True, help='Voice ID')
    test_parser.add_argument('--text', help='Text to speak')

    # Get status command
    status_parser = subparsers.add_parser('get-status', help='Get TTS status')

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    result = None

    if args.command == 'list-voices':
        result = list_voices_command(args)
    elif args.command == 'test-voice':
        result = test_voice_command(args)
    elif args.command == 'get-status':
        result = get_status_command(args)

    # Output JSON result
    print(json.dumps(result, indent=2))

    # Exit with appropriate code
    sys.exit(0 if result and result.get('success') else 1)


if __name__ == '__main__':
    main()
