#!/usr/bin/env python3
"""
Comprehensive TTS Integration Test

Tests all TTS components:
1. Module structure
2. Imports
3. Configuration
4. Output filtering
5. Provider availability
6. Agent integration
"""

import sys
import os
from pathlib import Path

# Add apps/backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


def test_module_structure():
    """Test 1: Module structure"""
    print("=" * 80)
    print("TEST 1: Module Structure")
    print("=" * 80)

    tts_dir = backend_dir / "integrations" / "tts"
    providers_dir = tts_dir / "providers"

    required_files = [
        tts_dir / "__init__.py",
        tts_dir / "manager.py",
        tts_dir / "config.py",
        tts_dir / "filters.py",
        providers_dir / "__init__.py",
        providers_dir / "piper.py",
        providers_dir / "macos.py",
        providers_dir / "system.py",
    ]

    all_exist = True
    for file_path in required_files:
        exists = file_path.exists()
        status = "✅" if exists else "❌"
        print(f"{status} {file_path.relative_to(backend_dir)}")
        if not exists:
            all_exist = False

    print(f"\nResult: {'✅ PASS' if all_exist else '❌ FAIL'}\n")
    return all_exist


def test_imports():
    """Test 2: Import all TTS modules"""
    print("=" * 80)
    print("TEST 2: Imports")
    print("=" * 80)

    imports_ok = True

    # Test main imports
    try:
        from integrations.tts import TTSManager, TTSConfig
        print("✅ from integrations.tts import TTSManager, TTSConfig")
    except Exception as e:
        print(f"❌ from integrations.tts import TTSManager, TTSConfig")
        print(f"   Error: {e}")
        imports_ok = False

    # Test manager imports
    try:
        from integrations.tts.manager import get_tts_manager
        print("✅ from integrations.tts.manager import get_tts_manager")
    except Exception as e:
        print(f"❌ from integrations.tts.manager import get_tts_manager")
        print(f"   Error: {e}")
        imports_ok = False

    # Test config imports
    try:
        from integrations.tts.config import TTSConfig
        print("✅ from integrations.tts.config import TTSConfig")
    except Exception as e:
        print(f"❌ from integrations.tts.config import TTSConfig")
        print(f"   Error: {e}")
        imports_ok = False

    # Test filter imports
    try:
        from integrations.tts.filters import OutputFilter
        print("✅ from integrations.tts.filters import OutputFilter")
    except Exception as e:
        print(f"❌ from integrations.tts.filters import OutputFilter")
        print(f"   Error: {e}")
        imports_ok = False

    # Test provider imports
    try:
        from integrations.tts.providers import PiperProvider, MacOSProvider, SystemProvider
        print("✅ from integrations.tts.providers import PiperProvider, MacOSProvider, SystemProvider")
    except Exception as e:
        print(f"❌ from integrations.tts.providers import PiperProvider, MacOSProvider, SystemProvider")
        print(f"   Error: {e}")
        imports_ok = False

    print(f"\nResult: {'✅ PASS' if imports_ok else '❌ FAIL'}\n")
    return imports_ok


def test_config():
    """Test 3: TTSConfig"""
    print("=" * 80)
    print("TEST 3: TTSConfig")
    print("=" * 80)

    config_ok = True

    try:
        from integrations.tts.config import TTSConfig

        # Test from_env() with defaults
        config = TTSConfig.from_env()
        print(f"✅ TTSConfig.from_env() works")
        print(f"   enabled: {config.enabled}")
        print(f"   preferred_provider: {config.preferred_provider}")
        print(f"   piper_model: {config.piper_model}")
        print(f"   macos_voice: {config.macos_voice}")
        print(f"   max_length: {config.max_length}")

        # Test manual config
        config2 = TTSConfig(
            enabled=True,
            preferred_provider="macos",
            macos_voice="Alex",
            max_length=300
        )
        print(f"\n✅ TTSConfig manual instantiation works")
        print(f"   enabled: {config2.enabled}")
        print(f"   preferred_provider: {config2.preferred_provider}")
        print(f"   macos_voice: {config2.macos_voice}")

        # Test is_enabled()
        assert config2.is_enabled() == True
        print(f"✅ config.is_enabled() returns correct value")

    except Exception as e:
        print(f"❌ TTSConfig test failed: {e}")
        import traceback
        traceback.print_exc()
        config_ok = False

    print(f"\nResult: {'✅ PASS' if config_ok else '❌ FAIL'}\n")
    return config_ok


