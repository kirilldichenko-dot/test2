from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from games.dice.engine import outcome, roll
from games.lobby import create_game, get_game, update_game
from leaderboard.service import refresh_and_persist_leaderboard
from profile.service import record_game_result


def _dice_keyboard(game_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🎲 Бросить", callback_data=f"play:dice:roll:{game_id}")],
            [InlineKeyboardButton("🔙 Назад", callback_data="nav:back:games")],
        ]
    )


async def start_dice_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    g = create_game("dice", host_id=user_id, mode="bot")
    # bot is implicit opponent
    update_game(g["game_id"], opponent_id="bot", players=[user_id, "bot"], status="active", board_state={})

    msg = update.effective_message
    if msg:
        await msg.reply_text(
            "🎲 Дуэль кубиков (бот)\n\nНажмите «Бросить».",
            reply_markup=_dice_keyboard(g["game_id"]),
        )


async def start_dice_pvp(update: Update, context: ContextTypes.DEFAULT_TYPE, game_id: str) -> None:
    msg = update.effective_message
    if msg:
        await msg.reply_text(
            f"🎲 Дуэль кубиков (PvP)\nИгра: {game_id}\n\nХодит текущий игрок — нажмите «Бросить».",
            reply_markup=_dice_keyboard(game_id),
        )


async def handle_dice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    query = update.callback_query
    if not query or not query.data:
        return False
    if not query.data.startswith("play:dice:roll:"):
        return False
    await query.answer()

    game_id = query.data.split(":")[-1]
    g = get_game(game_id)
    if not g:
        await query.message.reply_text("Игра не найдена.")
        return True

    user_id = update.effective_user.id
    if g.get("status") != "active":
        await query.message.reply_text("Игра не активна.")
        return True

    players = g.get("players") or []
    if user_id not in players:
        await query.message.reply_text("Вы не участник этой игры.")
        return True

    current_turn = g.get("current_turn")
    if current_turn not in (user_id, "bot"):
        await query.message.reply_text("Сейчас не ваш ход.")
        return True

    state = g.get("board_state") or {}
    host_id = int(g.get("host_id"))
    opp_id = g.get("opponent_id")

    # PvP: we store host_roll and opp_roll in state
    if user_id == host_id:
        state["host_roll"] = roll()
        update_game(game_id, board_state=state)
        await query.message.reply_text(f"Вы бросили: {state['host_roll']}")
        # next turn to opponent/bot
        next_turn = "bot" if opp_id == "bot" else int(opp_id)
        update_game(game_id, current_turn=next_turn)
    else:
        state["opp_roll"] = roll()
        update_game(game_id, board_state=state)
        await query.message.reply_text(f"Вы бросили: {state['opp_roll']}")
        update_game(game_id, current_turn=host_id)

    # Bot mode: if bot's turn, auto roll and finish
    g2 = get_game(game_id) or g
    state = g2.get("board_state") or state
    if opp_id == "bot" and g2.get("current_turn") == "bot":
        state["opp_roll"] = roll()
        update_game(game_id, board_state=state, current_turn=host_id)
        await query.message.reply_text(f"Бот бросил: {state['opp_roll']}")

    # Resolve if both rolled
    if state.get("host_roll") and state.get("opp_roll"):
        hr = int(state["host_roll"])
        orr = int(state["opp_roll"])
        score_host = outcome(hr, orr)

        # scoring: win +3, draw +1, lose +0
        if score_host == 1.0:
            host_delta, opp_delta = 3, 0
            res = "✅ Победа хоста"
        elif score_host == 0.5:
            host_delta, opp_delta = 1, 1
            res = "🤝 Ничья"
        else:
            host_delta, opp_delta = 0, 3
            res = "❌ Победа оппонента"

        # Update profiles (score-based field is kept for now)
        record_game_result(host_id, score_delta=host_delta, won=(score_host == 1.0), username=None)
        if opp_id != "bot":
            record_game_result(int(opp_id), score_delta=opp_delta, won=(score_host == 0.0), username=None)

        update_game(game_id, status="finished")
        refresh_and_persist_leaderboard()
        await query.message.reply_text(
            f"Итог: {hr} : {orr}\n{res}",
        )
    else:
        await query.message.reply_text("Ожидаем второй бросок…", reply_markup=_dice_keyboard(game_id))

    return True

