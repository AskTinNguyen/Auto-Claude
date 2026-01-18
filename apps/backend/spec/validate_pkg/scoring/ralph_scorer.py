"""
Ralph's Spec Quality Scoring System
====================================

Implements the 10 Principles of Good Spec Design scoring system.
Scores specs on a 100-point scale across 5 categories:
- Structure (20 points)
- Boundaries (20 points)
- Story Quality (25 points)
- Concreteness (20 points)
- Context (15 points)

Grades: A (90+), B (80-89), C (70-79), D (60-69), F (<60)
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class QualityIssue:
    """A specific quality issue found in the spec."""

    category: str
    severity: str  # "critical", "major", "minor"
    description: str
    location: Optional[str] = None  # Section or line reference
    suggestion: Optional[str] = None


@dataclass
class ScoreBreakdown:
    """Detailed score breakdown by category."""

    structure_score: float  # Out of 20
    boundaries_score: float  # Out of 20
    story_quality_score: float  # Out of 25
    concreteness_score: float  # Out of 20
    context_score: float  # Out of 15

    structure_details: str = ""
    boundaries_details: str = ""
    story_quality_details: str = ""
    concreteness_details: str = ""
    context_details: str = ""

    @property
    def total_score(self) -> float:
        """Calculate total score out of 100."""
        return (
            self.structure_score +
            self.boundaries_score +
            self.story_quality_score +
            self.concreteness_score +
            self.context_score
        )


@dataclass
class QualityScore:
    """Complete quality assessment of a spec."""

    score: float  # 0-100
    grade: str  # A, B, C, D, F
    breakdown: ScoreBreakdown
    issues: list[QualityIssue] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        """Format the quality score as a readable report."""
        lines = [
            f"=== Spec Quality Score: {self.score:.1f}/100 (Grade: {self.grade}) ===",
            "",
            "Score Breakdown:",
            f"  Structure:     {self.breakdown.structure_score:.1f}/20",
            f"  Boundaries:    {self.breakdown.boundaries_score:.1f}/20",
            f"  Story Quality: {self.breakdown.story_quality_score:.1f}/25",
            f"  Concreteness:  {self.breakdown.concreteness_score:.1f}/20",
            f"  Context:       {self.breakdown.context_score:.1f}/15",
        ]

        if self.issues:
            lines.append("")
            lines.append(f"Issues Found ({len(self.issues)}):")
            critical = [i for i in self.issues if i.severity == "critical"]
            major = [i for i in self.issues if i.severity == "major"]
            minor = [i for i in self.issues if i.severity == "minor"]

            for severity, issue_list in [("CRITICAL", critical), ("MAJOR", major), ("MINOR", minor)]:
                if issue_list:
                    lines.append(f"\n  {severity}:")
                    for issue in issue_list:
                        location = f" ({issue.location})" if issue.location else ""
                        lines.append(f"    - [{issue.category}]{location} {issue.description}")
                        if issue.suggestion:
                            lines.append(f"      → {issue.suggestion}")

        if self.recommendations:
            lines.append("")
            lines.append("Recommendations:")
            for rec in self.recommendations:
                lines.append(f"  • {rec}")

        return "\n".join(lines)


class RalphSpecScorer:
    """
    Ralph's spec quality scoring system.

    Evaluates specs based on the 10 Principles of Good Spec Design:
    1. Structure: Required sections and story format
    2. Boundaries: Three-tier permission system
    3. Story Quality: Verifiable criteria with examples
    4. Concreteness: No vague language or placeholders
    5. Context: Project structure and commands
    """

    # Required sections for a complete spec
    REQUIRED_SECTIONS = [
        "User Story",
        "Acceptance Criteria",
        "Technical Context",
        "Implementation Guidelines",
        "Testing Requirements"
    ]

    # Vague language patterns to detect
    VAGUE_PATTERNS = [
        r'\b(should|could|might|maybe|probably|possibly)\b',
        r'\b(as needed|if needed|when needed|where needed)\b',
        r'\b(appropriate|suitable|relevant|necessary)\b',
        r'\b(good|nice|better|best|optimal)\b',
        r'\b(etc\.?|and so on)\b',
        r'\b(some|several|many|various|multiple)\b(?!\s+(?:times|days|weeks|months|years|items|files|users))',
        r'\b(consider|try to|attempt to)\b',
        r'\b(usually|generally|typically|normally)\b',
    ]

    # Placeholder patterns to detect
    PLACEHOLDER_PATTERNS = [
        r'\[.*?\]',  # [something]
        r'<.*?>',    # <something>
        r'\{.*?\}',  # {something}
        r'TODO',
        r'FIXME',
        r'TBD',
        r'XXX',
        r'\.\.\.',   # Ellipsis
    ]

    def __init__(self, spec_path: Path):
        """
        Initialize scorer with spec file.

        Args:
            spec_path: Path to spec.md file
        """
        self.spec_path = spec_path
        self.spec_content = self._load_spec()
        self.sections = self._parse_sections()

    def _load_spec(self) -> str:
        """Load spec content from file."""
        if not self.spec_path.exists():
            raise FileNotFoundError(f"Spec file not found: {self.spec_path}")
        return self.spec_path.read_text()

    def _parse_sections(self) -> dict[str, str]:
        """Parse spec into sections based on markdown headers."""
        sections = {}
        current_section = None
        current_content = []

        for line in self.spec_content.split('\n'):
            # Check for markdown headers
            if line.startswith('#'):
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()

                # Start new section
                current_section = line.lstrip('#').strip()
                current_content = []
            elif current_section:
                current_content.append(line)

        # Save last section
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()

        return sections

    def score(self) -> QualityScore:
        """
        Score the spec and return detailed quality assessment.

        Returns:
            QualityScore with grade, breakdown, issues, and recommendations
        """
        issues: list[QualityIssue] = []

        # Score each category
        structure_score, structure_issues = self._score_structure()
        boundaries_score, boundaries_issues = self._score_boundaries()
        story_quality_score, story_issues = self._score_story_quality()
        concreteness_score, concreteness_issues = self._score_concreteness()
        context_score, context_issues = self._score_context()

        # Collect all issues
        issues.extend(structure_issues)
        issues.extend(boundaries_issues)
        issues.extend(story_issues)
        issues.extend(concreteness_issues)
        issues.extend(context_issues)

        # Create breakdown
        breakdown = ScoreBreakdown(
            structure_score=structure_score,
            boundaries_score=boundaries_score,
            story_quality_score=story_quality_score,
            concreteness_score=concreteness_score,
            context_score=context_score
        )

        total_score = breakdown.total_score
        grade = self._calculate_grade(total_score)
        recommendations = self._generate_recommendations(issues, breakdown)

        return QualityScore(
            score=total_score,
            grade=grade,
            breakdown=breakdown,
            issues=issues,
            recommendations=recommendations
        )

    def _score_structure(self) -> tuple[float, list[QualityIssue]]:
        """
        Score structure (20 points).

        Checks:
        - All required sections present (10 points)
        - User Story follows "As a... I want... So that..." format (5 points)
        - Sections are properly organized (5 points)
        """
        score = 20.0
        issues: list[QualityIssue] = []

        # Check required sections (10 points, 2 per section)
        missing_sections = []
        for section in self.REQUIRED_SECTIONS:
            if section not in self.sections:
                missing_sections.append(section)
                score -= 2.0

        if missing_sections:
            issues.append(QualityIssue(
                category="Structure",
                severity="critical",
                description=f"Missing required sections: {', '.join(missing_sections)}",
                suggestion="Add all required sections to complete the spec structure"
            ))

        # Check User Story format (5 points)
        if "User Story" in self.sections:
            story = self.sections["User Story"]
            has_as_a = "As a" in story or "As an" in story
            has_i_want = "I want" in story
            has_so_that = "So that" in story or "so that" in story

            story_score = 0.0
            if has_as_a:
                story_score += 2.0
            else:
                issues.append(QualityIssue(
                    category="Structure",
                    severity="major",
                    description="User Story missing 'As a...' persona",
                    location="User Story",
                    suggestion="Start with 'As a [persona]...' to identify the user"
                ))

            if has_i_want:
                story_score += 2.0
            else:
                issues.append(QualityIssue(
                    category="Structure",
                    severity="major",
                    description="User Story missing 'I want...' goal",
                    location="User Story",
                    suggestion="Add 'I want [action]...' to describe the desired feature"
                ))

            if has_so_that:
                story_score += 1.0
            else:
                issues.append(QualityIssue(
                    category="Structure",
                    severity="minor",
                    description="User Story missing 'So that...' benefit",
                    location="User Story",
                    suggestion="Add 'So that [benefit]...' to explain the value"
                ))

            score = score - 5.0 + story_score
        else:
            score -= 5.0

        # Check section organization (5 points)
        # Penalty for overly long sections or missing content
        for section in self.REQUIRED_SECTIONS:
            if section in self.sections:
                content = self.sections[section].strip()
                if len(content) < 50:
                    issues.append(QualityIssue(
                        category="Structure",
                        severity="minor",
                        description=f"Section '{section}' is too brief (< 50 chars)",
                        location=section,
                        suggestion="Add more detail to provide adequate guidance"
                    ))
                    score -= 1.0

        return max(0.0, score), issues

    def _score_boundaries(self) -> tuple[float, list[QualityIssue]]:
        """
        Score boundaries (20 points).

        Checks:
        - Three-tier permission system present (15 points)
        - Permissions are specific and clear (5 points)
        """
        score = 20.0
        issues: list[QualityIssue] = []

        # Look for permissions section
        permission_sections = [
            "Permissions",
            "Agent Permissions",
            "Implementation Guidelines",
            "Constraints"
        ]

        permission_content = ""
        permission_section_name = None
        for section in permission_sections:
            if section in self.sections:
                permission_content = self.sections[section]
                permission_section_name = section
                break

        if not permission_content:
            issues.append(QualityIssue(
                category="Boundaries",
                severity="critical",
                description="No permissions section found",
                suggestion="Add a section defining what the agent CAN and CANNOT do"
            ))
            return 0.0, issues

        # Check for three-tier system (15 points total, 5 per tier)
        has_must_not = any(phrase in permission_content for phrase in [
            "MUST NOT", "Must not", "Never", "NEVER", "Forbidden", "Prohibited"
        ])
        has_must = any(phrase in permission_content for phrase in [
            "MUST", "Must", "Required", "REQUIRED", "Always", "ALWAYS"
        ])
        has_may = any(phrase in permission_content for phrase in [
            "MAY", "May", "Can", "CAN", "Optional", "OPTIONAL", "Allowed"
        ])

        if not has_must_not:
            issues.append(QualityIssue(
                category="Boundaries",
                severity="critical",
                description="Missing MUST NOT (forbidden) permissions",
                location=permission_section_name,
                suggestion="Add explicit 'MUST NOT' constraints to prevent unwanted behavior"
            ))
            score -= 5.0

        if not has_must:
            issues.append(QualityIssue(
                category="Boundaries",
                severity="major",
                description="Missing MUST (required) permissions",
                location=permission_section_name,
                suggestion="Add explicit 'MUST' requirements for mandatory behavior"
            ))
            score -= 5.0

        if not has_may:
            issues.append(QualityIssue(
                category="Boundaries",
                severity="minor",
                description="Missing MAY (optional) permissions",
                location=permission_section_name,
                suggestion="Add 'MAY' permissions to clarify what is allowed but not required"
            ))
            score -= 5.0

        # Check specificity (5 points)
        # Penalty for vague permissions
        vague_count = 0
        for pattern in self.VAGUE_PATTERNS[:3]:  # Check first 3 patterns
            matches = re.findall(pattern, permission_content, re.IGNORECASE)
            vague_count += len(matches)

        if vague_count > 3:
            issues.append(QualityIssue(
                category="Boundaries",
                severity="major",
                description=f"Permissions contain vague language ({vague_count} instances)",
                location=permission_section_name,
                suggestion="Replace vague terms with specific, measurable requirements"
            ))
            score -= min(5.0, vague_count * 0.5)

        return max(0.0, score), issues

    def _score_story_quality(self) -> tuple[float, list[QualityIssue]]:
        """
        Score story quality (25 points).

        Checks:
        - Acceptance criteria are verifiable (15 points)
        - Examples provided (10 points)
        """
        score = 25.0
        issues: list[QualityIssue] = []

        if "Acceptance Criteria" not in self.sections:
            issues.append(QualityIssue(
                category="Story Quality",
                severity="critical",
                description="No Acceptance Criteria section",
                suggestion="Add Acceptance Criteria section with verifiable conditions"
            ))
            return 0.0, issues

        criteria = self.sections["Acceptance Criteria"]

        # Check for verifiable criteria (15 points)
        # Look for numbered/bulleted lists
        lines = criteria.split('\n')
        criterion_count = 0
        for line in lines:
            if re.match(r'^\s*[-*\d.]+\s+', line):
                criterion_count += 1

        if criterion_count == 0:
            issues.append(QualityIssue(
                category="Story Quality",
                severity="critical",
                description="No structured acceptance criteria found",
                location="Acceptance Criteria",
                suggestion="List criteria as numbered or bulleted items"
            ))
            score -= 10.0
        elif criterion_count < 3:
            issues.append(QualityIssue(
                category="Story Quality",
                severity="major",
                description=f"Only {criterion_count} acceptance criteria (recommend 3+)",
                location="Acceptance Criteria",
                suggestion="Add more specific criteria to ensure thorough validation"
            ))
            score -= 5.0

        # Check for action verbs (given/when/then, verify, ensure, etc.)
        action_verbs = [
            "given", "when", "then", "verify", "ensure", "confirm",
            "validate", "check", "display", "show", "return", "respond"
        ]
        has_verbs = any(verb in criteria.lower() for verb in action_verbs)

        if not has_verbs:
            issues.append(QualityIssue(
                category="Story Quality",
                severity="major",
                description="Criteria lack action verbs (given/when/then, verify, etc.)",
                location="Acceptance Criteria",
                suggestion="Use action verbs to make criteria testable"
            ))
            score -= 5.0

        # Check for examples (10 points)
        has_examples = any(section in self.sections for section in [
            "Examples",
            "Example",
            "Sample",
            "Use Cases"
        ])

        if not has_examples:
            # Check if examples are embedded in other sections
            example_keywords = ["e.g.", "for example", "such as", "example:"]
            has_embedded_examples = any(
                any(keyword in section.lower() for keyword in example_keywords)
                for section in self.sections.values()
            )

            if not has_embedded_examples:
                issues.append(QualityIssue(
                    category="Story Quality",
                    severity="major",
                    description="No examples provided",
                    suggestion="Add concrete examples to illustrate expected behavior"
                ))
                score -= 10.0
            else:
                # Partial credit for embedded examples
                score -= 5.0

        return max(0.0, score), issues

    def _score_concreteness(self) -> tuple[float, list[QualityIssue]]:
        """
        Score concreteness (20 points).

        Checks:
        - No vague language (10 points)
        - No placeholders (10 points)
        """
        score = 20.0
        issues: list[QualityIssue] = []

        # Check for vague language (10 points)
        vague_findings: dict[str, list[str]] = {}
        for pattern in self.VAGUE_PATTERNS:
            matches = re.findall(pattern, self.spec_content, re.IGNORECASE)
            if matches:
                vague_findings[pattern] = matches

        total_vague = sum(len(matches) for matches in vague_findings.values())
        if total_vague > 0:
            severity = "critical" if total_vague > 10 else "major" if total_vague > 5 else "minor"
            issues.append(QualityIssue(
                category="Concreteness",
                severity=severity,
                description=f"Found {total_vague} instances of vague language",
                suggestion="Replace vague terms with specific, measurable language"
            ))
            # Deduct up to 10 points based on count
            deduction = min(10.0, total_vague * 0.5)
            score -= deduction

        # Check for placeholders (10 points)
        placeholder_findings: dict[str, list[str]] = {}
        for pattern in self.PLACEHOLDER_PATTERNS:
            matches = re.findall(pattern, self.spec_content, re.IGNORECASE)
            if matches:
                placeholder_findings[pattern] = matches

        total_placeholders = sum(len(matches) for matches in placeholder_findings.values())
        if total_placeholders > 0:
            severity = "critical" if total_placeholders > 5 else "major"
            issues.append(QualityIssue(
                category="Concreteness",
                severity=severity,
                description=f"Found {total_placeholders} placeholders (TODO, TBD, [...], etc.)",
                suggestion="Replace all placeholders with concrete specifications"
            ))
            # Deduct up to 10 points based on count
            deduction = min(10.0, total_placeholders * 2.0)
            score -= deduction

        return max(0.0, score), issues

    def _score_context(self) -> tuple[float, list[QualityIssue]]:
        """
        Score context (15 points).

        Checks:
        - Technical context provided (10 points)
        - Commands/steps provided (5 points)
        """
        score = 15.0
        issues: list[QualityIssue] = []

        # Check for technical context (10 points)
        if "Technical Context" not in self.sections:
            issues.append(QualityIssue(
                category="Context",
                severity="critical",
                description="No Technical Context section",
                suggestion="Add Technical Context section describing relevant architecture and files"
            ))
            score -= 10.0
        else:
            context = self.sections["Technical Context"]

            # Check for file paths
            has_paths = bool(re.search(r'[/\\][\w.-]+', context))
            if not has_paths:
                issues.append(QualityIssue(
                    category="Context",
                    severity="major",
                    description="Technical Context lacks file paths",
                    location="Technical Context",
                    suggestion="Include specific file paths that will be modified"
                ))
                score -= 5.0

            # Check for technical terms/components
            if len(context) < 100:
                issues.append(QualityIssue(
                    category="Context",
                    severity="minor",
                    description="Technical Context is too brief",
                    location="Technical Context",
                    suggestion="Expand context with architecture details and dependencies"
                ))
                score -= 2.0

        # Check for commands/steps (5 points)
        has_commands = False
        command_sections = ["Commands", "Setup", "Testing", "Testing Requirements"]

        for section in command_sections:
            if section in self.sections:
                content = self.sections[section]
                # Look for code blocks or command-like patterns
                has_code_blocks = "```" in content or "`" in content
                has_command_patterns = bool(re.search(r'^\s*[$#]', content, re.MULTILINE))

                if has_code_blocks or has_command_patterns:
                    has_commands = True
                    break

        if not has_commands:
            issues.append(QualityIssue(
                category="Context",
                severity="minor",
                description="No commands or setup steps provided",
                suggestion="Include specific commands for setup, testing, or validation"
            ))
            score -= 5.0

        return max(0.0, score), issues

    def _calculate_grade(self, score: float) -> str:
        """Convert numerical score to letter grade."""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

    def _generate_recommendations(
        self,
        issues: list[QualityIssue],
        breakdown: ScoreBreakdown
    ) -> list[str]:
        """Generate actionable recommendations based on issues and scores."""
        recommendations = []

        # Priority recommendations based on critical issues
        critical = [i for i in issues if i.severity == "critical"]
        if critical:
            recommendations.append(
                f"Address {len(critical)} critical issues first - these prevent the spec from being actionable"
            )

        # Category-specific recommendations
        if breakdown.structure_score < 15:
            recommendations.append(
                "Improve spec structure: ensure all required sections are present and well-organized"
            )

        if breakdown.boundaries_score < 15:
            recommendations.append(
                "Strengthen boundaries: implement the three-tier permission system (MUST/MUST NOT/MAY)"
            )

        if breakdown.story_quality_score < 20:
            recommendations.append(
                "Enhance story quality: add more verifiable acceptance criteria and concrete examples"
            )

        if breakdown.concreteness_score < 15:
            recommendations.append(
                "Increase concreteness: eliminate vague language and replace placeholders with specifics"
            )

        if breakdown.context_score < 10:
            recommendations.append(
                "Add more context: include file paths, architecture details, and setup commands"
            )

        # Overall recommendation based on total score
        if breakdown.total_score < 60:
            recommendations.append(
                "This spec needs significant revision before implementation. Focus on the critical issues first."
            )
        elif breakdown.total_score < 80:
            recommendations.append(
                "This spec is functional but could be improved. Address major issues to reduce ambiguity."
            )
        elif breakdown.total_score < 90:
            recommendations.append(
                "This spec is good. Minor improvements would make it excellent."
            )
        else:
            recommendations.append(
                "This spec meets high quality standards. Minimal improvements needed."
            )

        return recommendations
