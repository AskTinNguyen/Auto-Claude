# LAN Access Module

PIN-based authentication module for LAN access with IP detection and URL generation.

## Features

- 4-digit PIN generation (random or configured)
- Local network IP detection (192.168.x.x, 10.x.x.x, 172.16-31.x.x)
- Tailscale IP detection (100.64.0.0/10 range)
- URL generation with and without PIN embedded
- Cookie-based authentication support
- Localhost bypass for development

## Installation

The module is part of the Auto Claude frontend codebase. Import from:

```typescript
import { getLanAccessModule } from './lan';
```

## Usage

### Basic Setup

```typescript
import { getLanAccessModule } from './lan';

// Get singleton instance
const lanModule = getLanAccessModule();

// Generate a random PIN
const pin = lanModule.generatePin();
console.log(`PIN: ${pin}`); // e.g., "1234"

// Or use a configured PIN
const staticPin = lanModule.generatePin('5678');

// Set server port
lanModule.setPort(3000);
```

### IP Detection

```typescript
// Get local network IP
const localIp = lanModule.getLocalIpAddress();
console.log(`Local IP: ${localIp}`); // e.g., "192.168.1.100"

// Get Tailscale IP (if available)
const tailscaleIp = lanModule.getTailscaleIpAddress();
console.log(`Tailscale IP: ${tailscaleIp}`); // e.g., "100.64.0.5" or null

// Get all addresses at once
const addresses = lanModule.getNetworkAddresses();
console.log(addresses);
// { localIp: "192.168.1.100", tailscaleIp: "100.64.0.5" }
```

### URL Generation

```typescript
// Generate URLs without PIN (for display)
const lanUrl = lanModule.getLanUrl();
console.log(lanUrl); // "http://192.168.1.100:3000"

const tailscaleUrl = lanModule.getTailscaleUrl();
console.log(tailscaleUrl); // "http://100.64.0.5:3000"

// Generate URLs with PIN embedded (for QR codes)
const lanUrlWithPin = lanModule.getLanUrlWithPin();
console.log(lanUrlWithPin); // "http://192.168.1.100:3000?pin=1234"

const tailscaleUrlWithPin = lanModule.getTailscaleUrlWithPin();
console.log(tailscaleUrlWithPin); // "http://100.64.0.5:3000?pin=1234"

// Get all URLs at once
const urls = lanModule.getAllUrls();
console.log(urls);
/*
{
  lan: "http://192.168.1.100:3000",
  lanWithPin: "http://192.168.1.100:3000?pin=1234",
  tailscale: "http://100.64.0.5:3000",
  tailscaleWithPin: "http://100.64.0.5:3000?pin=1234"
}
*/
```

### PIN Validation

```typescript
// Validate a PIN
const isValid = lanModule.validatePin('1234');
if (isValid) {
  console.log('PIN is correct');
} else {
  console.log('PIN is incorrect');
}

// Get current PIN
const currentPin = lanModule.getCurrentPin();
console.log(`Current PIN: ${currentPin}`); // "1234" or null
```

### Reset State

```typescript
// Clear PIN and reset state
lanModule.reset();

console.log(lanModule.getCurrentPin()); // null
```

## API Reference

### `generatePin(configuredPin?: string | null): string`

Generate a 4-digit PIN or use a configured PIN.

- **Parameters:**
  - `configuredPin` (optional): Static PIN to use instead of generating random one
- **Returns:** The generated or configured PIN
- **Throws:** Error if configured PIN is not exactly 4 digits

### `setPort(port: number): void`

Set the server port for URL generation.

- **Parameters:**
  - `port`: Port number (1-65535)
- **Throws:** Error if port is out of valid range

### `getCurrentPin(): string | null`

Get the current PIN.

- **Returns:** Current PIN or null if not generated

### `validatePin(pin: string): boolean`

Validate a PIN against the current PIN.

- **Parameters:**
  - `pin`: PIN to validate
- **Returns:** True if PIN matches current PIN, false otherwise

