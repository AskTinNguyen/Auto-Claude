/**
 * API Client Usage Examples
 *
 * This file demonstrates how to use the API client for making authenticated
 * HTTP requests to the /rpc endpoint with LAN auth handling.
 *
 * DO NOT IMPORT THIS FILE - It's for documentation purposes only.
 */

/* eslint-disable @typescript-eslint/no-unused-vars */

import {
  apiClient,
  createApiClient,
  onError,
  onRequest,
  onResponse,
  type ApiError,
} from './api-client';

// ============================================================================
// Example 1: Basic Usage with Default Client
// ============================================================================

async function basicExample() {
  try {
    // GET request
    const response = await apiClient.get('/health');
    const data = await response.json();
    console.log('Health check:', data);

    // POST request with body
    const createResponse = await apiClient.post('/tasks', {
      title: 'New Task',
      description: 'Task description',
    });
    const createdTask = await createResponse.json();
    console.log('Created task:', createdTask);
  } catch (error) {
    // Error is already handled by interceptors
    // UNAUTHORIZED errors will trigger PIN entry modal automatically
    console.error('Request failed:', error);
  }
}

// ============================================================================
// Example 2: Custom Client with Custom Interceptors
// ============================================================================

async function customClientExample() {
  const client = createApiClient({
    baseURL: `${window.location.origin}/rpc`,
    credentials: 'include', // Send cookies with every request

    // Custom error interceptor for logging
    errorInterceptors: [
      onError((error: ApiError) => {
        // UNAUTHORIZED is already handled by default interceptor
        // Add custom error handling here
        if (error.code === 'NOT_FOUND') {
          console.warn('Resource not found:', error.message);
        } else if (error.code === 'VALIDATION_ERROR') {
          console.warn('Validation failed:', error.message);
        }
      }),
    ],

    // Request interceptor to add custom headers
    requestInterceptors: [
      onRequest((request) => {
        const headers = new Headers(request.headers);
        headers.set('X-Client-Version', '1.0.0');
        return new Request(request, { headers });
      }),
    ],

    // Response interceptor for logging
    responseInterceptors: [
      onResponse((response) => {
        console.log(`Response: ${response.status} ${response.url}`);
        return response;
      }),
    ],
  });

  // Use the custom client
  const response = await client.get('/status');
  const data = await response.json();
  console.log('Status:', data);
}

// ============================================================================
// Example 3: Handling Different HTTP Methods
// ============================================================================

async function httpMethodsExample() {
  // GET request
  const getResponse = await apiClient.get('/users/123');
  const user = await getResponse.json();

  // POST request
  const postResponse = await apiClient.post('/users', {
    name: 'John Doe',
    email: 'john@example.com',
  });

  // PUT request (full update)
  const putResponse = await apiClient.put('/users/123', {
    name: 'Jane Doe',
    email: 'jane@example.com',
  });

  // PATCH request (partial update)
  const patchResponse = await apiClient.patch('/users/123', {
    email: 'newemail@example.com',
  });

  // DELETE request
  const deleteResponse = await apiClient.delete('/users/123');
}

// ============================================================================
// Example 4: Error Handling Patterns
// ============================================================================

async function errorHandlingExample() {
  try {
    const response = await apiClient.get('/protected-resource');
    const data = await response.json();
    console.log('Protected data:', data);
  } catch (error) {
    const apiError = error as ApiError;

    // UNAUTHORIZED (401) errors trigger PIN entry modal automatically
    // You can also handle specific error codes:
    switch (apiError.code) {
      case 'UNAUTHORIZED':
        // PIN entry modal is already shown by default interceptor
        console.log('Authentication required - PIN modal will appear');
        break;

      case 'FORBIDDEN':
        console.error('Access denied');
        break;

      case 'NOT_FOUND':
        console.error('Resource not found');
        break;

      case 'VALIDATION_ERROR':
        console.error('Invalid input:', apiError.message);
        break;

      case 'NETWORK_ERROR':
        console.error('Network connection failed');
        break;

      default:
        console.error('Unexpected error:', apiError.message);
    }
  }
}

// ============================================================================
// Example 5: Using with React Hooks
// ============================================================================

