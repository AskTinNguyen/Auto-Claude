# PIN Authentication Middleware - Usage Examples

This document shows how to integrate the PIN authentication middleware with different HTTP server frameworks.

## Table of Contents

- [Basic Concepts](#basic-concepts)
- [Node.js HTTP Server](#nodejs-http-server)
- [Express Integration](#express-integration)
- [Fastify Integration](#fastify-integration)
- [Electron HTTP Server](#electron-http-server)
- [Testing](#testing)

---

## Basic Concepts

The middleware follows the Web Fetch API standard:

```typescript
type Middleware = (request: Request) => Response | void | Promise<Response | void>
```

**Behavior:**
- Returns `void` → Request is authenticated, proceed to handler
- Returns `Response` → Authentication failed or redirect, return this response

**Authentication Flow:**
1. Localhost requests (127.0.0.1, ::1, localhost) always bypass
2. Check for valid auth cookie (`nightshift_lan_auth`)
3. If no cookie, check for `?pin=XXXX` query parameter
4. If PIN is valid, redirect to clean URL with cookie set
5. If no PIN or invalid PIN, return 401 with PIN entry page

---

## Node.js HTTP Server

Basic integration with Node.js built-in HTTP server:

```typescript
import http from 'http';
import { getLanAccessModule, pinAuthMiddleware } from './lan';

// Setup LAN module
const lanModule = getLanAccessModule();
const pin = lanModule.generatePin();
console.log(`🔐 PIN: ${pin}`);

const PORT = 3000;
lanModule.setPort(PORT);

// Create middleware
const authMiddleware = pinAuthMiddleware(true);

// Create server
const server = http.createServer(async (req, res) => {
  // Convert Node.js request to Web Request
  const url = `http://${req.headers.host}${req.url}`;
  const request = new Request(url, {
    method: req.method,
    headers: Object.fromEntries(
      Object.entries(req.headers).map(([k, v]) => [k, Array.isArray(v) ? v[0] : v || ''])
    ),
  });

  // Run middleware
  const authResponse = await authMiddleware(request);

  if (authResponse) {
    // Authentication required or failed
    res.writeHead(authResponse.status, Object.fromEntries(authResponse.headers));
    const body = await authResponse.text();
    res.end(body);
    return;
  }

  // Authenticated - handle request
  res.writeHead(200, { 'Content-Type': 'text/html' });
  res.end('<h1>Welcome! You are authenticated.</h1>');
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`\n📡 Server running on:`);
  console.log(`  Local: http://localhost:${PORT}`);
  console.log(`  LAN: ${lanModule.getLanUrl()}`);
});
```

---

## Express Integration

Integration with Express framework:

```typescript
import express from 'express';
import { getLanAccessModule, pinAuthMiddleware } from './lan';

const app = express();

// Setup LAN module
const lanModule = getLanAccessModule();
const pin = lanModule.generatePin();
console.log(`🔐 PIN: ${pin}`);

const PORT = 3000;
lanModule.setPort(PORT);

// Create middleware wrapper for Express
const authMiddleware = pinAuthMiddleware(true);

app.use(async (req, res, next) => {
  // Convert Express request to Web Request
  const url = `${req.protocol}://${req.get('host')}${req.originalUrl}`;
  const request = new Request(url, {
    method: req.method,
    headers: Object.fromEntries(
      Object.entries(req.headers).map(([k, v]) => [k, Array.isArray(v) ? v[0] : v || ''])
    ),
  });

  // Run middleware
  const authResponse = await authMiddleware(request);

  if (authResponse) {
    // Authentication required or failed
    res.status(authResponse.status);
    authResponse.headers.forEach((value, key) => {
      res.setHeader(key, value);
    });
    const body = await authResponse.text();
    res.send(body);
    return;
  }

  // Authenticated - continue
  next();
});

// Your routes
app.get('/', (req, res) => {
  res.send('<h1>Welcome! You are authenticated.</h1>');
});

app.get('/api/data', (req, res) => {
  res.json({ message: 'Secure data', timestamp: Date.now() });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`\n📡 Server running on:`);
  console.log(`  Local: http://localhost:${PORT}`);
  console.log(`  LAN: ${lanModule.getLanUrl()}`);
  console.log(`  LAN (with PIN): ${lanModule.getLanUrlWithPin()}`);
});
```

---

## Fastify Integration

Integration with Fastify framework:

```typescript
import Fastify from 'fastify';
import { getLanAccessModule, pinAuthMiddleware } from './lan';

const fastify = Fastify({ logger: true });

// Setup LAN module
const lanModule = getLanAccessModule();
const pin = lanModule.generatePin();
console.log(`🔐 PIN: ${pin}`);

const PORT = 3000;
lanModule.setPort(PORT);

// Create middleware
const authMiddleware = pinAuthMiddleware(true);

// Add middleware hook
fastify.addHook('onRequest', async (request, reply) => {
  // Convert Fastify request to Web Request
  const url = `${request.protocol}://${request.hostname}${request.url}`;
  const webRequest = new Request(url, {
    method: request.method,
    headers: Object.fromEntries(
      Object.entries(request.headers).map(([k, v]) => [k, Array.isArray(v) ? v[0] : v || ''])
    ),
  });

  // Run middleware
  const authResponse = await authMiddleware(webRequest);

  if (authResponse) {
    // Authentication required or failed
    reply.code(authResponse.status);
    authResponse.headers.forEach((value, key) => {
      reply.header(key, value);
    });
    const body = await authResponse.text();
    reply.send(body);
    return;
  }

  // Authenticated - continue
});

// Your routes
fastify.get('/', async (request, reply) => {
  return { message: 'Welcome! You are authenticated.' };
});

fastify.get('/api/data', async (request, reply) => {
  return { message: 'Secure data', timestamp: Date.now() };
});

// Start server
fastify.listen({ port: PORT, host: '0.0.0.0' }, (err) => {
  if (err) {
    fastify.log.error(err);
    process.exit(1);
  }
  console.log(`\n📡 Server running on:`);
  console.log(`  Local: http://localhost:${PORT}`);
  console.log(`  LAN: ${lanModule.getLanUrl()}`);
});
```

---

## Electron HTTP Server

Integration with Electron's built-in HTTP server for LAN access:

```typescript
import { app } from 'electron';
import http from 'http';
import { getLanAccessModule, pinAuthMiddleware } from './lan';

// Wait for Electron to be ready
app.whenReady().then(() => {
  // Setup LAN module
  const lanModule = getLanAccessModule();

  // Use configured PIN or generate random one
  const configuredPin = process.env.LAN_ACCESS_PIN;
  const pin = lanModule.generatePin(configuredPin);

  if (!configuredPin) {
    console.log(`🔐 Generated PIN: ${pin}`);
    console.log('Set LAN_ACCESS_PIN environment variable to use a fixed PIN');
  }

  const PORT = parseInt(process.env.LAN_PORT || '3000', 10);
  lanModule.setPort(PORT);

  // Create middleware (disable in development for easier testing)
  const enableAuth = process.env.NODE_ENV === 'production';
  const authMiddleware = pinAuthMiddleware(enableAuth);

  // Create HTTP server
  const server = http.createServer(async (req, res) => {
    // Convert to Web Request
    const url = `http://${req.headers.host}${req.url}`;
    const request = new Request(url, {
      method: req.method,
      headers: Object.fromEntries(
        Object.entries(req.headers).map(([k, v]) => [k, Array.isArray(v) ? v[0] : v || ''])
      ),
    });

    // Run authentication middleware
    const authResponse = await authMiddleware(request);

    if (authResponse) {
      res.writeHead(authResponse.status, Object.fromEntries(authResponse.headers));
      const body = await authResponse.text();
      res.end(body);
      return;
    }

    // Authenticated - route to handlers
    if (req.url === '/') {
      res.writeHead(200, { 'Content-Type': 'text/html' });
      res.end(`
        <!DOCTYPE html>
        <html>
          <head>
            <title>Auto Claude - LAN Access</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
          </head>
          <body>
            <h1>Auto Claude LAN Access</h1>
            <p>Welcome! You have successfully authenticated.</p>
          </body>
        </html>
      `);
    } else if (req.url === '/api/status') {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ status: 'ok', authenticated: true }));
    } else {
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      res.end('Not Found');
    }
  });

  server.listen(PORT, '0.0.0.0', () => {
    const urls = lanModule.getAllUrls();
    console.log(`\n📡 LAN Access enabled:`);
    console.log(`  Local: http://localhost:${PORT}`);
    if (urls.lan) console.log(`  LAN: ${urls.lan}`);
    if (urls.tailscale) console.log(`  Tailscale: ${urls.tailscale}`);
    console.log(`\n📱 Mobile access (with PIN embedded):`);
    if (urls.lanWithPin) console.log(`  ${urls.lanWithPin}`);
    if (urls.tailscaleWithPin) console.log(`  ${urls.tailscaleWithPin}`);
  });

  // Cleanup on app quit
  app.on('before-quit', () => {
    server.close();
  });
});
```

---

## Testing

### Manual Testing

1. **Start your server** with the middleware enabled
2. **From localhost** - Should bypass authentication automatically
3. **From another device** on the network:
   - Navigate to LAN URL (e.g., `http://192.168.1.100:3000`)
   - Should see PIN entry page
   - Enter the 4-digit PIN
   - Should be redirected and receive auth cookie
   - Cookie valid for 30 days

