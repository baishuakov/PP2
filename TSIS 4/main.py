"""
main.py
-------
Entry point. Implements all four game screens as a state machine:

  MENU -> NAME_ENTRY -> PLAY -> GAME_OVER
  MENU -> LEADERBOARD -> MENU
  MENU -> SETTINGS -> MENU

Settings are loaded from settings.json at startup and saved on the
Settings screen. The DB connection is attempted at startup and
degrades gracefully if Postgres is unavailable.
"""

import sys
import os
import json
import datetime
import pygame

import config as C
import db
from game import Game, GameState, Dir, PowerUpKind, POWERUP_LABELS

# ── screen identifiers ─────────────────────────────────────────────────────
S_MENU        = "menu"
S_NAME        = "name_entry"
S_PLAY        = "play"
S_OVER        = "over"
S_LEADERBOARD = "leaderboard"
S_SETTINGS    = "settings"

SETTINGS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "settings.json")

DEFAULT_SETTINGS = {
    "snake_color": list(C.C_SNAKE_DEFAULT),
    "grid":        True,
    "sound":       True,
}


# ── tiny UI helpers ────────────────────────────────────────────────────────
class Button:
    def __init__(self, rect, label, action, *, font):
        self.rect  = pygame.Rect(rect)
        self.label = label
        self.action = action
        self.font   = font

    def draw(self, surface, mouse_pos):
        hover = self.rect.collidepoint(mouse_pos)
        bg = (70, 84, 110) if hover else (42, 50, 68)
        pygame.draw.rect(surface, bg, self.rect, border_radius=8)
        pygame.draw.rect(surface, (90, 100, 130), self.rect, 2, border_radius=8)
        lbl = self.font.render(self.label, True, C.C_TEXT)
        surface.blit(lbl, lbl.get_rect(center=self.rect.center))

    def hit(self, pos):
        return self.rect.collidepoint(pos)


def draw_text(surface, text, font, color, center):
    s = font.render(text, True, color)
    surface.blit(s, s.get_rect(center=center))


def draw_panel(surface, rect):
    pygame.draw.rect(surface, C.C_SIDEBAR, rect, border_radius=12)
    pygame.draw.rect(surface, C.C_BORDER,  rect, 2,  border_radius=12)


