/**
 * TTS (Text-to-Speech) types for Auto Claude frontend
 */

export type TTSProvider = 'piper' | 'macos' | 'system';

/**
 * Voice metadata returned by TTS providers
 */
export interface TTSVoice {
  id: string;
  name: string;
  language: string;
  provider: TTSProvider;
  quality?: string;
  installed: boolean;
  filename?: string;
  metadata?: Record<string, any>;
}

/**
 * TTS manager status information
 */
export interface TTSStatus {
  enabled: boolean;
  activeProvider: string | null;
  activeProviderInfo: string | null;
  availableProviders: string[];
  voiceCounts: Record<string, number>;
  config: {
    maxLength: number;
    announcePhases: boolean;
    announceSubtasks: boolean;
    announceQa: boolean;
    filterCodeBlocks: boolean;
    filterMarkdown: boolean;
    filterFilePaths: boolean;
    filterUrls: boolean;
  };
}

/**
 * Result of listing voices grouped by provider
 */
export interface TTSVoicesByProvider {
  [provider: string]: TTSVoice[];
}

/**
 * IPC result wrapper for TTS operations
 */
export interface TTSResult<T> {
  success: boolean;
  data?: T;
  error?: string;
}
