from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class Language:
    code: str             # Short identifier (e.g., 'en', 'hi', 'gu')
    display_name: str     # UI label with native script
    stt_code: str         # SpeechRecognition language tag (BCP-47)
    tts_code: str         # gTTS language code
    trans_code: str       # Translation language code
    flag: str             # Country emoji flag


SUPPORTED_LANGUAGES: Dict[str, Language] = {
    "en": Language(
        code="en",
        display_name="English (India)",
        stt_code="en-IN",
        tts_code="en",
        trans_code="en",
        flag="🇮🇳",
    ),
    "hi": Language(
        code="hi",
        display_name="Hindi (हिन्दी)",
        stt_code="hi-IN",
        tts_code="hi",
        trans_code="hi",
        flag="🇮🇳",
    ),
    "gu": Language(
        code="gu",
        display_name="Gujarati (ગુજરાતી)",
        stt_code="gu-IN",
        tts_code="gu",
        trans_code="gu",
        flag="🇮🇳",
    ),
}

DEFAULT_LANGUAGE = "en"
DEFAULT_TARGET_LANGUAGE = "hi"

# Clean list of main languages for dropdowns
PRIMARY_LANGUAGE_KEYS = ["en", "hi", "gu"]


def get_language(code: str) -> Language:
    """Retrieve language configuration by code or return default."""
    if not code:
        return SUPPORTED_LANGUAGES[DEFAULT_LANGUAGE]
    normalized = code.strip().lower()
    if normalized in SUPPORTED_LANGUAGES:
        return SUPPORTED_LANGUAGES[normalized]
    # Check if short code matches (e.g. 'en')
    for lang in SUPPORTED_LANGUAGES.values():
        if lang.code == normalized or lang.trans_code == normalized:
            return lang
    return SUPPORTED_LANGUAGES[DEFAULT_LANGUAGE]


def get_language_by_display_name(name: str) -> Language:
    """Find language by display name (with or without flag)."""
    cleaned = name.strip()
    for lang in SUPPORTED_LANGUAGES.values():
        formatted = f"{lang.flag} {lang.display_name}"
        if cleaned == formatted or cleaned == lang.display_name:
            return lang
        if lang.display_name.lower() in cleaned.lower():
            return lang
    return SUPPORTED_LANGUAGES[DEFAULT_LANGUAGE]


def get_dropdown_options() -> List[str]:
    """Return formatted strings with flags for UI dropdowns."""
    return [f"{SUPPORTED_LANGUAGES[k].flag}  {SUPPORTED_LANGUAGES[k].display_name}" for k in PRIMARY_LANGUAGE_KEYS]
