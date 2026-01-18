#!/usr/bin/env python3
"""
Comprehensive Ralph Quality Scoring System Test Suite
======================================================

Tests all aspects of the quality scoring system:
1. Imports and class definitions
2. Scoring with sample specs (good, medium, poor)
3. Vague language detection
4. Placeholder detection
5. Validation integration
6. CLI integration
"""

import json
import sys
import tempfile
from pathlib import Path

# Test 1: Import all classes
print("=" * 80)
print("TEST 1: RalphSpecScorer Imports")
print("=" * 80)

try:
    from spec.validate_pkg.scoring.ralph_scorer import (
        QualityIssue,
        QualityScore,
        RalphSpecScorer,
        ScoreBreakdown,
    )
    print("✅ Successfully imported RalphSpecScorer")
    print("✅ Successfully imported QualityScore")
    print("✅ Successfully imported ScoreBreakdown")
    print("✅ Successfully imported QualityIssue")
    print()
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Test scoring with sample specs
print("=" * 80)
print("TEST 2: Scoring with Sample Specs")
print("=" * 80)

# Create temporary directory for test specs
test_dir = Path(tempfile.mkdtemp())

# Good quality spec (should score 80+)
good_spec = """# User Story
As a developer, I want an automated testing framework, so that I can ensure code quality before deployment.

# Acceptance Criteria
1. Given a valid test suite, when I run the test command, then all tests execute successfully
2. Given a failing test, when I run the test suite, then the system displays the failure with stack trace
3. Given test results, when tests complete, then a JSON report is generated in ./test-results/
4. Verify that test execution time is under 5 seconds for the sample suite

# Technical Context
The testing framework will integrate with the existing Python backend located in `/apps/backend/`.
Key files to modify:
- `/apps/backend/tests/test_runner.py` - Main test execution engine
- `/apps/backend/core/test_config.py` - Test configuration and settings
- `/apps/backend/tests/fixtures.py` - Shared test fixtures

The framework uses pytest 8.0+ with coverage reporting via pytest-cov.

# Implementation Guidelines
MUST:
- Use pytest as the testing framework
- Generate coverage reports above 80%
- Run tests in isolated environments

MUST NOT:
- Modify production code during test execution
- Share state between test cases
- Skip test cleanup

MAY:
- Use parallel test execution for performance
- Cache test fixtures for faster runs
- Generate HTML coverage reports

# Testing Requirements
Run the test suite:
```bash
cd apps/backend
pytest tests/ -v --cov=core --cov-report=html
```

Verify coverage:
```bash
coverage report --fail-under=80
```

# Examples
Example test execution output:
```
test_authentication.py::test_login_success ✓
test_authentication.py::test_login_failure ✓
Coverage: 85%
```

Example JSON report structure:
```json
{
  "total_tests": 42,
  "passed": 40,
  "failed": 2,
  "coverage": 85.2
}
```
"""

# Medium quality spec (should score 60-79)
medium_spec = """# User Story
As a user, I want to see a dashboard.

# Acceptance Criteria
- Dashboard should display relevant information
- It should be responsive
- Users can customize the layout if needed

# Technical Context
Located in the frontend somewhere. Uses React or something similar.

# Implementation Guidelines
Make sure the dashboard works properly and looks good.
Try to follow best practices where appropriate.

# Testing Requirements
Test the dashboard to ensure it works as expected.
"""

# Poor quality spec (should score <60)
poor_spec = """# User Story
Add a feature

# Acceptance Criteria
TODO: Define criteria

# Technical Context
[Add technical details here]

# Implementation Guidelines
TBD

# Testing Requirements
...
"""

# Test good spec
good_spec_path = test_dir / "good_spec.md"
good_spec_path.write_text(good_spec)

scorer = RalphSpecScorer(good_spec_path)
good_score = scorer.score()

print(f"GOOD SPEC:")
print(f"  Score: {good_score.score:.1f}/100")
print(f"  Grade: {good_score.grade}")
print(f"  Structure: {good_score.breakdown.structure_score:.1f}/20")
print(f"  Boundaries: {good_score.breakdown.boundaries_score:.1f}/20")
print(f"  Story Quality: {good_score.breakdown.story_quality_score:.1f}/25")
print(f"  Concreteness: {good_score.breakdown.concreteness_score:.1f}/20")
print(f"  Context: {good_score.breakdown.context_score:.1f}/15")
print(f"  Issues: {len(good_score.issues)}")

good_score_pass = good_score.score >= 80
if good_score_pass:
    print("✅ Good spec scored 80+ as expected")
