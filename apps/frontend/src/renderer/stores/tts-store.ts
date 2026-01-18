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

  // Actions
  setEnabled: (enabled: boolean) => void;
  setProvider: (provider: TTSProvider) => void;
  setSelectedVoice: (voiceId: string | null) => void;
  setAvailableVoices: (voices: TTSVoice[]) => void;
  setLoading: (loading: boolean) => void;
  setTesting: (testing: boolean) => void;
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

  setEnabled: (enabled) => set({ enabled }),

  setProvider: (provider) => {
    set({ provider, selectedVoice: null });
    // Reload voices for the new provider
    get().loadVoices();
  },

  setSelectedVoice: (voiceId) => set({ selectedVoice: voiceId }),

  setAvailableVoices: (voices) => set({ availableVoices: voices }),

  setLoading: (loading) => set({ isLoading: loading }),

  setTesting: (testing) => set({ isTesting: testing }),

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

// Load voices on store initialization
useTTSStore.getState().loadVoices();
