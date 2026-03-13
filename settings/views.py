from settings.service import get_user_settings
from menu.keys import settings_keyboard


def render_settings_menu(user_id: int) -> tuple[str, object]:
    s = get_user_settings(user_id)
    return "⚙ Settings", settings_keyboard(**s)

