#!/usr/bin/env python3
"""
Manual sync script - demonstrates syncing Ralph CLI progress to Kanban format.
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "apps" / "backend"))

from integrations.ralph_cli import sync_progress_to_plan

if __name__ == "__main__":
    spec_dir = Path(__file__).parent / ".auto-claude" / "specs" / "009-ralph-cli-test"

    print("=" * 70)
    print("Syncing Ralph CLI Progress to Kanban Format")
    print("=" * 70)
    print(f"\nSpec directory: {spec_dir}")
    print(f"Progress file: {spec_dir / 'progress.md'}")
    print(f"Plan file: {spec_dir / 'implementation_plan.json'}")
    print()

    result = sync_progress_to_plan(spec_dir)

    if result:
        print("✅ Sync successful!")
        print()
        print("Kanban will now show:")

        # Read and display the synced data
        import json
        plan_file = spec_dir / "implementation_plan.json"
        plan = json.loads(plan_file.read_text())

        if "ralph_progress" in plan:
            rp = plan["ralph_progress"]
            print(f"  - Completed stories: {rp['completed_stories']}")
            print(f"  - Pending stories: {rp['pending_stories']}")
            print(f"  - Total stories: {rp['total_stories']}")
            print(f"  - Commits: {', '.join(rp['commits'])}")
            print()
            print(f"Last sync: {rp['last_sync']}")
        else:
            print("  ⚠️  No ralph_progress field found")
    else:
        print("❌ Sync failed")
        sys.exit(1)

    print()
    print("=" * 70)
    print("Next: Start Electron app and check Kanban view for task 009")
    print("=" * 70)
