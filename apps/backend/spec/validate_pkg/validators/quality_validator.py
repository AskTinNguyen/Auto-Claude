"""
Quality Validator
=================

Validates spec quality using Ralph's scoring system.
Integrates RalphSpecScorer into the validation pipeline.
"""

import json
from pathlib import Path

from ..models import ValidationResult
from ..scoring.ralph_scorer import RalphSpecScorer


class QualityValidator:
    """Validates spec quality using Ralph's scoring system."""

    def __init__(self, spec_dir: Path, min_score: float = 70.0):
        """Initialize the quality validator.

        Args:
            spec_dir: Path to the spec directory
            min_score: Minimum score required to pass (default: 70.0)
        """
        self.spec_dir = Path(spec_dir)
        self.min_score = min_score

    def validate(self) -> ValidationResult:
        """Validate spec quality using Ralph's scoring system.

        Returns:
            ValidationResult with quality assessment
        """
        errors = []
        warnings = []
        fixes = []

        spec_file = self.spec_dir / "spec.md"

        if not spec_file.exists():
            errors.append("spec.md not found - cannot assess quality")
            fixes.append("Create spec.md before running quality assessment")
            return ValidationResult(False, "quality", errors, warnings, fixes)

        # Run quality scoring
        try:
            scorer = RalphSpecScorer(spec_file)
            quality_score = scorer.score()

            # Save quality score to JSON
            quality_file = self.spec_dir / "quality_score.json"
            self._save_quality_score(quality_file, quality_score)

            # Determine validation result based on score
            passed = quality_score.score >= self.min_score

            # Convert critical issues to errors
            critical_issues = [i for i in quality_score.issues if i.severity == "critical"]
            for issue in critical_issues:
                location = f" ({issue.location})" if issue.location else ""
                errors.append(f"[{issue.category}]{location} {issue.description}")
                if issue.suggestion:
                    fixes.append(issue.suggestion)

            # Convert major issues to warnings
            major_issues = [i for i in quality_score.issues if i.severity == "major"]
            for issue in major_issues:
                location = f" ({issue.location})" if issue.location else ""
                warnings.append(f"[{issue.category}]{location} {issue.description}")

            # Add score summary to warnings
            if not passed:
                errors.insert(
                    0,
                    f"Quality score {quality_score.score:.1f}/100 (Grade: {quality_score.grade}) "
                    f"below minimum threshold {self.min_score:.1f}"
                )
            else:
                warnings.insert(
                    0,
                    f"Quality score: {quality_score.score:.1f}/100 (Grade: {quality_score.grade})"
                )

            # Add recommendations as fixes
            for rec in quality_score.recommendations:
                fixes.append(rec)

            return ValidationResult(
                valid=passed,
                checkpoint="quality",
                errors=errors,
                warnings=warnings,
                fixes=fixes,
            )

        except Exception as e:
            errors.append(f"Quality scoring failed: {str(e)}")
            return ValidationResult(False, "quality", errors, warnings, fixes)

    def _save_quality_score(self, output_file: Path, quality_score) -> None:
        """Save quality score to JSON file.

        Args:
            output_file: Path to save quality_score.json
            quality_score: QualityScore object to save
        """
        data = {
            "score": quality_score.score,
            "grade": quality_score.grade,
            "breakdown": {
                "structure": quality_score.breakdown.structure_score,
                "boundaries": quality_score.breakdown.boundaries_score,
                "story_quality": quality_score.breakdown.story_quality_score,
                "concreteness": quality_score.breakdown.concreteness_score,
                "context": quality_score.breakdown.context_score,
            },
            "issues": [
                {
                    "category": issue.category,
                    "severity": issue.severity,
                    "description": issue.description,
                    "location": issue.location,
                    "suggestion": issue.suggestion,
                }
                for issue in quality_score.issues
            ],
            "recommendations": quality_score.recommendations,
        }

        output_file.write_text(json.dumps(data, indent=2))
