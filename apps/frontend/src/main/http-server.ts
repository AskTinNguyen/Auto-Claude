/**
 * HTTP Server Manager for Electron App
 *
 * Manages the HTTP server lifecycle with LAN access support and PIN authentication.
 * Uses Node.js http module (not Bun) for Electron compatibility.
 *
 * Provides multiple API styles for mobile clients:
 * - JSON-RPC 2.0 at /rpc for programmatic access
 * - REST-like API at /api/* for simpler HTTP access
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
import type { RpcMethodRegistry } from './rpc/types';
import { createRestRoutes, createDynamicRestHandler } from './rpc/rest-routes';

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
   * RPC methods registry (stored for REST routes)
   */
  private rpcMethods: RpcMethodRegistry | null = null;

  /**
   * Start the HTTP server with given settings
   *
   * @param settings Application settings
   * @param rpcHandler Optional RPC handler function
   * @param rpcMethods Optional RPC methods registry for REST API
   */
  async start(
    settings: AppSettings,
    rpcHandler?: RequestHandler,
    rpcMethods?: RpcMethodRegistry
  ): Promise<void> {
    // Store RPC methods for REST routes
    if (rpcMethods) {
      this.rpcMethods = rpcMethods;
    }
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

    // Add REST API routes if RPC methods provided
    let restRoutes: Record<string, RequestHandler> = {};
    let dynamicRestHandler: RequestHandler | null = null;
    if (this.rpcMethods) {
      restRoutes = createRestRoutes(this.rpcMethods);
      dynamicRestHandler = protect(createDynamicRestHandler(this.rpcMethods));

      // Add static REST routes (protected)
      for (const [path, handler] of Object.entries(restRoutes)) {
        routes[path] = protect(handler);
      }

      // Add API documentation endpoint
      routes['/api'] = async () => {
        return new Response(
          JSON.stringify({
            name: 'Auto Claude Mobile API',
            version: '1.0.0',
            endpoints: {
              rpc: {
                path: '/rpc',
                method: 'POST',
                description: 'JSON-RPC 2.0 endpoint',
                methods: [
                  'project.list', 'project.get', 'project.getActive', 'project.setActive',
                  'task.list', 'task.get', 'task.create', 'task.delete',
                  'task.start', 'task.stop', 'task.getStatus', 'task.updateStatus',
                  'system.health', 'system.version', 'system.getLogs'
                ]
              },
              rest: {
                projects: {
                  'GET /api/projects': 'List all projects',
                  'GET /api/projects/active': 'Get active project',
                  'GET /api/projects/:id': 'Get project by ID',
                  'POST /api/projects/:id/activate': 'Set active project',
                  'GET /api/projects/:id/tasks': 'List tasks for project',
                  'POST /api/projects/:id/tasks': 'Create task in project'
                },
                tasks: {
                  'GET /api/tasks/:id': 'Get task by ID',
                  'DELETE /api/tasks/:id': 'Delete task',
                  'POST /api/tasks/:id/start': 'Start task',
                  'POST /api/tasks/:id/stop': 'Stop task',
                  'GET /api/tasks/:id/status': 'Get task status',
                  'PUT /api/tasks/:id/status': 'Update task status',
                  'GET /api/tasks/:id/logs': 'Get task logs'
                },
                system: {
                  'GET /api/health': 'Health check',
                  'GET /api/version': 'Get version info'
                }
              }
            },
            authentication: {
              method: 'PIN',
              description: 'Authenticate via GET /auth?pin=XXXX to receive auth cookie'
            }
          }),
          {
            status: 200,
            headers: { 'Content-Type': 'application/json' }
          }
        );
      };
    }

    // Return Node.js http handler
    return async (req: http.IncomingMessage, res: http.ServerResponse) => {
      try {
        // Convert to Request object for middleware compatibility
        const url = new URL(req.url || '/', `http://${req.headers.host}`);

        // Read body for POST/PUT/PATCH requests
        let body: string | undefined;
        const method = req.method || 'GET';
        if (method !== 'GET' && method !== 'HEAD') {
          body = await this.readRequestBody(req);
        }

        const request = this.createFetchRequest(req, url, body);

        // Find matching route (exact match first)
        let handler = routes[url.pathname];

        // If no exact match and path starts with /api/, try dynamic REST handler
        if (!handler && url.pathname.startsWith('/api/') && dynamicRestHandler) {
          handler = dynamicRestHandler;
        }

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
   * Read request body from Node.js IncomingMessage
   *
   * @param req Node.js request
   * @returns Promise resolving to body string
   */
  private readRequestBody(req: http.IncomingMessage): Promise<string> {
    return new Promise((resolve, reject) => {
      const chunks: Buffer[] = [];

      req.on('data', (chunk: Buffer) => {
        chunks.push(chunk);
      });

      req.on('end', () => {
        resolve(Buffer.concat(chunks).toString('utf-8'));
      });

      req.on('error', (err) => {
        reject(err);
      });
    });
  }

  /**
   * Convert Node.js IncomingMessage to Fetch API Request
   *
   * @param req Node.js request
   * @param url Parsed URL
   * @param body Optional body string for POST/PUT requests
   * @returns Fetch API Request
   */
  private createFetchRequest(
    req: http.IncomingMessage,
    url: URL,
    body?: string
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

    // For POST/PUT/PATCH/DELETE, include body if provided
    return new Request(url.toString(), {
      method,
      headers,
      body: body || undefined,
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
