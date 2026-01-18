import { ipcMain } from 'electron';
import type { BrowserWindow } from 'electron';
import { IPC_CHANNELS } from '../../shared/constants';
import type { IPCResult, TTSVoice, TTSStatus, TTSVoicesByProvider, TTSProvider } from '../../shared/types';
import { spawn } from 'child_process';
import path from 'path';
import { app } from 'electron';
import { debugError, debugLog } from '../../shared/utils/debug-logger';
import fs from 'fs/promises';
import { existsSync } from 'fs';

/**
 * Get the path to the Python backend
 */
function getPythonBackendPath(): string {
  // In development: apps/backend
  // In production: resources/app.asar.unpacked/apps/backend (if bundled)
  const isDev = !app.isPackaged;

  if (isDev) {
    // Development mode
    return path.join(app.getAppPath(), '..', '..', 'apps', 'backend');
  } else {
    // Production mode
    return path.join(process.resourcesPath, 'apps', 'backend');
  }
}

/**
 * Execute TTS IPC bridge command and parse JSON result
 */
async function executeTTSCommand(args: string[]): Promise<any> {
  return new Promise((resolve, reject) => {
    const backendPath = getPythonBackendPath();
    const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';

    debugLog('[TTS-IPC] Executing:', pythonCmd, ['-m', 'integrations.tts.ipc_bridge', ...args]);

    const child = spawn(pythonCmd, ['-m', 'integrations.tts.ipc_bridge', ...args], {
      cwd: backendPath,
      env: { ...process.env },
    });

    let stdout = '';
    let stderr = '';

    child.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    child.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    child.on('close', (code) => {
      if (code !== 0) {
        debugError('[TTS-IPC] Command failed with code', code);
        debugError('[TTS-IPC] stderr:', stderr);
        reject(new Error(`TTS command failed: ${stderr || 'Unknown error'}`));
        return;
      }

      try {
        const result = JSON.parse(stdout);
        resolve(result);
      } catch (error) {
        debugError('[TTS-IPC] Failed to parse JSON:', stdout);
        reject(new Error(`Failed to parse TTS response: ${error}`));
      }
    });

    child.on('error', (error) => {
      debugError('[TTS-IPC] Spawn error:', error);
      reject(new Error(`Failed to spawn TTS process: ${error.message}`));
    });
  });
}

/**
 * Convert snake_case to camelCase for JavaScript
 */
function toCamelCase(obj: any): any {
  if (Array.isArray(obj)) {
    return obj.map(toCamelCase);
  } else if (obj !== null && typeof obj === 'object') {
    return Object.keys(obj).reduce((result, key) => {
      const camelKey = key.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
      result[camelKey] = toCamelCase(obj[key]);
      return result;
    }, {} as any);
  }
  return obj;
}

/**
 * Get the path to the voice-config.json file
 */
function getVoiceConfigPath(): string {
  const isDev = !app.isPackaged;
  let projectRoot: string;

  if (isDev) {
    // Development: go up from apps/frontend to project root
    projectRoot = path.join(app.getAppPath(), '..', '..');
  } else {
    // Production: assume config is in resources
    projectRoot = process.resourcesPath;
  }

  return path.join(projectRoot, '.ralph', 'voice-config.json');
}

/**
 * Read auto-speak configuration from voice-config.json
 */
async function readAutoSpeakConfig(): Promise<{ enabled: boolean; mode: 'short' | 'full'; provider?: string; selectedVoice?: string | null }> {
  const configPath = getVoiceConfigPath();

  // Default config
  const defaultConfig = { enabled: false, mode: 'short' as const, provider: undefined, selectedVoice: undefined };

  try {
    if (!existsSync(configPath)) {
      return defaultConfig;
    }

    const content = await fs.readFile(configPath, 'utf-8');
    const config = JSON.parse(content);

    return {
      enabled: config.autoSpeak?.enabled ?? defaultConfig.enabled,
      mode: config.autoSpeak?.mode ?? defaultConfig.mode,
      provider: config.voice?.provider,
      selectedVoice: config.voice?.selectedVoice
    };
  } catch (error) {
    debugError('[TTS-IPC] Failed to read voice-config.json:', error);
    return defaultConfig;
  }
}

/**
 * Write auto-speak configuration to voice-config.json
 */
async function writeAutoSpeakConfig(enabled: boolean, mode: 'short' | 'full', provider?: string, selectedVoice?: string | null): Promise<void> {
  const configPath = getVoiceConfigPath();
  const configDir = path.dirname(configPath);

  try {
    // Ensure .ralph directory exists
    if (!existsSync(configDir)) {
      await fs.mkdir(configDir, { recursive: true });
    }

    // Read existing config or create new one
    let config: any = {};
    if (existsSync(configPath)) {
      const content = await fs.readFile(configPath, 'utf-8');
      config = JSON.parse(content);
    }

    // Update autoSpeak section
    config.autoSpeak = { enabled, mode };

    // Update voice section if provider/selectedVoice provided
    if (provider !== undefined || selectedVoice !== undefined) {
      config.voice = config.voice || {};
      if (provider !== undefined) {
        config.voice.provider = provider;
      }
      if (selectedVoice !== undefined) {
        config.voice.selectedVoice = selectedVoice;
      }
    }

    // Write back to file
    await fs.writeFile(configPath, JSON.stringify(config, null, 2), 'utf-8');
    debugLog('[TTS-IPC] Updated voice-config.json:', config);
  } catch (error) {
    debugError('[TTS-IPC] Failed to write voice-config.json:', error);
    throw error;
  }
}

