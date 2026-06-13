from typing import ClassVar

CHAR_W = 4
CHAR_H = 4

_BLOCK = frozenset({"█", "▀", "▄", "^", "~"})
_FULL = frozenset({"█"})
_UPPER = frozenset({"▀", "^", "~"})
_LOWER = frozenset({"▄"})


class Logo:
    LETTERS: ClassVar[dict[str, list[str]]] = {
        "O": ["    ", "█▀▀█", "█__█", "▀▀▀▀"],
        "P": ["    ", "█▀▀█", "█__█", "█▀▀▀"],
        "E": ["    ", "█▀▀█", "█^^^", "▀▀▀▀"],
        "N": ["    ", "█▀▀▄", "█__█", "▀~~▀"],
        "C": [" ▄  ", "█▀▀▀", "█___", "▀▀▀▀"],
        "D": ["    ", "█▀▀█", "█__█", "▀▀▀▀"],
    }

    @classmethod
    def letter_at(cls, name: str, cell_w: int, cell_h: int) -> list[list[bool]]:
        pattern = cls.LETTERS[name]
        bitmap: list[list[bool]] = []
        for row in pattern:
            for _ in range(cell_h):
                pixel_row: list[bool] = []
                for ch in row:
                    inked = ch in _BLOCK
                    for _ in range(cell_w):
                        pixel_row.append(inked)
                bitmap.append(pixel_row)
        return bitmap
