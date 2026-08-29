from typing import Literal

LanguageCode = Literal["en", "hi"]
SUPPORTED_LANGUAGES = {"en", "hi"}


def normalize_language(value: str | None) -> LanguageCode:
    """Normalize supported demo languages; unknown values safely use English."""
    return "hi" if (value or "").strip().casefold() == "hi" else "en"


def localized_fields(localizations: dict | None, language: str | None, defaults: dict[str, str]) -> tuple[dict[str, str], LanguageCode, bool]:
    """Select localized fields while retaining English defaults and fallback state."""
    requested = normalize_language(language)
    records = localizations if isinstance(localizations, dict) else {}
    selected_record = records.get(requested, {}) if isinstance(records.get(requested, {}), dict) else {}
    english_record = records.get("en", {}) if isinstance(records.get("en", {}), dict) else {}
    selected: dict[str, str] = {}
    fully_localized = requested == "en"
    for field, default in defaults.items():
        value = selected_record.get(field) or (english_record.get(field) if requested == "en" else None) or default
        selected[field] = str(value)
        if requested == "hi" and field not in selected_record:
            fully_localized = False
    return selected, requested, fully_localized