/**
 * Register all TTS-related IPC handlers
 */
export function registerTTSHandlers(
  _getMainWindow: () => BrowserWindow | null
): void {
  // ============================================
  // TTS Status
  // ============================================

  ipcMain.handle(IPC_CHANNELS.TTS_GET_STATUS, async (): Promise<IPCResult<TTSStatus>> => {
    try {
      debugLog('[TTS-IPC] Getting TTS status');

      const result = await executeTTSCommand(['get-status']);

      if (!result.success) {
        return {
          success: false,
          error: result.error || 'Failed to get TTS status'
        };
      }

      // Convert snake_case to camelCase
      const status = toCamelCase(result.status) as TTSStatus;

      return {
        success: true,
        data: status
      };
    } catch (error) {
      debugError('[TTS-IPC] Error getting status:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  });

  // ============================================
  // List Voices
  // ============================================

  ipcMain.handle(
    IPC_CHANNELS.TTS_GET_VOICES,
    async (_, provider?: TTSProvider): Promise<IPCResult<TTSVoice[]>> => {
      try {
        debugLog('[TTS-IPC] Getting voices for provider:', provider || 'all');

        const args = ['list-voices'];
        if (provider) {
          args.push('--provider', provider);
        }

        const result = await executeTTSCommand(args);

        if (!result.success) {
          return {
            success: false,
            error: result.error || 'Failed to list voices'
          };
        }

        // Extract voices for the specified provider (or all providers)
        const voicesByProvider: TTSVoicesByProvider = toCamelCase(result.voices);

        // Flatten to array if single provider requested
        let voices: TTSVoice[] = [];
        if (provider && voicesByProvider[provider]) {
          voices = voicesByProvider[provider];
        } else {
          // Return all voices from all providers
          voices = Object.values(voicesByProvider).flat();
        }

        debugLog(`[TTS-IPC] Found ${voices.length} voices`);

        return {
          success: true,
          data: voices
        };
      } catch (error) {
        debugError('[TTS-IPC] Error listing voices:', error);
        return {
          success: false,
          error: error instanceof Error ? error.message : 'Unknown error'
        };
      }
    }
  );

  // ============================================
  // Test Voice
  // ============================================

  ipcMain.handle(
    IPC_CHANNELS.TTS_TEST_VOICE,
    async (_, provider: TTSProvider, voiceId: string, text?: string): Promise<IPCResult<void>> => {
      try {
        debugLog('[TTS-IPC] Testing voice:', voiceId, 'provider:', provider);

        const args = ['test-voice', '--provider', provider, '--voice', voiceId];
        if (text) {
          args.push('--text', text);
        }

        const result = await executeTTSCommand(args);

        if (!result.success) {
          return {
            success: false,
            error: result.error || 'Failed to test voice'
          };
        }

        debugLog('[TTS-IPC] Voice test completed successfully');

        return {
          success: true
        };
      } catch (error) {
        debugError('[TTS-IPC] Error testing voice:', error);
        return {
          success: false,
          error: error instanceof Error ? error.message : 'Unknown error'
        };
      }
    }
  );

  // ============================================
  // Get Auto-Speak Config
  // ============================================

  ipcMain.handle(
    IPC_CHANNELS.TTS_GET_AUTOSPEAK,
    async (): Promise<IPCResult<{ enabled: boolean; mode: 'short' | 'full'; provider?: string; selectedVoice?: string | null }>> => {
      try {
        debugLog('[TTS-IPC] Getting auto-speak config');

        const config = await readAutoSpeakConfig();

        return {
          success: true,
          data: config
        };
      } catch (error) {
        debugError('[TTS-IPC] Error getting auto-speak config:', error);
        return {
          success: false,
          error: error instanceof Error ? error.message : 'Unknown error'
        };
      }
    }
  );

  // ============================================
  // Set Auto-Speak Config
  // ============================================

  ipcMain.handle(
    IPC_CHANNELS.TTS_SET_AUTOSPEAK,
    async (_, enabled: boolean, mode: 'short' | 'full', provider?: string, selectedVoice?: string | null): Promise<IPCResult<void>> => {
      try {
        debugLog('[TTS-IPC] Setting auto-speak config:', { enabled, mode, provider, selectedVoice });

        await writeAutoSpeakConfig(enabled, mode, provider, selectedVoice);

        return {
          success: true
        };
      } catch (error) {
        debugError('[TTS-IPC] Error setting auto-speak config:', error);
        return {
          success: false,
          error: error instanceof Error ? error.message : 'Unknown error'
        };
      }
    }
  );

  debugLog('[TTS-IPC] TTS handlers registered');
}
