/**
 * REST-like API Routes for Mobile Access
 *
 * Provides simple GET/POST endpoints that are easier for mobile clients
 * to consume than JSON-RPC. These wrap the RPC methods internally.
 */

import type { RpcMethodRegistry } from './types';
import { RpcError } from './methods';

type RequestHandler = (request: Request) => Promise<Response>;

/**
 * Create JSON response helper
 */
function jsonResponse(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

/**
 * Create error response helper
 */
function errorResponse(message: string, status = 400): Response {
  return jsonResponse({ error: message }, status);
}

/**
 * Extract URL parameters from path
 * e.g., /api/projects/:id -> { id: 'actual-id' }
 */
function matchPath(
  pattern: string,
  pathname: string
): Record<string, string> | null {
  const patternParts = pattern.split('/');
  const pathParts = pathname.split('/');

  if (patternParts.length !== pathParts.length) {
    return null;
  }

  const params: Record<string, string> = {};

  for (let i = 0; i < patternParts.length; i++) {
    const patternPart = patternParts[i];
    const pathPart = pathParts[i];

    if (patternPart.startsWith(':')) {
      // Parameter capture
      params[patternPart.slice(1)] = pathPart;
    } else if (patternPart !== pathPart) {
      // No match
      return null;
    }
  }

  return params;
}

/**
 * Create REST API routes that wrap RPC methods
 */
export function createRestRoutes(methods: RpcMethodRegistry): Record<string, RequestHandler> {
  const routes: Record<string, RequestHandler> = {};

  // ─────────────────────────────────────────────────────────────────────────
  // System Routes
  // ─────────────────────────────────────────────────────────────────────────

  routes['/api/health'] = async () => {
    const result = await methods['system.health']({});
    return jsonResponse(result);
  };

  routes['/api/version'] = async () => {
    const result = await methods['system.version']({});
    return jsonResponse(result);
  };

  // ─────────────────────────────────────────────────────────────────────────
  // Project Routes
  // ─────────────────────────────────────────────────────────────────────────

  routes['/api/projects'] = async (request) => {
    if (request.method === 'GET') {
      const result = await methods['project.list']({});
      return jsonResponse(result);
    }
    return errorResponse('Method not allowed', 405);
  };

  routes['/api/projects/active'] = async (request) => {
    if (request.method === 'GET') {
      const result = await methods['project.getActive']({});
      return jsonResponse(result);
    }
    return errorResponse('Method not allowed', 405);
  };

  // ─────────────────────────────────────────────────────────────────────────
  // Task Routes
  // ─────────────────────────────────────────────────────────────────────────

  // Note: Dynamic routes need special handling in the router

  return routes;
}

/**
 * Dynamic route handler for REST API
 * Handles parameterized routes like /api/projects/:id/tasks
 */
export function createDynamicRestHandler(
  methods: RpcMethodRegistry
): RequestHandler {
  return async (request: Request): Promise<Response> => {
    const url = new URL(request.url);
    const pathname = url.pathname;

    try {
      // GET /api/projects/:projectId
      let params = matchPath('/api/projects/:projectId', pathname);
      if (params && request.method === 'GET') {
        const result = await methods['project.get']({ projectId: params.projectId });
        if (!result) {
          return errorResponse('Project not found', 404);
        }
        return jsonResponse(result);
      }

      // POST /api/projects/:projectId/activate
      params = matchPath('/api/projects/:projectId/activate', pathname);
      if (params && request.method === 'POST') {
        const result = await methods['project.setActive']({ projectId: params.projectId });
        return jsonResponse(result);
      }

      // GET /api/projects/:projectId/tasks
      params = matchPath('/api/projects/:projectId/tasks', pathname);
      if (params && request.method === 'GET') {
        const result = await methods['task.list']({ projectId: params.projectId });
        return jsonResponse(result);
      }

      // POST /api/projects/:projectId/tasks
      if (params && request.method === 'POST') {
        const body = await request.json() as {
          title?: string;
          description: string;
          metadata?: Record<string, unknown>;
        };
        if (!body.description) {
          return errorResponse('description is required');
        }
        const result = await methods['task.create']({
          projectId: params.projectId,
          title: body.title || '',
          description: body.description,
          metadata: body.metadata as never,
        });
        return jsonResponse(result, 201);
      }

      // GET /api/tasks/:taskId
      params = matchPath('/api/tasks/:taskId', pathname);
      if (params && request.method === 'GET') {
        const result = await methods['task.get']({ taskId: params.taskId });
        if (!result) {
          return errorResponse('Task not found', 404);
        }
        return jsonResponse(result);
      }

      // DELETE /api/tasks/:taskId
      if (params && request.method === 'DELETE') {
        const result = await methods['task.delete']({ taskId: params.taskId });
        return jsonResponse(result);
      }

      // POST /api/tasks/:taskId/start
      params = matchPath('/api/tasks/:taskId/start', pathname);
      if (params && request.method === 'POST') {
        const result = await methods['task.start']({ taskId: params.taskId });
        return jsonResponse(result);
      }

      // POST /api/tasks/:taskId/stop
      params = matchPath('/api/tasks/:taskId/stop', pathname);
      if (params && request.method === 'POST') {
        const result = await methods['task.stop']({ taskId: params.taskId });
        return jsonResponse(result);
      }

      // GET /api/tasks/:taskId/status
      params = matchPath('/api/tasks/:taskId/status', pathname);
      if (params && request.method === 'GET') {
        const result = await methods['task.getStatus']({ taskId: params.taskId });
        return jsonResponse(result);
      }

      // PUT /api/tasks/:taskId/status
      if (params && request.method === 'PUT') {
        const body = await request.json() as { status: string };
        if (!body.status) {
          return errorResponse('status is required');
        }
        const result = await methods['task.updateStatus']({
          taskId: params.taskId,
          status: body.status as never,
        });
        return jsonResponse(result);
      }

      // GET /api/tasks/:taskId/logs
      params = matchPath('/api/tasks/:taskId/logs', pathname);
      if (params && request.method === 'GET') {
        const limitParam = url.searchParams.get('limit');
        const limit = limitParam ? parseInt(limitParam, 10) : undefined;
        const result = await methods['system.getLogs']({
          taskId: params.taskId,
          limit,
        });
        return jsonResponse(result);
      }

      // No route matched
      return errorResponse('Not Found', 404);
    } catch (error) {
      console.error('[REST] Error handling request:', error);

      if (error instanceof RpcError) {
        const status =
          error.code === -32001 ? 404 : // NOT_FOUND
          error.code === -32002 ? 409 : // TASK_RUNNING (conflict)
          400;
        return errorResponse(error.message, status);
      }

      return errorResponse(
        error instanceof Error ? error.message : 'Internal Server Error',
        500
      );
    }
  };
}
