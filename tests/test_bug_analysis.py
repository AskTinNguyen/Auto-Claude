#!/usr/bin/env python3
"""
Tests for Bug Analysis Module
=============================

Comprehensive unit tests for the bug_analysis module including:
- models.py: BugCategory, BugData, CategorizedBug, BugPattern
- scanner.py: Git history scanning, parsing, issue extraction
- categorizer.py: Prompt building, response parsing, API integration

Note: This test module mocks external dependencies (git commands, API calls,
file I/O) to ensure isolated, fast tests.
"""

import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio

import pytest

# =============================================================================
# MOCK SETUP - Must happen before ANY imports from auto-claude
# =============================================================================

# Store original modules for cleanup
_original_modules = {}
_mocked_module_names = [
    'claude_agent_sdk',
    'claude_code_sdk',
    'core.simple_client',
]

for name in _mocked_module_names:
    if name in sys.modules:
        _original_modules[name] = sys.modules[name]

# Mock claude_agent_sdk
mock_sdk = MagicMock()
mock_sdk.ClaudeSDKClient = MagicMock()
mock_sdk.ClaudeAgentOptions = MagicMock()
mock_sdk.ClaudeCodeOptions = MagicMock()
sys.modules['claude_agent_sdk'] = mock_sdk

# Mock claude_code_sdk
mock_code_sdk = MagicMock()
sys.modules['claude_code_sdk'] = mock_code_sdk
sys.modules['claude_code_sdk.types'] = MagicMock()

