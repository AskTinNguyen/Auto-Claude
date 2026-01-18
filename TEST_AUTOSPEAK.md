# 🧪 Testing Auto-Speak Toggle with Electron MCP

## Prerequisites

1. ✅ Electron MCP is now enabled in `apps/backend/.env`:
   - `ELECTRON_MCP_ENABLED=true`
   - `ELECTRON_DEBUG_PORT=9222`

2. ✅ Auto-Speak toggle code is implemented

## Testing Methods

### Method 1: Manual UI Testing (Recommended First)

This is the quickest way to verify the toggle works:

1. **Start the Electron app:**
   ```bash
   cd /Users/tinnguyen/Auto-Claude
   npm run dev
   ```
   
   The app already runs with `--remote-debugging-port=9222` in dev mode.

2. **Open Settings:**
   - Click the ⚙️ Settings icon in the app
   - Or press `Cmd+,` (macOS)

3. **Navigate to TTS:**
   - In the left sidebar, click **TTS** (🔊 Volume2 icon)

4. **Test the Auto-Speak toggle:**
   - Scroll down to see **"Auto-Speak (Ralph)"**
   - Click the toggle switch
   - ✅ If it toggles ON/OFF → **SUCCESS!**
   - ✅ If mode dropdown appears when ON → **SUCCESS!**

5. **Verify settings persist:**
   ```bash
   cat .ralph/voice-config.json
   ```
   
   Should show:
   ```json
   {
     "autoSpeak": {
       "enabled": true,
       "mode": "short"
     }
   }
   ```

---

### Method 2: Automated E2E Testing with QA Agent

Use Auto-Claude's QA agent to automatically test the toggle:

1. **Create a test spec:**
   ```bash
   cd /Users/tinnguyen/Auto-Claude/apps/backend
   
   # Create a simple test task
   mkdir -p .auto-claude/specs/test-autospeak
   cat > .auto-claude/specs/test-autospeak/spec.md << 'SPEC'
# Test Auto-Speak Toggle

## Description
E2E test to verify the Auto-Speak toggle in Settings → TTS works correctly.

## Acceptance Criteria
1. ✅ Can open Settings page
2. ✅ Can navigate to TTS section  
3. ✅ Auto-Speak toggle is visible
4. ✅ Auto-Speak toggle is clickable
5. ✅ Clicking toggle changes state (ON/OFF)
6. ✅ Mode dropdown appears when toggle is ON
7. ✅ Settings persist to .ralph/voice-config.json

## Test Steps
1. Take screenshot of initial state
2. Click Settings (if not already open)
3. Click TTS in navigation
4. Locate "Auto-Speak (Ralph)" toggle
5. Click the toggle to turn it ON
6. Verify mode dropdown appears
7. Select "Short" mode
8. Verify settings saved to .ralph/voice-config.json
9. Click toggle to turn it OFF
10. Verify mode dropdown disappears
11. Take final screenshot
SPEC
   ```

2. **Run QA agent with Electron MCP:**
   ```bash
   # Make sure Electron app is running first!
   # In another terminal: npm run dev
   
   # Then run QA
   python -c "
   from agents.qa_reviewer import run_qa_reviewer
   
   spec_dir = '.auto-claude/specs/test-autospeak'
   project_dir = '/Users/tinnguyen/Auto-Claude'
   
   result = run_qa_reviewer(
       spec_dir=spec_dir,
       project_dir=project_dir,
       model='claude-sonnet-4-5-20250929'
   )
   
   print(f'QA Result: {result}')
   "
   ```

3. **Review QA results:**
   - The QA agent will use Electron MCP tools to interact with the app
   - Screenshots will be captured automatically
   - Results saved to `.auto-claude/specs/test-autospeak/qa_report.md`

---

### Method 3: Direct Electron MCP Commands

For advanced debugging, you can send commands directly:

```bash
cd /Users/tinnguyen/Auto-Claude/apps/backend

# Start Python REPL
python3

# In Python:
>>> from integrations.electron_mcp import ElectronMCP
>>> mcp = ElectronMCP(debug_port=9222)

# Take screenshot
>>> screenshot = mcp.take_screenshot()
>>> print(f"Screenshot: {screenshot}")

# Get page structure
>>> structure = mcp.send_command("get_page_structure")
>>> print(structure['title'])

# Click Settings
>>> mcp.send_command("click_by_text", {"text": "Settings"})

# Navigate to TTS
>>> import time
>>> time.sleep(1)
>>> mcp.send_command("click_by_text", {"text": "TTS"})

# Click Auto-Speak toggle
>>> time.sleep(1)
>>> mcp.send_command("click_by_selector", {"selector": "#auto-speak-enabled"})

# Take final screenshot
>>> screenshot = mcp.take_screenshot()
>>> print(f"Final screenshot: {screenshot}")

# Verify config file
>>> import json
>>> with open('.ralph/voice-config.json') as f:
...     config = json.load(f)
>>> print(config['autoSpeak'])
```

---

## Troubleshooting

### Toggle not clickable?
1. Restart the Electron app: `npm run dev`
2. Check browser console for errors (View → Toggle Developer Tools)
3. Verify TypeScript compiled without errors

### Electron MCP connection fails?
1. Verify app is running with remote debugging:
   ```bash
   lsof -i :9222
   ```
   Should show Electron process

2. Check `ELECTRON_MCP_ENABLED=true` in `apps/backend/.env`

3. Restart both the Electron app and any test scripts

### Settings not saving?
1. Check `.ralph/` directory exists:
   ```bash
   mkdir -p .ralph
   ```

2. Check file permissions:
   ```bash
   ls -la .ralph/voice-config.json
   ```

3. Check Electron logs for errors

---

## Expected Results

✅ **Success Criteria:**
- Toggle is visible in Settings → TTS
- Toggle responds to clicks (changes state)
- Mode dropdown appears/disappears based on toggle state
- Settings persist to `.ralph/voice-config.json`
- No console errors

❌ **Failure Indicators:**
- Toggle is grayed out / disabled
- Clicking toggle does nothing
- Console shows TypeScript errors
- Config file not created/updated

---

## Next Steps After Testing

Once the toggle works:

1. **Test with an actual build:**
   ```bash
   cd apps/backend
   python spec_runner.py --task "Add hello world function" --complexity simple
   python run.py --spec <spec-number>
   ```
   
   You should hear voice announcements during the build!

2. **Test mode switching:**
   - Toggle between "Short" and "Full" mode
   - Verify backend reads the new mode

3. **Test persistence:**
   - Toggle ON, close app, reopen
   - Verify toggle state persists