else:
    print(f"❌ Good spec scored {good_score.score:.1f}, expected 80+")

print()

# Test medium spec
medium_spec_path = test_dir / "medium_spec.md"
medium_spec_path.write_text(medium_spec)

scorer = RalphSpecScorer(medium_spec_path)
medium_score = scorer.score()

print(f"MEDIUM SPEC:")
print(f"  Score: {medium_score.score:.1f}/100")
print(f"  Grade: {medium_score.grade}")
print(f"  Structure: {medium_score.breakdown.structure_score:.1f}/20")
print(f"  Boundaries: {medium_score.breakdown.boundaries_score:.1f}/20")
print(f"  Story Quality: {medium_score.breakdown.story_quality_score:.1f}/25")
print(f"  Concreteness: {medium_score.breakdown.concreteness_score:.1f}/20")
print(f"  Context: {medium_score.breakdown.context_score:.1f}/15")
print(f"  Issues: {len(medium_score.issues)}")

medium_score_pass = 60 <= medium_score.score < 80
if medium_score_pass:
    print("✅ Medium spec scored 60-79 as expected")
else:
    print(f"❌ Medium spec scored {medium_score.score:.1f}, expected 60-79")

print()

# Test poor spec
poor_spec_path = test_dir / "poor_spec.md"
poor_spec_path.write_text(poor_spec)

scorer = RalphSpecScorer(poor_spec_path)
poor_score = scorer.score()

print(f"POOR SPEC:")
print(f"  Score: {poor_score.score:.1f}/100")
print(f"  Grade: {poor_score.grade}")
print(f"  Structure: {poor_score.breakdown.structure_score:.1f}/20")
print(f"  Boundaries: {poor_score.breakdown.boundaries_score:.1f}/20")
print(f"  Story Quality: {poor_score.breakdown.story_quality_score:.1f}/25")
print(f"  Concreteness: {poor_score.breakdown.concreteness_score:.1f}/20")
print(f"  Context: {poor_score.breakdown.context_score:.1f}/15")
print(f"  Issues: {len(poor_score.issues)}")

poor_score_pass = poor_score.score < 60
if poor_score_pass:
    print("✅ Poor spec scored <60 as expected")
else:
    print(f"❌ Poor spec scored {poor_score.score:.1f}, expected <60")

print()

# Test 3: Grade calculation
print("=" * 80)
print("TEST 3: Grade Calculation")
print("=" * 80)

grade_tests = [
    (95, "A"),
    (85, "B"),
    (75, "C"),
    (65, "D"),
    (55, "F"),
]

all_grades_correct = True
for score, expected_grade in grade_tests:
    calculated_grade = scorer._calculate_grade(score)
    if calculated_grade == expected_grade:
        print(f"✅ Score {score} -> Grade {calculated_grade} (expected {expected_grade})")
    else:
        print(f"❌ Score {score} -> Grade {calculated_grade} (expected {expected_grade})")
        all_grades_correct = False

if all_grades_correct:
    print("✅ All grade calculations correct")
else:
    print("❌ Some grade calculations failed")

print()

# Test 4: Vague language detection
print("=" * 80)
print("TEST 4: Vague Language Detection")
print("=" * 80)

vague_spec = """# User Story
As a user, I want a feature that should work properly.

# Acceptance Criteria
- The system should handle requests appropriately
- Users might be able to customize settings as needed
- Performance should be good and response time optimal

# Technical Context
The feature could be implemented in various ways.
Try to follow best practices where suitable.
Several components may need updates.

# Implementation Guidelines
Consider using modern frameworks.
The implementation should be done correctly.

# Testing Requirements
Test as needed to ensure everything works as expected.
"""

vague_spec_path = test_dir / "vague_spec.md"
vague_spec_path.write_text(vague_spec)

scorer = RalphSpecScorer(vague_spec_path)
vague_score = scorer.score()

# Find concreteness issues
concreteness_issues = [i for i in vague_score.issues if i.category == "Concreteness"]
vague_language_issue = None
for issue in concreteness_issues:
    if "vague language" in issue.description.lower():
        vague_language_issue = issue
        break

vague_detected = vague_language_issue is not None
vague_penalized = vague_score.breakdown.concreteness_score < 20

if vague_language_issue:
    print(f"✅ Detected vague language: {vague_language_issue.description}")
    print(f"   Severity: {vague_language_issue.severity}")

    # Check if concreteness score is penalized
    if vague_penalized:
        print(f"✅ Concreteness score penalized: {vague_score.breakdown.concreteness_score:.1f}/20")
    else:
        print(f"❌ Concreteness score not penalized enough: {vague_score.breakdown.concreteness_score:.1f}/20")
