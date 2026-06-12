from pathlib import Path

from opensnake.config import (
    CELL_SIZE,
    GAMEOVER_DISPLAY_MS,
    HOOK_DIR,
    HOOK_FILE,
    PID_PATH,
    SOCKET_PATH,
    TICK_MS,
    TIMEOUT_MS,
)


def test_socket_path_is_absolute() -> None:
    assert isinstance(SOCKET_PATH, Path)
    assert str(SOCKET_PATH).endswith("opensnake.sock")


def test_pid_path_is_absolute() -> None:
    assert isinstance(PID_PATH, Path)
    assert str(PID_PATH).endswith("opensnake.pid")


def test_hook_paths() -> None:
    assert str(HOOK_FILE).endswith("opensnake.ts")
    assert str(HOOK_DIR).endswith("hooks")


def test_constants_are_positive() -> None:
    assert CELL_SIZE > 0
    assert TICK_MS > 0
    assert TIMEOUT_MS > 0
    assert GAMEOVER_DISPLAY_MS > 0


def test_timeout_longer_than_tick() -> None:
    assert TIMEOUT_MS > TICK_MS
    assert GAMEOVER_DISPLAY_MS > TICK_MS
