# Ralph Permission Boundaries

This module implements Ralph-CLI's three-tier permission boundary system for Auto-Claude specs.

## Overview

The permission boundary system provides clear decision boundaries for what implementation agents can do autonomously, what requires user approval, and what's prohibited.

## Three Tiers

### ✅ Always Do (No Permission Required)
Actions the agent can take autonomously without asking.

### ⚠️ Ask First (Requires User Approval)
Actions requiring explicit user confirmation.

### 🚫 Never Do (Prohibited Actions)
Actions that are absolutely forbidden.

## Usage

### Environment Variable

Set `SPEC_TEMPLATE=ralph` in `.env` to enable Ralph-enhanced spec creation:

```bash
# .env
SPEC_TEMPLATE=ralph
```

### Automatic Project Detection

The system automatically detects your project type and generates appropriate boundaries:

- `electron_app` - Electron desktop applications
- `python_backend` - Python backend services
- `web_frontend` - Web frontend applications
- `react_typescript` - React + TypeScript projects
- `backend_api` - Backend API services
- `python_cli` - Python CLI tools
- `generic` - Fallback for unrecognized projects

### Example

```python
from spec.permissions.models import PermissionBoundary, detect_project_type

# Detect project type
project_type = detect_project_type("/path/to/project")
print(f"Detected: {project_type}")  # e.g., "electron_app"

# Generate boundaries
boundaries = PermissionBoundary.from_project_type(project_type)

# Validate (requires minimum 3 items per tier)
errors = boundaries.validate()
if errors:
    print(f"Validation errors: {errors}")

# Convert to markdown for spec.md
markdown = boundaries.to_markdown()
print(markdown)

# Save to file
import json
with open("boundaries.json", "w") as f:
    json.dump(boundaries.to_dict(), f, indent=2)
```

## Integration with Spec Creation

When `SPEC_TEMPLATE=ralph` is set:

1. **Project Detection**: During spec creation, the system detects the project type
2. **Boundary Generation**: Appropriate boundaries are generated based on the project type
3. **File Creation**: `boundaries.json` is saved to the spec directory
4. **Spec Writing**: Boundaries are included in the spec writer prompt and inserted into `spec.md`

The boundaries appear in the generated `spec.md` under a dedicated "Boundaries" section.

## Customization

You can customize boundaries by:

1. **Modifying templates** in `models.py` (`from_project_type()` method)
2. **Creating custom boundaries** programmatically:

```python
custom = PermissionBoundary(
    always_do=[
        "Modify feature-specific files",
        "Add unit tests",
        "Run test suite",
    ],
    ask_first=[
        "Change core modules",
        "Add dependencies",
        "Modify configuration",
    ],
    never_do=[
        "Commit secrets",
        "Delete tests",
        "Skip validation",
    ],
    non_goals=[
        "Performance optimization (separate task)",
    ]
)
```

## Validation

All boundaries must meet these requirements:

- **Minimum 3 items** in Always Do tier
- **Minimum 3 items** in Ask First tier
- **Minimum 3 items** in Never Do tier
- Non-Goals tier is optional

The `validate()` method returns a list of error messages (empty list if valid).

## Files

- `models.py` - Core PermissionBoundary model and project type detection
- `README.md` - This documentation
- `__init__.py` - Module exports

## See Also

- Ralph-CLI PRD boundary system: [Original inspiration](https://github.com/ralphcli/ralph)
- Spec creation pipeline: `apps/backend/spec/phases/spec_phases.py`
- Spec writer prompt: `apps/backend/prompts/spec_writer_ralph.md`
