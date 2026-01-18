/**
 * Frontend Integration Example - LAN Auth State Management
 *
 * This file demonstrates how to integrate the LAN authentication Zustand store
 * into your React application for PIN-based authentication.
 *
 * @example
 * See the examples below for:
 * - API client error handling
 * - PIN entry modal component
 * - Auth state management
 * - Complete integration
 */

import React, { useState, useEffect } from 'react';
import {
  useLanAuthStore,
  useNeedsAuth,
  useLanAuthActions,
  useFailedAttempts,
} from './lan-auth-store';

// ============================================================================
// EXAMPLE 1: API Client Error Interceptor
// ============================================================================

/**
 * API error response type
 */
interface ApiError {
  status: number;
  code?: string;
  message?: string;
}

/**
 * API client with automatic auth handling
 */
export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = '') {
    this.baseUrl = baseUrl;
  }

  /**
   * Make an API request with auth error handling
   */
  async request<T = any>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
      });

      // Handle authentication errors
      if (response.status === 401) {
        const data = await response.json().catch(() => ({}));

        if (data.code === 'UNAUTHORIZED') {
          // Trigger PIN entry modal
          const { requireAuth } = useLanAuthStore.getState();
          requireAuth();

          throw new Error('Authentication required');
        }
      }

      // Handle other errors
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      return response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  /**
   * Example: Call RPC endpoint
   */
  async callRpc(method: string, params: any): Promise<any> {
    return this.request('/rpc', {
      method: 'POST',
      body: JSON.stringify({
        jsonrpc: '2.0',
        id: Date.now(),
        method,
        params,
      }),
    });
  }
}

// ============================================================================
// EXAMPLE 2: PIN Entry Modal Component
// ============================================================================

/**
 * PIN entry modal component
 */
