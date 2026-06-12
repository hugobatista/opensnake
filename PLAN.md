# snake-eater 🐍🎮

Desktop snake game that eats your screen while an AI coding agent is processing.

## Core mechanic

```
Agent starts "thinking"
  → opencode plugin sends "start" via Unix socket
  → snake-eater daemon opens Pygame window (NOFRAME, always-on-top)
  → Screenshot captured (one shot at game start)
  → Snake moves, marking 16×16px grid cells as eaten
  → Eaten cells show as dark "void"
  → Untouched areas show original screenshot

Agent goes idle
  → opencode plugin sends "stop" via Unix socket
  → Window closes, score displayed

Score = % of screen pixels eaten
```

No OCR, no character detection, no terminal dependency. Works with any app on screen.

## Architecture

```
opencode plugin ── Unix socket ──→ snake-eater daemon ──→ Pygame window
  (TypeScript)     $XDG_RUNTIME_DIR/   (Python/asyncio)   (NOFRAME, ontop)
                                      │
                                  Screenshot capture
                                  (gnome-screenshot → grim → spectacle → portal)
```

### Components

| Component | Language | Role |
|---|---|---|
| `opencode plugin` | TypeScript (~80 lines) | Hooks `session.status`/`session.idle`, sends `start`/`stop` to socket; template at `plugins/opencode-plugin.ts` |
| `daemon.py` | Python/asyncio | Unix socket listener, manages game lifecycle |
| `game/engine.py` | Python | Snake grid (16×16px cells), mask (bool[][]), collision, scoring |
| `game/renderer.py` | Python | Pygame: blits screenshot bg, applies mask, draws snake + HUD |
| `screenshot.py` | Python | Captures full screen via fallback chain |
| `cli.py` | Python (Typer) | Commands: install, daemon, once, status |
| `config.py` | Python | XDG paths, settings |

### IPC protocol

Unix socket at `$XDG_RUNTIME_DIR/snake-eater.sock`

```json
→ {"action": "start"}   → daemon opens game window
← {"status": "ok"}

→ {"action": "stop"}    → daemon closes window, logs score
← {"status": "ok"}

→ {"action": "ping"}    → health check
← {"status": "ok"}
```

## CLI

```
snake-eater install opencode      → writes ~/.config/opencode/plugins/snake-game.ts
snake-eater uninstall opencode     → removes plugin file
snake-eater daemon                 → starts background socket listener
snake-eater once                   → launches game immediately (for testing)
snake-eater status                 → check if daemon is running
```

## Project structure

```
~/code/projects/snake-eater/
├── pyproject.toml
├── README.md
├── PLAN.md
├── src/
│   └── snake_eater/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── config.py
│       ├── daemon.py
│       ├── screenshot.py
│       └── game/
│           ├── __init__.py
│           ├── engine.py
│           └── renderer.py
├── tests/
│   ├── __init__.py
│   ├── test_engine.py
│   ├── test_config.py
│   └── test_screenshot.py
└── plugins/
    └── opencode-plugin.ts   # Template for opencode plugin (shipped with package)
```

## Game engine design

| Concept | Detail |
|---|---|
| **Grid** | Window divided into `CELL`-sized squares (default 16×16 px) |
| **Mask** | `bool[][]` — `True` = eaten (void), `False` = screenshot visible |
| **Snake** | Classic grid-based snake. Head moves 1 cell per tick. |
| **Eating** | Snake head enters a new cell → marks it eaten → `score += 1` |
| **Collision** | Wall or self → game over (snake shrinks, score frozen) |
| **End** | Session goes idle → show score overlay, close after 5s |
| **Timeout** | No "stop" received after 60s → auto-close (safety for orphan sessions) |

### Renderer per-frame logic

```
1. Blit screenshot to screen
2. Iterate mask grid: for each eaten cell, draw dark void pixel
3. Draw snake (head = bright green #00ff66, body = gradient green)
4. Draw HUD: score "% eaten", timer, "AI working..." / "DONE"
```

## Screenshot fallback chain

```python
def capture() -> str:
    # Returns path to captured PNG
    # Try in order:
    1. gnome-screenshot -f /tmp/snake-eater/capture.png     # GNOME
    2. grim /tmp/snake-eater/capture.png                     # wlroots
    3. spectacle --background --output ...                    # KDE
    4. xdg-desktop-portal D-Bus API                           # universal fallback
```

## Dependencies

```toml
[project]
dependencies = [
    "pygame>=2.6,<3.0",
    "typer>=0.12,<1.0",
    "dbus-next>=0.2.3,<1.0",
]
# Screenshot tools called via subprocess:
#   gnome-screenshot, grim, spectacle, or dbus-next for portal

[tool.hatch.envs.default]
dependencies = [
    "pytest>=8.0,<9.0",
    "pytest-cov>=5.0,<6.0",
]
```

## Risks and mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| Wayland screenshot shows permission dialog | Medium | Document one-time dialog; cache permission |
| Always-on-top fails on GNOME mutter | Medium | `wmctrl` best-effort; document alt-tab as fallback |
| Multiple opencode sessions spam signals | Low | Daemon singleton via PID file; idempotent start/stop |
| Orphan daemon on crash | Low | Auto-close after 60s no input; 5min idle exit |
| HiDPI scaling mismatch | Low | Downscale screenshot to window size |
| Headless/no display | Low | Detect `$DISPLAY`/`$WAYLAND_DISPLAY`, exit gracefully |

## Extensibility (future)

Other agents just need to send JSON to the Unix socket:

```bash
# Claude Code adapter
echo '{"action":"start"}' | socat - UNIX-CONNECT:$XDG_RUNTIME_DIR/snake-eater.sock
claude "$@"
echo '{"action":"stop"}' | socat - UNIX-CONNECT:$XDG_RUNTIME_DIR/snake-eater.sock
```

`snake-eater install claude-code` would create this wrapper.

## Implementation phases

| Phase | What | Verification |
|---|---|---|
| **1** | Scaffold: pyproject.toml, .gitignore, src/ layout, tests/ | `hatch run check` passes |
| **2** | Game engine: engine.py + unit tests | `hatch run test` covers grid, mask, snake, collision, scoring |
| **3** | Screenshot + Renderer: screenshot.py (fallback chain) + renderer.py (pygame window) | Manual: `snake-eater once` opens window with live screenshot |
| **4** | Daemon: daemon.py + config.py + tests | `hatch run test` covers socket messages, lifecycle |
| **5** | CLI: cli.py (Typer) + __main__.py | All commands return expected output |
| **6** | opencode plugin: opencode-plugin.ts | Plugin appears in opencode, sends signals on thinking/idle |
| **7** | Integration: end-to-end with simulated opencode | Full flow: plugin → socket → daemon → game → window → score |
| **8** | Polish: README, packaging, edge cases | `hatch run validate` passes, installs cleanly via pip |

## Author

For pyproject.toml: `{ name = "Hugo Batista <code at hugobatista.com>" }` — confirm before writing.
