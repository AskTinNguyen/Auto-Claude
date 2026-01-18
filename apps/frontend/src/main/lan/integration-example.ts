/**
 * Complete Integration Example - PIN Auth Middleware for Bun/Node.js HTTP Server
 *
 * This file demonstrates how to integrate PIN authentication middleware into your
 * Bun or Node.js HTTP server with TypeScript.
 *
 * @example
 * See the examples below for complete server setup with:
 * - LAN access configuration
 * - Protected routes with PIN authentication
 * - Auth endpoint for PIN validation
 * - Server startup with logging
 */

import {
  getLanAccessModule,
  createServerOptions,
  logLanAccessInfo,
  type RequestHandler,
  type ServerOptions,
} from './index';

// ============================================================================
// EXAMPLE 1: Basic Bun Server with PIN Auth
// ============================================================================

/**
 * Example RPC handler (protected route)
 */
async function rpcHandler(request: Request): Promise<Response> {
  const body = await request.json();

  // Your RPC logic here
  return new Response(
    JSON.stringify({
      jsonrpc: '2.0',
      id: body.id,
      result: { message: 'RPC call successful' },
    }),
    {
      headers: { 'Content-Type': 'application/json' },
    }
  );
}

/**
 * Example health check handler (public route)
 */
function healthCheckHandler(_request: Request): Response {
  return new Response(
    JSON.stringify({ status: 'ok', timestamp: Date.now() }),
    {
      headers: { 'Content-Type': 'application/json' },
    }
  );
}

/**
 * Configuration interface
 */
interface AppConfig {
  /** Whether to allow LAN access (enables PIN auth) */
  allowLan: boolean;
  /** Optional static PIN (if null, generates random PIN) */
  lanPin?: string | null;
  /** Server port */
  port?: number;
}

/**
 * Start server with PIN authentication
 */
export function startServer(config: AppConfig): void {
  const port = config.port || 3000;
  const lanModule = getLanAccessModule();

  // Create server options with protected routes
  const options = createServerOptions(
    lanModule,
    config.allowLan,
    port,
    // Protected routes (require PIN auth when allowLan is true)
    {
      '/rpc': rpcHandler,
      '/api/projects': async (_req) => {
        return new Response(JSON.stringify({ projects: [] }), {
          headers: { 'Content-Type': 'application/json' },
        });
      },
    },
    // Public routes (no auth required)
    {
      '/health': healthCheckHandler,
    }
  );

  // Log LAN access info if enabled
  if (config.allowLan) {
    logLanAccessInfo(lanModule, config.allowLan, port, config.lanPin);
  }

  // Start Bun server
  const server = Bun.serve({
    hostname: options.hostname,
    port: options.port,
    fetch(request: Request): Response | Promise<Response> {
      const url = new URL(request.url);
      const handler = options.routes?.[url.pathname];

      if (handler) {
        return handler(request);
      }

      // 404 for unknown routes
      return new Response('Not Found', { status: 404 });
    },
  });

  console.log(`Server running on ${options.hostname}:${server.port}`);
}

// ============================================================================
// EXAMPLE 2: Advanced Configuration with Custom Handlers
// ============================================================================

/**
 * Advanced server configuration
 */
export function createAdvancedServer(config: AppConfig): ServerOptions {
  const port = config.port || 3000;
  const lanModule = getLanAccessModule();

  // Define protected routes
  const protectedRoutes: Record<string, RequestHandler> = {
    // RPC endpoint
    '/rpc': async (request: Request): Promise<Response> => {
      try {
        const body = await request.json();
        // Handle RPC calls
        return new Response(JSON.stringify({ result: 'success' }), {
          headers: { 'Content-Type': 'application/json' },
        });
      } catch (error) {
        return new Response(
          JSON.stringify({ error: 'Invalid request' }),
          {
            status: 400,
            headers: { 'Content-Type': 'application/json' },
          }
        );
      }
    },

    // API endpoints
    '/api/status': async (_request: Request): Promise<Response> => {
      return new Response(
        JSON.stringify({
          status: 'running',
          version: '1.0.0',
          timestamp: Date.now(),
        }),
        {
          headers: { 'Content-Type': 'application/json' },
        }
      );
    },

    '/api/projects': async (_request: Request): Promise<Response> => {
      return new Response(
        JSON.stringify({
          projects: [
            { id: '1', name: 'Project A' },
            { id: '2', name: 'Project B' },
          ],
        }),
        {
          headers: { 'Content-Type': 'application/json' },
        }
      );
    },
  };

  // Define public routes (no auth required)
  const publicRoutes: Record<string, RequestHandler> = {
    '/health': healthCheckHandler,

    '/version': (_request: Request): Response => {
      return new Response(
        JSON.stringify({ version: '1.0.0' }),
        {
          headers: { 'Content-Type': 'application/json' },
        }
      );
    },
  };

  // Create server options
  const options = createServerOptions(
    lanModule,
    config.allowLan,
    port,
    protectedRoutes,
    publicRoutes
  );

  // Log LAN access info
  if (config.allowLan) {
    logLanAccessInfo(lanModule, config.allowLan, port, config.lanPin);
  }

  return options;
}

