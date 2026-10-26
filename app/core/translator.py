import json
import logging
import urllib.parse
import urllib.request
from typing import Optional

logger = logging.getLogger(__name__)


class TranslationError(Exception):
    """Raised when translation request fails."""
    pass


class TranslatorEngine:
    """
    Multilingual translation engine supporting English, Hindi, and Gujarati.
    """

    SUPPORTED_LANGUAGES = {"en", "hi", "gu"}

    def __init__(self, timeout: float = 8.0):
        self.timeout = timeout
        self._cache: dict[tuple[str, str, str], str] = {}

    def translate(self, text: str, source_lang: str = "auto", target_lang: str = "hi") -> str:
        """
        Translate text from source_lang to target_lang.
        If source_lang == target_lang, returns original text.
        """
        clean_text = text.strip()
        if not clean_text:
            return ""

        # Normalize language codes
        s_lang = (source_lang or "auto").strip().lower()
        t_lang = (target_lang or "hi").strip().lower()

        # Map regional variants e.g. 'en-IN' or 'en-US' -> 'en'
        if "-" in s_lang:
            s_lang = s_lang.split("-")[0]
        if "-" in t_lang:
            t_lang = t_lang.split("-")[0]

        if s_lang == t_lang and s_lang != "auto":
            return clean_text

        cache_key = (clean_text, s_lang, t_lang)
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Try Primary GTX endpoint
        result = None
        try:
            result = self._translate_gtx(clean_text, s_lang, t_lang)
        except Exception as err:
            logger.warning(f"GTX translation failed: {err}. Attempting fallback endpoint...")
            try:
                result = self._translate_dict(clean_text, s_lang, t_lang)
            except Exception as fallback_err:
                logger.error(f"Fallback translation also failed: {fallback_err}")
                raise TranslationError(f"Translation failed: {fallback_err}") from fallback_err

        if result:
            self._cache[cache_key] = result
            return result

        return clean_text

    def _translate_gtx(self, text: str, source: str, target: str) -> str:
        """Query translate.googleapis.com endpoint."""
        query = urllib.parse.quote(text)
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={source}&tl={target}&dt=t&q={query}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Charset": "utf-8",
            },
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
            if data and isinstance(data, list) and data[0]:
                translated_segments = [seg[0] for seg in data[0] if seg and seg[0]]
                return "".join(translated_segments)
        raise TranslationError("Invalid response structure from GTX translation service.")

    def _translate_dict(self, text: str, source: str, target: str) -> str:
        """Query clients5.google.com dictionary endpoint."""
        query = urllib.parse.quote(text)
        url = f"https://clients5.google.com/translate_a/t?client=dict-chrome-ex&sl={source}&tl={target}&q={query}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept-Charset": "utf-8",
            },
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
            if isinstance(data, list) and data:
                return data[0]
            if isinstance(data, str):
                return data
        raise TranslationError("Invalid response structure from fallback translation service.")

