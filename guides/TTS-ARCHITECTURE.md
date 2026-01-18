# TTS Architecture Overview

Auto-Claude has **two separate TTS systems** that serve different purposes.

---

## 1. Auto-Claude Agent TTS (Python)

**Purpose**: Voice feedback during autonomous builds (subtask announcements, phase changes, QA results)

**Location**: `apps/backend/integrations/tts/`

```
integrations/tts/
├── config.py          # TTSConfig - reads from env vars + .ralph/voice-config.json
├── manager.py         # TTSManager - orchestrates providers, speak_subtask_start(), etc.
├── filter.py          # Filters code blocks, markdown, URLs from speech
├── voice_info.py      # VoiceInfo dataclass
├── ipc_bridge.py      # JSON CLI for Electron IPC (list-voices, test-voice)
└── providers/
    ├── piper.py       # Piper neural TTS (cross-platform)
    ├── macos.py       # macOS `say` command
    └── system.py      # System fallback
```

**Config Sources** (priority order):
1. Environment variables (`TTS_ENABLED`, `TTS_PROVIDER`, `TTS_PIPER_MODEL`, etc.)
2. `<project>/.ralph/voice-config.json` (set by Electron UI)

**Key Functions**:
- `get_tts_manager(project_dir=...)` - Get/create TTS manager instance
- `tts_manager.speak_subtask_start(name)` - "Working on: ..."
- `tts_manager.speak_subtask_complete(name)` - "Completed: ..."
- `tts_manager.speak_phase(phase, message)` - Phase announcements
- `tts_manager.speak_qa_result(passed)` - QA pass/fail

**Used By**:
- `agents/coder.py` - Subtask announcements
- `agents/session.py` - Completion announcements
- `qa/reviewer.py`, `qa/fixer.py`, `qa/loop.py` - QA announcements

**Worktree Handling**:
Config always reads from **original project root**, not worktree (fixed in `_get_original_project_root()`).

---

## 2. Claude Code Hook TTS (Node.js)

**Purpose**: Speak Claude's responses after each turn in Claude Code CLI

**Location**: `~/.claude-auto-speak/`

```
~/.claude-auto-speak/
├── config.json        # Main config (ttsEngine, piperVoice, voice, etc.)
├── bin/speak          # Node.js TTS wrapper script
├── lib/
│   ├── config.mjs     # Config loader
│   ├── tts-manager.sh # Bash TTS coordination (locks, cancellation)
│   └── summarize.mjs  # LLM summarization of responses
└── hooks/
    ├── stop-hook.sh   # Triggered on Claude Code "Stop" event
    └── prompt-ack-hook.sh  # Acknowledgment on prompt submit
```

**Config**: `~/.claude-auto-speak/config.json`
```json
{
  "enabled": true,
  "ttsEngine": "piper",
  "piperPath": "/path/to/piper",
  "piperVoice": "/path/to/voice.onnx",
  "voice": "Samantha",  // for macOS
  "multilingual": { "voiceByLanguage": { "en": "en_US-ryan-medium" } }
}
```

**Hook Registration**: `~/.claude/settings.local.json`
```json
{
  "hooks": {
    "Stop": [{ "hooks": [{ "type": "command", "command": "...stop-hook.sh" }] }]
  }
}
```

---

## 3. Config Sync Between Systems

The **Electron UI** writes to both configs when voice settings change:

```
Electron UI (Settings → TTS)
       │
       ├──► .ralph/voice-config.json     (Auto-Claude Agent TTS)
       │
       └──► ~/.claude-auto-speak/config.json  (Claude Code Hook TTS)
```

**Sync Logic**: `apps/frontend/src/main/ipc-handlers/tts-handlers.ts`
- `writeAutoSpeakConfig()` - Writes to `.ralph/voice-config.json`
- `syncToClaudeAutoSpeak()` - Syncs to `~/.claude-auto-speak/config.json`

---

## 4. Voice ID Format

**Piper voices** use full model name as ID: `en_US-ryan-medium`

This matches Piper's `--model` argument requirement.

**Backward compatibility**: Old short names (`ryan`) are resolved to full names via `_resolve_piper_voice_name()`.

---

## 5. Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Default voice used | Config not found or wrong path | Check `.ralph/voice-config.json` exists with correct `selectedVoice` |
| TTS loop | Build retry loop (e.g., OAuth revoked) | Fix underlying error, run `claude /login` |
| No sound | Piper binary broken | Update `piperPath` in config to working binary |
| Worktree uses wrong voice | Old bug (fixed) | Config now reads from original project root |

---

## 6. Testing

```bash
# Test Auto-Claude TTS
cd apps/backend
python3 -c "
from integrations.tts.manager import get_tts_manager
from pathlib import Path
mgr = get_tts_manager(project_dir=Path('/path/to/project'))
mgr.speak('Hello from Auto-Claude TTS')
"

# Test Claude Code hook TTS
echo "Hello from Claude hook" | node ~/.claude-auto-speak/bin/speak

# Test Piper directly
echo "Hello" | piper --model ~/.local/share/piper-voices/en_US-ryan-medium.onnx --output-raw | aplay
```