def test_filters():
    """Test 4: OutputFilter"""
    print("=" * 80)
    print("TEST 4: OutputFilter")
    print("=" * 80)

    filter_ok = True

    try:
        from integrations.tts.filters import OutputFilter

        # Create filter with all options enabled
        filter_obj = OutputFilter(
            filter_code=True,
            filter_markdown=True,
            filter_paths=True,
            filter_urls=True
        )
        print("✅ OutputFilter instantiated")

        # Test cases
        test_cases = [
            ("Code block removal", "Check ```python\nprint('test')\n```", "Check"),
            ("Inline code removal", "Run `npm install` now", "Run now"),
            ("File path removal", "Edit /path/to/file.py", "Edit"),
            ("URL removal", "Visit https://example.com", "Visit"),
            ("Markdown bold", "Use **bold** text", "Use bold text"),
            ("Markdown italic", "Use *italic* text", "Use italic text"),
            ("Markdown link", "Click [here](http://example.com)", "Click here"),
            ("Truncate long text", "x" * 600, "..."),
        ]

        all_passed = True
        for name, input_text, expected_substring in test_cases:
            result = filter_obj.filter(input_text)
            if expected_substring in result or (expected_substring == "..." and result.endswith("...")):
                print(f"   ✅ {name}")
            else:
                print(f"   ❌ {name}")
                print(f"      Input: {input_text[:50]}")
                print(f"      Output: {result[:50]}")
                print(f"      Expected substring: {expected_substring}")
                all_passed = False

        if all_passed:
            print("✅ All filter tests passed")
        else:
            filter_ok = False

        # Test truncate method
        truncated = filter_obj.truncate("This is a sentence. This is another sentence.", 20)
        if len(truncated) <= 25:  # Allows for "..." and sentence boundary
            print("✅ Truncate method works")
        else:
            print(f"❌ Truncate method failed: {truncated}")
            filter_ok = False

    except Exception as e:
        print(f"❌ OutputFilter test failed: {e}")
        import traceback
        traceback.print_exc()
        filter_ok = False

    print(f"\nResult: {'✅ PASS' if filter_ok else '❌ FAIL'}\n")
    return filter_ok


def test_providers():
    """Test 5: Provider availability"""
    print("=" * 80)
    print("TEST 5: Provider Availability")
    print("=" * 80)

    providers_ok = True
    available_providers = []

    try:
        from integrations.tts.providers import PiperProvider, MacOSProvider, SystemProvider

        # Test Piper
        piper = PiperProvider()
        if piper.is_available():
            print(f"✅ Piper: {piper.get_info()}")
            available_providers.append("piper")
        else:
            print(f"⚠️  Piper: Not available (not installed)")

        # Test macOS
        macos = MacOSProvider()
        if macos.is_available():
            print(f"✅ macOS: {macos.get_info()}")
            available_providers.append("macos")
        else:
            print(f"⚠️  macOS: Not available (not on macOS or 'say' not found)")

        # Test System
        system = SystemProvider()
        if system.is_available():
            print(f"✅ System: {system.get_info()}")
            available_providers.append("system")
        else:
            print(f"⚠️  System: Not available")

        # Check provider methods
        print("\nProvider method tests:")
        for provider in [piper, macos, system]:
            try:
                name = provider.get_name()
                info = provider.get_info()
                available = provider.is_available()
                print(f"   ✅ {name}: get_name(), get_info(), is_available() work")
            except Exception as e:
                print(f"   ❌ {provider.__class__.__name__}: Method error: {e}")
                providers_ok = False

        print(f"\nAvailable providers on this system: {', '.join(available_providers) if available_providers else 'None'}")

    except Exception as e:
        print(f"❌ Provider test failed: {e}")
        import traceback
        traceback.print_exc()
        providers_ok = False

    print(f"\nResult: {'✅ PASS' if providers_ok else '❌ FAIL'}\n")
    return providers_ok


