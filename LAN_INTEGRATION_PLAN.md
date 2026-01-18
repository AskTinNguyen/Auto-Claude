# LAN Access Integration Plan

Complete plan to integrate all LAN access components into Auto-Claude Electron app.

## Current State ✅

### Commits Made
1. **bf6acbbc** - Backend LAN module with PIN authentication
   - PIN generation/validation (4-digit random or configured)
   - Network IP detection (local + Tailscale)
   - URL generation (with/without PIN)
   - Cookie-based auth middleware (HTML + JSON)
   - Server configuration utilities
   - Tests and documentation

2. **157c5b82** - Frontend authentication UI
   - PIN entry modal with auto-advance and paste support
   - API client with UNAUTHORIZED detection
   - Zustand store for auth state
   - QR code dialog component
   - i18n translations (en/fr)
   - Settings schema updates (`allowLan`, `lanPin`)

### Components Implemented

#### Backend (`apps/frontend/src/main/lan/`)
- ✅ `lan-module.ts` - Core PIN/IP/URL logic
- ✅ `pin-auth-middleware.ts` - Cookie-based auth with HTML page
- ✅ `middleware.ts` - JSON-focused auth middleware
- ✅ `server-config.ts` - Server setup utilities
- ✅ `LanQRDialog.tsx` - React QR code component
- ✅ `types.ts` - TypeScript interfaces
- ✅ Tests and documentation

#### Frontend (`apps/frontend/src/renderer/`)
- ✅ `components/auth/PinEntryModal.tsx` - PIN entry UI
- ✅ `lib/api-client.ts` - HTTP client with auth
- ✅ `stores/lan-auth-store.ts` - Auth state management
- ✅ i18n translations in `shared/i18n/locales/{en,fr}/auth.json`
- ✅ Settings types updated (`allowLan`, `lanPin`)

### What's Missing

❌ HTTP server not started in Electron main process
❌ LAN middleware not integrated with server
❌ Frontend components not wired to App.tsx
❌ Settings UI not added to AppSettings.tsx
❌ IPC handlers for LAN settings not created
❌ Server lifecycle not integrated with Electron app

---

## Integration Tasks

### 1. HTTP Server in Electron Main Process

**File:** `apps/frontend/src/main/http-server.ts` (NEW)

Create a new HTTP server manager that:
- Starts/stops with Electron app lifecycle
- Uses Bun or Node.js HTTP based on availability
- Applies LAN auth middleware when `allowLan` is enabled
- Binds to `0.0.0.0` (LAN) or `127.0.0.1` (localhost)
- Provides RPC endpoint for Electron renderer
- Handles health check and auth endpoints

**Key features:**
```typescript
export class HttpServerManager {
  async start(settings: AppSettings): Promise<void>;
  async stop(): Promise<void>;
  getUrl(): string | null;
  getCurrentPin(): string | null;
  getLanUrls(): LanUrls;
}
```

**Protected routes:**
- `/rpc` - JSON-RPC endpoint (requires auth if allowLan=true)
- Any future API endpoints

**Public routes:**
- `/health` - Health check (no auth)
- `/auth` - PIN validation endpoint (POST with pin parameter)

### 2. Integrate Server with Electron App

**File:** `apps/frontend/src/main/index.ts`

Add server startup/shutdown to Electron lifecycle:

```typescript
import { HttpServerManager } from './http-server';

let httpServer: HttpServerManager | null = null;

async function createWindow(): void {
  // ... existing window creation ...

  // Start HTTP server after window is ready
  const settings = loadSettingsSync();
  httpServer = new HttpServerManager();
  await httpServer.start(settings);

  // Log LAN access info if enabled
  if (settings.allowLan) {
    const urls = httpServer.getLanUrls();
    console.log('🔐 LAN Access Enabled');
    console.log(`   PIN: ${httpServer.getCurrentPin()}`);
    console.log(`   URL: ${urls.lan}`);
    console.log(`   QR: ${urls.lanWithPin}`);
  }
}

app.on('before-quit', async () => {
  if (httpServer) {
    await httpServer.stop();
  }
});
```

### 3. IPC Handlers for LAN Settings

**File:** `apps/frontend/src/main/ipc-handlers/lan-handlers.ts` (NEW)

Create IPC handlers to expose LAN functionality to renderer:

```typescript
export function setupLanHandlers() {
  // Get LAN URLs
  ipcMain.handle('lan:get-urls', async () => {
    return httpServer?.getLanUrls() ?? null;
  });

  // Get current PIN
  ipcMain.handle('lan:get-pin', async () => {
    return httpServer?.getCurrentPin() ?? null;
  });

  // Validate PIN (for testing)
  ipcMain.handle('lan:validate-pin', async (_, pin: string) => {
    return httpServer?.validatePin(pin) ?? false;
  });

  // Restart server with new settings
  ipcMain.handle('lan:restart-server', async (_, settings: AppSettings) => {
    await httpServer?.stop();
    await httpServer?.start(settings);
  });
}
```

