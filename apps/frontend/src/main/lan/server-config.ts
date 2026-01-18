/**
 * Server Configuration for LAN Access
 *
 * Provides configuration utilities for creating server options with
 * LAN access controls and PIN authentication.
 */

import type { LanAccessModule } from './lan-module';
import { pinAuthMiddleware, createAuthEndpoint, withMiddleware } from './middleware';
import type { RequestHandler } from './middleware';

/**
 * Server configuration options
 */
export interface ServerOptions {
  /** Hostname to bind to (0.0.0.0 for all interfaces, 127.0.0.1 for localhost) */
  hostname: string;
  /** Port to bind to */
  port: number;
  /** Optional routes with middleware applied */
  routes?: Record<string, RequestHandler>;
}

/**
 * Create server configuration based on LAN settings
 *
 * @param allowLan Whether to allow LAN access
 * @param port Server port (default: 3000)
 * @param forceBindAll Force binding to 0.0.0.0 (overrides allowLan)
 * @returns Server configuration options
 *
 * @example
 * ```ts
 * const bindAll = process.env.NIGHTSHIFT_BIND_ALL === "1";
 * const options = createServerConfig(config.allowLan, 3000, bindAll);
 * const server = Bun.serve(options);
 * ```
 */
export function createServerConfig(
  allowLan: boolean,
  port: number = 3000,
  forceBindAll: boolean = false
): ServerOptions {
  const hostname = (allowLan || forceBindAll) ? '0.0.0.0' : '127.0.0.1';

  return {
    hostname,
    port,
  };
}

/**
 * Create protected routes with PIN authentication middleware
 *
 * @param lanModule LAN access module for PIN validation
 * @param allowLan Whether LAN access is enabled
 * @param handlers Map of route paths to handler functions
 * @returns Map of route paths to protected handler functions
 *
 * @example
 * ```ts
 * const routes = createProtectedRoutes(
 *   getLanAccessModule(),
 *   config.allowLan,
 *   {
 *     "/rpc": rpcHandler,
 *     "/api/status": statusHandler,
 *   }
 * );
 * ```
 */
export function createProtectedRoutes(
  lanModule: LanAccessModule,
  allowLan: boolean,
  handlers: Record<string, RequestHandler>
): Record<string, RequestHandler> {
  const middleware = pinAuthMiddleware(lanModule, allowLan);
  const protect = withMiddleware(middleware);

  const protectedRoutes: Record<string, RequestHandler> = {};

  for (const [path, handler] of Object.entries(handlers)) {
    protectedRoutes[path] = protect(handler);
  }

  return protectedRoutes;
}

/**
 * Create complete server options with routes and authentication
 *
 * @param lanModule LAN access module
 * @param allowLan Whether LAN access is enabled
 * @param port Server port
 * @param protectedRoutes Routes that require PIN authentication
 * @param publicRoutes Optional public routes (no authentication)
 * @returns Complete server configuration
 *
 * @example
 * ```ts
 * const options = createServerOptions(
 *   getLanAccessModule(),
 *   config.allowLan,
 *   3000,
 *   {
 *     "/rpc": rpcHandler,
 *     "/api/projects": projectsHandler,
 *   },
 *   {
 *     "/health": healthCheckHandler,
 *   }
 * );
 *
 * const server = Bun.serve({
 *   ...options,
 *   fetch: (request) => {
 *     const url = new URL(request.url);
 *     const handler = options.routes?.[url.pathname];
 *     if (handler) {
 *       return handler(request);
 *     }
 *     return new Response("Not Found", { status: 404 });
 *   },
 * });
 * ```
 */
export function createServerOptions(
  lanModule: LanAccessModule,
  allowLan: boolean,
  port: number = 3000,
  protectedRoutes: Record<string, RequestHandler> = {},
  publicRoutes: Record<string, RequestHandler> = {}
): ServerOptions {
  const bindAll = process.env.NIGHTSHIFT_BIND_ALL === '1';
  const config = createServerConfig(allowLan, port, bindAll);

  // Create protected routes with middleware
  const protected_ = createProtectedRoutes(lanModule, allowLan, protectedRoutes);

  // Add auth endpoint
  const authEndpoint = createAuthEndpoint(lanModule, allowLan);

  // Combine all routes
  const routes: Record<string, RequestHandler> = {
    ...publicRoutes,
    ...protected_,
    '/auth': authEndpoint,
  };

  return {
    ...config,
    routes,
  };
}

/**
 * Log LAN access information when server starts
 *
 * @param lanModule LAN access module
 * @param allowLan Whether LAN access is enabled
 * @param port Actual server port
 * @param configuredPin Optional configured PIN (if not using random)
 *
 * @example
 * ```ts
 * if (config.allowLan) {
 *   logLanAccessInfo(getLanAccessModule(), true, actualPort, config.lanPin);
 * }
 * ```
 */
export function logLanAccessInfo(
  lanModule: LanAccessModule,
  allowLan: boolean,
  port: number,
  configuredPin?: string | null
): void {
  if (!allowLan) return;

  // Generate or use configured PIN
  const pin = lanModule.generatePin(configuredPin);
  lanModule.setPort(port);

  const addresses = lanModule.getNetworkAddresses();

  console.log('\n═══════════════════════════════════════════════════════');
  console.log('🌐 LAN ACCESS ENABLED');
  console.log('═══════════════════════════════════════════════════════');
  console.log(`\n📌 PIN: ${pin}`);
  console.log(`\n🔗 Access URLs:`);

  if (addresses.localIp) {
    console.log(`   Local Network: http://${addresses.localIp}:${port}?pin=${pin}`);
  }

  if (addresses.tailscaleIp) {
    console.log(`   Tailscale:     http://${addresses.tailscaleIp}:${port}?pin=${pin}`);
  }

  console.log('\n═══════════════════════════════════════════════════════\n');
}
