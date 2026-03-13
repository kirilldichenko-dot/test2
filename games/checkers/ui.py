from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from games.checkers.engine import EMPTY, is_black, is_white


PIECE_EMOJI = {
    "w": "⚪",
    "W": "⚪",
    "b": "⚫",
    "B": "⚫",
    ".": " ",
}


def render_keyboard(
    board: list[list[str]],
    *,
    game_id: str,
    selected: tuple[int, int] | None,
    highlights: set[tuple[int, int]] | None,
) -> InlineKeyboardMarkup:
    highlights = highlights or set()
    rows = []
    for r in range(8):
        row = []
        for c in range(8):
            if (r + c) % 2 == 0:
                row.append(InlineKeyboardButton("⬛", callback_data="noop"))
                continue
            p = board[r][c]
            label = PIECE_EMOJI.get(p, " ")
            if selected == (r, c):
                label = "🟦"
            elif (r, c) in highlights:
                label = "🟩"
            elif p != EMPTY:
                label = PIECE_EMOJI.get(p, "●")
            else:
                label = "▫️"
            row.append(
                InlineKeyboardButton(label, callback_data=f"play:checkers:cell:{game_id}:{r}:{c}")
            )
        rows.append(row)

    rows.append(
        [
            InlineKeyboardButton("🔄 Обновить", callback_data=f"play:checkers:refresh:{game_id}"),
            InlineKeyboardButton("🏳 Сдаться", callback_data=f"play:checkers:resign:{game_id}"),
        ]
    )
    rows.append([InlineKeyboardButton("🔙 Назад", callback_data="nav:back:games")])
    return InlineKeyboardMarkup(rows)


def render_text(white_turn: bool) -> str:
    return "Ход: Белые" if white_turn else "Ход: Чёрные"