### 4. Wire Frontend Components to App

**File:** `apps/frontend/src/renderer/App.tsx`

Add PIN entry modal to root app:

```typescript
import { PinEntryModal } from '@/components/auth/PinEntryModal';
import { useNeedsAuth } from '@/stores/lan-auth-store';

export function App() {
  const needsAuth = useNeedsAuth();

  return (
    <>
      {needsAuth && <PinEntryModal />}
      {/* ... existing app content ... */}
    </>
  );
}
```

### 5. Add LAN Settings UI

**File:** `apps/frontend/src/renderer/components/settings/AppSettings.tsx`

Add LAN configuration section:

```tsx
import { LanQRDialog } from '@/main/lan/LanQRDialog';
import { useState } from 'react';

// In AppSettings component
function LanAccessSettings({ settings, onUpdate }) {
  const [showQR, setShowQR] = useState(false);
  const [lanUrls, setLanUrls] = useState(null);
  const [currentPin, setCurrentPin] = useState(null);

  useEffect(() => {
    if (settings.allowLan) {
      // Fetch LAN URLs and PIN from main process
      window.electron.invoke('lan:get-urls').then(setLanUrls);
      window.electron.invoke('lan:get-pin').then(setCurrentPin);
    }
  }, [settings.allowLan]);

  return (
    <div className="settings-section">
      <h3>{t('settings:lan.title')}</h3>

      {/* Enable LAN Access Toggle */}
      <Toggle
        checked={settings.allowLan}
        onChange={(checked) => {
          onUpdate({ allowLan: checked });
          // Restart server with new settings
          window.electron.invoke('lan:restart-server', { ...settings, allowLan: checked });
        }}
        label={t('settings:lan.enableLan')}
      />

      {settings.allowLan && (
        <>
          {/* Static PIN Input */}
          <Input
            type="text"
            value={settings.lanPin || ''}
            onChange={(value) => onUpdate({ lanPin: value || null })}
            placeholder={t('settings:lan.pinPlaceholder')}
            maxLength={4}
            pattern="\\d{4}"
          />

          {/* Current PIN Display */}
          {currentPin && (
            <div className="lan-info">
              <p>{t('settings:lan.currentPin')}: <strong>{currentPin}</strong></p>
            </div>
          )}

          {/* LAN URLs Display */}
          {lanUrls?.lan && (
            <div className="lan-urls">
              <p>{t('settings:lan.localUrl')}: {lanUrls.lan}</p>
              {lanUrls.tailscale && (
                <p>{t('settings:lan.tailscaleUrl')}: {lanUrls.tailscale}</p>
              )}
            </div>
          )}

          {/* Show QR Code Button */}
          <button onClick={() => setShowQR(true)}>
            {t('settings:lan.showQrCode')}
          </button>

          {/* QR Code Dialog */}
          {showQR && lanUrls && (
            <LanQRDialog
              isOpen={showQR}
              onClose={() => setShowQR(false)}
              lanUrl={lanUrls.lanWithPin}
              tailscaleUrl={lanUrls.tailscaleWithPin}
              pin={currentPin}
            />
          )}
        </>
      )}
    </div>
  );
}
```

### 6. Add i18n Translations

**File:** `apps/frontend/src/shared/i18n/locales/en/settings.json`

Add LAN settings translations:

```json
{
  "lan": {
    "title": "LAN Access",
    "enableLan": "Enable LAN Access",
    "enableLanDescription": "Allow access from devices on your local network",
    "pinPlaceholder": "Enter 4-digit PIN (or leave empty for random)",
    "currentPin": "Current PIN",
    "localUrl": "Local Network URL",
    "tailscaleUrl": "Tailscale URL",
    "showQrCode": "Show QR Code",
    "qrCodeTitle": "Connect via QR Code",
    "securityWarning": "Only enable LAN access on trusted networks"
  }
}
```

(Same for `fr/settings.json` with French translations)

### 7. Update IPC Setup

**File:** `apps/frontend/src/main/ipc-setup.ts`

Add LAN handlers to IPC setup:

```typescript
import { setupLanHandlers } from './ipc-handlers/lan-handlers';

export function setupIpcHandlers() {
  // ... existing handlers ...
  setupLanHandlers();
}
```

### 8. Add Preload API Types

**File:** `apps/frontend/src/preload/index.d.ts`

Add LAN API to window.electron:

```typescript
interface ElectronAPI {
  // ... existing methods ...

  // LAN Access
  'lan:get-urls': () => Promise<LanUrls | null>;
  'lan:get-pin': () => Promise<string | null>;
  'lan:validate-pin': (pin: string) => Promise<boolean>;
  'lan:restart-server': (settings: AppSettings) => Promise<void>;
}
```

---

## Testing Plan

