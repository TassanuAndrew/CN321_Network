"""
Level builder - creates beautiful levels like the image
"""
from entities.objects import Platform, Tree, Cloud, Gem
from entities.enemies import Enemy
from core.config import *
import random

def build_level():
    """Build a beautiful level matching the reference image"""
    
    platforms = []
    trees = []
    clouds = []
    gems = []
    enemies = []
    
    # Ground level (like in image - at bottom)
    ground_y = 650
    for i in range(100):
        platforms.append(Platform(i * TILE_SIZE, ground_y, TILE_SIZE, 50))
    
    # Floating islands (multiple heights like in image)
    
    # Island 1 - Left side, high up
    for i in range(4):
        platforms.append(Platform(150 + i * TILE_SIZE, 250, TILE_SIZE, 150))
    trees.append(Tree(190, 250))
    trees.append(Tree(260, 250))
    gems.append(Gem(210, 200))
    
    # Island 2 - Center, medium height
    for i in range(5):
        platforms.append(Platform(450 + i * TILE_SIZE, 350, TILE_SIZE, 200))
    trees.append(Tree(500, 350))
    trees.append(Tree(600, 350))
    enemies.append(Enemy(520, 300))
    gems.append(Gem(550, 300))
    
    # Island 3 - Right side, high
    for i in range(4):
        platforms.append(Platform(850 + i * TILE_SIZE, 200, TILE_SIZE, 180))
    trees.append(Tree(900, 200))
    gems.append(Gem(950, 150))
    enemies.append(Enemy(920, 150))
    
    # Island 4 - Middle bottom
    for i in range(6):
        platforms.append(Platform(350 + i * TILE_SIZE, 500, TILE_SIZE, 150))
    trees.append(Tree(400, 500))
    trees.append(Tree(480, 500))
    trees.append(Tree(520, 500))
    trees.append(Tree(580, 500))
    
    # Island 5 - Far right, low
    for i in range(7):
        platforms.append(Platform(1100 + i * TILE_SIZE, 550, TILE_SIZE, 100))
    trees.append(Tree(1150, 550))
    trees.append(Tree(1250, 550))
    trees.append(Tree(1350, 550))
    gems.append(Gem(1200, 500))
    gems.append(Gem(1300, 500))
    
    # Small platforms for jumping (like in image)
    platforms.append(Platform(320, 400, TILE_SIZE, TILE_SIZE))
    platforms.append(Platform(700, 300, TILE_SIZE, TILE_SIZE))
    platforms.append(Platform(800, 250, TILE_SIZE, TILE_SIZE))
    platforms.append(Platform(1000, 450, TILE_SIZE, TILE_SIZE))
    
    # More enemies
    enemies.append(Enemy(380, 450))
    enemies.append(Enemy(650, 300))
    enemies.append(Enemy(1150, 500))
    enemies.append(Enemy(1300, 500))
    
    # More gems (แก้แล้ว: 3 ตัวที่ y=480 ไม่ทับแพลตฟอร์ม)
    for i in range(3):
        gems.append(Gem(200 + i * 100, 480))
    
    gems.append(Gem(750, 250))
    gems.append(Gem(850, 400))
    
    # Clouds (parallax background)
    for i in range(15):
        x = random.randint(0, 2000)
        y = random.randint(50, 250)
        size = random.uniform(0.8, 1.5)
        clouds.append(Cloud(x, y, size))
    
    return platforms, trees, clouds, gems, enemies, 1800  # Level width

def build_level_2():
    """Level 2 - Forest Islands"""
    
    platforms = []
    trees = []
    clouds = []
    gems = []
    enemies = []
    
    ground_y = 650
    for i in range(100):
        platforms.append(Platform(i * TILE_SIZE, ground_y, TILE_SIZE, 50))
    
    # Multiple small islands
    island_positions = [
        (200, 500, 3), (400, 350, 4), (650, 450, 3),
        (850, 300, 5), (1100, 400, 4), (1350, 250, 3)
    ]
    
    for x, y, width in island_positions:
        for i in range(width):
            platforms.append(Platform(x + i * TILE_SIZE, y, TILE_SIZE, 150))
        trees.append(Tree(x + 30, y))
        if width > 3:
            trees.append(Tree(x + TILE_SIZE * (width - 1) - 20, y))
    
    # Gems - ต้องเก็บครบ 5 ตัว
    gems.append(Gem(250, 400))
    gems.append(Gem(450, 300))
    gems.append(Gem(700, 400))
    gems.append(Gem(900, 250))
    gems.append(Gem(1200, 350))
    
    # Enemies
    enemies.append(Enemy(250, 400))
    enemies.append(Enemy(500, 300))
    enemies.append(Enemy(900, 250))
    enemies.append(Enemy(1150, 350))
    
    # Clouds
    for i in range(12):
        clouds.append(Cloud(random.randint(0, 1800), random.randint(50, 180), random.uniform(0.7, 1.4)))
    
    return platforms, trees, clouds, gems, enemies, 1600

