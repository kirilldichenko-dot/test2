from __future__ import annotations

import random

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from games.base import Game
from games.stats import record_play, get_user_game_stats
from profile.service import record_game_result, get_or_create_profile
from leaderboard.service import refresh_and_persist_leaderboard
from settings.service import get_user_settings


class DiceDuel(Game):
    game_id = "dice_duel"
    title = "🎲 Dice Duel"

    def _play_keyboard(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🎲 Roll", callback_data="play:dice_duel:roll")],
                [InlineKeyboardButton("🔙 Back", callback_data="nav:back:games")],
            ]
        )

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        self.set_active(context)
        user = update.effective_user
        get_or_create_profile(
            user.id,
            username=user.username or "",
            first_name=user.first_name or "",
            last_name=user.last_name or "",
        )

        msg = update.effective_message
        if not msg:
            return
        await msg.reply_text(
            "🎲 Dice Duel\n\nPress Roll to play against the bot.",
            reply_markup=self._play_keyboard(),
        )

        # Optional music hook (send a short audio if you add assets later)
        _ = get_user_settings(user.id)  # reserved for future

    async def show_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        s = get_user_game_stats(user.id, self.game_id)
        msg = update.effective_message
        if msg:
            await msg.reply_text(
                "📊 Dice Duel stats\n\n"
                f"Played: {int(s.get('played') or 0)}\n"
                f"Wins: {int(s.get('wins') or 0)}\n"
                f"Losses: {int(s.get('losses') or 0)}\n"
                f"Best score: {int(s.get('best_score') or 0)}"
            )

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        query = update.callback_query
        if not query or not query.data:
            return False
        if query.data != "play:dice_duel:roll":
            return False

        await query.answer()

        user_roll = random.randint(1, 6)
        bot_roll = random.randint(1, 6)

        if user_roll > bot_roll:
            outcome = "✅ You win!"
            won = True
            score_delta = 3
        elif user_roll < bot_roll:
            outcome = "❌ You lose."
            won = False
            score_delta = 0
        else:
            outcome = "🤝 Draw."
            won = None
            score_delta = 1

        user = update.effective_user
        record_game_result(
            user.id,
            score_delta=score_delta,
            won=won,
            username=user.username or "",
            first_name=user.first_name or "",
            last_name=user.last_name or "",
        )
        record_play(user.id, self.game_id, won=won, score_delta=score_delta)
        refresh_and_persist_leaderboard()

        await query.message.reply_text(
            f"🎲 You: {user_roll} | Bot: {bot_roll}\n{outcome}\n\n"
            f"+{score_delta} score",
            reply_markup=self._play_keyboard(),
        )
        return True

