"""
Platformer with Multiplayer + Chat
Features: TCP/UDP hybrid, Room system, Ping display
"""
import pygame
import sys
import time
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
def show_lobby():
    """Room selection screen — returns chosen room_id (1-3)."""
    title_font  = pygame.font.Font(None, 64)
    btn_font    = pygame.font.Font(None, 46)
    info_font   = pygame.font.Font(None, 26)

    room_colors = {
        1: (80, 130, 220),
        2: (80, 190, 130),
        3: (210, 120, 80),
    }
    room_labels = {
        1: "Room 1",
        2: "Room 2",
        3: "Room 3",
    }

    while True:
        screen.fill((20, 22, 40))

        # Title
        title = title_font.render("MULTIPLAYER PLATFORMER", True, (255, 255, 255))
        screen.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 130)))

        sub = btn_font.render("Select a Room to join", True, (180, 180, 220))
        screen.blit(sub, sub.get_rect(center=(WINDOW_WIDTH // 2, 200)))

        mouse_pos = pygame.mouse.get_pos()
        clicked   = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                clicked = True

        for i, room_id in enumerate([1, 2, 3]):
            btn_rect = pygame.Rect(WINDOW_WIDTH // 2 - 160, 290 + i * 100, 320, 70)
            hover    = btn_rect.collidepoint(mouse_pos)
            base_col = room_colors[room_id]
            col      = tuple(min(255, c + 50) for c in base_col) if hover else base_col

            pygame.draw.rect(screen, col, btn_rect, border_radius=14)
            pygame.draw.rect(screen, (255, 255, 255), btn_rect, 2, border_radius=14)

            label = btn_font.render(room_labels[room_id], True, (255, 255, 255))
            screen.blit(label, label.get_rect(center=btn_rect.center))

            if hover and clicked:
                return room_id

        # Info line
        note = info_font.render(
            "Players in the same room see each other  |  Different rooms are isolated",
            True, (120, 120, 160)
        )
        screen.blit(note, note.get_rect(center=(WINDOW_WIDTH // 2, 600)))

        # Protocol note
        proto = info_font.render(
            "Position sync: UDP  |  Chat / Gems / Events: TCP",
            True, (100, 180, 140)
        )
        screen.blit(proto, proto.get_rect(center=(WINDOW_WIDTH // 2, 630)))

        pygame.display.flip()
        clock.tick(60)


# ------------------------------------------------------------------ LEVEL ---
def load_level(level_num):
    global player, platforms, trees, clouds, gems, enemies, level_width, camera_x, gems_collected, total_gems

    player = Player(100, 500)
    camera_x = 0
    gems_collected = 0

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
    gem_id = message.get("gem_id")
    for gem in gems:
        if id(gem) == gem_id and not gem.collected:
            gem.collected = True
            break


network.on_init          = on_init
network.on_player_join   = on_player_join
network.on_player_leave  = on_player_leave
network.on_player_move   = on_player_move
network.on_chat          = on_chat_message
network.on_gem_collected = on_gem_collected


# --------------------------------------------------------------- STARTUP ----
selected_room = show_lobby()
print(f"Connecting to Room {selected_room}...")
if not network.connect(selected_room):
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
                    current_level += 1
                    load_level(current_level)
                    level_complete = False

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

    for gem in gems:
        if not gem.collected:
            gem.update(dt)
            if player.get_rect().colliderect(gem.get_rect()):
                gem.collected = True
                gems_collected += 1
                score += 10
                network.send_gem(id(gem))
                if gems_collected >= total_gems:
                    level_complete = True
                    score += 100

    for enemy in enemies:
        if enemy.alive:
            enemy.update(dt, platforms)
            if player.get_rect().colliderect(enemy.get_rect()):
                if player.vel_y > 0 and player.y + player.height - 10 < enemy.y + enemy.height // 2:
                    enemy.stomp()
                    player.vel_y = -8
                    score += 100
                else:
                    player.x, player.y = 100, 500
                    player.vel_x = player.vel_y = 0

    # ------------------------------------------------------------ camera -----
    target_camera = player.x - WINDOW_WIDTH // 3
    target_camera = max(0, min(target_camera, level_width - WINDOW_WIDTH))
    camera_x += (target_camera - camera_x) * CAMERA_SMOOTHNESS

    # ------------------------------------------------------------ draw -------
    screen.fill(SKY_COLOR)

    for cloud in clouds:
        cloud.draw(screen, camera_x)

    pygame.draw.rect(screen, WATER_BLUE, (0, 680, WINDOW_WIDTH, WINDOW_HEIGHT - 680))

    for platform in platforms:
        platform.draw(screen, camera_x)
    for tree in trees:
        tree.draw(screen, camera_x)
    for gem in gems:
        gem.draw(screen, camera_x)
    for enemy in enemies:
        enemy.draw(screen, camera_x)

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
    screen.blit(small_font.render(f"Ping: {ping} ms", True, ping_col), (WINDOW_WIDTH - 130, 18))
    screen.blit(small_font.render(f"Players: {len(other_players) + 1}", True, WHITE), (WINDOW_WIDTH - 130, 38))

    # Level indicator
    screen.blit(small_font.render(f"Level {current_level}/5", True, (200, 200, 200)), (WINDOW_WIDTH // 2 - 30, 16))

    # Chat
    chat.draw(screen)

    # Level complete overlay
    if level_complete:
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (0, 0, 0, 150), (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))
        screen.blit(overlay, (0, 0))
        if current_level < 5:
            complete_text = font.render("LEVEL COMPLETE!", True, GRASS_GREEN)
            next_text     = small_font.render("Press N for next level", True, WHITE)
        else:
            complete_text = font.render("ALL LEVELS COMPLETE!", True, (255, 215, 0))
            next_text     = small_font.render("You won!", True, WHITE)
        screen.blit(complete_text, complete_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 30)))
        screen.blit(next_text,     next_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 10)))

    # Controls hint
    if chat.active:
        hint = small_font.render("Typing... | ENTER: Send | ESC: Cancel", True, (255, 200, 100))
    else:
        hint = small_font.render("A/D: Move | SPACE: Jump | ENTER: Chat | TAB: Hide chat | R: Restart", True, (100, 100, 100))
    screen.blit(hint, (WINDOW_WIDTH // 2 - hint.get_width() // 2, WINDOW_HEIGHT - 22))

    pygame.display.flip()

pygame.quit()
sys.exit()
