"""
main.py
-------
Entry point. Runs a small state machine over screens:

  MENU -> NAME -> PLAY -> GAME_OVER
  MENU -> SETTINGS -> MENU
  MENU -> LEADERBOARD -> MENU

Settings are loaded at startup and saved any time they change. The
leaderboard is read on demand and rewritten when a run finishes.
"""

import sys
import pygame

from ui import (
    Button, OptionCycler, TextInput,
    BG, PANEL, ACCENT, TEXT, MUTED, GOOD, DANGER,
    draw_centered_text, draw_panel,
)
from racer import (
    Game, CAR_COLORS, FINISH_DISTANCE,
)
from persistence import (
    load_settings, save_settings,
    load_leaderboard, add_score,
)


WIN_W, WIN_H = 800, 720
FPS = 60


# Screen identifiers
S_MENU = "menu"
S_NAME = "name"
S_PLAY = "play"
S_OVER = "over"
S_SETTINGS = "settings"
S_LEADERBOARD = "leaderboard"


class App:
    def __init__(self):
        pygame.init()
        # mixer init can fail on headless setups — don't crash the whole game over it
        try:
            pygame.mixer.init()
            self.mixer_ok = True
        except pygame.error:
            self.mixer_ok = False

        pygame.display.set_caption("TSIS3 — Racer")
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        self.clock = pygame.time.Clock()

        # fonts
        self.f_huge = pygame.font.SysFont("arial", 56, bold=True)
        self.f_big = pygame.font.SysFont("arial", 34, bold=True)
        self.f_med = pygame.font.SysFont("arial", 22)
        self.f_small = pygame.font.SysFont("arial", 18)
        self.f_tiny = pygame.font.SysFont("arial", 14)

        self.settings = load_settings()
        self.player_name = "Player"
        self.state = S_MENU
        self.game = None
        self.last_run = None       # dict with score/distance/coins
        self.running = True

        # widgets per screen — built lazily
        self._menu_buttons = self._build_menu_buttons()
        self._settings_widgets = None
        self._over_buttons = None
        self._leaderboard_buttons = None
        self._name_widgets = None

    # ------------------------------------------------------------------
    # screen builders
    # ------------------------------------------------------------------
    def _build_menu_buttons(self):
        cx = WIN_W // 2
        bw, bh, gap = 260, 56, 18
        y0 = 280
        return [
            Button((cx - bw // 2, y0,             bw, bh), "Play",
                   lambda: self._goto(S_NAME), font=self.f_med),
            Button((cx - bw // 2, y0 + (bh + gap), bw, bh), "Leaderboard",
                   lambda: self._goto(S_LEADERBOARD), font=self.f_med),
            Button((cx - bw // 2, y0 + 2 * (bh + gap), bw, bh), "Settings",
                   lambda: self._goto(S_SETTINGS), font=self.f_med),
            Button((cx - bw // 2, y0 + 3 * (bh + gap), bw, bh), "Quit",
                   self._quit, font=self.f_med),
        ]

    def _build_settings_widgets(self):
        cx = WIN_W // 2
        bw, bh, gap = 460, 56, 16
        y0 = 200

        sound_options = ["on", "off"]
        sound_idx = 0 if self.settings.get("sound", True) else 1
        car_colors = list(CAR_COLORS.keys())
        car_idx = car_colors.index(self.settings.get("car_color", "red")) \
            if self.settings.get("car_color") in car_colors else 0
        diff_options = ["easy", "normal", "hard"]
        diff_idx = diff_options.index(self.settings.get("difficulty", "normal")) \
            if self.settings.get("difficulty") in diff_options else 1

        widgets = {
            "sound": OptionCycler(
                (cx - bw // 2, y0, bw, bh),
                "Sound",
                sound_options, sound_idx,
                self._set_sound,
                font=self.f_med),
            "car": OptionCycler(
                (cx - bw // 2, y0 + (bh + gap), bw, bh),
                "Car color",
                car_colors, car_idx,
                self._set_car_color,
                font=self.f_med),
            "diff": OptionCycler(
                (cx - bw // 2, y0 + 2 * (bh + gap), bw, bh),
                "Difficulty",
                diff_options, diff_idx,
                self._set_difficulty,
                font=self.f_med),
            "back": Button(
                (cx - 100, y0 + 4 * (bh + gap), 200, bh),
                "Back",
                lambda: self._goto(S_MENU),
                font=self.f_med),
        }
        return widgets

    def _build_over_buttons(self):
        cx = WIN_W // 2
        bw, bh, gap = 200, 50, 20
        y = WIN_H - 110
        return [
            Button((cx - bw - gap // 2, y, bw, bh), "Retry",
                   self._retry, font=self.f_med),
            Button((cx + gap // 2, y, bw, bh), "Main Menu",
                   lambda: self._goto(S_MENU), font=self.f_med),
        ]

    def _build_leaderboard_buttons(self):
        return [
            Button((WIN_W // 2 - 100, WIN_H - 80, 200, 50), "Back",
                   lambda: self._goto(S_MENU), font=self.f_med),
        ]

    def _build_name_widgets(self):
        cx = WIN_W // 2
        return {
            "input": TextInput((cx - 200, 320, 400, 56), font=self.f_big,
                               max_length=12),
            "start": Button((cx - 110, 410, 220, 56),
                            "Start race", self._start_run, font=self.f_med),
            "back":  Button((cx - 110, 480, 220, 50),
                            "Back", lambda: self._goto(S_MENU), font=self.f_med),
        }

    # ------------------------------------------------------------------
    # state transitions
    # ------------------------------------------------------------------
    def _goto(self, state):
        self.state = state
        if state == S_SETTINGS:
            self._settings_widgets = self._build_settings_widgets()
        elif state == S_OVER:
            self._over_buttons = self._build_over_buttons()
        elif state == S_LEADERBOARD:
            self._leaderboard_buttons = self._build_leaderboard_buttons()
            self._cached_leaderboard = load_leaderboard()
        elif state == S_NAME:
            self._name_widgets = self._build_name_widgets()
            # pre-fill with last used name
            self._name_widgets["input"].text = self.player_name \
                if self.player_name != "Player" else ""

    def _start_run(self):
        # take the typed name (or fall back to default)
        typed = self._name_widgets["input"].text.strip() if self._name_widgets else ""
        self.player_name = typed if typed else "Player"
        self.game = Game((WIN_W, WIN_H), self.settings)
        self.state = S_PLAY

    def _retry(self):
        self.game = Game((WIN_W, WIN_H), self.settings)
        self.state = S_PLAY

    def _quit(self):
        self.running = False

    # settings handlers ------------------------------------------------
    def _set_sound(self, value):
        self.settings["sound"] = (value == "on")
        save_settings(self.settings)

    def _set_car_color(self, value):
        self.settings["car_color"] = value
        save_settings(self.settings)

    def _set_difficulty(self, value):
        self.settings["difficulty"] = value
        save_settings(self.settings)

    # ------------------------------------------------------------------
    # event dispatch
    # ------------------------------------------------------------------
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                continue

            if self.state == S_MENU:
                for b in self._menu_buttons:
                    b.handle(event)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.running = False

            elif self.state == S_NAME:
                result = self._name_widgets["input"].handle(event)
                if result == "submit":
                    self._start_run()
                self._name_widgets["start"].handle(event)
                self._name_widgets["back"].handle(event)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self._goto(S_MENU)

            elif self.state == S_PLAY:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    # treat ESC as a forfeit — record the run as-is
                    self._end_run()

            elif self.state == S_OVER:
                for b in self._over_buttons:
                    b.handle(event)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self._retry()
                    elif event.key == pygame.K_ESCAPE:
                        self._goto(S_MENU)

            elif self.state == S_SETTINGS:
                for w in self._settings_widgets.values():
                    w.handle(event)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self._goto(S_MENU)

            elif self.state == S_LEADERBOARD:
                for b in self._leaderboard_buttons:
                    b.handle(event)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self._goto(S_MENU)

    # ------------------------------------------------------------------
    # update + draw per state
    # ------------------------------------------------------------------
    def update(self, dt):
        mouse = pygame.mouse.get_pos()

        if self.state == S_MENU:
            for b in self._menu_buttons:
                b.update(mouse)

        elif self.state == S_NAME:
            self._name_widgets["start"].update(mouse)
            self._name_widgets["back"].update(mouse)

        elif self.state == S_PLAY:
            keys = pygame.key.get_pressed()
            self.game.update(keys, dt)
            if not self.game.alive or self.game.finished:
                self._end_run()

        elif self.state == S_OVER:
            for b in self._over_buttons:
                b.update(mouse)

        elif self.state == S_SETTINGS:
            for w in self._settings_widgets.values():
                w.update(mouse)

        elif self.state == S_LEADERBOARD:
            for b in self._leaderboard_buttons:
                b.update(mouse)

    def _end_run(self):
        if self.game is None:
            self._goto(S_MENU)
            return
        self.last_run = {
            "name": self.player_name,
            "score": self.game.score,
            "distance": int(self.game.distance),
            "coins": self.game.coins_collected,
            "finished": self.game.finished,
        }
        # persist to leaderboard
        add_score(self.player_name,
                  self.last_run["score"],
                  self.last_run["distance"],
                  self.last_run["coins"])
        self._goto(S_OVER)

    # ------------------------------------------------------------------
    # screens
    # ------------------------------------------------------------------
    def draw_menu(self):
        self.screen.fill(BG)
        draw_centered_text(self.screen, "TSIS3 — Racer",
                           self.f_huge, ACCENT, (WIN_W // 2, 130))
        draw_centered_text(self.screen, "Avoid the traffic. Grab power-ups. Reach the finish.",
                           self.f_med, MUTED, (WIN_W // 2, 200))
        for b in self._menu_buttons:
            b.draw(self.screen)
        draw_centered_text(self.screen,
                           "Arrow keys / WASD to drive   ·   ESC to forfeit during a run",
                           self.f_small, MUTED, (WIN_W // 2, WIN_H - 40))

    def draw_name(self):
        self.screen.fill(BG)
        draw_centered_text(self.screen, "Enter your name",
                           self.f_big, ACCENT, (WIN_W // 2, 220))
        draw_centered_text(self.screen, "(used on the leaderboard, max 12 chars)",
                           self.f_small, MUTED, (WIN_W // 2, 270))
        self._name_widgets["input"].draw(self.screen)
        self._name_widgets["start"].draw(self.screen)
        self._name_widgets["back"].draw(self.screen)
        draw_centered_text(self.screen, "Press Enter to start",
                           self.f_small, MUTED, (WIN_W // 2, WIN_H - 40))

    def draw_play(self):
        self.game.draw(self.screen)
        self._draw_hud()

    def _draw_hud(self):
        # top bar
        pygame.draw.rect(self.screen, (0, 0, 0, 180), (0, 0, WIN_W, 40))
        bar = pygame.Surface((WIN_W, 40), pygame.SRCALPHA)
        bar.fill((0, 0, 0, 140))
        self.screen.blit(bar, (0, 0))

        score_txt = self.f_med.render(f"Score: {self.game.score}", True, TEXT)
        self.screen.blit(score_txt, (12, 8))

        coins_txt = self.f_med.render(f"Coins: {self.game.coins_collected}", True, ACCENT)
        self.screen.blit(coins_txt, (180, 8))

        # distance / progress
        traveled = int(self.game.distance)
        remaining = self.game.remaining_distance
        dist_txt = self.f_small.render(
            f"{traveled} m   /   {FINISH_DISTANCE} m   ({remaining} m left)",
            True, TEXT)
        self.screen.blit(dist_txt, (WIN_W - dist_txt.get_width() - 12, 12))

        # progress bar
        bar_w, bar_h = WIN_W - 24, 6
        pygame.draw.rect(self.screen, (60, 60, 70), (12, 44, bar_w, bar_h))
        prog = min(1.0, self.game.distance / FINISH_DISTANCE)
        pygame.draw.rect(self.screen, GOOD, (12, 44, int(bar_w * prog), bar_h))

        # active power-up box
        if self.game.effect:
            x, y = 12, 60
            box = pygame.Rect(x, y, 220, 40)
            pygame.draw.rect(self.screen, PANEL, box, border_radius=8)
            pygame.draw.rect(self.screen, ACCENT, box, 2, border_radius=8)
            kind = self.game.effect.kind.title()
            if self.game.effect.duration is not None:
                t = max(0.0, self.game.effect.duration)
                msg = f"{kind}: {t:0.1f}s"
            else:
                msg = f"{kind}: until hit"
            self.screen.blit(self.f_small.render(msg, True, TEXT),
                             (x + 12, y + 11))

    def draw_over(self):
        # show a faded snapshot of the last frame behind a panel
        self.game.draw(self.screen)
        veil = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 170))
        self.screen.blit(veil, (0, 0))

        panel = pygame.Rect(WIN_W // 2 - 240, 130, 480, 380)
        draw_panel(self.screen, panel)

        title = "Finished!" if self.last_run.get("finished") else "Game over"
        title_color = GOOD if self.last_run.get("finished") else DANGER
        draw_centered_text(self.screen, title, self.f_big, title_color,
                           (WIN_W // 2, 175))

        lr = self.last_run
        rows = [
            ("Name",      lr["name"]),
            ("Score",     str(lr["score"])),
            ("Distance",  f'{lr["distance"]} m'),
            ("Coins",     str(lr["coins"])),
        ]
        y = 240
        for label, value in rows:
            ls = self.f_med.render(label, True, MUTED)
            vs = self.f_med.render(value, True, TEXT)
            self.screen.blit(ls, (panel.x + 40, y))
            self.screen.blit(vs, (panel.right - 40 - vs.get_width(), y))
            y += 44

        for b in self._over_buttons:
            b.draw(self.screen)

    def draw_settings(self):
        self.screen.fill(BG)
        draw_centered_text(self.screen, "Settings", self.f_big, ACCENT,
                           (WIN_W // 2, 120))
        draw_centered_text(self.screen, "Click any row to cycle its value",
                           self.f_small, MUTED, (WIN_W // 2, 160))

        for w in self._settings_widgets.values():
            w.draw(self.screen)

        # show the chosen car color as a small preview swatch
        color_name = self.settings.get("car_color", "red")
        color = CAR_COLORS.get(color_name, (220, 50, 50))
        sw = pygame.Rect(WIN_W // 2 + 235 - 140, 270, 30, 30)
        pygame.draw.rect(self.screen, color, sw, border_radius=6)
        pygame.draw.rect(self.screen, (20, 20, 20), sw, 2, border_radius=6)

    def draw_leaderboard(self):
        self.screen.fill(BG)
        draw_centered_text(self.screen, "Leaderboard — Top 10",
                           self.f_big, ACCENT, (WIN_W // 2, 80))

        panel = pygame.Rect(WIN_W // 2 - 320, 130, 640, 480)
        draw_panel(self.screen, panel)

        # header
        hx = panel.x + 24
        y = panel.y + 20
        headers = [("#", 0), ("Name", 60), ("Score", 280), ("Distance", 440)]
        for label, off in headers:
            self.screen.blit(self.f_small.render(label, True, MUTED),
                             (hx + off, y))
        pygame.draw.line(self.screen, MUTED,
                         (panel.x + 16, y + 24),
                         (panel.right - 16, y + 24), 1)

        entries = self._cached_leaderboard
        if not entries:
            draw_centered_text(self.screen, "No scores yet — go race!",
                               self.f_med, MUTED,
                               (WIN_W // 2, panel.centery))
        else:
            row_y = y + 36
            for rank, e in enumerate(entries, start=1):
                color = ACCENT if rank == 1 else TEXT
                self.screen.blit(self.f_med.render(f"{rank}", True, color),
                                 (hx, row_y))
                self.screen.blit(self.f_med.render(e["name"][:12], True, color),
                                 (hx + 60, row_y))
                self.screen.blit(self.f_med.render(str(e["score"]), True, color),
                                 (hx + 280, row_y))
                self.screen.blit(self.f_med.render(f'{e["distance"]} m', True, color),
                                 (hx + 440, row_y))
                row_y += 36

        for b in self._leaderboard_buttons:
            b.draw(self.screen)

    # ------------------------------------------------------------------
    # main loop
    # ------------------------------------------------------------------
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.update(dt)

            if self.state == S_MENU:
                self.draw_menu()
            elif self.state == S_NAME:
                self.draw_name()
            elif self.state == S_PLAY:
                self.draw_play()
            elif self.state == S_OVER:
                self.draw_over()
            elif self.state == S_SETTINGS:
                self.draw_settings()
            elif self.state == S_LEADERBOARD:
                self.draw_leaderboard()

            pygame.display.flip()

        pygame.quit()
        sys.exit(0)


if __name__ == "__main__":
    App().run()
