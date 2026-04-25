"""
Platformer with Multiplayer + Chat
Features: TCP/UDP hybrid, Room system, Ping display
"""
import pygame
import sys
import time
import math
import random
from core.config import *
from core.network import NetworkClient
from entities.player import Player
from entities.objects import *
from entities.enemies import Enemy
from levels.builder import build_level, build_level_2, build_level_3, build_level_4, build_level_5
from ui.chat import ChatBox

# Initialize
pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Multiplayer Platformer + Chat")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)

# ---------------------------------------------------------------- visuals --
# Pre-render gradient sky (done once, blitted every frame)
sky_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
for _y in range(WINDOW_HEIGHT):
    _t = _y / WINDOW_HEIGHT
    _c = (
        int(SKY_TOP[0] + (SKY_BOTTOM[0] - SKY_TOP[0]) * _t),
        int(SKY_TOP[1] + (SKY_BOTTOM[1] - SKY_TOP[1]) * _t),
        int(SKY_TOP[2] + (SKY_BOTTOM[2] - SKY_TOP[2]) * _t),
    )
    pygame.draw.line(sky_surface, _c, (0, _y), (WINDOW_WIDTH, _y))

# Mountain shapes for background parallax
_mountain_data = [
    (0, 520, 260), (220, 450, 230), (420, 510, 250),
    (620, 460, 240), (840, 530, 270), (1060, 470, 245),
    (1280, 520, 260), (1500, 455, 235),
]

