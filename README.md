# opensnake 🐍

[![GitHub Tag](https://img.shields.io/github/v/tag/hugobatista/opensnake?logo=github&label=latest)](https://go.hugobatista.com/gh/hugobatista/opensnake/releases)
[![Lint](https://img.shields.io/github/actions/workflow/status/hugobatista/opensnake/lint.yml?label=Lint)](https://go.hugobatista.com/gh/hugobatista/opensnake/actions/workflows/lint.yml)
[![Test](https://img.shields.io/github/actions/workflow/status/hugobatista/opensnake/test.yml?label=Test)](https://go.hugobatista.com/gh/hugobatista/opensnake/actions/workflows/test.yml)
[![PyPI - Version](https://img.shields.io/pypi/v/opensnake.svg)](https://pypi.org/project/opensnake)
[![Renovate](https://img.shields.io/badge/renovate-enabled-brightgreen?logo=renovatebot)](https://docs.renovatebot.com)

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
# Via pip
pip install opensnake

# Or via uv tool
uv tool install opensnake

# Or from source
git clone https://github.com/hugobatista/opensnake
cd opensnake
uv sync
```

After installing, register the opencode plugin and restart opencode:

```bash
opensnake install
```

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

