# Port Ralph CLI Terminal Commands to Auto-Claude

## Objective

Port Ralph-CLI's comprehensive terminal command suite to Auto-Claude, creating a unified CLI experience that combines Auto-Claude's Python backend with Ralph's powerful command-line tools.

---

## Background

We've successfully integrated Ralph-CLI's core features into Auto-Claude:
- ✅ Ralph's PRD template (spec_writer_ralph.md)
- ✅ Ralph's planning format (planner_ralph.md)
- ✅ Quality scoring system (0-100, A-F grades)
- ✅ TTS integration (voice feedback)
- ✅ Monitoring (heartbeat, cost tracking, events)
- ✅ Frontend components (React/TypeScript)

**Next step**: Port Ralph's 40+ terminal commands to create a feature-complete CLI for Auto-Claude.

---

## Ralph CLI Commands to Port

### Category 1: Getting Started (4 commands)
```bash
ralph install [--skills] [--import-from]  # Copy .agents/ralph into repo
ralph init                                # Interactive setup wizard
ralph ping                                # Verify agent connection
ralph help                                # Show help message
```

**Auto-Claude equivalent**: Adapt to Python CLI with Auto-Claude's structure

### Category 2: Core Workflow (5 commands)
```bash
ralph prd ["<request>"] [--out path]      # Generate PRD via agent
ralph plan [n] [--prd=N]                  # Create implementation plan
ralph build [n] [--resume] [--auto-fix]   # Execute n build iterations
ralph eval [run-id] [--all]               # Evaluate run quality
ralph improve [--generate] [--apply]      # Review/apply guardrails
```

**Auto-Claude status**:
- ✅ `spec_runner.py` (equivalent to `ralph prd`)
- ✅ Planning phase integrated
- ✅ `run.py` (equivalent to `ralph build`)
- ❌ `eval` and `improve` need porting

### Category 3: Stream Management (7 commands - Parallel Execution)
```bash
ralph stream list                         # List all PRD streams
ralph stream status                       # Show stream status
ralph stream new                          # Create new stream
ralph stream init <N>                     # Initialize worktree
ralph stream build <N> [n]                # Run iterations in stream N
ralph stream merge <N>                    # Merge stream to main
ralph stream cleanup <N>                  # Remove stream worktree
```

**Auto-Claude status**:
- ✅ Git worktree support exists (`.worktrees/` in Auto-Claude)
- ❌ Stream management CLI missing

### Category 4: Analytics & Estimation (8 commands)
```bash
ralph estimate [--prd=N] [--json]         # Estimate time/cost
ralph stats [--global] [--json]           # Performance dashboard
ralph stats switches [--json]             # Agent switch analytics
ralph budget set <amount>                 # Set budget limit
ralph budget show                         # Show budget status
ralph budget clear                        # Remove budget
ralph routing analyze                     # Analyze routing outcomes
ralph routing suggest                     # Suggest threshold adjustments
ralph routing learn                       # Generate guardrails
```

**Auto-Claude status**:
- ✅ Cost tracking integrated (monitoring/cost_tracker.py)
- ❌ CLI commands missing for stats/budget/routing

### Category 5: Diagnostics & Experimentation (10 commands)
```bash
ralph doctor [--verbose] [--fix]          # Environment diagnostics
ralph diagnose [--run id] [--json]        # Detect failure patterns

ralph experiment create <name>            # Create A/B experiment
ralph experiment list                     # List experiments
ralph experiment status <name>            # Show experiment status
ralph experiment start <name>             # Start experiment
ralph experiment pause <name>             # Pause experiment
ralph experiment conclude <name>          # Conclude experiment
ralph experiment analyze <name>           # Analyze results
```

**Auto-Claude status**:
- ❌ Doctor command missing (useful for setup validation)
- ❌ Experiment framework missing (valuable for A/B testing prompts)

### Category 6: Project & Knowledge Management (7 commands)
```bash
ralph registry add [--tags]               # Register project
ralph registry list [--tags]              # List projects
ralph registry remove                     # Remove project
ralph registry update                     # Update metadata

ralph search <query> [--filters]          # Search across projects
ralph import guardrails [--from]          # Import guardrails
ralph optimize prompts [--apply]          # Improve prompts
```

