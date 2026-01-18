#!/usr/bin/env python3
"""
Test script for documentation generation.
Tests the parsers and formatters without requiring full CLI setup.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from documentation.parsers import PythonParser, TypeScriptParser
from documentation.formatters import DocstringFormatter, JSDocFormatter


def test_python_parser():
    """Test Python parser on sample file."""
    print("=" * 80)
    print("TESTING PYTHON PARSER")
    print("=" * 80)

    formatter = DocstringFormatter()

    # Read sample Python file
    sample_file = Path("test-docs-samples/calculator.py")
    if not sample_file.exists():
        print(f"❌ Sample file not found: {sample_file}")
        return False

    # Initialize parser with file path
    parser = PythonParser(sample_file)

    # Parse the file
    parsed = parser.parse()
    functions = parsed["functions"]
    classes = parsed["classes"]

    print(f"\n✓ Found {len(functions)} functions:\n")

    for func in functions:
        print(f"Function: {func.name}")
        print(f"  Line: {func.line_number}")
        print(f"  Parameters: {func.params}")
        print(f"  Return Type: {func.return_type}")
        print(f"  Has Docstring: {bool(func.docstring)}")

        if not func.docstring:
            # Generate docstring
            param_descriptions = {p.split(":")[0].strip(): f"The {p.split(':')[0].strip()} parameter" for p in func.params}
            docstring = formatter.format_function_docstring(
                func_info=func,
                description=f"Calculate {func.name} of a number.",
                param_descriptions=param_descriptions,
                return_description="The result of the calculation",
                raises={"ValueError": "If input is invalid"}
            )
            print(f"\n  Generated Docstring:\n{docstring}\n")
        print()

    print(f"\n✓ Found {len(classes)} classes:\n")

    for cls in classes:
        print(f"Class: {cls.name}")
        print(f"  Line: {cls.line_number}")
        print(f"  Methods: {len(cls.methods)}")
        print(f"  Has Docstring: {bool(cls.docstring)}")

        if not cls.docstring:
            # Generate docstring
            docstring = formatter.format_class_docstring(
                class_info=cls,
                description=f"A class for {cls.name} operations.",
                attributes={"precision": "Decimal precision for calculations"}
            )
            print(f"\n  Generated Docstring:\n{docstring}\n")
        print()

    return True


def test_typescript_parser():
    """Test TypeScript parser on sample file."""
    print("\n" + "=" * 80)
    print("TESTING TYPESCRIPT PARSER")
    print("=" * 80)

    formatter = JSDocFormatter()

    # Read sample TypeScript file
    sample_file = Path("test-docs-samples/user-manager.ts")
    if not sample_file.exists():
        print(f"❌ Sample file not found: {sample_file}")
        return False

    # Initialize parser with file path
    parser = TypeScriptParser(sample_file)

    # Parse the file
    parsed = parser.parse()
    functions = parsed["functions"]
    classes = parsed["classes"]
    interfaces = parsed["interfaces"]

    print(f"\n✓ Found {len(functions)} functions:\n")

    for func in functions:
        print(f"Function: {func.name}")
        print(f"  Line: {func.line_number}")
        print(f"  Parameters: {func.params}")
        print(f"  Return Type: {func.return_type}")
        print(f"  Has JSDoc: {bool(func.docstring)}")

        if not func.docstring:
            # Generate JSDoc
            param_descriptions = {p.split(":")[0].strip(): f"The {p.split(':')[0].strip()} parameter" for p in func.params if p}
            jsdoc = formatter.format_function_jsdoc(
                func_info=func,
                description=f"Performs {func.name} operation.",
                param_descriptions=param_descriptions,
                return_description="The operation result"
            )
            print(f"\n  Generated JSDoc:\n{jsdoc}\n")
        print()

    print(f"\n✓ Found {len(classes)} classes:\n")

    for cls in classes:
        print(f"Class: {cls.name}")
        print(f"  Line: {cls.line_number}")
        print(f"  Methods: {len(cls.methods)}")
        print(f"  Has JSDoc: {bool(cls.docstring)}")

        if not cls.docstring:
            # Generate JSDoc
            jsdoc = formatter.format_class_jsdoc(
                class_info=cls,
                description=f"A class for {cls.name} management."
            )
            print(f"\n  Generated JSDoc:\n{jsdoc}\n")
        print()

    print(f"\n✓ Found {len(interfaces)} interfaces:\n")

    for interface in interfaces:
        print(f"Interface: {interface['name']}")
        print(f"  Line: {interface['line_number']}")
        print()

    return True


def main():
    """Run all tests."""
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "DOCUMENTATION GENERATION TEST" + " " * 29 + "║")
    print("╚" + "=" * 78 + "╝\n")

    success = True

    try:
        # Test Python parser
        if not test_python_parser():
            success = False

        # Test TypeScript parser
        if not test_typescript_parser():
            success = False

        # Summary
        print("\n" + "=" * 80)
        if success:
            print("✅ ALL TESTS PASSED")
        else:
            print("❌ SOME TESTS FAILED")
        print("=" * 80 + "\n")

        return 0 if success else 1

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
