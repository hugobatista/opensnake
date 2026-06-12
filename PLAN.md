# opensnake 🐍

Desktop snake game that shows a transparent overlay while opencode is processing. The snake eats OPENCODE letters rendered in ASCII block art, scoring points for each letter collected.

## Core mechanic

```
opencode starts "thinking"
  → plugin sends "start" via Unix socket
  → opensnake daemon opens transparent Pygame window (NOFRAME, always-on-top, SRCALPHA)
  → Snake moves on a grid. OPENCODE letters are placed as collectible targets
  → Snake eats a letter → letter disappears → score += 100
  → Desktop is visible through transparent areas

opencode goes idle
  → plugin sends "stop" via Unix socket
  → Scoreboard overlay shown for 5s → window closes

ESC key at any time → game over → score shown → window closes
```

Score = points from letters eaten. Max score = 800 (8 letters × 100).

## Architecture

```
opencode plugin ── Unix socket ──→ opensnake daemon ──→ Pygame window
  (TypeScript)     $XDG_RUNTIME_DIR/   (Python/asyncio)   (NOFRAME, ontop, SRCALPHA)
```

No screenshot capture. No external screenshot tools. No D-Bus.

### Components

| Component | Language | Role |
|---|---|---|
| `opencode plugin` | TypeScript (~40 lines) | Hooks `session.status`/`session.idle`, sends `start`/`stop` to socket |
| `daemon.py` | Python/asyncio | Unix socket listener, manages game lifecycle |
| `game/engine.py` | Python | Snake grid, letter placement, collision, scoring |
| `game/renderer.py` | Python | Pygame: transparent surface, draws logo letters, snake, HUD |
| `cli.py` | Python (Typer) | Commands: daemon, once, status |
| `config.py` | Python | XDG paths, settings |

### IPC protocol

Unix socket at `$XDG_RUNTIME_DIR/opensnake.sock`

```json
→ {"action": "start"}   → daemon opens game window
← {"status": "ok"}

→ {"action": "stop"}    → daemon closes window, logs score
← {"status": "ok"}

→ {"action": "ping"}    → health check
← {"status": "ok"}
```

### opencode plugin hook

The plugin intercepts `session.status` and `session.idle` events. When the agent starts thinking (status transitions to `thinking`), it sends `start`. When the agent goes idle or completes, it sends `stop`. Plugin file lives at `~/.config/opencode/hooks/opensnake.ts` (opencode-plugin hook, not a full plugin).

## CLI

```
opensnake daemon    → starts background socket listener
opensnake once      → launches game immediately (for testing, no daemon needed)
opensnake status    → check if daemon is running
opensnake install   → installs the opencode hook file
opensnake uninstall → removes the hook file
```

## Project structure

```
~/code/projects/opensnake/
├── pyproject.toml
├── README.md
├── PLAN.md
├── src/
│   └── opensnake/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── config.py
│       ├── daemon.py
│       ├── logo.py         # OPENCODE ASCII art (matching opencode's logo.ts)
│       └── game/
│           ├── __init__.py
│           ├── engine.py
│           └── renderer.py
├── tests/
│   ├── __init__.py
│   ├── test_engine.py
│   └── test_config.py
└── hooks/
    └── opensnake.ts        # opencode hook (shipped with package)
```

## OPENCODE logo

Rendered using the same block characters as opencode's own TUI (`packages/tui/src/logo.ts`):

```
                    ▄     
█▀▀█ █▀▀█ █▀▀█ █▀▀▄ █▀▀▀ █▀▀█ █▀▀█ █▀▀█
█__█ █__█ █^^^ █__█ █___ █__█ █__█ █^^^
▀▀▀▀ █▀▀▀ ▀▀▀▀ ▀~~▀ ▀▀▀▀ ▀▀▀▀ ▀▀▀▀ ▀▀▀▀
```

Characters used: `█` (U+2588), `▀` (U+2580), `▄` (U+2584), `_`, `^`, `~`, ` `, `,`.

Each individual letter (O, P, E, N, C, O, D, E) is a separate collectible item. Letters are placed at fixed positions on the grid, or scattered randomly each game. A letter is collected when the snake head occupies any cell of that letter's bounding box.

After all 8 letters are eaten, a new set of letters respawns at new positions.

## Game engine design

