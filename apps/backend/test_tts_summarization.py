#!/usr/bin/env python3
"""
Comprehensive test suite for TTS summarization improvements.

Tests:
1. Adaptive mode detection (short/medium/full)
2. Cleanup function (symbols, technical terms, repetition)
3. AI summarization with Ollama
4. Fallback mechanism when Ollama unavailable
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from integrations.tts.tts_modes import (
    detect_optimal_mode,
    get_mode_config,
    analyze_metrics,
    calculate_complexity_score,
)
from integrations.tts.summarizer import (
    clean_summary,
    remove_repetitive_sentences,
    truncate_for_tts,
    summarize_for_tts,
    fallback_summarize,
)


# Test data
class TestCase:
    def __init__(self, name, input_text, expects_not_contain=None, expects_contain=None, expected_mode=None):
        self.name = name
        self.input_text = input_text
        self.expects_not_contain = expects_not_contain or []
        self.expects_contain = expects_contain or []
        self.expected_mode = expected_mode


# Cleanup function tests
CLEANUP_TESTS = [
    TestCase(
        name="Symbol removal (tilde, slash)",
        input_text="Updated the voice-config.json file in ~/.agents/ralph/ to set maxChars to 700",
        expects_not_contain=["~", "/", ".json", "dot", "slash", "tilde"],
    ),
    TestCase(
        name="Technical abbreviations",
        input_text="The API returns JSON data via HTTP to the CLI with TTS config",
        expects_not_contain=["API", "JSON", "HTTP", "CLI", "TTS"],
    ),
    TestCase(
        name="Technical references",
        input_text="Modified the file to update the function in the config",
        expects_not_contain=["the file", "the function", "the config"],
    ),
    TestCase(
        name="Repetitive sentences",
        input_text="Modified the configuration. Updated the configuration. Changed the configuration. Tests pass.",
        expects_not_contain=["Updated the configuration", "Changed the configuration"],
        expects_contain=["Modified", "Tests pass"],
    ),
    TestCase(
        name="File extensions",
        input_text="Created test.js, updated config.json, and modified index.html files",
        expects_not_contain=[".js", ".json", ".html"],
    ),
    TestCase(
        name="Path patterns",
        input_text="Files in .agents/ralph/lib/ and src/components/ were updated",
        expects_not_contain=[".agents/ralph/lib", "src/components"],
    ),
    TestCase(
        name="Multiple symbols",
        input_text="Config has keys: @name, #id, $value, %rate, ^level, &mode, *flag, `code`, ~path, /dir, |pipe",
        expects_not_contain=["@", "#", "$", "%", "^", "&", "*", "`", "~", "/", "|"],
    ),
]


# Adaptive mode detection tests
MODE_DETECTION_TESTS = [
    TestCase(
        name="Short response (under 100 chars)",
        input_text="Build completed successfully.",
        expected_mode="short",
    ),
    TestCase(
        name="Medium response (multi-paragraph)",
        input_text="""I've updated the configuration file with the new settings.

The changes include:
- Updated the voice model to use a more natural sounding voice
- Adjusted the speaking rate for better clarity
- Enabled auto-speak mode for build notifications
- Added support for multiple languages
- Configured fallback options

You can test the new settings by running the build.

Let me know if you need any further adjustments to the configuration.""",
        expected_mode="medium",
    ),
    TestCase(
        name="Full response (complex with code blocks, tables)",
        input_text="""# Implementation Plan

## Overview
This is a comprehensive implementation with multiple sections.

## User Stories
- US-001: As a user, I want to configure TTS
- US-002: As a developer, I want to test voice output
- US-003: As an admin, I want to manage voice settings

## Timeline
Week 1: Initial setup
Week 2: Core implementation
Week 3: Testing and refinement

## Technical Details

```python
def configure_tts():
    # Implementation here
    pass
```

