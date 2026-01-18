#!/usr/bin/env python3
"""
Test script for voice lock queueing mechanism.

Demonstrates cross-process TTS coordination by launching multiple
concurrent TTS requests that queue up and play sequentially.

Usage:
    # Terminal 1:
    python apps/backend/test_voice_lock.py

    # Terminal 2 (run immediately):
    python apps/backend/test_voice_lock.py

    Expected: Both terminals queue up, speak one at a time without overlap
"""

import sys
import time
from pathlib import Path
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from integrations.tts import get_tts_manager, VoiceLock

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger(__name__)


def test_basic_lock():
    """Test basic lock acquisition and release."""
    print("\n" + "="*60)
    print("Test 1: Basic Lock Acquisition")
    print("="*60)

    lock = VoiceLock()

    print(f"Lock directory: {lock.lock_dir}")
    print(f"CLI ID: {lock.cli_id}")
    print(f"PID: {lock.pid}")

    print("\nAttempting to acquire lock...")
    result = lock.try_acquire()

    if result["success"]:
        print("✓ Lock acquired successfully")
        time.sleep(1)
        print("Releasing lock...")
        lock.release()
        print("✓ Lock released")
    else:
        print(f"✗ Failed to acquire lock: {result['error']}")
        if result.get("holder"):
            holder = result["holder"]
            print(f"  Held by: {holder['cli_id']} (PID: {holder['pid']})")


def test_lock_timeout():
    """Test lock waiting with timeout."""
    print("\n" + "="*60)
    print("Test 2: Lock Wait with Timeout")
    print("="*60)

    lock = VoiceLock()

    print("Acquiring lock for 5 seconds...")
    result = lock.wait_for_lock(timeout_seconds=15.0)

    if result["success"]:
        print("✓ Lock acquired")
        print("Holding lock for 5 seconds (try running this script in another terminal now)...")
        time.sleep(5)
        print("Releasing lock...")
        lock.release()
        print("✓ Lock released")
    else:
        print("✗ Lock acquisition failed")


def test_tts_with_lock():
    """Test TTS with voice lock coordination."""
    print("\n" + "="*60)
    print("Test 3: TTS with Voice Lock")
    print("="*60)

    manager = get_tts_manager()

    if not manager.is_enabled():
        print("✗ TTS is not enabled")
        print("  Check TTS configuration and providers")
        return

    messages = [
        "First message - this should play immediately",
        "Second message - this should queue if another instance is running",
        "Third message - final message in the queue",
    ]

    for i, msg in enumerate(messages, 1):
        print(f"\n[{i}/{len(messages)}] Speaking: {msg[:50]}...")
        success = manager.speak(msg, filter_content=False)

        if success:
            print(f"  ✓ Message {i} completed")
        else:
            print(f"  ✗ Message {i} failed")

        # Small delay between messages
        time.sleep(0.5)

    print("\n✓ All messages processed")


def test_parallel_simulation():
    """Simulate parallel TTS requests to test queueing."""
    print("\n" + "="*60)
    print("Test 4: Parallel TTS Simulation")
    print("="*60)
    print("This test simulates concurrent TTS requests.")
    print("For real parallel testing, run this script in 2+ terminals simultaneously.")
    print("="*60)

    manager = get_tts_manager()

    if not manager.is_enabled():
        print("✗ TTS is not enabled")
        return

    import multiprocessing

    def speak_worker(process_id: int):
        """Worker function for parallel TTS."""
        # Each process needs its own manager
        mgr = get_tts_manager()
        msg = f"Message from process {process_id}"
        print(f"[Process {process_id}] Speaking: {msg}")
        success = mgr.speak(msg, filter_content=False)
        return success

    # Launch 3 concurrent processes
    processes = []
    for i in range(3):
        p = multiprocessing.Process(target=speak_worker, args=(i + 1,))
        processes.append(p)
        p.start()
        time.sleep(0.1)  # Stagger starts slightly

    # Wait for all to complete
    for p in processes:
        p.join()

    print("\n✓ All parallel processes completed")


def test_context_manager():
    """Test lock as context manager."""
    print("\n" + "="*60)
    print("Test 5: Lock Context Manager")
    print("="*60)

    try:
        with VoiceLock() as lock:
            print(f"✓ Lock acquired: {lock.cli_id}")
            print("Holding for 2 seconds...")
            time.sleep(2)
            print("Exiting context (auto-release)...")
        print("✓ Lock auto-released")
    except TimeoutError as e:
        print(f"✗ Failed to acquire lock: {e}")


def main():
    """Run all tests or specific test."""
    import argparse

    parser = argparse.ArgumentParser(description="Test voice lock queueing")
    parser.add_argument(
        '--test',
        type=int,
        choices=[1, 2, 3, 4, 5],
        help='Run specific test (1-5), or all if not specified'
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Run quick tests only (1, 2, 5)'
    )

    args = parser.parse_args()

    print("\n" + "="*60)
    print("Voice Lock Queueing Test Suite")
    print("="*60)
    print("This tests cross-process TTS coordination.")
    print("Run this script in multiple terminals simultaneously to test queueing.")
    print("="*60)

    if args.test:
        # Run specific test
        tests = {
            1: test_basic_lock,
            2: test_lock_timeout,
            3: test_tts_with_lock,
            4: test_parallel_simulation,
            5: test_context_manager,
        }
        tests[args.test]()
    elif args.quick:
        # Quick tests only
        test_basic_lock()
        test_lock_timeout()
        test_context_manager()
    else:
        # Run all tests
        test_basic_lock()
        test_lock_timeout()
        test_context_manager()

        # Ask before TTS tests
        print("\n" + "="*60)
        response = input("Run TTS tests with audio output? [y/N]: ")
        if response.lower() == 'y':
            test_tts_with_lock()

            response = input("\nRun parallel TTS test? [y/N]: ")
            if response.lower() == 'y':
                test_parallel_simulation()
        else:
            print("Skipping TTS tests")

    print("\n" + "="*60)
    print("Test suite complete")
    print("="*60)


if __name__ == '__main__':
    main()
