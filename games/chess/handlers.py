from __future__ import annotations

import re

import chess
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from games.chess.ai import pick_move
from games.chess.engine import game_result, load_board, to_fen, try_push_uci
from games.chess.ui import render_board, turn_text
from games.lobby import create_game, get_game, update_game
from leaderboard.service import refresh_and_persist_leaderboard
from profile.service import get_or_create_profile, record_game_result, update_elo_after_match


_UCI_RE = re.compile(r"^[a-h][1-8][a-h][1-8][qrbn]?$", re.IGNORECASE)


def _kb(game_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🔄 Обновить", callback_data=f"play:chess:refresh:{game_id}"),
                InlineKeyboardButton("🏳 Сдаться", callback_data=f"play:chess:resign:{game_id}"),
            ],
            [InlineKeyboardButton("🔙 Назад", callback_data="nav:back:games")],
        ]
    )


async def _send_state(update: Update, context: ContextTypes.DEFAULT_TYPE, game_id: str) -> None:
    g = get_game(game_id)
    if not g:
        return
    board = load_board((g.get("board_state") or {}).get("fen"))
    text = (
        f"♟ Шахматы\nИгра: {game_id}\n\n"
        f"<pre>{render_board(board)}</pre>\n\n"
        f"{turn_text(board)}\n"
        "Ход: отправьте UCI, например <code>e2e4</code>"
    )
    msg = update.effective_message
    if msg:
        await msg.reply_html(text, reply_markup=_kb(game_id))


async def start_chess_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    get_or_create_profile(user.id, username=user.username or "", first_name=user.first_name or "", last_name=user.last_name or "")

    g = create_game("chess", host_id=user.id, mode="bot")
    board = chess.Board()
    update_game(
        g["game_id"],
        opponent_id="bot",
        players=[user.id, "bot"],
        status="active",
        current_turn=user.id,
        board_state={"fen": board.fen(), "white_id": user.id, "black_id": "bot"},
    )
    context.user_data["active_chess_game_id"] = g["game_id"]
    await _send_state(update, context, g["game_id"])


async def start_chess_pvp(update: Update, context: ContextTypes.DEFAULT_TYPE, game_id: str) -> None:
    g = get_game(game_id)
    if not g:
        return
    if not g.get("board_state"):
        board = chess.Board()
        update_game(
            game_id,
            board_state={
                "fen": board.fen(),
                "white_id": int(g["host_id"]),
                "black_id": int(g["opponent_id"]),
            },
        )
    context.user_data["active_chess_game_id"] = game_id
    await _send_state(update, context, game_id)


async def handle_chess_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    query = update.callback_query
    if not query or not query.data:
        return False
    if not query.data.startswith("play:chess:"):
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
        await _send_state(update, context, game_id)
        return True

    if action == "resign":
        user_id = update.effective_user.id
        host_id = int(g.get("host_id"))
        opp_id = g.get("opponent_id")
        update_game(game_id, status="finished")

        # PvP ELO: resign => loss
        if opp_id != "bot" and opp_id is not None:
            a = host_id
            b = int(opp_id)
            if user_id == a:
                update_elo_after_match("chess", user_a_id=a, user_b_id=b, score_a=0.0)
            else:
                update_elo_after_match("chess", user_a_id=b, user_b_id=a, score_a=0.0)

        await query.message.reply_text("🏳 Партия завершена: игрок сдался.")
        refresh_and_persist_leaderboard()
        return True

    return True


async def handle_chess_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    msg = update.effective_message
    if not msg or not msg.text:
        return False

    game_id = context.user_data.get("active_chess_game_id")
    if not game_id:
        return False

    g = get_game(str(game_id))
    if not g or g.get("game_type") != "chess" or g.get("status") != "active":
        return False

    uci = msg.text.strip().lower()
    if not _UCI_RE.match(uci):
        return False

    user_id = update.effective_user.id
    board_state = g.get("board_state") or {}
    board = load_board(board_state.get("fen"))

    white_id = board_state.get("white_id")
    black_id = board_state.get("black_id")
    is_white_turn = board.turn == chess.WHITE
    expected_player = white_id if is_white_turn else black_id

    if expected_player != user_id:
        await msg.reply_text("Сейчас не ваш ход.")
        return True

    if not try_push_uci(board, uci):
        await msg.reply_text("Нелегальный ход.")
        return True

    # Update state
    board_state["fen"] = to_fen(board)
    update_game(str(game_id), board_state=board_state)

    over, over_text, score_white = game_result(board)
    if over:
        update_game(str(game_id), status="finished")
        # PvP ELO update
        opp = g.get("opponent_id")
        host_id = int(g.get("host_id"))
        if opp != "bot" and opp is not None:
            # host is always white in our setup
            update_elo_after_match("chess", user_a_id=int(white_id), user_b_id=int(black_id), score_a=float(score_white))
        await msg.reply_text(over_text)
        refresh_and_persist_leaderboard()
        return True

    # Bot reply if needed
    if g.get("opponent_id") == "bot":
        bot_move = pick_move(board)
        board.push(bot_move)
        board_state["fen"] = to_fen(board)
        update_game(str(game_id), board_state=board_state)

        over, over_text, _ = game_result(board)
        if over:
            update_game(str(game_id), status="finished")
            await msg.reply_text(over_text)
            refresh_and_persist_leaderboard()
            return True

    await _send_state(update, context, str(game_id))
    return True

