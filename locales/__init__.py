# Localization module

import os
from locales import ru, en

# Available languages
LANGUAGES = {
    'ru': ru.MESSAGES,
    'en': en.MESSAGES,
}

# Default language
DEFAULT_LANGUAGE = 'ru'

# Current language
_current_language = DEFAULT_LANGUAGE


def set_language(lang: str) -> bool:
    """Sets the current language. Returns True on success."""
    global _current_language
    if lang in LANGUAGES:
        _current_language = lang
        return True
    return False


def get_language() -> str:
    """Returns the current language."""
    return _current_language


def get_available_languages() -> list:
    """Returns a list of available languages."""
    return list(LANGUAGES.keys())


def t(key: str, **kwargs) -> str:
    """
    Returns a localized string by key.
    Supports formatting via kwargs.
    """
    messages = LANGUAGES.get(_current_language, LANGUAGES[DEFAULT_LANGUAGE])
    text = messages.get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except KeyError:
            return text
    return text
