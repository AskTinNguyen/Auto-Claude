"""
AI-powered TTS summarization using Ollama.

Ported from Ralph CLI's summarize-for-tts.mjs for context-aware summarization.
"""

import os
import re
import requests
from typing import Optional, Tuple
from .tts_modes import ModeConfig, detect_optimal_mode, get_mode_config


def detect_language(text: str) -> str:
    """
    Detect if text is Vietnamese or English.
    Simple heuristic: check for Vietnamese-specific characters.
    """
    # Vietnamese-specific characters
    vietnamese_chars = re.compile(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', re.IGNORECASE)

    if vietnamese_chars.search(text):
        return "vi"
    return "en"


def remove_repetitive_sentences(text: str) -> str:
    """
    Remove repetitive sentences that say the same thing differently.
    E.g., "Modified the file. Updated the file. Changed the file." → "Modified the file."
    """
    sentences = re.split(r'\.\s+', text)

    if len(sentences) <= 2:
        return text  # Not enough sentences to have repetition

    # If text is very short (< 50 chars), don't risk removing content
    # Lowered threshold from 100 to 50 to allow removal in test cases
    if len(text) < 50:
        return text

    unique_sentences = []
    seen_concepts = set()

    for sentence in sentences:
        # Extract key words (nouns/verbs) from sentence
        words = re.sub(r'[^\w\s]', '', sentence.lower()).split()
        words = [w for w in words if len(w) > 3]  # Only meaningful words

        # Create a concept signature (sorted unique words)
        concept_sig = '-'.join(sorted(set(words)))

        # Check if we've seen a very similar sentence
        is_duplicate = False
        for seen_sig in seen_concepts:
            overlap = calculate_overlap(concept_sig, seen_sig)
            if overlap > 0.25:  # More than 25% word overlap = duplicate concept (Jaccard similarity)
                is_duplicate = True
                break

        if not is_duplicate:
            unique_sentences.append(sentence)
            seen_concepts.add(concept_sig)

    return '. '.join(unique_sentences)


def calculate_overlap(sig1: str, sig2: str) -> float:
    """Calculate word overlap between two concept signatures."""
    words1 = set(sig1.split('-'))
    words2 = set(sig2.split('-'))

    intersection = len(words1 & words2)
    union = len(words1 | words2)

    return intersection / union if union > 0 else 0


def clean_summary(text: str) -> str:
    """
    Clean up the generated summary.
    Enhanced to catch symbols, technical terms, and repetitive patterns.
    """
    result = text.strip()

    # Remove code blocks
    result = re.sub(r'```[\s\S]*?```', '', result)
    result = re.sub(r'`([^`]+)`', r'\1', result)

    # Remove markdown formatting
    result = re.sub(r'^#{1,6}\s+', '', result, flags=re.MULTILINE)
    result = re.sub(r'\*\*([^*]+)\*\*', r'\1', result)
    result = re.sub(r'\*([^*]+)\*', r'\1', result)
    result = re.sub(r'__([^_]+)__', r'\1', result)
    result = re.sub(r'_([^_]+)_', r'\1', result)

    # Remove bullet points
    result = re.sub(r'^[\s]*[-*+]\s+', '', result, flags=re.MULTILINE)
    result = re.sub(r'^[\s]*\d+\.\s+', '', result, flags=re.MULTILINE)

    # Remove file paths and extensions (aggressive)
    # Matches: path/to/file.ext, .agents/ralph/script.sh, etc.
    result = re.sub(
        r'[\w\-./]+\.(sh|js|mjs|ts|tsx|jsx|json|md|txt|py|yaml|yml|css|html|xml|sql|rb|go|rs|java|c|cpp|h)',
        '',
        result,
        flags=re.IGNORECASE
    )

    # Remove path-like patterns (e.g., .agents/ralph/lib/, src/components/)
    result = re.sub(r'\.[\w\-/]+/', '', result)
    result = re.sub(r'[\w\-]+/[\w\-]+/', '', result)  # foo/bar/ patterns

    # Remove URLs
    result = re.sub(r'https?://[^\s]+', '', result)

    # Remove XML/HTML-like tags
    result = re.sub(r'<[^>]+>', '', result)

    # AGGRESSIVE SYMBOL REMOVAL
    # Remove ALL problematic symbols that TTS reads literally
    result = re.sub(r'[~\/\\|<>{}[\]@#$%^&*`+=_]', '', result)

    # Replace "dot" when it appears as word (from file extensions being read)
    result = re.sub(r'\bdot\b', '', result, flags=re.IGNORECASE)
    result = re.sub(r'\bslash\b', '', result, flags=re.IGNORECASE)
    result = re.sub(r'\btilda\b', '', result, flags=re.IGNORECASE)
    result = re.sub(r'\btilde\b', '', result, flags=re.IGNORECASE)

    # Remove technical abbreviations that slip through
    result = re.sub(r'\b(API|CLI|TTS|JSON|HTML|CSS|URL|HTTP|HTTPS|SSH|FTP)\b', '', result)

    # Remove common technical words when followed by generic terms
    result = re.sub(r'\bthe (file|script|function|config|directory|folder|repository|repo)\b', 'it', result, flags=re.IGNORECASE)
    result = re.sub(r'\bin the (file|script|function|config|directory|folder)\b', '', result, flags=re.IGNORECASE)

    # Remove common status emojis that TTS reads literally
    # This includes checkmarks, crosses, warnings, etc.
    emoji_pattern = re.compile(
        r'[\u2705\u274C\u26A0\u2713\u2714\u2611\u274E\u2B1C\u2B1B'
        r'\U0001F534\U0001F7E2\U0001F7E1\u2B50\U0001F389\U0001F44D\U0001F44E'
        r'\U0001F680\U0001F4A1\U0001F4DD\U0001F527\U0001F41B]'
    )
    result = emoji_pattern.sub('', result)

    # Fallback: remove any remaining emoji characters
    result = re.sub(r'[\U0001F300-\U0001F9FF]|[\u2600-\u26FF]|[\u2700-\u27BF]', '', result)

    # Fix spacing around punctuation
    result = re.sub(r'\s+([,.!?;:])', r'\1', result)  # Remove space before punctuation
    result = re.sub(r'([,.!?;:])\s*', r'\1 ', result)  # Ensure space after punctuation

    # Remove extra punctuation (multiple periods, etc.)
    result = re.sub(r'\.{2,}', '.', result)
    result = re.sub(r',{2,}', ',', result)

    # Remove repetitive sentence patterns
    result = remove_repetitive_sentences(result)

    # Normalize whitespace
    result = re.sub(r'\s+', ' ', result)

    return result.strip()


def truncate_for_tts(text: str, max_length: int = 150) -> str:
    """
    Truncate text for TTS at a clean sentence boundary.
    Ensures summary ends with proper punctuation and doesn't cut mid-word.
    """
    if not text or len(text) <= max_length:
        # Ensure it ends with punctuation
        if text and not re.search(r'[.!?]$', text):
            return text + "."
        return text

    # Try to truncate at sentence boundary (., !, ?)
    truncated = text[:max_length]

    # Look for last sentence ending
    last_period = truncated.rfind('. ')
    last_exclaim = truncated.rfind('! ')
    last_question = truncated.rfind('? ')

    last_sentence_end = max(last_period, last_exclaim, last_question)

    if last_sentence_end > max_length * 0.5:
        # Found a sentence boundary in the second half - use it
        return truncated[:last_sentence_end + 1]

    # No good sentence boundary - truncate at last word
    last_space = truncated.rfind(' ')
    if last_space > max_length * 0.7:
        return truncated[:last_space] + "."

    # Fallback: just truncate and add period
    return truncated + "."


def context_aware_summarize(
    response: str,
    user_question: Optional[str],
    mode_config: ModeConfig,
    ollama_url: Optional[str] = None,
    ollama_model: Optional[str] = None
) -> str:
    """
    Context-aware summarization using Ollama.
    Considers the user's original question when summarizing.

    Args:
        response: The filtered response text
        user_question: The user's original question (optional)
        mode_config: Mode configuration with maxChars, maxTokens, promptWords, promptStyle
        ollama_url: Ollama API URL (defaults to env or localhost)
        ollama_model: Ollama model name (defaults to env or qwen2.5:1.5b)

    Returns:
        Summarized text
    """
    ollama_url = ollama_url or os.getenv("OLLAMA_URL", "http://localhost:11434")
    ollama_model = ollama_model or os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")
    timeout = 15 if mode_config.max_tokens > 200 else 10

    # Detect language of the response for proper TTS routing
    detected_lang = detect_language(response)
    is_vietnamese = detected_lang == "vi"

    # Language-specific instructions
    lang_instruction = (
        "- CRITICAL: Summarize in Vietnamese (tiếng Việt) - preserve the original language"
        if is_vietnamese
        else "- Use ONLY plain conversational English - no technical terms"
    )

    # Build context-aware prompt based on mode
    if user_question and user_question.strip():
        prompt = f"""You are a voice assistant. The user asked: "{user_question.strip()[:200]}"

The assistant's response:
{response[:3000]}

Your task: Create a clear spoken summary answering what the user asked.

FORMAT ({mode_config.prompt_style}, {mode_config.prompt_words}):
{lang_instruction}
- Use natural conversational speech
- For lists: "First, [action]. Second, [action]. Third, [action]."
- State ONLY the main point once - do not repeat or rephrase

STRICT RULES - NEVER include:
- File names or paths (voice-config.json, .agents/ralph, src/components)
- File extensions (.sh, .js, .py, .md, .json, .tsx)
- Technical references ("the file", "the script", "the function", "the config")
- Symbols: ~ / \\ | @ # $ % ^ & * ` < > {{ }} [ ] = + _
- Numbers with units unless essential (150ms, 10s, 200MB)
- Abbreviations (TTS, API, CLI) - say full words
- Code syntax or technical jargon

WHAT TO SAY:
- Actions completed: "Added feature X", "Fixed the login bug"
- Key outcomes: "Users can now...", "The system will..."
- Next steps: "You should...", "Consider..."
- Answer directly - what did we accomplish?

BAD: "Updated the voice config dot json file in dot agents slash ralph"
GOOD: "Changed the voice settings to use a quieter tone"

BAD: "One, modified the file. Two, tested the file. Three, the file works now."
GOOD: "First, adjusted the settings. Second, verified it works. Done."

Spoken summary (natural speech only, no repetition):"""
    else:
        # Fallback to standard summarization without context
        prompt = f"""You are a voice assistant converting this response to natural speech:

{response[:3000]}

Create a spoken summary ({mode_config.prompt_style}, {mode_config.prompt_words}).

STRICT RULES - NEVER include:
- File names, paths, or extensions
- Symbols: ~ / \\ | @ # $ % ^ & * ` < > {{ }} [ ] = + _
{lang_instruction}
- Technical references or abbreviations
- Repetitive phrases

FORMAT:
- Natural conversational speech
- For lists: "First, [item]. Second, [item]. Third, [item]."
- State each point once only

Spoken summary (no repetition):"""

    try:
        # Call Ollama API
        response_data = requests.post(
            f"{ollama_url}/api/generate",
            json={
                "model": ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": mode_config.max_tokens,
                    "temperature": 0.2,        # Lower = more focused, less repetition
                    "top_p": 0.85,             # Slightly more deterministic
                    "top_k": 40,               # Limit vocabulary diversity
                    "repeat_penalty": 1.3,     # Strongly penalize repetition
                    "frequency_penalty": 0.5,  # Reduce word reuse
                    "presence_penalty": 0.3,   # Encourage variety in concepts
                    "stop": ["\n\n", "Summary:", "Note:", "Important:"],  # Stop at meta-text
                },
            },
            timeout=timeout
        )

        response_data.raise_for_status()
        data = response_data.json()
        return clean_summary(data.get("response", ""))

    except Exception as e:
        # Fallback to regex-based cleanup
        return fallback_summarize(response, mode_config)


