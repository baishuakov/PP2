"""
ui.py
-----
Small UI helpers built on raw pygame: buttons, a text-input widget,
and a couple of layout/draw utilities used by the menu screens.
No external UI libraries.
"""

import pygame


# ---------------------------------------------------------------------------
# Color palette for UI
# ---------------------------------------------------------------------------
BG = (22, 26, 34)
PANEL = (32, 38, 50)
ACCENT = (255, 196, 0)
TEXT = (235, 235, 235)
MUTED = (140, 150, 165)
BTN_BG = (52, 60, 78)
BTN_BG_HOVER = (78, 90, 118)
BTN_BORDER = (110, 120, 140)
DANGER = (220, 70, 70)
GOOD = (90, 200, 120)


# ---------------------------------------------------------------------------
# Button
# ---------------------------------------------------------------------------
class Button:
    """A simple rectangular button with hover state and an action callback.

    `on_click` is a zero-arg callable invoked when the button is clicked.
    """
    def __init__(self, rect, label, on_click, *, font=None,
                 bg=BTN_BG, bg_hover=BTN_BG_HOVER, fg=TEXT):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.on_click = on_click
        self.font = font
        self.bg = bg
        self.bg_hover = bg_hover
        self.fg = fg
        self.hovered = False

    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.on_click()
                return True
        return False

    def draw(self, surface):
        pygame.draw.rect(surface,
                         self.bg_hover if self.hovered else self.bg,
                         self.rect, border_radius=8)
        pygame.draw.rect(surface, BTN_BORDER, self.rect, 2, border_radius=8)
        if self.font:
            text = self.font.render(self.label, True, self.fg)
            surface.blit(text, text.get_rect(center=self.rect.center))


# ---------------------------------------------------------------------------
# Toggle / cycler — used by Settings
# ---------------------------------------------------------------------------
class OptionCycler:
    """Click to cycle through a list of options (e.g. difficulty levels)."""
    def __init__(self, rect, label, options, current_index, on_change, *, font=None):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.options = options
        self.index = current_index % len(options)
        self.on_change = on_change
        self.font = font
        self.hovered = False

    @property
    def value(self):
        return self.options[self.index]

    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.index = (self.index + 1) % len(self.options)
                self.on_change(self.value)
                return True
        return False

    def draw(self, surface):
        pygame.draw.rect(surface,
                         BTN_BG_HOVER if self.hovered else BTN_BG,
                         self.rect, border_radius=8)
        pygame.draw.rect(surface, BTN_BORDER, self.rect, 2, border_radius=8)

        if self.font:
            label_surf = self.font.render(self.label, True, MUTED)
            value_surf = self.font.render(str(self.value).title(), True, ACCENT)
            surface.blit(label_surf, (self.rect.x + 14,
                                      self.rect.y + (self.rect.h - label_surf.get_height()) // 2))
            surface.blit(value_surf,
                         (self.rect.right - value_surf.get_width() - 14,
                          self.rect.y + (self.rect.h - value_surf.get_height()) // 2))


# ---------------------------------------------------------------------------
# Text input — used for username entry on the start screen
# ---------------------------------------------------------------------------
class TextInput:
    def __init__(self, rect, *, font=None, max_length=12, placeholder="Your name"):
        self.rect = pygame.Rect(rect)
        self.font = font
        self.max_length = max_length
        self.placeholder = placeholder
        self.text = ""
        self.active = True   # focused by default; only one input on screen at a time

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active = self.rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                return "submit"
            elif event.unicode and event.unicode.isprintable():
                if len(self.text) < self.max_length:
                    # block characters that would mess up the JSON file or display
                    if event.unicode not in ('"', "\\", "\t"):
                        self.text += event.unicode
        return None

    def draw(self, surface):
        bg = PANEL if self.active else BTN_BG
        pygame.draw.rect(surface, bg, self.rect, border_radius=8)
        pygame.draw.rect(surface, ACCENT if self.active else BTN_BORDER,
                         self.rect, 2, border_radius=8)

        if self.font:
            display_text = self.text if self.text else self.placeholder
            color = TEXT if self.text else MUTED
            surf = self.font.render(display_text, True, color)
            surface.blit(surf, (self.rect.x + 12,
                                self.rect.y + (self.rect.h - surf.get_height()) // 2))

            # blinking caret when focused
            if self.active and self.text and (pygame.time.get_ticks() // 500) % 2 == 0:
                caret_x = self.rect.x + 12 + surf.get_width() + 2
                pygame.draw.line(surface, TEXT,
                                 (caret_x, self.rect.y + 8),
                                 (caret_x, self.rect.bottom - 8), 2)


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------
def draw_centered_text(surface, text, font, color, center):
    surf = font.render(text, True, color)
    surface.blit(surf, surf.get_rect(center=center))


def draw_panel(surface, rect, *, title=None, title_font=None):
    pygame.draw.rect(surface, PANEL, rect, border_radius=12)
    pygame.draw.rect(surface, BTN_BORDER, rect, 2, border_radius=12)
    if title and title_font:
        t = title_font.render(title, True, ACCENT)
        surface.blit(t, (rect.x + 20, rect.y + 14))
