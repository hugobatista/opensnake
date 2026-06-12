import json
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def _xdg_runtime_dir() -> Path:
    base = (
        os.environ.get("XDG_RUNTIME_DIR")
        or os.environ.get("TMPDIR")
        or str(tempfile.gettempdir())
    )
    return Path(base)


SOCKET_PATH: Path = _xdg_runtime_dir() / "opensnake.sock"
PLUGIN_DIR: Path = Path.home() / ".config" / "opencode" / "plugins"
PLUGIN_FILE: Path = PLUGIN_DIR / "opensnake.ts"

TIMEOUT_MS: int = 60_000
GAMEOVER_DISPLAY_MS: int = 5_000

CONFIG_DIR: Path = (
    Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    / "opensnake"
)
CONFIG_FILE: Path = CONFIG_DIR / "config.json"

_DEFAULT_GRAY_MAP: dict[str, list[int]] = {
    "O": [180, 220],
    "P": [160, 200],
    "E": [200, 240],
    "N": [140, 180],
    "C": [210, 250],
    "D": [170, 210],
}


@dataclass
class GameConfig:
    opacity: float = 0.6
    tick_ms: int = 80
    cell_size: int = 32
    letter_count: int = 100
    initial_letters: int = 10
    spawn_interval_ms: int = 3000
    gray_map: dict[str, list[int]] = field(
        default_factory=lambda: dict(_DEFAULT_GRAY_MAP)
    )
    daemon_cmd: str = "opensnake"

    def to_dict(self) -> dict[str, Any]:
        return {
            "opacity": self.opacity,
            "tick_ms": self.tick_ms,
            "cell_size": self.cell_size,
            "letter_count": self.letter_count,
            "initial_letters": self.initial_letters,
            "spawn_interval_ms": self.spawn_interval_ms,
            "gray_map": dict(self.gray_map),
            "daemon_cmd": self.daemon_cmd,
        }


def load_config() -> GameConfig:
    cfg = GameConfig()
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text())
            if isinstance(data.get("opacity"), (int, float)):
                cfg.opacity = float(data["opacity"])
            if isinstance(data.get("tick_ms"), int):
                cfg.tick_ms = data["tick_ms"]
            if isinstance(data.get("cell_size"), int):
                cfg.cell_size = data["cell_size"]
            if isinstance(data.get("letter_count"), int):
                cfg.letter_count = data["letter_count"]
            if isinstance(data.get("initial_letters"), int):
                cfg.initial_letters = data["initial_letters"]
            if isinstance(data.get("spawn_interval_ms"), int):
                cfg.spawn_interval_ms = data["spawn_interval_ms"]
            if isinstance(data.get("gray_map"), dict):
                for k, v in data["gray_map"].items():
                    if isinstance(v, list) and len(v) == 2:
                        cfg.gray_map[str(k)] = [int(v[0]), int(v[1])]
            if isinstance(data.get("daemon_cmd"), str):
                cfg.daemon_cmd = data["daemon_cmd"]
        except Exception:
            pass
    return cfg


def save_config(cfg: GameConfig) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg.to_dict(), indent=2) + "\n")
