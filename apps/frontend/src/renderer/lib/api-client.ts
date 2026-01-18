/**
 * API Client for HTTP requests to /rpc endpoint
 *
 * Handles credentials (cookies) and LAN auth errors (UNAUTHORIZED)
 */

import { useLanAuthStore } from '@/stores/lan-auth-store';

/**
 * Error response from the API (supports both standard and oRPC format)
 */
export interface ApiError {
  code?: string;
  message?: string;
  status?: number;
  [key: string]: unknown;
}

/**
 * Error interceptor callback type
 */
export type ErrorInterceptor = (error: ApiError) => void | Promise<void>;

/**
 * Request interceptor callback type
 */
export type RequestInterceptor = (
  request: Request,
  init?: RequestInit
) => Request | Promise<Request>;

/**
 * Response interceptor callback type
 */
export type ResponseInterceptor = (response: Response) => Response | Promise<Response>;

/**
 * API client configuration
 */
export interface ApiClientConfig {
  /** Base URL for API requests (defaults to window.location.origin/rpc) */
  baseURL?: string;

  /** Custom fetch implementation (defaults to globalThis.fetch) */
  fetch?: typeof globalThis.fetch;

  /** Error interceptors to run on failed requests */
  errorInterceptors?: ErrorInterceptor[];

  /** Request interceptors to run before sending requests */
  requestInterceptors?: RequestInterceptor[];

  /** Response interceptors to run after receiving responses */
  responseInterceptors?: ResponseInterceptor[];

  /** Whether to include credentials (cookies) in requests (defaults to true) */
  credentials?: RequestCredentials;
}

/**
 * API client for making authenticated HTTP requests
 */
export class ApiClient {
  private baseURL: string;
  private fetchImpl: typeof globalThis.fetch;
  private errorInterceptors: ErrorInterceptor[];
  private requestInterceptors: RequestInterceptor[];
  private responseInterceptors: ResponseInterceptor[];
  private credentials: RequestCredentials;

  constructor(config: ApiClientConfig = {}) {
    this.baseURL = config.baseURL || `${window.location.origin}/rpc`;
    this.fetchImpl = config.fetch || globalThis.fetch.bind(globalThis);
    this.errorInterceptors = config.errorInterceptors || [];
    this.requestInterceptors = config.requestInterceptors || [];
    this.responseInterceptors = config.responseInterceptors || [];
    this.credentials = config.credentials || 'include';

    // Add default UNAUTHORIZED error interceptor
    this.addErrorInterceptor(this.defaultUnauthorizedHandler);
  }

  /**
   * Default handler for UNAUTHORIZED errors - triggers PIN entry modal
   */
  private defaultUnauthorizedHandler = (error: ApiError): void => {
    // Check for UNAUTHORIZED in both standard and oRPC error formats
    if (
      error.code === 'UNAUTHORIZED' ||
      error.status === 401 ||
      (error as { error?: { code?: string } }).error?.code === 'UNAUTHORIZED'
    ) {
      // Trigger PIN entry modal via Zustand store
      useLanAuthStore.getState().requireAuth();
    }
  };

  /**
   * Add an error interceptor
   */
  addErrorInterceptor(interceptor: ErrorInterceptor): void {
    this.errorInterceptors.push(interceptor);
  }

  /**
   * Add a request interceptor
   */
  addRequestInterceptor(interceptor: RequestInterceptor): void {
    this.requestInterceptors.push(interceptor);
  }

  /**
   * Add a response interceptor
   */
  addResponseInterceptor(interceptor: ResponseInterceptor): void {
    this.responseInterceptors.push(interceptor);
  }

  /**
   * Run error interceptors
   */
  private async runErrorInterceptors(error: ApiError): Promise<void> {
    for (const interceptor of this.errorInterceptors) {
      await interceptor(error);
    }
  }

  /**
   * Run request interceptors
   */
  private async runRequestInterceptors(
    request: Request,
    init?: RequestInit
  ): Promise<Request> {
    let modifiedRequest = request;
    for (const interceptor of this.requestInterceptors) {
      modifiedRequest = await interceptor(modifiedRequest, init);
    }
    return modifiedRequest;
  }

