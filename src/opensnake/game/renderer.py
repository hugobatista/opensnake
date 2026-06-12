import ctypes
import os
import platform
from enum import StrEnum, auto
from typing import Any

import pygame

from opensnake.game.engine import Direction, Engine, GameState
from opensnake.logo import INK, Logo

CELL_SIZE = 32
TICK_MS = 150


class Key(StrEnum):
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()
    ESC = auto()


_DIR_MAP = {
    pygame.K_UP: Direction.UP,
    pygame.K_DOWN: Direction.DOWN,
    pygame.K_LEFT: Direction.LEFT,
    pygame.K_RIGHT: Direction.RIGHT,
}

_KEY_MAP: dict[int, Key] = {
    pygame.K_UP: Key.UP,
    pygame.K_DOWN: Key.DOWN,
    pygame.K_LEFT: Key.LEFT,
    pygame.K_RIGHT: Key.RIGHT,
    pygame.K_ESCAPE: Key.ESC,
}


# ── X11 XShape transparency (Linux) ──────────────────────────────────


class _XRect(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_short),
        ("y", ctypes.c_short),
        ("width", ctypes.c_ushort),
        ("height", ctypes.c_ushort),
    ]


_XSHAPE: dict[str, Any] | None = None


def _xshape_setup() -> dict[str, Any] | None:
    if platform.system() != "Linux":
        return None
    try:
        x11 = ctypes.cdll.LoadLibrary("libX11.so.6")
        xext = ctypes.cdll.LoadLibrary("libXext.so.6")
    except Exception:
        return None

    x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
    x11.XOpenDisplay.restype = ctypes.c_void_p
    raw = x11.XOpenDisplay(None)
    if not raw:
        return None
    display = ctypes.c_void_p(raw) if isinstance(raw, int) else raw

    x11.XFlush.argtypes = [ctypes.c_void_p]
    x11.XFlush.restype = ctypes.c_int

    wm_info = pygame.display.get_wm_info()
    x_window = ctypes.c_ulong(wm_info.get("window", 0))
    if not x_window.value:
        x11.XCloseDisplay(display)
        return None

    combine = xext.XShapeCombineRectangles
    combine.argtypes = [
        ctypes.c_void_p,
        ctypes.c_ulong,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(_XRect),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
    ]
    combine.restype = None

    # Make the entire window transparent initially
    combine(display, x_window, 0, 0, 0, None, 0, 0, 0)
    x11.XFlush(display)

    return {
        "display": display,
        "window": x_window,
        "combine": combine,
        "x11": x11,
    }


_RectList = list[tuple[int, int, int, int]]


def _xshape_apply(xshape: dict[str, Any] | None, rects: _RectList) -> None:
    if xshape is None:
        return
    combine = xshape["combine"]
    gpu_rects = (_XRect * len(rects))()
    for i, (x, y, w, h) in enumerate(rects):
        gpu_rects[i].x = ctypes.c_short(x)
        gpu_rects[i].y = ctypes.c_short(y)
        gpu_rects[i].width = ctypes.c_ushort(w)
        gpu_rects[i].height = ctypes.c_ushort(h)
    combine(
        xshape["display"],
        xshape["window"],
        0,  # ShapeBounding
        0,
        0,
        gpu_rects,
        len(rects),
        0,  # ShapeSet
        0,  # Unsorted
    )
    xshape["x11"].XFlush(xshape["display"])


# ── macOS NSWindow transparency ─────────────────────────────────────


def _macos_setup() -> bool:
    if platform.system() != "Darwin":
        return False
    try:
        import ctypes.util

        wm_info = pygame.display.get_wm_info()
        ns_window = ctypes.c_void_p(wm_info.get("window", 0))
        if not ns_window.value:
            return False

        objc_path = ctypes.util.find_library("objc")
        if not objc_path:
            return False
        objc = ctypes.cdll.LoadLibrary(objc_path)
        objc.objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        objc.objc_msgSend.restype = ctypes.c_void_p

        sel_set_opaque = objc.sel_registerName(b"setOpaque:")
        sel_set_bg = objc.sel_registerName(b"setBackgroundColor:")
        sel_clear_color = objc.sel_registerName(b"clearColor")
        ns_color = objc.objc_getClass(b"NSColor")

        # Make window non-opaque with clear background
        opaque_variadic = objc.objc_msgSend
        opaque_variadic.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_bool,
        ]
        opaque_variadic.restype = None
        opaque_variadic(ns_window, sel_set_opaque, False)

        clr = objc.objc_msgSend(ns_color, sel_clear_color)
        bg_variadic = objc.objc_msgSend
        bg_variadic.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_void_p,
        ]
        bg_variadic.restype = None
        bg_variadic(ns_window, sel_set_bg, clr)

        return True
    except Exception:
        return False


# ── Renderer ─────────────────────────────────────────────────────────


