"""
tools.py
--------
Helper classes and functions for the Paint application.
Keeps drawing-tool logic separate from the main event loop.
"""

import pygame
from collections import deque


# ---------------------------------------------------------------------------
# Tool name constants — use these instead of raw strings to avoid typos
# ---------------------------------------------------------------------------
PENCIL = "pencil"
LINE = "line"
RECT = "rect"
CIRCLE = "circle"
ELLIPSE = "ellipse"
TRIANGLE = "triangle"
FILL = "fill"
TEXT = "text"
ERASER = "eraser"


# ---------------------------------------------------------------------------
# Brush sizes
# ---------------------------------------------------------------------------
BRUSH_SIZES = {
    "small": 2,
    "medium": 5,
    "large": 10,
}


# ---------------------------------------------------------------------------
# Color palette used by the toolbar
# ---------------------------------------------------------------------------
PALETTE = [
    (0, 0, 0),         # black
    (255, 255, 255),   # white
    (255, 0, 0),       # red
    (0, 200, 0),       # green
    (0, 0, 255),       # blue
    (255, 255, 0),     # yellow
    (255, 128, 0),     # orange
    (160, 32, 240),    # purple
    (0, 200, 200),     # cyan
    (255, 105, 180),   # pink
]


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------
def draw_pencil_segment(surface, color, p1, p2, width):
    """Draw a line segment between two consecutive mouse positions.
    A small filled circle is added at each endpoint to avoid the
    'gap' that pygame.draw.line leaves at thicker widths."""
    pygame.draw.line(surface, color, p1, p2, width)
    # round the joints so thick strokes look smooth
    pygame.draw.circle(surface, color, p1, max(1, width // 2))
    pygame.draw.circle(surface, color, p2, max(1, width // 2))


def draw_straight_line(surface, color, start, end, width):
    pygame.draw.line(surface, color, start, end, width)


def draw_rect(surface, color, start, end, width):
    x = min(start[0], end[0])
    y = min(start[1], end[1])
    w = abs(end[0] - start[0])
    h = abs(end[1] - start[1])
    if w > 0 and h > 0:
        pygame.draw.rect(surface, color, (x, y, w, h), width)


def draw_circle(surface, color, start, end, width):
    """Circle defined by center=start, radius = distance to end."""
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    radius = int((dx * dx + dy * dy) ** 0.5)
    if radius > 0:
        pygame.draw.circle(surface, color, start, radius, width)


def draw_ellipse(surface, color, start, end, width):
    x = min(start[0], end[0])
    y = min(start[1], end[1])
    w = abs(end[0] - start[0])
    h = abs(end[1] - start[1])
    if w > 0 and h > 0:
        pygame.draw.ellipse(surface, color, (x, y, w, h), width)


def draw_triangle(surface, color, start, end, width):
    """Isosceles triangle inside the bounding box (start, end)."""
    x1, y1 = start
    x2, y2 = end
    apex = ((x1 + x2) // 2, min(y1, y2))
    bl = (min(x1, x2), max(y1, y2))
    br = (max(x1, x2), max(y1, y2))
    pygame.draw.polygon(surface, color, [apex, bl, br], width)


# ---------------------------------------------------------------------------
# Flood fill — scanline-style BFS using get_at / set_at
# ---------------------------------------------------------------------------
def flood_fill(surface, pos, fill_color, bounds):
    """Flood-fill starting at `pos` with `fill_color`.

    `bounds` is a pygame.Rect that limits the fill area to the canvas.
    Uses an iterative BFS with a deque so we don't blow the recursion stack
    on large regions. Exact-color match is the boundary rule (per spec).
    """
    x0, y0 = pos
    if not bounds.collidepoint(x0, y0):
        return

    target = surface.get_at((x0, y0))
    fill = pygame.Color(*fill_color)

    # nothing to do if the click is already on the target color
    if target == fill:
        return

    # surface lock greatly speeds up many get_at/set_at calls
    surface.lock()
    try:
        queue = deque()
        queue.append((x0, y0))
        min_x, min_y = bounds.left, bounds.top
        max_x, max_y = bounds.right - 1, bounds.bottom - 1

        while queue:
            x, y = queue.popleft()
            if x < min_x or x > max_x or y < min_y or y > max_y:
                continue
            if surface.get_at((x, y)) != target:
                continue

            # walk left to find the start of the run
            lx = x
            while lx >= min_x and surface.get_at((lx, y)) == target:
                lx -= 1
            lx += 1

            # walk right and paint the run; queue pixels above/below
            rx = lx
            while rx <= max_x and surface.get_at((rx, y)) == target:
                surface.set_at((rx, y), fill)
                if y - 1 >= min_y and surface.get_at((rx, y - 1)) == target:
                    queue.append((rx, y - 1))
                if y + 1 <= max_y and surface.get_at((rx, y + 1)) == target:
                    queue.append((rx, y + 1))
                rx += 1
    finally:
        surface.unlock()


# ---------------------------------------------------------------------------
# Toolbar button — minimal clickable rectangle with a label
# ---------------------------------------------------------------------------
class Button:
    def __init__(self, rect, label, action, *, payload=None):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.action = action          # short string like "tool" / "size" / "color"
        self.payload = payload        # the value to apply when clicked

    def draw(self, surface, font, *, active=False, swatch_color=None):
        # background
        bg = (220, 220, 220) if not active else (255, 230, 120)
        pygame.draw.rect(surface, bg, self.rect)
        pygame.draw.rect(surface, (60, 60, 60), self.rect, 1)

        # color swatch buttons render a filled square instead of text
        if swatch_color is not None:
            inner = self.rect.inflate(-8, -8)
            pygame.draw.rect(surface, swatch_color, inner)
            pygame.draw.rect(surface, (40, 40, 40), inner, 1)
        else:
            text = font.render(self.label, True, (20, 20, 20))
            tr = text.get_rect(center=self.rect.center)
            surface.blit(text, tr)

    def hit(self, pos):
        return self.rect.collidepoint(pos)