  /**
   * Run response interceptors
   */
  private async runResponseInterceptors(response: Response): Promise<Response> {
    let modifiedResponse = response;
    for (const interceptor of this.responseInterceptors) {
      modifiedResponse = await interceptor(modifiedResponse);
    }
    return modifiedResponse;
  }

  /**
   * Make an HTTP request
   *
   * @param path API path (appended to baseURL)
   * @param init Fetch options
   * @returns Response object
   */
  async request(path: string, init: RequestInit = {}): Promise<Response> {
    const url = `${this.baseURL}${path}`;

    // Create request with credentials
    const requestInit: RequestInit = {
      ...init,
      credentials: this.credentials,
    };

    let request = new Request(url, requestInit);

    // Run request interceptors
    request = await this.runRequestInterceptors(request, requestInit);

    try {
      // Make the request
      let response = await this.fetchImpl(request);

      // Run response interceptors
      response = await this.runResponseInterceptors(response);

      // Handle error responses
      if (!response.ok) {
        await this.handleErrorResponse(response);
      }

      return response;
    } catch (error) {
      // Handle network errors
      const apiError: ApiError = {
        code: 'NETWORK_ERROR',
        message: error instanceof Error ? error.message : 'Network error occurred',
        status: 0,
      };
      await this.runErrorInterceptors(apiError);
      throw error;
    }
  }

  /**
   * Handle error response from the API
   */
  private async handleErrorResponse(response: Response): Promise<void> {
    let error: ApiError = {
      status: response.status,
      message: response.statusText,
    };

    // Try to parse error body as JSON (supports oRPC and standard formats)
    try {
      const contentType = response.headers.get('content-type');
      if (contentType?.includes('application/json')) {
        const errorBody = await response.json();
        error = {
          ...error,
          ...errorBody,
          // Support oRPC nested error format
          code: errorBody.code || errorBody.error?.code || error.code,
          message: errorBody.message || errorBody.error?.message || error.message,
        };
      }
    } catch {
      // If JSON parsing fails, use status code as error code
      error.code = `HTTP_${response.status}`;
    }

    // Run error interceptors
    await this.runErrorInterceptors(error);

    // Throw the error for the caller to handle
    throw error;
  }

  /**
   * Make a GET request
   */
  async get(path: string, init: RequestInit = {}): Promise<Response> {
    return this.request(path, { ...init, method: 'GET' });
  }

  /**
   * Make a POST request
   */
  async post(path: string, body?: unknown, init: RequestInit = {}): Promise<Response> {
    const headers = new Headers(init.headers);
    if (body && !headers.has('content-type')) {
      headers.set('content-type', 'application/json');
    }

    return this.request(path, {
      ...init,
      method: 'POST',
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  /**
   * Make a PUT request
   */
  async put(path: string, body?: unknown, init: RequestInit = {}): Promise<Response> {
    const headers = new Headers(init.headers);
    if (body && !headers.has('content-type')) {
      headers.set('content-type', 'application/json');
    }

    return this.request(path, {
      ...init,
      method: 'PUT',
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  /**
   * Make a PATCH request
   */
  async patch(path: string, body?: unknown, init: RequestInit = {}): Promise<Response> {
    const headers = new Headers(init.headers);
    if (body && !headers.has('content-type')) {
      headers.set('content-type', 'application/json');
    }

    return this.request(path, {
      ...init,
      method: 'PATCH',
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  /**
   * Make a DELETE request
   */
  async delete(path: string, init: RequestInit = {}): Promise<Response> {
    return this.request(path, { ...init, method: 'DELETE' });
  }
}

/**
 * Create a default API client instance
 */
export function createApiClient(config: ApiClientConfig = {}): ApiClient {
  return new ApiClient(config);
}

/**
 * Default API client instance (singleton)
 */
export const apiClient = createApiClient();

/**
 * Helper to add error logging interceptor
 */
export function onError(handler: ErrorInterceptor): ErrorInterceptor {
  return handler;
}

/**
 * Helper to add request logging interceptor
 */
export function onRequest(handler: RequestInterceptor): RequestInterceptor {
  return handler;
}

/**
 * Helper to add response logging interceptor
 */
export function onResponse(handler: ResponseInterceptor): ResponseInterceptor {
  return handler;
}
