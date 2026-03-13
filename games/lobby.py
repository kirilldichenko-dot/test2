from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from data.storage import get_paths, read_json, write_json


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> Dict[str, Any]:
    paths = get_paths()
    data = read_json(paths.games)
    if not isinstance(data.get("games"), dict):
        data["games"] = {}
    return data


def _save(data: Dict[str, Any]) -> None:
    paths = get_paths()
    write_json(paths.games, data)


def create_game(game_type: str, *, host_id: int, mode: str) -> Dict[str, Any]:
    data = _load()
    games = data["games"]

    game_id = secrets.token_hex(4)
    obj = {
        "game_id": game_id,
        "game_type": game_type,
        "mode": mode,  # bot|pvp
        "host_id": host_id,
        "opponent_id": None,
        "players": [host_id],
        "status": "waiting" if mode == "pvp" else "active",
        "current_turn": host_id,
        "board_state": None,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }
    games[game_id] = obj
    data["games"] = games
    _save(data)
    return obj


def list_waiting(game_type: str) -> List[Dict[str, Any]]:
    data = _load()
    games = data["games"]
    out = []
    for g in games.values():
        if not isinstance(g, dict):
            continue
        if g.get("game_type") != game_type:
            continue
        if g.get("mode") != "pvp":
            continue
        if g.get("status") != "waiting":
            continue
        out.append(g)
    out.sort(key=lambda x: x.get("created_at") or "")
    return out


def list_active_for_user(user_id: int, game_type: Optional[str] = None) -> List[Dict[str, Any]]:
    data = _load()
    games = data["games"]
    out = []
    for g in games.values():
        if not isinstance(g, dict):
            continue
        if game_type and g.get("game_type") != game_type:
            continue
        if g.get("status") != "active":
            continue
        players = g.get("players") or []
        if user_id in players:
            out.append(g)
    out.sort(key=lambda x: x.get("updated_at") or "", reverse=True)
    return out


def get_game(game_id: str) -> Optional[Dict[str, Any]]:
    data = _load()
    g = data["games"].get(game_id)
    return g if isinstance(g, dict) else None


def update_game(game_id: str, **updates: Any) -> Optional[Dict[str, Any]]:
    data = _load()
    games = data["games"]
    g = games.get(game_id)
    if not isinstance(g, dict):
        return None
    g.update(updates)
    g["updated_at"] = _now_iso()
    games[game_id] = g
    data["games"] = games
    _save(data)
    return g


def join_game(game_id: str, *, opponent_id: int) -> Optional[Dict[str, Any]]:
    g = get_game(game_id)
    if not g:
        return None
    if g.get("mode") != "pvp" or g.get("status") != "waiting":
        return None
    if int(g.get("host_id")) == opponent_id:
        return None
    return update_game(
        game_id,
        opponent_id=opponent_id,
        players=[int(g["host_id"]), opponent_id],
        status="active",
        current_turn=int(g["host_id"]),
    )

