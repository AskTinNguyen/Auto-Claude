# Electron CDP Testing Skill

This skill enables automated testing of Electron apps via Chrome DevTools Protocol (CDP).

## Problem Context

When testing Electron apps, there are two common pitfalls:

1. **agent-browser opens its own Chromium** - When you use `agent-browser open http://localhost:5173`, it opens a separate browser that does NOT have access to `window.electronAPI` because the Electron preload script only runs inside the actual Electron window.

2. **CDP connects to wrong target** - When using `agent-browser --cdp 9222`, it may connect to DevTools instead of the main app window.

## Solution: Direct WebSocket CDP Connection

### Step 1: Start Electron with Remote Debugging

```bash
# From the frontend directory
npm run dev:mcp
# This runs: electron-vite dev -- --remote-debugging-port=9222
```

### Step 2: List Available CDP Targets

```bash
curl -s http://localhost:9222/json
```

This returns JSON with available targets. Look for the one with `"title": "Auto Claude"` (or your app name) and `"type": "page"`:

```json
{
  "id": "BA1A364B10B4180539DD84E06565901B",
  "title": "Auto Claude",
  "type": "page",
  "url": "http://localhost:5173/",
  "webSocketDebuggerUrl": "ws://localhost:9222/devtools/page/BA1A364B10B4180539DD84E06565901B"
}
```

### Step 3: Connect via WebSocket and Execute Tests

Use Node.js with the `ws` package to connect directly to the correct page:

```javascript
const WebSocket = require('ws');
const pageId = 'BA1A364B10B4180539DD84E06565901B'; // Get from Step 2
const ws = new WebSocket(`ws://localhost:9222/devtools/page/${pageId}`);

ws.on('open', () => {
  // Execute JavaScript in the Electron renderer
  ws.send(JSON.stringify({
    id: 1,
    method: 'Runtime.evaluate',
    params: {
      expression: 'typeof window.electronAPI',
      // For async operations, use awaitPromise: true
    }
  }));
});

ws.on('message', (data) => {
  const result = JSON.parse(data);
  console.log(result.result?.result?.value);
  ws.close();
});
```

## Common CDP Operations

### Test if electronAPI exists

```javascript
expression: 'typeof window.electronAPI.listDocumentation'
// Returns: "function" if exists
```

### Call an IPC method (async)

```javascript
ws.send(JSON.stringify({
  id: 1,
  method: 'Runtime.evaluate',
  params: {
    expression: 'window.electronAPI.listDocumentation("project-id").then(r => JSON.stringify(r))',
    awaitPromise: true
  }
}));
```

### Click a button

```javascript
expression: '(function() { const btn = Array.from(document.querySelectorAll("button")).find(b => b.textContent.includes("Documentation")); if (btn) { btn.click(); return "Clicked"; } return "Not found"; })()'
```

### Take a screenshot

```javascript
const fs = require('fs');

ws.send(JSON.stringify({
  id: 1,
  method: 'Page.captureScreenshot',
  params: { format: 'png' }
}));

ws.on('message', (data) => {
  const result = JSON.parse(data);
  if (result.result?.data) {
    fs.writeFileSync('/tmp/screenshot.png', Buffer.from(result.result.data, 'base64'));
  }
});
```

## Complete Test Script Example

```javascript
// electron-cdp-test.js
const WebSocket = require('ws');
const fs = require('fs');

async function testElectronApp() {
  // 1. Get available targets
  const response = await fetch('http://localhost:9222/json');
  const targets = await response.json();
  const mainPage = targets.find(t => t.type === 'page' && t.title !== 'DevTools');

  if (!mainPage) {
    console.error('Main page not found');
    process.exit(1);
  }

  // 2. Connect to the main page
  const ws = new WebSocket(mainPage.webSocketDebuggerUrl);

  return new Promise((resolve, reject) => {
    ws.on('open', async () => {
      // 3. Test electronAPI exists
      ws.send(JSON.stringify({
        id: 1,
        method: 'Runtime.evaluate',
        params: { expression: 'typeof window.electronAPI' }
      }));
    });

    ws.on('message', (data) => {
      const result = JSON.parse(data);

      if (result.id === 1) {
        const apiType = result.result?.result?.value;
        console.log('electronAPI type:', apiType);

        if (apiType === 'object') {
          console.log('SUCCESS: electronAPI is available');
          // Continue with more tests...
        } else {
          console.log('FAIL: electronAPI not available');
        }

        ws.close();
        resolve();
      }
    });

    ws.on('error', reject);
    setTimeout(() => reject(new Error('Timeout')), 10000);
  });
}

testElectronApp().catch(console.error);
```

## Inline One-Liner for Quick Tests

```bash
# Test if electronAPI exists
node -e "
const WebSocket = require('ws');
const ws = new WebSocket('ws://localhost:9222/devtools/page/PAGE_ID_HERE');
ws.on('open', () => {
  ws.send(JSON.stringify({id:1,method:'Runtime.evaluate',params:{expression:'typeof window.electronAPI'}}));
});
ws.on('message', (d) => { console.log(JSON.parse(d).result?.result?.value); ws.close(); process.exit(0); });
setTimeout(() => process.exit(1), 5000);
"
```

## Troubleshooting

### "Cannot start http server for devtools" error
The CDP port is already in use. Kill existing processes:
```bash
lsof -ti:9222 | xargs kill -9
pkill -f "electron"
```

### agent-browser connects to DevTools instead of main window
Don't use `agent-browser --cdp 9222`. Instead, use the direct WebSocket approach described above.

### "window.electronAPI is undefined"
You're likely connecting to a regular browser window instead of the Electron window. Use the WebSocket approach with the correct page ID.

## Key Insight

The critical understanding is that `window.electronAPI` is only available in the **Electron renderer process** where the preload script runs. Regular browsers accessing `localhost:5173` won't have it. Always test via CDP connection to the actual Electron window.