else:
    print("❌ Failed to detect vague language")

# Count vague terms manually
vague_terms = ["should", "properly", "appropriately", "might", "good", "optimal",
               "could", "various", "as needed", "suitable", "several", "may",
               "consider", "correctly", "as expected"]

found_terms = []
for term in vague_terms:
    if term in vague_spec.lower():
        found_terms.append(term)

print(f"\nVague terms found: {len(found_terms)}")
print(f"Terms: {', '.join(found_terms)}")

print()

# Test 5: Placeholder detection
print("=" * 80)
print("TEST 5: Placeholder Detection")
print("=" * 80)

placeholder_spec = """# User Story
TODO: Write user story

# Acceptance Criteria
- TBD
- [Add criteria here]
- <Define acceptance criteria>

# Technical Context
Implementation details: {...}

# Implementation Guidelines
FIXME: Add guidelines

# Testing Requirements
XXX: Need to define test cases
... more to come
"""

placeholder_spec_path = test_dir / "placeholder_spec.md"
placeholder_spec_path.write_text(placeholder_spec)

scorer = RalphSpecScorer(placeholder_spec_path)
placeholder_score = scorer.score()

# Find placeholder issues
placeholder_issues = [i for i in placeholder_score.issues if "placeholder" in i.description.lower()]

placeholder_detected = len(placeholder_issues) > 0
placeholder_penalized = placeholder_score.breakdown.concreteness_score < 20

if placeholder_issues:
    issue = placeholder_issues[0]
    print(f"✅ Detected placeholders: {issue.description}")
    print(f"   Severity: {issue.severity}")

    # Check if concreteness score is penalized
    if placeholder_penalized:
        print(f"✅ Concreteness score penalized: {placeholder_score.breakdown.concreteness_score:.1f}/20")
    else:
        print(f"❌ Concreteness score not penalized enough: {placeholder_score.breakdown.concreteness_score:.1f}/20")
else:
    print("❌ Failed to detect placeholders")

# Count placeholders manually
placeholders = ["TODO", "TBD", "[Add criteria here]", "<Define acceptance criteria>",
                "{...}", "FIXME", "XXX", "..."]

found_placeholders = []
for placeholder in placeholders:
    if placeholder in placeholder_spec:
        found_placeholders.append(placeholder)

print(f"\nPlaceholders found: {len(found_placeholders)}")
print(f"Placeholders: {', '.join(found_placeholders)}")

print()

# Test 6: Validation integration
print("=" * 80)
print("TEST 6: Validation Integration")
print("=" * 80)

try:
    from spec.validate_pkg.validators.quality_validator import QualityValidator
    from spec.validate_pkg.spec_validator import SpecValidator

    print("✅ Successfully imported QualityValidator")
    print("✅ Successfully imported SpecValidator")

    # Create a test spec directory
    spec_test_dir = test_dir / "test_spec_001"
    spec_test_dir.mkdir()

    # Copy good spec
    (spec_test_dir / "spec.md").write_text(good_spec)

    # Test QualityValidator
    quality_validator = QualityValidator(spec_test_dir, min_score=70.0)
    result = quality_validator.validate()

    print(f"\nQualityValidator result:")
    print(f"  Valid: {result.valid}")
    print(f"  Checkpoint: {result.checkpoint}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Warnings: {len(result.warnings)}")

    # Check if quality_score.json was created
    quality_file = spec_test_dir / "quality_score.json"
    quality_file_exists = quality_file.exists()

    if quality_file_exists:
        print(f"✅ quality_score.json created")

        # Verify JSON structure
        quality_data = json.loads(quality_file.read_text())
        required_keys = ["score", "grade", "breakdown", "issues", "recommendations"]

        missing_keys = [key for key in required_keys if key not in quality_data]
        json_structure_valid = not missing_keys

        if json_structure_valid:
            print(f"✅ quality_score.json has all required keys")
            print(f"   Score: {quality_data['score']:.1f}")
            print(f"   Grade: {quality_data['grade']}")
        else:
            print(f"❌ quality_score.json missing keys: {', '.join(missing_keys)}")
    else:
        print(f"❌ quality_score.json not created")
        json_structure_valid = False

    # Test SpecValidator integration
    spec_validator = SpecValidator(spec_test_dir, min_quality_score=70.0)

    # Check that quality validator is initialized
    has_quality_validator = hasattr(spec_validator, '_quality_validator')
    if has_quality_validator:
        print(f"✅ SpecValidator has _quality_validator attribute")
    else:
        print(f"❌ SpecValidator missing _quality_validator attribute")

    # Check that validate_quality method exists
    has_validate_quality = hasattr(spec_validator, 'validate_quality')
    if has_validate_quality:
        print(f"✅ SpecValidator has validate_quality method")
    else:
        print(f"❌ SpecValidator missing validate_quality method")

