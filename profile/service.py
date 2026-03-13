from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from data.storage import get_paths, read_json, write_json


@dataclass
class UserProfile:
    user_id: int
    username: str
    first_name: str
    last_name: str
    total_score: int
    games_played: int
    wins: int
    losses: int
    chess_elo: int
    checkers_elo: int

    @property
    def win_rate(self) -> float:
        if self.games_played <= 0:
            return 0.0
        return self.wins / self.games_played

    @property
    def rating(self) -> int:
        return int(self.chess_elo) + int(self.checkers_elo)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_or_create_profile(
    user_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
) -> UserProfile:
    paths = get_paths()
    data = read_json(paths.users)
    users = data.get("users", {})
    key = str(user_id)
    u = users.get(key)

    if not isinstance(u, dict):
        u = {
            "user_id": user_id,
            "username": username or "",
            "first_name": first_name or "",
            "last_name": last_name or "",
            "created_at": _now_iso(),
            "total_score": 0,
            "games_played": 0,
            "wins": 0,
            "losses": 0,
            "chess_elo": 1000,
            "checkers_elo": 1000,
        }
        users[key] = u
        data["users"] = users
        write_json(paths.users, data)
    else:
        changed = False
        for field, value in (
            ("username", username),
            ("first_name", first_name),
            ("last_name", last_name),
        ):
            if value is not None and value != "" and u.get(field) != value:
                u[field] = value
                changed = True
        if changed:
            users[key] = u
            data["users"] = users
            write_json(paths.users, data)

    return UserProfile(
        user_id=user_id,
        username=str(u.get("username") or ""),
        first_name=str(u.get("first_name") or ""),
        last_name=str(u.get("last_name") or ""),
        total_score=int(u.get("total_score") or 0),
        games_played=int(u.get("games_played") or 0),
        wins=int(u.get("wins") or 0),
        losses=int(u.get("losses") or 0),
        chess_elo=int(u.get("chess_elo") or 1000),
        checkers_elo=int(u.get("checkers_elo") or 1000),
    )


def expected_score(r_a: int, r_b: int) -> float:
    return 1.0 / (1.0 + 10 ** ((r_b - r_a) / 400))


def apply_elo(r_a: int, r_b: int, score_a: float, k: int = 32) -> tuple[int, int]:
    e_a = expected_score(r_a, r_b)
    e_b = expected_score(r_b, r_a)
    new_a = round(r_a + k * (score_a - e_a))
    new_b = round(r_b + k * ((1.0 - score_a) - e_b))
    return int(new_a), int(new_b)


def update_elo_after_match(
    game_type: str,
    *,
    user_a_id: int,
    user_b_id: int,
    score_a: float,
    k: int = 32,
) -> None:
    """Update ELO for chess/checkers only. score_a: 1.0 win, 0.5 draw, 0.0 loss."""
    if game_type not in ("chess", "checkers"):
        return

    paths = get_paths()
    data = read_json(paths.users)
    users = data.get("users", {})

    a = users.get(str(user_a_id))
    b = users.get(str(user_b_id))
    if not isinstance(a, dict):
        a = get_or_create_profile(user_a_id).__dict__
    if not isinstance(b, dict):
        b = get_or_create_profile(user_b_id).__dict__

    field = "chess_elo" if game_type == "chess" else "checkers_elo"
    r_a = int(a.get(field) or 1000)
    r_b = int(b.get(field) or 1000)
    new_a, new_b = apply_elo(r_a, r_b, score_a, k=k)
    a[field] = new_a
    b[field] = new_b

    users[str(user_a_id)] = a
    users[str(user_b_id)] = b
    data["users"] = users
    write_json(paths.users, data)


def record_game_result(
    user_id: int,
    *,
    score_delta: int,
    won: Optional[bool],
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
) -> UserProfile:
    paths = get_paths()
    data = read_json(paths.users)
    users = data.get("users", {})
    key = str(user_id)

    u = users.get(key)
    if not isinstance(u, dict):
        u = get_or_create_profile(
            user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        ).__dict__

    u["total_score"] = int(u.get("total_score") or 0) + int(score_delta)
    u["games_played"] = int(u.get("games_played") or 0) + 1
    if won is True:
        u["wins"] = int(u.get("wins") or 0) + 1
    elif won is False:
        u["losses"] = int(u.get("losses") or 0) + 1

    # Keep identity fresh when provided
    if username is not None:
        u["username"] = username or ""
    if first_name is not None:
        u["first_name"] = first_name or ""
    if last_name is not None:
        u["last_name"] = last_name or ""

    users[key] = u
    data["users"] = users
    write_json(paths.users, data)

    return get_or_create_profile(user_id)


def list_profiles() -> Dict[str, Any]:
    paths = get_paths()
    data = read_json(paths.users)
    users = data.get("users", {})
    return users if isinstance(users, dict) else {}

