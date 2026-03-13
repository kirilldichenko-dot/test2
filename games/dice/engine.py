from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional


@dataclass
class DiceState:
    host_roll: Optional[int] = None
    opp_roll: Optional[int] = None


def new_state() -> DiceState:
    return DiceState()


def roll() -> int:
    return random.randint(1, 6)


def outcome(host_roll: int, opp_roll: int) -> float:
    """Return score for host: 1.0 win, 0.5 draw, 0.0 loss."""
    if host_roll > opp_roll:
        return 1.0
    if host_roll < opp_roll:
        return 0.0
    return 0.5