def build_level_3():
    """Level 3 - Sky Towers"""
    
    platforms = []
    trees = []
    clouds = []
    gems = []
    enemies = []
    
    ground_y = 650
    for i in range(80):
        platforms.append(Platform(i * TILE_SIZE, ground_y, TILE_SIZE, 50))
    
    # Tower 1
    for i in range(4):
        platforms.append(Platform(250, 650 - i * TILE_SIZE, TILE_SIZE * 2, TILE_SIZE))
    trees.append(Tree(270, 750 - 5 * TILE_SIZE))
    gems.append(Gem(270, 650 - 6 * TILE_SIZE - 20))
    
    # Tower 2
    for i in range(8):
        platforms.append(Platform(550, 650 - i * TILE_SIZE, TILE_SIZE * 3, TILE_SIZE))
    trees.append(Tree(590, 650 - 7 * TILE_SIZE))
    gems.append(Gem(590, 650 - 8 * TILE_SIZE - 20))
    enemies.append(Enemy(570, 650 - 7 * TILE_SIZE - 40))
    
    # Tower 3
    for i in range(10):
        platforms.append(Platform(900, 650 - i * TILE_SIZE, TILE_SIZE * 2, TILE_SIZE))
    trees.append(Tree(920, 650 - 9 * TILE_SIZE))
    gems.append(Gem(920, 650 - 10 * TILE_SIZE - 20))
    
    # Floating platforms
    for i in range(8):
        x = 350 + i * 80
        y = 400 - (i % 3) * 50
        platforms.append(Platform(x, y, TILE_SIZE, TILE_SIZE))
        if i % 2 == 0:
            gems.append(Gem(x + 15, y - 40))
    
    # More enemies
    enemies.append(Enemy(400, 350))
    enemies.append(Enemy(950, 250))
    
    # Clouds
    for i in range(15):
        clouds.append(Cloud(random.randint(0, 1500), random.randint(40, 160), random.uniform(0.8, 1.5)))
    
    return platforms, trees, clouds, gems, enemies, 1400

def build_level_4():
    """Level 4 - Canyon Gaps"""
    
    platforms = []
    trees = []
    clouds = []
    gems = []
    enemies = []
    
    ground_y = 650
    
    # Ground with gaps
    for i in range(0, 15):
        platforms.append(Platform(i * TILE_SIZE, ground_y, TILE_SIZE, 50))
    
    # Gap
    
    for i in range(20, 35):
        platforms.append(Platform(i * TILE_SIZE, ground_y, TILE_SIZE, 50))
    
    # Gap
    
    for i in range(40, 60):
        platforms.append(Platform(i * TILE_SIZE, ground_y, TILE_SIZE, 50))
    
    # Bridges over gaps
    for i in range(3):
        platforms.append(Platform(650 + i * TILE_SIZE, 500, TILE_SIZE, TILE_SIZE))
    
    for i in range(3):
        platforms.append(Platform(1400 + i * TILE_SIZE, 500, TILE_SIZE, TILE_SIZE * 2))
    
    # High platforms
    for i in range(5):
        platforms.append(Platform(300 + i * TILE_SIZE, 350, TILE_SIZE, 100))
    trees.append(Tree(350, 350))
    trees.append(Tree(450, 350))
    
    # Gems - 6 ตัว
    gems.append(Gem(400, 300))
    gems.append(Gem(700, 450))
    gems.append(Gem(900, 600))
    gems.append(Gem(1100, 600))
    gems.append(Gem(1450, 400))
    gems.append(Gem(1600, 600))
    
    # Enemies
    enemies.append(Enemy(350, 300))
    enemies.append(Enemy(700, 450))
    enemies.append(Enemy(1100, 600))
    enemies.append(Enemy(1500, 400))
    
    # Clouds
    for i in range(12):
        clouds.append(Cloud(random.randint(0, 2000), random.randint(50, 200), random.uniform(0.7, 1.3)))
    
    return platforms, trees, clouds, gems, enemies, 2200

def build_level_5():
    """Level 5 - Final Challenge"""
    
    platforms = []
    trees = []
    clouds = []
    gems = []
    enemies = []
    
    ground_y = 650
    for i in range(100):
        platforms.append(Platform(i * TILE_SIZE, ground_y, TILE_SIZE, 50))
    
    # Complex layout
    # Section 1 - Low platforms
    for i in range(4):
        platforms.append(Platform(200 + i * 100, 550, TILE_SIZE, 100))
        enemies.append(Enemy(220 + i * 100, 500))
    
    # Section 2 - High climb
    for i in range(4):
        platforms.append(Platform(650, 600 - i * 60, TILE_SIZE * 2, TILE_SIZE))
    trees.append(Tree(670, 850 - 7 * 60))
    gems.append(Gem(670, 800 - 8 * 60))
    
    # Section 3 - Sky platforms
    sky_platforms = [
        (900, 300), (1000, 250), (1100, 200),
        (1200, 250), (1300, 300), (1400, 350)
    ]
    
    for x, y in sky_platforms:
        platforms.append(Platform(x, y, TILE_SIZE, TILE_SIZE))
        gems.append(Gem(x + 15, y - 40))
    
    # Section 4 - Final island
    for i in range(7):
        platforms.append(Platform(1600 + i * TILE_SIZE, 240, TILE_SIZE, 250))
    trees.append(Tree(1650, 240))
    trees.append(Tree(1750, 240))
    trees.append(Tree(1850, 240))
    gems.append(Gem(1720, 150))
    
    # Many enemies
    enemies.append(Enemy(950, 250))
    enemies.append(Enemy(1150, 150))
    enemies.append(Enemy(1350, 300))
    enemies.append(Enemy(1700, 150))
    
    # Extra clouds
    for i in range(20):
        clouds.append(Cloud(random.randint(0, 2500), random.randint(40, 180), random.uniform(0.6, 1.5)))
    
    return platforms, trees, clouds, gems, enemies, 2400
