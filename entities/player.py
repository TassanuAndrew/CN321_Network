"""
Player - detailed character with animations
"""
import pygame
import math
from core.config import *


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width  = PLAYER_SIZE
        self.height = PLAYER_SIZE
        self.vel_x  = 0
        self.vel_y  = 0
        self.on_ground    = False
        self.facing_right = True
        self.animation_timer = 0
        self.jump_squish     = 0.0

    def move_left(self):
        self.vel_x = -MOVE_SPEED
        self.facing_right = False

    def move_right(self):
        self.vel_x = MOVE_SPEED
        self.facing_right = True

    def stop(self):
        self.vel_x = 0

    def jump(self):
        if self.on_ground:
            self.vel_y = JUMP_SPEED
            self.on_ground   = False
            self.jump_squish = 1.0

    def update(self, dt, platforms):
        if abs(self.vel_x) > 0:
            self.animation_timer += dt * 8
        else:
            self.animation_timer = 0

        if self.jump_squish > 0:
            self.jump_squish = max(0.0, self.jump_squish - dt * 5)

        self.vel_y += GRAVITY
        if self.vel_y > MAX_FALL_SPEED:
            self.vel_y = MAX_FALL_SPEED

        self.x += self.vel_x
        self._collide_x(platforms)
        self.y += self.vel_y
        self._collide_y(platforms)

    def _collide_x(self, platforms):
        rect = pygame.Rect(self.x, self.y, self.width, self.height)
        for p in platforms:
            if rect.colliderect(p.get_rect()):
                if self.vel_x > 0:
                    self.x = p.x - self.width
                elif self.vel_x < 0:
                    self.x = p.x + p.width

    def _collide_y(self, platforms):
        rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.on_ground = False
        for p in platforms:
            if rect.colliderect(p.get_rect()):
                if self.vel_y > 0:
                    self.y = p.y - self.height
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:
                    self.y = p.y + p.height
                    self.vel_y = 0

    def draw(self, screen, camera_x):
        x = int(self.x - camera_x)
        y = int(self.y)

        # Squish on jump
        squish = math.sin(self.jump_squish * math.pi) * 0.25

        # Shadow
        sw = int((self.width - 6) * (1 + squish * 0.5))
        pygame.draw.ellipse(screen, (0, 0, 0),
                            (x + self.width // 2 - sw // 2, y + self.height - 2, sw, 5))

        # --- Legs ---
        leg_swing = int(5 * math.sin(self.animation_timer)) if abs(self.vel_x) > 0 else 0
        leg_w, leg_h = 9, 11

        # Left leg
        ll_y = y + self.height - leg_h + leg_swing
        pygame.draw.rect(screen, PLAYER_LEG, (x + 4, ll_y, leg_w, leg_h), border_radius=3)
        pygame.draw.ellipse(screen, (25, 25, 45), (x + 2, ll_y + leg_h - 4, 13, 6))

        # Right leg
        rl_y = y + self.height - leg_h - leg_swing
        pygame.draw.rect(screen, PLAYER_LEG, (x + 19, rl_y, leg_w, leg_h), border_radius=3)
        pygame.draw.ellipse(screen, (25, 25, 45), (x + 17, rl_y + leg_h - 4, 13, 6))

        # --- Body ---
        body_y = y + 12
        body_h = 13
        pygame.draw.rect(screen, PLAYER_COLOR, (x + 3, body_y, self.width - 6, body_h), border_radius=5)
        # Shine
        pygame.draw.rect(screen, (130, 170, 255), (x + 5, body_y + 2, 9, 4), border_radius=2)

        # --- Arms ---
        arm_swing = int(5 * math.sin(self.animation_timer)) if abs(self.vel_x) > 0 else 0
        pygame.draw.rect(screen, PLAYER_COLOR, (x - 2, body_y + arm_swing,  6, 10), border_radius=3)
        pygame.draw.rect(screen, PLAYER_COLOR, (x + 28, body_y - arm_swing, 6, 10), border_radius=3)

        # --- Head ---
        hcx = x + self.width // 2
        hcy = y + 9
        pygame.draw.circle(screen, PLAYER_HEAD, (hcx, hcy), 10)
        pygame.draw.circle(screen, (255, 230, 200), (hcx - 3, hcy - 3), 4)  # highlight

        # --- Eyes ---
        if self.facing_right:
            ex1, ex2 = hcx + 2, hcx + 7
        else:
            ex1, ex2 = hcx - 7, hcx - 2
        ey = hcy
        po = 1 if self.facing_right else -1

        pygame.draw.circle(screen, WHITE, (ex1, ey), 3)
        pygame.draw.circle(screen, WHITE, (ex2, ey), 3)
        pygame.draw.circle(screen, (30, 30, 80), (ex1 + po, ey), 2)
        pygame.draw.circle(screen, (30, 30, 80), (ex2 + po, ey), 2)
        pygame.draw.circle(screen, WHITE, (ex1 + po, ey - 1), 1)
        pygame.draw.circle(screen, WHITE, (ex2 + po, ey - 1), 1)

        # --- Hat ---
        pygame.draw.rect(screen, PLAYER_HAT, (hcx - 12, hcy - 10, 24, 4), border_radius=2)   # brim
        pygame.draw.rect(screen, PLAYER_HAT, (hcx - 8,  hcy - 20, 16, 12), border_radius=3)  # top
        pygame.draw.rect(screen, PLAYER_BAND, (hcx - 8,  hcy - 12, 16, 3))                   # band

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
