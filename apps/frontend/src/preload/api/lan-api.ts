import { ipcRenderer } from 'electron';
import type { LanUrls } from '../../main/lan/types';
import type { AppSettings } from '../../shared/types';

/**
 * LAN Access API
 *
 * Provides methods for renderer process to interact with LAN access features:
 * - Get LAN URLs (local and Tailscale)
 * - Get current PIN
 * - Validate PIN
 * - Restart server with new settings
 */
export interface LanAPI {
  /**
   * Get LAN URLs (local and Tailscale)
   * Returns URLs with and without PIN embedded
   */
  getLanUrls: () => Promise<LanUrls | null>;

  /**
   * Get current PIN
   * Returns the active PIN (either configured or randomly generated)
   */
  getLanPin: () => Promise<string | null>;

  /**
   * Validate a PIN (for testing)
   * Returns true if the PIN is valid
   */
  validateLanPin: (pin: string) => Promise<boolean>;

  /**
   * Restart server with new settings
   * Used when LAN access is toggled or PIN is changed
   */
  restartLanServer: (settings: AppSettings) => Promise<void>;
}

export const createLanAPI = (): LanAPI => ({
  getLanUrls: (): Promise<LanUrls | null> =>
    ipcRenderer.invoke('lan:get-urls'),

  getLanPin: (): Promise<string | null> =>
    ipcRenderer.invoke('lan:get-pin'),

  validateLanPin: (pin: string): Promise<boolean> =>
    ipcRenderer.invoke('lan:validate-pin', pin),

  restartLanServer: (settings: AppSettings): Promise<void> =>
    ipcRenderer.invoke('lan:restart-server', settings)
});
