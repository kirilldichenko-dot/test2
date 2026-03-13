from telegram import User

from profile.service import get_or_create_profile


def render_profile_ru(user: User) -> str:
    p = get_or_create_profile(
        user.id,
        username=user.username or "",
        first_name=user.first_name or "",
        last_name=user.last_name or "",
    )
    username = f"@{p.username}" if p.username else "—"
    win_rate = f"{p.win_rate * 100:.1f}%"
    full_name = (f"{p.first_name} {p.last_name}").strip() or "—"

    return (
        "👤 Профиль\n\n"
        f"ID: {p.user_id}\n"
        f"Имя: {full_name}\n"
        f"Username: {username}\n\n"
        f"Всего игр: {p.games_played}\n"
        f"Победы: {p.wins}\n"
        f"Процент побед: {win_rate}\n\n"
        f"Рейтинг (шахматы): {p.chess_elo}\n"
        f"Рейтинг (шашки): {p.checkers_elo}\n"
        f"Рейтинг (итого): {p.rating}"
    )

