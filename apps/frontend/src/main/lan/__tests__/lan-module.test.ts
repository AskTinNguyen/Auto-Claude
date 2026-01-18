/**
 * LAN Access Module Tests
 */

import { describe, it, expect, beforeEach } from '@jest/globals';
import { createLanAccessModule } from '../lan-module';
import type { LanAccessModule } from '../lan-module';

describe('LanAccessModule', () => {
  let module: LanAccessModule;

  beforeEach(() => {
    module = createLanAccessModule();
  });

  describe('PIN Generation', () => {
    it('should generate a 4-digit PIN', () => {
      const pin = module.generatePin();
      expect(pin).toMatch(/^\d{4}$/);
      expect(parseInt(pin, 10)).toBeGreaterThanOrEqual(1000);
      expect(parseInt(pin, 10)).toBeLessThanOrEqual(9999);
    });

    it('should use configured PIN if provided', () => {
      const configuredPin = '1234';
      const pin = module.generatePin(configuredPin);
      expect(pin).toBe(configuredPin);
      expect(module.getCurrentPin()).toBe(configuredPin);
    });

    it('should throw error for invalid configured PIN', () => {
      expect(() => module.generatePin('123')).toThrow('Configured PIN must be exactly 4 digits');
      expect(() => module.generatePin('12345')).toThrow('Configured PIN must be exactly 4 digits');
      expect(() => module.generatePin('abcd')).toThrow('Configured PIN must be exactly 4 digits');
    });

    it('should store generated PIN', () => {
      const pin = module.generatePin();
      expect(module.getCurrentPin()).toBe(pin);
    });

    it('should return null for current PIN before generation', () => {
      expect(module.getCurrentPin()).toBeNull();
    });
  });

  describe('PIN Validation', () => {
    it('should validate correct PIN', () => {
      const pin = module.generatePin();
      expect(module.validatePin(pin)).toBe(true);
    });

    it('should reject incorrect PIN', () => {
      module.generatePin('1234');
      expect(module.validatePin('5678')).toBe(false);
    });

    it('should return false when no PIN is set', () => {
      expect(module.validatePin('1234')).toBe(false);
    });
  });

  describe('Port Management', () => {
    it('should set valid port', () => {
      expect(() => module.setPort(8080)).not.toThrow();
    });

    it('should throw error for invalid port', () => {
      expect(() => module.setPort(0)).toThrow('Port must be between 1 and 65535');
      expect(() => module.setPort(65536)).toThrow('Port must be between 1 and 65535');
      expect(() => module.setPort(-1)).toThrow('Port must be between 1 and 65535');
    });
  });

  describe('IP Detection', () => {
    it('should detect local IP address', () => {
      const localIp = module.getLocalIpAddress();
      // Can be null in some environments (like CI), but if present should be valid
      if (localIp) {
        expect(localIp).toMatch(/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/);
        expect(localIp).not.toBe('127.0.0.1');
      }
    });

    it('should detect Tailscale IP address', () => {
      const tailscaleIp = module.getTailscaleIpAddress();
      // Will be null unless Tailscale is running
      if (tailscaleIp) {
        expect(tailscaleIp).toMatch(/^100\.64\.\d{1,3}\.\d{1,3}$/);
      }
    });

    it('should get all network addresses', () => {
      const addresses = module.getNetworkAddresses();
      expect(addresses).toHaveProperty('localIp');
      expect(addresses).toHaveProperty('tailscaleIp');
    });
  });

  describe('URL Generation', () => {
    beforeEach(() => {
      module.generatePin('1234');
      module.setPort(3000);
    });

    it('should generate LAN URL without PIN', () => {
      const url = module.getLanUrl();
      if (url) {
        expect(url).toMatch(/^http:\/\/\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:3000$/);
        expect(url).not.toContain('pin=');
      }
    });

    it('should generate LAN URL with PIN', () => {
      const url = module.getLanUrlWithPin();
      if (url) {
        expect(url).toMatch(/^http:\/\/\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:3000\?pin=1234$/);
      }
    });

    it('should generate Tailscale URL without PIN', () => {
      const url = module.getTailscaleUrl();
      // Will be null unless Tailscale is running
      if (url) {
        expect(url).toMatch(/^http:\/\/100\.64\.\d{1,3}\.\d{1,3}:3000$/);
        expect(url).not.toContain('pin=');
      }
    });

    it('should generate Tailscale URL with PIN', () => {
      const url = module.getTailscaleUrlWithPin();
      // Will be null unless Tailscale is running
      if (url) {
        expect(url).toMatch(/^http:\/\/100\.64\.\d{1,3}\.\d{1,3}:3000\?pin=1234$/);
      }
    });

    it('should get all URLs', () => {
      const urls = module.getAllUrls();
      expect(urls).toHaveProperty('lan');
      expect(urls).toHaveProperty('lanWithPin');
      expect(urls).toHaveProperty('tailscale');
      expect(urls).toHaveProperty('tailscaleWithPin');
    });

    it('should use custom port in URLs', () => {
      module.setPort(8080);
      const url = module.getLanUrl();
      if (url) {
        expect(url).toContain(':8080');
      }
    });
  });

  describe('Reset', () => {
    it('should clear PIN on reset', () => {
      module.generatePin('1234');
      expect(module.getCurrentPin()).toBe('1234');

      module.reset();
      expect(module.getCurrentPin()).toBeNull();
    });

    it('should not include PIN in URLs after reset', () => {
      module.generatePin('1234');
      module.reset();

      const url = module.getLanUrlWithPin();
      if (url) {
        expect(url).not.toContain('pin=');
      }
    });
  });
});
