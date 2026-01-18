# Bug Wikipedia - Quick Start Guide

## What Was Built

✅ **Phase 1 Complete** - Core data models and scanning functionality

- **models.py** - BugCategory, BugData, CategorizedBug, BugPattern
- **scanner.py** - Git history scanning, file analysis, GitHub URL generation
- **categorizer.py** - AI-powered categorization with Claude Haiku

**Status**: ~1100 lines of production Python code created

## What's Next

🚧 **Phase 2** - Documentation and pattern detection

1. `generator.py` - Generate markdown docs from categorized bugs
2. `detector.py` - Detect recurring patterns, create GitHub issues
3. `deep_dive.py` - Root cause analysis using Auto-Claude agents
4. `cli/bug_commands.py` - CLI command handlers
5. Modify `cli/main.py` - Register commands
6. Extend `qa/report.py` - Auto-extract bugs from QA failures

## Quick Test (What Works Now)

```python
# Test the models
from bug_analysis.models import BugCategory, BugData
from datetime import datetime, timezone

# Create a bug
bug = BugData(
    id="bug-test1234",
    commit_sha="test1234567890",
    commit_message="fix: resolve login issue",
    author_name="Test User",
    author_email="test@example.com",
    date_fixed=datetime.now(timezone.utc),
    files_changed=["src/auth/login.py"],
    diff="- old code\n+ new code",
    related_issues=["#123"],
    github_url="https://github.com/user/repo/commit/test1234",
    error_message="KeyError: 'user_id'",
    scanned_at=datetime.now(timezone.utc)
)

# Save to file
from pathlib import Path
output_dir = Path(".auto-claude/bug-wikipedia/raw")
bug.save(output_dir)

# Load it back
loaded = BugData.load(output_dir / "bug-test1234.json")
print(f"Loaded bug: {loaded.commit_message}")
```

```python
# Test the scanner
from bug_analysis.scanner import scan_bugs
from pathlib import Path

project_dir = Path("/Users/tinnguyen/Auto-Claude")
bug_wikipedia_dir = Path(".auto-claude/bug-wikipedia")

# Scan git history
total, new = scan_bugs(project_dir, bug_wikipedia_dir, scan_mode="project")
print(f"Found {total} bugs, processed {new} new ones")

# Check results
raw_dir = bug_wikipedia_dir / "raw"
print(f"Bug files created: {len(list(raw_dir.glob('*.json')))}")
```

```python
# Test the categorizer (requires ANTHROPIC_API_KEY)
import asyncio
from bug_analysis.categorizer import categorize_bugs
from pathlib import Path

async def test_categorizer():
    bug_wikipedia_dir = Path(".auto-claude/bug-wikipedia")

    # Categorize 3 bugs
    success, fail = await categorize_bugs(
        bug_wikipedia_dir,
        limit=3,
        dry_run=False  # Set to True to preview without API calls
    )
    print(f"Success: {success}, Failed: {fail}")

# Run it
asyncio.run(test_categorizer())
```

## File Reference

### Ralph CLI Source Files
Located in: `/Users/tinnguyen/ralph-cli/scripts/`

- `bug-scanner.js` → ✅ Ported to `scanner.py`
- `bug-categorizer.js` → ✅ Ported to `categorizer.py`
- `bug-wikipedia-generator.js` → 🚧 Port to `generator.py`
- `bug-pattern-detector.js` → 🚧 Port to `detector.py`

### Auto-Claude Implementation
Located in: `/Users/tinnguyen/Auto-Claude/apps/backend/bug_analysis/`

- ✅ `__init__.py` - Module exports
- ✅ `models.py` - Data models (318 lines)
- ✅ `scanner.py` - Git scanning (417 lines)
- ✅ `categorizer.py` - AI categorization (352 lines)
- 🚧 `generator.py` - TODO
- 🚧 `detector.py` - TODO
- 🚧 `deep_dive.py` - TODO
- 🚧 `integration.py` - TODO

## Next Command to Run

```bash
# Create generator.py next
cd /Users/tinnguyen/Auto-Claude
code apps/backend/bug_analysis/generator.py

# Port from:
# /Users/tinnguyen/ralph-cli/scripts/bug-wikipedia-generator.js

# Key functions to port:
# - generate_index_md()
# - generate_category_md()
# - generate_developer_md()
# - generate_module_md()
# - generate_metrics()
```

## Implementation Guide

📖 **Full Details**: See `BUG_WIKIPEDIA_PORT_IMPLEMENTATION.md`

**Quick Steps**:
1. Read Ralph CLI source file (JS)
2. Create Python file with same structure
3. Replace Node.js APIs:
   - `fs` → `pathlib.Path`
   - `execSync` → `subprocess.run`
   - `@anthropic-ai/sdk` → `core.simple_client`
4. Use async/await for API calls
5. Add type hints
6. Test incrementally

## Progress Tracker

- [x] Phase 1: Models + Scanner + Categorizer (✅ DONE)
- [ ] Phase 2: Generator + Detector
- [ ] Phase 3: Deep Dive + Integration
- [ ] Phase 4: CLI Commands
- [ ] Phase 5: QA Integration
- [ ] Phase 6: Testing
- [ ] Phase 7: Frontend (Optional)

## Questions?

- **Implementation Guide**: `BUG_WIKIPEDIA_PORT_IMPLEMENTATION.md`
- **Session Summary**: `BUG_WIKIPEDIA_PORT_SUMMARY.md`
- **Original Plan**: See prompt above (full porting plan)

---

**Created**: 2026-01-18
**Status**: Phase 1 Complete (3/7 core modules)
**Next**: Create generator.py and detector.py
