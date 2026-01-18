/**
 * HTTP Server Manager for Electron App
 *
 * Manages the HTTP server lifecycle with LAN access support and PIN authentication.
 * Uses Node.js http module (not Bun) for Electron compatibility.
 */

import * as http from 'http';
import type { AppSettings } from '../shared/types';
import {
  getLanAccessModule,
  createServerConfig,
  apiPinAuthMiddleware,
  createAuthEndpoint,
  withMiddleware,
  logLanAccessInfo,
} from './lan';
import type { LanUrls, RequestHandler } from './lan';

/**
 * HTTP Server Manager
 *
 * Handles HTTP server lifecycle, routing, and LAN authentication.
 */
export class HttpServerManager {
  private server: http.Server | null = null;
  private currentSettings: AppSettings | null = null;
  private actualPort: number = 0;

  /**
   * Start the HTTP server with given settings
   *
   * @param settings Application settings
   * @param rpcHandler Optional RPC handler function
   */
  async start(
    settings: AppSettings,
    rpcHandler?: RequestHandler
  ): Promise<void> {
    // Stop existing server if running
    if (this.server) {
      await this.stop();
    }

    this.currentSettings = settings;
    const lanModule = getLanAccessModule();

    // Determine port (default 3000)
    const port = 3000;

    // Generate PIN (use configured or random)
    const pin = lanModule.generatePin(settings.lanPin);
    lanModule.setPort(port);

    // Create server configuration
    const allowLan = settings.allowLan ?? false;
    const serverConfig = createServerConfig(allowLan, port);

    // Create request handler
    const requestHandler = this.createRequestHandler(
      lanModule,
      allowLan,
      rpcHandler
    );

    // Create and start server
    this.server = http.createServer(requestHandler);

    return new Promise((resolve, reject) => {
      if (!this.server) {
        reject(new Error('Server creation failed'));
        return;
      }

      this.server.on('error', (error) => {
        console.error('[HttpServer] Server error:', error);
        reject(error);
      });

      this.server.listen(port, serverConfig.hostname, () => {
        this.actualPort = port;
        console.log(`[HttpServer] Server started on ${serverConfig.hostname}:${port}`);

        // Log LAN access info if enabled
        if (allowLan) {
          logLanAccessInfo(lanModule, allowLan, port, settings.lanPin);
        } else {
          console.log(`[HttpServer] Server listening on http://localhost:${port}`);
        }

        resolve();
      });
    });
  }

  /**
   * Stop the HTTP server
   */
  async stop(): Promise<void> {
    if (!this.server) {
      return;
    }

    return new Promise((resolve, reject) => {
      if (!this.server) {
        resolve();
        return;
      }

      this.server.close((err) => {
        if (err) {
          console.error('[HttpServer] Error stopping server:', err);
          reject(err);
        } else {
          console.log('[HttpServer] Server stopped');
          this.server = null;
          this.actualPort = 0;
          resolve();
        }
      });
    });
  }

  /**
   * Get the server URL
   *
   * @returns Server URL or null if not running
   */
  getUrl(): string | null {
    if (!this.server || this.actualPort === 0) {
      return null;
    }

    return `http://localhost:${this.actualPort}`;
  }

  /**
   * Get the current PIN
   *
   * @returns Current PIN or null if not set
   */
  getCurrentPin(): string | null {
    const lanModule = getLanAccessModule();
    return lanModule.getCurrentPin();
  }

  /**
   * Get all LAN URLs
   *
   * @returns LAN URLs object
   */
  getLanUrls(): LanUrls {
    const lanModule = getLanAccessModule();
    return lanModule.getAllUrls();
  }

  /**
   * Validate a PIN
   *
   * @param pin PIN to validate
   * @returns True if PIN is valid
   */
  validatePin(pin: string): boolean {
    const lanModule = getLanAccessModule();
    return lanModule.validatePin(pin);
  }

  /**
   * Create the main request handler with routing
   *
   * @param lanModule LAN access module
   * @param allowLan Whether LAN access is enabled
   * @param rpcHandler Optional RPC handler
   * @returns Request handler function
   */
  private createRequestHandler(
    lanModule: any,
    allowLan: boolean,
    rpcHandler?: RequestHandler
  ): (req: http.IncomingMessage, res: http.ServerResponse) => void {
    // Create middleware function (use API middleware for JSON responses)
    const middleware = apiPinAuthMiddleware(lanModule, allowLan);
    const protect = withMiddleware(middleware);

    // Create auth endpoint
    const authEndpoint = createAuthEndpoint(lanModule, allowLan);

    // Create routes
    const routes: Record<string, RequestHandler> = {
      '/health': this.createHealthHandler(),
      '/auth': authEndpoint,
    };

    // Add RPC route if handler provided
    if (rpcHandler) {
      routes['/rpc'] = protect(rpcHandler);
    }

    // Return Node.js http handler
    return async (req: http.IncomingMessage, res: http.ServerResponse) => {
      try {
        // Convert to Request object for middleware compatibility
        const url = new URL(req.url || '/', `http://${req.headers.host}`);
        const request = this.createFetchRequest(req, url);

        // Find matching route
        const handler = routes[url.pathname];

        let response: Response;
        if (handler) {
          response = await handler(request);
        } else {
          response = new Response(
            JSON.stringify({ error: 'Not Found' }),
            { status: 404, headers: { 'Content-Type': 'application/json' } }
          );
        }

        // Write response to Node.js response object
        this.writeFetchResponse(response, res);
      } catch (error) {
        console.error('[HttpServer] Request handler error:', error);
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Internal Server Error' }));
      }
    };
  }

  /**
   * Create health check handler
   *
   * @returns Health check handler
   */
  private createHealthHandler(): RequestHandler {
    return async () => {
      return new Response(
        JSON.stringify({ status: 'ok' }),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    };
  }

  /**
   * Convert Node.js IncomingMessage to Fetch API Request
   *
   * @param req Node.js request
   * @param url Parsed URL
   * @returns Fetch API Request
   */
  private createFetchRequest(
    req: http.IncomingMessage,
    url: URL
  ): Request {
    const headers = new Headers();
    for (const [key, value] of Object.entries(req.headers)) {
      if (value) {
        if (Array.isArray(value)) {
          value.forEach((v) => headers.append(key, v));
        } else {
          headers.set(key, value);
        }
      }
    }

    const method = req.method || 'GET';

    // For GET and HEAD requests, no body
    if (method === 'GET' || method === 'HEAD') {
      return new Request(url.toString(), {
        method,
        headers,
      });
    }

    // For other methods, we'll handle the body as a stream
    // Note: For simplicity, we're creating a Request without body
    // since our current use case (PIN auth) doesn't require request bodies
    return new Request(url.toString(), {
      method,
      headers,
    });
  }

  /**
   * Write Fetch API Response to Node.js ServerResponse
   *
   * @param response Fetch API Response
   * @param res Node.js response
   */
  private async writeFetchResponse(
    response: Response,
    res: http.ServerResponse
  ): Promise<void> {
    // Set status
    res.writeHead(response.status, response.statusText);

    // Set headers
    response.headers.forEach((value, key) => {
      res.setHeader(key, value);
    });

    // Write body
    if (response.body) {
      const text = await response.text();
      res.end(text);
    } else {
      res.end();
    }
  }
}
