# opensnake 🐍

Desktop snake game that plays on a transparent overlay while opencode is
processing. The snake eats OPENCODE letters rendered in ASCII block art
(matching the opencode TUI logo), scoring points for each letter collected.

## How it works

When opencode starts processing (`session.status` → `busy`), the plugin sends
"start" via a Unix socket. The daemon opens a fullscreen borderless Pygame
window. The window uses XShape (Linux) or NSWindow transparency (macOS) so
only game elements are visible — the desktop shows through everywhere else.

The snake moves on a grid. OPENCODE letters appear progressively (3 initially,
then one every 3 seconds up to 100). Each letter eaten scores 100 points and
the snake grows by 3 cells. ESC exits immediately. The 60-second daemon
timeout prevents orphan sessions.

The plugin auto-starts the daemon on load — no manual `opensnake daemon` needed.

## Installation

```bash
# From source (recommended)
git clone https://github.com/hugobatista/opensnake
cd opensnake
uv sync

# Install the opencode plugin
opensnake install
```

Restart opencode to load the plugin. That's it — the daemon starts
automatically.

## Usage

```bash
# Launch game once (for testing, no daemon needed)
opensnake once

# Manual daemon control (usually auto-started by plugin)
opensnake daemon
opensnake status

# Plugin management
opensnake install
opensnake uninstall

# View or regenerate config
opensnake config
```

### CLI flags

```bash
opensnake once --opacity 0.85 --tick-ms 120 --letter-count 50
```

## Configuration

Optional file at `~/.config/opensnake/config.json`:

```json
{
  "opacity": 0.8,
  "tick_ms": 80,
  "cell_size": 32,
  "letter_count": 100,
  "initial_letters": 10,
  "spawn_interval_ms": 3000,
  "gray_map": {
    "O": [180, 220],
    "P": [160, 200],
    "E": [200, 240],
    "N": [140, 180],
    "C": [210, 250],
    "D": [170, 210]
  }
}
```

| Field | Default | Description |
|---|---|---|
| `opacity` | 0.8 | Window opacity (0.0–1.0) |
| `tick_ms` | 80 | Snake speed (lower = faster) |
| `cell_size` | 32 | Grid cell size in pixels |
| `letter_count` | 100 | Maximum letters on screen |
| `initial_letters` | 10 | Letters at game start |
| `spawn_interval_ms` | 3000 | How often a new letter appears |
| `gray_map` | (per letter) | Fill/border gray values per letter |

## Development

```bash
uv sync
hatch run lint      # auto-fix lint issues
hatch run test      # run pytest with coverage
hatch run check     # full suite: lint + format + test + typecheck
```

## Project structure

```
src/opensnake/
├── cli.py          # Typer CLI (daemon, once, status, install, uninstall, config)
├── config.py       # GameConfig dataclass, JSON config load/save
├── daemon.py       # Unix socket listener, game lifecycle, PID singleton
├── logo.py         # OPENCODE ASCII art letter definitions
├── __main__.py     # Entry point
└── game/
    ├── engine.py   # Snake grid, progressive letter spawning, collision, scoring
    └── renderer.py # Pygame: XShape transparency, logo rendering, snake, HUD
hooks/
└── opensnake.ts    # opencode Plugin (auto-starts daemon, sends start/stop)
tests/
├── test_config.py
└── test_engine.py
```