**Auto-Claude status**:
- ❌ Project registry missing
- ❌ Cross-project search missing
- ✅ Guardrails partially exist (security.py)

### Category 7: Voice & TTS (2 commands)
```bash
ralph speak ["<text>"] [--auto-on/off]    # Speak text / manage auto-speak
ralph recap [--full|--short|--preview]    # Summarize and speak
```

**Auto-Claude status**:
- ✅ TTS integrated (integrations/tts/)
- ❌ CLI commands missing

### Category 8: Executive Automation (5 commands)
```bash
ralph automation slack-report             # Send reports to Slack
ralph automation check-blockers           # Detect blocked PRDs
ralph automation github-archive           # Archive metrics
ralph automation scan-bugs                # Scan git for bugs
ralph automation verify                   # Check installation
```

**Auto-Claude status**:
- ❌ Automation suite missing
- ⚠️ Linear integration exists (could expand)

### Category 9: Utilities (6 commands)
```bash
ralph checkpoint list [--prd=N]           # List checkpoints
ralph checkpoint clear [--prd=N]          # Clear checkpoints
ralph watch [--prd=N] [--build]           # Watch files for changes
ralph ui [port] [--open]                  # Start UI server
ralph log "<message>"                     # Append to activity log
ralph completions [bash|zsh|fish]         # Shell completions
```

**Auto-Claude status**:
- ✅ UI exists (Electron frontend)
- ❌ Checkpoint management CLI missing
- ❌ Watch mode missing
- ❌ Shell completions missing

### Category 10: Quality Review (1 command)
```bash
ralph review                              # Quality review workflow
```

**Auto-Claude status**:
- ✅ QA reviewer/fixer integrated
- ❌ CLI command missing

---

## Implementation Strategy

### Phase 1: Foundation (Week 1-2)
**Create Python CLI structure**

1. **Create CLI package** (`apps/backend/cli/`)
   ```
   apps/backend/cli/
   ├── __init__.py
   ├── commands/
   │   ├── __init__.py
   │   ├── install.py
   │   ├── init.py
   │   ├── ping.py
   │   ├── estimate.py
   │   ├── stats.py
   │   ├── budget.py
   │   ├── doctor.py
   │   ├── stream.py
   │   ├── checkpoint.py
   │   ├── speak.py
   │   └── [...]
   ├── main.py          # Main CLI dispatcher
   └── parser.py        # Argument parsing
   ```

2. **Create entry point** (`apps/backend/autoclauder` or `apps/backend/ac`)
   ```python
   #!/usr/bin/env python3
   """Auto-Claude CLI - Ralph-enhanced"""
   from cli.main import main
   if __name__ == "__main__":
       main()
   ```

3. **Add to package.json scripts** for easy access
   ```json
   {
     "scripts": {
       "ac": "cd apps/backend && python -m cli.main"
     }
   }
   ```

### Phase 2: Core Commands (Week 3-4)
**Port essential workflow commands**

- ✅ `ac init` - Interactive setup wizard
- ✅ `ac doctor` - Environment diagnostics
- ✅ `ac ping` - Verify Claude connection
- ✅ `ac estimate` - Cost/time estimation
- ✅ `ac stats` - Performance dashboard
- ✅ `ac budget` - Budget management

### Phase 3: Stream Management (Week 5-6)
**Leverage Auto-Claude's worktree system**

- ✅ `ac stream list` - List active worktrees
- ✅ `ac stream new` - Create new spec worktree
- ✅ `ac stream status` - Show all stream statuses
- ✅ `ac stream build <N>` - Run build in specific worktree
- ✅ `ac stream merge <N>` - Merge worktree to main
- ✅ `ac stream cleanup <N>` - Remove worktree

### Phase 4: Advanced Features (Week 7-8)
**Experimentation & optimization**

- ✅ `ac experiment create/list/analyze` - A/B testing framework
- ✅ `ac routing analyze/suggest/learn` - Model routing optimization
- ✅ `ac optimize prompts` - Prompt improvement
- ✅ `ac diagnose` - Failure pattern detection

### Phase 5: Voice & Automation (Week 9-10)
**TTS CLI & automation suite**

