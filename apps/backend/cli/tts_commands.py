#!/usr/bin/env python3
"""
TTS Voice Management CLI

Command-line tool for discovering, testing, and managing TTS voices.

Usage:
    python apps/backend/cli/tts_commands.py list [--provider PROVIDER]
    python apps/backend/cli/tts_commands.py info VOICE_ID [--provider PROVIDER]
    python apps/backend/cli/tts_commands.py test VOICE_ID [--text TEXT] [--provider PROVIDER]
    python apps/backend/cli/tts_commands.py clear-cache
    python apps/backend/cli/tts_commands.py status
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from integrations.tts import get_tts_manager, VoiceInfo
from integrations.tts.providers.piper import PiperProvider


def list_voices(args):
    """List all available voices."""
    manager = get_tts_manager()

    voices_by_provider = manager.list_all_voices(provider_filter=args.provider)

    if not voices_by_provider:
        print("No voices found.")
        return

    total_voices = 0

    for provider_name, voices in voices_by_provider.items():
        if not voices:
            continue

        total_voices += len(voices)

        print(f"\n{provider_name.upper()} Provider ({len(voices)} voices):")
        print("-" * 60)

        for voice in voices:
            # Format: ID | Name | Language | Quality
            quality_str = f" [{voice.quality}]" if voice.quality else ""
            print(f"  {voice.id:20s} | {voice.name:30s} | {voice.language:10s}{quality_str}")

            # Show filename for file-based voices
            if voice.filename and args.verbose:
                print(f"    File: {voice.filename}")

    print(f"\nTotal: {total_voices} voices across {len(voices_by_provider)} providers")


def get_voice_info_cmd(args):
    """Get detailed information about a specific voice."""
    manager = get_tts_manager()

    voice = manager.get_voice_info(args.voice_id, provider=args.provider)

    if not voice:
        provider_str = f" in provider '{args.provider}'" if args.provider else ""
        print(f"Voice '{args.voice_id}' not found{provider_str}.")
        return 1

    print("\nVoice Information:")
    print("=" * 60)
    print(f"ID:         {voice.id}")
    print(f"Name:       {voice.name}")
    print(f"Language:   {voice.language}")
    print(f"Provider:   {voice.provider}")
    print(f"Quality:    {voice.quality or 'N/A'}")
    print(f"Installed:  {'Yes' if voice.installed else 'No'}")

    if voice.filename:
        print(f"File:       {voice.filename}")

    if voice.metadata:
        print("\nMetadata:")
        for key, value in voice.metadata.items():
            print(f"  {key}: {value}")

    return 0


def test_voice_cmd(args):
    """Test a voice by speaking text."""
    manager = get_tts_manager()

    # Get voice info
    voice = manager.get_voice_info(args.voice_id, provider=args.provider)

    if not voice:
        provider_str = f" in provider '{args.provider}'" if args.provider else ""
        print(f"Voice '{args.voice_id}' not found{provider_str}.")
        return 1

    print(f"Testing voice: {voice.name} ({voice.provider})")
    print(f"Text: {args.text}")

    # For Piper, we need to set the model
    if voice.provider == "piper":
        # Reconstruct model name from voice info
        if voice.filename:
            # Get filename without path and extension
            model_name = Path(voice.filename).stem
            print(f"Using Piper model: {model_name}")

            # Create a new Piper provider with this model
            from integrations.tts.providers.piper import PiperProvider
            piper = PiperProvider(model=model_name)

            if not piper.is_available():
                print("Error: Piper is not available")
                return 1

            success = piper.speak(args.text)
        else:
            print("Error: Piper voice has no filename")
            return 1
    else:
        # For macOS and system, use the manager
        success = manager.speak(args.text, filter_content=False)

    if success:
        print("✓ Voice test completed successfully")
        return 0
    else:
        print("✗ Voice test failed")
        return 1


def clear_cache_cmd(args):
    """Clear the Piper voice cache."""
    PiperProvider.clear_cache()
    print("✓ Piper voice cache cleared")
    return 0


def status_cmd(args):
    """Show TTS manager status."""
    manager = get_tts_manager()
    status = manager.get_status()

    print("\nTTS Manager Status:")
    print("=" * 60)
    print(f"Enabled:          {status['enabled']}")
    print(f"Active Provider:  {status['active_provider'] or 'None'}")

    if status['active_provider']:
        print(f"Provider Info:    {status['active_provider_info']}")

    print(f"\nAvailable Providers: {', '.join(status['available_providers']) or 'None'}")

    if status.get('voice_counts'):
        print("\nVoice Counts:")
        for provider, count in status['voice_counts'].items():
            print(f"  {provider}: {count} voices")

    print("\nConfiguration:")
    config = status['config']
    print(f"  Max Length:       {config['max_length']}")
    print(f"  Announce Phases:  {config['announce_phases']}")
    print(f"  Announce Subtasks: {config['announce_subtasks']}")
    print(f"  Announce QA:      {config['announce_qa']}")
    print(f"  Filter Code:      {config['filter_code_blocks']}")
    print(f"  Filter Markdown:  {config['filter_markdown']}")
    print(f"  Filter Paths:     {config['filter_file_paths']}")
    print(f"  Filter URLs:      {config['filter_urls']}")

    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="TTS Voice Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # List command
    list_parser = subparsers.add_parser('list', help='List available voices')
    list_parser.add_argument(
        '--provider',
        choices=['piper', 'macos', 'system'],
        help='Filter by provider'
    )
    list_parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed information (e.g., file paths)'
    )

    # Info command
    info_parser = subparsers.add_parser('info', help='Get voice information')
    info_parser.add_argument('voice_id', help='Voice ID to get info for')
    info_parser.add_argument(
        '--provider',
        choices=['piper', 'macos', 'system'],
        help='Provider to search in'
    )

    # Test command
    test_parser = subparsers.add_parser('test', help='Test a voice')
    test_parser.add_argument('voice_id', help='Voice ID to test')
    test_parser.add_argument(
        '--text',
        default='This is a test of the selected voice.',
        help='Text to speak (default: test message)'
    )
    test_parser.add_argument(
        '--provider',
        choices=['piper', 'macos', 'system'],
        help='Provider to use'
    )

    # Clear cache command
    clear_parser = subparsers.add_parser('clear-cache', help='Clear Piper voice cache')

    # Status command
    status_parser = subparsers.add_parser('status', help='Show TTS manager status')

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Execute command
    try:
        if args.command == 'list':
            list_voices(args)
            return 0
        elif args.command == 'info':
            return get_voice_info_cmd(args)
        elif args.command == 'test':
            return test_voice_cmd(args)
        elif args.command == 'clear-cache':
            return clear_cache_cmd(args)
        elif args.command == 'status':
            return status_cmd(args)
        else:
            parser.print_help()
            return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
