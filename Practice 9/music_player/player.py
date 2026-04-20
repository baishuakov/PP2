import pygame
import os

class MusicPlayer:
    def __init__(self, music_folder):
        self.music_folder = music_folder

        self.playlist = []
        for file in os.listdir(music_folder):
            if file.endswith(".mp3") or file.endswith(".wav"):
                self.playlist.append(file)
        self.playlist.sort()

        self.current_index = 0
        self.playing = False
        self.paused = False

        if len(self.playlist) > 0:
            pygame.mixer.music.load(os.path.join(self.music_folder, self.playlist[0]))

    def play_pause(self):
        if len(self.playlist) == 0:
            return

        if not self.playing:
            pygame.mixer.music.play()
            self.playing = True
            self.paused = False
        elif self.paused:
            pygame.mixer.music.unpause()
            self.paused = False
        else:
            pygame.mixer.music.pause()
            self.paused = True

    def next_track(self):
        if len(self.playlist) == 0:
            return
        self.current_index = (self.current_index + 1) % len(self.playlist)
        pygame.mixer.music.load(os.path.join(self.music_folder, self.playlist[self.current_index]))
        pygame.mixer.music.play()
        self.playing = True
        self.paused = False

    def previous_track(self):
        if len(self.playlist) == 0:
            return
        self.current_index = (self.current_index - 1) % len(self.playlist)
        pygame.mixer.music.load(os.path.join(self.music_folder, self.playlist[self.current_index]))
        pygame.mixer.music.play()
        self.playing = True
        self.paused = False

    def get_status(self):
        if not self.playing:
            return "Stopped"
        elif self.paused:
            return "Paused"
        else:
            return "Playing"

    def get_current_track_name(self):
        if len(self.playlist) == 0:
            return "No tracks"
        return self.playlist[self.current_index]

    def update(self):
        if self.playing and not self.paused:
            if not pygame.mixer.music.get_busy():
                self.next_track()

    def get_position(self):
        pos_ms = pygame.mixer.music.get_pos()
        if pos_ms == -1:
            return "0:00"
        seconds = pos_ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"