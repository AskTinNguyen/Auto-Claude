"""
TTS mode configurations and adaptive complexity detection.

Ported from Ralph CLI's tts-modes.mjs for language-agnostic complexity scoring.
"""

import re
from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass
class ModeConfig:
    """Configuration for a TTS summarization mode."""
    max_chars: int
    max_tokens: int
    prompt_words: str
    prompt_style: str


# Mode configurations matching Ralph CLI
MODES = {
    "short": ModeConfig(
        max_chars=150,
        max_tokens=150,
        prompt_words="under 30 words",
        prompt_style="1-2 sentences"
    ),
    "medium": ModeConfig(
        max_chars=500,
        max_tokens=250,
        prompt_words="under 60 words",
        prompt_style="bulleted list using numbered words (One, Two, Three)"
    ),
    "full": ModeConfig(
        max_chars=700,
        max_tokens=300,
        prompt_words="under 90 words",
        prompt_style="comprehensive bulleted list with numbered items"
    ),
}


# Score thresholds for mode detection (0-100 scale)
MODE_THRESHOLDS = {
    "short": (0, 25),    # Simple, brief responses
    "medium": (26, 55),  # Multi-paragraph explanations
    "full": (56, 100),   # Complex, structured content
}


# Pre-compiled regex patterns for performance
PATTERNS = {
    "paragraphs": re.compile(r'\n\n+'),
    "sentences": re.compile(r'[.!?。！？]+'),
    "headings": re.compile(r'^#{1,6}\s', re.MULTILINE),
    "code_blocks": re.compile(r'```'),
    "table_rows": re.compile(r'^\s*\|.+\|', re.MULTILINE),
    "bullets": re.compile(r'^[\s]*[-*+]\s+', re.MULTILINE),
    "numbered_items": re.compile(r'^[\s]*\d+\.\s+', re.MULTILINE),
    "user_stories": re.compile(r'US-\d+'),
    "weeks_phases": re.compile(r'(?:Week|Tuần|Phase|Giai đoạn)\s+\d+', re.IGNORECASE),
}


@dataclass
class TextMetrics:
    """Universal structural metrics for text analysis."""
    char_count: int = 0
    word_count: int = 0
    paragraph_count: int = 0
    sentence_count: int = 0
    avg_sentence_length: float = 0.0
    heading_count: int = 0
    code_block_count: int = 0
    table_row_count: int = 0
    list_item_count: int = 0
    nesting_depth: int = 0


def count_words(text: str) -> int:
    """Count words (whitespace-delimited tokens)."""
    tokens = text.strip().split()
    return len([t for t in tokens if t])


def count_paragraphs(text: str) -> int:
    """Count paragraphs (double newline separated blocks)."""
    matches = PATTERNS["paragraphs"].findall(text)
    return len(matches) + 1


def count_sentences(text: str) -> int:
    """Count sentences using universal terminators (. ! ? 。！？)."""
    matches = PATTERNS["sentences"].findall(text)
    return len(matches)


def count_headings(text: str) -> int:
    """Count markdown headings (# to ######)."""
    matches = PATTERNS["headings"].findall(text)
    return len(matches)


def count_code_blocks(text: str) -> int:
    """Count fenced code blocks (``` pairs)."""
    matches = PATTERNS["code_blocks"].findall(text)
    return len(matches) // 2


def count_table_rows(text: str) -> int:
    """Count markdown table rows (lines with | delimiters)."""
    matches = PATTERNS["table_rows"].findall(text)
    return len(matches)


def count_list_items(text: str) -> int:
    """Count list items (bullets and numbered)."""
    bullets = PATTERNS["bullets"].findall(text)
    numbered = PATTERNS["numbered_items"].findall(text)
    return len(bullets) + len(numbered)


def calculate_nesting_depth(text: str) -> int:
    """
    Calculate maximum nesting depth based on indentation.
    Returns depth in levels (2 spaces or 1 tab = 1 level).
    """
    lines = text.split('\n')
    max_depth = 0

    for line in lines:
        match = re.match(r'^[\s\t]+', line)
        if match:
            # Convert to consistent depth: 2 spaces or 1 tab = 1 level
            indent = match.group(0).replace('\t', '  ')
            depth = len(indent) // 2
            max_depth = max(max_depth, depth)

    return max_depth


def analyze_metrics(text: str) -> TextMetrics:
    """
    Analyze text and extract universal structural metrics.
    Works across all languages and content types.
    """
    if not text or not isinstance(text, str):
        return TextMetrics()

    char_count = len(text)
    word_count = count_words(text)
    paragraph_count = count_paragraphs(text)
    sentence_count = count_sentences(text)
    avg_sentence_length = char_count / sentence_count if sentence_count > 0 else 0
    heading_count = count_headings(text)
    code_block_count = count_code_blocks(text)
    table_row_count = count_table_rows(text)
    list_item_count = count_list_items(text)
    nesting_depth = calculate_nesting_depth(text)

    return TextMetrics(
        char_count=char_count,
        word_count=word_count,
        paragraph_count=paragraph_count,
        sentence_count=sentence_count,
        avg_sentence_length=avg_sentence_length,
        heading_count=heading_count,
        code_block_count=code_block_count,
        table_row_count=table_row_count,
        list_item_count=list_item_count,
        nesting_depth=nesting_depth
    )