### Automated Testing

```typescript
import { pinAuthMiddleware } from './lan';
import { getLanAccessModule } from './lan-module';

describe('PIN Authentication Middleware', () => {
  let lanModule: ReturnType<typeof getLanAccessModule>;

  beforeEach(() => {
    lanModule = getLanAccessModule();
    lanModule.reset();
    lanModule.generatePin('1234'); // Fixed PIN for testing
  });

  test('localhost bypass', async () => {
    const middleware = pinAuthMiddleware(true);
    const request = new Request('http://localhost:3000/');

    const response = await middleware(request);
    expect(response).toBeUndefined(); // Should proceed to handler
  });

  test('valid cookie authentication', async () => {
    const middleware = pinAuthMiddleware(true);
    const request = new Request('http://192.168.1.100:3000/', {
      headers: { Cookie: 'nightshift_lan_auth=1234' },
    });

    const response = await middleware(request);
    expect(response).toBeUndefined(); // Should proceed to handler
  });

  test('invalid cookie shows PIN page', async () => {
    const middleware = pinAuthMiddleware(true);
    const request = new Request('http://192.168.1.100:3000/', {
      headers: { Cookie: 'nightshift_lan_auth=9999' },
    });

    const response = await middleware(request);
    expect(response).toBeInstanceOf(Response);
    expect(response!.status).toBe(401);
    const body = await response!.text();
    expect(body).toContain('Enter PIN');
  });

  test('valid PIN query redirects with cookie', async () => {
    const middleware = pinAuthMiddleware(true);
    const request = new Request('http://192.168.1.100:3000/?pin=1234');

    const response = await middleware(request);
    expect(response).toBeInstanceOf(Response);
    expect(response!.status).toBe(302);
    expect(response!.headers.get('Location')).toBe('http://192.168.1.100:3000/');
    expect(response!.headers.get('Set-Cookie')).toContain('nightshift_lan_auth=1234');
  });

  test('invalid PIN shows error', async () => {
    const middleware = pinAuthMiddleware(true);
    const request = new Request('http://192.168.1.100:3000/?pin=9999');

    const response = await middleware(request);
    expect(response).toBeInstanceOf(Response);
    expect(response!.status).toBe(401);
    const body = await response!.text();
    expect(body).toContain('Invalid PIN');
  });

  test('disabled middleware is no-op', async () => {
    const middleware = pinAuthMiddleware(false);
    const request = new Request('http://192.168.1.100:3000/');

    const response = await middleware(request);
    expect(response).toBeUndefined(); // Should always proceed
  });
});
```