### Unit Tests
- ✅ LAN module tests (already in `__tests__/lan-module.test.ts`)
- ✅ PIN entry modal tests (already in `__tests__/PinEntryModal.test.tsx`)
- ✅ QR dialog tests (already in `__tests__/LanQRDialog.test.tsx`)

### Integration Tests
1. **Server Startup**
   - [ ] Server starts with Electron app
   - [ ] Server binds to correct hostname (0.0.0.0 vs 127.0.0.1)
   - [ ] Correct port is used
   - [ ] PIN is generated on startup

2. **Authentication Flow**
   - [ ] `/rpc` returns 401 when no cookie present
   - [ ] `/auth` endpoint validates correct PIN
   - [ ] Cookie is set after successful auth
   - [ ] Subsequent requests with cookie succeed
   - [ ] Invalid PIN returns error
   - [ ] Localhost requests bypass auth

3. **Frontend Integration**
   - [ ] API client triggers PIN modal on 401
   - [ ] PIN entry modal submits to `/auth`
   - [ ] Successful auth closes modal
   - [ ] Failed auth shows error message
   - [ ] Retry attempts are tracked

4. **Settings Integration**
   - [ ] Toggle LAN access restarts server
   - [ ] Static PIN is applied on server restart
   - [ ] QR code dialog shows correct URLs
   - [ ] Settings persist across app restarts

### Manual Testing
1. **Basic LAN Access**
   - [ ] Enable LAN in settings
   - [ ] Server starts and displays PIN
   - [ ] Access from mobile device on same network
   - [ ] PIN entry works
   - [ ] Cookie persists across requests

2. **QR Code Flow**
   - [ ] QR code displays with embedded PIN
   - [ ] Scan QR code on mobile
   - [ ] Auto-redirect to `/auth?pin=XXXX`
   - [ ] Cookie set, access granted

3. **Localhost Bypass**
   - [ ] Access from localhost without PIN
   - [ ] No auth required for localhost

4. **Tailscale**
   - [ ] Tailscale URL shown when available
   - [ ] Access via Tailscale works
   - [ ] PIN auth required for Tailscale

---

## Implementation Order

1. ✅ **DONE** - Create backend LAN module
2. ✅ **DONE** - Create frontend UI components
3. 🔄 **NOW** - Create HTTP server manager
4. 🔄 **NOW** - Integrate server with Electron lifecycle
5. 🔄 **NOW** - Add IPC handlers for LAN settings
6. 🔄 **NOW** - Wire frontend components to App
7. 🔄 **NOW** - Add LAN settings UI
8. 🔄 **NOW** - Add i18n translations
9. ⏳ **NEXT** - Test integration end-to-end
10. ⏳ **NEXT** - Create integration tests
11. ⏳ **NEXT** - Update documentation

---

## Security Considerations

✅ **Already Implemented:**
- PIN-based authentication
- Cookie-based session management
- Localhost bypass for development
- CORS headers for security
- 4-digit PIN (10,000 combinations)

⚠️ **Additional Considerations:**
- Consider rate limiting for PIN attempts
- Add session timeout for cookies
- Consider HTTPS for production (self-signed cert)
- Add option to disable LAN access in production
- Log authentication attempts for security audit

---

## Next Steps

After this integration is complete:
1. Test on all platforms (Windows, macOS, Linux)
2. Test on different network configurations
3. Add analytics for LAN usage
4. Consider adding:
   - Session management UI (view/revoke active sessions)
   - PIN rotation/expiry
   - Multiple PIN support for different users
   - HTTPS support with self-signed certificates

---

## Files to Create/Modify

### New Files
- `apps/frontend/src/main/http-server.ts` - HTTP server manager
- `apps/frontend/src/main/ipc-handlers/lan-handlers.ts` - IPC handlers

### Modified Files
- `apps/frontend/src/main/index.ts` - Add server lifecycle
- `apps/frontend/src/main/ipc-setup.ts` - Add LAN handlers
- `apps/frontend/src/renderer/App.tsx` - Add PIN modal
- `apps/frontend/src/renderer/components/settings/AppSettings.tsx` - Add LAN settings UI
- `apps/frontend/src/shared/i18n/locales/en/settings.json` - Add translations
- `apps/frontend/src/shared/i18n/locales/fr/settings.json` - Add translations
- `apps/frontend/src/preload/index.d.ts` - Add LAN API types

---

## Estimated Completion Time

- HTTP server manager: 1-2 hours
- Electron integration: 1 hour
- IPC handlers: 30 minutes
- Frontend wiring: 1 hour
- Settings UI: 1-2 hours
- Translations: 30 minutes
- Testing: 2-3 hours

**Total:** ~7-10 hours

---

## Success Criteria

✅ Feature is complete when:
1. HTTP server starts with Electron app
2. LAN access can be toggled in settings
3. PIN authentication works from remote device
4. QR code flow works end-to-end
5. Settings persist across restarts
6. All tests pass
7. Documentation is updated
8. Works on all platforms (Windows, macOS, Linux)
