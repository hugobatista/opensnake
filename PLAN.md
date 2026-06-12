# opensnake 🐍

Desktop snake game that plays on a transparent overlay while opencode is
processing. The snake eats OPENCODE letters rendered in ASCII block art
(matching the opencode TUI logo), scoring points for each letter collected.

## Core mechanic

```
opencode starts processing (session.status → busy)
  → plugin sends "start" via Unix socket
  → opensnake daemon opens transparent Pygame window (NOFRAME, always-on-top)
  → Snake moves on a grid. OPENCODE letters appear progressively (3 initial,
    then 1 every 3s up to 100)
  → Snake eats a letter → letter disappears → score += 100 → snake grows 3
  → Desktop visible through XShape-transparent areas

opencode goes idle (session.idle or session.status → idle)
  → plugin sends "stop" via Unix socket
  → daemon kills game subprocess

ESC key at any time → game over → score shown → window closes
60s daemon timeout → auto-closes orphan sessions
```

## Architecture

```
opencode plugin ── Unix socket ──→ opensnake daemon ──→ Pygame window
  (TypeScript)     $XDG_RUNTIME_DIR/   (Python/asyncio)   (NOFRAME, XShape)
```

No screenshot capture. No external tools. No D-Bus.

### Plugin auto-starts daemon

The plugin (loaded by opencode on startup) reads `daemon_cmd` from the config
file and spawns the daemon via `Bun.spawn`. The daemon's own PID check
prevents duplicates. Users never need to run `opensnake daemon` manually.

### Components

| Component | Language | Role |
|---|---|---|
| `opencode plugin` | TypeScript (~50 lines) | Hooks `session.status`, sends `start`/`stop`; auto-starts daemon |
| `daemon.py` | Python/asyncio | Unix socket listener, manages game lifecycle and game subprocess |
| `game/engine.py` | Python | Snake grid, progressive letter spawning, collision, scoring |
| `game/renderer.py` | Python | Pygame: XShape transparency, logo letters, snake, HUD |
| `cli.py` | Python (Typer) | Commands: daemon, once, status, install, uninstall, config |
| `config.py` | Python | GameConfig dataclass, JSON config load/save |

### IPC protocol

Unix socket at `$XDG_RUNTIME_DIR/opensnake.sock`

```json
→ {"action": "start"}   → daemon opens game window
← {"status": "ok"}

→ {"action": "stop"}    → daemon kills game subprocess
← {"status": "ok"}

→ {"action": "ping"}    → health check
← {"status": "ok"}
```

## CLI

```
opensnake daemon      → starts background socket listener
opensnake once        → launches game immediately (for testing, no daemon)
opensnake once --opacity 0.8 --tick-ms 80 --letter-count 100
opensnake status      → check if daemon is running
opensnake install     → writes plugin to ~/.config/opencode/plugins/ + writes config
opensnake uninstall   → removes plugin file
opensnake config      → prints or generates default config at ~/.config/opensnake/config.json
```

## Game engine design

| Concept | Detail |
|---|---|
| **Window** | Fullscreen NOFRAME, always-on-top |
| **Transparency** | XShape (Linux X11): only game element rectangles are visible; NSWindow `setOpaque:NO` (macOS). Desktop shows through everywhere else. Window opacity via `_NET_WM_WINDOW_OPACITY` |
| **Grid** | Window divided into `CELL`-sized squares (default 32×32 px, configurable) |
| **Snake** | Classic grid-based snake. Head moves 1 cell per tick. |
| **Letters** | Each OPENCODE letter occupies a 4×4 cell bounding box. Rendered as ASCII block art with per-letter gray values (configurable in `gray_map`). |
| **Eating** | Snake head overlaps a letter's inked cell → letter removed → `score += 100` → snake grows by 3 cells |
| **Collision** | Wall or self → game over |
| **Controls** | Arrow keys to steer. ESC to exit immediately. |
| **Progressive spawn** | `initial_letters` (default 10) at start. Remaining letters placed one at a time every `spawn_interval_ms` (default 3s) up to `letter_count` (default 100). |
| **End** | "stop" received → daemon kills game. ESC → game over overlay → close. |
| **Timeout** | No "start" after 60s → daemon auto-kills game (safety for orphan sessions) |

### Renderer per-frame logic

```
1. Fill drawing surface with black
2. Draw remaining OPENCODE letters (grayscale blocks from gray_map)
3. Draw snake (head = #00ff66, body = gradient green)
4. Draw HUD: "SCORE: N", "LETTERS: N"
5. If game over: draw semi-transparent overlay + scoreboard
6. Compute XShape rectangles for all visible elements
7. Apply XShape (only visible elements are shown; desktop visible elsewhere)
8. Flip display
```

## OPENCODE logo

Rendered using the same block characters as opencode's own TUI (`packages/tui/src/logo.ts`):

```
                    ▄
█▀▀█ █▀▀█ █▀▀█ █▀▀▄ █▀▀▀ █▀▀█ █▀▀█ █▀▀█
█__█ █__█ █^^^ █__█ █___ █__█ █__█ █^^^
▀▀▀▀ █▀▀▀ ▀▀▀▀ ▀~~▀ ▀▀▀▀ ▀▀▀▀ ▀▀▀▀ ▀▀▀▀
```

Characters used: `█` (U+2588), `▀` (U+2580), `▄` (U+2584), `_`, `^`, `~`, ` `.

Each letter (O, P, E, N, C, D) is a separate collectible. Letters reuse across
the OPENCODE sequence (O and E appear twice).

## Configuration

Optional JSON file at `~/.config/opensnake/config.json`. All fields have defaults.

```json
{
  "opacity": 0.8,
  "tick_ms": 80,
  "cell_size": 32,
  "letter_count": 100,
  "initial_letters": 10,
  "spawn_interval_ms": 3000,
  "gray_map": { "O": [180, 220], "P": [160, 200], "E": [200, 240],
                "N": [140, 180], "C": [210, 250], "D": [170, 210] },
  "daemon_cmd": "opensnake"
}
```

`daemon_cmd` is set automatically by `opensnake install` to the resolved Python
path (e.g. `/path/to/.venv/bin/python -m opensnake`).

## Dependencies

```toml
[project]
name = "opensnake"
dependencies = [
    "pygame>=2.6,<3.0",
    "typer>=0.12,<1.0",
]

[tool.hatch.envs.default]
dependencies = [
    "pytest>=8.0,<9.0",
    "pytest-cov>=5.0,<6.0",
]
```

## Platform-specific transparency

| Platform | Method |
|---|---|
| **Linux (X11)** | XShape `CombineRectangles` for per-pixel visibility + `_NET_WM_WINDOW_OPACITY` for window translucency |
| **Linux (Wayland)** | Fallback: XWayland (XShape via XWayland) |
| **macOS** | NSWindow `setOpaque:NO` + clear background |

## Risks and mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| XShape fails without X11/compositor | Medium | Game still runs visually (no desktop transparency); `_xshape_setup` returns None gracefully |
| Multiple opencode sessions spam signals | Low | Daemon singleton via PID file; plugin `running` flag debounces duplicate busy events |
| Orphan daemon on crash | Low | Auto-kill game after 60s no input; persist daemon for 5min idle then exit |
| Headless/no display | Low | Detect `$DISPLAY`/`$WAYLAND_DISPLAY`, Pygame init fails gracefully |
| Wayland without XWayland | Low | No transparency fallback needed; game runs in windowed mode |
| Plugin daemon_cmd stale after reinstall | Low | `opensnake install` rewrites config with fresh path |

## Author

Hugo Batista <code at hugobatista.com>
