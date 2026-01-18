# TTS AI Summarization

Auto-Claude now features AI-powered TTS summarization using Ollama, ported from Ralph CLI's sophisticated TTS system.

## Overview

Instead of simple character-based truncation, Auto-Claude now uses:

1. **Adaptive Mode Detection** - Automatically chooses summarization length based on response complexity
2. **AI-Powered Summarization** - Uses local Ollama (Qwen 2.5:1.5b) for context-aware summarization
3. **Aggressive Cleanup** - Removes symbols, technical jargon, and repetitive sentences
4. **Fallback Mechanism** - Gracefully falls back to regex-based cleanup when Ollama unavailable

## Features

### 1. Adaptive Modes

Three modes based on response complexity (0-100 score):

| Mode | Max Chars | Max Tokens | Word Count | Use Case |
|------|-----------|------------|------------|----------|
| **short** | 150 | 150 | ~30 words | Simple, brief responses (score 0-25) |
| **medium** | 500 | 250 | ~60 words | Multi-paragraph explanations (score 26-55) |
| **full** | 700 | 300 | ~90 words | Complex, structured content (score 56-100) |

### 2. Complexity Scoring

Automatic complexity detection based on:

- **Base score** from length (0-30 points)
- **Structure complexity**: paragraphs, headings, nesting (0-25 points)
- **List/table density** (0-25 points)
- **Code density** (0-15 points)
- **Sentence complexity** (0-10 points)
- **Pattern bonus**: PRD elements like US-XXX, Week/Phase (0-35 points)

### 3. AI Summarization

Uses Ollama for intelligent summarization with:

- **Context awareness** - Considers the user's original question
- **Language detection** - Supports Vietnamese and English
- **Temperature control** - Low temperature (0.2) for focused, consistent output
- **Repetition penalties** - Prevents redundant phrasing
- **Stop sequences** - Stops at meta-text like "Summary:", "Note:"

### 4. Aggressive Cleanup

Removes TTS-unfriendly content:

**Symbols**: `~ / \ | @ # $ % ^ & * \` < > { } [ ] = + _`

**Technical terms**:
- File paths: `~/.agents/ralph/`, `src/components/`
- File extensions: `.js`, `.py`, `.json`, `.md`
- Abbreviations: API, CLI, TTS, JSON, HTTP
- Technical references: "the file", "the script", "the function"

**Repetition**:
- Detects sentences with >25% word overlap (Jaccard similarity)
- Example: "Modified the config. Updated the config. Changed the config." → "Modified the config."

**Emojis**: All emoji characters removed

## Configuration

### Environment Variables

```bash
# Enable AI summarization (default: true)
TTS_ENABLE_AI_SUMMARIZATION=true

# Summarization mode (adaptive, short, medium, full)
TTS_SUMMARIZATION_MODE=adaptive

# Fallback mode if adaptive detection fails
TTS_FALLBACK_MODE=short

# Ollama configuration
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:1.5b
```

### In Code

```python
from integrations.tts import TTSManager, TTSConfig

# Create config with AI summarization
config = TTSConfig(
    enabled=True,
    enable_ai_summarization=True,
    summarization_mode="adaptive",
    fallback_mode="short",
    ollama_url="http://localhost:11434",
    ollama_model="qwen2.5:1.5b"
)

manager = TTSManager(config)

# Speak with context-aware summarization
manager.speak(
    text="Long response from Claude...",
    user_question="What did you implement?"  # Optional context
)
```

## How It Works

### Pipeline

```
Input Text
    ↓
Output Filter (basic filtering)
    ↓
[AI Summarization Enabled?]
    ↓ Yes                      ↓ No (Legacy)
Adaptive Mode Detection    Basic truncation
    ↓
AI Summarization (Ollama)
    ↓ (on error)
Fallback Summarization
    ↓
Aggressive Cleanup
    ↓
Truncate to Max Length
    ↓
Speak
```