# ── App ────────────────────────────────────────────────────────────────────
class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("TSIS4 — Snake")
        self.screen = pygame.display.set_mode((C.WIN_W, C.WIN_H))
        self.clock  = pygame.time.Clock()

        self.f_title  = pygame.font.SysFont("arial", 48, bold=True)
        self.f_big    = pygame.font.SysFont("arial", 30, bold=True)
        self.f_med    = pygame.font.SysFont("arial", 20)
        self.f_small  = pygame.font.SysFont("arial", 15)

        self.settings   = self._load_settings()
        self.username   = ""
        self.player_id  = None
        self.personal_best = 0
        self.game       = None
        self.last_score = 0
        self.last_level = 1

        self._lb_cache  = []   # leaderboard rows from DB

        self.state      = S_MENU
        self._name_buf  = ""   # typed text on name-entry screen

        # try DB; non-fatal if it fails
        db.connect()

    # ── settings ──────────────────────────────────────────────────────────
    def _load_settings(self):
        try:
            with open(SETTINGS_PATH, "r") as f:
                data = json.load(f)
            merged = dict(DEFAULT_SETTINGS)
            merged.update({k: v for k, v in data.items()
                           if k in DEFAULT_SETTINGS})
            return merged
        except Exception:
            return dict(DEFAULT_SETTINGS)

    def _save_settings(self):
        try:
            with open(SETTINGS_PATH, "w") as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"[settings] save failed: {e}")

    @property
    def _snake_color(self):
        return tuple(self.settings["snake_color"])

    # ── transitions ───────────────────────────────────────────────────────
    def _start_game(self):
        self.personal_best = db.get_personal_best(self.player_id)
        self.game = Game(self._snake_color, self.personal_best)
        self.state = S_PLAY

    def _end_game(self):
        self.last_score = self.game.score
        self.last_level = self.game.level
        db.save_session(self.player_id, self.last_score, self.last_level)
        self.state = S_OVER

    def _open_leaderboard(self):
        self._lb_cache = db.get_top10()
        self.state = S_LEADERBOARD

    # ── main loop ─────────────────────────────────────────────────────────
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif self.state == S_MENU:
                    self._handle_menu(event)
                elif self.state == S_NAME:
                    self._handle_name(event)
                elif self.state == S_PLAY:
                    self._handle_play(event)
                elif self.state == S_OVER:
                    self._handle_over(event)
                elif self.state == S_LEADERBOARD:
                    self._handle_lb(event)
                elif self.state == S_SETTINGS:
                    self._handle_settings(event)

            # update game logic
            if self.state == S_PLAY and self.game:
                self.game.update()
                if self.game.state == GameState.DEAD:
                    self._end_game()

            # draw
            self.screen.fill(C.C_BG)
            if self.state == S_MENU:
                self._draw_menu()
            elif self.state == S_NAME:
                self._draw_name()
            elif self.state == S_PLAY:
                self._draw_play()
            elif self.state == S_OVER:
                self._draw_over()
            elif self.state == S_LEADERBOARD:
                self._draw_leaderboard()
            elif self.state == S_SETTINGS:
                self._draw_settings()

            pygame.display.flip()

        db.close()
        pygame.quit()
        sys.exit()

    # ── event handlers ────────────────────────────────────────────────────
    def _handle_menu(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mp = event.pos
            bw, bh = 240, 50
            cx = C.WIN_W // 2
            btns = self._menu_buttons()
            for b in btns:
                if b.hit(mp):
                    if b.action == "play":
                        self.state = S_NAME
                        self._name_buf = self.username
                    elif b.action == "lb":
                        self._open_leaderboard()
                    elif b.action == "settings":
                        self.state = S_SETTINGS
                    elif b.action == "quit":
                        pygame.event.post(pygame.event.Event(pygame.QUIT))
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            pygame.event.post(pygame.event.Event(pygame.QUIT))

    def _handle_name(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                name = self._name_buf.strip() or "Player"
                self.username  = name
                self.player_id = db.get_or_create_player(name)
                self._start_game()
            elif event.key == pygame.K_BACKSPACE:
                self._name_buf = self._name_buf[:-1]
            elif event.key == pygame.K_ESCAPE:
                self.state = S_MENU
            elif event.unicode and event.unicode.isprintable():
                if len(self._name_buf) < 20:
                    self._name_buf += event.unicode

    def _handle_play(self, event):
        DIR_MAP = {
            pygame.K_UP: Dir.UP, pygame.K_w: Dir.UP,
            pygame.K_DOWN: Dir.DOWN, pygame.K_s: Dir.DOWN,
            pygame.K_LEFT: Dir.LEFT, pygame.K_a: Dir.LEFT,
            pygame.K_RIGHT: Dir.RIGHT, pygame.K_d: Dir.RIGHT,
        }
        if event.type == pygame.KEYDOWN:
            if event.key in DIR_MAP:
                self.game.steer(DIR_MAP[event.key])
            elif event.key == pygame.K_ESCAPE:
                self._end_game()

    def _handle_over(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mp = event.pos
            for b in self._over_buttons():
                if b.hit(mp):
                    if b.action == "retry":
                        self._start_game()
                    elif b.action == "menu":
                        self.state = S_MENU
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self._start_game()
            elif event.key == pygame.K_ESCAPE:
                self.state = S_MENU

    def _handle_lb(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._back_button().hit(event.pos):
                self.state = S_MENU
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.state = S_MENU

    def _handle_settings(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mp = event.pos
            for b in self._settings_buttons():
                if b.hit(mp):
                    if b.action == "toggle_grid":
                        self.settings["grid"] = not self.settings["grid"]
                    elif b.action == "toggle_sound":
                        self.settings["sound"] = not self.settings["sound"]
                    elif b.action.startswith("color_"):
                        hexstr = b.action.split("_", 1)[1]
                        r = int(hexstr[0:2], 16)
                        g = int(hexstr[2:4], 16)
                        bl = int(hexstr[4:6], 16)
                        self.settings["snake_color"] = [r, g, bl]
                    elif b.action == "save_back":
                        self._save_settings()
                        self.state = S_MENU
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._save_settings()
            self.state = S_MENU

    # ── button factories ──────────────────────────────────────────────────
    def _menu_buttons(self):
        cx, bw, bh, gap = C.WIN_W // 2, 240, 50, 14
        labels = [("Play",        "play"),
                  ("Leaderboard", "lb"),
                  ("Settings",    "settings"),
                  ("Quit",        "quit")]
        y0 = 280
        return [Button((cx - bw//2, y0 + i*(bh+gap), bw, bh),
                       lbl, act, font=self.f_med)
                for i, (lbl, act) in enumerate(labels)]

    def _over_buttons(self):
        cx = C.WIN_W // 2
        bw, bh = 180, 48
        y = C.WIN_H // 2 + 100
        return [
            Button((cx - bw - 12, y, bw, bh), "Retry [R]", "retry", font=self.f_med),
            Button((cx + 12,      y, bw, bh), "Main Menu",  "menu",  font=self.f_med),
        ]

    def _back_button(self):
        return Button((C.WIN_W//2 - 80, C.WIN_H - 70, 160, 44),
                      "Back", "back", font=self.f_med)

    def _settings_buttons(self):
        cx, bw, bh, gap = C.WIN_W//2, 320, 46, 12
        y0 = 200
        btns = [
            Button((cx - bw//2, y0, bw, bh),
                   f"Grid overlay: {'ON' if self.settings['grid'] else 'OFF'}",
                   "toggle_grid", font=self.f_med),
            Button((cx - bw//2, y0 + bh + gap, bw, bh),
                   f"Sound: {'ON' if self.settings['sound'] else 'OFF'}",
                   "toggle_sound", font=self.f_med),
        ]
        # color swatches
        colors = [
            ("50C878", "Emerald"),
            ("4682B4", "Blue"),
            ("FFD700", "Gold"),
            ("FF6347", "Tomato"),
            ("DA70D6", "Orchid"),
        ]
        sw, sg = 56, 10
        total_w = len(colors) * sw + (len(colors)-1) * sg
        sx = cx - total_w // 2
        sy = y0 + 2*(bh+gap) + 30
        for hexcol, name in colors:
            btns.append(Button((sx, sy, sw, bh), "", f"color_{hexcol}",
                               font=self.f_small))
            sx += sw + sg

        # save & back
        btns.append(Button((cx - 80, C.WIN_H - 80, 160, 46),
                           "Save & Back", "save_back", font=self.f_med))
        return btns

    # ── draw routines ─────────────────────────────────────────────────────
    def _draw_menu(self):
        draw_text(self.screen, "🐍  Snake",
                  self.f_title, C.C_ACCENT, (C.WIN_W//2, 130))
        draw_text(self.screen, "Use arrow keys or WASD",
                  self.f_small, C.C_MUTED, (C.WIN_W//2, 200))
        mp = pygame.mouse.get_pos()
        for b in self._menu_buttons():
            b.draw(self.screen, mp)

        db_status = "DB: connected" if db.DB_AVAILABLE else "DB: offline (local mode)"
        db_color  = C.C_GOOD if db.DB_AVAILABLE else C.C_DANGER
        draw_text(self.screen, db_status,
                  self.f_small, db_color, (C.WIN_W//2, C.WIN_H - 30))

    def _draw_name(self):
        draw_text(self.screen, "Enter your name",
                  self.f_big, C.C_ACCENT, (C.WIN_W//2, 220))
        draw_text(self.screen, "(press Enter to start, Esc to go back)",
                  self.f_small, C.C_MUTED, (C.WIN_W//2, 265))

        # input box
        bw, bh = 340, 52
        box = pygame.Rect(C.WIN_W//2 - bw//2, 300, bw, bh)
        pygame.draw.rect(self.screen, C.C_SIDEBAR, box, border_radius=8)
        pygame.draw.rect(self.screen, C.C_ACCENT,  box, 2,  border_radius=8)

        display = self._name_buf if self._name_buf else "Player"
        color   = C.C_TEXT if self._name_buf else C.C_MUTED
        txt = self.f_big.render(display, True, color)
        self.screen.blit(txt, (box.x + 14, box.y + (bh - txt.get_height())//2))

        # blinking caret
        if self._name_buf and (pygame.time.get_ticks()//500) % 2 == 0:
            caret_x = box.x + 14 + txt.get_width() + 2
            pygame.draw.line(self.screen, C.C_TEXT,
                             (caret_x, box.y+10), (caret_x, box.bottom-10), 2)

    def _draw_play(self):
        g = self.game
        # arena
        g.draw(self.screen, self.settings["grid"])

        # sidebar
        sx = C.ARENA_COLS * C.CELL
        sw = C.WIN_W - sx
        pygame.draw.rect(self.screen, C.C_SIDEBAR,
                         (sx, 0, sw, C.WIN_H))
        pygame.draw.line(self.screen, C.C_BORDER,
                         (sx, 0), (sx, C.WIN_H), 2)

        def sb_text(label, value, y, vc=C.C_TEXT):
            ls = self.f_small.render(label, True, C.C_MUTED)
            vs = self.f_med.render(str(value), True, vc)
            self.screen.blit(ls, (sx + 14, y))
            self.screen.blit(vs, (sx + 14, y + 18))

        y = 20
        sb_text("SCORE",  g.score,         y, C.C_ACCENT)
        sb_text("BEST",   g.personal_best, y + 60)
        sb_text("LEVEL",  g.level,         y + 120)
        sb_text("LENGTH", len(g.snake.body), y + 180)
        sb_text("PLAYER", self.username or "—", y + 240, C.C_GOOD)

        # active effect
        if g.effect:
            kind = g.effect.kind
            from game import POWERUP_COLORS
            color = POWERUP_COLORS[kind]
            label = POWERUP_LABELS[kind]
            ey = y + 310
            draw_text(self.screen, "ACTIVE", self.f_small, C.C_MUTED,
                      (sx + sw//2, ey))
            draw_text(self.screen, label, self.f_med, color,
                      (sx + sw//2, ey + 22))
            if g.effect.remaining_ms >= 0:
                secs = g.effect.remaining_ms / 1000
                draw_text(self.screen, f"{secs:.1f}s",
                          self.f_small, C.C_MUTED, (sx + sw//2, ey + 46))

        # controls reminder
        draw_text(self.screen, "ESC = forfeit",
                  self.f_small, C.C_MUTED, (sx + sw//2, C.WIN_H - 24))

    def _draw_over(self):
        panel = pygame.Rect(C.WIN_W//2 - 260, C.WIN_H//2 - 180, 520, 360)
        draw_panel(self.screen, panel)

        draw_text(self.screen, "GAME OVER",
                  self.f_title, C.C_DANGER, (C.WIN_W//2, C.WIN_H//2 - 130))

        rows = [
            ("Score",         str(self.last_score), C.C_ACCENT),
            ("Level reached", str(self.last_level),  C.C_TEXT),
            ("Personal best", str(max(self.last_score,
                                      self.personal_best)), C.C_GOOD),
        ]
        y = C.WIN_H//2 - 60
        for label, value, color in rows:
            ls = self.f_med.render(label, True, C.C_MUTED)
            vs = self.f_med.render(value,  True, color)
            self.screen.blit(ls, (panel.x + 40, y))
            self.screen.blit(vs, (panel.right - 40 - vs.get_width(), y))
            y += 40

        mp = pygame.mouse.get_pos()
        for b in self._over_buttons():
            b.draw(self.screen, mp)

    def _draw_leaderboard(self):
        draw_text(self.screen, "Leaderboard — Top 10",
                  self.f_big, C.C_ACCENT, (C.WIN_W//2, 60))

        panel = pygame.Rect(C.WIN_W//2 - 340, 100, 680, 460)
        draw_panel(self.screen, panel)

        # header
        cols = [(40, "#"), (80, "Username"), (320, "Score"),
                (420, "Level"), (520, "Date")]
        y = panel.y + 16
        for x_off, hdr in cols:
            h = self.f_small.render(hdr, True, C.C_MUTED)
            self.screen.blit(h, (panel.x + x_off, y))
        pygame.draw.line(self.screen, C.C_BORDER,
                         (panel.x + 20, y + 22),
                         (panel.right - 20, y + 22))

        if not self._lb_cache:
            draw_text(self.screen, "No scores yet — go play!",
                      self.f_med, C.C_MUTED, (C.WIN_W//2, panel.centery))
        else:
            ry = y + 32
            for rank, row in enumerate(self._lb_cache, 1):
                color = C.C_ACCENT if rank == 1 else C.C_TEXT
                played = row.get("played_at", "")
                if isinstance(played, datetime.datetime):
                    played = played.strftime("%Y-%m-%d")
                else:
                    played = str(played)[:10]
                cells = [
                    (40,  str(rank)),
                    (80,  str(row.get("username", ""))[:16]),
                    (320, str(row.get("score", 0))),
                    (420, str(row.get("level_reached", "—"))),
                    (520, played),
                ]
                for x_off, val in cells:
                    s = self.f_med.render(val, True, color)
                    self.screen.blit(s, (panel.x + x_off, ry))
                ry += 36

        mp = pygame.mouse.get_pos()
        self._back_button().draw(self.screen, mp)

        if not db.DB_AVAILABLE:
            draw_text(self.screen, "DB offline — scores not saved",
                      self.f_small, C.C_DANGER, (C.WIN_W//2, C.WIN_H - 30))

    def _draw_settings(self):
        draw_text(self.screen, "Settings",
                  self.f_big, C.C_ACCENT, (C.WIN_W//2, 100))

        mp = pygame.mouse.get_pos()
        btns = self._settings_buttons()

        # draw normal buttons
        for b in btns:
            if b.action.startswith("color_"):
                continue   # drawn separately
            b.draw(self.screen, mp)

        # color swatches label
        draw_text(self.screen, "Snake color",
                  self.f_small, C.C_MUTED,
                  (C.WIN_W//2, 340))

        # draw swatch buttons as colored squares
        colors_hex = [
            ("50C878", (80,200,120)),
            ("4682B4", (70,130,180)),
            ("FFD700", (255,215,0)),
            ("FF6347", (255,99,71)),
            ("DA70D6", (218,112,214)),
        ]
        sw, sg, bh = 56, 10, 46
        total_w = len(colors_hex) * sw + (len(colors_hex)-1) * sg
        sx = C.WIN_W//2 - total_w//2
        sy = 360
        current_color = tuple(self.settings["snake_color"])
        for hexcol, rgb in colors_hex:
            rect = pygame.Rect(sx, sy, sw, bh)
            pygame.draw.rect(self.screen, rgb, rect, border_radius=8)
            if current_color == rgb:
                pygame.draw.rect(self.screen, (255,255,255), rect, 3, border_radius=8)
            else:
                pygame.draw.rect(self.screen, (60,60,80), rect, 1, border_radius=8)
            sx += sw + sg

        # save & back button
        btns[-1].draw(self.screen, mp)

        draw_text(self.screen, "Changes saved automatically on exit",
                  self.f_small, C.C_MUTED, (C.WIN_W//2, C.WIN_H - 50))


# ── entry point ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    App().run()
