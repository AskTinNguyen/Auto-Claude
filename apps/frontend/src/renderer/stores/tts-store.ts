import { create } from 'zustand';
import type { TTSProvider, TTSVoice } from '../../shared/types';

export type { TTSProvider, TTSVoice };

interface TTSState {
  enabled: boolean;
  provider: TTSProvider;
  selectedVoice: string | null;
  availableVoices: TTSVoice[];
  isLoading: boolean;
  isTesting: boolean;
  autoSpeak: boolean;
  autoSpeakMode: 'short' | 'full';

  // Actions
  setEnabled: (enabled: boolean) => void;
  setProvider: (provider: TTSProvider) => void;
  setSelectedVoice: (voiceId: string | null) => void;
  setAvailableVoices: (voices: TTSVoice[]) => void;
  setLoading: (loading: boolean) => void;
  setTesting: (testing: boolean) => void;
  setAutoSpeak: (enabled: boolean) => Promise<void>;
  setAutoSpeakMode: (mode: 'short' | 'full') => Promise<void>;
  loadAutoSpeakConfig: () => Promise<void>;
  saveVoiceConfig: () => Promise<void>;
  testVoice: () => Promise<void>;
  loadVoices: () => Promise<void>;
}

export const useTTSStore = create<TTSState>((set, get) => ({
  enabled: false,
  provider: 'system',
  selectedVoice: null,
  availableVoices: [],
  isLoading: false,
  isTesting: false,
  autoSpeak: false,
  autoSpeakMode: 'short',

  setEnabled: (enabled) => set({ enabled }),

  setProvider: async (provider) => {
    set({ provider, selectedVoice: null });
    // Reload voices for the new provider
    get().loadVoices();
    // Save provider to config
    await get().saveVoiceConfig();
  },

  setSelectedVoice: async (voiceId) => {
    set({ selectedVoice: voiceId });
    // Save selected voice to config
    await get().saveVoiceConfig();
  },

  setAvailableVoices: (voices) => set({ availableVoices: voices }),

  setLoading: (loading) => set({ isLoading: loading }),

  setTesting: (testing) => set({ isTesting: testing }),

  setAutoSpeak: async (enabled) => {
    try {
      const result = await window.electronAPI.setAutoSpeak(enabled, get().autoSpeakMode);
      if (result.success) {
        set({ autoSpeak: enabled });
      } else {
        console.error('Failed to set auto-speak:', result.error);
      }
    } catch (error) {
      console.error('Failed to set auto-speak:', error);
    }
  },

  setAutoSpeakMode: async (mode) => {
    try {
      const result = await window.electronAPI.setAutoSpeak(get().autoSpeak, mode);
      if (result.success) {
        set({ autoSpeakMode: mode });
      } else {
        console.error('Failed to set auto-speak mode:', result.error);
      }
    } catch (error) {
      console.error('Failed to set auto-speak mode:', error);
    }
  },

  loadAutoSpeakConfig: async () => {
    try {
      const result = await window.electronAPI.getAutoSpeakConfig();
      if (result.success && result.data) {
        // If autoSpeak is enabled or provider is configured, enable the main TTS toggle
        // This ensures the TTS settings section stays visible after refresh
        const shouldEnableTTS = result.data.enabled || !!result.data.provider;

        set({
          enabled: shouldEnableTTS,
          autoSpeak: result.data.enabled,
          autoSpeakMode: result.data.mode || 'short',
          provider: result.data.provider || get().provider,
          selectedVoice: result.data.selectedVoice || get().selectedVoice,
        });
      }
    } catch (error) {
      console.error('Failed to load auto-speak config:', error);
    }
  },

  saveVoiceConfig: async () => {
    try {
      const { autoSpeak, autoSpeakMode, provider, selectedVoice } = get();
      const result = await window.electronAPI.setAutoSpeak(
        autoSpeak,
        autoSpeakMode,
        provider,
        selectedVoice
      );
      if (!result.success) {
        console.error('Failed to save voice config:', result.error);
      }
    } catch (error) {
      console.error('Failed to save voice config:', error);
    }
  },

  testVoice: async () => {
    const { selectedVoice, provider } = get();
    if (!selectedVoice) return;

    set({ isTesting: true });
    try {
      const result = await window.electronAPI.testVoice(
        provider,
        selectedVoice,
        'This is a test of the selected voice.'
      );

      if (!result.success) {
        console.error('Failed to test TTS voice:', result.error);
      }
    } catch (error) {
      console.error('Failed to test TTS voice:', error);
    } finally {
      set({ isTesting: false });
    }
  },

  loadVoices: async () => {
    const { provider } = get();
    set({ isLoading: true });

    try {
      const result = await window.electronAPI.getVoices(provider);

      if (result.success && result.data) {
        set({ availableVoices: result.data });
      } else {
        console.error('Failed to load TTS voices:', result.error);
        set({ availableVoices: [] });
      }
    } catch (error) {
      console.error('Failed to load TTS voices:', error);
      set({ availableVoices: [] });
    } finally {
      set({ isLoading: false });
    }
  },
}));

// Load config first (which sets provider), then load voices for that provider
// This ensures voices match the saved provider from the start
useTTSStore.getState().loadAutoSpeakConfig().then(() => {
  useTTSStore.getState().loadVoices();
});
