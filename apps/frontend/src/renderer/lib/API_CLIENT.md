# API Client

HTTP client for making authenticated requests to the `/rpc` endpoint with automatic LAN auth handling.

## Features

- ✅ **Credentials Included**: All requests automatically include `credentials: "include"` to send cookies
- ✅ **UNAUTHORIZED Detection**: Automatically detects 401/UNAUTHORIZED responses
- ✅ **PIN Entry Trigger**: Triggers PIN entry modal via Zustand store when authentication is required
- ✅ **oRPC Support**: Handles both standard and oRPC error formats
- ✅ **Interceptors**: Support for error, request, and response interceptors
- ✅ **TypeScript**: Full TypeScript support with type definitions

## Quick Start

```typescript
import { apiClient } from '@/lib/api-client';

// Make a GET request
const response = await apiClient.get('/health');
const data = await response.json();

// Make a POST request
const createResponse = await apiClient.post('/tasks', {
  title: 'New Task',
  description: 'Task description',
});
```

## Installation

The API client is already installed. Import it from:

```typescript
import { apiClient, createApiClient, onError } from '@/lib/api-client';
```

## Usage

### Default Client (Singleton)

Use the default `apiClient` for most cases:

```typescript
import { apiClient } from '@/lib/api-client';

// GET request
const response = await apiClient.get('/users/123');
const user = await response.json();

// POST request
await apiClient.post('/users', { name: 'John', email: 'john@example.com' });

// PUT request
await apiClient.put('/users/123', { name: 'Jane' });

// PATCH request
await apiClient.patch('/users/123', { email: 'new@example.com' });

// DELETE request
await apiClient.delete('/users/123');
```

### Custom Client

Create a custom client with specific configuration:

```typescript
import { createApiClient, onError } from '@/lib/api-client';

const client = createApiClient({
  baseURL: `${window.location.origin}/rpc`,
  credentials: 'include',
  errorInterceptors: [
    onError((error) => {
      console.error('API Error:', error);
    }),
  ],
});
```

## Authentication Flow

The API client automatically handles LAN authentication:

1. **Request Made**: Client makes request to `/rpc` with `credentials: "include"`
2. **UNAUTHORIZED Response**: Server returns 401 with `code: "UNAUTHORIZED"`
3. **PIN Modal Triggered**: Error interceptor calls `useLanAuthStore.getState().requireAuth()`
4. **User Enters PIN**: PIN entry modal appears (managed by Zustand store)
5. **Authentication**: PIN is sent to `/auth` endpoint
6. **Cookie Set**: Server responds with `Set-Cookie` header
7. **Authenticated**: Subsequent requests include the auth cookie

You don't need to handle authentication manually - it's automatic!

## Error Handling

The client automatically handles errors and provides detailed error information:

```typescript
import type { ApiError } from '@/lib/api-client';

try {
  await apiClient.get('/protected-resource');
} catch (error) {
  const apiError = error as ApiError;

  switch (apiError.code) {
    case 'UNAUTHORIZED':
      // PIN modal is already shown automatically
      console.log('Authentication required');
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
  }
}
```

## Supported Error Formats

The client handles both standard and oRPC error formats:

### Standard Format
```json
{
  "code": "UNAUTHORIZED",
  "message": "Authentication required",
  "status": 401
}
```

### oRPC Format
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required"
  }
}
```

Both formats trigger the same error handling behavior.

## Interceptors

### Error Interceptors

Add custom error handling:

```typescript
import { apiClient, onError } from '@/lib/api-client';

apiClient.addErrorInterceptor(
  onError((error) => {
    if (error.code === 'VALIDATION_ERROR') {
      console.warn('Validation failed:', error.message);
    }
  })
);
```

### Request Interceptors

Modify requests before they're sent:

```typescript
import { apiClient, onRequest } from '@/lib/api-client';

apiClient.addRequestInterceptor(
  onRequest((request) => {
    const headers = new Headers(request.headers);
    headers.set('X-Custom-Header', 'value');
    return new Request(request, { headers });
  })
);
```

### Response Interceptors

Process responses before they're returned:

```typescript
import { apiClient, onResponse } from '@/lib/api-client';

apiClient.addResponseInterceptor(
  onResponse((response) => {
    console.log(`Response: ${response.status}`);
    return response;
  })
);
```

## React Integration

### With Hooks

```typescript
import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';
import type { ApiError } from '@/lib/api-client';

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
        if (!cancelled) setLoading(false);
      }
    }

    fetchData();

    return () => {
      cancelled = true;
    };
  }, [endpoint]);

  return { data, loading, error };
}
```

### In Components

```typescript
function UserProfile({ userId }: { userId: string }) {
  const { data: user, loading, error } = useApiData(`/users/${userId}`);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;
  if (!user) return <div>User not found</div>;

  return <div>Welcome, {user.name}!</div>;
}
```

## Configuration

### Default Configuration

```typescript
{
  baseURL: `${window.location.origin}/rpc`,
  credentials: 'include',
  fetch: globalThis.fetch,
  errorInterceptors: [defaultUnauthorizedHandler],
  requestInterceptors: [],
  responseInterceptors: []
}
```

### Custom Configuration

```typescript
import { createApiClient } from '@/lib/api-client';

