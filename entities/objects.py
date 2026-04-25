"""
Platforms, Trees, Clouds, Gems
"""
import pygame
import math
from core.config import *


class Platform:
    def __init__(self, x, y, width=TILE_SIZE, height=TILE_SIZE):
        self.x = x
        self.y = y
        self.width  = width
        self.height = height

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, screen, camera_x):
        x = int(self.x - camera_x)
        y = int(self.y)
        w = int(self.width)
        h = int(self.height)

        # Stone body
        pygame.draw.rect(screen, PLATFORM_STONE, (x, y, w, h))

        # Stone tile texture
        for tx in range(0, w, 16):
            for ty in range(9, h, 8):
                sw = min(14, w - tx - 2)
                sh = min(6,  h - ty - 2)
                if sw > 1 and sh > 1:
                    pygame.draw.rect(screen, PLATFORM_LIGHT, (x + tx + 1, y + ty + 1, sw, sh))
                    pygame.draw.rect(screen, (130, 125, 145), (x + tx + 1, y + ty + 1, sw // 2, 1))

        # Grass top
        pygame.draw.rect(screen, GRASS_GREEN,  (x, y, w, 9))
        pygame.draw.rect(screen, GRASS_LIGHT,  (x, y, w, 3))

        # Grass blades
        for gx in range(2, w - 2, 5):
            bh = 3 + (gx % 3)
            pygame.draw.line(screen, (100, 220, 100), (x + gx, y), (x + gx - 1, y - bh), 1)

        # 3D bevel edges
        pygame.draw.line(screen, GRASS_LIGHT,   (x,     y),     (x + w, y),     1)
        pygame.draw.line(screen, PLATFORM_LIGHT, (x,     y + 9), (x,     y + h), 1)
        pygame.draw.line(screen, PLATFORM_DARK,  (x + w - 1, y), (x + w - 1, y + h), 1)


class Tree:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.animation = 0.0

    def update(self, dt):
        self.animation += dt

    def draw(self, screen, camera_x):
        x = int(self.x - camera_x)
        y = int(self.y)

        sway    = int(2 * math.sin(self.animation * 1.5))
        trunk_w = 10
        trunk_h = 38

        # Trunk with gradient
        for i in range(trunk_w):
            t = abs(i - trunk_w / 2) / (trunk_w / 2)
            r = int(100 - 30 * t)
            g = int(65  - 20 * t)
            b = int(35  - 10 * t)
            pygame.draw.line(screen, (r, g, b),
                             (x - trunk_w // 2 + i, y - trunk_h),
                             (x - trunk_w // 2 + i, y))

        # Bark marks
        for bh in range(8, trunk_h, 10):
            pygame.draw.line(screen, (75, 48, 22),
                             (x - 3, y - bh), (x + 1, y - bh - 3), 1)

        # Leaf layers (bottom → top so top overlaps)
        layers = [
            (0,  -trunk_h - 4,  22, TREE_DARK),
            (-11, -trunk_h - 14, 18, TREE_LEAVES),
            (11,  -trunk_h - 17, 17, TREE_LEAVES),
            (0,  -trunk_h - 27, 20, (60, 180, 80)),
            (0,  -trunk_h - 39, 16, TREE_BRIGHT),
        ]
        for lx, ly, lr, lc in layers:
            px = x + lx + sway
            py = y + ly
            pygame.draw.circle(screen, TREE_DARK,  (px + 2, py + 2), lr)
            pygame.draw.circle(screen, lc,          (px, py), lr)
            light = (min(255, lc[0] + 40), min(255, lc[1] + 40), min(255, lc[2] + 20))
            pygame.draw.circle(screen, light, (px - lr // 4, py - lr // 4), lr // 3)


class Cloud:
    def __init__(self, x, y, size=1.0):
        self.x     = x
        self.y     = y
        self.size  = size
        self.speed = 8 * size

    def update(self, dt):
        self.x += self.speed * dt
        if self.x > 3500:
            self.x = -200

    def draw(self, screen, camera_x):
        x = int(self.x - camera_x * 0.4)
        y = int(self.y)
        s = self.size

        # Shadow layer
        for ox, oy, r in [
            (2,  4, 18), (-int(14*s)+2, int(6*s)+4, 14),
            (int(14*s)+2, int(6*s)+4, 14), (-int(7*s)+2, int(3*s)+4, 16),
            (int(7*s)+2, int(3*s)+4, 16),
        ]:
            pygame.draw.circle(screen, CLOUD_SHADOW, (x + ox, y + oy), int(r * s))

        # White layer
        for ox, oy, r in [
            (0, 0, 20), (-int(15*s), int(6*s), 15),
            (int(15*s), int(6*s), 15), (-int(7*s), int(3*s), 16),
            (int(7*s), int(3*s), 16),
        ]:
            pygame.draw.circle(screen, CLOUD_WHITE, (x + ox, y + oy), int(r * s))

        # Highlight
        pygame.draw.circle(screen, (255, 255, 255), (x - int(5*s), y - int(5*s)), int(8*s))


class Gem:
    def __init__(self, x, y):
        self.x         = x
        self.y         = y
        self.collected = False
        self.animation = 0.0
        self.bob_offset = 0.0
        self.rotation   = 0.0

    def update(self, dt):
        self.animation  += dt * 3
        self.bob_offset  = math.sin(self.animation) * 4
        self.rotation   += dt * 120   # degrees / second

    def draw(self, screen, camera_x):
        if self.collected:
            return

        cx = int(self.x - camera_x)
        cy = int(self.y + self.bob_offset)
        r  = math.radians(self.rotation)

        def diamond(cx, cy, size):
            pts = []
            for i, angle in enumerate([r, r + math.pi/2, r + math.pi, r + 3*math.pi/2]):
                d = size * 1.4 if i % 2 == 0 else size * 0.7
                pts.append((cx + int(math.cos(angle) * d),
                             cy + int(math.sin(angle) * d)))
            return pts

        # Outer glow (simple larger version, dimmer)
        glow_pts = diamond(cx, cy, 13)
        pygame.draw.polygon(screen, (180, 30, 130), glow_pts)

        # Main gem
        outer_pts = diamond(cx, cy, 10)
        pygame.draw.polygon(screen, GEM_COLOR, outer_pts)

        # Inner highlight
        inner_pts = diamond(cx, cy, 5)
        pygame.draw.polygon(screen, GEM_INNER, inner_pts)

        # Rotating sparkle arms
        spark_r = r + self.animation * 0.4
        for angle in (spark_r, spark_r + math.pi):
            sx1 = cx + int(math.cos(angle) * 2)
            sy1 = cy + int(math.sin(angle) * 2)
            sx2 = cx + int(math.cos(angle) * 16)
            sy2 = cy + int(math.sin(angle) * 16)
            pygame.draw.line(screen, WHITE, (sx1, sy1), (sx2, sy2), 1)

    def get_rect(self):
        return pygame.Rect(self.x - 8, self.y - 10, 16, 20)
