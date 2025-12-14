import re
from collections import Counter

try:
    from langdetect import detect
except ImportError:
    detect = None

# -----------------------------
# Unicode ranges
# -----------------------------
HINDI_RANGE = r'[\u0900-\u097F]'
ENGLISH_RANGE = r'[a-zA-Z]'
SPANISH_HINTS = {"hola", "gracias", "por", "como", "estas", "buenos", "dias"}

# -----------------------------
# Detect language per word
# -----------------------------
def detect_word_language(word: str) -> str:
    if re.search(HINDI_RANGE, word):
        return "hi"
    if re.search(ENGLISH_RANGE, word):
        if word.lower() in SPANISH_HINTS:
            return "es"
        return "en"
    return "unknown"

# -----------------------------
# Detect sentence language
# -----------------------------
def detect_language(text: str) -> dict:
    """
    Returns:
    {
        "language": "en" | "hi" | "es" | "mixed",
        "confidence": float,
        "breakdown": {"en": 3, "hi": 2}
    }
    """

    words = text.split()
    if not words:
        return {"language": "unknown", "confidence": 0.0, "breakdown": {}}

    counts = Counter()

    for word in words:
        lang = detect_word_language(word)
        if lang != "unknown":
            counts[lang] += 1

    # No rule-based detection → fallback ML
    if not counts and detect:
        try:
            lang = detect(text)
            return {
                "language": lang,
                "confidence": 0.6,
                "breakdown": {lang: len(words)}
            }
        except:
            pass

    # Mixed language detection
    if len(counts) > 1:
        return {
            "language": "mixed",
            "confidence": 0.9,
            "breakdown": dict(counts)
        }

    # Single language
    language = counts.most_common(1)[0][0]
    confidence = counts[language] / len(words)

    return {
        "language": language,
        "confidence": round(confidence, 2),
        "breakdown": dict(counts)
    }
