import shutil
from pathlib import Path

import typer

from opensnake.config import (
    CONFIG_FILE,
    PLUGIN_DIR,
    PLUGIN_FILE,
    GameConfig,
    load_config,
    save_config,
)

desc = "opensnake — transparent overlay snake game for opencode"
app = typer.Typer(help=desc)


@app.command()
def once(
    opacity: float = typer.Option(
        None,
        "--opacity",
        min=0.0,
        max=1.0,
        help="Window opacity (0.0-1.0). Overrides config file.",
    ),
    tick_ms: int = typer.Option(
        None,
        "--tick-ms",
        min=20,
        help="Snake speed in ms per tick (lower = faster).",
    ),
    letter_count: int = typer.Option(
        None,
        "--letter-count",
        min=1,
        help="Maximum letters on screen. Overrides config file.",
    ),
) -> None:
    """Launch the game immediately (for testing)."""
    cfg = load_config()
    if opacity is not None:
        cfg.opacity = opacity
    if tick_ms is not None:
        cfg.tick_ms = tick_ms
    if letter_count is not None:
        cfg.letter_count = letter_count

    from opensnake.game.renderer import Renderer

    Renderer(cfg).run()


@app.command()
def daemon() -> None:
    """Start the background socket listener daemon."""
    from opensnake.daemon import run_daemon

    run_daemon()


@app.command()
def status() -> None:
    """Check if the daemon is running."""
    from opensnake.daemon import Daemon

    if Daemon.is_running():
        typer.echo("opensnake daemon is running")
    else:
        typer.echo("opensnake daemon is not running")


@app.command()
def install() -> None:
    """Install the opencode plugin file."""
    PLUGIN_DIR.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).resolve().parent.parent.parent
    src = root / "hooks" / "opensnake.ts"
    if not src.exists():
        typer.echo("plugin file not found, skipping", err=True)
        raise typer.Exit(1)
    shutil.copy2(str(src), str(PLUGIN_FILE))
    typer.echo(f"installed plugin to {PLUGIN_FILE}")


@app.command()
def uninstall() -> None:
    """Remove the opencode plugin file."""
    if PLUGIN_FILE.exists():
        PLUGIN_FILE.unlink()
        typer.echo("plugin removed")
    else:
        typer.echo("plugin not found")


@app.command()
def config() -> None:
    """Print or generate the default config file."""
    if CONFIG_FILE.exists():
        typer.echo(CONFIG_FILE.read_text())
    else:
        cfg = GameConfig()
        save_config(cfg)
        typer.echo(f"wrote default config to {CONFIG_FILE}")


def main() -> None:
    app()
