"""
Permission Boundary Models
==========================

Three-tier permission boundaries for agent autonomy.
Adapted from Ralph-CLI's PRD boundary system.
"""

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class PermissionBoundary:
    """
    Three-tier permission boundaries for agent operations.

    Inspired by Ralph-CLI's PRD boundary system:
    - Always Do (✅): Agent can execute autonomously without asking
    - Ask First (⚠️): Requires user approval before execution
    - Never Do (🚫): Prohibited actions that should never occur
    - Non-Goals: Features explicitly out of scope

    Ralph's requirement: Minimum 3 items per tier
    """

    always_do: List[str] = field(default_factory=list)
    ask_first: List[str] = field(default_factory=list)
    never_do: List[str] = field(default_factory=list)
    non_goals: List[str] = field(default_factory=list)

    def validate(self) -> List[str]:
        """
        Validate boundary structure.

        Ralph requirement: Each tier must have minimum 3 items.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if len(self.always_do) < 3:
            errors.append(
                f"'Always Do' tier requires at least 3 items (has {len(self.always_do)})"
            )

        if len(self.ask_first) < 3:
            errors.append(
                f"'Ask First' tier requires at least 3 items (has {len(self.ask_first)})"
            )

        if len(self.never_do) < 3:
            errors.append(
                f"'Never Do' tier requires at least 3 items (has {len(self.never_do)})"
            )

        return errors

    def is_valid(self) -> bool:
        """Check if boundaries are valid."""
        return len(self.validate()) == 0

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "always_do": self.always_do,
            "ask_first": self.ask_first,
            "never_do": self.never_do,
            "non_goals": self.non_goals,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "PermissionBoundary":
        """Load from dictionary."""
        return cls(
            always_do=data.get("always_do", []),
            ask_first=data.get("ask_first", []),
            never_do=data.get("never_do", []),
            non_goals=data.get("non_goals", []),
        )

    @classmethod
    def from_project_type(cls, project_type: str) -> "PermissionBoundary":
        """
        Generate default boundaries based on detected project type.

        Args:
            project_type: Detected project type (e.g., "web_frontend", "backend_api")

        Returns:
            PermissionBoundary with project-appropriate defaults
        """
        templates = {
            "web_frontend": cls(
                always_do=[
                    "Modify files in src/components, src/pages, src/features",
                    "Add unit tests for new components (*.test.tsx, *.spec.tsx)",
                    "Run npm test and npm run build to verify changes",
                    "Update CSS/styling files and component prop types",
                    "Add TypeScript interfaces and type definitions",
                    "Update i18n translation files for new UI text",
                    "Create component stories for Storybook (if applicable)",
                ],
                ask_first=[
                    "Modify shared utility files (src/utils, src/lib, src/shared)",
                    "Add new npm dependencies to package.json",
                    "Change API endpoint contracts or GraphQL schemas",
                    "Modify build configuration (webpack, vite, tsconfig)",
                    "Update Dockerfile or docker-compose.yml",
                    "Change routing configuration or add new routes",
                    "Modify state management stores (Redux, Zustand, etc.)",
                ],
                never_do=[
                    "Commit secrets, API keys, or authentication tokens",
                    "Delete existing tests without replacement",
                    "Push directly to main/master branch",
                    "Modify production environment configuration (.env.production)",
                    "Remove error handling or input validation",
                    "Disable TypeScript strict mode or ESLint rules",
                    "Commit node_modules or build artifacts",
                ],
                non_goals=[
                    "Performance optimization (separate task)",
                    "Mobile responsive design (future iteration)",
                ],
            ),
            "backend_api": cls(
                always_do=[
                    "Modify files in src/api, src/routes, src/controllers",
                    "Add endpoint tests (pytest, unittest, etc.)",
                    "Run pytest and linting (pylint, flake8, mypy)",
                    "Update API documentation (OpenAPI/Swagger)",
                    "Add database migrations for schema changes",
                    "Add input validation schemas (Pydantic, marshmallow)",
                    "Update error response formats",
                ],
                ask_first=[
                    "Change authentication or authorization logic",
                    "Modify rate limiting or throttling configuration",
                    "Add new external service integrations (AWS, Stripe, etc.)",
                    "Change database indexes or query optimization",
                    "Update API versioning strategy",
                    "Modify core middleware or request/response interceptors",
                    "Add new database tables or major schema changes",
                ],
                never_do=[
                    "Expose sensitive data in API responses or logs",
                    "Disable authentication or authorization checks",
                    "Commit database credentials or API secrets",
                    "Remove input validation or sanitization",
                    "Delete database migration files",
                    "Skip HTTPS or security headers in production",
                    "Log user passwords or sensitive PII",
                ],
                non_goals=[],
            ),
            "python_cli": cls(
                always_do=[
                    "Modify CLI command files (cli/, commands/)",
                    "Add command tests (pytest tests/)",
                    "Run pytest with coverage reporting",
                    "Update CLI help text and documentation",
                    "Add new CLI flags and arguments",
                    "Update requirements.txt with new dependencies",
                    "Add input validation for CLI arguments",
                ],
                ask_first=[
                    "Change default CLI behavior or command structure",
                    "Add new external dependencies (require approval)",
                    "Modify configuration file format (.yaml, .toml, .json)",
                    "Change exit codes or error handling strategy",
                    "Add new subcommands to existing command groups",
                    "Modify logging configuration or output formats",
                ],
                never_do=[
                    "Remove backward compatibility with previous versions",
                    "Delete user configuration files without backup",
                    "Commit credentials or API tokens to version control",
                    "Remove command help text or usage information",
                    "Change command names without deprecation period",
                ],
                non_goals=[],
            ),
            "electron_app": cls(
                always_do=[
                    "Modify renderer process code (src/renderer/)",
                    "Add component tests and E2E tests",
                    "Run npm test and npm run build",
                    "Update i18n translations for new UI text",
                    "Add IPC channel handlers for new features",
                    "Update TypeScript interfaces for IPC communication",
                ],
                ask_first=[
                    "Modify main process code (src/main/)",
                    "Change IPC channel names or message formats",
                    "Add new native node modules or dependencies",
                    "Modify auto-updater configuration",
                    "Change Electron security settings (CSP, webSecurity)",
                    "Update app signing or notarization configuration",
                ],
                never_do=[
                    "Disable Electron security features (nodeIntegration, contextIsolation)",
                    "Expose main process APIs to renderer without validation",
                    "Commit signing certificates or update server credentials",
                    "Remove error handling in main process",
                    "Allow arbitrary code execution from renderer",
                ],
                non_goals=[],
            ),
            "react_typescript": cls(
                always_do=[
                    "Modify React components in src/components",
                    "Add component tests (*.test.tsx)",
                    "Run npm test and type checking (tsc --noEmit)",
                    "Update component prop types and interfaces",
                    "Add hooks for state management",
                    "Update i18n translation keys",
                    "Create component documentation",
                ],
                ask_first=[
                    "Modify shared hooks (src/hooks/)",
                    "Change context providers or global state",
                    "Add new npm dependencies",
                    "Modify build configuration (webpack, tsconfig)",
                    "Change routing structure or add new routes",
                ],
                never_do=[
                    "Use 'any' type without justification",
                    "Disable TypeScript strict checks",
                    "Remove error boundaries",
                    "Commit .env files with secrets",
                    "Delete tests without replacement",
                ],
                non_goals=[],
            ),
            "python_backend": cls(
                always_do=[
                    "Modify feature modules in apps/backend/",
                    "Add pytest tests for new functionality",
                    "Run pytest, mypy, and pylint",
                    "Add type hints to all new functions",
                    "Update docstrings following project conventions",
                    "Add database migrations if schema changes",
                ],
                ask_first=[
                    "Modify core modules (core/, integrations/)",
                    "Change Claude Agent SDK configuration",
                    "Add new external service integrations",
                    "Modify security policies or sandbox rules",
                    "Change database connection or ORM configuration",
                ],
                never_do=[
                    "Commit API keys, OAuth tokens, or secrets",
                    "Disable security checks or sandbox isolation",
                    "Remove type hints from existing code",
                    "Skip pytest or type checking",
                    "Modify production .env files",
                ],
                non_goals=[],
            ),
        }

        # Return template if exists, otherwise generic default
        return templates.get(
            project_type,
            cls(
                always_do=[
                    "Modify feature-specific files",
                    "Add tests for new functionality",
                    "Run project test suite",
                ],
                ask_first=[
                    "Modify shared/core code",
                    "Add external dependencies",
                    "Change configuration files",
                ],
                never_do=[
                    "Commit secrets or credentials",
                    "Delete existing tests",
                    "Skip test execution",
                ],
                non_goals=[],
            ),
        )

    def to_markdown(self) -> str:
        """
        Convert boundaries to markdown format for spec.md.

        Returns:
            Markdown-formatted string ready for inclusion in spec
        """
        lines = ["## Boundaries (Three-Tier Permission System)", ""]

        # Always Do section
        lines.append("### ✅ Always Do (No Permission Required)")
        lines.append("")
        lines.append("Actions the agent can take autonomously without asking:")
        lines.append("")
        for item in self.always_do:
            lines.append(f"- {item}")
        lines.append("")

        # Ask First section
        lines.append("### ⚠️ Ask First (Requires User Approval)")
        lines.append("")
        lines.append("Actions requiring explicit user confirmation:")
        lines.append("")
        for item in self.ask_first:
            lines.append(f"- {item}")
        lines.append("")

        # Never Do section
        lines.append("### 🚫 Never Do (Prohibited Actions)")
        lines.append("")
        lines.append("Actions that are absolutely forbidden:")
        lines.append("")
        for item in self.never_do:
            lines.append(f"- {item}")
        lines.append("")

        # Non-Goals section
        if self.non_goals:
            lines.append("### Non-Goals (Explicit Out of Scope)")
            lines.append("")
            lines.append("Features and functionality NOT included in this PRD:")
            lines.append("")
            for item in self.non_goals:
                lines.append(f"- {item}")
            lines.append("")

        return "\n".join(lines)


def detect_project_type(project_dir) -> str:
    """
    Detect project type from project structure and files.

    Args:
        project_dir: Path to project directory

    Returns:
        Project type string (e.g., "web_frontend", "backend_api")
    """
    from pathlib import Path

    project_path = Path(project_dir)

    # Check for Electron app
    if (project_path / "apps" / "frontend" / "src" / "main").exists() and (
        project_path / "apps" / "frontend" / "src" / "renderer"
    ).exists():
        return "electron_app"

    # Check for Python backend
    if (project_path / "apps" / "backend").exists() and (
        project_path / "apps" / "backend" / "core"
    ).exists():
        return "python_backend"

    # Check for React TypeScript frontend
    if (project_path / "tsconfig.json").exists():
        package_json = project_path / "package.json"
        if package_json.exists():
            import json

            try:
                with open(package_json) as f:
                    pkg = json.load(f)
                    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                    if "react" in deps and "typescript" in deps:
                        return "react_typescript"
                    if "react" in deps:
                        return "web_frontend"
            except Exception:
                pass

    # Check for Python CLI
    if (project_path / "cli").exists() or (project_path / "commands").exists():
        if (project_path / "requirements.txt").exists() or (
            project_path / "pyproject.toml"
        ).exists():
            return "python_cli"

    # Check for backend API
    if (project_path / "src" / "api").exists() or (project_path / "src" / "routes").exists():
        return "backend_api"

    # Check for web frontend
    if (project_path / "src" / "components").exists() or (
        project_path / "src" / "pages"
    ).exists():
        return "web_frontend"

    # Default fallback
    return "generic"
