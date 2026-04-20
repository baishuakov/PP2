import pygame
import sys
from ball import Ball

pygame.init()

screen = pygame.display.set_mode((800, 500))
ball = Ball()
clock = pygame.time.Clock()

done = True
while done:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                pygame.quit()
            if event.key == pygame.K_UP:
                ball.move_up()
            if event.key == pygame.K_DOWN:
                ball.move_down(500)
            if event.key == pygame.K_LEFT:
                ball.move_left()
            if event.key == pygame.K_RIGHT:
                ball.move_right(800)

    screen.fill((255, 255, 255))
    ball.draw(screen)
    pygame.display.flip()
    clock.tick(60)
    
pygame.quit()