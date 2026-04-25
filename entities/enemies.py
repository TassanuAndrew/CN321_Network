"""
Enemies - angry character with horns
"""
import pygame
import math
from core.config import *


class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width  = 30
        self.height = 28
        self.vel_x  = -ENEMY_SPEED
        self.vel_y  = 0
        self.alive  = True
        self.animation = 0.0

    def update(self, dt, platforms):
        if not self.alive:
            return

        self.animation += dt * 5

        self.vel_y += GRAVITY
        if self.vel_y > MAX_FALL_SPEED:
            self.vel_y = MAX_FALL_SPEED

        self.x += self.vel_x
        self.y += self.vel_y

        rect = pygame.Rect(self.x, self.y, self.width, self.height)
        for p in platforms:
            if rect.colliderect(p.get_rect()):
                if self.vel_y > 0:
                    self.y = p.y - self.height
                    self.vel_y = 0
                elif self.vel_x > 0:
                    self.x = p.x - self.width
                    self.vel_x = -ENEMY_SPEED
                elif self.vel_x < 0:
                    self.x = p.x + p.width
                    self.vel_x = ENEMY_SPEED

        if self.y > WINDOW_HEIGHT:
            self.alive = False

    def stomp(self):
        self.alive = False

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, screen, camera_x):
        if not self.alive:
            return

        x  = int(self.x - camera_x)
        y  = int(self.y)
        cx = x + self.width // 2

        # Shadow
        pygame.draw.ellipse(screen, (0, 0, 0),
                            (cx - 12, y + self.height - 3, 24, 5))

        # Feet
        bounce = abs(int(3 * math.sin(self.animation * 2)))
        pygame.draw.ellipse(screen, ENEMY_DARK, (x + 2,  y + self.height - 8 + bounce, 10, 8))
        pygame.draw.ellipse(screen, ENEMY_DARK, (x + 18, y + self.height - 8 - bounce, 10, 8))

        # Body
        pygame.draw.ellipse(screen, ENEMY_COLOR, (x + 2, y + 6, self.width - 4, self.height - 6))
        # Shine
        pygame.draw.ellipse(screen, (240, 110, 130), (x + 7, y + 9, 9, 5))

        # Horns
        pygame.draw.polygon(screen, ENEMY_HORN, [(x + 7,  y + 7), (x + 3,  y - 5), (x + 11, y + 3)])
        pygame.draw.polygon(screen, ENEMY_HORN, [(x + 23, y + 7), (x + 27, y - 5), (x + 19, y + 3)])

        # Eyes
        ey = y + 12
        blink = int(self.animation) % 12 == 0

        if not blink:
            for ex in (x + 10, x + 20):
                pygame.draw.circle(screen, WHITE, (ex, ey), 5)
                pygame.draw.circle(screen, (30, 30, 80), (ex, ey), 3)
                pygame.draw.circle(screen, WHITE, (ex, ey - 1), 1)
            # Angry brows
            pygame.draw.line(screen, (100, 20, 30), (x + 6,  ey - 6), (x + 14, ey - 4), 2)
            pygame.draw.line(screen, (100, 20, 30), (x + 24, ey - 6), (x + 16, ey - 4), 2)
        else:
            pygame.draw.line(screen, (30, 30, 80), (x + 6,  ey), (x + 14, ey), 2)
            pygame.draw.line(screen, (30, 30, 80), (x + 16, ey), (x + 24, ey), 2)

        # Frown
        pygame.draw.lines(screen, (100, 20, 30), False,
                          [(x + 10, y + 20), (x + 15, y + 22), (x + 20, y + 20)], 2)