export function PinEntryModal(): JSX.Element | null {
  const needsAuth = useNeedsAuth();
  const { clearAuth, incrementFailedAttempts, resetFailedAttempts } = useLanAuthActions();
  const failedAttempts = useFailedAttempts();
  const [pin, setPin] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Reset state when modal opens
  useEffect(() => {
    if (needsAuth) {
      setPin('');
      setIsSubmitting(false);
    }
  }, [needsAuth]);

  if (!needsAuth) {
    return null;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (pin.length !== 4) {
      return;
    }

    setIsSubmitting(true);

    try {
      // Attempt authentication by navigating to /auth endpoint
      const url = new URL('/auth', window.location.origin);
      url.searchParams.set('pin', pin);

      const response = await fetch(url.toString(), {
        method: 'GET',
        credentials: 'include', // Include cookies
      });

      if (response.ok || response.status === 302) {
        // Success - cookie is set, clear auth requirement
        resetFailedAttempts();
        clearAuth();
      } else {
        // Failed - increment counter
        incrementFailedAttempts();
        setPin('');
      }
    } catch (error) {
      console.error('Auth error:', error);
      incrementFailedAttempts();
      setPin('');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-8 max-w-md w-full">
        <h2 className="text-2xl font-bold mb-4">Enter PIN</h2>
        <p className="text-gray-600 mb-6">
          Enter your 4-digit PIN to access this device
        </p>

        <form onSubmit={handleSubmit}>
          <input
            type="text"
            inputMode="numeric"
            pattern="[0-9]*"
            maxLength={4}
            value={pin}
            onChange={(e) => setPin(e.target.value.replace(/\D/g, ''))}
            className="w-full text-center text-3xl tracking-widest border-2 border-gray-300 rounded-lg p-4 mb-4 focus:outline-none focus:border-blue-500"
            placeholder="····"
            autoFocus
            disabled={isSubmitting}
          />

          {failedAttempts > 0 && (
            <div className="text-red-500 text-sm mb-4">
              Invalid PIN. {failedAttempts} failed attempt(s).
            </div>
          )}

          <button
            type="submit"
            disabled={pin.length !== 4 || isSubmitting}
            className="w-full bg-blue-500 text-white py-3 rounded-lg font-semibold hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            {isSubmitting ? 'Verifying...' : 'Unlock'}
          </button>
        </form>
      </div>
    </div>
  );
}

// ============================================================================
// EXAMPLE 3: Advanced PIN Entry with Individual Digits
// ============================================================================

/**
 * PIN digit input component (like iOS PIN entry)
 */
export function AdvancedPinEntryModal(): JSX.Element | null {
  const needsAuth = useNeedsAuth();
  const { clearAuth, incrementFailedAttempts, resetFailedAttempts } = useLanAuthActions();
  const failedAttempts = useFailedAttempts();
  const [digits, setDigits] = useState<string[]>(['', '', '', '']);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const inputRefs = React.useRef<(HTMLInputElement | null)[]>([]);

  useEffect(() => {
    if (needsAuth) {
      setDigits(['', '', '', '']);
      setIsSubmitting(false);
      inputRefs.current[0]?.focus();
    }
  }, [needsAuth]);

  if (!needsAuth) {
    return null;
  }

  const handleDigitChange = (index: number, value: string) => {
    // Only allow single digit
    const digit = value.slice(-1).replace(/\D/g, '');

    const newDigits = [...digits];
    newDigits[index] = digit;
    setDigits(newDigits);

    // Auto-focus next input
    if (digit && index < 3) {
      inputRefs.current[index + 1]?.focus();
    }

    // Auto-submit when all digits entered
    if (index === 3 && digit && newDigits.every((d) => d !== '')) {
      submitPin(newDigits.join(''));
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !digits[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const submitPin = async (pin: string) => {
    setIsSubmitting(true);

    try {
      const url = new URL('/auth', window.location.origin);
      url.searchParams.set('pin', pin);

      const response = await fetch(url.toString(), {
        method: 'GET',
        credentials: 'include',
      });

      if (response.ok || response.status === 302) {
        resetFailedAttempts();
        clearAuth();
      } else {
        incrementFailedAttempts();
        setDigits(['', '', '', '']);
        inputRefs.current[0]?.focus();
      }
    } catch (error) {
      console.error('Auth error:', error);
      incrementFailedAttempts();
      setDigits(['', '', '', '']);
      inputRefs.current[0]?.focus();
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-8 max-w-md w-full">
        <h2 className="text-2xl font-bold mb-4 text-center">Enter PIN</h2>
        <p className="text-gray-600 mb-8 text-center">
          Enter your 4-digit PIN to access this device
        </p>

        <div className="flex gap-4 justify-center mb-6">
          {digits.map((digit, index) => (
            <input
              key={index}
              ref={(el) => (inputRefs.current[index] = el)}
              type="text"
              inputMode="numeric"
              pattern="[0-9]"
              maxLength={1}
              value={digit}
              onChange={(e) => handleDigitChange(index, e.target.value)}
              onKeyDown={(e) => handleKeyDown(index, e)}
              className="w-16 h-16 text-center text-3xl border-2 border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              disabled={isSubmitting}
            />
          ))}
        </div>

        {failedAttempts > 0 && (
          <div className="text-red-500 text-sm text-center mb-4">
            Invalid PIN. {failedAttempts} failed attempt(s).
          </div>
        )}

        <p className="text-gray-500 text-sm text-center">
          PIN will be remembered for 24 hours
        </p>
      </div>
    </div>
  );
}

// ============================================================================
// EXAMPLE 4: Complete App Integration
// ============================================================================

/**
 * Main app component with LAN auth integration
 */
export function AppWithLanAuth(): JSX.Element {
  const needsAuth = useNeedsAuth();

  return (
    <div className="app">
      {/* PIN entry modal (shown when auth required) */}
      {needsAuth && <AdvancedPinEntryModal />}

      {/* Main app content */}
      <MainAppContent />
    </div>
  );
}

/**
 * Main app content (your actual app)
 */
function MainAppContent(): JSX.Element {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const apiClient = new ApiClient();

  const fetchData = async () => {
    setLoading(true);
    try {
      const result = await apiClient.callRpc('getData', {});
      setData(result);
    } catch (error) {
      console.error('Failed to fetch data:', error);
      // Error is handled by ApiClient (shows PIN modal if 401)
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-4">My App</h1>

      <button
        onClick={fetchData}
        disabled={loading}
        className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 disabled:bg-gray-300"
      >
        {loading ? 'Loading...' : 'Fetch Data'}
      </button>

      {data && (
        <div className="mt-4 p-4 bg-gray-100 rounded">
          <pre>{JSON.stringify(data, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// EXAMPLE 5: Custom Hook for API Calls with Auth
// ============================================================================

/**
 * Custom hook for API calls with automatic auth handling
 */
export function useAuthenticatedApi() {
  const { requireAuth } = useLanAuthActions();
  const apiClient = new ApiClient();

  const makeRequest = async <T = any>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T | null> => {
    try {
      return await apiClient.request<T>(endpoint, options);
    } catch (error: any) {
      if (error.message === 'Authentication required') {
        // Auth modal is already shown by ApiClient
        return null;
      }
      throw error;
    }
  };

  return { makeRequest };
}

/**
 * Example component using the custom hook
 */
export function DataFetcherComponent(): JSX.Element {
  const { makeRequest } = useAuthenticatedApi();
  const [projects, setProjects] = useState<any[]>([]);

  useEffect(() => {
    makeRequest('/api/projects')
      .then((data) => {
        if (data) {
          setProjects(data.projects || []);
        }
      })
      .catch(console.error);
  }, []);

  return (
    <div>
      <h2>Projects</h2>
      <ul>
        {projects.map((project) => (
          <li key={project.id}>{project.name}</li>
        ))}
      </ul>
    </div>
  );
}

// ============================================================================
// EXAMPLE 6: Auth Status Indicator
// ============================================================================

/**
 * Component that shows auth status
 */
export function AuthStatusIndicator(): JSX.Element {
  const needsAuth = useNeedsAuth();

  return (
    <div className="fixed top-4 right-4 z-40">
      {needsAuth ? (
        <div className="bg-yellow-500 text-white px-4 py-2 rounded-lg shadow-lg">
          🔒 Authentication Required
        </div>
      ) : (
        <div className="bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg">
          ✅ Authenticated
        </div>
      )}
    </div>
  );
}
