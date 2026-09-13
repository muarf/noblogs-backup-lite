"""i18n.py — Simple translation mechanism.

Uses JSON files for localization to avoid requiring gettext/msgfmt dependencies.
"""
import json
import os
from pathlib import Path

LOCALES_DIR = Path(__file__).resolve().parent / "locales"

_translations = {}
_current_lang = "fr"  # Default

def init_i18n() -> None:
    global _translations, _current_lang

    # Detect language from LANG environment variable
    lang_env = os.environ.get("LANG", "")
    if lang_env.startswith("en"):
        _current_lang = "en"
    elif lang_env.startswith("it"):
        _current_lang = "it"
    else:
        _current_lang = "fr"

    if _current_lang == "fr":
        return # Default language, strings in the source are in French

    locale_file = LOCALES_DIR / f"{_current_lang}.json"
    if locale_file.exists():
        try:
            with open(locale_file, "r", encoding="utf-8") as f:
                _translations = json.load(f)
        except Exception as e:
            pass # Fallback to French if error

def t(message: str) -> str:
    """Translate a message to the current language."""
    if _current_lang == "fr":
        return message
    return _translations.get(message, message)

init_i18n()
