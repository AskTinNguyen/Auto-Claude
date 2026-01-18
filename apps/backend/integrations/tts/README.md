# TTS (Text-to-Speech) Integration

Voice feedback system for Auto Claude autonomous builds. Provides real-time audio announcements for phase transitions, subtask completions, and QA results.

## Features

- **Multi-provider support** with automatic fallback
  - Piper: High-quality neural TTS
  - macOS: Native `say` command
  - System: Platform-specific fallback (espeak, spd-say, festival)

- **Intelligent output filtering**
  - Removes code blocks, file paths, markdown formatting
  - Filters technical jargon and URLs
  - Preserves meaningful content for clear speech

- **Configurable announcements**
  - Phase transitions (Planning, Implementation, QA)
  - Subtask start and completion
  - QA validation results
  - Error messages

## Installation

### macOS

**Option 1: Native say (built-in)**
```bash
# No installation needed - uses macOS native TTS
# Enable in .env:
TTS_ENABLED=true
TTS_PROVIDER=macos
```

**Option 2: Piper (higher quality)**
```bash
brew install piper-tts

# Enable in .env:
TTS_ENABLED=true
TTS_PROVIDER=piper
```

### Linux

**Option 1: System TTS (espeak)**
```bash
# Ubuntu/Debian
sudo apt-get install espeak-ng

# Fedora
sudo dnf install espeak-ng

# Arch
sudo pacman -S espeak-ng

# Enable in .env:
TTS_ENABLED=true
TTS_PROVIDER=system
```

**Option 2: Piper (higher quality)**
```bash
# Download from GitHub releases
# https://github.com/rhasspy/piper/releases

# Extract and add to PATH
wget https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_amd64.tar.gz
tar -xzf piper_amd64.tar.gz
sudo mv piper /usr/local/bin/

# Enable in .env:
TTS_ENABLED=true
TTS_PROVIDER=piper
```

### Windows

**Option 1: PowerShell (built-in)**
```bash
# No installation needed - uses Windows Speech API
# Enable in .env:
TTS_ENABLED=true
TTS_PROVIDER=system
```

**Option 2: Piper (higher quality)**
```powershell
# Download from GitHub releases
# https://github.com/rhasspy/piper/releases
# Extract and add to PATH

# Enable in .env:
TTS_ENABLED=true
TTS_PROVIDER=piper
```

## Configuration

Add to `apps/backend/.env`:

```bash
# Enable TTS
TTS_ENABLED=true

# Provider (auto, piper, macos, system)
TTS_PROVIDER=auto

# Piper settings (if using piper)
TTS_PIPER_MODEL=en_US-lessac-medium
TTS_PIPER_PATH=/opt/homebrew/bin/piper

# macOS settings (if using macos)
TTS_MACOS_VOICE=Samantha
TTS_MACOS_RATE=200

# Announcement toggles
TTS_ANNOUNCE_PHASES=true
TTS_ANNOUNCE_SUBTASKS=true
TTS_ANNOUNCE_QA=true

# Content filtering
TTS_FILTER_CODE=true
TTS_FILTER_MARKDOWN=true
TTS_FILTER_PATHS=true
TTS_FILTER_URLS=true

# Max speech length
TTS_MAX_LENGTH=500
```

## Usage

### Basic Usage

```python
from integrations.tts import TTSManager, TTSConfig

# Create manager with env config
manager = TTSManager()

# Or create with custom config
config = TTSConfig(
    enabled=True,
    preferred_provider="piper",
    piper_model="en_US-lessac-medium"
)
manager = TTSManager(config)

# Speak arbitrary text
manager.speak("Build completed successfully")

# Speak with filtering
manager.speak("Check file at /path/to/file.py", filter_content=True)
```

### Phase Announcements

```python
# Announce phase transition
manager.speak_phase("Planning", "Creating implementation plan")

# Simple phase announcement
manager.speak_phase("Implementation")
```

### Subtask Announcements

```python
# Announce subtask start
manager.speak_subtask_start("Add user authentication")

# Announce subtask completion
manager.speak_subtask_complete("Add user authentication", success=True)

# Announce subtask failure
manager.speak_subtask_complete("Run tests", success=False)
```

### QA Announcements

```python
# Announce QA pass
manager.speak_qa_result(passed=True)

# Announce QA failure with issue count
manager.speak_qa_result(passed=False, issue_count=3)
```

### Build Status

```python
# Announce build completion
manager.speak_build_complete(success=True)

# Announce build failure
manager.speak_build_complete(success=False)
```

### Error Handling

```python
# Speak error with automatic filtering
manager.speak_error("Failed to import module at /path/to/file.py")
```

### Check Status

```python
# Get TTS status
status = manager.get_status()
print(status['enabled'])              # True/False
print(status['active_provider'])      # "piper", "macos", "system"
print(status['available_providers'])  # ["piper", "macos"]
```

## Content Filtering

The TTS system automatically filters technical content to improve speech clarity:

### What Gets Filtered

- **Code blocks**: Fenced and inline code
- **File paths**: Unix and Windows paths
- **URLs**: http/https links
- **Markdown**: Headers, bold, italic, links
- **Commands**: Shell, npm, git commands
- **Technical patterns**: Imports, function signatures, stack traces

### Example

**Input:**
```
Check file at /Users/name/project/src/main.py for the bug.
Run `npm install` to fix dependencies.
See https://github.com/user/repo for details.
```

