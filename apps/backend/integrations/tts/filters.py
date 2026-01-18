"""
Output filtering for TTS to remove code blocks, markdown, and technical content.
Adapted from Ralph-CLI's output-filter.js
"""

import re
from typing import List, Tuple


class OutputFilter:
    """Filters text content before TTS conversion."""

    # Code block patterns
    CODE_BLOCK_PATTERNS = [
        # Fenced code blocks with language
        r'```[\w]*\n.*?```',
        # Inline code
        r'`[^`]+`',
        # XML/HTML-like tags with content
        r'<[^>]+>.*?</[^>]+>',
        # Single XML/HTML tags
        r'<[^>]+/>',
        r'<[^>]+>',
    ]

    # Markdown patterns
    MARKDOWN_PATTERNS = [
        # Headers
        r'^#{1,6}\s+',
        # Bold/italic
        r'\*\*([^*]+)\*\*',
        r'__([^_]+)__',
        r'\*([^*]+)\*',
        r'_([^_]+)_',
        # Links
        r'\[([^\]]+)\]\([^)]+\)',
        # Images
        r'!\[([^\]]*)\]\([^)]+\)',
        # Lists
        r'^\s*[-*+]\s+',
        r'^\s*\d+\.\s+',
        # Blockquotes
        r'^>\s+',
        # Horizontal rules
        r'^[-*_]{3,}$',
    ]

    # File path patterns
    FILE_PATH_PATTERNS = [
        # Unix absolute paths
        r'/(?:[\w-]+/)+[\w.-]+',
        # Windows paths
        r'[A-Z]:\\(?:[\w-]+\\)+[\w.-]+',
        # Relative paths with extensions
        r'(?:\.\.?/)+[\w-]+(?:/[\w-]+)*\.[\w]+',
        # Common file extensions in any context
        r'\b[\w-]+\.(?:py|js|ts|tsx|jsx|json|md|txt|yml|yaml|toml|ini|env|sh|bash|css|scss|html|xml|sql|go|rs|java|cpp|c|h)\b',
    ]

    # URL patterns
    URL_PATTERNS = [
        r'https?://[^\s]+',
        r'www\.[^\s]+',
    ]

    # Command/terminal patterns
    COMMAND_PATTERNS = [
        # Shell commands
        r'\$\s+[\w-]+.*$',
        # npm/yarn commands
        r'(?:npm|yarn|pnpm)\s+(?:run\s+)?[\w-]+',
        # git commands
        r'git\s+[\w-]+(?:\s+[^\s]+)*',
        # python commands
        r'python3?\s+[\w/-]+\.py',
    ]

    # Technical jargon patterns (Ralph's "too nerdy" filter)
    TECHNICAL_PATTERNS = [
        # Stack traces
        r'at\s+[\w.]+\s+\([^)]+:\d+:\d+\)',
        # Import statements
        r'from\s+[\w.]+\s+import\s+',
        r'import\s+[\w.]+',
        # Function signatures
        r'def\s+\w+\([^)]*\)\s*->',
        r'function\s+\w+\([^)]*\)',
        # Variable assignments with types
        r':\s+(?:str|int|float|bool|List|Dict|Optional|Union)\[',
        # JSON-like structures
        r'\{\s*"[^"]+"\s*:\s*',
        # Environment variables
        r'\$[A-Z_]+',
        r'process\.env\.\w+',
    ]

    def __init__(
        self,
        filter_code: bool = True,
        filter_markdown: bool = True,
        filter_paths: bool = True,
        filter_urls: bool = True,
    ):
        """Initialize filter with configuration."""
        self.filter_code = filter_code
        self.filter_markdown = filter_markdown
        self.filter_paths = filter_paths
        self.filter_urls = filter_urls

        # Compile patterns for performance
        self._compiled_patterns: List[Tuple[re.Pattern, str]] = []
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns based on configuration."""
        self._compiled_patterns = []

        if self.filter_code:
            for pattern in self.CODE_BLOCK_PATTERNS:
                self._compiled_patterns.append((re.compile(pattern, re.DOTALL | re.MULTILINE), ""))
            for pattern in self.COMMAND_PATTERNS:
                self._compiled_patterns.append((re.compile(pattern, re.MULTILINE), ""))
            for pattern in self.TECHNICAL_PATTERNS:
                self._compiled_patterns.append((re.compile(pattern, re.MULTILINE), ""))

        if self.filter_markdown:
            for pattern in self.MARKDOWN_PATTERNS:
                # For markdown, we keep the content but remove the formatting
                if pattern.startswith(r'\['):  # Links
                    self._compiled_patterns.append((re.compile(pattern), r'\1'))
                elif pattern.startswith(r'\*\*') or pattern.startswith(r'__'):  # Bold
                    self._compiled_patterns.append((re.compile(pattern), r'\1'))
                elif pattern.startswith(r'\*') or pattern.startswith(r'_'):  # Italic
                    self._compiled_patterns.append((re.compile(pattern), r'\1'))
                else:
                    self._compiled_patterns.append((re.compile(pattern, re.MULTILINE), ""))

        if self.filter_paths:
            for pattern in self.FILE_PATH_PATTERNS:
                self._compiled_patterns.append((re.compile(pattern), ""))

        if self.filter_urls:
            for pattern in self.URL_PATTERNS:
                self._compiled_patterns.append((re.compile(pattern), ""))

    def filter(self, text: str) -> str:
        """
        Filter text by removing code blocks, markdown, file paths, etc.

        Args:
            text: Raw text to filter

        Returns:
            Filtered text suitable for TTS
        """
        if not text:
            return ""

        filtered = text

        # Apply all patterns
        for pattern, replacement in self._compiled_patterns:
            filtered = pattern.sub(replacement, filtered)

        # Clean up whitespace
        filtered = self._clean_whitespace(filtered)

        # Remove common filler words that don't add value to TTS
        filtered = self._remove_filler(filtered)

        return filtered.strip()

    def _clean_whitespace(self, text: str) -> str:
        """Clean up excessive whitespace."""
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        # Remove spaces before punctuation
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        # Ensure space after punctuation
        text = re.sub(r'([.,!?;:])(\w)', r'\1 \2', text)
        return text

    def _remove_filler(self, text: str) -> str:
        """Remove common filler phrases that don't add value to TTS."""
        filler_patterns = [
            r'\bOk,?\s+',
            r'\bOkay,?\s+',
            r'\bAlright,?\s+',
            r'\bSure,?\s+',
            r'\bGot it,?\s+',
            r'\bI see,?\s+',
            r'\bUnderstood,?\s+',
        ]

        for pattern in filler_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        return text

    def truncate(self, text: str, max_length: int) -> str:
        """
        Truncate text to max length, preserving sentence boundaries.

        Args:
            text: Text to truncate
            max_length: Maximum character length

        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text

        # Try to break at sentence boundary
        truncated = text[:max_length]
        last_period = truncated.rfind('.')
        last_exclamation = truncated.rfind('!')
        last_question = truncated.rfind('?')

        last_sentence = max(last_period, last_exclamation, last_question)

        if last_sentence > max_length * 0.7:  # At least 70% of desired length
            return truncated[:last_sentence + 1]

        # Otherwise, break at word boundary
        last_space = truncated.rfind(' ')
        if last_space > 0:
            return truncated[:last_space] + "..."

        return truncated + "..."


def create_filter(
    filter_code: bool = True,
    filter_markdown: bool = True,
    filter_paths: bool = True,
    filter_urls: bool = True,
) -> OutputFilter:
    """Factory function to create an OutputFilter instance."""
    return OutputFilter(
        filter_code=filter_code,
        filter_markdown=filter_markdown,
        filter_paths=filter_paths,
        filter_urls=filter_urls,
    )
