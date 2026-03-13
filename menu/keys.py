from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🎮 Играть", callback_data="main:games")],
            [InlineKeyboardButton("👤 Профиль", callback_data="main:profile")],
            [InlineKeyboardButton("🏆 Рейтинг", callback_data="main:leaderboard")],
            [InlineKeyboardButton("⚙ Настройки", callback_data="main:settings")],
        ]
    )


def games_list_keyboard() -> InlineKeyboardMarkup:
    games = [
        ("♟ Шахматы", "chess"),
        ("⭕ Шашки", "checkers"),
        ("🎲 Дуэль кубиков", "dice"),
    ]
    rows = [[InlineKeyboardButton(title, callback_data=f"games:open:{gid}")] for title, gid in games]
    rows.append([InlineKeyboardButton("🔙 Назад", callback_data="nav:back:main")])
    return InlineKeyboardMarkup(rows)


def game_modes_keyboard(game_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("▶ Играть с ботом", callback_data=f"mode:{game_id}:bot")],
            [InlineKeyboardButton("👥 Играть с игроком", callback_data=f"mode:{game_id}:pvp")],
            [InlineKeyboardButton("🔙 Назад", callback_data="nav:back:games")],
        ]
    )

def lobby_keyboard(game_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Создать игру", callback_data=f"lobby:{game_id}:create")],
            [InlineKeyboardButton("Присоединиться", callback_data=f"lobby:{game_id}:join")],
            [InlineKeyboardButton("Активные игры", callback_data=f"lobby:{game_id}:active")],
            [InlineKeyboardButton("🔙 Назад", callback_data=f"games:open:{game_id}")],
        ]
    )

def settings_keyboard(music_on: bool, language: str, difficulty: str, theme: str) -> InlineKeyboardMarkup:
    music_label = "🔊 Музыка: Вкл" if music_on else "🔇 Музыка: Выкл"
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(music_label, callback_data="settings:music:toggle")],
            [InlineKeyboardButton(f"🌐 Язык: {language}", callback_data="settings:lang:cycle")],
            [InlineKeyboardButton(f"🎮 Сложность: {difficulty}", callback_data="settings:difficulty:cycle")],
            [InlineKeyboardButton(f"🎨 Тема: {theme}", callback_data="settings:theme:cycle")],
            [InlineKeyboardButton("🔙 Назад", callback_data="nav:back:main")],
        ]
    )

