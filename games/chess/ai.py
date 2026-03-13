from __future__ import annotations

import random

import chess


def pick_move(board: chess.Board) -> chess.Move:
    """Very basic AI: pick a random legal move."""
    moves = list(board.legal_moves)
    return random.choice(moves)