### `getLocalIpAddress(): string | null`

Get local network IP address. Prefers standard private network ranges (192.168.x.x, 10.x.x.x, 172.16-31.x.x) over CGNAT/Tailscale ranges.

- **Returns:** Local IP address or null if not found
- **Excludes:** Localhost (127.0.0.1, ::1), link-local (169.254.x.x)

### `getTailscaleIpAddress(): string | null`

Get Tailscale IP address (100.64.0.0/10 range).

- **Returns:** Tailscale IP or null if not found

### `getNetworkAddresses(): NetworkAddresses`

Get all network addresses.

- **Returns:** Object with `localIp` and `tailscaleIp` properties

### `getLanUrl(): string | null`

Get LAN URL without PIN.

- **Returns:** LAN URL or null if no local IP

### `getLanUrlWithPin(): string | null`

Get LAN URL with PIN embedded (for QR codes).

- **Returns:** LAN URL with PIN or null if no local IP or PIN

### `getTailscaleUrl(): string | null`

Get Tailscale URL without PIN.

- **Returns:** Tailscale URL or null if no Tailscale IP

### `getTailscaleUrlWithPin(): string | null`

Get Tailscale URL with PIN embedded.

- **Returns:** Tailscale URL with PIN or null if no Tailscale IP or PIN

### `getAllUrls(): LanUrls`

Get all LAN URLs.

- **Returns:** Object containing all URL variants

### `reset(): void`

Reset the module state (clear PIN).

## Network Ranges

The module detects and categorizes IP addresses into the following ranges:

### Standard Private Networks (Preferred)
- **192.168.0.0/16** - Common home/office networks
- **10.0.0.0/8** - Large private networks
- **172.16.0.0/12** - Private networks (172.16.0.0 - 172.31.255.255)

### Tailscale Network
- **100.64.0.0/10** - Tailscale VPN network (CGNAT range)

### Excluded Ranges
- **127.0.0.1, ::1** - Localhost
- **169.254.0.0/16** - Link-local addresses

## Example: Express Server Integration

```typescript
import express from 'express';
import { getLanAccessModule } from './lan';

const app = express();
const lanModule = getLanAccessModule();

// Generate PIN on startup
const pin = lanModule.generatePin();
console.log(`🔐 LAN Access PIN: ${pin}`);

// Set port
const PORT = 3000;
lanModule.setPort(PORT);

// Print access URLs
const urls = lanModule.getAllUrls();
console.log('\n📡 Access URLs:');
console.log(`  Local: ${urls.lan}`);
if (urls.tailscale) {
  console.log(`  Tailscale: ${urls.tailscale}`);
}
console.log('\n📱 QR Code URLs (with PIN):');
console.log(`  Local: ${urls.lanWithPin}`);
if (urls.tailscaleWithPin) {
  console.log(`  Tailscale: ${urls.tailscaleWithPin}`);
}

// Start server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`\n✅ Server listening on all interfaces at port ${PORT}`);
});
```

## Testing

Run the test suite:

```bash
npm test lan-module.test.ts
```

## TypeScript Types

All types are exported from the module:

```typescript
import type {
  NetworkInterface,
  LanConfig,
  LanUrls,
  NetworkAddresses,
} from './lan';
```

## Security Considerations

1. **PIN Storage**: PINs are stored in memory only and are not persisted
2. **PIN Length**: 4-digit PINs provide 10,000 possible combinations
3. **Rate Limiting**: Implement rate limiting on PIN validation in production
4. **HTTPS**: Consider using HTTPS for production deployments
5. **Localhost Bypass**: Localhost requests should bypass PIN authentication for development

## Next Steps

To complete the LAN access feature, you'll need to implement:

1. **PIN Auth Middleware** - Cookie-based authentication with PIN validation
2. **Server Integration** - Add middleware to Express/Fastify server
3. **Client Components** - PIN entry UI and auth state management
4. **QR Code Generator** - Generate QR codes for mobile access

See the feature architecture documentation for detailed implementation guidance.
