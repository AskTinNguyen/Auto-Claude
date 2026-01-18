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
}

export const createTTSAPI = (): TTSAPI => ({
  getStatus: (): Promise<IPCResult<TTSStatus>> =>
    ipcRenderer.invoke(IPC_CHANNELS.TTS_GET_STATUS),

  getVoices: (provider?: TTSProvider): Promise<IPCResult<TTSVoice[]>> =>
    ipcRenderer.invoke(IPC_CHANNELS.TTS_GET_VOICES, provider),

  testVoice: (provider: TTSProvider, voiceId: string, text?: string): Promise<IPCResult<void>> =>
    ipcRenderer.invoke(IPC_CHANNELS.TTS_TEST_VOICE, provider, voiceId, text)
});
