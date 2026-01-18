# Voice Selection Integration - Complete

## Problem Fixed

**Original Issue:** Auto-speak was working but NOT using the selected voice (e.g., Piper Ryan). Instead, it used the default voice from environment variables.

**Root Cause:** Voice selection was stored in the frontend TTS store but not persisted to `voice-config.json`, so the backend couldn't read the user's voice preference.

## Solution Implemented

### Complete Voice Selection Pipeline

#### 1. Frontend Changes

**TTS Store (`apps/frontend/src/renderer/stores/tts-store.ts`)**
- Made `setProvider()` and `setSelectedVoice()` async
- Both now call `saveVoiceConfig()` after updating state
- Added `saveVoiceConfig()` method to persist all TTS settings to voice-config.json
- Updated `loadAutoSpeakConfig()` to restore provider and selectedVoice on app start

**IPC API (`apps/frontend/src/preload/api/tts-api.ts`)**
- Extended `AutoSpeakConfig` interface to include:
  ```typescript
  export interface AutoSpeakConfig {
    enabled: boolean;
    mode: 'short' | 'full';
    provider?: TTSProvider;
    selectedVoice?: string | null;
  }
  ```

**IPC Handlers (`apps/frontend/src/main/ipc-handlers/tts-handlers.ts`)**
- Updated `readAutoSpeakConfig()` to return provider and selectedVoice
- Updated `writeAutoSpeakConfig()` to save voice section:
  ```json
  {
    "autoSpeak": { "enabled": true, "mode": "full" },
    "voice": { "provider": "piper", "selectedVoice": "en_US-ryan-medium" }
  }
  ```

#### 2. Backend Changes

**TTS Config (`apps/backend/integrations/tts/config.py`)**
- Modified `from_env()` to accept `project_dir` parameter
- Reads `.ralph/voice-config.json` and overrides env var defaults
- Maps selectedVoice to provider-specific settings:
  - Piper: `piper_model = "en_US-ryan-medium"`
  - macOS: `macos_voice = "Ryan"`

**TTS Manager (`apps/backend/integrations/tts/manager.py`)**
- Updated `__init__()` to accept `project_dir` parameter
- Passes `project_dir` to `TTSConfig.from_env()`
- Updated `get_tts_manager()` to forward `project_dir`

## Configuration Structure

**`.ralph/voice-config.json`** (complete structure):
```json
{
  "autoSpeak": {
    "enabled": true,
    "mode": "full"
  },
  "voice": {
    "provider": "piper",
    "selectedVoice": "en_US-ryan-medium"
  }
}
```

## How It Works

1. **User selects voice in UI** (Settings → TTS)
   - Frontend calls `setProvider()` or `setSelectedVoice()`
   - Store updates state AND calls `saveVoiceConfig()`
   - IPC handler writes to `.ralph/voice-config.json`

2. **Backend reads configuration on init**
   - TTS manager initialized with `project_dir`
   - TTSConfig reads env vars first (defaults)
   - Then reads voice-config.json (overrides)
   - Selected voice applied to provider settings

3. **Auto-speak uses selected voice**
   - Agent announces phases/subtasks
   - TTS manager uses active provider with selected voice
   - Announcements use Piper Ryan (or whatever voice was selected)

## Testing Results

**Backend Integration Test** (`apps/backend/test_voice_config.py`):
```
✅ TTS enabled correctly (from .env)
✅ Preferred provider set to 'piper'
✅ Piper model set to 'en_US-ryan-medium'
✅ Active provider is 'piper' with correct voice
```

## User Testing Steps

1. **Restart Electron app** (to apply changes):
   ```bash
   npm run dev
   ```

2. **Select voice in UI**:
   - Open Settings → Text-To-Speech
   - Select "Piper" as provider
   - Select "Ryan" voice
   - Settings should auto-save

3. **Verify configuration**:
   ```bash
   cat .ralph/voice-config.json
   # Should show both autoSpeak and voice sections
   ```

4. **Test auto-speak**:
   - Run a spec with auto-speak enabled
   - Verify announcements use Piper Ryan voice
   - Try different voices to confirm they work

## Files Changed

### Frontend
- `apps/frontend/src/renderer/stores/tts-store.ts`
- `apps/frontend/src/preload/api/tts-api.ts`
- `apps/frontend/src/main/ipc-handlers/tts-handlers.ts`
- `apps/frontend/src/shared/types/ipc.ts`

### Backend
- `apps/backend/integrations/tts/config.py`
- `apps/backend/integrations/tts/manager.py`

### Testing
- `apps/backend/test_voice_config.py` (new)
- `.ralph/voice-config.json` (updated structure)

## Next Steps

The integration is complete and tested. The user should:

1. Restart the Electron app
2. Select their preferred voice in Settings → TTS
3. Test auto-speak to confirm it uses the selected voice
4. Report any issues

## Notes

- Voice settings persist across app restarts
- Changing voice in UI immediately saves to config
- Backend reads config on each TTS manager initialization
- Provider-specific voice formats handled automatically:
  - Piper: full model name (e.g., "en_US-ryan-medium")
  - macOS: voice name only (e.g., "Ryan")
