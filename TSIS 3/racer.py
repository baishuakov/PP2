"""
The world scrolls downward — the player stays on screen and the track
moves underneath. All "speed" values are pixels per second; the main
loop multiplies them by dt so behavior is framerate-independent.
"""

import math
import random
import pygame


# ---------------------------------------------------------------------------
# Track / lane geometry
# ---------------------------------------------------------------------------
ROAD_LEFT = 120
ROAD_RIGHT = 680
ROAD_WIDTH = ROAD_RIGHT - ROAD_LEFT
LANES = 4
LANE_WIDTH = ROAD_WIDTH / LANES
# x-coordinate of the center of each lane
LANE_CENTERS = [ROAD_LEFT + LANE_WIDTH * (i + 0.5) for i in range(LANES)]


# Total race distance in "world meters" (1 m = 1 px scrolled)
FINISH_DISTANCE = 5000


# Car colors — selectable in Settings
CAR_COLORS = {
    "red":    (220, 50, 50),
    "blue":   (60, 130, 230),
    "green":  (70, 190, 90),
    "yellow": (240, 210, 60),
    "white":  (235, 235, 235),
}


# Difficulty multipliers — applied to base speeds and spawn rates
DIFFICULTY = {
    "easy":   {"speed": 0.85, "spawn": 0.75, "scaling": 0.7},
    "normal": {"speed": 1.00, "spawn": 1.00, "scaling": 1.0},
    "hard":   {"speed": 1.20, "spawn": 1.35, "scaling": 1.4},
}


# ---------------------------------------------------------------------------
# Player car
# ---------------------------------------------------------------------------
class Player:
    WIDTH = 44
    HEIGHT = 70
    BASE_SPEED = 320          # lateral movement speed (px/s)

    def __init__(self, color_name, screen_h):
        self.color = CAR_COLORS.get(color_name, CAR_COLORS["red"])
        # start centered between lanes 1 and 2, near bottom
        self.x = (LANE_CENTERS[1] + LANE_CENTERS[2]) / 2
        self.y = screen_h - 120
        self.screen_h = screen_h

    @property
    def rect(self):
        return pygame.Rect(int(self.x - self.WIDTH / 2),
                           int(self.y - self.HEIGHT / 2),
                           self.WIDTH, self.HEIGHT)

    def update(self, keys, dt, slow_factor=1.0):
        speed = self.BASE_SPEED * slow_factor
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= speed * dt
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += speed * dt
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.y -= speed * 0.6 * dt
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.y += speed * 0.6 * dt

        # clamp inside road & lower part of screen
        half_w = self.WIDTH / 2
        self.x = max(ROAD_LEFT + half_w, min(ROAD_RIGHT - half_w, self.x))
        self.y = max(self.screen_h * 0.35,
                     min(self.screen_h - self.HEIGHT / 2 - 10, self.y))

    def draw(self, surface):
        # body
        body = self.rect
        pygame.draw.rect(surface, self.color, body, border_radius=8)
        pygame.draw.rect(surface, (20, 20, 20), body, 2, border_radius=8)
        # windshield
        ws = pygame.Rect(body.x + 6, body.y + 12, body.w - 12, 18)
        pygame.draw.rect(surface, (40, 60, 90), ws, border_radius=4)
        # wheels (decorative)
        wh = 14
        pygame.draw.rect(surface, (30, 30, 30),
                         (body.x - 4, body.y + 10, 6, wh), border_radius=2)
        pygame.draw.rect(surface, (30, 30, 30),
                         (body.right - 2, body.y + 10, 6, wh), border_radius=2)
        pygame.draw.rect(surface, (30, 30, 30),
                         (body.x - 4, body.bottom - 24, 6, wh), border_radius=2)
        pygame.draw.rect(surface, (30, 30, 30),
                         (body.right - 2, body.bottom - 24, 6, wh), border_radius=2)


# ---------------------------------------------------------------------------
# Generic scrolling object — base for traffic, obstacles, pickups, events
# ---------------------------------------------------------------------------
class WorldObject:
    """Anything on the road that scrolls with the world."""
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.alive = True
        # objects with a self_speed move downward in addition to world scroll
        # (e.g. traffic that's slower or faster than the player)
        self.self_speed = 0

    @property
    def rect(self):
        return pygame.Rect(int(self.x - self.w / 2),
                           int(self.y - self.h / 2),
                           self.w, self.h)

    def update(self, dt, world_speed):
        self.y += (world_speed + self.self_speed) * dt
        # despawn once off the bottom of the screen
        if self.y - self.h > 1000:
            self.alive = False

    def draw(self, surface):
        pass


