#!/usr/bin/env python3
"""
Detailed Ralph Quality Scoring Report with Improved Medium Spec
================================================================

This creates a detailed breakdown showing how each spec is scored.
"""

import tempfile
from pathlib import Path

from spec.validate_pkg.scoring.ralph_scorer import RalphSpecScorer

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
"""

# Improved medium quality spec (should score 60-79)
medium_spec = """# User Story
As a user, I want to see a task dashboard, so that I can track my work progress.

# Acceptance Criteria
1. Dashboard displays all active tasks
2. Tasks are grouped by status (pending, in progress, completed)
3. Users can filter tasks by date range
4. Each task card shows title, status, and created date

# Technical Context
Located in `/apps/frontend/src/pages/Dashboard.tsx`. Uses React 18 with TypeScript.
Fetches data from `/api/tasks` endpoint.

# Implementation Guidelines
MUST:
- Display tasks in a grid layout
- Update task list in real-time when tasks change
- Handle loading and error states

MUST NOT:
- Block the UI while fetching data
- Display tasks from other users

# Testing Requirements
```bash
npm test Dashboard.test.tsx
```
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

# Test all three specs
print("=" * 80)
print("RALPH QUALITY SCORING - DETAILED REPORT")
print("=" * 80)
print()

for spec_name, spec_content in [("GOOD", good_spec), ("MEDIUM", medium_spec), ("POOR", poor_spec)]:
    print(f"{'=' * 80}")
    print(f"{spec_name} QUALITY SPEC")
    print(f"{'=' * 80}")

    spec_path = test_dir / f"{spec_name.lower()}_spec.md"
    spec_path.write_text(spec_content)

    scorer = RalphSpecScorer(spec_path)
    score = scorer.score()

    print(score)
    print()