import { useState, useEffect } from 'react';

function useApiData<T>(endpoint: string) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchData() {
      try {
        setLoading(true);
        setError(null);

        const response = await apiClient.get(endpoint);
        if (cancelled) return;

        const result = await response.json();
        setData(result);
      } catch (err) {
        if (cancelled) return;
        setError(err as ApiError);
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchData();

    return () => {
      cancelled = true;
    };
  }, [endpoint]);

  return { data, loading, error };
}

// Usage in a component:
function UserProfile({ userId }: { userId: string }) {
  const { data: user, loading, error } = useApiData(`/users/${userId}`);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;
  if (!user) return <div>User not found</div>;

  return <div>Welcome, {user.name}!</div>;
}

// ============================================================================
// Example 6: Advanced - Retry Logic
// ============================================================================

async function retryExample() {
  const client = createApiClient();

  // Add retry logic for network errors
  client.addErrorInterceptor(
    onError(async (error: ApiError) => {
      if (error.code === 'NETWORK_ERROR') {
        console.log('Network error detected, you could implement retry logic here');
        // Note: Actual retry would require more sophisticated implementation
      }
    })
  );

  const response = await client.get('/data');
  return response.json();
}

// ============================================================================
// Example 7: Request/Response Transformation
// ============================================================================

async function transformationExample() {
  const client = createApiClient();

  // Transform request - add auth token from local storage
  client.addRequestInterceptor(
    onRequest((request) => {
      const token = localStorage.getItem('api-token');
      if (token) {
        const headers = new Headers(request.headers);
        headers.set('Authorization', `Bearer ${token}`);
        return new Request(request, { headers });
      }
      return request;
    })
  );

  // Transform response - parse dates
  client.addResponseInterceptor(
    onResponse(async (response) => {
      // Clone response to allow reading body multiple times
      const clone = response.clone();

      try {
        const data = await clone.json();

        // Transform date strings to Date objects
        if (data.createdAt) {
          data.createdAt = new Date(data.createdAt);
        }
        if (data.updatedAt) {
          data.updatedAt = new Date(data.updatedAt);
        }

        // Create new response with transformed data
        return new Response(JSON.stringify(data), {
          status: response.status,
          statusText: response.statusText,
          headers: response.headers,
        });
      } catch {
        // If not JSON, return original response
        return response;
      }
    })
  );

  const response = await client.get('/tasks/123');
  const task = await response.json();
  console.log('Task created at:', task.createdAt instanceof Date);
}

// ============================================================================
// Example 8: oRPC-style Usage (if you're using oRPC)
// ============================================================================

/**
 * Example showing how the client handles oRPC error format
 *
 * oRPC typically wraps errors like:
 * {
 *   error: {
 *     code: "UNAUTHORIZED",
 *     message: "Authentication required"
 *   }
 * }
 *
 * The API client automatically detects both formats:
 * - Standard: { code: "UNAUTHORIZED", message: "..." }
 * - oRPC: { error: { code: "UNAUTHORIZED", message: "..." } }
 */
async function orpcExample() {
  try {
    // This works with both error formats
    const response = await apiClient.post('/rpc', {
      method: 'users.create',
      params: { name: 'John' },
    });

    const result = await response.json();
    console.log('Result:', result);
  } catch (error) {
    const apiError = error as ApiError;
    // Error code will be extracted from either format
    console.log('Error code:', apiError.code);
    console.log('Error message:', apiError.message);
  }
}

// ============================================================================
// Integration with LAN Auth Store
// ============================================================================

/**
 * The API client automatically integrates with the LAN auth store.
 * When a 401 UNAUTHORIZED error is detected:
 *
 * 1. The default error interceptor calls useLanAuthStore.getState().requireAuth()
 * 2. This sets needsAuth=true in the Zustand store
 * 3. Your PIN entry modal (which watches needsAuth) appears
 * 4. User enters PIN
 * 5. PIN is sent to /auth endpoint
 * 6. Server responds with Set-Cookie header
 * 7. Cookie is stored by browser
 * 8. Subsequent requests include the cookie (credentials: "include")
 * 9. Requests are now authenticated
 *
 * You don't need to do anything special - it just works!
 */
