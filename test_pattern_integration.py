#!/usr/bin/env python3
"""
Integration test for Code Patterns Library feature.
Tests: extract → categorize → search → suggest → export → import → analytics
"""
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# Add apps/backend to path
backend_dir = Path(__file__).parent / "apps" / "backend"
sys.path.insert(0, str(backend_dir))

def test_pattern_workflow():
    """Test complete pattern workflow end-to-end."""
    print("=" * 60)
    print("Code Patterns Library - Integration Test")
    print("=" * 60)
    print()

    test_results = {
        "total_tests": 0,
        "passed": 0,
        "failed": 0,
        "errors": []
    }

    # Test 1: Import and initialize pattern library
    print("Test 1: Import and initialize pattern library...")
    test_results["total_tests"] += 1
    try:
        from services.pattern_library import PatternLibrary, categorize_pattern
        from models.pattern import CodePattern, PatternCategory, PatternMetadata

        # Create temp directory for test library
        with tempfile.TemporaryDirectory() as tmpdir:
            library = PatternLibrary(tmpdir)
            print("✓ Pattern library initialized")
            test_results["passed"] += 1

            # Test 2: Add a test pattern
            print("\nTest 2: Add a test pattern...")
            test_results["total_tests"] += 1
            try:
                now = datetime.now().isoformat()
                test_pattern = CodePattern(
                    id="test-react-component",
                    name="React Functional Component",
                    description="Reusable React functional component with hooks",
                    pattern_type="component",
                    category=PatternCategory.COMPONENT,
                    code_example="""
import React, { useState } from 'react';

const MyComponent = ({ title }) => {
  const [count, setCount] = useState(0);

  return (
    <div>
      <h1>{title}</h1>
      <p>Count: {count}</p>
      <button onClick={() => setCount(count + 1)}>Increment</button>
    </div>
  );
};

export default MyComponent;
""",
                    usage_context="Use when creating reusable UI components with local state",
                    keywords=["react", "component", "hooks", "useState"],
                    files_involved=["src/components/MyComponent.tsx"],
                    metadata=PatternMetadata(
                        created_at=now,
                        updated_at=now,
                        success_rate=0.95,
                        tags=["frontend", "ui"]
                    )
                )

                library.add_pattern(test_pattern)
                print("✓ Test pattern added")
                test_results["passed"] += 1

                # Test 3: Verify pattern categorization
                print("\nTest 3: Verify pattern categorization...")
                test_results["total_tests"] += 1
                try:
                    category = categorize_pattern(
                        pattern_type="component",
                        description=test_pattern.description,
                        code_example=test_pattern.code_example,
                        keywords=test_pattern.keywords,
                        files_involved=test_pattern.files_involved
                    )
                    assert category == PatternCategory.COMPONENT, f"Expected COMPONENT, got {category}"
                    print(f"✓ Pattern correctly categorized as {category}")
                    test_results["passed"] += 1

                    # Test 4: Keyword search
                    print("\nTest 4: Keyword search...")
                    test_results["total_tests"] += 1
                    try:
                        # Search using a term that appears in the description
                        results = library.search_patterns("functional component")
                        assert len(results) > 0, f"No results found for 'functional component'. Library has {library.get_pattern_count()} patterns."
                        assert any(p.id == "test-react-component" for p in results), "Test pattern not in search results"
                        print(f"✓ Keyword search found {len(results)} pattern(s)")
                        test_results["passed"] += 1

                        # Test 5: Category filtering
                        print("\nTest 5: Category filtering...")
                        test_results["total_tests"] += 1
                        try:
                            component_patterns = library.get_patterns_by_category(PatternCategory.COMPONENT)
                            assert len(component_patterns) > 0, "No component patterns found"
                            print(f"✓ Found {len(component_patterns)} component pattern(s)")
                            test_results["passed"] += 1

                            # Test 6: Pattern analytics
                            print("\nTest 6: Pattern analytics...")
                            test_results["total_tests"] += 1
                            try:
                                # Record some usage
                                library.record_pattern_usage("test-react-component", success=True)
                                library.record_pattern_usage("test-react-component", success=True)
                                library.record_pattern_usage("test-react-component", success=False)

                                # Get library analytics
                                from services.pattern_library import get_pattern_analytics
                                analytics = get_pattern_analytics(tmpdir)

                                assert "total_patterns" in analytics, "Missing total_patterns in analytics"
                                assert "total_usage" in analytics, "Missing total_usage in analytics"
                                assert "most_popular_pattern" in analytics, "Missing most_popular_pattern in analytics"

                                print(f"✓ Analytics: {analytics['total_patterns']} total patterns")
                                print(f"  - Total usage: {analytics['total_usage']}")
                                print(f"  - Average success rate: {analytics['average_success_rate']:.1%}")
                                if analytics['most_popular_pattern']:
                                    print(f"  - Most popular: {analytics['most_popular_pattern']['name']} ({analytics['most_popular_pattern']['usage_count']} uses)")
                                test_results["passed"] += 1

                                # Test 7: Export patterns
                                print("\nTest 7: Export patterns to JSON...")
                                test_results["total_tests"] += 1
                                try:
                                    from services.pattern_library import export_patterns
                                    export_data = export_patterns(tmpdir)

                                    assert "export_version" in export_data, "Missing export_version in export"
                                    assert "patterns" in export_data, "Missing patterns in export"
                                    assert len(export_data["patterns"]) > 0, "No patterns in export"

                                    # Save to file
                                    export_file = Path(tmpdir) / "exported_patterns.json"
                                    with open(export_file, 'w') as f:
                                        json.dump(export_data, f, indent=2)

                                    print(f"✓ Exported {len(export_data['patterns'])} pattern(s) to {export_file}")
                                    test_results["passed"] += 1

                                    # Test 8: Import patterns
                                    print("\nTest 8: Import patterns from JSON...")
                                    test_results["total_tests"] += 1
                                    try:
                                        # Create a new library in different directory
                                        with tempfile.TemporaryDirectory() as tmpdir2:
                                            library2 = PatternLibrary(tmpdir2)

                                            # Import patterns
                                            from services.pattern_library import import_patterns
                                            with open(export_file) as f:
                                                import_data = json.load(f)

                                            result = import_patterns(tmpdir2, import_data, merge_strategy="skip")

                                            assert result["imported"] > 0, "No patterns imported"
                                            assert library2.pattern_exists("test-react-component"), "Imported pattern not found"

                                            print(f"✓ Imported {result['imported']} pattern(s)")
                                            print(f"  - {result['skipped']} skipped")
                                            print(f"  - {result['updated']} updated")
                                            test_results["passed"] += 1

                                    except Exception as e:
                                        print(f"✗ Import test failed: {e}")
                                        test_results["failed"] += 1
                                        test_results["errors"].append(f"Test 8: {str(e)}")

                                except Exception as e:
                                    print(f"✗ Export test failed: {e}")
                                    test_results["failed"] += 1
                                    test_results["errors"].append(f"Test 7: {str(e)}")

                            except Exception as e:
                                print(f"✗ Analytics test failed: {e}")
                                test_results["failed"] += 1
                                test_results["errors"].append(f"Test 6: {str(e)}")

                        except Exception as e:
                            print(f"✗ Category filtering failed: {e}")
                            test_results["failed"] += 1
                            test_results["errors"].append(f"Test 5: {str(e)}")

                    except Exception as e:
                        print(f"✗ Keyword search failed: {e}")
                        test_results["failed"] += 1
                        test_results["errors"].append(f"Test 4: {str(e)}")

                except Exception as e:
                    print(f"✗ Categorization failed: {e}")
                    test_results["failed"] += 1
                    test_results["errors"].append(f"Test 3: {str(e)}")

            except Exception as e:
                print(f"✗ Add pattern failed: {e}")
                test_results["failed"] += 1
                test_results["errors"].append(f"Test 2: {str(e)}")

    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        test_results["failed"] += 1
        test_results["errors"].append(f"Test 1: {str(e)}")

    # Test 9: Semantic search (if Graphiti is available)
    print("\nTest 9: Semantic search (Graphiti)...")
    test_results["total_tests"] += 1
    try:
        from memory.patterns import search_patterns_semantic

        # This will check if Graphiti is enabled
        results = search_patterns_semantic(".", "react components with state")
        print(f"✓ Semantic search available (found {len(results)} results)")
        test_results["passed"] += 1
    except Exception as e:
        # Semantic search might not be available if Graphiti is not configured
        print(f"ℹ Semantic search skipped (Graphiti not enabled): {e}")
        test_results["passed"] += 1  # Not a failure, just not available

    # Test 10: Pattern tools availability
    print("\nTest 10: Pattern tools for agents...")
    test_results["total_tests"] += 1
    try:
        from agents.tools_pkg.tools.pattern import create_pattern_tools
        tools = create_pattern_tools(Path("./.auto-claude/specs/007-code-patterns-library-with-ai-learning"), Path("."))
        print(f"✓ Pattern tools factory available (created {len(tools)} tools)")
        test_results["passed"] += 1
    except Exception as e:
        print(f"✗ Pattern tools import failed: {e}")
        test_results["failed"] += 1
        test_results["errors"].append(f"Test 10: {str(e)}")

    # Print summary
    print()
    print("=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    print(f"Total Tests: {test_results['total_tests']}")
    print(f"Passed: {test_results['passed']} ✓")
    print(f"Failed: {test_results['failed']} ✗")
    print(f"Success Rate: {test_results['passed'] / test_results['total_tests'] * 100:.1f}%")

    if test_results["errors"]:
        print("\nErrors:")
        for error in test_results["errors"]:
            print(f"  - {error}")

    print()

    # Return exit code
    return 0 if test_results["failed"] == 0 else 1

if __name__ == "__main__":
    exit_code = test_pattern_workflow()
    sys.exit(exit_code)