def fallback_summarize(text: str, mode_config: ModeConfig) -> str:
    """
    Fallback summarization when LLM is unavailable.

    Args:
        text: Text to summarize
        mode_config: Mode configuration with maxChars

    Returns:
        Cleaned and truncated text
    """
    result = clean_summary(text)
    max_length = mode_config.max_chars

    # If still too long, truncate at sentence boundary
    if len(result) > max_length:
        truncated = result[:max_length]
        last_period = truncated.rfind('. ')
        if last_period > max_length * 0.5:
            return truncated[:last_period + 1]
        return truncated[:truncated.rfind(' ')] + "..."

    return result


def summarize_for_tts(
    response_text: str,
    user_question: Optional[str] = None,
    mode: str = "adaptive",
    fallback_mode: str = "short"
) -> Tuple[str, str]:
    """
    Main entry point for TTS summarization.

    Args:
        response_text: The assistant's response text
        user_question: The user's original question (optional)
        mode: Summarization mode ("adaptive", "short", "medium", "full")
        fallback_mode: Fallback mode if adaptive detection fails

    Returns:
        Tuple of (summarized_text, mode_used)
    """
    if not response_text or not response_text.strip():
        return "", "short"

    # Determine mode configuration
    if mode == "adaptive":
        detection = detect_optimal_mode(response_text)
        mode_config = get_mode_config(detection.mode)
        mode_used = detection.mode
    else:
        mode_config = get_mode_config(mode)
        mode_used = mode

    # Context-aware summarization with Ollama
    summary = context_aware_summarize(response_text, user_question, mode_config)

    if summary and summary.strip():
        # Clean up the summary - remove quotes if present
        cleaned = summary.strip()

        # Remove wrapping quotes (some LLMs add them)
        if (cleaned.startswith('"') and cleaned.endswith('"')) or \
           (cleaned.startswith("'") and cleaned.endswith("'")):
            cleaned = cleaned[1:-1]

        # CRITICAL: Enforce max length for TTS (prevents jibberish from overly long text)
        # Truncate at sentence boundary based on mode configuration
        cleaned = truncate_for_tts(cleaned.strip(), mode_config.max_chars)

        return cleaned, mode_used

    return "", mode_used
