"""
paint.py
--------
A small Paint application built with Pygame.

Features (TSIS2):
  * Pencil (freehand)
  * Straight line with live preview
  * Rectangle / Circle / Ellipse / Triangle (live preview) — all respect brush size
  * Three brush sizes (small / medium / large) — keys 1, 2, 3 or toolbar
  * Flood-fill using get_at / set_at
  * Text tool — click to place, type, Enter to confirm, Escape to cancel
  * Eraser
  * Ctrl+S saves the canvas as a timestamped .png

Keyboard shortcuts:
  P  pencil          L  straight line
  R  rectangle       C  circle           E  ellipse        T  triangle
  F  fill            X  text             B  eraser
  1  small brush     2  medium brush     3  large brush
  Ctrl+S  save       Ctrl+Z  undo last stroke (best-effort)
"""

import os
import sys
import datetime
import pygame

from tools import (
    PENCIL, LINE, RECT, CIRCLE, ELLIPSE, TRIANGLE, FILL, TEXT, ERASER,
    BRUSH_SIZES, PALETTE, Button,
    draw_pencil_segment, draw_straight_line,
    draw_rect, draw_circle, draw_ellipse, draw_triangle,
    flood_fill,
)


# ---------------------------------------------------------------------------
# Window / canvas geometry
# ---------------------------------------------------------------------------
WIN_W, WIN_H = 1100, 720
TOOLBAR_H = 90
CANVAS_RECT = pygame.Rect(0, TOOLBAR_H, WIN_W, WIN_H - TOOLBAR_H)
CANVAS_BG = (255, 255, 255)


