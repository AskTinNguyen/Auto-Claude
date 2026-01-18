/**
 * LAN Access Module
 *
 * Provides PIN-based authentication for LAN access with IP detection
 * and URL generation for local network and Tailscale connections.
 */

import * as os from 'os';
import type { NetworkInterface, LanConfig, LanUrls, NetworkAddresses } from './types';

/**
 * LAN Access Manager
 *
 * Handles PIN generation, IP detection, and URL generation for LAN access.
 */
export class LanAccessModule {
  private currentPin: string | null = null;
  private port: number = 3000; // Default port

  /**
   * Generate a 4-digit PIN
   * @param configuredPin Optional static PIN to use instead of generating random one
   * @returns The generated or configured PIN
   */
  generatePin(configuredPin?: string | null): string {
    if (configuredPin) {
      // Validate configured PIN
      if (!/^\d{4}$/.test(configuredPin)) {
        throw new Error('Configured PIN must be exactly 4 digits');
      }
      this.currentPin = configuredPin;
      return configuredPin;
    }

    // Generate random 4-digit PIN
    const pin = Math.floor(1000 + Math.random() * 9000).toString();
    this.currentPin = pin;
    return pin;
  }

  /**
   * Set the server port for URL generation
   * @param port Server port number
   */
  setPort(port: number): void {
    if (port < 1 || port > 65535) {
      throw new Error('Port must be between 1 and 65535');
    }
    this.port = port;
  }

  /**
   * Get the current PIN
   * @returns Current PIN or null if not generated
   */
  getCurrentPin(): string | null {
    return this.currentPin;
  }

  /**
   * Validate a PIN against the current PIN
   * @param pin PIN to validate
   * @returns True if PIN matches current PIN
   */
  validatePin(pin: string): boolean {
    if (!this.currentPin) {
      return false;
    }
    return pin === this.currentPin;
  }

  /**
   * Get all network interfaces
   * @returns Array of network interfaces
   */
  private getNetworkInterfaces(): NetworkInterface[] {
    const interfaces = os.networkInterfaces();
    const result: NetworkInterface[] = [];

    for (const [name, addrs] of Object.entries(interfaces)) {
      if (!addrs) continue;

      for (const addr of addrs) {
        result.push({
          address: addr.address,
          family: addr.family as 'IPv4' | 'IPv6',
          internal: addr.internal,
        });
      }
    }

    return result;
  }

  /**
   * Check if an IP is in a specific CIDR range
   * @param ip IP address to check
   * @param cidr CIDR notation (e.g., '192.168.0.0/16')
   * @returns True if IP is in range
   */
  private isInCidrRange(ip: string, cidr: string): boolean {
    const [range, bits] = cidr.split('/');
    const mask = ~(2 ** (32 - parseInt(bits)) - 1);

    const ipInt = this.ipToInt(ip);
    const rangeInt = this.ipToInt(range);

    return (ipInt & mask) === (rangeInt & mask);
  }

  /**
   * Convert IP address to integer
   * @param ip IP address string
   * @returns Integer representation
   */
  private ipToInt(ip: string): number {
    return ip.split('.').reduce((int, octet) => (int << 8) + parseInt(octet, 10), 0) >>> 0;
  }

  /**
   * Check if IP is in standard private network ranges
   * @param ip IP address to check
   * @returns True if in standard private ranges
   */
  private isStandardPrivateNetwork(ip: string): boolean {
    // 192.168.0.0/16
    if (this.isInCidrRange(ip, '192.168.0.0/16')) return true;

    // 10.0.0.0/8
    if (this.isInCidrRange(ip, '10.0.0.0/8')) return true;

    // 172.16.0.0/12 (172.16.0.0 - 172.31.255.255)
    if (this.isInCidrRange(ip, '172.16.0.0/12')) return true;

    return false;
  }

  /**
   * Check if IP is in Tailscale range
   * @param ip IP address to check
   * @returns True if in Tailscale range (100.64.0.0/10)
   */
  private isTailscaleIp(ip: string): boolean {
    return this.isInCidrRange(ip, '100.64.0.0/10');
  }

