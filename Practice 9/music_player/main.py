import pygame
import os
from player import MusicPlayer

pygame.init()
pygame.mixer.init()

screen = pygame.display.set_mode((800, 500))

font = pygame.font.Font(None, 32)
small_font = pygame.font.Font(None, 26)

clock = pygame.time.Clock()

music_directory = "music"
player = MusicPlayer(music_directory)

running = True
while running:

    player.update()

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:

            if event.key == pygame.K_SPACE:
                player.play_pause()

            elif event.key == pygame.K_RIGHT:
                player.next_track()

            elif event.key == pygame.K_LEFT:
                player.previous_track()

            elif event.key == pygame.K_q:
                running = False

    screen.fill((175, 238, 238))  #pale turquoise

    title = font.render("Music Player", True, (0, 0, 128))
    screen.blit(title, (320, 50))

    instructions = small_font.render(
        "SPACE - Play/Pause   LEFT - Previous   RIGHT - Next   Q - Quit",
        True,
        (0, 0, 128)
    )
    screen.blit(instructions, (150, 100))

    if len(player.playlist) > 0:

        current_text = font.render("Current track:", True, (0, 0, 128))
        screen.blit(current_text, (50, 200))

        track_text = small_font.render(player.get_current_track_name(), True, (0, 0, 0))
        screen.blit(track_text, (50, 240))

        status_text = small_font.render("Status: " + player.get_status() + "   " + player.get_position(), True, (0, 0, 128))
        screen.blit(status_text, (50, 280))

        list_title = font.render("Playlist:", True, (0, 0, 0))
        screen.blit(list_title, (420, 200))

        y = 240
        for i in range(len(player.playlist)):
            if i == player.current_index:
                text = small_font.render("> " + player.playlist[i], True, (65, 105, 225))
            else:
                text = small_font.render(player.playlist[i], True, (0, 0, 0))
            screen.blit(text, (420, y))
            y += 35

    else:
        no_music = font.render("No music files found", True, (255, 0, 0))
        screen.blit(no_music, (180, 240))

    pygame.display.flip()
    clock.tick(30)

pygame.quit()