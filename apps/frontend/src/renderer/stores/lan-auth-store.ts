/**
 * LAN Authentication State Store
 *
 * Manages PIN authentication state for LAN access using Zustand.
 * Used by API client error interceptors and PIN entry components.
 */

import { create } from 'zustand';

/**
 * LAN authentication state
 */
export interface LanAuthState {
  /** Whether PIN entry is currently required */
  needsAuth: boolean;

  /** Trigger PIN entry modal (called by API client on 401 errors) */
  requireAuth: () => void;

  /** Clear auth requirement (called after successful PIN entry) */
  clearAuth: () => void;

  /** Track number of failed auth attempts */
  failedAttempts: number;

  /** Increment failed attempts counter */
  incrementFailedAttempts: () => void;

  /** Reset failed attempts counter */
  resetFailedAttempts: () => void;
}

/**
 * Create LAN authentication store
 *
 * @example
 * ```tsx
 * // In API client error interceptor
 * import { useLanAuthStore } from '@/stores/lan-auth-store';
 *
 * async function handleApiError(error: ApiError) {
 *   if (error.status === 401 && error.code === 'UNAUTHORIZED') {
 *     const { requireAuth } = useLanAuthStore.getState();
 *     requireAuth();
 *   }
 * }
 *
 * // In PIN entry component
 * function PinEntryModal() {
 *   const { needsAuth, clearAuth, failedAttempts } = useLanAuthStore();
 *
 *   const handleSubmit = async (pin: string) => {
 *     try {
 *       await authenticateWithPin(pin);
 *       clearAuth();
 *     } catch (error) {
 *       // Error handling
 *     }
 *   };
 *
 *   if (!needsAuth) return null;
 *
 *   return (
 *     <Modal>
 *       <PinInput onSubmit={handleSubmit} />
 *       {failedAttempts > 0 && <ErrorMessage />}
 *     </Modal>
 *   );
 * }
 * ```
 */
export const useLanAuthStore = create<LanAuthState>((set) => ({
  needsAuth: false,
  failedAttempts: 0,

  requireAuth: () => {
    set({ needsAuth: true });
  },

  clearAuth: () => {
    set({ needsAuth: false, failedAttempts: 0 });
  },

  incrementFailedAttempts: () => {
    set((state) => ({ failedAttempts: state.failedAttempts + 1 }));
  },

  resetFailedAttempts: () => {
    set({ failedAttempts: 0 });
  },
}));

/**
 * Hook to check if LAN auth is required
 *
 * @returns Whether PIN entry is currently required
 *
 * @example
 * ```tsx
 * function App() {
 *   const needsAuth = useNeedsAuth();
 *
 *   return (
 *     <div>
 *       {needsAuth && <PinEntryModal />}
 *       <MainContent />
 *     </div>
 *   );
 * }
 * ```
 */
export function useNeedsAuth(): boolean {
  return useLanAuthStore((state) => state.needsAuth);
}

/**
 * Hook to get auth actions
 *
 * @returns Auth action functions
 *
 * @example
 * ```tsx
 * function ApiClient() {
 *   const { requireAuth } = useLanAuthActions();
 *
 *   const handleUnauthorized = () => {
 *     requireAuth();
 *   };
 *
 *   // ... rest of component
 * }
 * ```
 */
export function useLanAuthActions() {
  return useLanAuthStore((state) => ({
    requireAuth: state.requireAuth,
    clearAuth: state.clearAuth,
    incrementFailedAttempts: state.incrementFailedAttempts,
    resetFailedAttempts: state.resetFailedAttempts,
  }));
}

/**
 * Hook to get failed attempts count
 *
 * @returns Number of failed authentication attempts
 *
 * @example
 * ```tsx
 * function PinEntryForm() {
 *   const failedAttempts = useFailedAttempts();
 *
 *   return (
 *     <div>
 *       {failedAttempts > 0 && (
 *         <ErrorMessage>
 *           Invalid PIN. {failedAttempts} failed attempt(s).
 *         </ErrorMessage>
 *       )}
 *     </div>
 *   );
 * }
 * ```
 */
export function useFailedAttempts(): number {
  return useLanAuthStore((state) => state.failedAttempts);
}
