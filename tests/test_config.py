from pathlib import Path

from opensnake.config import (
    GAMEOVER_DISPLAY_MS,
    PID_PATH,
    PLUGIN_DIR,
    PLUGIN_FILE,
    SOCKET_PATH,
    TIMEOUT_MS,
    GameConfig,
)


def test_socket_path_is_absolute() -> None:
    assert isinstance(SOCKET_PATH, Path)
    assert str(SOCKET_PATH).endswith("opensnake.sock")


def test_pid_path_is_absolute() -> None:
    assert isinstance(PID_PATH, Path)
    assert str(PID_PATH).endswith("opensnake.pid")


def test_plugin_paths() -> None:
    assert str(PLUGIN_FILE).endswith("opensnake.ts")
    assert str(PLUGIN_DIR).endswith("plugins")


def test_constants_are_positive() -> None:
    assert TIMEOUT_MS > 0
    assert GAMEOVER_DISPLAY_MS > 0


def test_timeout_longer_than_gameover() -> None:
    assert TIMEOUT_MS > GAMEOVER_DISPLAY_MS


def test_game_config_defaults() -> None:
    cfg = GameConfig()
    assert cfg.opacity == 0.6
    assert cfg.tick_ms == 80
    assert cfg.cell_size == 32
    assert cfg.letter_count == 100
    assert cfg.initial_letters == 10
    assert cfg.spawn_interval_ms == 3000
    assert "O" in cfg.gray_map


def test_game_config_to_dict() -> None:
    cfg = GameConfig()
    d = cfg.to_dict()
    assert d["opacity"] == 0.6
    assert d["letter_count"] == 100


def test_config_file_roundtrip(tmp_path: Path) -> None:
    cfg = GameConfig()
    cfg.opacity = 0.7
    cfg.tick_ms = 200
    cfg.letter_count = 36
    assert cfg.opacity == 0.7
    assert cfg.tick_ms == 200
    assert cfg.letter_count == 36
