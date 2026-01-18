/**
 * LAN Access Module - Public API
 *
 * Exports the LAN access module for PIN-based authentication and network access.
 */

export {
  LanAccessModule,
  getLanAccessModule,
  createLanAccessModule,
} from './lan-module';

export type {
  NetworkInterface,
  LanConfig,
  LanUrls,
  NetworkAddresses,
} from './types';

// Existing PIN auth middleware with HTML page
export { pinAuthMiddleware } from './pin-auth-middleware';
export type { Middleware } from './pin-auth-middleware';

// New API-focused middleware (JSON responses)
export {
  pinAuthMiddleware as apiPinAuthMiddleware,
  createAuthEndpoint,
  withMiddleware,
} from './middleware';

export type {
  MiddlewareResponse,
  RequestHandler,
} from './middleware';

// Server configuration utilities
export {
  createServerConfig,
  createProtectedRoutes,
  createServerOptions,
  logLanAccessInfo,
} from './server-config';

export type {
  ServerOptions,
} from './server-config';

// QR Code Dialog component
export { LanQRDialog } from './LanQRDialog';
export type { LanQRDialogProps } from './LanQRDialog';