except ImportError as e:
    print(f"❌ Import failed: {e}")
    quality_file_exists = False
    json_structure_valid = False
    has_quality_validator = False
    has_validate_quality = False
except Exception as e:
    print(f"❌ Validation integration test failed: {e}")
    quality_file_exists = False
    json_structure_valid = False
    has_quality_validator = False
    has_validate_quality = False

print()

# Test 7: CLI integration
print("=" * 80)
print("TEST 7: validate_spec.py CLI Integration")
print("=" * 80)

cli_script = Path("spec/validate_spec.py")

cli_exists = cli_script.exists()

if cli_exists:
    print(f"✅ validate_spec.py exists")

    # Read the file to check for quality checkpoint
    cli_content = cli_script.read_text()

    has_quality_checkpoint = '"quality"' in cli_content
    if has_quality_checkpoint:
        print(f"✅ 'quality' checkpoint available in CLI")
    else:
        print(f"❌ 'quality' checkpoint not found in CLI")

    has_min_score_flag = '--min-score' in cli_content
    if has_min_score_flag:
        print(f"✅ '--min-score' flag exists")
    else:
        print(f"❌ '--min-score' flag not found")

    # Check help text mentions quality
    has_quality_help = 'quality' in cli_content.lower()
    if has_quality_help:
        print(f"✅ Help text mentions quality checkpoint")
    else:
        print(f"❌ Help text missing quality checkpoint info")

    # Check argparse configuration
    has_min_quality_param = 'min_quality_score' in cli_content
    if has_min_quality_param:
        print(f"✅ min_quality_score parameter found")
    else:
        print(f"❌ min_quality_score parameter not found")

else:
    print(f"❌ validate_spec.py not found")
    has_quality_checkpoint = False
    has_min_score_flag = False
    has_quality_help = False
    has_min_quality_param = False

print()

# Test 8: Performance test
print("=" * 80)
print("TEST 8: Performance Notes")
print("=" * 80)

import time

# Test scoring performance on a large spec
large_spec = good_spec * 10  # Repeat the spec 10 times
large_spec_path = test_dir / "large_spec.md"
large_spec_path.write_text(large_spec)

start_time = time.time()
scorer = RalphSpecScorer(large_spec_path)
score = scorer.score()
end_time = time.time()

execution_time = (end_time - start_time) * 1000  # Convert to milliseconds

print(f"Large spec scoring performance:")
print(f"  File size: {len(large_spec)} characters")
print(f"  Execution time: {execution_time:.2f}ms")

performance_good = execution_time < 500
performance_acceptable = execution_time < 1000

if performance_good:
    print(f"✅ Performance is good (<500ms)")
elif performance_acceptable:
    print(f"⚠️  Performance is acceptable (<1000ms)")
else:
    print(f"❌ Performance is slow (>{execution_time:.0f}ms)")

print()

# Summary
print("=" * 80)
print("TEST SUMMARY")
print("=" * 80)

test_results = [
    ("Import RalphSpecScorer", True),
    ("Import QualityScore", True),
    ("Import ScoreBreakdown", True),
    ("Import QualityIssue", True),
    ("Good spec scores 80+", good_score_pass),
    ("Medium spec scores 60-79", medium_score_pass),
    ("Poor spec scores <60", poor_score_pass),
    ("Grade calculation correct", all_grades_correct),
    ("Vague language detection", vague_detected),
    ("Vague language penalization", vague_penalized),
    ("Placeholder detection", placeholder_detected),
    ("Placeholder penalization", placeholder_penalized),
    ("QualityValidator integration", quality_file_exists),
    ("quality_score.json structure", json_structure_valid),
    ("CLI quality checkpoint", has_quality_checkpoint),
    ("CLI min-score flag", has_min_score_flag),
    ("Performance acceptable", performance_acceptable),
]

passed = sum(1 for _, result in test_results if result)
total = len(test_results)

for test_name, result in test_results:
    status = "✅" if result else "❌"
    print(f"{status} {test_name}")

print()
print(f"TOTAL: {passed}/{total} tests passed")

if passed == total:
    print("🎉 ALL TESTS PASSED!")
    sys.exit(0)
else:
    print(f"⚠️  {total - passed} tests failed")
    sys.exit(1)
