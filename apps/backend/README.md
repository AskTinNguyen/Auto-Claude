# Auto Claude Backend

Autonomous coding framework powered by Claude AI. Builds software features through coordinated multi-agent sessions.

## Getting Started

### 1. Install

```bash
cd apps/backend
python -m pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
```

Set your Claude API token in `.env`:
```
CLAUDE_CODE_OAUTH_TOKEN=your-token-here
```

Get your token by running: `claude setup-token`

### 3. Run

```bash
# List available specs
python run.py --list

# Run a spec
python run.py --spec 001
```

## Requirements

- Python 3.10+
- Claude API token

## Commands

| Command | Description |
|---------|-------------|
| `--list` | List all specs |
| `--spec 001` | Run spec 001 |
| `--spec 001 --isolated` | Run in isolated workspace |
| `--spec 001 --direct` | Run directly in repo |
| `--spec 001 --merge` | Merge completed build |
| `--spec 001 --review` | Review build changes |
| `--spec 001 --discard` | Discard build |
| `--spec 001 --qa` | Run QA validation |
| `--list-worktrees` | List all worktrees |
| `--help` | Show all options |

## Merge Completion Tracking

Auto Claude automatically tracks all merge operations to provide visibility into merge history, conflicts resolved, and AI assistance used.

### What Gets Tracked

Each successful merge records:
- **Metadata**: Spec name, timestamp, unique merge ID
- **Files**: List of all files merged
- **Conflict Statistics**: Conflicts resolved, AI-assisted merges, auto-merged files
- **Merge Strategy**: fast-forward, 3-way, ai-assisted, or manual
- **Performance**: Optional duration in seconds
- **Success Status**: Whether merge completed successfully

### Storage Location

Merge history is stored in JSON format:
```
.auto-claude/merge-history/merge_history.json
```

This file is automatically created on the first merge and persists across all specs.

### Querying Merge History

Use the `MergeCompletionStorage` API to query merge data:

```python
from core.workspace.merge_completion import MergeCompletionStorage

# Initialize storage
storage = MergeCompletionStorage(project_dir=Path("/path/to/project"))

# Get all merges for a specific spec
spec_merges = storage.get_merge_history(spec_name="001-auth-feature")

# Get recent merges (default: 10 most recent)
recent = storage.get_recent_merges(limit=20)

# Get merges by strategy
ai_assisted = storage.get_merges_by_strategy("ai-assisted")

# Get successful vs failed merges
successful = storage.get_successful_merges()
failed = storage.get_failed_merges()

# Get merges with conflicts
conflict_merges = storage.get_merges_with_conflicts()

# Get summary statistics
stats = storage.get_merge_stats_summary(spec_name="001-auth-feature")
# Returns: total_merges, successful_merges, failed_merges,
#          total_conflicts_resolved, total_ai_assisted,
#          total_files_merged, average_duration, merge_strategies
```

### Advanced Queries

```python
# Find files merged multiple times
multi_merged = storage.get_files_merged_multiple_times()
# Returns: {file_path: [merge_id1, merge_id2, ...]}

# Get most frequently merged files
hotspots = storage.get_most_merged_files(limit=10)
# Returns: [(file_path, merge_count), ...]

# Get merges within date range
from datetime import datetime
start = datetime(2024, 1, 1)
end = datetime(2024, 12, 31)
year_merges = storage.get_merges_by_date_range(start, end)

# Get specific merge by ID
merge = storage.get_merge_by_id("uuid-here")
```

### UI Integration

The Electron frontend automatically displays merge history in the UI. Merge data is read from the JSON file and displayed with:
- Merge timeline
- Conflict statistics
- AI assistance metrics
- Success/failure status

## Configuration

Optional `.env` settings:

| Variable | Description |
|----------|-------------|
| `AUTO_BUILD_MODEL` | Override Claude model |
| `DEBUG=true` | Enable debug logging |
| `LINEAR_API_KEY` | Enable Linear integration |
| `GRAPHITI_ENABLED=true` | Enable memory system |

## Troubleshooting

**"tree-sitter not available"** - Safe to ignore, uses regex fallback.

**Missing module errors** - Run `python -m pip install -r requirements.txt`

**Debug mode** - Set `DEBUG=true DEBUG_LEVEL=2` before running.

---

## For Developers

### Project Structure

```
backend/
├── agents/          # AI agent execution
├── analysis/        # Code analysis
├── cli/             # Command-line interface
├── core/            # Core utilities
├── integrations/    # External services (Linear, Graphiti)
├── merge/           # Git merge handling
├── project/         # Project detection
├── prompts/         # Prompt templates
├── qa/              # QA validation
├── spec/            # Spec management
└── ui/              # Terminal UI
```

### Design Principles

- **SOLID** - Single responsibility, clean interfaces
- **DRY** - Shared utilities in `core/`
- **KISS** - Simple flat imports via facade modules

### Import Convention

```python
# Use facade modules for clean imports
from debug import debug, debug_error
from progress import count_subtasks
from workspace import setup_workspace
```

### Adding Features

1. Create module in appropriate folder
2. Export API in `__init__.py`
3. Add facade module at root if commonly imported

## License

AGPL-3.0