class TrafficCar(WorldObject):
    """Enemy vehicle — collision ends the run."""
    def __init__(self, lane_index, color):
        x = LANE_CENTERS[lane_index]
        super().__init__(x, -80, 44, 70)
        self.color = color
        # traffic moves downward slower than world scroll, so it appears to
        # drift toward the player — a small randomization adds variety
        self.self_speed = random.uniform(-60, 40)

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect, border_radius=8)
        pygame.draw.rect(surface, (20, 20, 20), self.rect, 2, border_radius=8)
        ws = pygame.Rect(self.rect.x + 6, self.rect.y + 12,
                         self.rect.w - 12, 18)
        pygame.draw.rect(surface, (40, 60, 90), ws, border_radius=4)


class OilSpill(WorldObject):
    """Doesn't kill but reduces control briefly when touched."""
    def __init__(self, lane_index):
        super().__init__(LANE_CENTERS[lane_index], -60, 70, 50)

    def draw(self, surface):
        pygame.draw.ellipse(surface, (15, 15, 20), self.rect)
        # glossy highlight
        inner = self.rect.inflate(-20, -20)
        pygame.draw.ellipse(surface, (60, 60, 80), inner, 2)


class Pothole(WorldObject):
    """Crash hazard — same as traffic, ends the run on contact."""
    def __init__(self, lane_index):
        super().__init__(LANE_CENTERS[lane_index], -50, 50, 30)

    def draw(self, surface):
        pygame.draw.ellipse(surface, (40, 30, 25), self.rect)
        pygame.draw.ellipse(surface, (15, 10, 8),
                            self.rect.inflate(-12, -8))


class Barrier(WorldObject):
    """Static barrier blocking part of a lane."""
    def __init__(self, lane_index):
        super().__init__(LANE_CENTERS[lane_index], -60, 60, 24)

    def draw(self, surface):
        # red/white stripes
        r = self.rect
        pygame.draw.rect(surface, (220, 60, 60), r)
        stripe_w = 8
        for i in range(0, r.w, stripe_w * 2):
            pygame.draw.rect(surface, (240, 240, 240),
                             (r.x + i, r.y, stripe_w, r.h))
        pygame.draw.rect(surface, (20, 20, 20), r, 2)


class SpeedBump(WorldObject):
    """Slows the player briefly when crossed."""
    def __init__(self):
        # spans the whole road
        super().__init__((ROAD_LEFT + ROAD_RIGHT) / 2, -30, ROAD_WIDTH, 18)

    def draw(self, surface):
        r = self.rect
        pygame.draw.rect(surface, (180, 140, 30), r)
        for i in range(0, r.w, 30):
            pygame.draw.line(surface, (40, 30, 10),
                             (r.x + i, r.y), (r.x + i, r.bottom), 2)


class NitroStrip(WorldObject):
    """Crossing it grants a brief speed boost."""
    def __init__(self, lane_index):
        super().__init__(LANE_CENTERS[lane_index], -60, 50, 80)

    def draw(self, surface):
        r = self.rect
        pygame.draw.rect(surface, (40, 200, 255), r, border_radius=6)
        # arrow chevrons
        for i in range(3):
            yo = r.y + 10 + i * 22
            pygame.draw.polygon(surface, (255, 255, 255), [
                (r.centerx - 14, yo + 12),
                (r.centerx, yo),
                (r.centerx + 14, yo + 12),
                (r.centerx, yo + 6),
            ])


class Coin(WorldObject):
    def __init__(self, lane_index):
        super().__init__(LANE_CENTERS[lane_index], -40, 26, 26)

    def draw(self, surface):
        c = self.rect.center
        pygame.draw.circle(surface, (255, 210, 50), c, 13)
        pygame.draw.circle(surface, (200, 150, 20), c, 13, 2)
        pygame.draw.circle(surface, (255, 240, 150), c, 6)


