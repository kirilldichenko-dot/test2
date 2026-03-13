from __future__ import annotations

from typing import Any, Dict, Optional

from data.storage import get_paths, read_json, write_json


def get_user_game_stats(user_id: int, game_id: str) -> Dict[str, Any]:
    paths = get_paths()
    data = read_json(paths.game_stats)
    stats = data.get("stats", {})
    u = stats.get(str(user_id), {})
    g = u.get(game_id)
    if not isinstance(g, dict):
        g = {"played": 0, "wins": 0, "losses": 0, "best_score": 0}
        u[game_id] = g
        stats[str(user_id)] = u
        data["stats"] = stats
        write_json(paths.game_stats, data)
    return g


def record_play(
    user_id: int,
    game_id: str,
    *,
    won: Optional[bool],
    score_delta: int,
    best_score_candidate: Optional[int] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    paths = get_paths()
    data = read_json(paths.game_stats)
    stats = data.get("stats", {})
    u = stats.get(str(user_id), {})
    g = u.get(game_id)
    if not isinstance(g, dict):
        g = {"played": 0, "wins": 0, "losses": 0, "best_score": 0}

    g["played"] = int(g.get("played") or 0) + 1
    if won is True:
        g["wins"] = int(g.get("wins") or 0) + 1
    elif won is False:
        g["losses"] = int(g.get("losses") or 0) + 1

    if best_score_candidate is None:
        best_score_candidate = int(g.get("best_score") or 0) + int(score_delta)

    g["best_score"] = max(int(g.get("best_score") or 0), int(best_score_candidate))

    if isinstance(extra, dict):
        g.setdefault("extra", {})
        if isinstance(g["extra"], dict):
            g["extra"].update(extra)

    u[game_id] = g
    stats[str(user_id)] = u
    data["stats"] = stats
    write_json(paths.game_stats, data)
    return g

