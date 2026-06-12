import random
from dataclasses import dataclass, field
from enum import StrEnum, auto

from opensnake.logo import CHAR_H, CHAR_W, Logo


class Direction(StrEnum):
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()


class GameState(StrEnum):
    PLAYING = auto()
    DEAD = auto()


_OPPOSITE: dict[Direction, Direction] = {
    Direction.UP: Direction.DOWN,
    Direction.DOWN: Direction.UP,
    Direction.LEFT: Direction.RIGHT,
    Direction.RIGHT: Direction.LEFT,
}


@dataclass
class Letter:
    name: str
    grid_x: int
    grid_y: int
    collected: bool = False

    def __post_init__(self) -> None:
        self._bitmap = Logo.letter_at(self.name, 1, 1)

    @property
    def width(self) -> int:
        return CHAR_W

    @property
    def height(self) -> int:
        return CHAR_H

    def occupies(self, gx: int, gy: int) -> bool:
        lx = gx - self.grid_x
        ly = gy - self.grid_y
        if 0 <= lx < self.width and 0 <= ly < self.height:
            return self._bitmap[ly][lx]
        return False


@dataclass
class Snake:
    body: list[tuple[int, int]] = field(default_factory=list)
    direction: Direction = Direction.RIGHT
    _grow_pending: int = 0

    @classmethod
    def starting_at(cls, x: int, y: int, length: int = 3) -> "Snake":
        return cls(body=[(x - i, y) for i in range(length)])

    @property
    def head(self) -> tuple[int, int]:
        return self.body[0]

    def move(self) -> tuple[int, int]:
        hx, hy = self.head
        dx, dy = {
            Direction.UP: (0, -1),
            Direction.DOWN: (0, 1),
            Direction.LEFT: (-1, 0),
            Direction.RIGHT: (1, 0),
        }[self.direction]
        new_head = (hx + dx, hy + dy)
        self.body.insert(0, new_head)
        if self._grow_pending > 0:
            self._grow_pending -= 1
        else:
            self.body.pop()
        return new_head

    def grow(self, cells: int) -> None:
        self._grow_pending += cells

    def collides_with(self, pos: tuple[int, int]) -> bool:
        return pos in self.body

    def collides_with_self(self, pos: tuple[int, int]) -> bool:
        return pos in self.body[1:]

    def change_direction(self, new_dir: Direction) -> None:
        if _OPPOSITE.get(new_dir) != self.direction:
            self.direction = new_dir


class Engine:
    def __init__(self, grid_w: int, grid_h: int) -> None:
        self.grid_w = grid_w
        self.grid_h = grid_h
        self.snake = Snake.starting_at(grid_w // 2, grid_h // 2)
        self.letters: list[Letter] = []
        self.score = 0
        self.state = GameState.PLAYING
        self.respawn_letters()

    def tick(self) -> None:
        if self.state != GameState.PLAYING:
            return
        new_head = self.snake.move()
        x, y = new_head
        hit_wall = not (0 <= x < self.grid_w and 0 <= y < self.grid_h)
        if hit_wall or self.snake.collides_with_self(new_head):
            self.state = GameState.DEAD
            return
        for letter in self.letters:
            nx, ny = new_head
            if not letter.collected and letter.occupies(nx, ny):
                letter.collected = True
                self.score += 100
                self.snake.grow(3)
                break
        if self.all_collected():
            self.respawn_letters()

    def all_collected(self) -> bool:
        return all(letter.collected for letter in self.letters)

    def respawn_letters(self) -> None:
        placements = ["O", "P", "E", "N", "C", "O", "D", "E"]
        self.letters.clear()
        occupied = set(self.snake.body)
        for name in placements:
            for _ in range(100):
                gx = random.randint(0, max(0, self.grid_w - CHAR_W))
                gy = random.randint(0, max(0, self.grid_h - CHAR_H))
                letter = Letter(name, gx, gy)
                cells = {
                    (cx, cy)
                    for cx in range(gx, gx + CHAR_W)
                    for cy in range(gy, gy + CHAR_H)
                    if letter.occupies(cx, cy)
                }
                if not cells.intersection(occupied):
                    self.letters.append(letter)
                    occupied.update(cells)
                    break
