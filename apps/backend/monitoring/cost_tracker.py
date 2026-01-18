"""
Cost Tracker
============

Track token usage and API costs per session.
Enforces budget limits with warnings and hard stops.

Features:
- Track input/output tokens per session and iteration
- Calculate costs based on Claude pricing
- Enforce budget limits with warnings
- Save cost reports to spec directory
- Support multiple Claude models with different pricing
"""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class TokenUsage:
    """Token usage for a single API call."""

    input_tokens: int
    output_tokens: int
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0


@dataclass
class SessionCost:
    """Cost tracking for a single session."""

    session_id: int
    subtask_id: str | None
    phase: str
    model: str
    timestamp: str
    input_tokens: int
    output_tokens: int
    cache_creation_input_tokens: int
    cache_read_input_tokens: int
    cost_usd: float


@dataclass
class CostReport:
    """Overall cost report for the entire build."""

    total_input_tokens: int
    total_output_tokens: int
    total_cache_creation_tokens: int
    total_cache_read_tokens: int
    total_cost_usd: float
    sessions: list[SessionCost]
    created_at: str
    last_updated: str


class CostTracker:
    """
    Track token usage and API costs across build sessions.

    Supports Claude pricing tiers with prompt caching.
    """

    # Claude Sonnet 4.5 pricing (per 1M tokens) as of January 2025
    # Source: https://www.anthropic.com/pricing
    PRICING = {
        "claude-sonnet-4-5-20250929": {
            "input": 3.00,  # $3.00 per 1M input tokens
            "output": 15.00,  # $15.00 per 1M output tokens
            "cache_creation": 3.75,  # $3.75 per 1M cache creation tokens
            "cache_read": 0.30,  # $0.30 per 1M cache read tokens
        },
        "claude-sonnet-3-5-20240229": {
            "input": 3.00,
            "output": 15.00,
            "cache_creation": 3.75,
            "cache_read": 0.30,
        },
        "claude-opus-3-5-20241022": {
            "input": 15.00,
            "output": 75.00,
            "cache_creation": 18.75,
            "cache_read": 1.50,
        },
        "claude-3-5-sonnet-20241022": {
            "input": 3.00,
            "output": 15.00,
            "cache_creation": 3.75,
            "cache_read": 0.30,
        },
        # Add more models as needed
    }

    # Default pricing for unknown models (use Sonnet pricing)
    DEFAULT_PRICING = {
        "input": 3.00,
        "output": 15.00,
        "cache_creation": 3.75,
        "cache_read": 0.30,
    }

    def __init__(
        self,
        spec_dir: Path,
        budget_usd: float | None = None,
        warning_threshold: float = 0.8,
    ):
        """
        Initialize cost tracker.

        Args:
            spec_dir: Spec directory for storing cost reports
            budget_usd: Optional budget limit in USD
            warning_threshold: Warn when this fraction of budget is used (default: 0.8 = 80%)
        """
        self.spec_dir = spec_dir
        self.budget_usd = budget_usd
        self.warning_threshold = warning_threshold

        self.cost_file = spec_dir / "cost_report.json"

        # Initialize or load existing report
        if self.cost_file.exists():
            self.report = self._load_report()
        else:
            self.report = CostReport(
                total_input_tokens=0,
                total_output_tokens=0,
                total_cache_creation_tokens=0,
                total_cache_read_tokens=0,
                total_cost_usd=0.0,
                sessions=[],
                created_at=datetime.now().isoformat(),
                last_updated=datetime.now().isoformat(),
            )

    def _load_report(self) -> CostReport:
        """Load cost report from JSON file."""
        try:
            with open(self.cost_file, encoding="utf-8") as f:
                data = json.load(f)

            # Convert session dicts back to SessionCost objects
            sessions = [SessionCost(**s) for s in data.get("sessions", [])]

            return CostReport(
                total_input_tokens=data.get("total_input_tokens", 0),
                total_output_tokens=data.get("total_output_tokens", 0),
                total_cache_creation_tokens=data.get("total_cache_creation_tokens", 0),
                total_cache_read_tokens=data.get("total_cache_read_tokens", 0),
                total_cost_usd=data.get("total_cost_usd", 0.0),
                sessions=sessions,
                created_at=data.get("created_at", datetime.now().isoformat()),
                last_updated=data.get("last_updated", datetime.now().isoformat()),
            )
        except (OSError, json.JSONDecodeError, TypeError):
            # If file is corrupted, start fresh
            return CostReport(
                total_input_tokens=0,
                total_output_tokens=0,
                total_cache_creation_tokens=0,
                total_cache_read_tokens=0,
                total_cost_usd=0.0,
                sessions=[],
                created_at=datetime.now().isoformat(),
                last_updated=datetime.now().isoformat(),
            )

    def _save_report(self) -> None:
        """Save cost report to JSON file."""
        self.report.last_updated = datetime.now().isoformat()

        try:
            # Convert to dict for JSON serialization
            report_dict = {
                "total_input_tokens": self.report.total_input_tokens,
                "total_output_tokens": self.report.total_output_tokens,
                "total_cache_creation_tokens": self.report.total_cache_creation_tokens,
                "total_cache_read_tokens": self.report.total_cache_read_tokens,
                "total_cost_usd": self.report.total_cost_usd,
                "sessions": [asdict(s) for s in self.report.sessions],
                "created_at": self.report.created_at,
                "last_updated": self.report.last_updated,
            }

            with open(self.cost_file, "w", encoding="utf-8") as f:
                json.dump(report_dict, f, indent=2)
        except OSError:
            pass

    def get_pricing(self, model: str) -> dict:
        """
        Get pricing for a model.

        Args:
            model: Model identifier

        Returns:
            Dict with input/output/cache pricing
        """
        return self.PRICING.get(model, self.DEFAULT_PRICING)

    def calculate_cost(self, model: str, usage: TokenUsage) -> float:
        """
        Calculate cost for token usage.

        Args:
            model: Model identifier
            usage: Token usage data

        Returns:
            Cost in USD
        """
        pricing = self.get_pricing(model)

        input_cost = (usage.input_tokens / 1_000_000) * pricing["input"]
        output_cost = (usage.output_tokens / 1_000_000) * pricing["output"]
        cache_creation_cost = (
            usage.cache_creation_input_tokens / 1_000_000
        ) * pricing["cache_creation"]
        cache_read_cost = (usage.cache_read_input_tokens / 1_000_000) * pricing[
            "cache_read"
        ]

        return input_cost + output_cost + cache_creation_cost + cache_read_cost

    def record_session(
        self,
        session_id: int,
        model: str,
        usage: TokenUsage,
        subtask_id: str | None = None,
        phase: str = "unknown",
    ) -> dict:
        """
        Record token usage for a session.

        Args:
            session_id: Session identifier
            model: Model used
            usage: Token usage data
            subtask_id: Optional subtask ID
            phase: Phase (planning, coding, validation)

        Returns:
            Dict with cost info and budget status
        """
        cost = self.calculate_cost(model, usage)

        session_cost = SessionCost(
            session_id=session_id,
            subtask_id=subtask_id,
            phase=phase,
            model=model,
            timestamp=datetime.now().isoformat(),
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            cache_creation_input_tokens=usage.cache_creation_input_tokens,
            cache_read_input_tokens=usage.cache_read_input_tokens,
            cost_usd=cost,
        )

        # Update totals
        self.report.total_input_tokens += usage.input_tokens
        self.report.total_output_tokens += usage.output_tokens
        self.report.total_cache_creation_tokens += usage.cache_creation_input_tokens
        self.report.total_cache_read_tokens += usage.cache_read_input_tokens
        self.report.total_cost_usd += cost
        self.report.sessions.append(session_cost)

        # Save to disk
        self._save_report()

        # Check budget
        result = {
            "session_cost_usd": cost,
            "total_cost_usd": self.report.total_cost_usd,
            "budget_exceeded": False,
            "budget_warning": False,
        }

        if self.budget_usd:
            usage_fraction = self.report.total_cost_usd / self.budget_usd
            result["budget_usage_percent"] = usage_fraction * 100

            if self.report.total_cost_usd >= self.budget_usd:
                result["budget_exceeded"] = True
            elif usage_fraction >= self.warning_threshold:
                result["budget_warning"] = True

        return result

    def get_report(self) -> CostReport:
        """Get the current cost report."""
        return self.report

    def get_summary(self) -> dict:
        """
        Get a summary of costs.

        Returns:
            Dict with summary statistics
        """
        total_tokens = (
            self.report.total_input_tokens
            + self.report.total_output_tokens
            + self.report.total_cache_creation_tokens
            + self.report.total_cache_read_tokens
        )

        summary = {
            "total_sessions": len(self.report.sessions),
            "total_tokens": total_tokens,
            "total_input_tokens": self.report.total_input_tokens,
            "total_output_tokens": self.report.total_output_tokens,
            "total_cache_creation_tokens": self.report.total_cache_creation_tokens,
            "total_cache_read_tokens": self.report.total_cache_read_tokens,
            "total_cost_usd": self.report.total_cost_usd,
        }

        if self.budget_usd:
            summary["budget_usd"] = self.budget_usd
            summary["budget_remaining_usd"] = self.budget_usd - self.report.total_cost_usd
            summary["budget_usage_percent"] = (
                self.report.total_cost_usd / self.budget_usd
            ) * 100

        return summary

    def reset(self) -> None:
        """Reset all cost tracking (use with caution)."""
        self.report = CostReport(
            total_input_tokens=0,
            total_output_tokens=0,
            total_cache_creation_tokens=0,
            total_cache_read_tokens=0,
            total_cost_usd=0.0,
            sessions=[],
            created_at=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
        )
        self._save_report()
