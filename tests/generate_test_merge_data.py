#!/usr/bin/env python3
"""
Generate Test Merge Data for Manual UI Verification

This script creates sample merge completion records in .auto-claude/merge-history/
for testing the frontend Merge History display.

Usage:
    python3 tests/generate_test_merge_data.py
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add apps/backend to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "apps" / "backend"))

from core.workspace import _record_merge_completion


def main():
    """Generate test merge data."""

    # Use current directory as project root
    project_dir = Path.cwd()

    print("🔧 Generating test merge data...")
    print(f"📁 Project directory: {project_dir}")

    # Test spec name
    spec_name = "001-merge-completion-tracking-implementation"

    # Scenario 1: Successful AI-assisted merge (recent)
    print("\n✅ Creating AI-assisted merge record...")
    _record_merge_completion(
        project_dir=project_dir,
        spec_name=spec_name,
        resolved_files=[
            "apps/backend/core/workspace/merge_completion.py",
            "apps/backend/core/workspace.py",
            "apps/frontend/src/renderer/components/task-detail/MergeHistory.tsx",
            "apps/frontend/src/renderer/components/task-detail/TaskDetailModal.tsx",
            "tests/test_merge_completion.py",
        ],
        stats={
            "conflicts_resolved": 5,
            "ai_assisted": 3,
            "auto_merged": 2,
            "git_conflicts": 5,
            "merge_strategy": "ai-assisted",
            "duration_seconds": 47.3,
        },
    )

    # Scenario 2: Fast-forward merge (no conflicts)
    print("✅ Creating fast-forward merge record...")
    _record_merge_completion(
        project_dir=project_dir,
        spec_name=spec_name,
        resolved_files=[
            "apps/frontend/src/shared/i18n/locales/en/tasks.json",
            "apps/frontend/src/shared/i18n/locales/fr/tasks.json",
        ],
        stats={
            "conflicts_resolved": 0,
            "ai_assisted": 0,
            "auto_merged": 0,
            "git_conflicts": 0,
            "merge_strategy": "fast-forward",
            "duration_seconds": 2.1,
        },
    )

    # Scenario 3: 3-way merge with some conflicts
    print("✅ Creating 3-way merge record...")
    _record_merge_completion(
        project_dir=project_dir,
        spec_name=spec_name,
        resolved_files=[
            "apps/frontend/src/main/ipc-handlers.ts",
            "apps/frontend/src/renderer/api/task-api.ts",
            "apps/frontend/src/shared/types/task.ts",
        ],
        stats={
            "conflicts_resolved": 2,
            "ai_assisted": 1,
            "auto_merged": 2,
            "git_conflicts": 2,
            "merge_strategy": "3-way",
            "duration_seconds": 18.7,
        },
    )

    # Scenario 4: Another spec to test filtering
    print("✅ Creating merge record for different spec...")
    _record_merge_completion(
        project_dir=project_dir,
        spec_name="002-example-feature",
        resolved_files=[
            "README.md",
            "package.json",
        ],
        stats={
            "conflicts_resolved": 1,
            "ai_assisted": 0,
            "auto_merged": 1,
            "git_conflicts": 1,
            "merge_strategy": "3-way",
            "duration_seconds": 5.4,
        },
    )

    # Check merge history file
    merge_history_file = project_dir / ".auto-claude" / "merge-history" / "merge_history.json"

    if merge_history_file.exists():
        print(f"\n✅ Test merge data created successfully!")
        print(f"📄 Location: {merge_history_file}")
        print(f"📊 File size: {merge_history_file.stat().st_size} bytes")

        # Read and display summary
        import json
        with open(merge_history_file) as f:
            data = json.load(f)

        print(f"\n📈 Summary:")
        print(f"   Total merge records: {len(data)}")

        # Count by spec
        specs = {}
        for record in data:
            spec = record.get("spec_name", "unknown")
            specs[spec] = specs.get(spec, 0) + 1

        print(f"   Records by spec:")
        for spec, count in specs.items():
            print(f"     - {spec}: {count}")

        print(f"\n🎉 Ready for UI testing!")
        print(f"\nNext steps:")
        print(f"1. Run 'npm run dev' to start the frontend")
        print(f"2. Open a task detail modal")
        print(f"3. Click the 'Merge History' tab")
        print(f"4. Verify merge events are displayed correctly")

    else:
        print(f"\n❌ Error: Merge history file not created")
        print(f"Expected location: {merge_history_file}")


if __name__ == "__main__":
    main()