class Renderer:
    def __init__(self) -> None:
        os.environ["SDL_VIDEO_X11_NET_WM_BYPASS_COMPOSITOR"] = "0"

        pygame.init()
        info = pygame.display.Info()
        self.w, self.h = info.current_w, info.current_h

        self.screen = pygame.display.set_mode(
            (self.w, self.h),
            pygame.NOFRAME | pygame.FULLSCREEN,
        )

        pygame.display.set_caption("opensnake")
        pygame.event.set_allowed([pygame.KEYDOWN, pygame.QUIT])
        self.clock = pygame.time.Clock()

        self._xshape = _xshape_setup()
        _macos_setup()

        self._draw_surf = pygame.Surface((self.w, self.h))

        g_w = self.w // CELL_SIZE
        g_h = self.h // CELL_SIZE
        self.engine = Engine(g_w, g_h)
        self.font = self._make_font(28)
        self.game_over_font = self._make_font(56)

    def _make_font(self, size: int) -> pygame.font.Font:
        try:
            return pygame.font.SysFont("monospace", size, bold=True)
        except Exception:
            return pygame.font.Font(None, size)

    def _ink_rects(self, gx: int, gy: int, pattern: list[str]) -> _RectList:
        rects: list[tuple[int, int, int, int]] = []
        bx = gx * CELL_SIZE
        by = gy * CELL_SIZE
        for ly, line in enumerate(pattern):
            for lx, ch in enumerate(line):
                if ch in INK:
                    rects.append(
                        (
                            bx + lx * CELL_SIZE,
                            by + ly * CELL_SIZE,
                            CELL_SIZE,
                            CELL_SIZE,
                        )
                    )
        return rects

    def _draw_letter(self, letter_name: str, gx: int, gy: int) -> None:
        pattern = Logo.LETTERS[letter_name]
        bx = gx * CELL_SIZE
        by = gy * CELL_SIZE
        for ly, line in enumerate(pattern):
            for lx, ch in enumerate(line):
                if ch in INK:
                    rx = bx + lx * CELL_SIZE
                    ry = by + ly * CELL_SIZE
                    rect = (rx, ry, CELL_SIZE, CELL_SIZE)
                    pygame.draw.rect(self._draw_surf, (180, 220, 255), rect)
                    pygame.draw.rect(self._draw_surf, (100, 160, 220), rect, 1)

    def _draw_snake(self) -> _RectList:
        rects: list[tuple[int, int, int, int]] = []
        cells = self.engine.snake.body
        for i, (gx, gy) in enumerate(cells):
            rect = (gx * CELL_SIZE, gy * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            rects.append(rect)
            if i == 0:
                color = (0, 255, 102)
                border = (0, 255, 130)
            else:
                t = i / max(len(cells) - 1, 1)
                g = int(255 * (1 - t * 0.6))
                b = int(100 * (1 - t * 0.5))
                color = (0, g, b)
                border = (0, min(g + 30, 255), min(b + 30, 255))
            pygame.draw.rect(self._draw_surf, color, rect)
            pygame.draw.rect(self._draw_surf, border, rect, 2)
        return rects

    def _draw_hud(self) -> _RectList:
        score_text = f"SCORE: {self.engine.score}"
        text_surf = self.font.render(score_text, True, (200, 200, 200))
        remaining = sum(
            1 for letter in self.engine.letters if not letter.collected
        )
        sub_surf = self.font.render(
            f"LETTERS: {remaining}", True, (150, 150, 150)
        )

        tx = self.w - text_surf.get_width() - 20
        ty = 20
        sx = self.w - sub_surf.get_width() - 20
        sy = 55

        self._draw_surf.blit(text_surf, (tx, ty))
        self._draw_surf.blit(sub_surf, (sx, sy))

        return [
            (tx, ty, text_surf.get_width(), text_surf.get_height()),
            (sx, sy, sub_surf.get_width(), sub_surf.get_height()),
        ]

    def _draw_game_over(self) -> None:
        overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self._draw_surf.blit(overlay, (0, 0))
        text = self.game_over_font.render("GAME OVER", True, (255, 100, 100))
        score = self.font.render(
            f"Final Score: {self.engine.score}", True, (255, 255, 255)
        )
        hint = self.font.render("ESC to close", True, (150, 150, 150))
        cx = self.w // 2
        tw = text.get_width()
        sw = score.get_width()
        hw = hint.get_width()
        self._draw_surf.blit(text, (cx - tw // 2, self.h // 2 - 80))
        self._draw_surf.blit(score, (cx - sw // 2, self.h // 2))
        self._draw_surf.blit(hint, (cx - hw // 2, self.h // 2 + 50))

    def run(self) -> int:
        running = True
        game_over_start: float | None = None
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.engine.state == GameState.DEAD:
                            running = False
                        else:
                            self.engine.state = GameState.DEAD
                    elif (
                        event.key in _DIR_MAP
                        and self.engine.state == GameState.PLAYING
                    ):
                        self.engine.snake.change_direction(_DIR_MAP[event.key])

            if self.engine.state == GameState.PLAYING:
                self.engine.tick()

            self._draw_surf.fill((0, 0, 0))
            shape_rects: _RectList = []

            for letter in self.engine.letters:
                if not letter.collected:
                    self._draw_letter(letter.name, letter.grid_x, letter.grid_y)
                    pat = Logo.LETTERS[letter.name]
                    gx, gy = letter.grid_x, letter.grid_y
                    shape_rects.extend(self._ink_rects(gx, gy, pat))

            shape_rects.extend(self._draw_snake())

            if self.engine.state == GameState.DEAD:
                self._draw_game_over()
                shape_rects.append((0, 0, self.w, self.h))
                if game_over_start is None:
                    game_over_start = pygame.time.get_ticks()
                elif pygame.time.get_ticks() - game_over_start >= 5000:
                    running = False

            hud_rects = self._draw_hud()
            shape_rects.extend(hud_rects)

            _xshape_apply(self._xshape, shape_rects)

            self.screen.blit(self._draw_surf, (0, 0))
            pygame.display.flip()
            self.clock.tick_busy_loop(1000 // TICK_MS)

        pygame.display.quit()
        pygame.quit()
        return self.engine.score
