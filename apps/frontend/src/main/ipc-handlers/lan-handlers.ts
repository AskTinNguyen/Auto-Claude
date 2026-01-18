import { ipcMain } from 'electron';
import type { LanUrls } from '../lan/types';
import type { AppSettings } from '../../shared/types';
import { getHttpServer } from '../index';

/**
 * LAN Access IPC Handlers
 *
 * Handles communication between renderer process and main process for LAN access features:
 * - Get LAN URLs (local and Tailscale)
 * - Get current PIN
 * - Validate PIN (for testing)
 * - Restart server with new settings
 *
 * These handlers access the HTTP server instance via getHttpServer() from main/index.ts.
 */

/**
 * Register all LAN-related IPC handlers
 */
export function setupLanHandlers(): void {
  /**
   * Get LAN URLs (local and Tailscale)
   * Returns URLs with and without PIN embedded
   */
  ipcMain.handle('lan:get-urls', async (): Promise<LanUrls | null> => {
    try {
      const httpServer = getHttpServer();
      if (!httpServer) {
        console.warn('[lan-handlers] HTTP server not initialized');
        return null;
      }

      const urls = httpServer.getLanUrls();
      return urls;
    } catch (error) {
      console.error('[lan-handlers] Error getting LAN URLs:', error);
      return null;
    }
  });

  /**
   * Get current PIN
   * Returns the active PIN (either configured or randomly generated)
   */
  ipcMain.handle('lan:get-pin', async (): Promise<string | null> => {
    try {
      const httpServer = getHttpServer();
      if (!httpServer) {
        console.warn('[lan-handlers] HTTP server not initialized');
        return null;
      }

      const pin = httpServer.getCurrentPin();
      return pin;
    } catch (error) {
      console.error('[lan-handlers] Error getting PIN:', error);
      return null;
    }
  });

  /**
   * Validate a PIN (for testing)
   * Returns true if the PIN is valid
   */
  ipcMain.handle('lan:validate-pin', async (_, pin: string): Promise<boolean> => {
    try {
      const httpServer = getHttpServer();
      if (!httpServer) {
        console.warn('[lan-handlers] HTTP server not initialized');
        return false;
      }

      if (typeof pin !== 'string' || pin.length !== 4) {
        console.warn('[lan-handlers] Invalid PIN format:', pin);
        return false;
      }

      const isValid = httpServer.validatePin(pin);
      return isValid;
    } catch (error) {
      console.error('[lan-handlers] Error validating PIN:', error);
      return false;
    }
  });

  /**
   * Restart server with new settings
   * Used when LAN access is toggled or PIN is changed
   */
  ipcMain.handle('lan:restart-server', async (_, settings: AppSettings): Promise<void> => {
    try {
      const httpServer = getHttpServer();
      if (!httpServer) {
        console.warn('[lan-handlers] HTTP server not initialized');
        return;
      }

      // Stop the server
      await httpServer.stop();

      // Start with new settings
      await httpServer.start(settings);

      console.log('[lan-handlers] Server restarted with new settings');
    } catch (error) {
      console.error('[lan-handlers] Error restarting server:', error);
      throw error;
    }
  });

  console.log('[lan-handlers] LAN IPC handlers registered');
}