def calculate_complexity_score(metrics: TextMetrics) -> int:
    """
    Calculate complexity score from metrics (0-100).
    Higher score = more complex content.
    """
    score = 0

    # Base score from length (0-30 points)
    # 100 chars = 1 point, max 30 points at 3000 chars
    score += min(30, metrics.char_count / 100)

    # Structure complexity (0-25 points)
    # Paragraphs: 2 points each, max 10
    score += min(10, metrics.paragraph_count * 2)
    # Headings: 3 points each, max 10
    score += min(10, metrics.heading_count * 3)
    # Nesting depth: 2 points per level, max 5
    score += min(5, metrics.nesting_depth * 2)

    # List/table density (0-25 points)
    # List items: 2 points each, max 15
    score += min(15, metrics.list_item_count * 2)
    # Table rows: 1.5 points each, max 10
    score += min(10, int(metrics.table_row_count * 1.5))

    # Code density (0-15 points)
    # Code blocks: 5 points each, max 15
    score += min(15, metrics.code_block_count * 5)

    # Sentence complexity (0-10 points)
    # Average sentence length / 10, max 10 points
    if metrics.sentence_count > 0:
        score += min(10, metrics.avg_sentence_length / 10)

    return min(100, round(score))


def calculate_pattern_bonus(text: str) -> int:
    """
    Calculate pattern-based bonus points for backward compatibility.
    PRD patterns (US-XXX, Week/Phase) add bonus to existing score.
    """
    bonus = 0

    # User stories: 3+ = +20 bonus
    user_stories = PATTERNS["user_stories"].findall(text)
    if len(user_stories) >= 3:
        bonus += 20

    # Weeks/Phases: 2+ = +15 bonus
    weeks_phases = PATTERNS["weeks_phases"].findall(text)
    if len(weeks_phases) >= 2:
        bonus += 15

    return bonus


@dataclass
class ModeDetectionResult:
    """Result of adaptive mode detection."""
    mode: str
    reason: str
    score: int
    metrics: TextMetrics


def detect_optimal_mode(response_text: str) -> ModeDetectionResult:
    """
    Detect optimal summarization mode based on response complexity.
    Uses universal structural metrics that work across all languages and topics.
    """
    # Handle invalid input
    if not response_text or not isinstance(response_text, str):
        return ModeDetectionResult(
            mode="short",
            reason="Empty or invalid input",
            score=0,
            metrics=TextMetrics()
        )

    # Early exit for very short responses (optimization)
    if len(response_text) < 100:
        return ModeDetectionResult(
            mode="short",
            reason="Brief response (< 100 chars)",
            score=len(response_text) // 10,
            metrics=TextMetrics(char_count=len(response_text))
        )

    # Analyze metrics
    metrics = analyze_metrics(response_text)

    # Calculate base complexity score
    base_score = calculate_complexity_score(metrics)

    # Add pattern bonus for backward compatibility
    pattern_bonus = calculate_pattern_bonus(response_text)

    # Final score (capped at 100)
    final_score = min(100, base_score + pattern_bonus)

    # Determine mode based on score thresholds
    if final_score >= MODE_THRESHOLDS["full"][0]:
        mode = "full"
        reason = f"High complexity (score: {final_score})"
    elif final_score >= MODE_THRESHOLDS["medium"][0]:
        mode = "medium"
        reason = f"Medium complexity (score: {final_score})"
    else:
        mode = "short"
        reason = f"Low complexity (score: {final_score})"

    # Add detail about what contributed to score
    details = []
    if metrics.paragraph_count > 3:
        details.append(f"{metrics.paragraph_count} paragraphs")
    if metrics.heading_count > 0:
        details.append(f"{metrics.heading_count} headings")
    if metrics.list_item_count > 5:
        details.append(f"{metrics.list_item_count} list items")
    if metrics.code_block_count > 0:
        details.append(f"{metrics.code_block_count} code blocks")
    if metrics.table_row_count > 0:
        details.append(f"{metrics.table_row_count} table rows")
    if pattern_bonus > 0:
        details.append(f"+{pattern_bonus} pattern bonus")

    if details:
        reason += f" - {', '.join(details)}"

    return ModeDetectionResult(
        mode=mode,
        reason=reason,
        score=final_score,
        metrics=metrics
    )


def get_mode_config(mode_name: str) -> ModeConfig:
    """Get mode configuration by name."""
    return MODES.get(mode_name, MODES["short"])
