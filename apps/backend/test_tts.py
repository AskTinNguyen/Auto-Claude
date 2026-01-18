#!/usr/bin/env python3
"""
Test script for TTS integration.

Usage:
    python test_tts.py                    # Test with default config
    python test_tts.py --provider piper   # Test specific provider
    python test_tts.py --demo             # Run full demo
"""

import argparse
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from integrations.tts import TTSManager, TTSConfig


def test_basic_speech(manager: TTSManager):
    """Test basic speech functionality."""
    print("\n=== Testing Basic Speech ===")

    # Test simple text
    print("Speaking: 'Hello, this is the TTS integration test.'")
    manager.speak("Hello, this is the TTS integration test.")

    # Test filtered text (should remove code)
    print("\nSpeaking text with code blocks (should filter):")
    manager.speak("Here is some code: ```python\nprint('hello')\n``` and that's it.")


def test_phase_announcements(manager: TTSManager):
    """Test phase announcement methods."""
    print("\n=== Testing Phase Announcements ===")

    phases = [
        ("Planning", "Creating implementation plan"),
        ("Implementation", "Building the feature"),
        ("Testing", "Running QA validation"),
    ]

    for phase_name, description in phases:
        print(f"Announcing phase: {phase_name}")
        manager.speak_phase(phase_name, description)


def test_subtask_announcements(manager: TTSManager):
    """Test subtask announcement methods."""
    print("\n=== Testing Subtask Announcements ===")

    subtasks = [
        ("Create user authentication module", True),
        ("Add login endpoint to API", True),
        ("Write unit tests for auth", False),
    ]

    for task, success in subtasks:
        print(f"Announcing subtask: {task} (success={success})")
        manager.speak_subtask_complete(task, success)


def test_qa_announcements(manager: TTSManager):
    """Test QA announcement methods."""
    print("\n=== Testing QA Announcements ===")

    # QA passed
    print("Announcing QA pass:")
    manager.speak_qa_result(passed=True)

    # QA failed with issues
    print("\nAnnouncing QA fail with 3 issues:")
    manager.speak_qa_result(passed=False, issue_count=3)


def test_error_handling(manager: TTSManager):
    """Test error announcement with filtering."""
    print("\n=== Testing Error Announcements ===")

    error_msg = """
    Failed to import module at /path/to/file.py line 42.
    Error: ModuleNotFoundError: No module named 'foo'
    ```python
    import foo
    ```
    """

    print("Speaking error (should filter paths and code):")
    manager.speak_error(error_msg)


def test_output_filtering(manager: TTSManager):
    """Test content filtering on various input types."""
    print("\n=== Testing Content Filtering ===")

    test_cases = [
        "Check file at /Users/tinnguyen/Auto-Claude/apps/backend/core/client.py",
        "Visit https://github.com/AndyMik90/Auto-Claude for more info",
        "Run command: `npm install` to install dependencies",
        "Here's the code:\n```python\ndef hello():\n    print('world')\n```",
        "Use **bold** and *italic* formatting in markdown",
    ]

    for text in test_cases:
        print(f"\nOriginal: {text[:60]}...")
        filtered = manager.filter.filter(text)
        print(f"Filtered: {filtered}")


def run_demo(manager: TTSManager):
    """Run full TTS demo with all features."""
    print("\n" + "="*60)
    print("TTS INTEGRATION DEMO")
    print("="*60)

    # Show status
    status = manager.get_status()
    print(f"\nTTS Enabled: {status['enabled']}")
    print(f"Active Provider: {status['active_provider_info']}")
    print(f"Available Providers: {', '.join(status['available_providers'])}")

    if not manager.is_enabled():
        print("\nWARNING: TTS is not enabled or no providers available!")
        print("Set TTS_ENABLED=true in your .env file to enable.")
        return

    # Run tests
    test_basic_speech(manager)
    test_phase_announcements(manager)
    test_subtask_announcements(manager)
    test_qa_announcements(manager)
    test_error_handling(manager)

    # Final message
    print("\n=== Demo Complete ===")
    manager.speak("TTS integration demo complete. All tests passed.")


def main():
    parser = argparse.ArgumentParser(description="Test TTS integration")
    parser.add_argument(
        "--provider",
        choices=["auto", "piper", "macos", "system"],
        help="Force specific TTS provider"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run full demo with all features"
    )
    parser.add_argument(
        "--filter-test",
        action="store_true",
        help="Test content filtering only (no audio)"
    )

    args = parser.parse_args()

    # Create config
    config = TTSConfig.from_env()

    # Override provider if specified
    if args.provider:
        config.preferred_provider = args.provider

    # For filter test, disable TTS
    if args.filter_test:
        config.enabled = False

    # Create manager
    manager = TTSManager(config)

    # Run appropriate test
    if args.filter_test:
        test_output_filtering(manager)
    elif args.demo:
        run_demo(manager)
    else:
        # Quick test
        print("\n=== Quick TTS Test ===")
        status = manager.get_status()
        print(f"TTS Enabled: {status['enabled']}")
        print(f"Active Provider: {status['active_provider_info']}")

        if manager.is_enabled():
            print("\nSpeaking test message...")
            manager.speak("TTS integration is working correctly.")
        else:
            print("\nTTS is not enabled. Set TTS_ENABLED=true in .env to enable.")
            print("\nTesting content filtering (no audio):")
            test_output_filtering(manager)


if __name__ == "__main__":
    main()
