"""
Mario Maker Style Platformer - Configuration
"""

# Screen
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
FPS = 60  

# Colors - Beautiful palette inspired by the image
SKY_COLOR = (210, 190, 160)  # Tan/beige sky
CLOUD_WHITE = (255, 255, 255)
PLATFORM_DARK = (90, 85, 110)  # Dark purple-gray
PLATFORM_LIGHT = (120, 140, 160)  # Light blue-gray
GRASS_GREEN = (80, 150, 120)  # Teal green
TREE_TRUNK = (140, 100, 80)  # Brown
TREE_LEAVES = (100, 180, 140)  # Green
WATER_BLUE = (120, 160, 200)
PLAYER_COLOR = (100, 120, 200)  # Blue
ENEMY_COLOR = (200, 100, 150)  # Pink/purple
GEM_COLOR = (255, 100, 150)  # Pink gem
COIN_COLOR = (255, 200, 50)
GREEN = (0, 255, 0)  
WHITE = (255, 255, 255)  

# Physics
GRAVITY = 0.6
JUMP_SPEED = -14
MOVE_SPEED = 4
MAX_FALL_SPEED = 12

# Player
PLAYER_SIZE = 32

# Tile
TILE_SIZE = 48

# Enemy
ENEMY_SPEED = 1.5

# Camera
CAMERA_SMOOTHNESS = 0.1

# Network ports
TCP_PORT = 5555
UDP_PORT = 5556   # position updates (fast, drop-tolerant)

# Decorations
MAX_CLOUDS = 20
MAX_TREES = 15
