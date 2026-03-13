from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from leaderboard.views import render_leaderboard_ru
from menu.keys import games_list_keyboard, lobby_keyboard, main_menu_keyboard, game_modes_keyboard, settings_keyboard
from profile.views import render_profile_ru
from settings.service import cycle_difficulty, cycle_language, cycle_theme, get_user_settings, toggle_music

from games.lobby import create_game, join_game, list_active_for_user, list_waiting
from games.chess.handlers import handle_chess_callback, start_chess_bot, start_chess_pvp
from games.checkers.handlers import handle_checkers_callback, start_checkers_bot, start_checkers_pvp
from games.dice.handlers import handle_dice_callback, start_dice_bot, start_dice_pvp


GAME_TITLES_RU = {"chess": "♟ Шахматы", "checkers": "⭕ Шашки", "dice": "🎲 Дуэль кубиков"}


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()

    data = query.data or ""
    msg = query.message
    if not msg:
        return

    # Gameplay callbacks (boards/buttons) have priority
    if data.startswith("play:chess:") and await handle_chess_callback(update, context):
        return
    if data.startswith("play:checkers:") and await handle_checkers_callback(update, context):
        return
    if data.startswith("play:dice:") and await handle_dice_callback(update, context):
        return

    # Navigation
    if data == "nav:back:main":
        await msg.edit_text("Главное меню", reply_markup=main_menu_keyboard())
        return
    if data == "nav:back:games":
        await msg.edit_text("🎮 Игры", reply_markup=games_list_keyboard())
        return

    # Main menu
    if data == "main:games":
        await msg.edit_text("🎮 Игры", reply_markup=games_list_keyboard())
        return
    if data == "main:profile":
        await msg.edit_text(render_profile_ru(update.effective_user), reply_markup=main_menu_keyboard())
        return
    if data == "main:leaderboard":
        await msg.edit_text(render_leaderboard_ru(), reply_markup=main_menu_keyboard())
        return
    if data == "main:settings":
        s = get_user_settings(update.effective_user.id)
        await msg.edit_text("⚙ Настройки", reply_markup=settings_keyboard(**s))
        return

    # Settings actions
    if data == "settings:music:toggle":
        toggle_music(update.effective_user.id)
        s = get_user_settings(update.effective_user.id)
        await msg.edit_text("⚙ Настройки", reply_markup=settings_keyboard(**s))
        return
    if data == "settings:lang:cycle":
        cycle_language(update.effective_user.id)
        s = get_user_settings(update.effective_user.id)
        await msg.edit_text("⚙ Настройки", reply_markup=settings_keyboard(**s))
        return
    if data == "settings:difficulty:cycle":
        cycle_difficulty(update.effective_user.id)
        s = get_user_settings(update.effective_user.id)
        await msg.edit_text("⚙ Настройки", reply_markup=settings_keyboard(**s))
        return
    if data == "settings:theme:cycle":
        cycle_theme(update.effective_user.id)
        s = get_user_settings(update.effective_user.id)
        await msg.edit_text("⚙ Настройки", reply_markup=settings_keyboard(**s))
        return

    # Games list → modes
    if data.startswith("games:open:"):
        game_id = data.split(":", 2)[2]
        title = GAME_TITLES_RU.get(game_id, "Игра")
        await msg.edit_text(title, reply_markup=game_modes_keyboard(game_id))
        return

    # Mode selection
    if data.startswith("mode:") and data.count(":") == 2:
        _, game_id, mode = data.split(":", 2)
        if mode == "bot":
            if game_id == "chess":
                await start_chess_bot(update, context)
                return
            if game_id == "checkers":
                await start_checkers_bot(update, context)
                return
            if game_id == "dice":
                await start_dice_bot(update, context)
                return
        if mode == "pvp":
            await msg.edit_text(f"{GAME_TITLES_RU.get(game_id,'Игра')}\n\n👥 Играть с игроком", reply_markup=lobby_keyboard(game_id))
            return

    # Lobby actions
    if data.startswith("lobby:") and data.count(":") >= 2:
        _, game_id, action, *rest = data.split(":")
        user_id = update.effective_user.id

        if action == "create":
            g = create_game(game_id, host_id=user_id, mode="pvp")
            await msg.reply_text(
                f"✅ Игра создана. ID: {g['game_id']}\nОжидаем второго игрока…"
            )
            return

        if action == "join":
            waiting = list_waiting(game_id)
            if not waiting:
                await msg.reply_text("Нет доступных игр. Создайте новую.")
                return
            rows = []
            for g in waiting[:10]:
                gid = g["game_id"]
                rows.append(
                    [
                        InlineKeyboardButton(
                            f"Присоединиться: {gid}",
                            callback_data=f"lobby:{game_id}:joinselect:{gid}",
                        )
                    ]
                )
            rows.append([InlineKeyboardButton("🔙 Назад", callback_data=f"mode:{game_id}:pvp")])
            await msg.reply_text("Выберите игру для присоединения:", reply_markup=InlineKeyboardMarkup(rows))
            return

        if action == "joinselect" and rest:
            game_obj = join_game(rest[0], opponent_id=user_id)
            if not game_obj:
                await msg.reply_text("Не удалось присоединиться (игра уже занята/не существует).")
                return
            # Start PvP session
            if game_id == "chess":
                await start_chess_pvp(update, context, game_obj["game_id"])
                return
            if game_id == "checkers":
                await start_checkers_pvp(update, context, game_obj["game_id"])
                return
            if game_id == "dice":
                await start_dice_pvp(update, context, game_obj["game_id"])
                return

        if action == "active":
            active = list_active_for_user(user_id, game_type=game_id)
            if not active:
                await msg.reply_text("Активных игр нет.")
                return
            lines = ["Активные игры:\n"]
            for g in active[:10]:
                lines.append(f"- {g['game_id']} ({g.get('status')})")
            await msg.reply_text("\n".join(lines))
            return

    await msg.reply_text("Неизвестное действие.")

