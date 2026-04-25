"""
Platforms and decorations
"""
import pygame
import math
from core.config import *

class Platform:
    """Platform tile"""
    
    def __init__(self, x, y, width=TILE_SIZE, height=TILE_SIZE):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
    
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def draw(self, screen, camera_x):
        x = self.x - camera_x
        
        # Dark platform body
        pygame.draw.rect(screen, PLATFORM_DARK, (x, self.y, self.width, self.height))
        
        # Grass on top
        grass_height = 8
        pygame.draw.rect(screen, GRASS_GREEN, (x, self.y, self.width, grass_height))
        
        # Grass texture
        for i in range(0, int(self.width), 6):
            grass_y = self.y + grass_height - (i % 3)
            pygame.draw.line(screen, (60, 140, 100), (x + i, self.y), (x + i, grass_y), 2)
        
        # Platform texture (stones)
        for i in range(0, int(self.width), 16):
            for j in range(grass_height, int(self.height), 16):
                stone_rect = (x + i + 2, self.y + j + 2, 12, 12)
                pygame.draw.rect(screen, PLATFORM_LIGHT, stone_rect)
                pygame.draw.rect(screen, (70, 75, 90), stone_rect, 1)

class Tree:
    """Decorative tree"""
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.animation = 0
    
    def update(self, dt):
        self.animation += dt
    
    def draw(self, screen, camera_x):
        x = self.x - camera_x
        
        # Trunk
        trunk_width = 12
        trunk_height = 40
        pygame.draw.rect(screen, TREE_TRUNK, (x - trunk_width//2, self.y - trunk_height, trunk_width, trunk_height))
        
        # Leaves (3 circles with animation)
        sway = int(3 * math.sin(self.animation * 2))
        
        # Bottom layer
        pygame.draw.circle(screen, (80, 160, 110), (x + sway, self.y - trunk_height - 10), 20)
        pygame.draw.circle(screen, TREE_LEAVES, (x + sway, self.y - trunk_height - 10), 18)
        
        # Middle
        pygame.draw.circle(screen, (70, 150, 100), (x - 10 + sway, self.y - trunk_height - 20), 18)
        pygame.draw.circle(screen, TREE_LEAVES, (x - 10 + sway, self.y - trunk_height - 20), 16)
        
        # Top
        pygame.draw.circle(screen, (60, 140, 90), (x + 10 + sway, self.y - trunk_height - 25), 16)
        pygame.draw.circle(screen, TREE_LEAVES, (x + 10 + sway, self.y - trunk_height - 25), 14)

class Cloud:
    """Floating cloud decoration"""
    
    def __init__(self, x, y, size=1.0):
        self.x = x
        self.y = y
        self.size = size
        self.speed = 10 * size
    
    def update(self, dt):
        self.x += self.speed * dt
        # Wrap around
        if self.x > 3000:
            self.x = -100
    
    def draw(self, screen, camera_x):
        x = self.x - camera_x * 0.5  # Parallax effect
        
        # Cloud made of circles
        base_size = int(20 * self.size)
        pygame.draw.circle(screen, CLOUD_WHITE, (int(x), int(self.y)), base_size)
        pygame.draw.circle(screen, CLOUD_WHITE, (int(x - 15 * self.size), int(self.y + 5)), int(base_size * 0.8))
        pygame.draw.circle(screen, CLOUD_WHITE, (int(x + 15 * self.size), int(self.y + 5)), int(base_size * 0.8))
        pygame.draw.circle(screen, CLOUD_WHITE, (int(x), int(self.y + 10)), int(base_size * 0.9))

class Gem:
    """Collectible gem"""
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.collected = False
        self.animation = 0
        self.bob_offset = 0
    
    def update(self, dt):
        self.animation += dt * 5
        self.bob_offset = math.sin(self.animation) * 5
    
    def draw(self, screen, camera_x):
        if self.collected:
            return
        
        x = self.x - camera_x
        y = self.y + self.bob_offset
        
        # Diamond shape
        points = [
            (x, y - 10),
            (x + 8, y),
            (x, y + 10),
            (x - 8, y)
        ]
        pygame.draw.polygon(screen, GEM_COLOR, points)
        pygame.draw.polygon(screen, (255, 150, 200), points, 2)
        
        # Sparkle
        if int(self.animation * 2) % 2 == 0:
            pygame.draw.line(screen, (255, 255, 255), (x - 12, y), (x + 12, y), 2)
            pygame.draw.line(screen, (255, 255, 255), (x, y - 12), (x, y + 12), 2)
    
    def get_rect(self):
        return pygame.Rect(self.x - 8, self.y - 10, 16, 20)
