from __future__ import annotations

from typing import Dict

from data.storage import get_paths, read_json, write_json


_LANGUAGES = ["en", "ru"]
_DIFFICULTIES = ["easy", "normal", "hard"]
_THEMES = ["dark", "light"]


def _defaults() -> Dict[str, object]:
    return {"music_on": False, "language": "en", "difficulty": "normal", "theme": "dark"}


def get_user_settings(user_id: int) -> Dict[str, object]:
    paths = get_paths()
    data = read_json(paths.settings)
    settings = data.get("settings", {})
    key = str(user_id)
    user_settings = settings.get(key)
    if not isinstance(user_settings, dict):
        user_settings = dict(_defaults())
        settings[key] = user_settings
        data["settings"] = settings
        write_json(paths.settings, data)

    # Ensure all keys exist
    changed = False
    for k, v in _defaults().items():
        if k not in user_settings:
            user_settings[k] = v
            changed = True
    if changed:
        settings[key] = user_settings
        data["settings"] = settings
        write_json(paths.settings, data)

    return {
        "music_on": bool(user_settings.get("music_on", False)),
        "language": str(user_settings.get("language", "en")),
        "difficulty": str(user_settings.get("difficulty", "normal")),
        "theme": str(user_settings.get("theme", "dark")),
    }


def _update(user_id: int, **updates: object) -> None:
    paths = get_paths()
    data = read_json(paths.settings)
    settings = data.get("settings", {})
    key = str(user_id)
    user_settings = settings.get(key) if isinstance(settings.get(key), dict) else dict(_defaults())
    user_settings.update(updates)
    settings[key] = user_settings
    data["settings"] = settings
    write_json(paths.settings, data)


def toggle_music(user_id: int) -> None:
    s = get_user_settings(user_id)
    _update(user_id, music_on=not s["music_on"])


def cycle_language(user_id: int) -> None:
    s = get_user_settings(user_id)
    cur = s["language"]
    idx = _LANGUAGES.index(cur) if cur in _LANGUAGES else 0
    _update(user_id, language=_LANGUAGES[(idx + 1) % len(_LANGUAGES)])


def cycle_difficulty(user_id: int) -> None:
    s = get_user_settings(user_id)
    cur = s["difficulty"]
    idx = _DIFFICULTIES.index(cur) if cur in _DIFFICULTIES else 0
    _update(user_id, difficulty=_DIFFICULTIES[(idx + 1) % len(_DIFFICULTIES)])


def cycle_theme(user_id: int) -> None:
    s = get_user_settings(user_id)
    cur = s["theme"]
    idx = _THEMES.index(cur) if cur in _THEMES else 0
    _update(user_id, theme=_THEMES[(idx + 1) % len(_THEMES)])

