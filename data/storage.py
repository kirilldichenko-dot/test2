import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict


@dataclass(frozen=True)
class StoragePaths:
    base_dir: Path

    @property
    def users(self) -> Path:
        return self.base_dir / "users.json"

    @property
    def games(self) -> Path:
        return self.base_dir / "games.json"

    @property
    def friends(self) -> Path:
        return self.base_dir / "friends.json"

    @property
    def leaderboard(self) -> Path:
        return self.base_dir / "leaderboard.json"

    @property
    def game_stats(self) -> Path:
        return self.base_dir / "game_stats.json"

    @property
    def settings(self) -> Path:
        return self.base_dir / "settings.json"


def _project_root() -> Path:
    # storage.py lives in <root>/data/storage.py
    return Path(__file__).resolve().parents[1]


def get_paths() -> StoragePaths:
    base = _project_root() / "data"
    return StoragePaths(base_dir=base)


def _default_json_for(name: str) -> Dict[str, Any]:
    if name == "users.json":
        return {"users": {}}
    if name == "games.json":
        return {"games": {}}
    if name == "friends.json":
        return {"friends": {}}
    if name == "leaderboard.json":
        return {"top": []}
    if name == "game_stats.json":
        return {"stats": {}}
    if name == "settings.json":
        return {"settings": {}}
    return {}


def ensure_data_files_exist() -> None:
    paths = get_paths()
    paths.base_dir.mkdir(parents=True, exist_ok=True)

    for p in (paths.users, paths.games, paths.leaderboard, paths.game_stats, paths.settings, paths.friends):
        if not p.exists():
            write_json(p, _default_json_for(p.name))


def read_json(path: Path) -> Dict[str, Any]:
    ensure_data_files_exist()
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        # If file got corrupted, back it up and recreate empty structure.
        backup = path.with_suffix(path.suffix + ".bak")
        try:
            os.replace(path, backup)
        except OSError:
            pass
        data = _default_json_for(path.name)
        write_json(path, data)
        return data


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    os.replace(tmp, path)

