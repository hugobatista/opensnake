import shutil
from pathlib import Path

import typer

from opensnake.config import HOOK_DIR, HOOK_FILE

desc = "opensnake — transparent overlay snake game for opencode"
app = typer.Typer(help=desc)


@app.command()
def once() -> None:
    """Launch the game immediately (for testing)."""
    from opensnake.game.renderer import Renderer

    Renderer().run()


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
    """Install the opencode hook file."""
    HOOK_DIR.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).resolve().parent.parent.parent
    src = root / "hooks" / "opensnake.ts"
    if not src.exists():
        typer.echo("hook file not found, skipping", err=True)
        raise typer.Exit(1)
    shutil.copy2(str(src), str(HOOK_FILE))
    typer.echo(f"installed hook to {HOOK_FILE}")


@app.command()
def uninstall() -> None:
    """Remove the opencode hook file."""
    if HOOK_FILE.exists():
        HOOK_FILE.unlink()
        typer.echo("hook removed")
    else:
        typer.echo("hook not found")


def main() -> None:
    app()
