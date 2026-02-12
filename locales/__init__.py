# Модуль локализации

import os
from locales import ru, en

# Доступные языки
LANGUAGES = {
    'ru': ru.MESSAGES,
    'en': en.MESSAGES,
}

# Язык по умолчанию
DEFAULT_LANGUAGE = 'ru'

# Текущий язык
_current_language = DEFAULT_LANGUAGE


def set_language(lang: str) -> bool:
    """Устанавливает текущий язык. Возвращает True при успехе."""
    global _current_language
    if lang in LANGUAGES:
        _current_language = lang
        return True
    return False


def get_language() -> str:
    """Возвращает текущий язык."""
    return _current_language


def get_available_languages() -> list:
    """Возвращает список доступных языков."""
    return list(LANGUAGES.keys())


def t(key: str, **kwargs) -> str:
    """
    Возвращает локализованную строку по ключу.
    Поддерживает форматирование через kwargs.
    """
    messages = LANGUAGES.get(_current_language, LANGUAGES[DEFAULT_LANGUAGE])
    text = messages.get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except KeyError:
            return text
    return text