| Concept | Detail |
|---|---|
| **Window** | Fullscreen transparent overlay with `pygame.SRCALPHA`, `NOFRAME`, always-on-top |
| **Background** | Fully transparent — desktop visible through the window |
| **Grid** | Window divided into `CELL`-sized squares (default 32×32 px) |
| **Snake** | Classic grid-based snake. Head moves 1 cell per tick. |
| **Letters** | Each OPENCODE letter occupies a bounding box (e.g., 4×4 cells per letter at a given scale). Letters are opaque blocks drawn on the transparent surface. |
| **Eating** | Snake head overlaps a letter's bounding box → letter removed → `score += 100` → snake grows by 3 cells |
| **Collision** | Wall or self → game over |
| **Controls** | Arrow keys to steer. ESC to exit immediately. |
| **End** | "stop" received → show scoreboard overlay for 5s → close. ESC → same. |
| **Timeout** | No "stop" after 60s → auto-close (safety for orphan sessions) |

### Renderer per-frame logic

```
1. Fill surface with transparent color (0,0,0,0)
2. Draw remaining OPENCODE letters (opaque white/colored blocks)
3. Draw snake (head = #00ff66, body = gradient green)
4. Draw HUD: "SCORE: N", "A-Z: OPENCODE letters remaining"
5. Flip display
```

## Letter rendering

Each letter is rendered as a bitmap using the same block-character pattern as the opencode logo. Each character in the ASCII art maps to a small block of pixels on screen (e.g., each char cell = 8×8 px). The overall logo at 4 lines × ~35 chars per line fits in a ~280×32 px area at 8px/char. We scale this up with a `CHAR_SIZE` constant.

Letters can be:
- **Fixed layout**: placed in predictable positions (e.g., scattered across the play field)
- **Random layout**: each game randomizes positions (avoiding overlap)

## Transparent overlay implementation

```python
import pygame

pygame.display.init()
# Set window to transparent
pygame.display.set_mode((width, height), pygame.NOFRAME)
hwnd = pygame.display.get_wm_info()["window"]
# Platform-specific transparency:
# Linux (X11): _NET_WM_WINDOW_OPACITY or compositor transparency
# macOS: NSWindow setOpaque:NO / setAlphaValue:
# Fallback: colorkey transparency on the surface
```

If native window transparency proves unreliable across platforms, use colorkey transparency:
- Set the window background to a specific colorkey (e.g., `#000001`)
- Draw everything else normally
- The colorkey makes unused areas completely transparent

## Scoreboard

- **During game**: top-right HUD showing current score (e.g., "SCORE: 300")
- **Game over**: centered overlay with final score, total letters eaten, "GAME OVER — Press ESC to close"
- **Session end**: same scoreboard auto-closes after 5s

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
| **Linux (X11)** | Set `_NET_WM_WINDOW_OPACITY` atom via `xprop` or set window colorkey via Pygame |
| **Linux (Wayland)** | Layer shell protocol (zwlr_layer_surface_v1) or colorkey fallback; `SDL_VIDEO_DRIVER=wayland` |
| **macOS** | Pygame window with colorkey transparency (most reliable cross-platform approach) |
| **Fallback** | Colorkey-based transparency works on all platforms via Pygame's `set_colorkey` |

## Risks and mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| Transparent overlay fails on some compositors | Medium | Colorkey fallback; document known-working setups |
| Multiple opencode sessions send conflicting signals | Low | Daemon singleton via PID file; idempotent start/stop |
| Orphan daemon on crash | Low | Auto-close after 60s no input; 5min idle exit |
| Headless/no display | Low | Detect `$DISPLAY`/`$WAYLAND_DISPLAY`, exit gracefully |
| Wayland layer-shell not available | Low | Fall back to colorkey transparency |

## Implementation phases

| Phase | What | Verification |
|---|---|---|
| **1** | Scaffold: pyproject.toml, .gitignore, src/ layout, logo.py (ASCII art data), tests/ | `hatch run check` passes |
| **2** | Game engine: engine.py + unit tests | `hatch run test` covers grid, snake, letter collision, scoring |
| **3** | Renderer: renderer.py (transparent Pygame window, logo rendering, snake drawing, HUD) | Manual: `opensnake once` opens transparent window with letters and snake |
| **4** | Daemon: daemon.py + config.py + tests | `hatch run test` covers socket messages, lifecycle |
| **5** | CLI: cli.py (Typer) + __main__.py | All commands return expected output |
| **6** | opencode hook: hooks/opensnake.ts | Hook fires on thinking/idle, signals reach daemon |
| **7** | Integration: end-to-end with simulated opencode | Full flow: hook → socket → daemon → game → window → score |
| **8** | Polish: README, packaging, edge cases | `hatch run validate` passes, installs cleanly via pip |

## Author

For pyproject.toml: `{ name = "Hugo Batista <code at hugobatista.com>" }` — confirm before writing.
