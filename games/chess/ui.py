from __future__ import annotations

import chess


_UNICODE = {
    chess.PAWN: ("♙", "♟"),
    chess.KNIGHT: ("♘", "♞"),
    chess.BISHOP: ("♗", "♝"),
    chess.ROOK: ("♖", "♜"),
    chess.QUEEN: ("♕", "♛"),
    chess.KING: ("♔", "♚"),
}


def render_board(board: chess.Board) -> str:
    lines = []
    for rank in range(8, 0, -1):
        row = []
        for file_idx in range(8):
            sq = chess.square(file_idx, rank - 1)
            piece = board.piece_at(sq)
            if not piece:
                row.append("·")
                continue
            white = piece.color == chess.WHITE
            row.append(_UNICODE[piece.piece_type][0 if white else 1])
        lines.append(f"{rank}  " + " ".join(row))
    lines.append("   a b c d e f g h")
    return "\n".join(lines)


def turn_text(board: chess.Board) -> str:
    return "Ход: Белые" if board.turn == chess.WHITE else "Ход: Чёрные"

