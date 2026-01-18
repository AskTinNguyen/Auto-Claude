"""
Spec Quality Scoring System
============================

Ralph's quality scoring system for spec validation.
Scores specs on structure, boundaries, story quality, concreteness, and context.
"""

from .ralph_scorer import RalphSpecScorer, QualityScore, ScoreBreakdown, QualityIssue

__all__ = ["RalphSpecScorer", "QualityScore", "ScoreBreakdown", "QualityIssue"]