| Feature | Status | Priority |
|---------|--------|----------|
| Voice selection | Done | High |
| Rate control | In Progress | Medium |
| Volume | Planned | Low |

This is a complex document with multiple structural elements.""",
        expected_mode="full",
    ),
]


def run_cleanup_tests():
    """Run cleanup function tests."""
    print("\n" + "=" * 60)
    print("TTS Cleanup Function Test Suite")
    print("=" * 60 + "\n")

    passed = 0
    failed = 0

    for test in CLEANUP_TESTS:
        print(f"\n📝 Test: {test.name}")
        print(f"   Input:  \"{test.input_text}\"")

        output = clean_summary(test.input_text)
        print(f"   Output: \"{output}\"")

        test_passed = True

        # Check that unwanted content is removed
        for unwanted in test.expects_not_contain:
            if unwanted in output:
                print(f"   ❌ FAIL: Still contains \"{unwanted}\"")
                test_passed = False

        # Check that wanted content is present
        for wanted in test.expects_contain:
            if wanted not in output:
                print(f"   ❌ FAIL: Missing \"{wanted}\"")
                test_passed = False

        if test_passed:
            print(f"   ✅ PASS")
            passed += 1
        else:
            failed += 1

    return passed, failed


def run_mode_detection_tests():
    """Run adaptive mode detection tests."""
    print("\n" + "=" * 60)
    print("Adaptive Mode Detection Test Suite")
    print("=" * 60 + "\n")

    passed = 0
    failed = 0

    for test in MODE_DETECTION_TESTS:
        print(f"\n📝 Test: {test.name}")
        print(f"   Expected mode: {test.expected_mode}")

        result = detect_optimal_mode(test.input_text)
        print(f"   Detected mode: {result.mode}")
        print(f"   Score: {result.score}")
        print(f"   Reason: {result.reason}")

        if result.mode == test.expected_mode:
            print(f"   ✅ PASS")
            passed += 1
        else:
            print(f"   ❌ FAIL: Expected {test.expected_mode}, got {result.mode}")
            failed += 1

    return passed, failed


def run_truncation_tests():
    """Run truncation tests."""
    print("\n" + "=" * 60)
    print("Truncation Test Suite")
    print("=" * 60 + "\n")

    passed = 0
    failed = 0

    tests = [
        ("Short text", "Hello world.", "Hello world."),
        (
            "Long text with sentence boundary",
            "First sentence is here. Second sentence is here. Third sentence is here. Fourth sentence is here.",
            150,
        ),
        (
            "Long text without good boundary",
            "This is a very long text without any sentence boundaries except at the end which makes it hard to truncate properly",
            100,
        ),
    ]

    for test_name, input_text, max_length in tests:
        if isinstance(max_length, int):
            output = truncate_for_tts(input_text, max_length)
        else:
            output = truncate_for_tts(input_text, 150)
            expected = max_length
            if output == expected:
                print(f"   ✅ PASS: {test_name}")
                passed += 1
            else:
                print(f"   ❌ FAIL: {test_name}")
                failed += 1
            continue

        print(f"\n📝 Test: {test_name}")
        print(f"   Input length: {len(input_text)}")
        print(f"   Max length: {max_length}")
        print(f"   Output length: {len(output)}")
        print(f"   Output: \"{output}\"")

        # Check that output is within limits
        if len(output) <= max_length:
            # Check that it ends with punctuation
            if output and output[-1] in '.!?':
                print(f"   ✅ PASS")
                passed += 1
            else:
                print(f"   ❌ FAIL: Doesn't end with punctuation")
                failed += 1
        else:
            print(f"   ❌ FAIL: Output too long ({len(output)} > {max_length})")
            failed += 1

    return passed, failed


def run_fallback_summarization_tests():
    """Test fallback summarization when Ollama is unavailable."""
    print("\n" + "=" * 60)
    print("Fallback Summarization Test Suite")
    print("=" * 60 + "\n")

    passed = 0
    failed = 0

    test_text = """I've updated the voice configuration in the ~/.agents/ralph/voice-config.json file.

