import os
import tempfile
from pathlib import Path


def _xdg_runtime_dir() -> Path:
    base = (
        os.environ.get("XDG_RUNTIME_DIR")
        or os.environ.get("TMPDIR")
        or str(tempfile.gettempdir())
    )
    return Path(base)


SOCKET_PATH: Path = _xdg_runtime_dir() / "opensnake.sock"
PID_PATH: Path = _xdg_runtime_dir() / "opensnake.pid"
HOOK_DIR: Path = Path.home() / ".config" / "opencode" / "hooks"
HOOK_FILE: Path = HOOK_DIR / "opensnake.ts"

TICK_MS: int = 150
CELL_SIZE: int = 32
TIMEOUT_MS: int = 60_000
GAMEOVER_DISPLAY_MS: int = 5_000