# Now we can import the bug_analysis modules
from bug_analysis.models import BugCategory, BugData, CategorizedBug, BugPattern
from bug_analysis.scanner import (
    scan_git_history,
    _parse_git_log_output,
    extract_related_issues,
    get_github_commit_url,
    get_files_changed,
    get_diff,
    create_bug_id,
    create_bug_data,
    get_github_repo_info,
    get_processed_commits,
    mark_commit_as_processed,
    create_bug_wikipedia_directories,
)
from bug_analysis.categorizer import (
    build_categorization_prompt,
    parse_categorization_response,
    categorize_bug_with_haiku,
    get_uncategorized_bugs,
    BUG_CATEGORIES,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def sample_bug_data():
    """Create sample BugData for testing"""
    return BugData(
        id="bug-test1234",
        commit_sha="test1234567890abcdef",
        commit_message="fix: resolve login issue",
        author_name="Test User",
        author_email="test@example.com",
        date_fixed=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        files_changed=["src/auth/login.py", "tests/test_login.py"],
        diff="- old_code()\n+ new_code()",
        related_issues=["#123", "PRD-45"],
        github_url="https://github.com/test/repo/commit/test1234",
        error_message="KeyError: 'user_id'",
        scanned_at=datetime(2024, 1, 15, 11, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def sample_categorized_bug(sample_bug_data):
    """Create sample CategorizedBug for testing"""
    return CategorizedBug.from_bug_data(
        sample_bug_data,
        primary_category=BugCategory.LOGIC_ERROR,
        secondary_categories=[BugCategory.USER_INPUT_VALIDATION],
        severity="high",
        reasoning="Login logic failed to handle missing user_id",
        prevention_tips="Add input validation for required fields",
    )


@pytest.fixture
def sample_commit_dict():
    """Create sample commit dictionary from git log"""
    return {
        "sha": "abc123def456789",
        "author_name": "Jane Developer",
        "author_email": "jane@example.com",
        "date": "2024-01-15 10:30:00 -0500",
        "message": "fix: handle edge case in parser",
        "body": "Fixed bug where parser failed on empty input.\n\nError: IndexError: list index out of range\n\nFixes #456",
    }


@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project directory"""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    return project_dir


@pytest.fixture
def temp_bug_wikipedia_dir(tmp_path):
    """Create a temporary bug-wikipedia directory"""
    bug_dir = tmp_path / "bug-wikipedia"
    bug_dir.mkdir()
    return bug_dir


# =============================================================================
# TESTS: models.py - BugCategory
# =============================================================================


class TestBugCategory:
    """Tests for BugCategory enum"""

    def test_bug_category_enum_values(self):
        """Test BugCategory enum has expected values"""
        assert BugCategory.LOGIC_ERROR.value == "logic-error"
        assert BugCategory.RACE_CONDITION.value == "race-condition"
        assert BugCategory.REQUIREMENTS_MISUNDERSTANDING.value == "requirements-misunderstanding"
        assert BugCategory.INTEGRATION_ISSUE.value == "integration-issue"
        assert BugCategory.ENVIRONMENT_SPECIFIC.value == "environment-specific"
        assert BugCategory.DEPENDENCY_ISSUE.value == "dependency-issue"
        assert BugCategory.PERFORMANCE_DEGRADATION.value == "performance-degradation"
        assert BugCategory.SECURITY_VULNERABILITY.value == "security-vulnerability"
        assert BugCategory.DATA_CORRUPTION.value == "data-corruption"
        assert BugCategory.USER_INPUT_VALIDATION.value == "user-input-validation"

    def test_bug_category_str(self):
        """Test BugCategory __str__ method"""
        assert str(BugCategory.LOGIC_ERROR) == "logic-error"
        assert str(BugCategory.RACE_CONDITION) == "race-condition"

    def test_bug_category_from_string_valid(self):
        """Test BugCategory.from_string with valid values"""
        assert BugCategory.from_string("logic-error") == BugCategory.LOGIC_ERROR
        assert BugCategory.from_string("race-condition") == BugCategory.RACE_CONDITION
        assert BugCategory.from_string("security-vulnerability") == BugCategory.SECURITY_VULNERABILITY

    def test_bug_category_from_string_invalid(self):
        """Test BugCategory.from_string with invalid value"""
        with pytest.raises(ValueError, match="Unknown bug category"):
            BugCategory.from_string("invalid-category")

    def test_bug_category_iteration(self):
        """Test iterating over BugCategory enum"""
        categories = list(BugCategory)
        assert len(categories) == 10
        assert BugCategory.LOGIC_ERROR in categories


# =============================================================================
# TESTS: models.py - BugData
# =============================================================================


class TestBugData:
    """Tests for BugData dataclass"""

    def test_bug_data_creation(self, sample_bug_data):
        """Test BugData creation with valid data"""
        assert sample_bug_data.id == "bug-test1234"
        assert sample_bug_data.commit_sha == "test1234567890abcdef"
        assert sample_bug_data.commit_message == "fix: resolve login issue"
        assert sample_bug_data.author_name == "Test User"
        assert len(sample_bug_data.files_changed) == 2

    def test_bug_data_to_dict(self, sample_bug_data):
        """Test BugData to_dict serialization"""
        data_dict = sample_bug_data.to_dict()

        assert data_dict["id"] == "bug-test1234"
        assert data_dict["commit_sha"] == "test1234567890abcdef"
        assert data_dict["author"]["name"] == "Test User"
        assert data_dict["author"]["email"] == "test@example.com"
        assert "date_fixed" in data_dict
        assert isinstance(data_dict["date_fixed"], str)  # ISO format string
        assert data_dict["files_changed"] == ["src/auth/login.py", "tests/test_login.py"]
        assert data_dict["related_issues"] == ["#123", "PRD-45"]

    def test_bug_data_from_dict(self, sample_bug_data):
        """Test BugData from_dict deserialization"""
        data_dict = sample_bug_data.to_dict()
        restored = BugData.from_dict(data_dict)

        assert restored.id == sample_bug_data.id
        assert restored.commit_sha == sample_bug_data.commit_sha
        assert restored.author_name == sample_bug_data.author_name
        assert restored.author_email == sample_bug_data.author_email
        assert restored.files_changed == sample_bug_data.files_changed
        assert restored.related_issues == sample_bug_data.related_issues

    def test_bug_data_from_dict_handles_missing_fields(self):
        """Test BugData from_dict handles missing optional fields"""
        minimal_dict = {
            "id": "bug-min",
            "commit_sha": "sha123",
            "commit_message": "fix: minimal",
            "author": {"name": "Test", "email": "test@test.com"},
        }

        bug = BugData.from_dict(minimal_dict)

        assert bug.id == "bug-min"
        assert bug.files_changed == []
        assert bug.diff == ""
        assert bug.related_issues == []
        assert bug.github_url is None

    def test_bug_data_roundtrip_serialization(self, sample_bug_data):
        """Test BugData survives JSON roundtrip"""
        data_dict = sample_bug_data.to_dict()
        json_str = json.dumps(data_dict)
        restored_dict = json.loads(json_str)
        restored_bug = BugData.from_dict(restored_dict)

        assert restored_bug.id == sample_bug_data.id
        assert restored_bug.commit_message == sample_bug_data.commit_message

    def test_bug_data_save_and_load(self, sample_bug_data, tmp_path):
        """Test BugData save and load to/from file"""
        output_dir = tmp_path / "bugs"
        output_dir.mkdir()

        sample_bug_data.save(output_dir)

        # Verify file was created
        output_file = output_dir / f"{sample_bug_data.id}.json"
        assert output_file.exists()

        # Load and verify
        loaded = BugData.load(output_file)
        assert loaded.id == sample_bug_data.id
        assert loaded.commit_sha == sample_bug_data.commit_sha


# =============================================================================
# TESTS: models.py - CategorizedBug
# =============================================================================


class TestCategorizedBug:
    """Tests for CategorizedBug dataclass"""

    def test_categorized_bug_creation(self, sample_categorized_bug):
        """Test CategorizedBug creation from BugData"""
        assert sample_categorized_bug.primary_category == BugCategory.LOGIC_ERROR
        assert BugCategory.USER_INPUT_VALIDATION in sample_categorized_bug.secondary_categories
        assert sample_categorized_bug.severity == "high"
        assert sample_categorized_bug.reasoning == "Login logic failed to handle missing user_id"

    def test_categorized_bug_from_bug_data(self, sample_bug_data):
        """Test CategorizedBug.from_bug_data factory method"""
        categorized = CategorizedBug.from_bug_data(
            sample_bug_data,
            primary_category=BugCategory.RACE_CONDITION,
            secondary_categories=[BugCategory.INTEGRATION_ISSUE],
            severity="critical",
            reasoning="Race condition in async handler",
            prevention_tips="Use proper locking",
        )

        # Should inherit all BugData fields
        assert categorized.id == sample_bug_data.id
        assert categorized.commit_sha == sample_bug_data.commit_sha
        assert categorized.files_changed == sample_bug_data.files_changed

        # Plus categorization fields
        assert categorized.primary_category == BugCategory.RACE_CONDITION
        assert categorized.severity == "critical"
        assert categorized.categorized_at is not None

    def test_categorized_bug_to_dict(self, sample_categorized_bug):
        """Test CategorizedBug to_dict includes categorization fields"""
        data_dict = sample_categorized_bug.to_dict()

        assert data_dict["primary_category"] == "logic-error"
        assert "user-input-validation" in data_dict["secondary_categories"]
        assert data_dict["severity"] == "high"
        assert data_dict["reasoning"] == "Login logic failed to handle missing user_id"
        assert "categorized_at" in data_dict

    def test_categorized_bug_from_dict(self, sample_categorized_bug):
        """Test CategorizedBug from_dict deserialization"""
        data_dict = sample_categorized_bug.to_dict()
        restored = CategorizedBug.from_dict(data_dict)

        assert restored.primary_category == BugCategory.LOGIC_ERROR
        assert BugCategory.USER_INPUT_VALIDATION in restored.secondary_categories
        assert restored.severity == "high"
        assert restored.reasoning == sample_categorized_bug.reasoning

    def test_categorized_bug_none_primary_category(self, sample_bug_data):
        """Test CategorizedBug handles None primary_category"""
        categorized = CategorizedBug.from_bug_data(
            sample_bug_data,
            primary_category=None,
            severity="low",
            reasoning="Uncategorized",
        )

        data_dict = categorized.to_dict()
        assert data_dict["primary_category"] is None

        restored = CategorizedBug.from_dict(data_dict)
        assert restored.primary_category is None


# =============================================================================
# TESTS: models.py - BugPattern
# =============================================================================


class TestBugPattern:
    """Tests for BugPattern dataclass"""

    def test_bug_pattern_creation(self, sample_categorized_bug):
        """Test BugPattern creation"""
        now = datetime.now(timezone.utc)
        pattern = BugPattern(
            key="logic-error-auth",
            category=BugCategory.LOGIC_ERROR,
            module="auth",
            bug_count=3,
            first_occurrence=now,
            latest_occurrence=now,
            bugs=[sample_categorized_bug],
            status="open",
        )

        assert pattern.key == "logic-error-auth"
        assert pattern.category == BugCategory.LOGIC_ERROR
        assert pattern.bug_count == 3
        assert len(pattern.bugs) == 1

    def test_bug_pattern_to_dict(self, sample_categorized_bug):
        """Test BugPattern to_dict serialization"""
        now = datetime.now(timezone.utc)
        pattern = BugPattern(
            key="logic-error-auth",
            category=BugCategory.LOGIC_ERROR,
            module="auth",
            bug_count=3,
            first_occurrence=now,
            latest_occurrence=now,
            bugs=[sample_categorized_bug],
            status="open",
            github_issue_number=123,
            github_issue_url="https://github.com/test/repo/issues/123",
        )

        data_dict = pattern.to_dict()

        assert data_dict["key"] == "logic-error-auth"
        assert data_dict["category"] == "logic-error"
        assert data_dict["module"] == "auth"
        assert data_dict["bug_count"] == 3
        assert data_dict["status"] == "open"
        assert data_dict["github_issue_number"] == 123
        assert len(data_dict["bugs"]) == 1

    def test_bug_pattern_from_dict(self, sample_categorized_bug):
        """Test BugPattern from_dict deserialization"""
        now = datetime.now(timezone.utc)
        pattern = BugPattern(
            key="race-condition-db",
            category=BugCategory.RACE_CONDITION,
            module="database",
            bug_count=5,
            first_occurrence=now,
            latest_occurrence=now,
            bugs=[sample_categorized_bug],
            status="closed",
        )

        data_dict = pattern.to_dict()
        restored = BugPattern.from_dict(data_dict)

        assert restored.key == "race-condition-db"
        assert restored.category == BugCategory.RACE_CONDITION
        assert restored.module == "database"
        assert restored.bug_count == 5
        assert restored.status == "closed"
        assert len(restored.bugs) == 1

    def test_bug_pattern_save_and_load(self, sample_categorized_bug, tmp_path):
        """Test BugPattern save and load to/from file"""
        output_dir = tmp_path / "patterns"
        output_dir.mkdir()

        now = datetime.now(timezone.utc)
        pattern = BugPattern(
            key="test-pattern",
            category=BugCategory.LOGIC_ERROR,
            module="test",
            bug_count=1,
            first_occurrence=now,
            latest_occurrence=now,
            bugs=[sample_categorized_bug],
        )

        pattern.save(output_dir)

        output_file = output_dir / "pattern-test-pattern.json"
        assert output_file.exists()

        loaded = BugPattern.load(output_file)
        assert loaded.key == "test-pattern"
        assert loaded.category == BugCategory.LOGIC_ERROR


# =============================================================================
# TESTS: scanner.py - Git History Scanning
# =============================================================================


class TestScanGitHistory:
    """Tests for git history scanning functions"""

    def test_parse_git_log_output_valid(self):
        """Test parsing valid git log output"""
        output = """abc123def456
Jane Developer
jane@example.com
2024-01-15 10:30:00 -0500
fix: handle edge case in parser
Fixed bug where parser failed on empty input.

Fixes #456
---END---
def789abc012
John Coder
john@example.com
2024-01-14 15:45:00 -0500
fix: race condition in worker
Thread safety issue resolved.
---END---"""

        commits = _parse_git_log_output(output)

        assert len(commits) == 2
        assert commits[0]["sha"] == "abc123def456"
        assert commits[0]["author_name"] == "Jane Developer"
        assert commits[0]["message"] == "fix: handle edge case in parser"
        assert "Fixes #456" in commits[0]["body"]

        assert commits[1]["sha"] == "def789abc012"
        assert commits[1]["author_name"] == "John Coder"

    def test_parse_git_log_output_empty(self):
        """Test parsing empty git log output"""
        commits = _parse_git_log_output("")
        assert commits == []

    def test_parse_git_log_output_malformed(self):
        """Test parsing malformed git log output"""
        output = """short
block
---END---"""

        commits = _parse_git_log_output(output)
        # Should skip blocks with < 4 lines
        assert commits == []

    @patch("bug_analysis.scanner.subprocess.run")
    def test_scan_git_history_success(self, mock_run, temp_project_dir):
        """Test scan_git_history with mocked subprocess"""
        mock_run.return_value = MagicMock(
            stdout="""abc123def456
Jane Developer
jane@example.com
2024-01-15 10:30:00 -0500
fix: handle edge case
Body text
---END---
def789abc012
John Coder
john@example.com
2024-01-14 15:45:00 -0500
feat: add new feature
No fix keyword here
---END---""",
            returncode=0,
        )

        commits = scan_git_history(temp_project_dir)

        # Should only return commits with bug keywords
        assert len(commits) == 1
        assert "fix" in commits[0]["message"].lower()

    @patch("bug_analysis.scanner.subprocess.run")
    def test_scan_git_history_filters_keywords(self, mock_run, temp_project_dir):
        """Test that scan_git_history filters by bug keywords"""
        mock_run.return_value = MagicMock(
            stdout="""sha1
Author1
email1@test.com
2024-01-15
bug: found issue
body
---END---
sha2
Author2
email2@test.com
2024-01-15
hotfix: urgent fix
body
---END---
sha3
Author3
email3@test.com
2024-01-15
patch: security update
body
---END---
sha4
Author4
email4@test.com
2024-01-15
feat: new feature
body
---END---""",
            returncode=0,
        )

        commits = scan_git_history(temp_project_dir)

        # Should include commits with bug, hotfix, patch keywords
        assert len(commits) == 3
        messages = [c["message"].lower() for c in commits]
        assert any("bug" in m for m in messages)
        assert any("hotfix" in m for m in messages)
        assert any("patch" in m for m in messages)


class TestExtractRelatedIssues:
    """Tests for issue reference extraction"""

    def test_extract_related_issues_github_format(self):
        """Test extracting GitHub-style issue references"""
        message = "fix: handle login bug"
        body = "This fixes #123 and closes #456."

        issues = extract_related_issues(message, body)

        assert "#123" in issues
        assert "#456" in issues

    def test_extract_related_issues_jira_format(self):
        """Test extracting JIRA-style issue references"""
        message = "fix: resolve PRD-45 issue"
        body = "Also related to PROJ-123."

        issues = extract_related_issues(message, body)

        assert "PRD-45" in issues
        assert "PROJ-123" in issues

    def test_extract_related_issues_mixed_format(self):
        """Test extracting mixed issue reference formats"""
        message = "fix: bug from #789"
        body = "Fixes PRD-100 and #123."

        issues = extract_related_issues(message, body)

        assert "#789" in issues
        assert "#123" in issues
        assert "PRD-100" in issues

    def test_extract_related_issues_no_issues(self):
        """Test extracting when no issues referenced"""
        message = "fix: minor bug"
        body = "Fixed a small issue."

        issues = extract_related_issues(message, body)
        assert issues == []

    def test_extract_related_issues_deduplication(self):
        """Test that duplicate issues are deduplicated"""
        message = "fix: issue #123"
        body = "Related to #123 and #123 again."

        issues = extract_related_issues(message, body)
        assert issues.count("#123") == 1


class TestGetGitHubCommitUrl:
    """Tests for GitHub URL generation"""

    @patch("bug_analysis.scanner.subprocess.run")
    def test_get_github_commit_url_https(self, mock_run, temp_project_dir):
        """Test GitHub URL generation from HTTPS remote"""
        mock_run.return_value = MagicMock(
            stdout="https://github.com/owner/repo.git\n",
            returncode=0,
        )

        url = get_github_commit_url("abc123", temp_project_dir)

        assert url == "https://github.com/owner/repo/commit/abc123"

    @patch("bug_analysis.scanner.subprocess.run")
    def test_get_github_commit_url_ssh(self, mock_run, temp_project_dir):
        """Test GitHub URL generation from SSH remote"""
        mock_run.return_value = MagicMock(
            stdout="git@github.com:owner/repo.git\n",
            returncode=0,
        )

        url = get_github_commit_url("def456", temp_project_dir)

        assert url == "https://github.com/owner/repo/commit/def456"

    @patch("bug_analysis.scanner.subprocess.run")
    def test_get_github_commit_url_no_remote(self, mock_run, temp_project_dir):
        """Test GitHub URL generation when no remote configured"""
        from subprocess import CalledProcessError
        mock_run.side_effect = CalledProcessError(1, "git")

        url = get_github_commit_url("abc123", temp_project_dir)

        assert url is None

    @patch("bug_analysis.scanner.subprocess.run")
    def test_get_github_repo_info_https_no_git_suffix(self, mock_run, temp_project_dir):
        """Test parsing HTTPS URL without .git suffix"""
        mock_run.return_value = MagicMock(
            stdout="https://github.com/owner/repo\n",
            returncode=0,
        )

        info = get_github_repo_info(temp_project_dir)

        assert info["owner"] == "owner"
        assert info["repo"] == "repo"


class TestGetFilesChanged:
    """Tests for get_files_changed function"""

    @patch("bug_analysis.scanner.subprocess.run")
    def test_get_files_changed_success(self, mock_run, temp_project_dir):
        """Test getting files changed in a commit"""
        mock_run.return_value = MagicMock(
            stdout="src/auth/login.py\nsrc/utils/helpers.py\ntests/test_login.py\n",
            returncode=0,
        )

        files = get_files_changed("abc123", temp_project_dir)

        assert len(files) == 3
        assert "src/auth/login.py" in files
        assert "tests/test_login.py" in files

    @patch("bug_analysis.scanner.subprocess.run")
    def test_get_files_changed_failure(self, mock_run, temp_project_dir):
        """Test handling git show failure"""
        from subprocess import CalledProcessError
        mock_run.side_effect = CalledProcessError(1, "git")

        files = get_files_changed("invalid", temp_project_dir)

        assert files == []


class TestGetDiff:
    """Tests for get_diff function"""

    @patch("bug_analysis.scanner.subprocess.run")
    def test_get_diff_success(self, mock_run, temp_project_dir):
        """Test getting diff for a commit"""
        mock_run.return_value = MagicMock(
            stdout="- old line\n+ new line\n",
            returncode=0,
        )

        diff = get_diff("abc123", temp_project_dir)

        assert "- old line" in diff
        assert "+ new line" in diff

    @patch("bug_analysis.scanner.subprocess.run")
    def test_get_diff_truncation(self, mock_run, temp_project_dir):
        """Test diff truncation at limit"""
        long_diff = "x" * 5000
        mock_run.return_value = MagicMock(
            stdout=long_diff,
            returncode=0,
        )

        diff = get_diff("abc123", temp_project_dir, limit=100)

        assert len(diff) == 100


class TestCreateBugId:
    """Tests for create_bug_id function"""

    def test_create_bug_id_format(self):
        """Test bug ID format"""
        bug_id = create_bug_id("abc123def456789")
        assert bug_id == "bug-abc123de"

    def test_create_bug_id_short_sha(self):
        """Test bug ID with short SHA"""
        bug_id = create_bug_id("short")
        assert bug_id == "bug-short"


class TestCreateBugData:
    """Tests for create_bug_data function"""

    @patch("bug_analysis.scanner.get_files_changed")
    @patch("bug_analysis.scanner.get_diff")
    @patch("bug_analysis.scanner.get_github_commit_url")
    def test_create_bug_data_success(
        self, mock_url, mock_diff, mock_files, sample_commit_dict, temp_project_dir
    ):
        """Test creating BugData from commit dict"""
        mock_files.return_value = ["src/parser.py"]
        mock_diff.return_value = "- old\n+ new"
        mock_url.return_value = "https://github.com/test/repo/commit/abc123def456789"

        bug_data = create_bug_data(sample_commit_dict, temp_project_dir)

        assert bug_data.id == "bug-abc123de"
        assert bug_data.commit_sha == "abc123def456789"
        assert bug_data.commit_message == "fix: handle edge case in parser"
        assert bug_data.author_name == "Jane Developer"
        assert bug_data.files_changed == ["src/parser.py"]
        assert "#456" in bug_data.related_issues
        assert "IndexError" in bug_data.error_message


# =============================================================================
# TESTS: scanner.py - Processed Commits Tracking
# =============================================================================


class TestProcessedCommitsTracking:
    """Tests for processed commits tracking"""

    def test_get_processed_commits_empty(self, temp_bug_wikipedia_dir):
        """Test getting processed commits when file doesn't exist"""
        commits = get_processed_commits(temp_bug_wikipedia_dir)
        assert commits == set()

    def test_get_processed_commits_existing(self, temp_bug_wikipedia_dir):
        """Test getting processed commits from existing file"""
        processed_file = temp_bug_wikipedia_dir / ".processed-commits"
        processed_file.write_text("sha1\nsha2\nsha3\n")

        commits = get_processed_commits(temp_bug_wikipedia_dir)

        assert commits == {"sha1", "sha2", "sha3"}

    def test_mark_commit_as_processed(self, temp_bug_wikipedia_dir):
        """Test marking a commit as processed"""
        mark_commit_as_processed("new_sha", temp_bug_wikipedia_dir)

        commits = get_processed_commits(temp_bug_wikipedia_dir)
        assert "new_sha" in commits

    def test_mark_commit_as_processed_appends(self, temp_bug_wikipedia_dir):
        """Test that marking commits appends to existing file"""
        mark_commit_as_processed("sha1", temp_bug_wikipedia_dir)
        mark_commit_as_processed("sha2", temp_bug_wikipedia_dir)

        commits = get_processed_commits(temp_bug_wikipedia_dir)
        assert "sha1" in commits
        assert "sha2" in commits


class TestCreateBugWikipediaDirectories:
    """Tests for directory creation"""

    def test_create_bug_wikipedia_directories(self, temp_bug_wikipedia_dir):
        """Test creating bug Wikipedia directory structure"""
        create_bug_wikipedia_directories(temp_bug_wikipedia_dir)

        expected_dirs = [
            "raw",
            "categorized",
            "categories",
            "by-developer",
            "by-module",
            "patterns",
            "metrics",
            "deep-dive",
        ]

        for dir_name in expected_dirs:
            assert (temp_bug_wikipedia_dir / dir_name).exists()


# =============================================================================
# TESTS: categorizer.py - Prompt Building
# =============================================================================


class TestBuildCategorizationPrompt:
    """Tests for prompt building"""

    def test_build_categorization_prompt_contains_bug_info(self, sample_bug_data):
        """Test that prompt contains bug information"""
        prompt = build_categorization_prompt(sample_bug_data)

        assert sample_bug_data.commit_message in prompt
        assert "src/auth/login.py" in prompt
        assert sample_bug_data.error_message in prompt

    def test_build_categorization_prompt_contains_categories(self, sample_bug_data):
        """Test that prompt contains all bug categories"""
        prompt = build_categorization_prompt(sample_bug_data)

        for category in BUG_CATEGORIES:
            assert category["id"] in prompt

    def test_build_categorization_prompt_truncates_diff(self, sample_bug_data):
        """Test that long diffs are truncated"""
        sample_bug_data.diff = "x" * 1000
        prompt = build_categorization_prompt(sample_bug_data)

        assert "..." in prompt  # Truncation indicator

    def test_build_categorization_prompt_handles_empty_diff(self, sample_bug_data):
        """Test that empty diff is handled"""
        sample_bug_data.diff = ""
        prompt = build_categorization_prompt(sample_bug_data)

        assert "No diff available" in prompt


# =============================================================================
# TESTS: categorizer.py - Response Parsing
# =============================================================================


class TestParseCategorizationResponse:
    """Tests for categorization response parsing"""

    def test_parse_categorization_response_valid_json(self):
        """Test parsing valid JSON response"""
        response = """{
            "primary_category": "logic-error",
            "secondary_categories": ["user-input-validation"],
            "severity": "high",
            "reasoning": "Logic error in handler",
            "prevention_tips": "Add tests",
            "similar_bugs": []
        }"""

        result = parse_categorization_response(response)

        assert result is not None
        assert result["primary_category"] == "logic-error"
        assert result["severity"] == "high"

    def test_parse_categorization_response_with_code_fences(self):
        """Test parsing response wrapped in markdown code fences"""
        response = """```json
{
    "primary_category": "race-condition",
    "secondary_categories": [],
    "severity": "critical",
    "reasoning": "Race condition in async code",
    "prevention_tips": "Use locks"
}
```"""

        result = parse_categorization_response(response)

        assert result is not None
        assert result["primary_category"] == "race-condition"

    def test_parse_categorization_response_invalid_json(self):
        """Test parsing invalid JSON returns None"""
        response = "This is not valid JSON"

        result = parse_categorization_response(response)

        assert result is None

    def test_parse_categorization_response_missing_required_fields(self):
        """Test parsing response missing required fields"""
        response = """{
            "primary_category": "logic-error"
        }"""

        result = parse_categorization_response(response)

        assert result is None  # Missing severity and reasoning

    def test_parse_categorization_response_invalid_category(self):
        """Test parsing response with invalid category"""
        response = """{
            "primary_category": "not-a-real-category",
            "secondary_categories": [],
            "severity": "high",
            "reasoning": "Test"
        }"""

        result = parse_categorization_response(response)

        assert result is None


# =============================================================================
# TESTS: categorizer.py - API Integration
# =============================================================================


class TestCategorizeBugWithHaiku:
    """Tests for API integration"""

    @pytest.mark.asyncio
    async def test_categorize_bug_with_haiku_success(self, sample_bug_data):
        """Test successful API categorization"""
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text="""{
                "primary_category": "logic-error",
                "secondary_categories": [],
                "severity": "medium",
                "reasoning": "Logic error detected",
                "prevention_tips": "Add tests"
            }""")
        ]

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch("bug_analysis.categorizer.create_simple_client", return_value=mock_client):
            result = await categorize_bug_with_haiku(sample_bug_data)

        assert result is not None
        assert result["primary_category"] == "logic-error"

    @pytest.mark.asyncio
    async def test_categorize_bug_with_haiku_retries_on_failure(self, sample_bug_data):
        """Test that API retries on failure"""
        call_count = 0

        async def mock_create(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("API Error")
            mock_response = MagicMock()
            mock_response.content = [
                MagicMock(text="""{
                    "primary_category": "logic-error",
                    "secondary_categories": [],
                    "severity": "medium",
                    "reasoning": "Test",
                    "prevention_tips": "Test"
                }""")
            ]
            return mock_response

        mock_client = AsyncMock()
        mock_client.messages.create = mock_create

        with patch("bug_analysis.categorizer.create_simple_client", return_value=mock_client):
            result = await categorize_bug_with_haiku(sample_bug_data)

        assert call_count == 3
        assert result is not None

    @pytest.mark.asyncio
    async def test_categorize_bug_with_haiku_max_retries_exceeded(self, sample_bug_data):
        """Test that None is returned after max retries"""
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(side_effect=Exception("API Error"))

        with patch("bug_analysis.categorizer.create_simple_client", return_value=mock_client):
            result = await categorize_bug_with_haiku(sample_bug_data)

        assert result is None


# =============================================================================
# TESTS: categorizer.py - Uncategorized Bug Discovery
# =============================================================================


class TestGetUncategorizedBugs:
    """Tests for uncategorized bug discovery"""

    def test_get_uncategorized_bugs_empty_dirs(self, temp_bug_wikipedia_dir):
        """Test with empty directories"""
        bugs = get_uncategorized_bugs(temp_bug_wikipedia_dir)
        assert bugs == []

    def test_get_uncategorized_bugs_all_categorized(self, temp_bug_wikipedia_dir, sample_bug_data):
        """Test when all bugs are categorized"""
        raw_dir = temp_bug_wikipedia_dir / "raw"
        categorized_dir = temp_bug_wikipedia_dir / "categorized"
        raw_dir.mkdir()
        categorized_dir.mkdir()

        # Create both raw and categorized versions
        sample_bug_data.save(raw_dir)
        sample_bug_data.save(categorized_dir)

        bugs = get_uncategorized_bugs(temp_bug_wikipedia_dir)
        assert len(bugs) == 0

    def test_get_uncategorized_bugs_some_uncategorized(self, temp_bug_wikipedia_dir, sample_bug_data):
        """Test when some bugs are uncategorized"""
        raw_dir = temp_bug_wikipedia_dir / "raw"
        categorized_dir = temp_bug_wikipedia_dir / "categorized"
        raw_dir.mkdir()
        categorized_dir.mkdir()

        # Create raw bug
        sample_bug_data.save(raw_dir)

        # Create second bug that is categorized
        bug2 = BugData(
            id="bug-other123",
            commit_sha="other123",
            commit_message="fix: other",
            author_name="Test",
            author_email="test@test.com",
            date_fixed=datetime.now(timezone.utc),
            files_changed=[],
            diff="",
            related_issues=[],
            github_url=None,
            error_message="",
            scanned_at=datetime.now(timezone.utc),
        )
        bug2.save(raw_dir)
        bug2.save(categorized_dir)

        bugs = get_uncategorized_bugs(temp_bug_wikipedia_dir)

        # Should only return the uncategorized bug
        assert len(bugs) == 1
        assert bugs[0].name == f"{sample_bug_data.id}.json"


# =============================================================================
# TESTS: Integration scenarios
# =============================================================================


class TestBugAnalysisIntegration:
    """Integration tests for bug analysis workflow"""

    def test_full_bug_data_workflow(self, tmp_path):
        """Test creating, serializing, and deserializing bug data"""
        # Create bug data
        bug = BugData(
            id="bug-integration",
            commit_sha="integration123",
            commit_message="fix: integration test bug",
            author_name="Integration Tester",
            author_email="int@test.com",
            date_fixed=datetime.now(timezone.utc),
            files_changed=["test.py"],
            diff="+ integrated",
            related_issues=["#999"],
            github_url="https://github.com/test/repo/commit/integration123",
            error_message="IntegrationError",
            scanned_at=datetime.now(timezone.utc),
        )

        # Save to file
        output_dir = tmp_path / "bugs"
        output_dir.mkdir()
        bug.save(output_dir)

        # Load from file
        loaded = BugData.load(output_dir / "bug-integration.json")

        # Verify
        assert loaded.id == bug.id
        assert loaded.commit_message == bug.commit_message
        assert loaded.related_issues == bug.related_issues

    def test_full_categorization_workflow(self, tmp_path, sample_bug_data):
        """Test bug categorization workflow"""
        # Create CategorizedBug from BugData
        categorized = CategorizedBug.from_bug_data(
            sample_bug_data,
            primary_category=BugCategory.LOGIC_ERROR,
            secondary_categories=[BugCategory.USER_INPUT_VALIDATION],
            severity="high",
            reasoning="Test reasoning",
            prevention_tips="Test tips",
        )

        # Save categorized bug
        output_dir = tmp_path / "categorized"
        output_dir.mkdir()
        categorized.save(output_dir)

        # Load and verify
        loaded = CategorizedBug.load(output_dir / f"{categorized.id}.json")

        assert loaded.primary_category == BugCategory.LOGIC_ERROR
        assert loaded.severity == "high"

    def test_pattern_detection_workflow(self, tmp_path, sample_categorized_bug):
        """Test pattern creation and persistence workflow"""
        now = datetime.now(timezone.utc)

        # Create pattern
        pattern = BugPattern(
            key="logic-error-auth",
            category=BugCategory.LOGIC_ERROR,
            module="auth",
            bug_count=5,
            first_occurrence=now,
            latest_occurrence=now,
            bugs=[sample_categorized_bug],
            status="open",
            github_issue_number=100,
            github_issue_url="https://github.com/test/repo/issues/100",
        )

        # Save pattern
        patterns_dir = tmp_path / "patterns"
        patterns_dir.mkdir()
        pattern.save(patterns_dir)

        # Load and verify
        loaded = BugPattern.load(patterns_dir / "pattern-logic-error-auth.json")

        assert loaded.key == "logic-error-auth"
        assert loaded.bug_count == 5
        assert loaded.github_issue_number == 100
        assert len(loaded.bugs) == 1
