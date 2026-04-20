import pygame
import random
import sys

pygame.init()

# ── Grid & screen constants ───────────────────────────────────────────────────
CELL       = 20          
COLS, ROWS = 30, 25      
HUD_H      = 50          

SCREEN_W = CELL * COLS
SCREEN_H = CELL * ROWS + HUD_H

BASE_FPS        = 8      
FPS_PER_LEVEL   = 2      
FOODS_PER_LEVEL = 3      

# ── Colours ───────────────────────────────────────────────────────────────────
BLACK    = (0,   0,   0  )
WHITE    = (255, 255, 255)
DKGREEN  = (0,   140, 0  )
GREEN    = (50,  200, 50 )
RED      = (220, 40,  40 )
YELLOW   = (255, 215, 0  )
GRAY     = (30,  30,  30 )
LT_GRAY  = (60,  60,  60 )
GOLD     = (255, 200, 0  )

screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Snake - Practice 9")
clock  = pygame.time.Clock()
font   = pygame.font.SysFont("Arial", 22, bold=True)
big    = pygame.font.SysFont("Arial", 44, bold=True)

UP, DOWN, LEFT, RIGHT = (0, -1), (0, 1), (-1, 0), (1, 0)
OPPOSITE = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}

def random_food_pos(occupied: set) -> tuple:
    while True:
        c = random.randint(1, COLS - 2)
        r = random.randint(1, ROWS - 2)
        if (c, r) not in occupied:
            return (c, r)

class Snake:
    def __init__(self):
        cx, cy = COLS // 2, ROWS // 2
        self.body      = [(cx, cy), (cx-1, cy), (cx-2, cy)]
        self.direction = RIGHT
        self._queued   = RIGHT    
        self._grow     = False    

    def queue_direction(self, new_dir: tuple):
        if new_dir != OPPOSITE.get(self.direction):
            self._queued = new_dir

    def move(self):
        self.direction = self._queued
        hx, hy = self.body[0]
        new_head = (hx + self.direction[0], hy + self.direction[1])
        self.body.insert(0, new_head)
        if self._grow: self._grow = False
        else: self.body.pop()

    def eat(self): self._grow = True
    def hit_wall(self) -> bool:
        hx, hy = self.body[0]
        return not (0 <= hx < COLS and 0 <= hy < ROWS)
    def hit_self(self) -> bool: return self.body[0] in self.body[1:]

    def draw(self, surface):
        for i, (c, r) in enumerate(self.body):
            x, y = c * CELL, r * CELL + HUD_H
            col = DKGREEN if i == 0 else GREEN
            pygame.draw.rect(surface, col, (x + 2, y + 2, CELL - 4, CELL - 4), border_radius=4)

    @property
    def cells(self) -> set: return set(self.body)

# ── Updated Food Class with Weights and Timer ─────────────────────────────────
class Food:
    def __init__(self, occupied: set):
        self.pos = random_food_pos(occupied)
        # Extra Task: Different weights (1, 2, or 3)
        self.weight = random.choices([1, 2, 3], weights=[70, 20, 10])[0]
        # Extra Task: Disappearing timer (measured in frames/ticks)
        self.timer = random.randint(30, 60) 

    def update(self, occupied: set):
        """Decrease timer and relocate if it hits zero."""
        self.timer -= 1
        if self.timer <= 0:
            self.pos = random_food_pos(occupied)
            self.timer = random.randint(30, 60) # Reset timer
            return True # Signal that it moved
        return False

    def draw(self, surface):
        c, r = self.pos
        cx = c * CELL + CELL // 2
        cy = r * CELL + CELL // 2 + HUD_H
        # Color changes based on weight
        color = RED if self.weight == 1 else GOLD if self.weight == 2 else (255, 0, 255)
        pygame.draw.circle(surface, color, (cx, cy), (CELL // 2 - 2) + self.weight)
        
        # Draw the timer bar above the food
        timer_width = (self.timer / 60) * CELL
        pygame.draw.rect(surface, WHITE, (c * CELL, r * CELL + HUD_H - 5, timer_width, 3))

def draw_hud(surface, score: int, level: int, foods_this_level: int):
    pygame.draw.rect(surface, GRAY, (0, 0, SCREEN_W, HUD_H))
    sc = font.render(f"Score: {score}", True, WHITE)
    lv = font.render(f"Level {level}", True, GOLD)
    surface.blit(sc, (12, HUD_H//2 - sc.get_height()//2))
    surface.blit(lv, (SCREEN_W//2 - lv.get_width()//2, HUD_H//2 - lv.get_height()//2))

def draw_overlay(surface, title: str, sub: str = ""):
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    surface.blit(overlay, (0, 0))
    t = big.render(title, True, WHITE)
    surface.blit(t, (SCREEN_W//2 - t.get_width()//2, SCREEN_H//2 - 70))
    if sub:
        s = font.render(sub, True, YELLOW)
        surface.blit(s, (SCREEN_W//2 - s.get_width()//2, SCREEN_H//2))

def main():
    snake = Snake()
    food  = Food(snake.cells)
    score, level, foods_eaten, current_fps = 0, 1, 0, BASE_FPS
    game_over = False

    while True:
        clock.tick(current_fps)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if game_over:
                    if event.key == pygame.K_r: main(); return
                    if event.key == pygame.K_q: pygame.quit(); sys.exit()
                else:
                    if event.key in (pygame.K_UP, pygame.K_w): snake.queue_direction(UP)
                    if event.key in (pygame.K_DOWN, pygame.K_s): snake.queue_direction(DOWN)
                    if event.key in (pygame.K_LEFT, pygame.K_a): snake.queue_direction(LEFT)
                    if event.key in (pygame.K_RIGHT, pygame.K_d): snake.queue_direction(RIGHT)

        if not game_over:
            snake.move()
            # Update food timer and check if it disappears
            food.update(snake.cells)

            if snake.hit_wall() or snake.hit_self():
                game_over = True
            elif snake.body[0] == food.pos:
                snake.eat()
                foods_eaten += 1
                # Increase score based on the food's weight
                score += (10 * level) * food.weight
                
                if foods_eaten // FOODS_PER_LEVEL + 1 > level:
                    level += 1
                    current_fps += FPS_PER_LEVEL
                
                food = Food(snake.cells)

        screen.fill(BLACK)
        draw_hud(screen, score, level, foods_eaten % FOODS_PER_LEVEL)
        food.draw(screen)
        snake.draw(screen)
        if game_over: draw_overlay(screen, "GAME OVER", f"Score: {score}")
        pygame.display.flip()

if __name__ == "__main__": main()