"""
game.py
-------
Core snake game engine.  No rendering happens here — game.py owns state only.
main.py calls update() each tick and draw() each frame.

Features implemented:
  * Classic snake movement on a grid
  * Three food types: normal, bonus (disappears), poison (shorten)
  * Three power-ups: speed-boost, slow-motion, shield
    - Only one active on the field at a time
    - 8 s field lifetime; 5 s effect duration
    - pygame.time.get_ticks() used throughout
  * Obstacle blocks starting at Level 3; safe-spawn guaranteed
  * Personal best fetched from DB and shown on HUD
  * Level progression, score, difficulty scaling
"""

import random
import enum
import pygame

import config as C


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------
class Dir(enum.Enum):
    UP    = ( 0, -1)
    DOWN  = ( 0,  1)
    LEFT  = (-1,  0)
    RIGHT = ( 1,  0)

OPPOSITES = {Dir.UP: Dir.DOWN, Dir.DOWN: Dir.UP,
             Dir.LEFT: Dir.RIGHT, Dir.RIGHT: Dir.LEFT}


class FoodKind(enum.Enum):
    NORMAL  = "normal"
    BONUS   = "bonus"
    POISON  = "poison"


class PowerUpKind(enum.Enum):
    SPEED  = "speed"
    SLOW   = "slow"
    SHIELD = "shield"

POWERUP_LABELS = {
    PowerUpKind.SPEED:  "SPEED",
    PowerUpKind.SLOW:   "SLOW",
    PowerUpKind.SHIELD: "SHIELD",
}
POWERUP_COLORS = {
    PowerUpKind.SPEED:  C.C_POWERUP_SPEED,
    PowerUpKind.SLOW:   C.C_POWERUP_SLOW,
    PowerUpKind.SHIELD: C.C_POWERUP_SHIELD,
}


# ---------------------------------------------------------------------------
# Cell helpers
# ---------------------------------------------------------------------------
def _cell_rect(col, row):
    """Return the pygame.Rect for a grid cell inside the arena."""
    return pygame.Rect(col * C.CELL, row * C.CELL, C.CELL, C.CELL)


def _rand_cell(excluded: set) -> tuple[int, int] | None:
    """Pick a random arena cell not in the excluded set.
    Returns None if every cell is occupied (shouldn't happen in practice)."""
    all_cells = {(c, r) for c in range(C.ARENA_COLS) for r in range(C.ROWS)}
    free = list(all_cells - excluded)
    return random.choice(free) if free else None


# ---------------------------------------------------------------------------
# Food
# ---------------------------------------------------------------------------
BONUS_FOOD_LIFETIME = 6_000   # ms before a bonus food disappears


class Food:
    def __init__(self, pos: tuple[int, int], kind: FoodKind):
        self.pos = pos
        self.kind = kind
        self.spawned_at = pygame.time.get_ticks()

    @property
    def alive(self) -> bool:
        if self.kind == FoodKind.BONUS:
            return pygame.time.get_ticks() - self.spawned_at < BONUS_FOOD_LIFETIME
        return True

    def color(self):
        return {
            FoodKind.NORMAL: C.C_FOOD_NORMAL,
            FoodKind.BONUS:  C.C_FOOD_BONUS,
            FoodKind.POISON: C.C_FOOD_POISON,
        }[self.kind]

    def draw(self, surface):
        rect = _cell_rect(*self.pos).inflate(-4, -4)
        pygame.draw.ellipse(surface, self.color(), rect)
        # highlight pip
        pip = pygame.Rect(rect.x + 4, rect.y + 4, 5, 5)
        pygame.draw.ellipse(surface, (255, 255, 255), pip)

        # bonus food: draw a shrinking countdown arc
        if self.kind == FoodKind.BONUS:
            remaining = max(0, BONUS_FOOD_LIFETIME -
                           (pygame.time.get_ticks() - self.spawned_at))
            frac = remaining / BONUS_FOOD_LIFETIME
            if frac < 0.4:   # only show when nearly expired
                pygame.draw.arc(surface, C.C_ACCENT,
                                _cell_rect(*self.pos).inflate(-2, -2),
                                0, frac * 3.14159 * 2, 2)


