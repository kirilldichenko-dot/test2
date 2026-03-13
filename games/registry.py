from __future__ import annotations

from typing import Dict, Optional

from games.base import Game
from games.dice_duel import DiceDuel
from games.guess_number import GuessTheNumber
from games.reaction_speed import ReactionSpeed
from games.stubs import StubGame


GAME_TITLES: Dict[str, str] = {
    "dice_duel": "🎲 Dice Duel",
    "coin_flip_battle": "🪙 Coin Flip Battle",
    "memory_game": "🧠 Memory Game",
    "guess_number": "🔢 Guess The Number",
    "reaction_speed": "⚡ Reaction Speed",
    "math_challenge": "🧮 Math Challenge",
    "puzzle_game": "🧩 Puzzle Game",
    "target_hit": "🎯 Target Hit",
    "mini_snake": "🐍 Mini Snake (text-based)",
    "card_draw": "🃏 Card Draw",
}


_GAMES: Dict[str, Game] = {
    "dice_duel": DiceDuel(),
    "guess_number": GuessTheNumber(),
    "reaction_speed": ReactionSpeed(),
    "coin_flip_battle": StubGame("coin_flip_battle", GAME_TITLES["coin_flip_battle"]),
    "memory_game": StubGame("memory_game", GAME_TITLES["memory_game"]),
    "math_challenge": StubGame("math_challenge", GAME_TITLES["math_challenge"]),
    "puzzle_game": StubGame("puzzle_game", GAME_TITLES["puzzle_game"]),
    "target_hit": StubGame("target_hit", GAME_TITLES["target_hit"]),
    "mini_snake": StubGame("mini_snake", GAME_TITLES["mini_snake"]),
    "card_draw": StubGame("card_draw", GAME_TITLES["card_draw"]),
}


def get_game(game_id: str) -> Optional[Game]:
    return _GAMES.get(game_id)


def get_active_game(context) -> Optional[Game]:
    gid = context.user_data.get("active_game_id")
    if not gid:
        return None
    return _GAMES.get(str(gid))