def _draw_mountains(surface, camera_x):
    for mx, my, mh in _mountain_data:
        for rep in range(3):
            bx = mx + rep * 1700
            sx = int(bx - camera_x * 0.15)
            pts = [(sx, my), (sx + mh // 2, my - mh), (sx + mh, my)]
            pygame.draw.polygon(surface, MOUNTAIN_FAR, pts)
            pygame.draw.line(surface, MOUNTAIN_NEAR, (sx, my), (sx + mh // 2, my - mh), 2)


# ------------------------------------------------------------ particles ----
class Particle:
    __slots__ = ['x', 'y', 'vx', 'vy', 'color', 'life', 'max_life', 'size']

    def __init__(self, x, y, color, vx, vy, life=0.8, size=4):
        self.x = x;  self.y = y
        self.vx = vx; self.vy = vy
        self.color    = color
        self.life     = life
        self.max_life = life
        self.size     = size

    def update(self, dt):
        self.x  += self.vx * dt * 60
        self.y  += self.vy * dt * 60
        self.vy += 0.08
        self.life -= dt

    def draw(self, surface, camera_x):
        alpha = max(0, self.life / self.max_life)
        s = max(1, int(self.size * alpha))
        pygame.draw.circle(surface, self.color,
                           (int(self.x - camera_x), int(self.y)), s)

    @property
    def alive(self):
        return self.life > 0


particles = []


def spawn_gem_particles(x, y):
    colors = [GEM_COLOR, GEM_INNER, GEM_GLOW, WHITE]
    for _ in range(14):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(1.0, 3.5)
        particles.append(Particle(
            x, y, random.choice(colors),
            math.cos(angle) * speed,
            math.sin(angle) * speed - 2.5,
            life=random.uniform(0.5, 0.9),
            size=random.randint(2, 5)
        ))


def spawn_stomp_particles(x, y):
    colors = [ENEMY_COLOR, ENEMY_DARK, (255, 180, 100), WHITE]
    for _ in range(10):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(0.5, 2.5)
        particles.append(Particle(
            x, y, random.choice(colors),
            math.cos(angle) * speed,
            math.sin(angle) * speed - 3.0,
            life=random.uniform(0.4, 0.7),
            size=random.randint(2, 4)
        ))

# Network
network = NetworkClient()
other_players = {}
my_player_id = None
current_room = 1
player_chat_bubbles = {}  # {player_id: {"text": str, "time": float}}

# Game state
current_level = 1
score = 0
gems_collected = 0
total_gems = 0
player_gem_counts = {}   # {player_id: gems collected this level}

# Chat
chat = ChatBox(10, WINDOW_HEIGHT - 180, 350, 170)


# --------------------------------------------------------- helper (bubble) ---
def _draw_bubble(surface, text, cx, y):
    bfont = pygame.font.Font(None, 16)
    rendered = bfont.render(text[:30], True, (0, 0, 0))
    w, h = rendered.get_width() + 12, 22
    bx = cx - w // 2
    pygame.draw.rect(surface, (255, 255, 255), (bx, y, w, h), border_radius=8)
    pygame.draw.rect(surface, (100, 100, 100), (bx, y, w, h), 2, border_radius=8)
    surface.blit(rendered, (bx + 6, y + 4))


# ------------------------------------------------------------------ LOBBY ---
def show_lobby(room_counts):
    """Room selection screen — shows live player counts, refreshes in background."""
    title_font = pygame.font.Font(None, 64)
    btn_font   = pygame.font.Font(None, 46)
    cnt_font   = pygame.font.Font(None, 26)
    info_font  = pygame.font.Font(None, 24)

    room_colors = {1: (80, 130, 220), 2: (80, 190, 130), 3: (210, 120, 80)}

    # Background thread refreshes room counts every 3 seconds without blocking UI
    import threading as _threading
    _stop = [False]
    def _refresh():
        while not _stop[0]:
            network.get_room_info()
            for _ in range(30):   # sleep 3s in small steps so thread exits fast
                if _stop[0]:
                    break
                time.sleep(0.1)
    _threading.Thread(target=_refresh, daemon=True).start()

    while True:
        screen.fill((20, 22, 40))

        title = title_font.render("MULTIPLAYER PLATFORMER", True, (255, 255, 255))
        screen.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 120)))

        sub = btn_font.render("Select a Room to join", True, (180, 180, 220))
        screen.blit(sub, sub.get_rect(center=(WINDOW_WIDTH // 2, 190)))

        mouse_pos = pygame.mouse.get_pos()
        clicked   = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                clicked = True

        for i, room_id in enumerate([1, 2, 3]):
            btn_rect = pygame.Rect(WINDOW_WIDTH // 2 - 170, 280 + i * 100, 340, 75)
            hover    = btn_rect.collidepoint(mouse_pos)
            base_col = room_colors[room_id]
            col      = tuple(min(255, c + 45) for c in base_col) if hover else base_col

            pygame.draw.rect(screen, col, btn_rect, border_radius=14)
            pygame.draw.rect(screen, (255, 255, 255), btn_rect, 2, border_radius=14)

            label = btn_font.render(f"Room {room_id}", True, (255, 255, 255))
            screen.blit(label, label.get_rect(midleft=(btn_rect.x + 24, btn_rect.centery)))

            # Player count badge — read from network.room_counts (updated by background thread)
            count = network.room_counts.get(room_id, 0)
            badge = cnt_font.render(f"{count} player{'s' if count != 1 else ''}", True, (255, 255, 200))
            screen.blit(badge, badge.get_rect(midright=(btn_rect.right - 20, btn_rect.centery)))

            if hover and clicked:
                _stop[0] = True   # stop refresh thread
                return room_id

        note = info_font.render(
            "Players in the same room see each other  |  Different rooms are isolated",
            True, (120, 120, 160)
        )
        screen.blit(note, note.get_rect(center=(WINDOW_WIDTH // 2, 590)))

        proto = info_font.render(
            "Position: UDP  |  Chat / Gems / Events: TCP  |  Auto-reconnect enabled",
            True, (100, 180, 140)
        )
        screen.blit(proto, proto.get_rect(center=(WINDOW_WIDTH // 2, 616)))

        pygame.display.flip()
        clock.tick(60)


# ------------------------------------------------------------------ LEVEL ---
def load_level(level_num):
    global player, platforms, trees, clouds, gems, enemies, level_width, camera_x, gems_collected, total_gems, player_gem_counts

    player = Player(100, 500)
    camera_x = 0
    gems_collected = 0
    player_gem_counts = {}

    if level_num == 1:
        platforms, trees, clouds, gems, enemies, level_width = build_level()
    elif level_num == 2:
        platforms, trees, clouds, gems, enemies, level_width = build_level_2()
    elif level_num == 3:
        platforms, trees, clouds, gems, enemies, level_width = build_level_3()
    elif level_num == 4:
        platforms, trees, clouds, gems, enemies, level_width = build_level_4()
    else:
        platforms, trees, clouds, gems, enemies, level_width = build_level_5()

    total_gems = len(gems)
    print(f"Level {level_num} loaded  |  Gems: {total_gems}")


# --------------------------------------------------------- NETWORK CALLBACKS -
def on_init(message):
    global my_player_id, current_room
    my_player_id = message.get("player_id")
    current_room = message.get("room_id", 1)
    game_state   = message.get("game_state", {})
    for pid, pdata in game_state.get("players", {}).items():
        if pid != my_player_id:
            other_players[pid] = {
                "player": Player(pdata["x"], pdata["y"]),
                "name":   pdata["name"]
            }
    chat.add_message("System", f"You are {my_player_id}  |  Room {current_room}")


def on_player_join(message):
    player_id   = message.get("player_id")
    player_data = message.get("player_data")
    if player_id not in other_players and player_id != my_player_id:
        other_players[player_id] = {
            "player": Player(player_data["x"], player_data["y"]),
            "name":   player_data["name"]
        }
        chat.add_message("System", f"{player_data['name']} joined")


def on_player_leave(message):
    player_id = message.get("player_id")
    if player_id in other_players:
        name = other_players[player_id]["name"]
        del other_players[player_id]
        chat.add_message("System", f"{name} left")


def on_player_move(message):
    player_id = message.get("player_id")
    if player_id in other_players:
        other_players[player_id]["player"].x = message.get("x")
        other_players[player_id]["player"].y = message.get("y")


def on_chat_message(message):
    name      = message.get("name")
    text      = message.get("text")
    player_id = message.get("player_id")

    if player_id == my_player_id:
        chat.add_message("You", text)
    else:
        chat.add_message(name, text)

    player_chat_bubbles[player_id] = {"text": text, "time": time.time()}


def on_gem_collected(message):
    global gems_collected, score, level_complete
    gem_idx      = message.get("gem_id")   # คือ index ในลิสต์ gems
    collector_id = message.get("player_id")
    if gem_idx is not None and 0 <= gem_idx < len(gems):
        gem = gems[gem_idx]
        if not gem.collected:
            gem.collected = True
            gems_collected += 1
            # score ไม่เพิ่ม — เฉพาะ player ที่เก็บเองถึงได้แต้ม
            player_gem_counts[collector_id] = player_gem_counts.get(collector_id, 0) + 1
            if gems_collected >= total_gems:
                level_complete = True


def on_enemy_stomped(message):
    enemy_idx = message.get("enemy_idx")
    if enemy_idx is not None and 0 <= enemy_idx < len(enemies):
        enemies[enemy_idx].stomp()


def on_next_level(message):
    global current_level, level_complete
    current_level = message.get("level", current_level)
    load_level(current_level)
    level_complete = False


network.on_init          = on_init
network.on_player_join   = on_player_join
network.on_player_leave  = on_player_leave
network.on_player_move   = on_player_move
network.on_chat          = on_chat_message
network.on_gem_collected = on_gem_collected
def on_reconnected():
    chat.add_message("System", "Reconnected to server!")


network.on_next_level    = on_next_level
network.on_enemy_stomped = on_enemy_stomped
network.on_reconnected   = on_reconnected


# --------------------------------------------------------------- STARTUP ----
print("Connecting to server...")
room_counts   = network.get_room_info()
selected_room = show_lobby(room_counts)
if not network.join_room(selected_room):
    print("Server not running!  Run: python server.py")
    sys.exit()

load_level(current_level)

print("=" * 60)
print("MULTIPLAYER PLATFORMER + CHAT")
print("=" * 60)
print("A/D: Move  |  SPACE: Jump  |  ENTER: Chat  |  R: Restart")
print("=" * 60)


# ---------------------------------------------------------------- GAME LOOP --
running = True
keys = set()
level_complete = False
last_position_send = 0

while running:
    dt = clock.tick(FPS) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if chat.active and not chat.is_mouse_over(event.pos):
                chat.active = False
                chat.input_text = ""

        elif event.type == pygame.KEYDOWN:
            keys.add(event.key)

            message = chat.handle_event(event)
            if message:
                network.send_chat(message)
                player_chat_bubbles[my_player_id] = {"text": message, "time": time.time()}
            if chat.active:
                continue

            if event.key == pygame.K_r:
                load_level(current_level)
                level_complete = False
            elif event.key == pygame.K_n and level_complete:
                if current_level < 5:
                    network.send_next_level(current_level + 1)
                    # all clients (including me) load via on_next_level callback

        elif event.type == pygame.KEYUP:
            keys.discard(event.key)

    # ------------------------------------------------------------ input ------
    if not chat.active:
        if pygame.K_a in keys or pygame.K_LEFT in keys:
            player.move_left()
        elif pygame.K_d in keys or pygame.K_RIGHT in keys:
            player.move_right()
        else:
            player.stop()

        if pygame.K_SPACE in keys or pygame.K_w in keys or pygame.K_UP in keys:
            player.jump()

    # ------------------------------------------------------------ update -----
    player.update(dt, platforms)

    # Send position via UDP every 50 ms
    if time.time() - last_position_send > 0.05:
        network.send_move(player.x, player.y)
        last_position_send = time.time()

    for tree in trees:
        tree.update(dt)
    for cloud in clouds:
        cloud.update(dt)

    for idx, gem in enumerate(gems):
        if not gem.collected:
            gem.update(dt)
            if player.get_rect().colliderect(gem.get_rect()):
                gem.collected = True
                gems_collected += 1
                score += 10
                player_gem_counts[my_player_id] = player_gem_counts.get(my_player_id, 0) + 1
                network.send_gem(idx)
                spawn_gem_particles(gem.x, gem.y)
                if gems_collected >= total_gems:
                    level_complete = True
                    score += 100

    for idx, enemy in enumerate(enemies):
        if enemy.alive:
            enemy.update(dt, platforms)
            if player.get_rect().colliderect(enemy.get_rect()):
                if player.vel_y > 0 and player.y + player.height - 10 < enemy.y + enemy.height // 2:
                    enemy.stomp()
                    player.vel_y = -8
                    score += 100
                    network.send_enemy_stomp(idx)
                    spawn_stomp_particles(enemy.x + enemy.width // 2, enemy.y)
                else:
                    player.x, player.y = 100, 500
                    player.vel_x = player.vel_y = 0

    # ------------------------------------------------------------ camera -----
    target_camera = player.x - WINDOW_WIDTH // 3
    target_camera = max(0, min(target_camera, level_width - WINDOW_WIDTH))
    camera_x += (target_camera - camera_x) * CAMERA_SMOOTHNESS

    # ------------------------------------------------------------ draw -------
    screen.blit(sky_surface, (0, 0))
    _draw_mountains(screen, camera_x)

    for cloud in clouds:
        cloud.draw(screen, camera_x)

    # Water with gradient
    water_y = 680
    for _wy in range(WINDOW_HEIGHT - water_y):
        _wt = _wy / (WINDOW_HEIGHT - water_y)
        _wc = (
            int(WATER_TOP[0] + (WATER_BOTTOM[0] - WATER_TOP[0]) * _wt),
            int(WATER_TOP[1] + (WATER_BOTTOM[1] - WATER_TOP[1]) * _wt),
            int(WATER_TOP[2] + (WATER_BOTTOM[2] - WATER_TOP[2]) * _wt),
        )
        pygame.draw.line(screen, _wc, (0, water_y + _wy), (WINDOW_WIDTH, water_y + _wy))
    # Water shimmer
    shimmer_x = int((time.time() * 60) % WINDOW_WIDTH)
    pygame.draw.line(screen, (180, 220, 255), (shimmer_x, water_y), (shimmer_x + 40, water_y + 3), 2)

    for platform in platforms:
        platform.draw(screen, camera_x)
    for tree in trees:
        tree.draw(screen, camera_x)
    for gem in gems:
        gem.draw(screen, camera_x)
    for enemy in enemies:
        enemy.draw(screen, camera_x)

    # Particles
    for p in particles[:]:
        p.update(dt)
        if p.alive:
            p.draw(screen, camera_x)
        else:
            particles.remove(p)

    # Other players
    for pid, pdata in other_players.items():
        op = pdata["player"]
        op.draw(screen, camera_x)
        name_surface = small_font.render(pdata["name"], True, (255, 200, 100))
        screen.blit(name_surface, (op.x - camera_x - name_surface.get_width() // 2 + 16, op.y - 15))

        if pid in player_chat_bubbles:
            bubble = player_chat_bubbles[pid]
            if time.time() - bubble["time"] < 5:
                _draw_bubble(screen, bubble["text"], op.x - camera_x + 16, op.y - 45)
            else:
                del player_chat_bubbles[pid]

    # My player
    player.draw(screen, camera_x)
    if my_player_id:
        my_label = small_font.render("You", True, (100, 255, 100))
        screen.blit(my_label, (player.x - camera_x - my_label.get_width() // 2 + 16, player.y - 15))

        if my_player_id in player_chat_bubbles:
            bubble = player_chat_bubbles[my_player_id]
            if time.time() - bubble["time"] < 5:
                _draw_bubble(screen, bubble["text"], player.x - camera_x + 16, player.y - 45)
            else:
                del player_chat_bubbles[my_player_id]

    # ------------------------------------------------------------ HUD --------
    pygame.draw.rect(screen, (0, 0, 0, 120), (10, 10, 220, 110), border_radius=10)
    screen.blit(font.render(f"Score: {score}", True, WHITE), (20, 18))
    gems_color = GRASS_GREEN if gems_collected >= total_gems else GEM_COLOR
    screen.blit(font.render(f"Gems: {gems_collected}/{total_gems}", True, gems_color), (20, 52))

    # Room badge
    room_colors = {1: (80, 130, 220), 2: (80, 190, 130), 3: (210, 120, 80)}
    room_col = room_colors.get(current_room, WHITE)
    screen.blit(small_font.render(f"Room {current_room}", True, room_col), (20, 88))

    # Ping (top-right)
    ping = network.ping_ms
    ping_col = (100, 255, 100) if ping < 50 else (255, 220, 50) if ping < 100 else (255, 80, 80)
    pygame.draw.rect(screen, (0, 0, 0, 120), (WINDOW_WIDTH - 140, 10, 130, 56), border_radius=10)
    screen.blit(small_font.render(f"Ping: {ping:.2f} ms", True, ping_col), (WINDOW_WIDTH - 130, 18))
    screen.blit(small_font.render(f"Players: {len(other_players) + 1}", True, WHITE), (WINDOW_WIDTH - 130, 38))

    # Level indicator
    screen.blit(small_font.render(f"Level {current_level}/5", True, (200, 200, 200)), (WINDOW_WIDTH // 2 - 30, 16))

    # Chat
    chat.draw(screen)

    # Level complete overlay
    if level_complete:
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (0, 0, 0, 180), (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))
        screen.blit(overlay, (0, 0))

        cy = WINDOW_HEIGHT // 2 - 100

        if current_level < 5:
            complete_text = font.render("LEVEL COMPLETE!", True, GRASS_GREEN)
        else:
            complete_text = font.render("ALL LEVELS COMPLETE!", True, (255, 215, 0))
        screen.blit(complete_text, complete_text.get_rect(center=(WINDOW_WIDTH // 2, cy)))
        cy += 50

        # Gem summary per player
        summary_title = small_font.render("── Gems Collected ──", True, (200, 200, 200))
        screen.blit(summary_title, summary_title.get_rect(center=(WINDOW_WIDTH // 2, cy)))
        cy += 28

        # My row
        my_count = player_gem_counts.get(my_player_id, 0)
        my_row = small_font.render(f"You ({my_player_id})  :  {my_count} gems", True, (100, 255, 100))
        screen.blit(my_row, my_row.get_rect(center=(WINDOW_WIDTH // 2, cy)))
        cy += 24

        # Other players
        for pid, pdata in other_players.items():
            count = player_gem_counts.get(pid, 0)
            row = small_font.render(f"{pdata['name']} ({pid})  :  {count} gems", True, (255, 200, 100))
            screen.blit(row, row.get_rect(center=(WINDOW_WIDTH // 2, cy)))
            cy += 24

        cy += 10
        if current_level < 5:
            next_text = small_font.render("Press N to go to next level", True, WHITE)
        else:
            next_text = small_font.render("You won! Thanks for playing!", True, WHITE)
        screen.blit(next_text, next_text.get_rect(center=(WINDOW_WIDTH // 2, cy)))

    # Controls hint
    if chat.active:
        hint = small_font.render("Typing... | ENTER: Send | ESC: Cancel", True, (255, 200, 100))
    else:
        hint = small_font.render("A/D: Move | SPACE: Jump | ENTER: Chat | TAB: Hide chat | R: Restart", True, (100, 100, 100))
    screen.blit(hint, (WINDOW_WIDTH // 2 - hint.get_width() // 2, WINDOW_HEIGHT - 22))

    # Connection lost / reconnecting overlay
    if not network.connected:
        lost_overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(lost_overlay, (0, 0, 0, 160), (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))
        screen.blit(lost_overlay, (0, 0))
        if network.reconnecting:
            lost_text = font.render("Connection Lost - Reconnecting...", True, (255, 200, 50))
            lost_sub  = small_font.render(f"Attempt {network.reconnect_attempts}  |  Retrying every 3 seconds", True, WHITE)
        else:
            lost_text = font.render("Connection Lost", True, (255, 80, 80))
            lost_sub  = small_font.render("Server disconnected. Please restart the game.", True, WHITE)
        screen.blit(lost_text, lost_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 20)))
        screen.blit(lost_sub,  lost_sub.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 20)))

    pygame.display.flip()

pygame.quit()
sys.exit()