# ---------------------------------------------------------------------------
# Power-up (on field)
# ---------------------------------------------------------------------------
class PowerUpItem:
    def __init__(self, pos: tuple[int, int], kind: PowerUpKind):
        self.pos = pos
        self.kind = kind
        self.spawned_at = pygame.time.get_ticks()

    @property
    def alive(self) -> bool:
        return (pygame.time.get_ticks() - self.spawned_at
                < C.POWERUP_FIELD_LIFETIME)

    def draw(self, surface):
        rect = _cell_rect(*self.pos).inflate(-2, -2)
        color = POWERUP_COLORS[self.kind]
        pygame.draw.rect(surface, color, rect, border_radius=5)
        pygame.draw.rect(surface, (255, 255, 255), rect, 2, border_radius=5)
        # blink in the last 2 s
        time_left = C.POWERUP_FIELD_LIFETIME - (pygame.time.get_ticks()
                                                 - self.spawned_at)
        if time_left < 2000 and (pygame.time.get_ticks() // 250) % 2 == 0:
            pygame.draw.rect(surface, (255, 255, 255), rect, 1, border_radius=5)

        font = pygame.font.SysFont("arial", 9, bold=True)
        lbl = font.render(POWERUP_LABELS[self.kind][0], True, (10, 10, 10))
        surface.blit(lbl, lbl.get_rect(center=rect.center))


# ---------------------------------------------------------------------------
# Active power-up effect (in the snake)
# ---------------------------------------------------------------------------
class ActiveEffect:
    def __init__(self, kind: PowerUpKind):
        self.kind = kind
        self.started_at = pygame.time.get_ticks()

    @property
    def remaining_ms(self) -> int:
        if self.kind == PowerUpKind.SHIELD:
            return -1   # unlimited until triggered
        return max(0, C.POWERUP_EFFECT_DURATION -
                   (pygame.time.get_ticks() - self.started_at))

    @property
    def active(self) -> bool:
        if self.kind == PowerUpKind.SHIELD:
            return True   # removed explicitly when triggered
        return self.remaining_ms > 0


# ---------------------------------------------------------------------------
# Obstacle block
# ---------------------------------------------------------------------------
class Obstacle:
    def __init__(self, pos: tuple[int, int]):
        self.pos = pos

    def draw(self, surface):
        rect = _cell_rect(*self.pos)
        pygame.draw.rect(surface, C.C_OBSTACLE, rect)
        pygame.draw.rect(surface, (50, 50, 65), rect, 1)
        # cross hatching
        pygame.draw.line(surface, (50, 50, 65),
                         rect.topleft, rect.bottomright, 1)
        pygame.draw.line(surface, (50, 50, 65),
                         rect.topright, rect.bottomleft, 1)


# ---------------------------------------------------------------------------
# Snake
# ---------------------------------------------------------------------------
class Snake:
    def __init__(self, color):
        # start in the middle, 3 segments long, heading right
        mid_c, mid_r = C.ARENA_COLS // 2, C.ROWS // 2
        self.body = [(mid_c - i, mid_r) for i in range(3)]
        self.direction = Dir.RIGHT
        self._next_dir = Dir.RIGHT
        self.color = color
        self.grow_pending = 0   # segments to add on next move

    @property
    def head(self):
        return self.body[0]

    @property
    def cells(self) -> set:
        return set(self.body)

    def steer(self, new_dir: Dir):
        if new_dir != OPPOSITES[self.direction]:
            self._next_dir = new_dir

    def step(self) -> tuple[int, int]:
        """Advance one cell. Returns the new head position."""
        self.direction = self._next_dir
        dc, dr = self.direction.value
        new_head = (self.body[0][0] + dc, self.body[0][1] + dr)
        self.body.insert(0, new_head)
        if self.grow_pending > 0:
            self.grow_pending -= 1
        else:
            self.body.pop()
        return new_head

    def grow(self, n=1):
        self.grow_pending += n

    def shorten(self, n=2) -> bool:
        """Remove n tail segments. Returns False if snake becomes too short."""
        for _ in range(n):
            if len(self.body) > 1:
                self.body.pop()
        return len(self.body) > 1

    def draw(self, surface, effect: ActiveEffect | None):
        shield_active = effect and effect.kind == PowerUpKind.SHIELD
        for i, (c, r) in enumerate(self.body):
            rect = _cell_rect(c, r).inflate(-2, -2)
            if i == 0:   # head
                color = C.C_SNAKE_SHIELD if shield_active else C.C_SNAKE_HEAD
                pygame.draw.rect(surface, color, rect, border_radius=5)
                # eyes
                ex = rect.x + 4 if self.direction in (Dir.RIGHT, Dir.UP) \
                     else rect.right - 9
                ey = rect.y + 4
                pygame.draw.circle(surface, (10, 10, 10), (ex, ey), 3)
            else:
                color = C.C_SNAKE_SHIELD if shield_active else self.color
                pygame.draw.rect(surface, color, rect, border_radius=4)
                # segment outline
                darker = tuple(max(0, v - 40) for v in color)
                pygame.draw.rect(surface, darker, rect, 1, border_radius=4)


# ---------------------------------------------------------------------------
# Game state machine
# ---------------------------------------------------------------------------
class GameState(enum.Enum):
    PLAYING = "playing"
    DEAD    = "dead"


class Game:
    def __init__(self, snake_color, personal_best: int = 0):
        self.snake = Snake(snake_color)
        self.state = GameState.PLAYING
        self.score = 0
        self.level = 1
        self.personal_best = personal_best

        self.foods: list[Food] = []
        self.powerup_on_field: PowerUpItem | None = None
        self.effect: ActiveEffect | None = None
        self.obstacles: list[Obstacle] = []

        # timing for the step ticker (separate from FPS)
        self._last_step_ms = pygame.time.get_ticks()
        self._step_interval = self._calc_step_interval()

        # spawn counters
        self._food_timer = 0
        self._powerup_timer = 0

        self._spawn_obstacles()
        self._spawn_food()

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _occupied_cells(self) -> set:
        occupied = self.snake.cells
        occupied |= {f.pos for f in self.foods}
        if self.powerup_on_field:
            occupied.add(self.powerup_on_field.pos)
        occupied |= {o.pos for o in self.obstacles}
        return occupied

    def _calc_step_interval(self) -> int:
        """ms between snake steps."""
        fps = C.BASE_FPS + (self.level - 1) * C.FPS_PER_LEVEL
        if self.effect:
            if self.effect.kind == PowerUpKind.SPEED:
                fps += C.SPEED_BOOST_FPS_DELTA
            elif self.effect.kind == PowerUpKind.SLOW:
                fps += C.SLOW_MOTION_FPS_DELTA   # negative → slower
        fps = max(2, fps)
        return int(1000 / fps)

    def _score_for_level(self) -> int:
        return 5 * self.level   # 5 food items per level to advance

    # ------------------------------------------------------------------
    # obstacle placement — safe (flood-fill check)
    # ------------------------------------------------------------------
    def _spawn_obstacles(self):
        if self.level < 3:
            self.obstacles = []
            return

        count = min(C.OBSTACLES_PER_LEVEL + (self.level - 3) * 2,
                    C.OBSTACLES_MAX)
        occupied = self.snake.cells
        new_obstacles = []

        attempts = 0
        while len(new_obstacles) < count and attempts < 500:
            attempts += 1
            pos = _rand_cell(occupied | {o.pos for o in new_obstacles})
            if pos is None:
                break
            # would this cell trap the snake head? quick BFS reachability check
            candidate_walls = (occupied
                               | {o.pos for o in new_obstacles}
                               | {pos})
            if self._reachable(self.snake.head, candidate_walls, threshold=10):
                new_obstacles.append(Obstacle(pos))

        self.obstacles = new_obstacles

    def _reachable(self, start, walls: set, threshold: int) -> bool:
        """BFS from start — returns True if at least `threshold` cells are
        reachable without crossing walls or arena borders."""
        visited = {start}
        queue = [start]
        while queue and len(visited) < threshold:
            c, r = queue.pop(0)
            for dc, dr in ((0,-1),(0,1),(-1,0),(1,0)):
                nc, nr = c + dc, r + dr
                if (nc, nr) not in visited and (nc, nr) not in walls:
                    if 0 <= nc < C.ARENA_COLS and 0 <= nr < C.ROWS:
                        visited.add((nc, nr))
                        queue.append((nc, nr))
        return len(visited) >= threshold

    # ------------------------------------------------------------------
    # food spawning
    # ------------------------------------------------------------------
    def _spawn_food(self):
        occupied = self._occupied_cells()
        pos = _rand_cell(occupied)
        if pos is None:
            return
        weights = [C.FOOD_WEIGHTS[k.value]
                   for k in (FoodKind.NORMAL, FoodKind.BONUS, FoodKind.POISON)]
        kind = random.choices(
            [FoodKind.NORMAL, FoodKind.BONUS, FoodKind.POISON],
            weights=weights, k=1
        )[0]
        self.foods.append(Food(pos, kind))

    def _maybe_spawn_powerup(self):
        if self.powerup_on_field is not None:
            return
        if random.random() < 0.15:   # ~15 % chance per food eaten
            occupied = self._occupied_cells()
            pos = _rand_cell(occupied)
            if pos:
                kind = random.choice(list(PowerUpKind))
                self.powerup_on_field = PowerUpItem(pos, kind)

    # ------------------------------------------------------------------
    # main update — called every frame
    # ------------------------------------------------------------------
    def update(self, keys_pressed=None):
        if self.state != GameState.PLAYING:
            return

        now = pygame.time.get_ticks()

        # expire power-up effect
        if self.effect and not self.effect.active:
            self.effect = None
            self._step_interval = self._calc_step_interval()

        # expire field power-up
        if self.powerup_on_field and not self.powerup_on_field.alive:
            self.powerup_on_field = None

        # expire bonus foods
        self.foods = [f for f in self.foods if f.alive]

        # ensure there's always at least one food
        if not self.foods:
            self._spawn_food()

        # snake step
        if now - self._last_step_ms >= self._step_interval:
            self._last_step_ms = now
            self._step()

    def steer(self, direction: Dir):
        self.snake.steer(direction)

    def _step(self):
        new_head = self.snake.step()
        c, r = new_head

        shield_active = (self.effect is not None
                         and self.effect.kind == PowerUpKind.SHIELD)

        # ----- border collision -----
        if not (0 <= c < C.ARENA_COLS and 0 <= r < C.ROWS):
            if shield_active:
                # wrap around / teleport to opposite edge
                c = c % C.ARENA_COLS
                r = r % C.ROWS
                new_head = (c, r)
                self.snake.body[0] = new_head
                self.effect = None          # shield consumed
                self._step_interval = self._calc_step_interval()
            else:
                self._die()
                return

        # ----- obstacle collision -----
        obs_cells = {o.pos for o in self.obstacles}
        if new_head in obs_cells:
            if shield_active:
                self.effect = None
                self._step_interval = self._calc_step_interval()
            else:
                self._die()
                return

        # ----- self collision -----
        if new_head in set(self.snake.body[1:]):
            if shield_active:
                self.effect = None
                self._step_interval = self._calc_step_interval()
            else:
                self._die()
                return

        # ----- food collision -----
        for food in list(self.foods):
            if food.pos == new_head:
                self.foods.remove(food)
                if food.kind == FoodKind.NORMAL:
                    self.snake.grow(1)
                    self.score += C.SCORE_NORMAL
                elif food.kind == FoodKind.BONUS:
                    self.snake.grow(1)
                    self.score += C.SCORE_BONUS
                elif food.kind == FoodKind.POISON:
                    survived = self.snake.shorten(2)
                    if not survived:
                        self._die()
                        return
                self._maybe_spawn_powerup()
                self._spawn_food()
                self._check_level_up()
                break

        # ----- power-up collision -----
        if self.powerup_on_field and self.powerup_on_field.pos == new_head:
            self._activate_powerup(self.powerup_on_field.kind)
            self.powerup_on_field = None

    def _activate_powerup(self, kind: PowerUpKind):
        self.effect = ActiveEffect(kind)
        self._step_interval = self._calc_step_interval()

    def _check_level_up(self):
        threshold = self.level * 5 * C.SCORE_NORMAL  # 50, 100, 150 …
        if self.score >= threshold:
            self.level += 1
            self._step_interval = self._calc_step_interval()
            self._spawn_obstacles()

    def _die(self):
        self.state = GameState.DEAD

    # ------------------------------------------------------------------
    # render
    # ------------------------------------------------------------------
    def draw(self, surface, show_grid: bool):
        # arena background
        arena_rect = pygame.Rect(0, 0, C.ARENA_COLS * C.CELL, C.ROWS * C.CELL)
        pygame.draw.rect(surface, C.C_ARENA, arena_rect)

        # grid
        if show_grid:
            for col in range(C.ARENA_COLS + 1):
                x = col * C.CELL
                pygame.draw.line(surface, C.C_GRID,
                                 (x, 0), (x, C.ROWS * C.CELL))
            for row in range(C.ROWS + 1):
                y = row * C.CELL
                pygame.draw.line(surface, C.C_GRID,
                                 (0, y), (C.ARENA_COLS * C.CELL, y))

        # border
        pygame.draw.rect(surface, C.C_BORDER, arena_rect, 3)

        # entities
        for o in self.obstacles:
            o.draw(surface)
        for f in self.foods:
            f.draw(surface)
        if self.powerup_on_field:
            self.powerup_on_field.draw(surface)
        self.snake.draw(surface, self.effect)
