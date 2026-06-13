# opensnake — Agent guide

## Structure

Single Python package under `src/opensnake/`. Entrypoint: `opensnake.cli:main` in `pyproject.toml`.

| Path | Role |
|---|---|
| `cli.py` | Typer CLI (`once`, `daemon`, `status`, `install`, `uninstall`, `config`) |
| `daemon.py` | Unix socket listener (asyncio), spawns/kills game subprocess |
| `config.py` | `GameConfig` dataclass, JSON load/save at `~/.config/opensnake/config.json` |
| `game/engine.py` | Snake grid, collision, scoring, letter spawning (pure logic, no pygame) |
| `game/renderer.py` | Pygame + XShape (X11) / NSWindow (macOS) transparency |
| `logo.py` | OPENCODE letter bitmap definitions |
| `hooks/opensnake.ts` | opencode plugin installed to `~/.config/opencode/plugins/` |

Socket: `$XDG_RUNTIME_DIR/opensnake.sock` (falls back to `TMPDIR`, then `/tmp`).

## Commands

```bash
# dev — use hatch scripts (defined in pyproject.toml under [tool.hatch.envs.default.scripts])
hatch run lint          # ruff check --fix
hatch run format        # ruff format
hatch run lint-check    # ruff check (read-only)
hatch run format-check  # ruff format --check
hatch run test          # pytest
hatch run typecheck     # mypy (src only, strict)
hatch run validate      # lint -> format -> test -> typecheck
hatch run check         # lint-check -> format-check -> test -> typecheck

# CI runs: uv sync --frozen --no-dev --group lint then uv run --no-sync <tool>
# same for --group test
```

## Conventions

- **ruff**: line-length 80, double quotes, target py311
- **mypy**: strict, checks `src/` only (excludes `tests/`)
- **Coverage**: `fail_under = 27` — only engine + config are unit-testable; renderer/daemon require display and aren't tested
- **pytest**: `--tb=short --strict-markers --cov --cov-report=term-missing`, `pythonpath = ["src"]`
- **uv required-version = "0.11.18"**, hatchling build backend

## Release flow

1. Bump version in `pyproject.toml`
2. Manual trigger `create_draft_release` workflow → creates `release/vX.Y.Z` branch + draft release
3. Publishing the draft triggers `pypi` workflow → `uv build` → publish to PyPI

## Platform notes

- XShape transparency on X11, NSWindow on macOS, graceful fallback on Wayland/headless
- Game window: NOFRAME fullscreen, always-on-top
- 60s orphan watchdog in daemon (`TIMEOUT_MS`)
- 5s game-over display (`GAMEOVER_DISPLAY_MS`)