- ✅ `ac speak` - TTS control
- ✅ `ac recap` - Summarize and speak
- ✅ `ac automation slack-report` - Team reporting
- ✅ `ac automation check-blockers` - Blocker detection
- ✅ `ac automation github-archive` - Metrics archiving

### Phase 6: Utilities & Polish (Week 11-12)
**Developer experience improvements**

- ✅ `ac checkpoint list/clear` - Checkpoint management
- ✅ `ac watch` - File watching for auto-rebuild
- ✅ `ac log` - Activity logging
- ✅ `ac completions` - Shell completions (bash/zsh/fish)
- ✅ `ac review` - Quality review workflow

---

## Technical Requirements

### 1. Python CLI Framework
**Use Click or Typer for command-line parsing**

```python
# apps/backend/cli/main.py
import click
from cli.commands import (
    install, init, ping, doctor, estimate, stats,
    budget, stream, checkpoint, speak, experiment
)

@click.group()
@click.version_option()
def cli():
    """Auto-Claude CLI - Ralph-enhanced autonomous coding"""
    pass

# Register command groups
cli.add_command(install.install)
cli.add_command(init.init)
cli.add_command(ping.ping)
cli.add_command(doctor.doctor)
cli.add_command(estimate.estimate)
cli.add_command(stats.stats)
cli.add_command(budget.budget)
cli.add_command(stream.stream)
cli.add_command(checkpoint.checkpoint)
cli.add_command(speak.speak)
cli.add_command(experiment.experiment)

if __name__ == "__main__":
    cli()
```

### 2. Reuse Existing Python Modules
**Leverage already-integrated components**

- ✅ `monitoring/cost_tracker.py` → `ac stats`, `ac budget`
- ✅ `monitoring/heartbeat.py` → `ac checkpoint`
- ✅ `integrations/tts/` → `ac speak`, `ac recap`
- ✅ `spec/validate_pkg/scoring/` → `ac review`
- ✅ `cli/worktree.py` → `ac stream`

### 3. Configuration Management
**Centralized config file**

```python
# apps/backend/cli/config.py
from dataclasses import dataclass
from pathlib import Path
import json

@dataclass
class AutoClaudeConfig:
    """Auto-Claude CLI configuration"""
    project_dir: Path
    auto_claude_dir: Path
    spec_template: str = "ralph"
    planner_template: str = "ralph"
    tts_enabled: bool = True
    tts_provider: str = "auto"
    monitoring_enabled: bool = True
    cost_budget_usd: float | None = None
    default_model: str = "claude-sonnet-4-5-20250929"

    @classmethod
    def load(cls, project_dir: Path) -> "AutoClaudeConfig":
        """Load config from .auto-claude-config.json"""
        config_file = project_dir / ".auto-claude-config.json"
        if config_file.exists():
            data = json.loads(config_file.read_text())
            return cls(project_dir=project_dir, **data)
        return cls(project_dir=project_dir)

    def save(self):
        """Save config to .auto-claude-config.json"""
        config_file = self.project_dir / ".auto-claude-config.json"
        config_file.write_text(json.dumps({
            "spec_template": self.spec_template,
            "planner_template": self.planner_template,
            "tts_enabled": self.tts_enabled,
            "tts_provider": self.tts_provider,
            "monitoring_enabled": self.monitoring_enabled,
            "cost_budget_usd": self.cost_budget_usd,
            "default_model": self.default_model,
        }, indent=2))
```

### 4. Cross-Platform Support
**Ensure Windows, macOS, Linux compatibility**

- Use `pathlib.Path` for all path operations
- Use platform-specific abstractions (already in `apps/backend/core/platform/`)
- Test on all three platforms via CI

---

## Command Specifications

### Priority 1: Essential Commands

#### `ac doctor`
```bash
ac doctor [--verbose] [--fix]

# Checks:
- Python version (3.12+)
- Claude CLI installed and authenticated
- uv installed (for backend deps)
- Node.js installed (for frontend)
- Git repository initialized
- .auto-claude directory structure
- Environment variables (.env)
- TTS provider availability

# With --fix:
- Create missing directories
- Generate .env from .env.example
- Run npm install / uv pip install
```

