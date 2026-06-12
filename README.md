# opensnake 🐍

Desktop snake game that plays on a transparent overlay while opencode is processing. The snake eats OPENCODE letters rendered in ASCII block art, scoring points for each letter collected.

## How it works

When opencode starts "thinking," the game opens a fullscreen borderless window with a screenshot of your desktop as the background — creating the illusion of a transparent overlay. The snake moves on a grid, eating OPENCODE letters that appear at random positions. Each letter eaten scores 100 points and the snake grows by 3 cells.

When opencode goes idle, the scoreboard is shown for 5 seconds and the window closes. The ESC key exits at any time.

The OPENCODE logo is rendered using the same Unicode block characters as the opencode TUI (`█` `▀` `▄` `_` `^` `~`).

## Installation

```bash
# From source
pip install opensnake

# Or in development mode
git clone https://github.com/yourname/opensnake
cd opensnake
uv sync
```

## Usage

```bash
# Launch game once (for testing)
opensnake once

# Start background socket daemon (for opencode integration)
opensnake daemon

# Check if daemon is running
opensnake status

# Install the opencode hook
opensnake install

# Remove the opencode hook
opensnake uninstall
```

### opencode integration

```bash
opensnake install   # writes hooks/opensnake.ts to ~/.config/opencode/hooks/
opensnake daemon    # starts the Unix socket listener
```

The hook sends `start`/`stop` signals to the daemon's Unix socket at `$XDG_RUNTIME_DIR/opensnake.sock` when opencode starts/stops thinking.

## Development

```bash
uv sync            # create venv and install deps
hatch run lint     # auto-fix lint issues
hatch run test     # run pytest with coverage
hatch run check    # full suite: lint + format + test + typecheck
```

### Project structure

```
src/opensnake/
├── cli.py          # Typer CLI (daemon, once, status, install, uninstall)
├── config.py       # XDG paths, settings
├── daemon.py       # Unix socket listener, game lifecycle
├── logo.py         # OPENCODE ASCII art letter definitions
├── __main__.py     # Entry point
└── game/
    ├── engine.py   # Snake grid, letter placement, collision, scoring
    └── renderer.py # Pygame: screenshot background, letters, snake, HUD
tests/
└── hooks/
    └── opensnake.ts  # opencode hook template
```
