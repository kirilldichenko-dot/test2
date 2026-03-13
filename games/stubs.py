from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from games.base import Game


class StubGame(Game):
    def __init__(self, game_id: str, title: str) -> None:
        self.game_id = game_id
        self.title = title

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        msg = update.effective_message
        if msg:
            await msg.reply_text(f"{self.title}\n\nThis game is under development.")