  /**
   * Check if IP is localhost or link-local
   * @param ip IP address to check
   * @returns True if should be excluded
   */
  private shouldExcludeIp(ip: string): boolean {
    // Localhost
    if (ip === '127.0.0.1' || ip === '::1') return true;

    // Link-local (169.254.0.0/16)
    if (this.isInCidrRange(ip, '169.254.0.0/16')) return true;

    return false;
  }

  /**
   * Get local network IP address
   * Prefers standard private network ranges over CGNAT/Tailscale
   * @returns Local IP address or null if not found
   */
  getLocalIpAddress(): string | null {
    const interfaces = this.getNetworkInterfaces();

    // Filter to IPv4, non-internal, non-excluded addresses
    const candidates = interfaces.filter(
      iface =>
        iface.family === 'IPv4' &&
        !iface.internal &&
        !this.shouldExcludeIp(iface.address)
    );

    // Prefer standard private networks
    const standardPrivate = candidates.find(iface =>
      this.isStandardPrivateNetwork(iface.address)
    );

    if (standardPrivate) {
      return standardPrivate.address;
    }

    // Fall back to any non-Tailscale address
    const nonTailscale = candidates.find(iface =>
      !this.isTailscaleIp(iface.address)
    );

    return nonTailscale?.address ?? null;
  }

  /**
   * Get Tailscale IP address
   * @returns Tailscale IP or null if not found
   */
  getTailscaleIpAddress(): string | null {
    const interfaces = this.getNetworkInterfaces();

    const tailscale = interfaces.find(
      iface =>
        iface.family === 'IPv4' &&
        !iface.internal &&
        this.isTailscaleIp(iface.address)
    );

    return tailscale?.address ?? null;
  }

  /**
   * Get all network addresses
   * @returns Network addresses object
   */
  getNetworkAddresses(): NetworkAddresses {
    return {
      localIp: this.getLocalIpAddress(),
      tailscaleIp: this.getTailscaleIpAddress(),
    };
  }

  /**
   * Generate URL with optional PIN
   * @param ip IP address
   * @param includePin Whether to include PIN in URL
   * @returns URL string or null if IP is null
   */
  private generateUrl(ip: string | null, includePin: boolean = false): string | null {
    if (!ip) return null;

    const baseUrl = `http://${ip}:${this.port}`;

    if (includePin && this.currentPin) {
      return `${baseUrl}?pin=${this.currentPin}`;
    }

    return baseUrl;
  }

  /**
   * Get LAN URL without PIN
   * @returns LAN URL or null if no local IP
   */
  getLanUrl(): string | null {
    return this.generateUrl(this.getLocalIpAddress(), false);
  }

  /**
   * Get LAN URL with PIN embedded (for QR codes)
   * @returns LAN URL with PIN or null if no local IP or PIN
   */
  getLanUrlWithPin(): string | null {
    return this.generateUrl(this.getLocalIpAddress(), true);
  }

  /**
   * Get Tailscale URL without PIN
   * @returns Tailscale URL or null if no Tailscale IP
   */
  getTailscaleUrl(): string | null {
    return this.generateUrl(this.getTailscaleIpAddress(), false);
  }

  /**
   * Get Tailscale URL with PIN embedded
   * @returns Tailscale URL with PIN or null if no Tailscale IP or PIN
   */
  getTailscaleUrlWithPin(): string | null {
    return this.generateUrl(this.getTailscaleIpAddress(), true);
  }

  /**
   * Get all LAN URLs
   * @returns Object containing all URL variants
   */
  getAllUrls(): LanUrls {
    return {
      lan: this.getLanUrl(),
      lanWithPin: this.getLanUrlWithPin(),
      tailscale: this.getTailscaleUrl(),
      tailscaleWithPin: this.getTailscaleUrlWithPin(),
    };
  }

  /**
   * Reset the module state (clear PIN)
   */
  reset(): void {
    this.currentPin = null;
  }
}

// Singleton instance
let instance: LanAccessModule | null = null;

/**
 * Get the singleton LAN access module instance
 * @returns LAN access module instance
 */
export function getLanAccessModule(): LanAccessModule {
  if (!instance) {
    instance = new LanAccessModule();
  }
  return instance;
}

/**
 * Create a new LAN access module instance (for testing)
 * @returns New LAN access module instance
 */
export function createLanAccessModule(): LanAccessModule {
  return new LanAccessModule();
}