#### `ac stats`
```bash
ac stats [--global] [--json] [--tokens]

# Shows:
- Total specs created
- Total builds run
- Success/failure rate
- Average cost per build
- Token usage by model
- Quality score trends
- Time metrics (avg build time)

# --global: Stats across all projects
# --json: JSON output for scripting
# --tokens: Detailed token breakdown
```

#### `ac budget`
```bash
ac budget set <amount> [--spec=N]    # Set budget limit
ac budget show [--spec=N]            # Show current budget/usage
ac budget clear [--spec=N]           # Remove budget limit

# Features:
- Budget warnings at 80%, 90%
- Hard stop at 100% (configurable)
- Per-spec budget tracking
- Global budget across all specs
```

#### `ac estimate`
```bash
ac estimate [--spec=N] [--json]

# Estimates:
- Input tokens (from spec.md, context.json)
- Expected output tokens (based on plan complexity)
- Cost by model (Sonnet 4.5, Opus 3.5, etc.)
- Time estimate (based on historical data)
- Quality score prediction

# Output format:
{
  "spec_id": "001-auth",
  "estimated_cost_usd": 2.45,
  "estimated_time_hours": 1.5,
  "estimated_tokens": {
    "input": 15000,
    "output": 8000
  },
  "confidence": "medium"
}
```

### Priority 2: Stream Management

#### `ac stream`
```bash
ac stream list                       # List all worktrees
ac stream new <name>                 # Create new spec worktree
ac stream status                     # Show all stream statuses
ac stream build <name> [iterations]  # Run build in worktree
ac stream merge <name>               # Merge to main
ac stream cleanup <name>             # Remove worktree

# Example workflow:
ac stream new auth-feature          # Creates .worktrees/auth-feature
ac stream build auth-feature 5      # Run 5 iterations
ac stream status                    # Check progress
ac stream merge auth-feature        # Merge to main branch
```

### Priority 3: Voice & TTS

#### `ac speak`
```bash
ac speak ["<text>"]                  # Speak text via TTS
ac speak --auto-on                   # Enable auto-speak
ac speak --auto-off                  # Disable auto-speak
ac speak --auto-status               # Check status
ac speak --list-voices               # List available voices
ac speak --set-voice <voice>         # Set default voice
ac speak --engine <piper|macos|sys>  # Set TTS engine

# Examples:
ac speak "Build completed successfully"
ac speak --auto-on                   # Auto-announce phases
```

#### `ac recap`
```bash
ac recap [--full|--short|--preview]

# Summarize last agent response and speak it
# --full: 200 words
# --short: 30 words
# --preview: Show without speaking
```

---

## Integration Points

### 1. Electron Frontend
**Add CLI command palette**

- Add "Command Palette" (Cmd+K / Ctrl+K)
- Execute CLI commands from UI
- Display command output in terminal panel
- Command history and autocomplete

### 2. Environment Variables
**Extend .env.example**

```bash
# CLI Configuration
AC_CLI_ENABLED=true
AC_CLI_COLOR=true
AC_CLI_VERBOSE=false

# Command Defaults
AC_DEFAULT_MODEL=claude-sonnet-4-5-20250929
AC_DEFAULT_ITERATIONS=5
AC_AUTO_COMMIT=true
AC_AUTO_PUSH=false
```

### 3. Configuration File
**Create .auto-claude-config.json**

```json
{
  "cli": {
    "enabled": true,
    "color": true,
    "verbose": false
  },
  "defaults": {
    "model": "claude-sonnet-4-5-20250929",
    "iterations": 5,
    "auto_commit": true
  },
  "budget": {
    "global_limit_usd": 100.0,
    "warning_threshold": 0.8
  },
  "tts": {
    "enabled": true,
    "provider": "piper",
    "voice": "alba",
    "auto_speak": false
  }
}
```

---

## Testing Strategy

### 1. Unit Tests
```bash
# apps/backend/tests/cli/
test_doctor.py          # Test environment checks
test_stats.py           # Test analytics
test_budget.py          # Test budget management
test_stream.py          # Test worktree management
test_estimate.py        # Test cost estimation
```

### 2. Integration Tests
```bash
# End-to-end command workflows
test_init_workflow.py   # ac init → ac doctor → ac ping
test_build_workflow.py  # ac spec → ac plan → ac build
test_stream_workflow.py # ac stream new → build → merge
```

