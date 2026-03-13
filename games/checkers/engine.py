from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple


EMPTY = "."
W_MAN = "w"
W_KING = "W"
B_MAN = "b"
B_KING = "B"


@dataclass
class Move:
    path: List[Tuple[int, int]]  # sequence of squares (r,c)
    captures: List[Tuple[int, int]]  # captured piece squares


def initial_board() -> List[List[str]]:
    board = [[EMPTY for _ in range(8)] for _ in range(8)]
    for r in range(3):
        for c in range(8):
            if (r + c) % 2 == 1:
                board[r][c] = B_MAN
    for r in range(5, 8):
        for c in range(8):
            if (r + c) % 2 == 1:
                board[r][c] = W_MAN
    return board


def in_bounds(r: int, c: int) -> bool:
    return 0 <= r < 8 and 0 <= c < 8


def is_white(piece: str) -> bool:
    return piece in (W_MAN, W_KING)


def is_black(piece: str) -> bool:
    return piece in (B_MAN, B_KING)


def is_king(piece: str) -> bool:
    return piece in (W_KING, B_KING)


def directions(piece: str) -> List[Tuple[int, int]]:
    if piece == W_MAN:
        return [(-1, -1), (-1, 1)]
    if piece == B_MAN:
        return [(1, -1), (1, 1)]
    return [(-1, -1), (-1, 1), (1, -1), (1, 1)]


def opponent(piece: str) -> tuple[str, str]:
    return (B_MAN, B_KING) if is_white(piece) else (W_MAN, W_KING)


def clone_board(board: List[List[str]]) -> List[List[str]]:
    return [row[:] for row in board]


def _piece_moves(board: List[List[str]], r: int, c: int) -> List[Move]:
    piece = board[r][c]
    if piece == EMPTY:
        return []

    moves: List[Move] = []
    for dr, dc in directions(piece):
        rr, cc = r + dr, c + dc
        if in_bounds(rr, cc) and board[rr][cc] == EMPTY:
            moves.append(Move(path=[(r, c), (rr, cc)], captures=[]))
    return moves


def _piece_captures(board: List[List[str]], r: int, c: int) -> List[Move]:
    piece = board[r][c]
    if piece == EMPTY:
        return []

    caps: List[Move] = []
    opp1, opp2 = opponent(piece)

    for dr, dc in directions(piece):
        mid_r, mid_c = r + dr, c + dc
        land_r, land_c = r + 2 * dr, c + 2 * dc
        if not in_bounds(land_r, land_c):
            continue
        if board[land_r][land_c] != EMPTY:
            continue
        if not in_bounds(mid_r, mid_c):
            continue
        if board[mid_r][mid_c] not in (opp1, opp2):
            continue

        # single capture, then try extend (multi-capture)
        next_board = clone_board(board)
        next_board[land_r][land_c] = piece
        next_board[r][c] = EMPTY
        next_board[mid_r][mid_c] = EMPTY

        tail_moves = _extend_captures(next_board, land_r, land_c, piece, [(r, c), (land_r, land_c)], [(mid_r, mid_c)])
        caps.extend(tail_moves)

    return caps


def _extend_captures(
    board: List[List[str]],
    r: int,
    c: int,
    piece: str,
    path: List[Tuple[int, int]],
    captures: List[Tuple[int, int]],
) -> List[Move]:
    opp1, opp2 = opponent(piece)
    extended: List[Move] = []
    found = False

    for dr, dc in directions(piece):
        mid_r, mid_c = r + dr, c + dc
        land_r, land_c = r + 2 * dr, c + 2 * dc
        if not in_bounds(land_r, land_c) or not in_bounds(mid_r, mid_c):
            continue
        if board[land_r][land_c] != EMPTY:
            continue
        if board[mid_r][mid_c] not in (opp1, opp2):
            continue

        found = True
        next_board = clone_board(board)
        next_board[land_r][land_c] = piece
        next_board[r][c] = EMPTY
        next_board[mid_r][mid_c] = EMPTY
        extended.extend(
            _extend_captures(
                next_board,
                land_r,
                land_c,
                piece,
                path + [(land_r, land_c)],
                captures + [(mid_r, mid_c)],
            )
        )

    if not found:
        extended.append(Move(path=path, captures=captures))
    return extended


def legal_moves(board: List[List[str]], *, white_turn: bool) -> List[Move]:
    all_caps: List[Move] = []
    all_moves: List[Move] = []
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p == EMPTY:
                continue
            if white_turn and not is_white(p):
                continue
            if (not white_turn) and not is_black(p):
                continue
            all_caps.extend(_piece_captures(board, r, c))
            all_moves.extend(_piece_moves(board, r, c))
    return all_caps if all_caps else all_moves


def apply_move(board: List[List[str]], move: Move) -> List[List[str]]:
    next_board = clone_board(board)
    (sr, sc) = move.path[0]
    (er, ec) = move.path[-1]
    piece = next_board[sr][sc]
    next_board[sr][sc] = EMPTY
    next_board[er][ec] = piece
    for cr, cc in move.captures:
        next_board[cr][cc] = EMPTY

    # promotion
    if piece == W_MAN and er == 0:
        next_board[er][ec] = W_KING
    if piece == B_MAN and er == 7:
        next_board[er][ec] = B_KING
    return next_board


def winner(board: List[List[str]]) -> Optional[str]:
    w = any(is_white(board[r][c]) for r in range(8) for c in range(8))
    b = any(is_black(board[r][c]) for r in range(8) for c in range(8))
    if w and not b:
        return "white"
    if b and not w:
        return "black"
    return None

