/**
 * RPC Request Handler
 *
 * Handles incoming HTTP RPC requests, parses JSON-RPC 2.0 messages,
 * validates requests, and routes them to appropriate method handlers.
 */

import type * as http from 'http';
import type { RpcMethodName, RpcMethodRegistry } from './types';
import {
  RPC_ERROR_CODES,
  createSuccessResponse,
  createErrorResponse,
} from './types';
import { RpcError } from './methods';

/**
 * Read request body as string
 */
async function readRequestBody(req: http.IncomingMessage): Promise<string> {
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
 * Parse JSON-RPC 2.0 request
 */
function parseRpcRequest(body: string): {
  jsonrpc?: string;
  method?: string;
  params?: Record<string, unknown>;
  id?: string | number;
} | null {
  try {
    return JSON.parse(body);
  } catch {
    return null;
  }
}

/**
 * Validate JSON-RPC 2.0 request structure
 */
function validateRpcRequest(request: unknown): {
  valid: boolean;
  error?: { code: number; message: string };
} {
  if (!request || typeof request !== 'object') {
    return {
      valid: false,
      error: { code: RPC_ERROR_CODES.INVALID_REQUEST, message: 'Invalid Request' },
    };
  }

  const req = request as Record<string, unknown>;

  if (req.jsonrpc !== '2.0') {
    return {
      valid: false,
      error: { code: RPC_ERROR_CODES.INVALID_REQUEST, message: 'Invalid jsonrpc version' },
    };
  }

  if (typeof req.method !== 'string') {
    return {
      valid: false,
      error: { code: RPC_ERROR_CODES.INVALID_REQUEST, message: 'Method must be a string' },
    };
  }

  if (req.params !== undefined && typeof req.params !== 'object') {
    return {
      valid: false,
      error: { code: RPC_ERROR_CODES.INVALID_PARAMS, message: 'Params must be an object' },
    };
  }

  return { valid: true };
}

/**
 * Create RPC request handler
 */
export function createRpcHandler(methods: RpcMethodRegistry) {
  /**
   * Handle a parsed RPC request
   */
  async function handleRpcRequest(
    method: string,
    params: Record<string, unknown>,
    id: string | number
  ): Promise<Response> {
    // Check if method exists
    if (!(method in methods)) {
      return new Response(
        JSON.stringify(
          createErrorResponse(
            RPC_ERROR_CODES.METHOD_NOT_FOUND,
            `Method not found: ${method}`,
            id
          )
        ),
        {
          status: 200, // JSON-RPC uses 200 for all responses
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    try {
      // Call the method handler
      const handler = methods[method as RpcMethodName];
      const result = await handler(params as never);

      return new Response(
        JSON.stringify(createSuccessResponse(result, id)),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    } catch (error) {
      console.error(`[RPC] Error in method ${method}:`, error);

      if (error instanceof RpcError) {
        return new Response(
          JSON.stringify(
            createErrorResponse(error.code, error.message, id, error.data)
          ),
          {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          }
        );
      }

      return new Response(
        JSON.stringify(
          createErrorResponse(
            RPC_ERROR_CODES.INTERNAL_ERROR,
            error instanceof Error ? error.message : 'Internal error',
            id
          )
        ),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }
  }

  /**
   * Main request handler for HTTP server
   */
  return async function rpcHandler(request: Request): Promise<Response> {
    // Only accept POST requests
    if (request.method !== 'POST') {
      return new Response(
        JSON.stringify(
          createErrorResponse(
            RPC_ERROR_CODES.INVALID_REQUEST,
            'Method not allowed. Use POST.',
            null
          )
        ),
        {
          status: 405,
          headers: {
            'Content-Type': 'application/json',
            Allow: 'POST',
          },
        }
      );
    }

    // Read body
    let body: string;
    try {
      body = await request.text();
    } catch (error) {
      console.error('[RPC] Failed to read request body:', error);
      return new Response(
        JSON.stringify(
          createErrorResponse(
            RPC_ERROR_CODES.PARSE_ERROR,
            'Failed to read request body',
            null
          )
        ),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Parse JSON
    const parsed = parseRpcRequest(body);
    if (!parsed) {
      return new Response(
        JSON.stringify(
          createErrorResponse(
            RPC_ERROR_CODES.PARSE_ERROR,
            'Parse error: Invalid JSON',
            null
          )
        ),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Validate structure
    const validation = validateRpcRequest(parsed);
    if (!validation.valid && validation.error) {
      return new Response(
        JSON.stringify(
          createErrorResponse(
            validation.error.code,
            validation.error.message,
            parsed.id || null
          )
        ),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Handle the request
    return handleRpcRequest(
      parsed.method!,
      (parsed.params || {}) as Record<string, unknown>,
      parsed.id || 0
    );
  };
}

/**
 * Get list of available methods for introspection
 */
export function getAvailableMethods(): string[] {
  return [
    'project.list',
    'project.get',
    'project.getActive',
    'project.setActive',
    'task.list',
    'task.get',
    'task.create',
    'task.delete',
    'task.start',
    'task.stop',
    'task.getStatus',
    'task.updateStatus',
    'system.health',
    'system.version',
    'system.getLogs',
  ];
}
