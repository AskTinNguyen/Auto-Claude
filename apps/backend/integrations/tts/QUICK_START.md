# TTS Quick Start Guide

Get voice feedback for Auto Claude builds in 60 seconds.

## 1. Install TTS Provider (Choose One)

### macOS - Use Built-in Say
```bash
# Nothing to install! macOS 'say' is built-in
```

### macOS - Use Piper (Better Quality)
```bash
brew install piper-tts
```

### Linux - Use espeak
```bash
# Ubuntu/Debian
sudo apt-get install espeak-ng

# Fedora
sudo dnf install espeak-ng

# Arch
sudo pacman -S espeak-ng
```

## 2. Enable TTS

Add to `apps/backend/.env`:

```bash
TTS_ENABLED=true
TTS_PROVIDER=auto
```

## 3. Test It

```bash
cd apps/backend
python test_tts.py
```

You should hear: "TTS integration is working correctly."

## 4. Run a Build

```bash
cd apps/backend
python run.py --spec 001
```

You'll hear announcements for:
- Phase transitions ("Starting Planning Phase")
- Subtask completions ("Completed: Add user authentication")
- QA results ("Quality assurance passed")

## Advanced Configuration

### Use Specific Provider

```bash
# Force Piper
TTS_PROVIDER=piper

# Force macOS say
TTS_PROVIDER=macos

# Force system fallback
TTS_PROVIDER=system
```

### Customize Voice (macOS)

```bash
# List available voices
say -v ?

# Use a different voice
TTS_MACOS_VOICE=Alex        # Male voice
TTS_MACOS_VOICE=Victoria    # Female professional
TTS_MACOS_VOICE=Daniel      # British male
```

### Customize Voice (Piper)

```bash
# Use different model
TTS_PIPER_MODEL=en_US-amy-medium    # Female, clear
TTS_PIPER_MODEL=en_US-ryan-medium   # Male, deep
TTS_PIPER_MODEL=en_GB-alba-medium   # British accent
```

### Adjust Speaking Rate (macOS)

```bash
TTS_MACOS_RATE=175    # Slower, relaxed
TTS_MACOS_RATE=200    # Normal (default)
TTS_MACOS_RATE=225    # Faster, brisk
```

### Selective Announcements

```bash
# Only announce QA results
TTS_ANNOUNCE_PHASES=false
TTS_ANNOUNCE_SUBTASKS=false
TTS_ANNOUNCE_QA=true
```

### Disable Filtering

```bash
# Hear everything (including file paths, code)
TTS_FILTER_CODE=false
TTS_FILTER_MARKDOWN=false
TTS_FILTER_PATHS=false
TTS_FILTER_URLS=false
```

## Troubleshooting

### No Audio Output

1. Check if enabled:
   ```bash
   grep TTS_ENABLED apps/backend/.env
   ```

2. Test provider manually:
   ```bash
   # macOS
   say "test"

   # Linux
   espeak-ng "test"
   ```

3. Check status:
   ```bash
   cd apps/backend
   python test_tts.py
   ```

### Provider Not Available

**Piper:**
```bash
# macOS
brew install piper-tts

# Verify
which piper
```

**espeak (Linux):**
```bash
# Ubuntu
sudo apt-get install espeak-ng

# Verify
which espeak-ng
```

### Too Much/Too Little Speech

```bash
# Increase max length
TTS_MAX_LENGTH=1000

# Decrease max length
TTS_MAX_LENGTH=200
```

## Full Demo

```bash
cd apps/backend

# Run comprehensive demo
python test_tts.py --demo
```

This tests:
- Basic speech
- Phase announcements
- Subtask announcements
- QA results
- Error handling
- Content filtering

## Code Examples

### Basic Usage

```python
from integrations.tts import get_tts_manager

tts = get_tts_manager()
tts.speak("Build started")
```

### In Agent Code

```python
from integrations.tts import get_tts_manager

tts = get_tts_manager()

# Phase transition
tts.speak_phase("Planning", "Creating implementation plan")

# Subtask
tts.speak_subtask_start("Add user authentication")
# ... do work ...
tts.speak_subtask_complete("Add user authentication", success=True)

# QA
issues = validate()
tts.speak_qa_result(passed=len(issues)==0, issue_count=len(issues))

# Build complete
tts.speak_build_complete(success=True)
```

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `TTS_ENABLED` | `false` | Enable TTS |
| `TTS_PROVIDER` | `auto` | Provider: auto, piper, macos, system |
| `TTS_PIPER_MODEL` | `en_US-lessac-medium` | Piper voice model |
| `TTS_PIPER_PATH` | (auto-detect) | Piper executable path |
| `TTS_MACOS_VOICE` | `Samantha` | macOS voice name |
| `TTS_MACOS_RATE` | `200` | macOS speaking rate (wpm) |
| `TTS_ANNOUNCE_PHASES` | `true` | Announce phase transitions |
| `TTS_ANNOUNCE_SUBTASKS` | `true` | Announce subtask events |
| `TTS_ANNOUNCE_QA` | `true` | Announce QA results |
| `TTS_FILTER_CODE` | `true` | Filter code blocks |
| `TTS_FILTER_MARKDOWN` | `true` | Filter markdown |
| `TTS_FILTER_PATHS` | `true` | Filter file paths |
| `TTS_FILTER_URLS` | `true` | Filter URLs |
| `TTS_MAX_LENGTH` | `500` | Max speech length (chars) |

## See Also

- [README.md](README.md) - Full documentation
- [test_tts.py](../../test_tts.py) - Test script
- [.env.example](../../.env.example) - Example configuration
