/**
 * LAN PIN Authentication Middleware
 *
 * Provides middleware for protecting HTTP routes with PIN-based authentication
 * when LAN access is enabled.
 */

import type { LanAccessModule } from './lan-module';

/**
 * Cookie configuration for PIN authentication
 */
const AUTH_COOKIE_NAME = 'auto-claude-lan-auth';
const COOKIE_MAX_AGE = 24 * 60 * 60; // 24 hours in seconds

/**
 * Check if request is from localhost
 */
function isLocalhost(hostname: string): boolean {
  return hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '::1';
}

/**
 * Parse cookies from request headers
 */
function parseCookies(cookieHeader: string | null): Record<string, string> {
  if (!cookieHeader) return {};

  return cookieHeader.split(';').reduce((cookies, cookie) => {
    const [name, ...rest] = cookie.trim().split('=');
    if (name && rest.length > 0) {
      cookies[name] = rest.join('=');
    }
    return cookies;
  }, {} as Record<string, string>);
}

/**
 * Extract PIN from auth cookie
 */
function getPinFromCookie(request: Request): string | null {
  const cookieHeader = request.headers.get('cookie');
  const cookies = parseCookies(cookieHeader);
  return cookies[AUTH_COOKIE_NAME] || null;
}

/**
 * Check if request has valid authentication
 */
function isAuthenticated(request: Request, lanModule: LanAccessModule): boolean {
  const pin = getPinFromCookie(request);
  if (!pin) return false;

  return lanModule.validatePin(pin);
}

/**
 * Middleware response types
 */
export type MiddlewareResponse = Response | null;
export type RequestHandler = (request: Request) => Promise<Response> | Response;

/**
 * Create PIN authentication middleware
 *
 * @param lanModule LAN access module instance for PIN validation
 * @param allowLan Whether LAN access is enabled
 * @returns Middleware function that checks PIN authentication
 *
 * @example
 * ```ts
 * const middleware = pinAuthMiddleware(getLanAccessModule(), config.allowLan);
 * const protectedHandler = withMiddleware(middleware)(rpcHandler);
 * ```
 */
export function pinAuthMiddleware(
  lanModule: LanAccessModule,
  allowLan: boolean
): (request: Request) => MiddlewareResponse {
  return (request: Request): MiddlewareResponse => {
    // If LAN access is disabled, allow all requests
    if (!allowLan) {
      return null; // Continue to handler
    }

    // Parse URL to check hostname
    const url = new URL(request.url);

    // Allow localhost without authentication
    if (isLocalhost(url.hostname)) {
      return null; // Continue to handler
    }

    // Check if request has valid authentication
    if (isAuthenticated(request, lanModule)) {
      return null; // Continue to handler
    }

    // Reject with 401 Unauthorized
    return new Response(
      JSON.stringify({
        error: 'Unauthorized',
        message: 'PIN authentication required',
        code: 'UNAUTHORIZED',
      }),
      {
        status: 401,
        headers: {
          'Content-Type': 'application/json',
          'WWW-Authenticate': 'Cookie',
        },
      }
    );
  };
}

/**
 * Compose middleware with a request handler
 *
 * @param middleware Middleware function to apply
 * @returns Function that wraps a handler with middleware
 *
 * @example
 * ```ts
 * const middleware = pinAuthMiddleware(lanModule, true);
 * const protectedHandler = withMiddleware(middleware)(myHandler);
 * ```
 */
export function withMiddleware(
  middleware: (request: Request) => MiddlewareResponse
): (handler: RequestHandler) => RequestHandler {
  return (handler: RequestHandler): RequestHandler => {
    return async (request: Request): Promise<Response> => {
      // Run middleware
      const middlewareResponse = middleware(request);

      // If middleware returns a response, return it (auth failed)
      if (middlewareResponse) {
        return middlewareResponse;
      }

      // Otherwise, continue to handler
      return handler(request);
    };
  };
}

/**
 * Create auth endpoint handler
 *
 * Handles PIN authentication via query parameter and sets auth cookie.
 *
 * @param lanModule LAN access module instance for PIN validation
 * @param allowLan Whether LAN access is enabled
 * @returns Request handler for /auth endpoint
 *
 * @example
 * ```ts
 * const authHandler = createAuthEndpoint(getLanAccessModule(), config.allowLan);
 * // Use in routes: "/auth": authHandler
 * ```
 */
export function createAuthEndpoint(
  lanModule: LanAccessModule,
  allowLan: boolean
): RequestHandler {
  return (request: Request): Response => {
    const url = new URL(request.url);

    // If localhost, redirect to home (no auth needed)
    if (isLocalhost(url.hostname)) {
      return new Response(null, {
        status: 302,
        headers: {
          Location: '/',
        },
      });
    }

    // If LAN is disabled, redirect to home
    if (!allowLan) {
      return new Response(null, {
        status: 302,
        headers: {
          Location: '/',
        },
      });
    }

    // Check if already authenticated
    if (isAuthenticated(request, lanModule)) {
      return new Response(null, {
        status: 302,
        headers: {
          Location: '/',
        },
      });
    }

    // Get PIN from query parameter
    const pin = url.searchParams.get('pin');

    // If no PIN provided, return error
    if (!pin) {
      return new Response(
        JSON.stringify({
          error: 'Bad Request',
          message: 'PIN parameter is required',
          code: 'MISSING_PIN',
        }),
        {
          status: 400,
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );
    }

    // Validate PIN
    if (!lanModule.validatePin(pin)) {
      return new Response(
        JSON.stringify({
          error: 'Unauthorized',
          message: 'Invalid PIN',
          code: 'INVALID_PIN',
        }),
        {
          status: 401,
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );
    }

    // PIN is valid - set cookie and redirect to home
    const cookieValue = `${AUTH_COOKIE_NAME}=${pin}; HttpOnly; Max-Age=${COOKIE_MAX_AGE}; Path=/; SameSite=Strict`;

    return new Response(null, {
      status: 302,
      headers: {
        Location: '/',
        'Set-Cookie': cookieValue,
      },
    });
  };
}
