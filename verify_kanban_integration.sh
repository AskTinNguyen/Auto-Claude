#!/bin/bash
# Verify that Kanban can read Ralph CLI progress

SPEC_DIR="/Users/tinnguyen/Auto-Claude/.auto-claude/specs/009-ralph-cli-test"

echo "========================================="
echo "Kanban Integration Verification"
echo "========================================="
echo ""

# Check 1: Files exist
echo "✓ Checking required files..."
files_ok=true

if [ -f "$SPEC_DIR/spec.md" ]; then
  echo "  ✅ spec.md exists"
else
  echo "  ❌ spec.md missing"
  files_ok=false
fi

if [ -f "$SPEC_DIR/prd.md" ] || [ -L "$SPEC_DIR/prd.md" ]; then
  echo "  ✅ prd.md exists ($([ -L "$SPEC_DIR/prd.md" ] && echo "symlink" || echo "file"))"
else
  echo "  ❌ prd.md missing (Ralph needs this)"
  files_ok=false
fi

if [ -f "$SPEC_DIR/task_metadata.json" ]; then
  echo "  ✅ task_metadata.json exists"
else
  echo "  ❌ task_metadata.json missing"
  files_ok=false
fi

if [ -f "$SPEC_DIR/implementation_plan.json" ]; then
  echo "  ✅ implementation_plan.json exists"
else
  echo "  ❌ implementation_plan.json missing"
  files_ok=false
fi

echo ""

# Check 2: Execution flow is set to Ralph
echo "✓ Checking execution flow configuration..."
if grep -q '"executionFlow".*"ralph"' "$SPEC_DIR/task_metadata.json" 2>/dev/null; then
  echo "  ✅ executionFlow set to 'ralph'"
else
  echo "  ⚠️  executionFlow not set to 'ralph'"
fi

echo ""

# Check 3: Ralph progress field exists
echo "✓ Checking Ralph progress sync..."
if [ -f "$SPEC_DIR/implementation_plan.json" ]; then
  if grep -q '"ralph_progress"' "$SPEC_DIR/implementation_plan.json" 2>/dev/null; then
    echo "  ✅ ralph_progress field exists in implementation_plan.json"
    echo ""
    echo "  Ralph Progress Data:"
    if command -v jq &> /dev/null; then
      jq '.ralph_progress' "$SPEC_DIR/implementation_plan.json" | sed 's/^/    /'
    else
      grep -A 8 '"ralph_progress"' "$SPEC_DIR/implementation_plan.json" | sed 's/^/    /'
    fi
  else
    echo "  ⚠️  ralph_progress field not found (build may not have started yet)"
  fi
else
  echo "  ❌ implementation_plan.json not found"
fi

echo ""

# Check 4: Progress file exists
echo "✓ Checking Ralph progress tracking..."
if [ -f "$SPEC_DIR/progress.md" ]; then
  echo "  ✅ progress.md exists"

  # Count completed vs pending
  completed=$(grep -c '^\- \[x\]' "$SPEC_DIR/progress.md" 2>/dev/null || echo "0")
  pending=$(grep -c '^\- \[ \]' "$SPEC_DIR/progress.md" 2>/dev/null || echo "0")

  if [ "$completed" -gt 0 ] || [ "$pending" -gt 0 ]; then
    echo "  📊 Stories: $completed completed, $pending pending"
  else
    echo "  ⏳ No stories tracked yet (build may not have started)"
  fi
else
  echo "  ⚠️  progress.md not found (will be created when Ralph starts)"
fi

echo ""
echo "========================================="
echo "Verification Complete"
echo "========================================="
echo ""

if [ "$files_ok" = true ]; then
  echo "✅ All checks passed! Kanban should be able to read this task."
  echo ""
  echo "Next steps:"
  echo "1. Start Electron app: npm run dev"
  echo "2. Navigate to Kanban view"
  echo "3. Look for task '009-ralph-cli-test'"
  echo "4. You should see Ralph progress if build has started"
else
  echo "⚠️  Some files are missing. Run Ralph CLI build first."
fi

echo ""
