/**
 * LAN Access Module Types
 *
 * Types for PIN-based LAN authentication and network access
 */

/**
 * Network interface information
 */
export interface NetworkInterface {
  address: string;
  family: 'IPv4' | 'IPv6';
  internal: boolean;
}

/**
 * LAN access configuration
 */
export interface LanConfig {
  /** Static PIN to use instead of generating random one */
  configuredPin?: string | null;
  /** Server port for URL generation */
  port?: number;
}

/**
 * LAN URLs for different network types
 */
export interface LanUrls {
  /** Local network URL without PIN */
  lan: string | null;
  /** Local network URL with PIN embedded */
  lanWithPin: string | null;
  /** Tailscale URL without PIN */
  tailscale: string | null;
  /** Tailscale URL with PIN embedded */
  tailscaleWithPin: string | null;
}

/**
 * Network IP addresses
 */
export interface NetworkAddresses {
  /** Local network IP (192.168.x.x, 10.x.x.x, 172.16-31.x.x) */
  localIp: string | null;
  /** Tailscale IP (100.64.0.0/10 range) */
  tailscaleIp: string | null;
}
