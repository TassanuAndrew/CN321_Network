"""
Player with smooth animations
"""
import pygame
import math
from core.config import *

class Player:
    """Player character"""
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = PLAYER_SIZE
        self.height = PLAYER_SIZE
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.facing_right = True
        self.animation_timer = 0
    
    def move_left(self):
        self.vel_x = -MOVE_SPEED
        self.facing_right = False
    
    def move_right(self):
        self.vel_x = MOVE_SPEED
        self.facing_right = True
    
    def stop(self):
        self.vel_x = 0
    
    def jump(self):
        # Single jump only - must be on ground
        if self.on_ground:
            self.vel_y = JUMP_SPEED
            self.on_ground = False
    
    def update(self, dt, platforms):
        # Animation
        if abs(self.vel_x) > 0:
            self.animation_timer += dt * 10
        else:
            self.animation_timer = 0
        
        # Gravity
        self.vel_y += GRAVITY
        if self.vel_y > MAX_FALL_SPEED:
            self.vel_y = MAX_FALL_SPEED
        
        # Move
        self.x += self.vel_x
        self.check_collision_x(platforms)
        
        self.y += self.vel_y
        self.check_collision_y(platforms)
    
    def check_collision_x(self, platforms):
        rect = pygame.Rect(self.x, self.y, self.width, self.height)
        for platform in platforms:
            if rect.colliderect(platform.get_rect()):
                if self.vel_x > 0:
                    self.x = platform.x - self.width
                elif self.vel_x < 0:
                    self.x = platform.x + platform.width
    
    def check_collision_y(self, platforms):
        rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.on_ground = False
        
        for platform in platforms:
            if rect.colliderect(platform.get_rect()):
                if self.vel_y > 0:
                    self.y = platform.y - self.height
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:
                    self.y = platform.y + platform.height
                    self.vel_y = 0
    
    def draw(self, screen, camera_x):
        x = self.x - camera_x
        
        # Body
        pygame.draw.rect(screen, PLAYER_COLOR, (x, self.y, self.width, self.height), border_radius=5)
        
        # Face
        face_offset = int(2 * math.sin(self.animation_timer))
        if self.facing_right:
            # Eyes
            pygame.draw.circle(screen, (255, 255, 255), (int(x + 20), int(self.y + 12 + face_offset)), 4)
            pygame.draw.circle(screen, (255, 255, 255), (int(x + 26), int(self.y + 12 + face_offset)), 4)
            pygame.draw.circle(screen, (0, 0, 0), (int(x + 21), int(self.y + 12 + face_offset)), 2)
            pygame.draw.circle(screen, (0, 0, 0), (int(x + 27), int(self.y + 12 + face_offset)), 2)
        else:
            pygame.draw.circle(screen, (255, 255, 255), (int(x + 6), int(self.y + 12 + face_offset)), 4)
            pygame.draw.circle(screen, (255, 255, 255), (int(x + 12), int(self.y + 12 + face_offset)), 4)
            pygame.draw.circle(screen, (0, 0, 0), (int(x + 7), int(self.y + 12 + face_offset)), 2)
            pygame.draw.circle(screen, (0, 0, 0), (int(x + 13), int(self.y + 12 + face_offset)), 2)
        
        # Feet (animated when moving)
        if abs(self.vel_x) > 0:
            foot_bounce = abs(int(3 * math.sin(self.animation_timer * 2)))
            pygame.draw.rect(screen, (80, 100, 180), (x + 6, self.y + self.height - 4 + foot_bounce, 8, 4))
            pygame.draw.rect(screen, (80, 100, 180), (x + 18, self.y + self.height - 4 - foot_bounce, 8, 4))
        else:
            pygame.draw.rect(screen, (80, 100, 180), (x + 6, self.y + self.height - 4, 8, 4))
            pygame.draw.rect(screen, (80, 100, 180), (x + 18, self.y + self.height - 4, 8, 4))
    
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
