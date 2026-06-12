from opensnake.game.engine import Direction, Engine, GameState, Snake


def test_snake_starting_position() -> None:
    s = Snake.starting_at(10, 10, 3)
    assert s.body == [(10, 10), (9, 10), (8, 10)]
    assert s.direction == Direction.RIGHT


def test_snake_move_no_grow() -> None:
    s = Snake.starting_at(5, 5, 3)
    head = s.move()
    assert head == (6, 5)
    assert s.body == [(6, 5), (5, 5), (4, 5)]


def test_snake_grow() -> None:
    s = Snake.starting_at(5, 5, 3)
    s.grow(2)
    head = s.move()
    assert head == (6, 5)
    assert len(s.body) == 4
    head = s.move()
    assert head == (7, 5)
    assert len(s.body) == 5
    head = s.move()
    assert head == (8, 5)
    assert len(s.body) == 5


def test_snake_change_direction_valid() -> None:
    s = Snake.starting_at(5, 5, 3)
    s.change_direction(Direction.UP)
    assert s.direction == Direction.UP


def test_snake_change_direction_opposite_ignored() -> None:
    s = Snake.starting_at(5, 5, 3)
    s.change_direction(Direction.LEFT)
    assert s.direction == Direction.RIGHT


def test_snake_self_collision() -> None:
    s = Snake.starting_at(5, 5, 5)
    s.change_direction(Direction.DOWN)
    s.move()
    s.change_direction(Direction.LEFT)
    s.move()
    s.change_direction(Direction.UP)
    head = s.move()
    # head lands on the cell that was previously body[2]
    assert s.collides_with_self(head)


def test_snake_collides_with() -> None:
    s = Snake.starting_at(10, 10, 3)
    assert s.collides_with((10, 10))
    assert not s.collides_with((99, 99))


def test_engine_initial_state() -> None:
    e = Engine(20, 20)
    assert e.state == GameState.PLAYING
    assert e.score == 0
    assert len(e.letters) == 8


def test_engine_tick_no_collision() -> None:
    e = Engine(60, 40)
    head_before = e.snake.head
    e.tick()
    assert e.state == GameState.PLAYING
    assert e.snake.head != head_before


def test_engine_wall_collision() -> None:
    e = Engine(60, 40)
    e.snake.body = [(0, 0), (1, 0), (2, 0)]
    e.snake.direction = Direction.LEFT
    e.tick()
    assert e.state == GameState.DEAD


def test_engine_respawn_letters() -> None:
    e = Engine(60, 40)
    for letter in e.letters:
        letter.collected = True
    e.respawn_letters()
    assert len(e.letters) == 8
    assert not any(letter.collected for letter in e.letters)


def test_engine_letter_collection_increases_score() -> None:
    e = Engine(60, 40)
    letter = e.letters[0]
    # place head to land on first inked cell of the letter
    # O letter: first inked cell is at (grid_x, grid_y + 1)
    target_x = letter.grid_x
    target_y = letter.grid_y + 1
    e.snake.body = [(target_x - 1, target_y)]
    e.snake.direction = Direction.RIGHT
    e.snake._grow_pending = 0
    e.tick()
    assert letter.collected
    assert e.score == 100


def test_engine_all_collected() -> None:
    e = Engine(60, 40)
    assert not e.all_collected()
    for letter in e.letters:
        letter.collected = True
    assert e.all_collected()


def test_engine_dead_state_no_tick() -> None:
    e = Engine(60, 40)
    e.state = GameState.DEAD
    head_before = e.snake.head
    e.tick()
    assert e.snake.head == head_before
