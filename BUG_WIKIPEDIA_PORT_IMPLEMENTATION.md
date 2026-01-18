# Bug Wikipedia Feature Port: Implementation Guide

## Status: Phase 1 Complete (Models + Scanner)

### Completed ✅

1. **Module Structure** - `/apps/backend/bug_analysis/`
   - `__init__.py` - Module exports
   - `models.py` - Complete data models (BugCategory, BugData, CategorizedBug, BugPattern)
   - `scanner.py` - Git history scanning (full port from JS to Python)

2. **Data Models**
   - `BugCategory` enum with 10 categories
   - `BugData` dataclass for raw bug data
   - `CategorizedBug` dataclass extending BugData
   - `BugPattern` dataclass for pattern tracking
   - JSON serialization/deserialization for all models

3. **Scanner Module**
   - Git history scanning with bug keyword filtering
   - File change and diff extraction
   - Issue reference extraction (#123, PRD-45)
   - GitHub URL generation
   - Processed commits tracking
   - Directory structure creation

### Next Steps 🚀

#### Phase 2: Categorizer (Priority: HIGH)

Create `/apps/backend/bug_analysis/categorizer.py`:

```python
"""
Bug Categorizer - AI-powered categorization using Claude Haiku
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime, timezone

from core.simple_client import create_simple_client
from .models import BugData, CategorizedBug, BugCategory

# Configuration
MAX_RETRIES = 3
RETRY_DELAY_MS = 1000
MAX_DIFF_LENGTH = 500
DEFAULT_BATCH_SIZE = 10
CATEGORIZATION_MODEL = "claude-3-5-haiku-20241022"


def build_categorization_prompt(bug: BugData) -> str:
    """Build prompt for Claude Haiku categorization"""
    # Port from bug-categorizer.js lines 270-314
    ...


async def categorize_bug_with_haiku(
    bug: BugData,
    client
) -> dict | None:
    """Call Claude Haiku for categorization with retries"""
    # Port from bug-categorizer.js lines 323-364
    ...


def parse_categorization_response(response_text: str) -> dict | None:
    """Parse and validate categorization JSON response"""
    # Port from bug-categorizer.js lines 371-411
    ...


async def categorize_bugs(
    bug_wikipedia_dir: Path,
    limit: int = DEFAULT_BATCH_SIZE,
    dry_run: bool = False
) -> tuple[int, int]:
    """Categorize uncategorized bugs"""
    # Main categorization logic
    ...
```

**Key changes from JS:**
- Use `await create_simple_client()` instead of Anthropic SDK
- Async/await for API calls
- Python pathlib instead of Node path module
- Rate limiting with asyncio.sleep(0.2)

#### Phase 3: Generator (Priority: HIGH)

Create `/apps/backend/bug_analysis/generator.py`:

Port from `/ralph-cli/scripts/bug-wikipedia-generator.js`:
- `generate_index_md()` - Table of contents
- `generate_category_md()` - Category-specific docs
- `generate_developer_md()` - By-developer sections
- `generate_module_md()` - By-module sections
- `generate_metrics()` - Statistics JSON

#### Phase 4: Detector (Priority: HIGH)

Create `/apps/backend/bug_analysis/detector.py`:

Port from `/ralph-cli/scripts/bug-pattern-detector.js`:
- `detect_patterns()` - Pattern detection logic
- `create_github_issue()` - GitHub API integration (use requests, not MCP)
- `check_pattern_resolution()` - Auto-close resolved patterns

#### Phase 5: Deep Dive (Priority: MEDIUM)

Create `/apps/backend/bug_analysis/deep_dive.py`:

**NOT porting Ralph's Factory YAML** - use Auto-Claude agents instead:

```python
from agents.planner import PlannerAgent

async def analyze_bug_pattern(
    pattern: BugPattern,
    spec_dir: Path
) -> Path:
    """Trigger root cause analysis using planner agent"""
    agent = PlannerAgent(
        spec_dir=spec_dir,
        model="claude-3-5-sonnet-20241022"
    )

    prompt = f"""Analyze recurring bug pattern:
    Category: {pattern.category.value}
    Module: {pattern.module}
    Bugs: {pattern.bug_count} in 30 days
    ...
    """

    result = await agent.analyze(prompt)
    # Save to deep-dive/{pattern.key}/
    ...
```

#### Phase 6: QA Integration (Priority: HIGH)

Extend `/apps/backend/qa/report.py`:

```python
# Add to record_iteration()
def record_iteration(...):
    # Existing code...

    # NEW: Extract bugs from issues
    if status == "rejected":
        from bug_analysis.integration import extract_bugs_from_iteration
        bugs = extract_bugs_from_iteration(issues, spec_dir)

        # Save bugs
        bug_wikipedia_dir = spec_dir / "bug-wikipedia"
        for bug in bugs:
            bug.save(bug_wikipedia_dir / "raw")

        # Check for patterns
        from bug_analysis.detector import detect_patterns
        patterns = await detect_patterns(bug_wikipedia_dir)
        if patterns:
            # Trigger deep dive, create GitHub issues
            ...
```

Create `/apps/backend/bug_analysis/integration.py`:

```python
def extract_bugs_from_iteration(
    issues: list[dict],
    spec_dir: Path
) -> list[BugData]:
    """Convert QA issues to BugData format"""
    ...
```

#### Phase 7: CLI Commands (Priority: HIGH)

Create `/apps/backend/cli/bug_commands.py`:

```python
async def handle_bug_scan_command(args):
    """ralph bug-scan [--mode=auto-claude|project]"""
    ...

async def handle_bug_categorize_command(args):
    """ralph bug-categorize [--limit=N] [--dry-run]"""
    ...

async def handle_bug_generate_command(args):
    """ralph bug-wiki"""
    ...

async def handle_bug_detect_command(args):
    """ralph bug-detect"""
    ...

async def handle_bug_status_command(args):
    """ralph bug-status"""
    ...

async def handle_bug_deep_dive_command(args):
    """ralph bug-deep-dive <pattern-key>"""
    ...
```

Register in `/apps/backend/cli/main.py`:

```python
# Add argument groups
bug_group = parser.add_argument_group("Bug Wikipedia")
bug_group.add_argument("--bug-scan", action="store_true")
bug_group.add_argument("--bug-categorize", action="store_true")
bug_group.add_argument("--bug-wiki", action="store_true")
bug_group.add_argument("--bug-detect", action="store_true")
bug_group.add_argument("--bug-status", action="store_true")
bug_group.add_argument("--bug-deep-dive", metavar="PATTERN")
bug_group.add_argument("--bug-mode", choices=["auto-claude", "project"], default="project")
bug_group.add_argument("--limit", type=int)
bug_group.add_argument("--dry-run", action="store_true")

# Route to handlers
if args.bug_scan:
    from cli.bug_commands import handle_bug_scan_command
    await handle_bug_scan_command(args)
# ... etc
```

#### Phase 8: Configuration (Priority: MEDIUM)

Create `.auto-claude/bug-wikipedia-config.json`:

```json
{
  "enabled": true,
  "scan_mode": "project",
  "pattern_threshold": 3,
  "pattern_window_days": 30,
  "pattern_resolution_days": 60,
  "auto_create_issues": true,
  "deep_dive_enabled": true,
  "deep_dive_agent": "planner",
  "categorization_model": "claude-3-5-haiku-20241022"
}
```

#### Phase 9: Frontend (Priority: LOW - Can defer)

1. **IPC Handlers** - `apps/frontend/src/main/ipc-handlers/bug-analysis-handlers.ts`
2. **React Components**:
   - `BugWikipediaView.tsx` - Main view with tabs
   - `PatternCard.tsx` - Pattern detail cards
   - `BugList.tsx` - Filterable bug list
3. **Navigation** - Add to main menu

#### Phase 10: Testing (Priority: HIGH after Phase 7)

1. **Unit Tests** - `tests/test_bug_analysis.py`
2. **Integration Tests** - `tests/test_bug_analysis_integration.py`
3. **E2E Tests** - `apps/frontend/e2e/bug-wikipedia.spec.ts`

### Implementation Order

**Week 1: Backend Core**
1. ✅ Models + Scanner (DONE)
2. Categorizer
3. Generator
4. Detector
5. CLI Commands

**Week 2: Integration**
6. QA Integration
7. Deep Dive
8. Configuration
9. End-to-end testing

**Week 3-4: Frontend (Optional)**
10. IPC Handlers
11. React Components
12. E2E Tests

### Testing Checklist

After completing backend phases:

```bash
# Test scan
cd /Users/tinnguyen/Auto-Claude
python run.py --bug-scan --bug-mode=auto-claude

# Test categorize (requires ANTHROPIC_API_KEY)
python run.py --bug-categorize --limit=5

# Test generate
python run.py --bug-wiki

# Test detect
python run.py --bug-detect

# Test status
python run.py --bug-status

# Test integration with QA
python run.py --spec test-spec --qa
# (Should auto-extract bugs from QA issues)
```

### Directory Structure

```
/Users/tinnguyen/Auto-Claude/
├── apps/backend/
│   ├── bug_analysis/          ✅ Created
│   │   ├── __init__.py        ✅ Done
│   │   ├── models.py          ✅ Done
│   │   ├── scanner.py         ✅ Done
│   │   ├── categorizer.py     🚧 Next
│   │   ├── generator.py       ⏳ Todo
│   │   ├── detector.py        ⏳ Todo
│   │   ├── deep_dive.py       ⏳ Todo
│   │   └── integration.py     ⏳ Todo
│   ├── cli/
│   │   ├── bug_commands.py    ⏳ Todo
│   │   └── main.py            🔧 Modify
│   └── qa/
│       └── report.py          🔧 Modify (add bug extraction)
├── .auto-claude/
│   ├── bug-wikipedia-config.json  ⏳ Create
│   └── bug-wikipedia/             ⏳ Auto-created
│       ├── raw/
│       ├── categorized/
│       ├── categories/
│       ├── by-developer/
│       ├── by-module/
│       ├── patterns/
│       ├── metrics/
│       └── deep-dive/
└── tests/
    ├── test_bug_analysis.py       ⏳ Todo
    └── test_bug_analysis_integration.py  ⏳ Todo
```

### Key Differences from Ralph CLI

1. **Language**: JavaScript → Python
2. **AI Client**: Anthropic SDK → `core.simple_client.create_simple_client()`
3. **Deep Dive**: Factory YAML → Auto-Claude PlannerAgent
4. **Storage**: `.ralph/bug-wikipedia/` → `.auto-claude/bug-wikipedia/`
5. **QA Integration**: NEW - Ralph doesn't have QA loop integration
6. **Scan Modes**: NEW - Can analyze Auto-Claude itself or user projects

### Success Criteria

✅ **Backend Complete When:**
- All CLI commands work (`--bug-scan`, `--bug-categorize`, etc.)
- QA integration triggers pattern detection automatically
- Deep dive generates root cause analysis
- GitHub issues created for patterns (optional, requires token)

✅ **Full Feature Complete When:**
- Frontend UI displays bug data
- E2E tests pass
- Documentation updated

### Notes

- **Priority**: Focus on backend (Phases 1-7) first
- **Frontend**: Can defer to later - backend provides full functionality via CLI
- **Testing**: Add unit tests as you build each module
- **Dependencies**: Uses existing Auto-Claude infrastructure (agents, simple_client, CLI)

### Files Modified from this Session

1. ✅ `/apps/backend/bug_analysis/__init__.py` - Created
2. ✅ `/apps/backend/bug_analysis/models.py` - Created (300+ lines)
3. ✅ `/apps/backend/bug_analysis/scanner.py` - Created (400+ lines)

### Next Command to Run

```bash
# Create categorizer.py
# Port from /Users/tinnguyen/ralph-cli/scripts/bug-categorizer.js
# Follow the template above for async/await patterns
```