The changes include:
- Updated the TTS provider to use Piper
- Adjusted the speaking rate to 200 WPM
- Enabled auto-speak mode for build notifications

You can test the new settings by running: python run.py --spec 001

Let me know if you need any adjustments to the voice settings."""

    mode_config = get_mode_config("medium")

    print(f"📝 Test: Fallback summarization (mode: medium)")
    print(f"   Input length: {len(test_text)} chars")

    output = fallback_summarize(test_text, mode_config)

    print(f"   Output length: {len(output)} chars")
    print(f"   Output: \"{output}\"")

    # Check criteria
    checks = [
        (len(output) <= mode_config.max_chars, f"Length within limit ({len(output)} <= {mode_config.max_chars})"),
        ("~" not in output, "No tilde symbols"),
        ("/" not in output, "No slash symbols"),
        (".json" not in output, "No file extensions"),
        ("TTS" not in output, "No technical abbreviations"),
    ]

    test_passed = True
    for check, description in checks:
        if check:
            print(f"   ✅ {description}")
        else:
            print(f"   ❌ {description}")
            test_passed = False

    if test_passed:
        passed += 1
    else:
        failed += 1

    return passed, failed


def run_full_summarization_test():
    """Test full summarization pipeline (without actually calling Ollama)."""
    print("\n" + "=" * 60)
    print("Full Summarization Pipeline Test")
    print("=" * 60 + "\n")

    test_text = """I've implemented the TTS summarization feature using Ollama for AI-powered summarization.

The implementation includes:
1. Adaptive mode detection (short/medium/full)
2. AI-powered summarization with context awareness
3. Aggressive cleanup of technical terms and symbols
4. Fallback to regex-based cleanup when Ollama is unavailable

The system now intelligently chooses the summarization length based on response complexity."""

    user_question = "What did you implement?"

    print(f"📝 Test: Full summarization pipeline")
    print(f"   User question: \"{user_question}\"")
    print(f"   Input length: {len(test_text)} chars")

    # Test with adaptive mode (will use fallback since Ollama likely unavailable)
    try:
        output, mode_used = summarize_for_tts(
            response_text=test_text,
            user_question=user_question,
            mode="adaptive",
            fallback_mode="medium"
        )

        print(f"   Mode used: {mode_used}")
        print(f"   Output length: {len(output)} chars")
        print(f"   Output: \"{output}\"")

        if output and len(output) > 0:
            print(f"   ✅ PASS: Summarization produced output")
            return 1, 0
        else:
            print(f"   ❌ FAIL: No output produced")
            return 0, 1
    except Exception as e:
        print(f"   ❌ FAIL: Exception: {e}")
        return 0, 1


def main():
    """Run all tests."""
    total_passed = 0
    total_failed = 0

    # Run cleanup tests
    passed, failed = run_cleanup_tests()
    total_passed += passed
    total_failed += failed

    # Run mode detection tests
    passed, failed = run_mode_detection_tests()
    total_passed += passed
    total_failed += failed

    # Run truncation tests
    passed, failed = run_truncation_tests()
    total_passed += passed
    total_failed += failed

    # Run fallback summarization tests
    passed, failed = run_fallback_summarization_tests()
    total_passed += passed
    total_failed += failed

    # Run full pipeline test
    passed, failed = run_full_summarization_test()
    total_passed += passed
    total_failed += failed

    # Summary
    print("\n" + "=" * 60)
    print(f"Results: {total_passed} passed, {total_failed} failed")
    print("=" * 60 + "\n")

    if total_failed > 0:
        print("❌ Some tests failed - review implementation")
        sys.exit(1)
    else:
        print("✅ All tests passed - TTS summarization is working correctly!")
        sys.exit(0)


if __name__ == "__main__":
    main()