**Filtered output (spoken):**
```
Check file for the bug. Run to fix dependencies. See for details.
```

### Customize Filtering

```python
from integrations.tts.filters import OutputFilter

# Create custom filter
filter = OutputFilter(
    filter_code=True,
    filter_markdown=True,
    filter_paths=False,  # Keep file paths
    filter_urls=True
)

# Use filter
filtered_text = filter.filter("Check /path/to/file.py")
print(filtered_text)  # "Check /path/to/file.py"
```

## Testing

```bash
cd apps/backend

# Quick test
python test_tts.py

# Test specific provider
python test_tts.py --provider piper

# Full demo
python test_tts.py --demo

# Test filtering only (no audio)
python test_tts.py --filter-test
```

## Provider Details

### Piper

**Pros:**
- High-quality neural voices
- Fast generation
- Cross-platform
- Multiple voice options

**Cons:**
- Requires separate installation
- Larger binary size (~50MB)

**Voice Models:**
- `en_US-lessac-medium` - Balanced, recommended
- `en_US-amy-medium` - Female, clear
- `en_US-ryan-medium` - Male, deep
- `en_GB-alba-medium` - British accent

### macOS say

**Pros:**
- Built-in, no installation
- Fast and reliable
- Multiple voices available

**Cons:**
- macOS only
- Less natural than neural voices

**Available Voices:**
```bash
# List voices
say -v ?

# Popular voices
# Samantha - Female, clear
# Alex - Male, balanced
# Victoria - Female, professional
# Daniel - Male, British
```

### System Fallback

**Linux:**
- espeak-ng (preferred)
- espeak
- spd-say (speech-dispatcher)
- festival
- flite

**Windows:**
- PowerShell System.Speech

**Pros:**
- Works on most systems
- No extra installation (usually)

**Cons:**
- Lower quality than neural voices
- Platform-dependent availability

## Architecture

```
integrations/tts/
├── __init__.py          # Public API
├── config.py            # Configuration management
├── manager.py           # Main TTS manager
├── filters.py           # Content filtering
└── providers/
    ├── __init__.py      # Provider exports
    ├── piper.py         # Piper neural TTS
    ├── macos.py         # macOS 'say' command
    └── system.py        # Platform fallback
```

### Key Components

**TTSManager** (`manager.py`)
- High-level API for TTS operations
- Provider selection and fallback
- Content filtering integration

**TTSConfig** (`config.py`)
- Environment variable loading
- Provider preferences
- Announcement toggles
- Filter settings

**OutputFilter** (`filters.py`)
- Pattern-based content filtering
- Preserves meaningful content
- Smart truncation at sentence boundaries

**Providers** (`providers/`)
- Piper: Neural TTS with audio file generation
- macOS: Native `say` command wrapper
- System: Platform-specific fallback commands

## Integration with Auto Claude

TTS announcements are integrated into the autonomous build pipeline:

1. **Spec Creation** (spec_runner.py)
   - Phase transitions (Discovery, Requirements, etc.)
   - Spec validation results

2. **Implementation** (run.py)
   - Planning phase start
   - Subtask start/completion
   - Agent transitions

3. **QA Validation** (qa_reviewer.py)
   - QA start announcement
   - QA result (pass/fail with issue count)

4. **QA Fixes** (qa_fixer.py)
   - Fix start/completion
   - Final QA revalidation

### Example Integration

```python
from integrations.tts import get_tts_manager

# Get global TTS manager
tts = get_tts_manager()

# In your agent code
def run_planning_phase():
    tts.speak_phase("Planning", "Creating implementation plan")
    # ... run planning logic ...

def run_subtask(subtask):
    tts.speak_subtask_start(subtask['name'])
    # ... run subtask logic ...
    tts.speak_subtask_complete(subtask['name'], success=True)

def run_qa():
    issues = validate_acceptance_criteria()
    passed = len(issues) == 0
    tts.speak_qa_result(passed, issue_count=len(issues))
```

## Troubleshooting

### No audio output

1. Check if TTS is enabled:
   ```bash
   # In .env
   TTS_ENABLED=true
   ```

2. Test provider manually:
   ```bash
   # macOS
   say "test"

   # Linux
   espeak-ng "test"

   # Piper
   echo "test" | piper --model en_US-lessac-medium --output-raw | aplay
   ```

3. Check provider availability:
   ```python
   python test_tts.py
   ```

### Provider not found

- **Piper**: Install via brew (macOS) or download from GitHub releases
- **macOS say**: Should be built-in (macOS only)
- **espeak**: Install via package manager (Linux)

### Audio quality issues

- Try Piper for best quality: `TTS_PROVIDER=piper`
- Adjust macOS rate: `TTS_MACOS_RATE=175` (slower) or `225` (faster)
- Try different voices: `say -v ?` (macOS) or check Piper models

### Speech too long/truncated

- Increase max length: `TTS_MAX_LENGTH=1000`
- Note: Longer speech may delay the build pipeline

### Too much technical jargon

- Enable all filters:
  ```bash
  TTS_FILTER_CODE=true
  TTS_FILTER_MARKDOWN=true
  TTS_FILTER_PATHS=true
  TTS_FILTER_URLS=true
  ```

## Credits

Adapted from [Ralph-CLI](https://github.com/yourusername/ralph-cli)'s output filtering system with enhancements for autonomous coding workflows.
