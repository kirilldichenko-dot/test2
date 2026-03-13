from leaderboard.service import refresh_and_persist_leaderboard


def render_leaderboard_ru() -> str:
    top = refresh_and_persist_leaderboard()
    if not top:
        return "🏆 Рейтинг\n\nПока нет игроков."

    lines = ["🏆 Рейтинг (Топ-10)\n"]
    for i, row in enumerate(top, start=1):
        username = row.get("username") or ""
        username_str = f"@{username}" if username else f"ID {row.get('user_id')}"
        rating = row.get("rating", 0)
        lines.append(f"{i}. {username_str} — {rating}")
    return "\n".join(lines)

