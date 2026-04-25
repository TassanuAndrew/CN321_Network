"""
Enemies
"""
import pygame
import math
from core.config import *

class Enemy:
    """Walking enemy"""
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 28
        self.height = 28
        self.vel_x = -ENEMY_SPEED
        self.vel_y = 0
        self.alive = True
        self.animation = 0
    
    def update(self, dt, platforms):
        if not self.alive:
            return
        
        self.animation += dt * 5
        
        # Gravity
        self.vel_y += GRAVITY
        if self.vel_y > MAX_FALL_SPEED:
            self.vel_y = MAX_FALL_SPEED
        
        # Move
        self.x += self.vel_x
        self.y += self.vel_y
        
        # Platform collision
        rect = pygame.Rect(self.x, self.y, self.width, self.height)
        for platform in platforms:
            if rect.colliderect(platform.get_rect()):
                if self.vel_y > 0:
                    self.y = platform.y - self.height
                    self.vel_y = 0
                elif self.vel_x > 0:
                    self.x = platform.x - self.width
                    self.vel_x = -ENEMY_SPEED
                elif self.vel_x < 0:
                    self.x = platform.x + platform.width
                    self.vel_x = ENEMY_SPEED
        
        # Fall off world
        if self.y > WINDOW_HEIGHT:
            self.alive = False
    
    def stomp(self):
        self.alive = False
    
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def draw(self, screen, camera_x):
        if not self.alive:
            return
        
        x = self.x - camera_x
        
        # Body (rounded)
        pygame.draw.ellipse(screen, ENEMY_COLOR, (x, self.y, self.width, self.height))
        
        # Eyes (animated)
        blink = int(self.animation) % 10 == 0
        if not blink:
            eye_size = 5
            eye1_x = x + 8
            eye2_x = x + 20
            eye_y = self.y + 12
            
            pygame.draw.circle(screen, (255, 255, 255), (eye1_x, eye_y), eye_size)
            pygame.draw.circle(screen, (255, 255, 255), (eye2_x, eye_y), eye_size)
            pygame.draw.circle(screen, (0, 0, 0), (eye1_x, eye_y), 3)
            pygame.draw.circle(screen, (0, 0, 0), (eye2_x, eye_y), 3)
        else:
            # Blink
            pygame.draw.line(screen, (0, 0, 0), (x + 8, self.y + 12), (x + 14, self.y + 12), 2)
            pygame.draw.line(screen, (0, 0, 0), (x + 20, self.y + 12), (x + 26, self.y + 12), 2)
        
        # Feet (bounce animation)
        foot_bounce = abs(int(2 * math.sin(self.animation * 2)))
        pygame.draw.ellipse(screen, (180, 80, 130), (x + 3, self.y + self.height - 8 + foot_bounce, 8, 8))
        pygame.draw.ellipse(screen, (180, 80, 130), (x + 17, self.y + self.height - 8 - foot_bounce, 8, 8))
