from __future__ import annotations

import random

from telegram import Update
from telegram.ext import ContextTypes

from games.base import Game
from games.stats import record_play, get_user_game_stats
from leaderboard.service import refresh_and_persist_leaderboard
from profile.service import record_game_result, get_or_create_profile


class GuessTheNumber(Game):
    game_id = "guess_number"
    title = "🔢 Guess The Number"

    def _state_key(self) -> str:
        return "guess_number_state"

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        self.set_active(context)
        user = update.effective_user
        get_or_create_profile(
            user.id,
            username=user.username or "",
            first_name=user.first_name or "",
            last_name=user.last_name or "",
        )

        target = random.randint(1, 100)
        attempts_left = 7
        context.user_data[self._state_key()] = {"target": target, "attempts_left": attempts_left, "attempts_used": 0}

        msg = update.effective_message
        if msg:
            await msg.reply_text(
                "🔢 Guess The Number\n\n"
                "I picked a number from 1 to 100.\n"
                "Send your guess as a message. You have 7 attempts."
            )

    async def show_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        s = get_user_game_stats(user.id, self.game_id)
        msg = update.effective_message
        if msg:
            await msg.reply_text(
                "📊 Guess The Number stats\n\n"
                f"Played: {int(s.get('played') or 0)}\n"
                f"Wins: {int(s.get('wins') or 0)}\n"
                f"Losses: {int(s.get('losses') or 0)}\n"
                f"Best score: {int(s.get('best_score') or 0)}"
            )

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        if context.user_data.get("active_game_id") != self.game_id:
            return False

        state = context.user_data.get(self._state_key())
        if not isinstance(state, dict):
            return False

        msg = update.effective_message
        if not msg or not msg.text:
            return False

        try:
            guess = int(msg.text.strip())
        except ValueError:
            await msg.reply_text("Please send a number (1–100).")
            return True

        target = int(state.get("target"))
        attempts_left = int(state.get("attempts_left"))
        attempts_used = int(state.get("attempts_used"))

        if attempts_left <= 0:
            await msg.reply_text("Game over. Start again from the menu.")
            return True

        attempts_left -= 1
        attempts_used += 1
        state["attempts_left"] = attempts_left
        state["attempts_used"] = attempts_used
        context.user_data[self._state_key()] = state

        if guess == target:
            score_delta = max(0, 10 - attempts_used)
            user = update.effective_user
            record_game_result(
                user.id,
                score_delta=score_delta,
                won=True,
                username=user.username or "",
                first_name=user.first_name or "",
                last_name=user.last_name or "",
            )
            record_play(user.id, self.game_id, won=True, score_delta=score_delta, best_score_candidate=score_delta)
            refresh_and_persist_leaderboard()

            self.clear_active(context)
            context.user_data.pop(self._state_key(), None)

            await msg.reply_text(
                f"✅ Correct! The number was {target}.\n"
                f"Attempts used: {attempts_used}\n"
                f"+{score_delta} score"
            )
            return True

        if attempts_left <= 0:
            user = update.effective_user
            record_game_result(
                user.id,
                score_delta=0,
                won=False,
                username=user.username or "",
                first_name=user.first_name or "",
                last_name=user.last_name or "",
            )
            record_play(user.id, self.game_id, won=False, score_delta=0)
            refresh_and_persist_leaderboard()

            self.clear_active(context)
            context.user_data.pop(self._state_key(), None)

            await msg.reply_text(
                f"❌ No attempts left. The number was {target}.\n"
                "You can start a new game from the menu."
            )
            return True

        hint = "Higher" if guess < target else "Lower"
        await msg.reply_text(f"{hint}. Attempts left: {attempts_left}")
        return True