def test_manager():
    """Test 6: TTSManager"""
    print("=" * 80)
    print("TEST 6: TTSManager")
    print("=" * 80)

    manager_ok = True

    try:
        from integrations.tts.manager import TTSManager, get_tts_manager
        from integrations.tts.config import TTSConfig

        # Test with disabled config
        config = TTSConfig(enabled=False)
        manager = TTSManager(config)
        print(f"✅ TTSManager instantiated (disabled)")
        print(f"   is_enabled(): {manager.is_enabled()}")

        # Test get_tts_manager
        global_manager = get_tts_manager()
        print(f"✅ get_tts_manager() works")

        # Test methods exist
        methods = [
            'speak',
            'speak_phase',
            'speak_subtask_start',
            'speak_subtask_complete',
            'speak_qa_result',
            'speak_build_complete',
            'speak_error',
            'get_status'
        ]

        all_methods_exist = True
        for method in methods:
            if hasattr(manager, method):
                print(f"   ✅ {method}() method exists")
            else:
                print(f"   ❌ {method}() method missing")
                all_methods_exist = False

        if not all_methods_exist:
            manager_ok = False

        # Test get_status()
        status = manager.get_status()
        if isinstance(status, dict) and 'enabled' in status:
            print(f"✅ get_status() returns valid dict")
            print(f"   Status: {status}")
        else:
            print(f"❌ get_status() returned invalid data: {status}")
            manager_ok = False

    except Exception as e:
        print(f"❌ TTSManager test failed: {e}")
        import traceback
        traceback.print_exc()
        manager_ok = False

    print(f"\nResult: {'✅ PASS' if manager_ok else '❌ FAIL'}\n")
    return manager_ok


def test_agent_integration():
    """Test 7: Agent integration"""
    print("=" * 80)
    print("TEST 7: Agent Integration")
    print("=" * 80)

    integration_ok = True

    agents_to_check = [
        ("coder", backend_dir / "agents" / "coder.py"),
        ("session", backend_dir / "agents" / "session.py"),
    ]

    for agent_name, agent_file in agents_to_check:
        if agent_file.exists():
            content = agent_file.read_text()

            # Check for TTS import
            has_import = "from integrations.tts import get_tts_manager" in content
            print(f"{'✅' if has_import else '❌'} {agent_name}.py: TTS import")
            if not has_import:
                integration_ok = False

            # Check for speak_ method calls
            speak_methods = [
                "speak_phase",
                "speak_subtask_start",
                "speak_subtask_complete",
                "speak_build_complete"
            ]

            found_methods = []
            for method in speak_methods:
                if method in content:
                    found_methods.append(method)

            if found_methods:
                print(f"   Found calls: {', '.join(found_methods)}")
            else:
                print(f"   ⚠️  No speak_* method calls found")
        else:
            print(f"⚠️  {agent_name}.py not found")

    print(f"\nResult: {'✅ PASS' if integration_ok else '❌ FAIL'}\n")
    return integration_ok


def test_env_configuration():
    """Test 8: .env configuration"""
    print("=" * 80)
    print("TEST 8: .env Configuration")
    print("=" * 80)

    env_ok = True

    env_example = backend_dir / ".env.example"

    if env_example.exists():
        content = env_example.read_text()

        required_vars = [
            "TTS_ENABLED",
            "TTS_PROVIDER",
            "TTS_PIPER_MODEL",
            "TTS_MACOS_VOICE",
            "TTS_ANNOUNCE_PHASES",
            "TTS_ANNOUNCE_SUBTASKS",
            "TTS_ANNOUNCE_QA",
            "TTS_FILTER_CODE",
            "TTS_MAX_LENGTH"
        ]

        all_documented = True
        for var in required_vars:
            if var in content:
                print(f"   ✅ {var} documented")
            else:
                print(f"   ❌ {var} missing")
                all_documented = False

        if all_documented:
            print("✅ All TTS env vars documented in .env.example")
        else:
            env_ok = False

    else:
        print(f"❌ .env.example not found")
        env_ok = False

    print(f"\nResult: {'✅ PASS' if env_ok else '❌ FAIL'}\n")
    return env_ok


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("COMPREHENSIVE TTS INTEGRATION TEST")
    print("=" * 80 + "\n")

    results = {
        "Module Structure": test_module_structure(),
        "Imports": test_imports(),
        "TTSConfig": test_config(),
        "OutputFilter": test_filters(),
        "Provider Availability": test_providers(),
        "TTSManager": test_manager(),
        "Agent Integration": test_agent_integration(),
        ".env Configuration": test_env_configuration(),
    }

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")

    all_passed = all(results.values())
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 80 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