# ---------------------------------------------------------------------------
# Toolbar layout
# ---------------------------------------------------------------------------
def build_toolbar():
    """Return a list of Button objects laid out across the toolbar."""
    buttons = []
    x, y, w, h = 8, 8, 70, 28
    gap = 4

    # row 1 — tool buttons
    tool_specs = [
        ("Pencil",  PENCIL),
        ("Line",    LINE),
        ("Rect",    RECT),
        ("Circle",  CIRCLE),
        ("Ellipse", ELLIPSE),
        ("Tri",     TRIANGLE),
        ("Fill",    FILL),
        ("Text",    TEXT),
        ("Eraser",  ERASER),
    ]
    cx = x
    for label, tool in tool_specs:
        buttons.append(Button((cx, y, w, h), label, "tool", payload=tool))
        cx += w + gap

    # brush size buttons (right of tools, same row)
    cx += 12
    for label, key in [("S", "small"), ("M", "medium"), ("L", "large")]:
        buttons.append(Button((cx, y, 30, h), label, "size", payload=key))
        cx += 30 + gap

    # save / clear buttons
    cx += 12
    buttons.append(Button((cx, y, 60, h), "Save", "save"))
    cx += 60 + gap
    buttons.append(Button((cx, y, 60, h), "Clear", "clear"))

    # row 2 — color palette swatches
    sx, sy, sw = 8, y + h + 10, 32
    for i, color in enumerate(PALETTE):
        buttons.append(
            Button((sx + i * (sw + gap), sy, sw, sw), "", "color", payload=color)
        )

    return buttons


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------
class PaintApp:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("TSIS2 — Paint")
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        self.clock = pygame.time.Clock()

        # canvas is a separate surface — we blit it onto the screen each frame.
        # keeping it separate makes save / flood-fill / undo simpler.
        self.canvas = pygame.Surface((CANVAS_RECT.w, CANVAS_RECT.h))
        self.canvas.fill(CANVAS_BG)

        self.font_ui = pygame.font.SysFont("arial", 14)
        self.font_status = pygame.font.SysFont("arial", 13)
        self.font_text_tool = pygame.font.SysFont("arial", 22)

        self.buttons = build_toolbar()

        # current state
        self.tool = PENCIL
        self.color = (0, 0, 0)
        self.brush_size = BRUSH_SIZES["medium"]
        self.brush_key = "medium"

        # mouse / shape state
        self.drawing = False
        self.last_pos = None         # for pencil: previous mouse position
        self.shape_start = None      # for shape tools: anchor point
        self.preview_end = None      # current mouse pos while dragging

        # text tool state
        self.text_pos = None
        self.text_buffer = ""

        # undo stack — store snapshots of the canvas before each stroke
        self.undo_stack = []
        self.UNDO_LIMIT = 20

    # ------------------------------------------------------------------
    # coordinate helpers — the canvas surface is offset by TOOLBAR_H
    # ------------------------------------------------------------------
    def to_canvas(self, pos):
        return (pos[0] - CANVAS_RECT.x, pos[1] - CANVAS_RECT.y)

    def in_canvas(self, pos):
        return CANVAS_RECT.collidepoint(pos)

    # ------------------------------------------------------------------
    # undo
    # ------------------------------------------------------------------
    def push_undo(self):
        snap = self.canvas.copy()
        self.undo_stack.append(snap)
        if len(self.undo_stack) > self.UNDO_LIMIT:
            self.undo_stack.pop(0)

    def undo(self):
        if self.undo_stack:
            self.canvas = self.undo_stack.pop()

    # ------------------------------------------------------------------
    # save
    # ------------------------------------------------------------------
    def save_canvas(self):
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"canvas_{ts}.png"
        out_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(out_dir, filename)
        pygame.image.save(self.canvas, path)
        print(f"[save] {path}")
        return filename

    # ------------------------------------------------------------------
    # event handling
    # ------------------------------------------------------------------
    def handle_button(self, btn):
        if btn.action == "tool":
            self.commit_text()       # make sure pending text isn't lost
            self.tool = btn.payload
            self.cancel_shape()
        elif btn.action == "size":
            self.brush_key = btn.payload
            self.brush_size = BRUSH_SIZES[btn.payload]
        elif btn.action == "color":
            self.color = btn.payload
        elif btn.action == "save":
            self.save_canvas()
        elif btn.action == "clear":
            self.push_undo()
            self.canvas.fill(CANVAS_BG)

    def cancel_shape(self):
        self.drawing = False
        self.shape_start = None
        self.preview_end = None
        self.last_pos = None

    # text-tool helpers ------------------------------------------------
    def commit_text(self):
        """Render the typed string permanently onto the canvas."""
        if self.text_pos is not None and self.text_buffer:
            surf = self.font_text_tool.render(self.text_buffer, True, self.color)
            self.canvas.blit(surf, self.text_pos)
        self.text_pos = None
        self.text_buffer = ""

    def cancel_text(self):
        self.text_pos = None
        self.text_buffer = ""

    # mouse ------------------------------------------------------------
    def on_mouse_down(self, pos, button):
        # toolbar click
        if pos[1] < TOOLBAR_H:
            for b in self.buttons:
                if b.hit(pos):
                    self.handle_button(b)
                    return
            return

        if not self.in_canvas(pos):
            return
        cpos = self.to_canvas(pos)

        # Text tool: clicking places (or moves) the cursor.
        # If something is already typed, commit it first.
        if self.tool == TEXT:
            self.commit_text()
            self.text_pos = cpos
            self.text_buffer = ""
            return

        # Fill tool — single click action
        if self.tool == FILL:
            self.push_undo()
            flood_fill(self.canvas, cpos, self.color,
                       pygame.Rect(0, 0, CANVAS_RECT.w, CANVAS_RECT.h))
            return

        # Eraser is just pencil with the canvas background color
        # all other tools share the same drag lifecycle
        if button == 1:
            self.push_undo()
            self.drawing = True
            self.last_pos = cpos
            self.shape_start = cpos
            self.preview_end = cpos

            # pencil and eraser draw a dot immediately so single clicks register
            if self.tool in (PENCIL, ERASER):
                draw_color = CANVAS_BG if self.tool == ERASER else self.color
                pygame.draw.circle(self.canvas, draw_color, cpos,
                                   max(1, self.brush_size // 2))

    def on_mouse_motion(self, pos):
        if not self.drawing:
            return
        # clamp to canvas so strokes don't bleed into the toolbar
        cpos = self.to_canvas(pos)
        cpos = (
            max(0, min(CANVAS_RECT.w - 1, cpos[0])),
            max(0, min(CANVAS_RECT.h - 1, cpos[1])),
        )

        if self.tool == PENCIL:
            draw_pencil_segment(self.canvas, self.color,
                                self.last_pos, cpos, self.brush_size)
            self.last_pos = cpos
        elif self.tool == ERASER:
            draw_pencil_segment(self.canvas, CANVAS_BG,
                                self.last_pos, cpos, self.brush_size)
            self.last_pos = cpos
        else:
            # shape tools just update the preview endpoint
            self.preview_end = cpos

    def on_mouse_up(self, pos):
        if not self.drawing:
            return
        cpos = self.to_canvas(pos)
        cpos = (
            max(0, min(CANVAS_RECT.w - 1, cpos[0])),
            max(0, min(CANVAS_RECT.h - 1, cpos[1])),
        )

        # commit the shape on release
        if self.tool == LINE:
            draw_straight_line(self.canvas, self.color,
                               self.shape_start, cpos, self.brush_size)
        elif self.tool == RECT:
            draw_rect(self.canvas, self.color,
                      self.shape_start, cpos, self.brush_size)
        elif self.tool == CIRCLE:
            draw_circle(self.canvas, self.color,
                        self.shape_start, cpos, self.brush_size)
        elif self.tool == ELLIPSE:
            draw_ellipse(self.canvas, self.color,
                         self.shape_start, cpos, self.brush_size)
        elif self.tool == TRIANGLE:
            draw_triangle(self.canvas, self.color,
                          self.shape_start, cpos, self.brush_size)

        self.cancel_shape()

    # keyboard ---------------------------------------------------------
    def on_key(self, event):
        # text-input mode swallows almost every key
        if self.text_pos is not None:
            if event.key == pygame.K_RETURN:
                self.commit_text()
                return
            if event.key == pygame.K_ESCAPE:
                self.cancel_text()
                return
            if event.key == pygame.K_BACKSPACE:
                self.text_buffer = self.text_buffer[:-1]
                return
            # Ctrl+S still works during text entry
            if event.key == pygame.K_s and (event.mod & pygame.KMOD_CTRL):
                self.save_canvas()
                return
            # only accept printable characters
            if event.unicode and event.unicode.isprintable():
                self.text_buffer += event.unicode
            return

        # global shortcuts
        if event.key == pygame.K_s and (event.mod & pygame.KMOD_CTRL):
            self.save_canvas()
            return
        if event.key == pygame.K_z and (event.mod & pygame.KMOD_CTRL):
            self.undo()
            return

        # tool shortcuts
        keymap = {
            pygame.K_p: PENCIL, pygame.K_l: LINE, pygame.K_r: RECT,
            pygame.K_c: CIRCLE, pygame.K_e: ELLIPSE, pygame.K_t: TRIANGLE,
            pygame.K_f: FILL,   pygame.K_x: TEXT,   pygame.K_b: ERASER,
        }
        if event.key in keymap:
            self.tool = keymap[event.key]
            self.cancel_shape()
            return

        # brush sizes
        if event.key == pygame.K_1:
            self.brush_size, self.brush_key = BRUSH_SIZES["small"], "small"
        elif event.key == pygame.K_2:
            self.brush_size, self.brush_key = BRUSH_SIZES["medium"], "medium"
        elif event.key == pygame.K_3:
            self.brush_size, self.brush_key = BRUSH_SIZES["large"], "large"

    # ------------------------------------------------------------------
    # rendering
    # ------------------------------------------------------------------
    def draw_toolbar(self):
        pygame.draw.rect(self.screen, (240, 240, 240),
                         (0, 0, WIN_W, TOOLBAR_H))
        pygame.draw.line(self.screen, (160, 160, 160),
                         (0, TOOLBAR_H), (WIN_W, TOOLBAR_H), 1)

        for b in self.buttons:
            active = False
            swatch = None
            if b.action == "tool":
                active = (b.payload == self.tool)
            elif b.action == "size":
                active = (b.payload == self.brush_key)
            elif b.action == "color":
                swatch = b.payload
                active = (b.payload == self.color)
            b.draw(self.screen, self.font_ui, active=active, swatch_color=swatch)

    def draw_preview(self):
        """Draw the in-progress shape on top of the canvas (not committed)."""
        if not self.drawing or self.tool in (PENCIL, ERASER):
            return
        if self.shape_start is None or self.preview_end is None:
            return

        # offset the preview so it appears in the right place on screen
        s = (self.shape_start[0] + CANVAS_RECT.x,
             self.shape_start[1] + CANVAS_RECT.y)
        e = (self.preview_end[0] + CANVAS_RECT.x,
             self.preview_end[1] + CANVAS_RECT.y)

        if self.tool == LINE:
            draw_straight_line(self.screen, self.color, s, e, self.brush_size)
        elif self.tool == RECT:
            draw_rect(self.screen, self.color, s, e, self.brush_size)
        elif self.tool == CIRCLE:
            draw_circle(self.screen, self.color, s, e, self.brush_size)
        elif self.tool == ELLIPSE:
            draw_ellipse(self.screen, self.color, s, e, self.brush_size)
        elif self.tool == TRIANGLE:
            draw_triangle(self.screen, self.color, s, e, self.brush_size)

    def draw_text_tool_overlay(self):
        if self.text_pos is None:
            return
        screen_pos = (self.text_pos[0] + CANVAS_RECT.x,
                      self.text_pos[1] + CANVAS_RECT.y)

        # show what the user has typed so far
        if self.text_buffer:
            surf = self.font_text_tool.render(self.text_buffer, True, self.color)
            self.screen.blit(surf, screen_pos)
            cursor_x = screen_pos[0] + surf.get_width()
        else:
            cursor_x = screen_pos[0]

        # blinking caret
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            ch = self.font_text_tool.get_height()
            pygame.draw.line(self.screen, self.color,
                             (cursor_x, screen_pos[1]),
                             (cursor_x, screen_pos[1] + ch), 2)

    def draw_status_bar(self):
        msg = (f"Tool: {self.tool}   Size: {self.brush_key} ({self.brush_size}px)   "
               f"Color: {self.color}   "
               f"Shortcuts: P L R C E T F X B | 1 2 3 | Ctrl+S save | Ctrl+Z undo")
        surf = self.font_status.render(msg, True, (40, 40, 40))
        self.screen.blit(surf, (8, WIN_H - 20))

    # ------------------------------------------------------------------
    # main loop
    # ------------------------------------------------------------------
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.on_mouse_down(event.pos, event.button)
                elif event.type == pygame.MOUSEMOTION:
                    self.on_mouse_motion(event.pos)
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.on_mouse_up(event.pos)
                elif event.type == pygame.KEYDOWN:
                    self.on_key(event)

            # render
            self.screen.fill((255, 255, 255))
            self.screen.blit(self.canvas, CANVAS_RECT.topleft)
            self.draw_preview()
            self.draw_text_tool_overlay()
            self.draw_toolbar()
            self.draw_status_bar()

            pygame.display.flip()
            self.clock.tick(120)

        pygame.quit()
        sys.exit(0)


if __name__ == "__main__":
    PaintApp().run()
