#!/bin/bash
# Monitor Ralph CLI progress and show what Kanban will see

SPEC_DIR="/Users/tinnguyen/Auto-Claude/.auto-claude/specs/009-ralph-cli-test"

echo "========================================="
echo "Ralph CLI Progress Monitor"
echo "========================================="
echo ""
echo "Monitoring: $SPEC_DIR"
echo ""
echo "Press Ctrl+C to stop"
echo ""

while true; do
  clear
  echo "========================================="
  echo "Ralph CLI Progress Monitor"
  echo "========================================="
  echo ""

  # Show progress.md (Ralph's format)
  if [ -f "$SPEC_DIR/progress.md" ]; then
    echo "📝 Ralph's progress.md:"
    echo "---"
    cat "$SPEC_DIR/progress.md"
    echo ""
  else
    echo "⏳ Waiting for progress.md..."
    echo ""
  fi

  # Show implementation_plan.json (Kanban's format)
  if [ -f "$SPEC_DIR/implementation_plan.json" ]; then
    echo "📊 Kanban's view (implementation_plan.json):"
    echo "---"

    # Extract ralph_progress field if it exists
    if command -v jq &> /dev/null; then
      if jq -e '.ralph_progress' "$SPEC_DIR/implementation_plan.json" &> /dev/null; then
        echo "Ralph Progress Summary:"
        jq '.ralph_progress' "$SPEC_DIR/implementation_plan.json"
      else
        echo "No ralph_progress field yet (will appear after first sync)"
      fi
    else
      # Fallback if jq not available
      grep -A 8 '"ralph_progress"' "$SPEC_DIR/implementation_plan.json" || echo "No ralph_progress field yet"
    fi
    echo ""
  else
    echo "⏳ Waiting for implementation_plan.json..."
    echo ""
  fi

  echo "========================================="
  echo "Last updated: $(date '+%H:%M:%S')"
  echo "========================================="

  sleep 2
done
