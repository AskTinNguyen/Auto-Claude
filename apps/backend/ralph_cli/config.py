"""
Ralph CLI Configuration
======================

YAML-based configuration for Ralph CLI settings.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Try to import yaml, fall back to basic parsing if not available
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


@dataclass
class CLIConfig:
    """CLI display and behavior settings."""
    enabled: bool = True
    color: bool = True
    verbose: bool = False


@dataclass
class DefaultsConfig:
    """Default values for operations."""
    model: str = "claude-sonnet-4-5-20250929"
    iterations: int = 5
    auto_commit: bool = True


@dataclass
class BudgetConfig:
    """Budget tracking settings."""
    global_limit_usd: float | None = None
    warning_threshold: float = 0.8


@dataclass
class TTSCliConfig:
    """TTS settings for CLI."""
    enabled: bool = True
    provider: str = "auto"
    voice: str = "alba"
    auto_speak: bool = False


@dataclass
class PermissionsConfig:
    """Permission boundary settings."""
    always_do: list[str] = field(default_factory=lambda: ["run_tests", "lint_code"])
    ask_first: list[str] = field(default_factory=lambda: ["delete_files", "modify_config"])
    never_do: list[str] = field(default_factory=lambda: ["push_to_main", "delete_branches"])


@dataclass
class RalphConfig:
    """
    Main Ralph CLI configuration.

    Loads from .ralph-config.yaml or environment variables.
    """
    cli: CLIConfig = field(default_factory=CLIConfig)
    defaults: DefaultsConfig = field(default_factory=DefaultsConfig)
    budget: BudgetConfig = field(default_factory=BudgetConfig)
    tts: TTSCliConfig = field(default_factory=TTSCliConfig)
    permissions: PermissionsConfig = field(default_factory=PermissionsConfig)

    # Paths
    project_dir: Path = field(default_factory=Path.cwd)
    auto_claude_dir: Path = field(default_factory=lambda: Path.cwd() / ".auto-claude")

    @classmethod
    def load(cls, project_dir: Path | None = None) -> "RalphConfig":
        """
        Load configuration from .ralph-config.yaml file.

        Falls back to environment variables and defaults.

        Args:
            project_dir: Project directory (uses cwd if None)

        Returns:
            RalphConfig instance
        """
        project_dir = project_dir or Path.cwd()
        config_file = project_dir / ".ralph-config.yaml"

        # Start with defaults
        config = cls(
            project_dir=project_dir,
            auto_claude_dir=project_dir / ".auto-claude"
        )

        # Load from YAML if available
        if config_file.exists() and YAML_AVAILABLE:
            try:
                with open(config_file, encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}

                config = cls._from_dict(data, project_dir)
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")

        # Override with environment variables
        config = cls._apply_env_overrides(config)

        return config

    @classmethod
    def _from_dict(cls, data: dict[str, Any], project_dir: Path) -> "RalphConfig":
        """Create config from dictionary."""
        cli_data = data.get("cli", {})
        defaults_data = data.get("defaults", {})
        budget_data = data.get("budget", {})
        tts_data = data.get("tts", {})
        permissions_data = data.get("permissions", {})

        return cls(
            cli=CLIConfig(
                enabled=cli_data.get("enabled", True),
                color=cli_data.get("color", True),
                verbose=cli_data.get("verbose", False),
            ),
            defaults=DefaultsConfig(
                model=defaults_data.get("model", "claude-sonnet-4-5-20250929"),
                iterations=defaults_data.get("iterations", 5),
                auto_commit=defaults_data.get("auto_commit", True),
            ),
            budget=BudgetConfig(
                global_limit_usd=budget_data.get("global_limit_usd"),
                warning_threshold=budget_data.get("warning_threshold", 0.8),
            ),
            tts=TTSCliConfig(
                enabled=tts_data.get("enabled", True),
                provider=tts_data.get("provider", "auto"),
                voice=tts_data.get("voice", "alba"),
                auto_speak=tts_data.get("auto_speak", False),
            ),
            permissions=PermissionsConfig(
                always_do=permissions_data.get("always_do", ["run_tests", "lint_code"]),
                ask_first=permissions_data.get("ask_first", ["delete_files", "modify_config"]),
                never_do=permissions_data.get("never_do", ["push_to_main", "delete_branches"]),
            ),
            project_dir=project_dir,
            auto_claude_dir=project_dir / ".auto-claude",
        )

    @classmethod
    def _apply_env_overrides(cls, config: "RalphConfig") -> "RalphConfig":
        """Apply environment variable overrides."""
        # CLI settings
        if os.getenv("RALPH_CLI_COLOR"):
            config.cli.color = os.getenv("RALPH_CLI_COLOR", "true").lower() == "true"
        if os.getenv("RALPH_CLI_VERBOSE"):
            config.cli.verbose = os.getenv("RALPH_CLI_VERBOSE", "false").lower() == "true"

        # Default settings
        if os.getenv("RALPH_DEFAULT_MODEL"):
            config.defaults.model = os.getenv("RALPH_DEFAULT_MODEL")
        if os.getenv("RALPH_DEFAULT_ITERATIONS"):
            config.defaults.iterations = int(os.getenv("RALPH_DEFAULT_ITERATIONS", "5"))

        # Budget settings
        if os.getenv("RALPH_BUDGET_LIMIT"):
            config.budget.global_limit_usd = float(os.getenv("RALPH_BUDGET_LIMIT"))

        # TTS settings
        if os.getenv("TTS_ENABLED"):
            config.tts.enabled = os.getenv("TTS_ENABLED", "true").lower() == "true"
        if os.getenv("TTS_PROVIDER"):
            config.tts.provider = os.getenv("TTS_PROVIDER")

        return config

    def save(self) -> None:
        """Save configuration to .ralph-config.yaml file."""
        if not YAML_AVAILABLE:
            print("Warning: PyYAML not installed, cannot save config")
            return

        config_file = self.project_dir / ".ralph-config.yaml"

        data = {
            "cli": {
                "enabled": self.cli.enabled,
                "color": self.cli.color,
                "verbose": self.cli.verbose,
            },
            "defaults": {
                "model": self.defaults.model,
                "iterations": self.defaults.iterations,
                "auto_commit": self.defaults.auto_commit,
            },
            "budget": {
                "global_limit_usd": self.budget.global_limit_usd,
                "warning_threshold": self.budget.warning_threshold,
            },
            "tts": {
                "enabled": self.tts.enabled,
                "provider": self.tts.provider,
                "voice": self.tts.voice,
                "auto_speak": self.tts.auto_speak,
            },
            "permissions": {
                "always_do": self.permissions.always_do,
                "ask_first": self.permissions.ask_first,
                "never_do": self.permissions.never_do,
            },
        }

        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        print(f"Configuration saved to {config_file}")

    def get_specs_dir(self) -> Path:
        """Get the specs directory path."""
        return self.auto_claude_dir / "specs"

    def get_worktrees_dir(self) -> Path:
        """Get the worktrees directory path."""
        return self.auto_claude_dir / "worktrees" / "tasks"