class PowerUp(WorldObject):
    """One of: nitro, shield, repair. Vanishes after `lifetime` seconds."""
    LIFETIME = 8.0  # seconds before despawn if not collected

    def __init__(self, lane_index, kind):
        super().__init__(LANE_CENTERS[lane_index], -40, 32, 32)
        self.kind = kind
        self.age = 0.0

    def update(self, dt, world_speed):
        super().update(dt, world_speed)
        self.age += dt
        if self.age >= self.LIFETIME:
            self.alive = False

    def draw(self, surface):
        c = self.rect.center
        # blink in the last 1.5 s of life so the player notices it's about to vanish
        time_left = self.LIFETIME - self.age
        if time_left < 1.5 and (pygame.time.get_ticks() // 120) % 2 == 0:
            return

        if self.kind == "nitro":
            pygame.draw.circle(surface, (40, 200, 255), c, 16)
            pygame.draw.circle(surface, (10, 80, 120), c, 16, 2)
            label = "N"
            label_color = (10, 40, 60)
        elif self.kind == "shield":
            pygame.draw.circle(surface, (140, 200, 255), c, 16)
            pygame.draw.circle(surface, (40, 80, 160), c, 16, 2)
            label = "S"
            label_color = (10, 30, 80)
        else:  # repair
            pygame.draw.circle(surface, (90, 220, 110), c, 16)
            pygame.draw.circle(surface, (30, 110, 50), c, 16, 2)
            label = "+"
            label_color = (10, 50, 20)

        # cheap built-in font label so we don't need a font passed in
        font = pygame.font.SysFont("arial", 18, bold=True)
        surf = font.render(label, True, label_color)
        surface.blit(surf, surf.get_rect(center=c))


# ---------------------------------------------------------------------------
# Active power-up effect carried by the player
# ---------------------------------------------------------------------------
class ActiveEffect:
    """Holds the currently active power-up. Only one at a time per the spec."""
    def __init__(self, kind, duration=None):
        self.kind = kind          # 'nitro' | 'shield' | None
        self.duration = duration  # remaining seconds, or None for "until hit"

    def tick(self, dt):
        if self.duration is not None:
            self.duration -= dt
            if self.duration <= 0:
                return False      # expired
        return True


# ---------------------------------------------------------------------------
# The full game state
# ---------------------------------------------------------------------------
class Game:
    BASE_WORLD_SPEED = 280   # px/s the world scrolls down at start
    NITRO_BOOST = 1.7        # world-speed multiplier while nitro active
    NITRO_DURATION = 4.0     # seconds (within the 3–5 s spec)
    OIL_SLOW_DURATION = 1.0  # seconds that lateral control is reduced

    def __init__(self, screen_size, settings):
        self.w, self.h = screen_size
        self.settings = settings
        self.difficulty = DIFFICULTY[settings.get("difficulty", "normal")]

        self.player = Player(settings.get("car_color", "red"), self.h)

        # world / scroll state
        self.world_speed = self.BASE_WORLD_SPEED * self.difficulty["speed"]
        self.distance = 0.0      # px scrolled
        self.lane_stripe_offset = 0.0  # for animated dashed centerline

        # entity lists
        self.traffic = []
        self.obstacles = []     # potholes, barriers, oil, speed bumps, nitro strips
        self.coins = []
        self.powerups = []

        # spawn timers
        self.t_traffic = 0.0
        self.t_obstacle = 0.0
        self.t_coin = 0.0
        self.t_powerup = 0.0
        self.t_event = 0.0

        # scoring
        self.coins_collected = 0
        self.bonus = 0
        self.alive = True
        self.finished = False

        # active power-up
        self.effect = None             # ActiveEffect or None
        self.oil_slow_until = 0.0      # game-time stamp; <= 0 means no slow

        # game time elapsed (for difficulty scaling and timed effects)
        self.elapsed = 0.0

    # ------------------------------------------------------------------
    # spawn helpers
    # ------------------------------------------------------------------
    def _occupied_lanes_near(self, y_top=-150, y_bottom=200):
        """Return set of lanes that already have something near the spawn area
        OR near the player. Prevents spawning directly on top of the player
        and prevents two things stacking on the same row."""
        lanes = set()
        # don't spawn directly on player
        for i, cx in enumerate(LANE_CENTERS):
            if abs(cx - self.player.x) < LANE_WIDTH * 0.6 \
                    and self.player.y - 200 < self.player.y < self.player.y + 50:
                lanes.add(i)
        # don't stack with anything near top of screen
        for obj in self.traffic + self.obstacles + self.powerups + self.coins:
            if y_top < obj.y < y_bottom:
                # find which lane it's closest to
                best = min(range(LANES),
                           key=lambda k: abs(LANE_CENTERS[k] - obj.x))
                lanes.add(best)
        return lanes

    def _safe_player_lane(self):
        """Return the lane index closest to the player — never spawn here."""
        return min(range(LANES),
                   key=lambda k: abs(LANE_CENTERS[k] - self.player.x))

    def _free_lanes(self):
        occupied = self._occupied_lanes_near()
        occupied.add(self._safe_player_lane())   # spec: never on top of player
        return [i for i in range(LANES) if i not in occupied]

    def spawn_traffic(self):
        free = self._free_lanes()
        if not free:
            return
        lane = random.choice(free)
        color = random.choice([(180, 180, 200), (60, 60, 70),
                               (200, 100, 40), (40, 110, 60)])
        self.traffic.append(TrafficCar(lane, color))

    def spawn_obstacle(self):
        free = self._free_lanes()
        if not free:
            return
        lane = random.choice(free)
        kind = random.choices(
            ["pothole", "barrier", "oil"],
            weights=[3, 2, 3], k=1
        )[0]
        if kind == "pothole":
            self.obstacles.append(Pothole(lane))
        elif kind == "barrier":
            self.obstacles.append(Barrier(lane))
        else:
            self.obstacles.append(OilSpill(lane))

    def spawn_event(self):
        # full-width speed bump or single-lane nitro strip
        if random.random() < 0.5:
            self.obstacles.append(SpeedBump())
        else:
            free = self._free_lanes()
            if free:
                self.obstacles.append(NitroStrip(random.choice(free)))

    def spawn_coin(self):
        free = self._free_lanes()
        if not free:
            return
        self.coins.append(Coin(random.choice(free)))

    def spawn_powerup(self):
        free = self._free_lanes()
        if not free:
            return
        kind = random.choice(["nitro", "shield", "repair"])
        self.powerups.append(PowerUp(random.choice(free), kind))

    # ------------------------------------------------------------------
    # main update
    # ------------------------------------------------------------------
    def update(self, keys, dt):
        if not self.alive or self.finished:
            return
        self.elapsed += dt

        # difficulty ramps with elapsed time — capped so it stays playable
        scaling = self.difficulty["scaling"]
        ramp = min(1.0 + self.elapsed * 0.015 * scaling, 2.2)
        cur_world_speed = self.BASE_WORLD_SPEED * self.difficulty["speed"] * ramp

        # nitro multiplies world speed
        if self.effect and self.effect.kind == "nitro":
            cur_world_speed *= self.NITRO_BOOST

        # oil reduces lateral control briefly
        slow_factor = 0.45 if self.elapsed < self.oil_slow_until else 1.0

        # tick the player input
        self.player.update(keys, dt, slow_factor=slow_factor)

        # tick the active effect
        if self.effect and self.effect.duration is not None:
            if not self.effect.tick(dt):
                self.effect = None

        # scroll
        self.distance += cur_world_speed * dt
        self.lane_stripe_offset = (self.lane_stripe_offset
                                   + cur_world_speed * dt) % 40

        # ----- spawn timers (intervals shrink as difficulty rises) -----
        spawn_mul = self.difficulty["spawn"] * ramp

        self.t_traffic += dt
        if self.t_traffic >= max(0.55, 1.6 / spawn_mul):
            self.t_traffic = 0
            self.spawn_traffic()

        self.t_obstacle += dt
        if self.t_obstacle >= max(0.9, 2.4 / spawn_mul):
            self.t_obstacle = 0
            self.spawn_obstacle()

        self.t_coin += dt
        if self.t_coin >= 1.1:
            self.t_coin = 0
            if random.random() < 0.7:
                self.spawn_coin()

        self.t_powerup += dt
        if self.t_powerup >= 7.0:
            self.t_powerup = 0
            if random.random() < 0.6:
                self.spawn_powerup()

        self.t_event += dt
        if self.t_event >= 9.0:
            self.t_event = 0
            self.spawn_event()

        # ----- update entities -----
        for group in (self.traffic, self.obstacles, self.coins, self.powerups):
            for o in group:
                o.update(dt, cur_world_speed)
            group[:] = [o for o in group if o.alive]

        # ----- collisions -----
        self._handle_collisions()

        # ----- finish line -----
        if self.distance >= FINISH_DISTANCE:
            self.finished = True

    def _handle_collisions(self):
        prect = self.player.rect

        # coins
        for c in self.coins:
            if c.rect.colliderect(prect):
                c.alive = False
                self.coins_collected += 1
                self.bonus += 5

        # power-ups (only one active — picking up a new one replaces the old)
        for p in self.powerups:
            if p.rect.colliderect(prect):
                p.alive = False
                self._activate_powerup(p.kind)

        # obstacles — handle each kind specifically
        for o in self.obstacles:
            if not o.rect.colliderect(prect):
                continue
            if isinstance(o, OilSpill):
                # not lethal — just lose lateral control for a moment
                self.oil_slow_until = self.elapsed + self.OIL_SLOW_DURATION
                o.alive = False
            elif isinstance(o, SpeedBump):
                # brief slowdown via the same oil mechanic; doesn't kill
                self.oil_slow_until = self.elapsed + 0.4
                o.alive = False
            elif isinstance(o, NitroStrip):
                self._activate_powerup("nitro")  # gives a free boost
                o.alive = False
            elif isinstance(o, (Pothole, Barrier)):
                if not self._absorb_hit():
                    self.alive = False
                o.alive = False

        # traffic — lethal unless shield/repair absorbs
        for t in self.traffic:
            if t.rect.colliderect(prect):
                if not self._absorb_hit():
                    self.alive = False
                t.alive = False

    def _absorb_hit(self):
        """Return True if a power-up absorbed the crash, False otherwise."""
        if self.effect and self.effect.kind == "shield":
            self.effect = None
            return True
        return False

    def _activate_powerup(self, kind):
        """Apply a power-up. Per spec, only one can be active at a time, so
        a new pickup replaces any current effect. Repair is instant."""
        if kind == "repair":
            # if there is currently a shield/nitro it's left alone — repair
            # doesn't *replace* an active effect, it just clears one obstacle.
            # But there's no "damage" state to clear here, so treat it as a
            # bonus + a free shield charge if nothing is active.
            self.bonus += 25
            if self.effect is None:
                self.effect = ActiveEffect("shield", duration=None)
            return

        if kind == "nitro":
            self.effect = ActiveEffect("nitro", duration=self.NITRO_DURATION)
            self.bonus += 10
        elif kind == "shield":
            self.effect = ActiveEffect("shield", duration=None)
            self.bonus += 10

    # ------------------------------------------------------------------
    # scoring
    # ------------------------------------------------------------------
    @property
    def score(self):
        return int(self.distance * 0.1) + self.coins_collected * 10 + self.bonus

    @property
    def remaining_distance(self):
        return max(0, FINISH_DISTANCE - int(self.distance))

    # ------------------------------------------------------------------
    # render
    # ------------------------------------------------------------------
    def draw(self, surface):
        # grass shoulders
        surface.fill((40, 90, 50))
        # road
        pygame.draw.rect(surface, (50, 50, 56),
                         (ROAD_LEFT, 0, ROAD_WIDTH, self.h))
        # road edges
        pygame.draw.rect(surface, (240, 240, 240),
                         (ROAD_LEFT - 4, 0, 4, self.h))
        pygame.draw.rect(surface, (240, 240, 240),
                         (ROAD_RIGHT, 0, 4, self.h))

        # animated lane separators (skip outermost edges)
        for lane in range(1, LANES):
            x = ROAD_LEFT + lane * LANE_WIDTH
            y = -40 + self.lane_stripe_offset
            while y < self.h:
                pygame.draw.rect(surface, (220, 220, 220),
                                 (x - 2, int(y), 4, 20))
                y += 40

        # entities — draw obstacles before traffic so cars sit on top
        for o in self.obstacles:
            o.draw(surface)
        for c in self.coins:
            c.draw(surface)
        for p in self.powerups:
            p.draw(surface)
        for t in self.traffic:
            t.draw(surface)

        # shield aura
        if self.effect and self.effect.kind == "shield":
            cx, cy = self.player.rect.center
            radius = 45 + int(3 * math.sin(pygame.time.get_ticks() / 120))
            pygame.draw.circle(surface, (140, 200, 255),
                               (cx, cy), radius, 3)

        self.player.draw(surface)