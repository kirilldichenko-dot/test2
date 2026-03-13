from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes


class Game(ABC):
    game_id: str
    title: str

    @abstractmethod
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        raise NotImplementedError

    async def show_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        msg = update.effective_message
        if msg:
            await msg.reply_text("No settings for this game yet.")

    async def show_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        msg = update.effective_message
        if msg:
            await msg.reply_text("No stats yet.")

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        return False

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        return False

    def active_key(self) -> str:
        return f"active_game:{self.game_id}"

    def set_active(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        context.user_data["active_game_id"] = self.game_id

    def clear_active(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        if context.user_data.get("active_game_id") == self.game_id:
            context.user_data.pop("active_game_id", None)

    @staticmethod
    def get_active_game_id(context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
        v = context.user_data.get("active_game_id")
        return str(v) if v else None

