from datetime import datetime
import json
import os
from typing import Dict, List, Optional

from app.utils.constants import HISTORY_FILE_PATH, DEFAULT_EXPORTS_DIR


class HistoryManager:
    """
    Manages persistent conversion and translation history for dashboard display.
    """

    @classmethod
    def load_history(cls) -> List[Dict]:
        os.makedirs(DEFAULT_EXPORTS_DIR, exist_ok=True)
        if not os.path.exists(HISTORY_FILE_PATH):
            cls.save_history([])
            return []

        try:
            with open(HISTORY_FILE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception:
            return []

    @classmethod
    def save_history(cls, items: List[Dict]) -> None:
        os.makedirs(DEFAULT_EXPORTS_DIR, exist_ok=True)
        try:
            with open(HISTORY_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(items, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[HistoryManager] Save error: {e}")

    @classmethod
    def add_entry(
        cls,
        conv_type: str,
        title: str,
        format_tag: str,
        file_path: str = "",
        source_text: str = "",
        translated_text: str = "",
        source_lang: str = "",
        target_lang: str = "",
    ) -> Dict:
        now = datetime.now()
        entry = {
            "id": f"item-{int(now.timestamp())}",
            "type": conv_type,
            "title": title[:50] if title else "Untitled Conversion",
            "source_text": source_text if source_text else "",
            "translated_text": translated_text if translated_text else "",
            "source_lang": source_lang,
            "target_lang": target_lang,
            "date": now.strftime("%d %b %Y"),
            "time": now.strftime("%I:%M %p"),
            "format": format_tag.upper(),
            "path": file_path,
        }
        items = cls.load_history()
        items.insert(0, entry)
        items = items[:50]
        cls.save_history(items)
        return entry

    @classmethod
    def get_recent(cls, count: int = 4) -> List[Dict]:
        items = cls.load_history()
        return items[:count]

    @classmethod
    def clear_all(cls) -> None:
        cls.save_history([])
