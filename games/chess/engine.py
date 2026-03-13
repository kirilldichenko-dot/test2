from __future__ import annotations

import chess


def new_board() -> chess.Board:
    return chess.Board()


def load_board(fen: str | None) -> chess.Board:
    if fen:
        return chess.Board(fen=fen)
    return chess.Board()


def to_fen(board: chess.Board) -> str:
    return board.fen()


def try_push_uci(board: chess.Board, uci: str) -> bool:
    try:
        move = chess.Move.from_uci(uci)
    except ValueError:
        return False
    if move not in board.legal_moves:
        return False
    board.push(move)
    return True


def game_result(board: chess.Board) -> tuple[bool, str, float | None]:
    """
    Returns (is_over, message, score_white) where score_white is:
    1.0 white win, 0.5 draw, 0.0 white loss, None if not over.
    """
    if board.is_checkmate():
        winner = "Белые" if board.turn == chess.BLACK else "Чёрные"
        score_white = 1.0 if winner == "Белые" else 0.0
        return True, f"Мат! Победили {winner}.", score_white
    if board.is_stalemate():
        return True, "Пат. Ничья.", 0.5
    if board.is_insufficient_material():
        return True, "Недостаточно материала. Ничья.", 0.5
    if board.can_claim_threefold_repetition():
        return True, "Троекратное повторение. Ничья.", 0.5
    if board.can_claim_fifty_moves():
        return True, "Правило 50 ходов. Ничья.", 0.5
    return False, "", None

