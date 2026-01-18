#!/bin/bash
# TTS Integration Test Script
# Run this to verify backend is working

cd "$(dirname "$0")/apps/backend"

echo "========================================="
echo "TTS Integration Test"
echo "========================================="
echo ""

echo "1. Testing TTS Status..."
python3 -m integrations.tts.ipc_bridge get-status | python3 -m json.tool | grep -E "(success|voice_counts)" -A 5
echo ""

echo "2. Testing Piper Voice Listing..."
python3 -m integrations.tts.ipc_bridge list-voices --provider piper | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data['success']:
    voices = data['voices']['piper']
    print(f'✅ Found {len(voices)} Piper voices:')
    for v in voices[:5]:
        print(f'   - {v[\"name\"]} ({v[\"language\"]})')
    if len(voices) > 5:
        print(f'   ... and {len(voices) - 5} more')
else:
    print(f'❌ Error: {data.get(\"error\")}')"
echo ""

echo "3. Testing macOS Voice Listing..."
python3 -m integrations.tts.ipc_bridge list-voices --provider macos | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data['success']:
    voices = data['voices']['macos']
    print(f'✅ Found {len(voices)} macOS voices')
else:
    print(f'❌ Error: {data.get(\"error\")}')"
echo ""

echo "========================================="
echo "Backend tests completed!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Open Auto Claude app (should already be running)"
echo "2. Go to Settings → Analytics"
echo "3. Enable TTS and test voice selection"
echo ""
