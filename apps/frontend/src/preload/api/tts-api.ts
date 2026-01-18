import { ipcRenderer } from 'electron';
import { IPC_CHANNELS } from '../../shared/constants';
import type { IPCResult, TTSVoice, TTSStatus, TTSProvider } from '../../shared/types';

/**
 * TTS (Text-to-Speech) API
 *
 * Provides methods for renderer process to interact with TTS features:
 * - Get TTS status
 * - List available voices
 * - Test voices
 */
export interface AutoSpeakConfig {
  enabled: boolean;
  mode: 'short' | 'full';
  provider?: TTSProvider;
  selectedVoice?: string | null;
}

export interface TTSAPI {
  /**
   * Get TTS manager status
   * Returns information about enabled state, active provider, and configuration
   */
  getStatus: () => Promise<IPCResult<TTSStatus>>;

  /**
   * Get available voices for a provider
   * @param provider - Optional provider to filter by (piper, macos, system)
   * @returns List of available voices
   */
  getVoices: (provider?: TTSProvider) => Promise<IPCResult<TTSVoice[]>>;

  /**
   * Test a voice by speaking text
   * @param provider - TTS provider (piper, macos, system)
   * @param voiceId - Voice identifier
   * @param text - Optional text to speak (defaults to test message)
   */
  testVoice: (provider: TTSProvider, voiceId: string, text?: string) => Promise<IPCResult<void>>;

  /**
   * Get Ralph auto-speak configuration
   * Returns whether auto-speak is enabled and the mode (short/full)
   */
  getAutoSpeakConfig: () => Promise<IPCResult<AutoSpeakConfig>>;

  /**
   * Set Ralph auto-speak configuration
   * @param enabled - Whether auto-speak is enabled
   * @param mode - Auto-speak mode (short or full announcements)
   * @param provider - Optional TTS provider
   * @param selectedVoice - Optional selected voice ID
   */
  setAutoSpeak: (enabled: boolean, mode: 'short' | 'full', provider?: TTSProvider, selectedVoice?: string | null) => Promise<IPCResult<void>>;
}

export const createTTSAPI = (): TTSAPI => ({
  getStatus: (): Promise<IPCResult<TTSStatus>> =>
    ipcRenderer.invoke(IPC_CHANNELS.TTS_GET_STATUS),

  getVoices: (provider?: TTSProvider): Promise<IPCResult<TTSVoice[]>> =>
    ipcRenderer.invoke(IPC_CHANNELS.TTS_GET_VOICES, provider),

  testVoice: (provider: TTSProvider, voiceId: string, text?: string): Promise<IPCResult<void>> =>
    ipcRenderer.invoke(IPC_CHANNELS.TTS_TEST_VOICE, provider, voiceId, text),

  getAutoSpeakConfig: (): Promise<IPCResult<AutoSpeakConfig>> =>
    ipcRenderer.invoke(IPC_CHANNELS.TTS_GET_AUTOSPEAK),

  setAutoSpeak: (enabled: boolean, mode: 'short' | 'full', provider?: TTSProvider, selectedVoice?: string | null): Promise<IPCResult<void>> =>
    ipcRenderer.invoke(IPC_CHANNELS.TTS_SET_AUTOSPEAK, enabled, mode, provider, selectedVoice)
});