---

## Environment Variables

Recommended environment variables for configuration:

```bash
# .env
LAN_ACCESS_ENABLED=true          # Enable/disable LAN access
LAN_ACCESS_PIN=1234               # Optional: Fixed PIN (auto-generated if not set)
LAN_PORT=3000                     # Server port
NODE_ENV=production               # Enable auth in production, optional in dev
```

---

## Security Considerations

1. **PIN Strength**: 4-digit PINs provide 10,000 combinations
2. **Rate Limiting**: Implement rate limiting to prevent brute force (not included in middleware)
3. **HTTPS**: Use HTTPS in production (consider self-signed certs for local network)
4. **Cookie Security**: Cookies are HttpOnly and SameSite=Lax
5. **Localhost Bypass**: Development convenience - remove in hardened deployments
6. **PIN Rotation**: Consider rotating PINs periodically
7. **Session Timeout**: 30-day cookie expiry (adjust as needed)

### Recommended Rate Limiting

```typescript
import rateLimit from 'express-rate-limit';

const pinLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 10, // 10 attempts per window
  skipSuccessfulRequests: true,
  handler: (req, res) => {
    res.status(429).send('Too many PIN attempts. Please try again later.');
  },
});

// Apply to PIN validation endpoint
app.use('/auth', pinLimiter);
```

---

## Troubleshooting

**Problem: PIN page not showing**
- Check that middleware is enabled: `pinAuthMiddleware(true)`
- Verify you're not accessing from localhost
- Check that LAN module has a PIN set: `lanModule.getCurrentPin()`

**Problem: Cookie not persisting**
- Verify response includes `Set-Cookie` header
- Check browser cookie settings (HttpOnly, SameSite)
- Ensure clock sync between client and server

**Problem: Localhost not bypassing**
- Check hostname resolution (localhost vs 127.0.0.1)
- Verify `isLocalhost()` function logic
- Check reverse proxy forwarding (X-Forwarded-For)

**Problem: Mobile paste not working**
- Ensure clipboard contains exactly 4 digits
- Check mobile browser clipboard permissions
- Try manual entry as fallback
