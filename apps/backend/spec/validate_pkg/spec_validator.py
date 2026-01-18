"""
Spec Validator
==============

Main validator class that orchestrates all validation checkpoints.
"""

from pathlib import Path

from .models import ValidationResult
from .validators import (
    ContextValidator,
    ImplementationPlanValidator,
    PrereqsValidator,
    QualityValidator,
    SpecDocumentValidator,
)


class SpecValidator:
    """Validates spec outputs at each checkpoint."""

    def __init__(self, spec_dir: Path, min_quality_score: float = 70.0):
        """Initialize the spec validator.

        Args:
            spec_dir: Path to the spec directory
            min_quality_score: Minimum quality score required (default: 70.0)
        """
        self.spec_dir = Path(spec_dir)
        self.min_quality_score = min_quality_score

        # Initialize individual validators
        self._prereqs_validator = PrereqsValidator(self.spec_dir)
        self._context_validator = ContextValidator(self.spec_dir)
        self._spec_document_validator = SpecDocumentValidator(self.spec_dir)
        self._implementation_plan_validator = ImplementationPlanValidator(self.spec_dir)
        self._quality_validator = QualityValidator(self.spec_dir, min_quality_score)

    def validate_all(self) -> list[ValidationResult]:
        """Run all validations.

        Returns:
            List of validation results for all checkpoints
        """
        results = [
            self.validate_prereqs(),
            self.validate_context(),
            self.validate_spec_document(),
            self.validate_implementation_plan(),
            self.validate_quality(),
        ]
        return results

    def validate_prereqs(self) -> ValidationResult:
        """Validate prerequisites exist.

        Returns:
            ValidationResult for prerequisites checkpoint
        """
        return self._prereqs_validator.validate()

    def validate_context(self) -> ValidationResult:
        """Validate context.json exists and has required structure.

        Returns:
            ValidationResult for context checkpoint
        """
        return self._context_validator.validate()

    def validate_spec_document(self) -> ValidationResult:
        """Validate spec.md exists and has required sections.

        Returns:
            ValidationResult for spec document checkpoint
        """
        return self._spec_document_validator.validate()

    def validate_implementation_plan(self) -> ValidationResult:
        """Validate implementation_plan.json exists and has valid schema.

        Returns:
            ValidationResult for implementation plan checkpoint
        """
        return self._implementation_plan_validator.validate()

    def validate_quality(self) -> ValidationResult:
        """Validate spec quality using Ralph's scoring system.

        Returns:
            ValidationResult for quality checkpoint
        """
        return self._quality_validator.validate()
