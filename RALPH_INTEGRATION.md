# Ralph-Enhanced Spec Creation Integration

This document describes the integration of Ralph-CLI's enhanced spec template into Auto-Claude's spec creation pipeline.

## Overview

Ralph-enhanced spec creation adds a three-tier permission boundary system to Auto-Claude specs, providing clear decision boundaries for what implementation agents can do autonomously, what requires user approval, and what's prohibited.

## Features

### 1. Three-Tier Permission System

- **✅ Always Do** - Actions agents can take autonomously without asking
- **⚠️ Ask First** - Actions requiring explicit user confirmation
- **🚫 Never Do** - Actions that are absolutely forbidden
- **Non-Goals** - Features explicitly out of scope

### 2. Project Type Detection

Automatically detects project type and generates appropriate boundaries:

- `electron_app` - Electron desktop applications
- `python_backend` - Python backend services
- `web_frontend` - Web frontend applications
- `react_typescript` - React + TypeScript projects
- `backend_api` - Backend API services
- `python_cli` - Python CLI tools
- `generic` - Fallback for unrecognized projects

### 3. Quality Scoring

Ralph template includes enhanced quality scoring (0-100 with A-F grades) based on:
- Structure (20 points) - Required sections, formatting
- Boundaries (20 points) - Three-tier permission system completeness
- Story Quality (25 points) - Verifiable criteria, examples, sizing
- Concreteness (20 points) - No vague language, no placeholders
- Context (15 points) - Project structure, commands, tech stack

## Usage

### Enable Ralph Template

Add to `apps/backend/.env`:

```bash
SPEC_TEMPLATE=ralph
```

### Create a Spec

```bash
cd apps/backend

# Create spec with Ralph template
python spec_runner.py --task "Add user authentication"

# The spec will include:
# - Auto-detected project type
# - Project-specific permission boundaries
# - boundaries.json file in spec directory
# - Enhanced quality validation
```

### Verify Integration

```bash
# Test project type detection
python3 -c "
import sys
sys.path.insert(0, 'apps/backend')
from spec.permissions.models import detect_project_type
print(f'Detected: {detect_project_type(\".\")}')"

# Test boundary generation
python3 -c "
import sys
sys.path.insert(0, 'apps/backend')
from spec.permissions.models import PermissionBoundary
boundaries = PermissionBoundary.from_project_type('electron_app')
print(f'Always Do: {len(boundaries.always_do)} items')
print(f'Ask First: {len(boundaries.ask_first)} items')
print(f'Never Do: {len(boundaries.never_do)} items')
print(f'Valid: {boundaries.is_valid()}')"
```

## Implementation Details

### Files Modified

1. **apps/backend/.env.example**
   - Added `SPEC_TEMPLATE` configuration option
   - Documentation for default vs ralph templates

2. **apps/backend/spec/phases/spec_phases.py**
   - Added `get_spec_template()` function
   - Modified `phase_spec_writing()` to support template selection
   - Added `_generate_boundaries_context()` method for Ralph template

3. **CLAUDE.md**
   - Added Ralph template documentation
   - Updated command examples
   - Added boundaries.json to spec directory structure

### Files Created

1. **apps/backend/spec/permissions/README.md**
   - Comprehensive documentation for permission boundaries
   - Usage examples
   - Customization guide

2. **RALPH_INTEGRATION.md** (this file)
   - Integration overview
   - Usage guide
   - Testing procedures

### Existing Files Used

1. **apps/backend/spec/permissions/models.py**
   - `PermissionBoundary` class
   - `detect_project_type()` function
   - Project-specific boundary templates

2. **apps/backend/prompts/spec_writer_ralph.md**
   - Ralph-enhanced spec writer prompt
   - Three-tier boundary requirements
   - Quality checklist

## Backward Compatibility

The integration is fully backward compatible:

- Default behavior unchanged (uses `spec_writer.md`)
- Ralph template is opt-in via `SPEC_TEMPLATE=ralph`
- Existing specs continue to work
- No changes to core spec creation pipeline

## Testing

### Unit Tests

```bash
cd apps/backend

# Test template selection
python3 -c "
import os
from spec.phases.spec_phases import get_spec_template

# Test default
assert get_spec_template() == 'default'

# Test ralph
os.environ['SPEC_TEMPLATE'] = 'ralph'
assert get_spec_template() == 'ralph'

# Test invalid (should fallback)
os.environ['SPEC_TEMPLATE'] = 'invalid'
assert get_spec_template() == 'default'

print('All tests passed!')
"
```

### Integration Test

```bash
cd apps/backend

# Create a test spec with Ralph template
export SPEC_TEMPLATE=ralph
python spec_runner.py --task "Test Ralph integration" --no-build

# Verify boundaries.json was created
ls -l .auto-claude/specs/*/boundaries.json

# Verify spec.md contains boundaries section
grep -A 5 "Boundaries (Three-Tier Permission System)" .auto-claude/specs/*/spec.md
```

## Configuration Reference

### Environment Variables

```bash
# Spec template selection
SPEC_TEMPLATE=default  # or 'ralph'
```

### Project Type Templates

See `apps/backend/spec/permissions/models.py` for all available project type templates:

- `electron_app`
- `python_backend`
- `web_frontend`
- `react_typescript`
- `backend_api`
- `python_cli`
- `generic` (fallback)

### Customization

To add a new project type:

1. Edit `apps/backend/spec/permissions/models.py`
2. Add new template to `PermissionBoundary.from_project_type()`
3. Update `detect_project_type()` if new detection logic needed

## See Also

- **Permission Boundaries Documentation**: `apps/backend/spec/permissions/README.md`
- **Ralph Spec Writer Prompt**: `apps/backend/prompts/spec_writer_ralph.md`
- **Ralph Scorer**: `apps/backend/spec/validate_pkg/scoring/ralph_scorer.py`
- **Project Instructions**: `CLAUDE.md`

## References

- Ralph-CLI: Inspiration for the three-tier boundary system
- Auto-Claude Spec Pipeline: `apps/backend/spec/pipeline/`
- Spec Validation: `apps/backend/spec/validate_pkg/`
