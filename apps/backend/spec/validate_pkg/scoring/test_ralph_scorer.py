"""
Test script for Ralph's Spec Scorer
====================================

Quick validation of the scoring system.
"""

from pathlib import Path
from ralph_scorer import RalphSpecScorer


def create_sample_spec(path: Path, quality: str = "good"):
    """Create a sample spec for testing."""
    if quality == "good":
        content = """# Feature Spec: User Authentication

## User Story
As a user of the application
I want to authenticate with email and password
So that I can securely access my account

## Acceptance Criteria
1. User can enter email and password
2. System validates credentials against database
3. Successful login redirects to dashboard
4. Failed login shows error message
5. Session expires after 1 hour of inactivity

## Technical Context
This feature modifies the following files:
- `apps/backend/auth/login.py` - Login endpoint
- `apps/frontend/src/components/LoginForm.tsx` - Login UI
- `apps/backend/models/user.py` - User model

Uses JWT tokens for session management with bcrypt password hashing.

## Implementation Guidelines

MUST:
- Hash passwords with bcrypt (cost factor 12)
- Use JWT tokens with 1-hour expiration
- Validate email format before database query

MUST NOT:
- Store passwords in plain text
- Log password values
- Allow SQL injection in email field

MAY:
- Add "Remember Me" checkbox for extended sessions
- Support OAuth providers in future

## Testing Requirements

Run these commands to validate:
```bash
pytest tests/test_auth.py
npm run test:integration
```

## Examples

Example successful login:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

Response:
```json
{
  "token": "eyJhbG...",
  "user": {
    "id": 123,
    "email": "user@example.com"
  }
}
```
"""
    elif quality == "poor":
        content = """# Feature

Add authentication stuff.

## What to do
- Add login
- Maybe password reset
- Some validation

## Notes
Should probably use JWT or something similar.
Files to change: [TBD]
"""
    else:  # medium
        content = """# User Authentication Feature

## User Story
As a user I want to log in.

## Acceptance Criteria
- Login works
- Passwords are secure
- Error handling is appropriate

## Technical Context
Needs authentication system.

## Implementation Guidelines
Follow security best practices.
"""

    path.write_text(content)


def test_scorer():
    """Test the scorer with different quality specs."""
    test_dir = Path("/tmp/ralph_scorer_test")
    test_dir.mkdir(exist_ok=True)

    # Test good spec
    print("=" * 70)
    print("Testing GOOD quality spec:")
    print("=" * 70)
    good_spec = test_dir / "good_spec.md"
    create_sample_spec(good_spec, "good")
    scorer = RalphSpecScorer(good_spec)
    result = scorer.score()
    print(result)
    print()

    # Test poor spec
    print("=" * 70)
    print("Testing POOR quality spec:")
    print("=" * 70)
    poor_spec = test_dir / "poor_spec.md"
    create_sample_spec(poor_spec, "poor")
    scorer = RalphSpecScorer(poor_spec)
    result = scorer.score()
    print(result)
    print()

    # Test medium spec
    print("=" * 70)
    print("Testing MEDIUM quality spec:")
    print("=" * 70)
    medium_spec = test_dir / "medium_spec.md"
    create_sample_spec(medium_spec, "medium")
    scorer = RalphSpecScorer(medium_spec)
    result = scorer.score()
    print(result)


if __name__ == "__main__":
    test_scorer()
