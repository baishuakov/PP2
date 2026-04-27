"""
config.py
---------
All magic numbers and tunable constants in one place.
Import this everywhere instead of scattering literals.
"""

# Window / grid
WIN_W = 800
WIN_H = 640
CELL = 24          # grid cell size in pixels
COLS = WIN_W // CELL   # 33
ROWS = WIN_H // CELL   # 26

# Sidebar width (right of the arena)
SIDEBAR_W = 200
ARENA_W = WIN_W - SIDEBAR_W   # 600  → 25 cells wide
ARENA_COLS = ARENA_W // CELL  # 25

# Frames per second at each base speed level
BASE_FPS = 8       # level 1 FPS
FPS_PER_LEVEL = 1  # added per level

# Obstacle blocks per level (starting at level 3)
OBSTACLES_PER_LEVEL = 3   # base count
OBSTACLES_MAX = 18

# Power-up timings (milliseconds)
POWERUP_FIELD_LIFETIME = 8_000   # disappears from field after this
POWERUP_EFFECT_DURATION = 5_000  # active duration once collected
SPEED_BOOST_FPS_DELTA = 4
SLOW_MOTION_FPS_DELTA = -4

# Food weights (for weighted random) — normal food
# Keep in sync with game.py FoodKind enum
FOOD_WEIGHTS = {
    "normal":  50,
    "bonus":   25,    # disappears after a short time
    "poison":  25,
}

# Score values
SCORE_NORMAL = 10
SCORE_BONUS   = 25

# Colors — palette
C_BG          = (15,  17,  22)
C_ARENA       = (20,  24,  32)
C_GRID        = (30,  36,  48)
C_SIDEBAR     = (24,  28,  38)
C_BORDER      = (60,  70,  90)
C_TEXT        = (220, 220, 230)
C_MUTED       = (110, 120, 140)
C_ACCENT      = (255, 200,  60)
C_GOOD        = ( 80, 200, 120)
C_DANGER      = (210,  60,  60)

C_SNAKE_DEFAULT = ( 80, 200, 120)
C_SNAKE_HEAD    = (140, 240, 160)
C_SNAKE_SHIELD  = ( 80, 160, 255)

C_FOOD_NORMAL = (255, 100,  80)
C_FOOD_BONUS  = (255, 210,  60)
C_FOOD_POISON = (110,  20,  20)

C_POWERUP_SPEED  = ( 60, 180, 255)
C_POWERUP_SLOW   = (180,  60, 255)
C_POWERUP_SHIELD = (255, 200,  60)

C_OBSTACLE = ( 80,  80,  95)

# DB connection — override with env vars in production
import os
DB_CONFIG = {
    "host":     os.environ.get("PGHOST", "localhost"),
    "port":     int(os.environ.get("PGPORT", 5432)),
    "dbname":   os.environ.get("PGDATABASE", "snake_game"),
    "user":     os.environ.get("PGUSER", "postgres"),
    "password": os.environ.get("PGPASSWORD", "postgres"),
}
