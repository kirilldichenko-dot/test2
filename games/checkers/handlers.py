from __future__ import annotations

import random

from telegram import Update
from telegram.ext import ContextTypes

from games.checkers.engine import Move, apply_move, initial_board, legal_moves, winner
from games.checkers.ui import render_keyboard, render_text
from games.lobby import create_game, get_game, update_game
from leaderboard.service import refresh_and_persist_leaderboard
from profile.service import get_or_create_profile, update_elo_after_match


def _state(game_obj: dict) -> dict:
    return game_obj.get("board_state") or {}


def _board(game_obj: dict) -> list[list[str]]:
    st = _state(game_obj)
    b = st.get("board")
    if isinstance(b, list) and len(b) == 8:
        return b
    return initial_board()


def _save_board(game_id: str, board: list[list[str]], white_turn: bool, white_id, black_id) -> None:
    update_game(
        game_id,
        board_state={"board": board, "white_turn": white_turn, "white_id": white_id, "black_id": black_id},
    )


async def start_checkers_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    get_or_create_profile(user.id, username=user.username or "", first_name=user.first_name or "", last_name=user.last_name or "")

    g = create_game("checkers", host_id=user.id, mode="bot")
    board = initial_board()
    # host plays white
    update_game(
        g["game_id"],
        opponent_id="bot",
        players=[user.id, "bot"],
        status="active",
        current_turn=user.id,
        board_state={"board": board, "white_turn": True, "white_id": user.id, "black_id": "bot"},
    )
    context.user_data["active_checkers_game_id"] = g["game_id"]
    await _send(update, context, g["game_id"])


async def start_checkers_pvp(update: Update, context: ContextTypes.DEFAULT_TYPE, game_id: str) -> None:
    g = get_game(game_id)
    if not g:
        return
    if not g.get("board_state"):
        board = initial_board()
        update_game(
            game_id,
            board_state={
                "board": board,
                "white_turn": True,
                "white_id": int(g["host_id"]),
                "black_id": int(g["opponent_id"]),
            },
        )
    context.user_data["active_checkers_game_id"] = game_id
    await _send(update, context, game_id)


async def _send(update: Update, context: ContextTypes.DEFAULT_TYPE, game_id: str) -> None:
    g = get_game(game_id)
    if not g:
        return
    st = _state(g)
    board = _board(g)
    white_turn = bool(st.get("white_turn", True))
    selected = context.user_data.get("checkers_selected", {}).get(game_id)
    highlights = context.user_data.get("checkers_highlights", {}).get(game_id) or set()
    if isinstance(highlights, list):
        highlights = set(tuple(x) for x in highlights)

    msg = update.effective_message
    if msg:
        await msg.reply_text(
            f"⭕ Шашки\nИгра: {game_id}\n\n{render_text(white_turn)}\nВыберите фигуру и клетку.",
            reply_markup=render_keyboard(
                board,
                game_id=game_id,
                selected=tuple(selected) if isinstance(selected, list) else selected,
                highlights=highlights,
            ),
        )


def _clear_selection(context: ContextTypes.DEFAULT_TYPE, game_id: str) -> None:
    sel = context.user_data.get("checkers_selected", {})
    hl = context.user_data.get("checkers_highlights", {})
    if isinstance(sel, dict):
        sel.pop(game_id, None)
        context.user_data["checkers_selected"] = sel
    if isinstance(hl, dict):
        hl.pop(game_id, None)
        context.user_data["checkers_highlights"] = hl


def _set_selection(context: ContextTypes.DEFAULT_TYPE, game_id: str, pos: tuple[int, int], highlights: set[tuple[int, int]]) -> None:
    sel = context.user_data.get("checkers_selected")
    if not isinstance(sel, dict):
        sel = {}
    sel[game_id] = list(pos)
    context.user_data["checkers_selected"] = sel

    hl = context.user_data.get("checkers_highlights")
    if not isinstance(hl, dict):
        hl = {}
    hl[game_id] = [list(x) for x in highlights]
    context.user_data["checkers_highlights"] = hl


def _legal_destinations(board, white_turn: bool, src: tuple[int, int]) -> dict[tuple[int, int], Move]:
    moves = legal_moves(board, white_turn=white_turn)
    dests = {}
    for m in moves:
        if m.path[0] == src:
            dests[m.path[-1]] = m
    return dests


async def handle_checkers_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    query = update.callback_query
    if not query or not query.data:
        return False
    if not query.data.startswith("play:checkers:"):
        return False
    await query.answer()

    parts = query.data.split(":")
    action = parts[2]
    game_id = parts[3] if len(parts) > 3 else ""

    g = get_game(game_id)
    if not g:
        await query.message.reply_text("Игра не найдена.")
        return True

    if action == "refresh":
        await _send(update, context, game_id)
        return True
    if action == "resign":
        update_game(game_id, status="finished")
        refresh_and_persist_leaderboard()
        await query.message.reply_text("🏳 Партия завершена: игрок сдался.")
        return True
    if action != "cell":
        return True

    r = int(parts[4])
    c = int(parts[5])

    st = _state(g)
    board = _board(g)
    white_turn = bool(st.get("white_turn", True))
    white_id = st.get("white_id")
    black_id = st.get("black_id")

    user_id = update.effective_user.id
    expected_player = white_id if white_turn else black_id
    if expected_player != user_id:
        await query.message.reply_text("Сейчас не ваш ход.")
        return True

    selected = context.user_data.get("checkers_selected", {}).get(game_id)
    selected = tuple(selected) if isinstance(selected, list) else None

    if not selected:
        # select piece
        dests = _legal_destinations(board, white_turn, (r, c))
        if not dests:
            await query.message.reply_text("Выберите свою фигуру с доступным ходом.")
            return True
        _set_selection(context, game_id, (r, c), set(dests.keys()))
        await _send(update, context, game_id)
        return True

    # apply move if destination valid
    dests = _legal_destinations(board, white_turn, selected)
    move = dests.get((r, c))
    if not move:
        _clear_selection(context, game_id)
        await query.message.reply_text("Ход отменён. Выберите фигуру заново.")
        await _send(update, context, game_id)
        return True

    board2 = apply_move(board, move)
    _clear_selection(context, game_id)
    # switch turn
    white_turn2 = not white_turn
    _save_board(game_id, board2, white_turn2, white_id, black_id)

    win = winner(board2)
    if win:
        update_game(game_id, status="finished")
        # PvP ELO
        if g.get("opponent_id") != "bot":
            score_white = 1.0 if win == "white" else 0.0
            update_elo_after_match("checkers", user_a_id=int(white_id), user_b_id=int(black_id), score_a=score_white)
        refresh_and_persist_leaderboard()
        await query.message.reply_text("✅ Игра окончена.")
        return True

    # bot move
    if g.get("opponent_id") == "bot" and (white_turn2 is False):
        moves = legal_moves(board2, white_turn=False)
        if moves:
            m = random.choice(moves)
            board3 = apply_move(board2, m)
            _save_board(game_id, board3, True, white_id, black_id)
            win = winner(board3)
            if win:
                update_game(game_id, status="finished")
                refresh_and_persist_leaderboard()
                await query.message.reply_text("Игра окончена.")
                return True

    await _send(update, context, game_id)
    return True