### 3. Cross-Platform Tests
```bash
# CI matrix: ubuntu-latest, macos-latest, windows-latest
pytest tests/cli/ --platform=all
```

---

## Success Criteria

### Must-Have (MVP)
- ✅ `ac doctor` - Environment validation
- ✅ `ac stats` - Performance metrics
- ✅ `ac budget` - Budget management
- ✅ `ac estimate` - Cost estimation
- ✅ `ac stream` - Worktree management
- ✅ `ac speak` - TTS control
- ✅ Shell completions (bash/zsh/fish)

### Nice-to-Have
- ✅ `ac experiment` - A/B testing framework
- ✅ `ac automation` - Slack/GitHub integration
- ✅ `ac routing` - Model routing analytics
- ✅ `ac watch` - File watching
- ✅ `ac diagnose` - Failure pattern detection

### Polish
- ✅ Colored output (rich library)
- ✅ Progress bars (click progress bar)
- ✅ Interactive prompts (questionary)
- ✅ Comprehensive help text
- ✅ Man pages / documentation

---

## Documentation Requirements

### 1. CLI Reference
**Create `CLI_REFERENCE.md`**
- All commands with examples
- Flag reference
- Configuration options
- Common workflows

### 2. Migration Guide
**Create `RALPH_TO_AUTO_CLAUDE.md`**
- Command mapping (ralph → ac)
- Config migration
- Breaking changes
- Feature parity matrix

### 3. Shell Completions
**Generate for bash/zsh/fish**
```bash
ac completions bash > /usr/local/etc/bash_completion.d/ac
ac completions zsh > ~/.zsh/completion/_ac
ac completions fish > ~/.config/fish/completions/ac.fish
```

---

## Deliverables

### Week 1-2: Foundation
- [ ] CLI package structure created
- [ ] Entry point (`ac` command) working
- [ ] Configuration system implemented
- [ ] `ac doctor` command working

### Week 3-4: Core Commands
- [ ] `ac stats` implemented
- [ ] `ac budget` implemented
- [ ] `ac estimate` implemented
- [ ] Tests passing (unit + integration)

### Week 5-6: Stream Management
- [ ] `ac stream` subcommands implemented
- [ ] Integration with existing worktree system
- [ ] Parallel execution support
- [ ] Tests passing

### Week 7-8: Advanced Features
- [ ] `ac experiment` framework
- [ ] `ac routing` analytics
- [ ] `ac diagnose` pattern detection
- [ ] Tests passing

### Week 9-10: Voice & Automation
- [ ] `ac speak` / `ac recap` implemented
- [ ] `ac automation` suite ported
- [ ] Slack/GitHub integrations
- [ ] Tests passing

### Week 11-12: Polish & Documentation
- [ ] Shell completions generated
- [ ] CLI_REFERENCE.md complete
- [ ] Migration guide complete
- [ ] Cross-platform tests passing
- [ ] Release v1.0.0

---

## Next Steps

1. **Review this plan** - Identify any missing commands or requirements
2. **Prioritize commands** - Which ones provide most value first?
3. **Create task breakdown** - Break into implementable subtasks
4. **Set up CLI structure** - Create package and entry point
5. **Begin implementation** - Start with `ac doctor` as proof of concept

---

## Questions to Answer

1. **Command name**: Use `ac` or `autoclauder` or `ralph` or something else?
2. **Backward compatibility**: Keep `python run.py` or migrate entirely to CLI?
3. **Configuration format**: JSON, YAML, or TOML for `.auto-claude-config`?
4. **Shell integration**: Should we create shell functions/aliases for convenience?
5. **Electron integration**: How tightly should CLI integrate with frontend?

---

## Estimated Effort

**Total**: 12 weeks (concurrent with other work)
**Team**: 1-2 developers
**Complexity**: Medium-High

**Risks**:
- Cross-platform compatibility issues
- Ralph feature parity challenges
- Integration complexity with existing Auto-Claude systems

**Mitigation**:
- Test early and often on all platforms
- Start with high-value commands
- Leverage existing Python modules where possible
- Maintain backward compatibility with `python run.py`

---

**Ready to begin implementation? Let's start with Phase 1: Foundation!**
