/**
 * RPC Types for LAN/Tailscale Mobile Access
 *
 * Defines the JSON-RPC 2.0 compatible interface for mobile clients
 * to interact with Auto Claude over HTTP.
 */

import type { Task, TaskStatus, TaskMetadata, Project, IPCResult } from '../../shared/types';

/**
 * JSON-RPC 2.0 Request
 */
export interface RpcRequest {
  jsonrpc: '2.0';
  method: string;
  params?: Record<string, unknown>;
  id: string | number;
}

/**
 * JSON-RPC 2.0 Success Response
 */
export interface RpcSuccessResponse<T = unknown> {
  jsonrpc: '2.0';
  result: T;
  id: string | number;
}

/**
 * JSON-RPC 2.0 Error Response
 */
export interface RpcErrorResponse {
  jsonrpc: '2.0';
  error: {
    code: number;
    message: string;
    data?: unknown;
  };
  id: string | number | null;
}

/**
 * Union type for RPC responses
 */
export type RpcResponse<T = unknown> = RpcSuccessResponse<T> | RpcErrorResponse;

/**
 * Standard JSON-RPC error codes
 */
export const RPC_ERROR_CODES = {
  PARSE_ERROR: -32700,
  INVALID_REQUEST: -32600,
  METHOD_NOT_FOUND: -32601,
  INVALID_PARAMS: -32602,
  INTERNAL_ERROR: -32603,
  // Custom error codes (range: -32000 to -32099)
  UNAUTHORIZED: -32000,
  NOT_FOUND: -32001,
  TASK_RUNNING: -32002,
  AUTH_REQUIRED: -32003,
  GIT_REQUIRED: -32004,
} as const;

/**
 * RPC Method names
 */
export type RpcMethodName =
  // Project methods
  | 'project.list'
  | 'project.get'
  | 'project.getActive'
  | 'project.setActive'
  // Task methods
  | 'task.list'
  | 'task.get'
  | 'task.create'
  | 'task.delete'
  | 'task.start'
  | 'task.stop'
  | 'task.getStatus'
  | 'task.updateStatus'
  // System methods
  | 'system.health'
  | 'system.version'
  | 'system.getLogs';

/**
 * Parameter types for each RPC method
 */
export interface RpcMethodParams {
  // Project methods
  'project.list': Record<string, never>;
  'project.get': { projectId: string };
  'project.getActive': Record<string, never>;
  'project.setActive': { projectId: string };
  // Task methods
  'task.list': { projectId: string };
  'task.get': { taskId: string };
  'task.create': {
    projectId: string;
    title: string;
    description: string;
    metadata?: TaskMetadata;
  };
  'task.delete': { taskId: string };
  'task.start': { taskId: string };
  'task.stop': { taskId: string };
  'task.getStatus': { taskId: string };
  'task.updateStatus': { taskId: string; status: TaskStatus };
  // System methods
  'system.health': Record<string, never>;
  'system.version': Record<string, never>;
  'system.getLogs': { taskId: string; limit?: number };
}

/**
 * Return types for each RPC method
 */
export interface RpcMethodReturns {
  // Project methods
  'project.list': Project[];
  'project.get': Project | null;
  'project.getActive': Project | null;
  'project.setActive': { success: boolean };
  // Task methods
  'task.list': Task[];
  'task.get': Task | null;
  'task.create': Task;
  'task.delete': { success: boolean };
  'task.start': { success: boolean; message: string };
  'task.stop': { success: boolean };
  'task.getStatus': { status: TaskStatus; isRunning: boolean };
  'task.updateStatus': { success: boolean };
  // System methods
  'system.health': { status: 'ok'; timestamp: string };
  'system.version': { version: string; platform: string };
  'system.getLogs': { logs: string[] };
}

/**
 * RPC Method handler type
 */
export type RpcMethodHandler<M extends RpcMethodName> = (
  params: RpcMethodParams[M]
) => Promise<RpcMethodReturns[M]>;

/**
 * Registry of all RPC method handlers
 */
export type RpcMethodRegistry = {
  [M in RpcMethodName]: RpcMethodHandler<M>;
};

/**
 * Helper to create typed RPC success response
 */
export function createSuccessResponse<T>(
  result: T,
  id: string | number
): RpcSuccessResponse<T> {
  return {
    jsonrpc: '2.0',
    result,
    id,
  };
}

/**
 * Helper to create typed RPC error response
 */
export function createErrorResponse(
  code: number,
  message: string,
  id: string | number | null,
  data?: unknown
): RpcErrorResponse {
  return {
    jsonrpc: '2.0',
    error: {
      code,
      message,
      ...(data !== undefined && { data }),
    },
    id,
  };
}