### Mode Detection Example

**Input**: Complex PRD with user stories, tables, code blocks

**Analysis**:
- char_count: 2500 → 25 points
- paragraphs: 8 → 10 points (capped)
- headings: 5 → 10 points (capped)
- list_items: 15 → 15 points (capped)
- code_blocks: 2 → 10 points
- table_rows: 5 → 7 points
- user_stories: 5 → +20 bonus
- weeks/phases: 3 → +15 bonus

**Total Score**: 77 + 35 = 112 (capped at 100)

**Mode**: **full** (score 56-100)

## Testing

Run the comprehensive test suite:

```bash
python3 apps/backend/test_tts_summarization.py
```

Tests include:
- ✅ Cleanup function (symbols, technical terms, repetition)
- ✅ Adaptive mode detection (short/medium/full)
- ✅ Truncation at sentence boundaries
- ✅ Fallback summarization (when Ollama unavailable)
- ✅ Full pipeline integration

## Performance

**Mode Detection**: ~1-5ms (regex-based, very fast)

**AI Summarization**:
- short mode: ~5-10s (150 tokens)
- medium mode: ~8-12s (250 tokens)
- full mode: ~10-15s (300 tokens)

**Fallback**: <1ms (regex-based cleanup)

## Comparison: Before vs After

### Before (Simple Truncation)

- Fixed 500 character limit
- Truncates at sentence boundary
- Basic filtering (removes code, markdown)
- No context awareness
- No AI understanding

**Example**:
```
Input (800 chars): "I've updated the voice-config.json file in ~/.agents/ralph/..."
Output (500 chars): "I've updated the voice-config.json file in ~/.agents/ralph/... [truncated mid-sentence]"
```

### After (AI Summarization)

- Adaptive length (150-700 chars based on complexity)
- AI-powered summarization with context
- Aggressive cleanup (symbols, tech jargon, repetition)
- Language detection
- Fallback to regex cleanup

**Example**:
```
Input (800 chars): "I've updated the voice-config.json file in ~/.agents/ralph/..."
Output (150 chars): "Changed the voice settings to use a quieter tone and enabled auto-speak mode for build notifications."
```

## Migration Guide

### Upgrading from Legacy Truncation

**No breaking changes!** The new system is backward-compatible.

1. **Default behavior**: AI summarization enabled with adaptive mode
2. **Disable AI**: Set `TTS_ENABLE_AI_SUMMARIZATION=false` to use legacy truncation
3. **Fixed mode**: Set `TTS_SUMMARIZATION_MODE=short` instead of `adaptive`

### Ollama Setup

1. Install Ollama: https://ollama.ai/download
2. Pull the model: `ollama pull qwen2.5:1.5b`
3. Verify running: `curl http://localhost:11434/api/tags`

If Ollama is unavailable, the system automatically falls back to regex-based cleanup.

## Troubleshooting

### "No output produced"

**Cause**: Text filtered to empty after cleanup

**Solution**: Disable aggressive filtering with `TTS_ENABLE_AI_SUMMARIZATION=false`

### "Timeout waiting for Ollama"

**Cause**: Ollama not running or slow response

**Solution**:
- Start Ollama: `ollama serve`
- Increase timeout in `summarizer.py` (default: 10-15s)
- Use fallback mode: Will auto-fallback on timeout

### "Wrong mode detected"

**Cause**: Complexity score near threshold boundary

**Solution**: Use fixed mode instead of adaptive:
```bash
TTS_SUMMARIZATION_MODE=medium  # Force medium mode
```

## Credits

Ported from Ralph CLI's sophisticated TTS system (`summarize-for-tts.mjs` and `tts-modes.mjs`).

Key improvements adapted:
- ✅ Adaptive mode detection with complexity scoring
- ✅ Context-aware AI summarization
- ✅ Aggressive cleanup logic
- ✅ Repetitive sentence detection
- ✅ Language detection for Vietnamese/English
