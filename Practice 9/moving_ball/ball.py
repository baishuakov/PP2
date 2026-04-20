import pygame

class Ball:
    def __init__(self):
        self.x = 400
        self.y = 250
        self.radius = 25
        self.color = (255, 0, 0)
        self.step = 20

    def move_up(self):
        self.y -= self.step
        if self.y - self.radius < 0:
            self.y = self.radius

    def move_down(self, screen_height):
        self.y += self.step
        if self.y + self.radius > screen_height:
            self.y = screen_height - self.radius

    def move_left(self):
        self.x -= self.step
        if self.x - self.radius < 0:
            self.x = self.radius

    def move_right(self, screen_width):
        self.x += self.step
        if self.x + self.radius > screen_width:
            self.x = screen_width - self.radius

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (self.x, self.y), self.radius)