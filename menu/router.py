from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from leaderboard.views import render_leaderboard_ru
from menu.keys import main_menu_keyboard, settings_keyboard
from profile.views import render_profile_ru
from settings.service import cycle_difficulty, cycle_language, cycle_theme, get_user_settings, toggle_music


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()

    data = query.data or ""
    msg = query.message
    if not msg:
        return

    # Navigation
    if data == "nav:back:main":
        await msg.edit_text("Главное меню", reply_markup=main_menu_keyboard())
        return

    # Main menu
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

    await msg.reply_text("Неизвестное действие.")

