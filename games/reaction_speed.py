from __future__ import annotations

import random
import asyncio
import time
import uuid

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from games.base import Game
from games.stats import record_play, get_user_game_stats
from leaderboard.service import refresh_and_persist_leaderboard
from profile.service import record_game_result, get_or_create_profile


class ReactionSpeed(Game):
    game_id = "reaction_speed"
    title = "⚡ Reaction Speed"

    def _state_key(self) -> str:
        return "reaction_speed_state"

    def _tap_keyboard(self, token: str) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            [[InlineKeyboardButton("⚡ Tap!", callback_data=f"play:reaction_speed:tap:{token}")]]
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

        token = uuid.uuid4().hex[:10]
        delay = random.uniform(1.0, 4.0)
        context.user_data[self._state_key()] = {
            "token": token,
            "ready": False,
            "go_ts": None,
            "message_id": None,
        }

        await msg.reply_text("⚡ Reaction Speed\n\nWait for GO…")

        chat_id = update.effective_chat.id

        async def _send_go() -> None:
            await asyncio.sleep(delay)
            state = context.user_data.get(self._state_key())
            if not isinstance(state, dict) or state.get("token") != token:
                return
            state["ready"] = True
            state["go_ts"] = time.time()
            context.user_data[self._state_key()] = state

            await context.bot.send_message(
                chat_id=chat_id,
                text="GO! Tap as fast as you can!",
                reply_markup=self._tap_keyboard(token),
            )

        context.application.create_task(_send_go())

    async def show_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        s = get_user_game_stats(user.id, self.game_id)
        best_ms = None
        extra = s.get("extra")
        if isinstance(extra, dict):
            best_ms = extra.get("best_ms")
        msg = update.effective_message
        if msg:
            best_ms_str = f"{int(best_ms)} ms" if best_ms is not None else "—"
            await msg.reply_text(
                "📊 Reaction Speed stats\n\n"
                f"Played: {int(s.get('played') or 0)}\n"
                f"Wins: {int(s.get('wins') or 0)}\n"
                f"Losses: {int(s.get('losses') or 0)}\n"
                f"Best reaction: {best_ms_str}\n"
                f"Best score: {int(s.get('best_score') or 0)}"
            )

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        query = update.callback_query
        if not query or not query.data:
            return False
        if not query.data.startswith("play:reaction_speed:tap:"):
            return False

        await query.answer()

        token = query.data.split(":")[-1]
        state = context.user_data.get(self._state_key())
        if not isinstance(state, dict) or state.get("token") != token:
            await query.message.reply_text("This round is no longer active. Start again from the menu.")
            return True

        if not state.get("ready") or not state.get("go_ts"):
            # Tapped too early
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

            context.user_data.pop(self._state_key(), None)
            self.clear_active(context)
            await query.message.reply_text("❌ Too early! You lose this round.")
            return True

        ms = int((time.time() - float(state["go_ts"])) * 1000)
        score_delta = max(0, 1000 - ms)

        user = update.effective_user
        record_game_result(
            user.id,
            score_delta=score_delta,
            won=True,
            username=user.username or "",
            first_name=user.first_name or "",
            last_name=user.last_name or "",
        )

        # Best reaction tracking
        prev_stats = get_user_game_stats(user.id, self.game_id)
        prev_best = None
        extra = prev_stats.get("extra")
        if isinstance(extra, dict):
            prev_best = extra.get("best_ms")
        best_ms = ms if prev_best is None else min(int(prev_best), ms)

        record_play(
            user.id,
            self.game_id,
            won=True,
            score_delta=score_delta,
            best_score_candidate=score_delta,
            extra={"best_ms": best_ms},
        )
        refresh_and_persist_leaderboard()

        context.user_data.pop(self._state_key(), None)
        self.clear_active(context)

        await query.message.reply_text(
            f"✅ Reaction: {ms} ms\n+{score_delta} score"
        )
        return True