// ============================================================================
// EXAMPLE 3: Environment-Based Configuration
// ============================================================================

/**
 * Load configuration from environment variables
 */
export function loadConfigFromEnv(): AppConfig {
  return {
    allowLan: process.env.ALLOW_LAN === 'true',
    lanPin: process.env.LAN_PIN || null,
    port: process.env.PORT ? parseInt(process.env.PORT, 10) : 3000,
  };
}

/**
 * Start server with environment-based configuration
 */
export function startServerFromEnv(): void {
  const config = loadConfigFromEnv();

  console.log('Starting server with configuration:');
  console.log(`  LAN Access: ${config.allowLan ? 'ENABLED' : 'DISABLED'}`);
  console.log(`  Port: ${config.port}`);
  console.log(`  Static PIN: ${config.lanPin ? 'Yes' : 'No (random)'}`);

  startServer(config);
}

// ============================================================================
// EXAMPLE 4: Complete Bun Server Implementation
// ============================================================================

/**
 * Complete server implementation with all features
 */
export class PinAuthServer {
  private server: any; // Bun.Server type
  private lanModule = getLanAccessModule();
  private config: AppConfig;

  constructor(config: AppConfig) {
    this.config = config;
  }

  /**
   * Register route handlers
   */
  private createRoutes(): Record<string, RequestHandler> {
    const protectedRoutes: Record<string, RequestHandler> = {
      '/rpc': rpcHandler,
      '/api/projects': async (_req) => {
        return new Response(JSON.stringify({ projects: [] }), {
          headers: { 'Content-Type': 'application/json' },
        });
      },
    };

    const publicRoutes: Record<string, RequestHandler> = {
      '/health': healthCheckHandler,
    };

    const options = createServerOptions(
      this.lanModule,
      this.config.allowLan,
      this.config.port || 3000,
      protectedRoutes,
      publicRoutes
    );

    return options.routes || {};
  }

  /**
   * Start the server
   */
  start(): void {
    const port = this.config.port || 3000;
    const bindAll = process.env.NIGHTSHIFT_BIND_ALL === '1';
    const hostname = (this.config.allowLan || bindAll) ? '0.0.0.0' : '127.0.0.1';

    const routes = this.createRoutes();

    // Log LAN access info
    if (this.config.allowLan) {
      logLanAccessInfo(this.lanModule, true, port, this.config.lanPin);
    }

    // Start server
    this.server = Bun.serve({
      hostname,
      port,
      fetch: (request: Request): Response | Promise<Response> => {
        const url = new URL(request.url);
        const handler = routes[url.pathname];

        if (handler) {
          return handler(request);
        }

        // Default 404 response
        return new Response('Not Found', { status: 404 });
      },
    });

    console.log(`\n🚀 Server started successfully!`);
    console.log(`   Address: http://${hostname}:${this.server.port}`);
    console.log(`   Environment: ${process.env.NODE_ENV || 'development'}\n`);
  }

  /**
   * Stop the server
   */
  stop(): void {
    if (this.server) {
      this.server.stop();
      console.log('Server stopped');
    }
  }

  /**
   * Get current PIN (for testing or display)
   */
  getCurrentPin(): string | null {
    return this.lanModule.getCurrentPin();
  }
}

// ============================================================================
// USAGE EXAMPLES
// ============================================================================

/**
 * Example 1: Simple startup
 */
export function example1_SimpleStartup() {
  startServer({
    allowLan: true,
    lanPin: '1234', // Static PIN
    port: 3000,
  });
}

/**
 * Example 2: Environment-based startup
 */
export function example2_EnvBasedStartup() {
  // Set environment variables:
  // ALLOW_LAN=true
  // LAN_PIN=1234
  // PORT=3000
  startServerFromEnv();
}

/**
 * Example 3: Class-based server
 */
export function example3_ClassBasedServer() {
  const server = new PinAuthServer({
    allowLan: true,
    lanPin: null, // Random PIN
    port: 3000,
  });

  server.start();

  // Later...
  // server.stop();
}

/**
 * Example 4: Custom configuration
 */
export function example4_CustomConfig() {
  const config: AppConfig = {
    allowLan: process.env.NODE_ENV === 'production',
    lanPin: process.env.LAN_PIN || null,
    port: parseInt(process.env.PORT || '3000', 10),
  };

  const options = createAdvancedServer(config);

  Bun.serve({
    ...options,
    fetch(request: Request) {
      const url = new URL(request.url);
      const handler = options.routes?.[url.pathname];
      return handler?.(request) ?? new Response('Not Found', { status: 404 });
    },
  });
}

// ============================================================================
// TypeScript Type Exports
// ============================================================================

export type {
  AppConfig,
  RequestHandler,
  ServerOptions,
};
