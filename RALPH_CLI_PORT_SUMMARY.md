# Ralph CLI Command Porting - Quick Reference

**Main Planning Document**: `PORT_RALPH_COMMANDS_PROMPT.md`

---

## What This Plan Covers

Porting 40+ Ralph-CLI terminal commands to Auto-Claude to create a unified, feature-complete CLI experience.

---

## Ralph Commands Identified

### 10 Command Categories

1. **Getting Started** (4 commands)
   - `ralph install`, `init`, `ping`, `help`

2. **Core Workflow** (5 commands)
   - `ralph prd`, `plan`, `build`, `eval`, `improve`
   - ✅ Auto-Claude has: spec_runner.py, run.py
   - ❌ Missing: eval, improve

3. **Stream Management** (7 commands)
   - Parallel execution with worktrees
   - `stream list`, `new`, `status`, `build`, `merge`, `cleanup`
   - ✅ Auto-Claude has: worktree support
   - ❌ Missing: CLI commands

4. **Analytics & Estimation** (8 commands)
   - `estimate`, `stats`, `budget`, `routing`
   - ✅ Auto-Claude has: cost_tracker.py
   - ❌ Missing: CLI commands

5. **Diagnostics & Experimentation** (10 commands)
   - `doctor`, `diagnose`, `experiment`
   - ❌ All missing

6. **Project & Knowledge Management** (7 commands)
   - `registry`, `search`, `import`, `optimize`
   - ❌ All missing

7. **Voice & TTS** (2 commands)
   - `speak`, `recap`
   - ✅ Auto-Claude has: TTS integration
   - ❌ Missing: CLI commands

8. **Executive Automation** (5 commands)
   - `automation slack-report`, `check-blockers`, etc.
   - ❌ All missing

9. **Utilities** (6 commands)
   - `checkpoint`, `watch`, `ui`, `log`, `completions`
   - ✅ Auto-Claude has: UI, checkpoints
   - ❌ Missing: CLI commands

10. **Quality Review** (1 command)
    - `ralph review`
    - ✅ Auto-Claude has: QA reviewer
    - ❌ Missing: CLI command

---

## Implementation Plan

### 12-Week Phased Approach

**Phase 1** (Weeks 1-2): Foundation
- Create CLI package structure
- Entry point (`ac` command)
- Configuration system
- `ac doctor` command

**Phase 2** (Weeks 3-4): Core Commands
- `ac stats`, `budget`, `estimate`

**Phase 3** (Weeks 5-6): Stream Management
- `ac stream` subcommands

**Phase 4** (Weeks 7-8): Advanced Features
- `ac experiment`, `routing`, `diagnose`

**Phase 5** (Weeks 9-10): Voice & Automation
- `ac speak`, `recap`, `automation`

**Phase 6** (Weeks 11-12): Polish
- Shell completions, documentation

---

## Technical Approach

### CLI Framework
```python
# Use Click or Typer
import click

@click.group()
def cli():
    """Auto-Claude CLI - Ralph-enhanced"""
    pass

@cli.command()
def doctor():
    """Environment diagnostics"""
    # Implementation
```

### Reuse Existing Modules
- `monitoring/cost_tracker.py` → `ac stats`, `budget`
- `integrations/tts/` → `ac speak`
- `cli/worktree.py` → `ac stream`
- `spec/validate_pkg/scoring/` → `ac review`

### Configuration
```json
// .auto-claude-config.json
{
  "cli": {
    "enabled": true,
    "color": true
  },
  "defaults": {
    "model": "claude-sonnet-4-5-20250929",
    "iterations": 5
  },
  "budget": {
    "global_limit_usd": 100.0
  }
}
```

---

## Priority Commands (MVP)

**Must-Have**:
1. ✅ `ac doctor` - Environment validation
2. ✅ `ac stats` - Performance metrics
3. ✅ `ac budget` - Budget management
4. ✅ `ac estimate` - Cost estimation
5. ✅ `ac stream` - Worktree management
6. ✅ `ac speak` - TTS control
7. ✅ Shell completions

**Nice-to-Have**:
- `ac experiment` - A/B testing
- `ac automation` - Slack/GitHub integration
- `ac routing` - Model routing analytics
- `ac watch` - File watching
- `ac diagnose` - Failure detection

---

## Example Commands

### Environment Check
```bash
$ ac doctor
✓ Python 3.12.1
✓ Claude CLI authenticated
✓ uv installed
✓ Node.js 20.x
✓ Git repository initialized
✓ .auto-claude directory exists
✓ TTS: Piper available
```

### Budget Management
```bash
$ ac budget set 10.00
Budget set: $10.00 for current spec

$ ac stats
Total specs: 12
Total builds: 47
Success rate: 85%
Average cost: $2.34
Quality score: 82.5/100 (B)
```

### Stream Management
```bash
$ ac stream new auth-feature
Created worktree: .worktrees/auth-feature

$ ac stream build auth-feature 5
Running 5 iterations in auth-feature...
[Progress output]

$ ac stream merge auth-feature
Merged auth-feature to main
```

### Voice Feedback
```bash
$ ac speak "Build completed successfully"
[Speaks via TTS]

$ ac speak --auto-on
Auto-speak enabled for phase announcements

$ ac recap --short
[Speaks 30-word summary of last response]
```

---

## Command Naming Considerations

**Options**:
1. `ac` - Short, memorable (recommended)
2. `autoclauder` - Descriptive but longer
3. `ralph` - Keep Ralph branding
4. `claude-code` - Match Anthropic CLI

**Recommendation**: Use `ac` as primary, with `autoclauder` as alias

---

## Integration with Electron Frontend

### Command Palette
- Add Cmd+K / Ctrl+K command palette
- Execute CLI commands from UI
- Display output in terminal panel
- Command history and autocomplete

### Terminal Integration
- Embedded terminal in Electron
- Run `ac` commands directly in UI
- Syntax highlighting for output
- Interactive prompts in terminal

---

## Next Steps

1. **Review the full plan** → `PORT_RALPH_COMMANDS_PROMPT.md`
2. **Answer key questions**:
   - Command name preference?
   - Backward compatibility approach?
   - Configuration format (JSON/YAML/TOML)?
3. **Create task breakdown** for implementation
4. **Set up CLI package structure**
5. **Implement `ac doctor` as proof of concept**

---

## Files Created

1. `PORT_RALPH_COMMANDS_PROMPT.md` - Comprehensive planning document (400+ lines)
2. `RALPH_CLI_PORT_SUMMARY.md` - This quick reference

---

## Estimated Effort

- **Duration**: 12 weeks
- **Team**: 1-2 developers
- **Complexity**: Medium-High
- **Deliverables**: 40+ commands, tests, documentation

---

**Ready to kick off the implementation!**

Use the prompt in `PORT_RALPH_COMMANDS_PROMPT.md` to plan the detailed implementation with an agent or development team.
