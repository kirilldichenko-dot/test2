from __future__ import annotations

from typing import Dict, List

from data.storage import get_paths, read_json, write_json
from profile.service import list_profiles


def compute_top10() -> List[Dict[str, object]]:
    profiles = list_profiles()
    items = []
    for key, u in profiles.items():
        if not isinstance(u, dict):
            continue
        user_id = int(u.get("user_id") or key)
        username = str(u.get("username") or "")
        score = int(u.get("total_score") or 0)
        wins = int(u.get("wins") or 0)
        games = int(u.get("games_played") or 0)
        chess_elo = int(u.get("chess_elo") or 1000)
        checkers_elo = int(u.get("checkers_elo") or 1000)
        rating = chess_elo + checkers_elo
        items.append(
            {
                "user_id": user_id,
                "username": username,
                "score": score,
                "wins": wins,
                "games_played": games,
                "chess_elo": chess_elo,
                "checkers_elo": checkers_elo,
                "rating": rating,
            }
        )

    items.sort(key=lambda x: (int(x["rating"]), int(x["wins"])), reverse=True)
    return items[:10]


def refresh_and_persist_leaderboard() -> List[Dict[str, object]]:
    top = compute_top10()
    paths = get_paths()
    data = read_json(paths.leaderboard)
    data["top"] = top
    write_json(paths.leaderboard, data)
    return top