const client = createApiClient({
  baseURL: 'https://api.example.com',
  credentials: 'same-origin',
  fetch: customFetch,
  errorInterceptors: [customErrorHandler],
  requestInterceptors: [addAuthHeader],
  responseInterceptors: [logResponse],
});
```

## API Reference

### `ApiClient`

Main client class for making HTTP requests.

#### Methods

- `get(path: string, init?: RequestInit): Promise<Response>` - Make GET request
- `post(path: string, body?: unknown, init?: RequestInit): Promise<Response>` - Make POST request
- `put(path: string, body?: unknown, init?: RequestInit): Promise<Response>` - Make PUT request
- `patch(path: string, body?: unknown, init?: RequestInit): Promise<Response>` - Make PATCH request
- `delete(path: string, init?: RequestInit): Promise<Response>` - Make DELETE request
- `request(path: string, init?: RequestInit): Promise<Response>` - Make custom request
- `addErrorInterceptor(interceptor: ErrorInterceptor): void` - Add error interceptor
- `addRequestInterceptor(interceptor: RequestInterceptor): void` - Add request interceptor
- `addResponseInterceptor(interceptor: ResponseInterceptor): void` - Add response interceptor

### `createApiClient(config?: ApiClientConfig): ApiClient`

Create a new API client instance.

### `apiClient`

Default singleton API client instance.

### Types

```typescript
interface ApiError {
  code?: string;
  message?: string;
  status?: number;
  [key: string]: unknown;
}

type ErrorInterceptor = (error: ApiError) => void | Promise<void>;
type RequestInterceptor = (request: Request, init?: RequestInit) => Request | Promise<Request>;
type ResponseInterceptor = (response: Response) => Response | Promise<Response>;

interface ApiClientConfig {
  baseURL?: string;
  fetch?: typeof globalThis.fetch;
  errorInterceptors?: ErrorInterceptor[];
  requestInterceptors?: RequestInterceptor[];
  responseInterceptors?: ResponseInterceptor[];
  credentials?: RequestCredentials;
}
```

## Examples

See [api-client.example.ts](./api-client.example.ts) for comprehensive usage examples.

## Testing

```typescript
import { createApiClient } from '@/lib/api-client';

describe('API Client', () => {
  it('should include credentials in requests', async () => {
    const mockFetch = vi.fn().mockResolvedValue(new Response('{}'));

    const client = createApiClient({
      fetch: mockFetch,
    });

    await client.get('/test');

    expect(mockFetch).toHaveBeenCalledWith(
      expect.any(Request),
      expect.objectContaining({ credentials: 'include' })
    );
  });

  it('should trigger PIN entry on UNAUTHORIZED', async () => {
    const mockFetch = vi.fn().mockResolvedValue(
      new Response('{"code":"UNAUTHORIZED"}', { status: 401 })
    );

    const client = createApiClient({
      fetch: mockFetch,
    });

    try {
      await client.get('/protected');
    } catch (error) {
      const apiError = error as ApiError;
      expect(apiError.code).toBe('UNAUTHORIZED');
    }

    // Verify PIN modal was triggered
    const store = useLanAuthStore.getState();
    expect(store.needsAuth).toBe(true);
  });
});
```

## Troubleshooting

### Credentials Not Included

**Problem**: Cookies aren't being sent with requests.

**Solution**: Ensure `credentials: "include"` is set in the client configuration (it's enabled by default).

### PIN Modal Not Appearing

**Problem**: UNAUTHORIZED errors don't trigger PIN entry.

**Solution**:
1. Check that error response has `code: "UNAUTHORIZED"` or `status: 401`
2. Verify `useLanAuthStore` is imported correctly
3. Ensure PIN entry modal component is watching `needsAuth` state

### CORS Errors

**Problem**: Requests fail with CORS errors.

**Solution**:
1. Ensure server sends proper CORS headers
2. Check that `credentials: "include"` is allowed by server
3. Verify `Access-Control-Allow-Credentials: true` header is present

## Related Files

- `/Users/tinnguyen/Auto-Claude/apps/frontend/src/renderer/lib/api-client.ts` - Main implementation
- `/Users/tinnguyen/Auto-Claude/apps/frontend/src/renderer/lib/api-client.example.ts` - Usage examples
- `/Users/tinnguyen/Auto-Claude/apps/frontend/src/renderer/stores/lan-auth-store.ts` - LAN auth Zustand store
- `/Users/tinnguyen/Auto-Claude/apps/frontend/src/main/lan/middleware.ts` - Server-side PIN auth middleware
