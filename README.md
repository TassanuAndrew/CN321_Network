# Multiplayer Platformer Game — Final

Real-time multiplayer 2D platformer with **TCP + UDP hybrid networking**, **room/lobby system**, **auto-reconnect**, and **live ping display**. Built with Python + Pygame for **CN321 — Data Communication and Computer Networks**.

---

## Project Overview

A 2D platformer game featuring real-time multiplayer using **Socket Programming**. Players join one of 3 isolated rooms, see each other move in real-time, collect gems cooperatively, defeat enemies, and chat through speech bubbles.

This is the **Final version** — extended from the midterm singleplayer build with significant network upgrades.

### What's New (vs. Midterm)

| Feature | Description |
|---|---|
| **TCP + UDP Hybrid** | TCP for reliable events (chat/gem/level), UDP for fast position updates (~60 fps) |
| **Room & Lobby System** | 3 isolated rooms with real-time player counts |
| **Ping Display** | Live RTT measurement via PING/PONG (ms precision) |
| **Auto-Reconnect** | TCP drop → retry every 3s, rejoin same room automatically |
| **Cooperative Sync** | Gems / enemies / level synced across all clients (index-based) |
| **Visual Overhaul** | Gradient sky, parallax mountains, particle FX |

### Bug Fixes from Midterm
- `id(gem)` → **list index** (cross-process safe)
- Gem list reset on `NEXT_LEVEL`
- Ping uses `round(..., 2)` instead of `int()` (preserves sub-millisecond precision)
- Lobby refresh runs in a background thread (non-blocking UI)

---

## Installation & Setup

### Prerequisites
```bash
Python 3.9+
pip install pygame
```

### Running the Game

**Step 1: Start Server**
```bash
python3 server.py
```

**Step 2: Start Client(s)**
```bash
python3 main.py
```
Open multiple terminals to run multiple clients for multiplayer testing.

---

## Controls

| Action | Key |
|--------|-----|
| Move | A/D or Arrow Keys |
| Jump | SPACE |
| Open/Send Chat | ENTER |
| Cancel Chat | ESC |
| Toggle Chat Window | TAB |
| Restart Level | R |
| Next Level | N |

---

## Project Structure
```
multiplayer-platformer-game/
├── server.py              # TCP + UDP server with room system
├── main.py                # Game client (lobby + game loop)
├── core/
│   ├── config.py          # Constants & color palette
│   └── network.py         # NetworkClient (TCP+UDP, auto-reconnect)
├── entities/
│   ├── player.py          # Player character logic
│   ├── objects.py         # Platforms, trees, clouds, gems
│   └── enemies.py         # Enemy AI
├── levels/
│   └── builder.py         # Level designs
└── ui/
    └── chat.py            # Chat interface + speech bubbles
```

---

## Technical Implementation

### Network Architecture

| Layer | Protocol | Port | Use Case |
|---|---|---|---|
| Reliable channel | **TCP** | 5555 | INIT, CHAT, GEM, ENEMY_STOMPED, NEXT_LEVEL, PING/PONG |
| Fast channel | **UDP** | 5556 | MOVE / PLAYER_MOVE (~60 fps) |

- **Server:** Multi-threaded — 1 thread per connected client + 1 dedicated UDP receiver thread
- **Client:** Daemon threads for `_receive_tcp` and `_ping_loop` (non-blocking game loop)
- **Data Format:** JSON, newline (`\n`) delimited
- **Concurrency:** `threading.Lock` protects shared room/player state

### Architecture Diagram
```
   Client 1 ─┐                        ┌─ Client 3
   (Room 1)  │                        │  (Room 2)
             ├──── TCP :5555 ────► SERVER
   Client 2 ─┤◄───  UDP :5556  ────┤  ├─ Client N
   (Room 1)  │                        │  (Room 3)
             └────────────────────────┘
                  Rooms: {1, 2, 3}
                  Thread per client
```

### Message Protocol

All messages are JSON, terminated by `\n`.

| Type | Direction | Channel | Payload |
|------|-----------|---------|---------|
| `ROOM_INFO` | Server → Client | TCP | `{rooms: {1: 2, 2: 0, 3: 1}}` |
| `INIT` | Server → Client | TCP | `player_id, room_id, game_state` |
| `MOVE` | Client → Server | **UDP** | `x, y` |
| `PLAYER_MOVE` | Server → Clients | **UDP→TCP bcast** | `player_id, x, y` |
| `PLAYER_JOIN` | Server → Clients | TCP | `player_id, player_data` |
| `PLAYER_LEAVE` | Server → Clients | TCP | `player_id` |
| `CHAT` | Both | TCP | `player_id, name, text` |
| `GEM` / `GEM_COLLECTED` | Both | TCP | `gem_id` (list index) |
| `ENEMY_STOMPED` | Both | TCP | `enemy_idx` |
| `NEXT_LEVEL` | Both | TCP | `level` |
| `PING` / `PONG` | Both | TCP | `timestamp` |

### Connection & Lobby Flow

```
1. Client opens temp TCP socket → reads ROOM_INFO → closes
   (server discards connection that never sends room_id)

2. Lobby UI displays player counts per room

3. Client picks room → opens fresh TCP socket
   → reads (and discards) ROOM_INFO
   → sends {"room_id": N}

4. Server creates player_id, returns INIT with game_state

5. Client registers UDP address with UDP_REGISTER message

6. Game loop runs:
   - MOVE via UDP every frame
   - GEM/CHAT/EVENTS via TCP as they happen
   - PING via TCP every 1s
```

### Auto-Reconnect

When the TCP socket drops:
1. `recv()` raises an exception → `connected = False`
2. Background thread sleeps 3s, then tries `tcp.connect()` again
3. On success: re-reads `ROOM_INFO`, re-sends original `room_id`, re-registers UDP
4. Triggers `on_reconnected()` callback (chat shows "Reconnected!")

The main game loop never blocks — players keep playing locally during reconnect attempts.

### Cooperative Sync (Why list index, not `id()`)

Python's `id(obj)` returns a memory address that **differs per process**. Two clients running the same level get totally different `id()` values for the "same" gem, breaking sync.

**Solution:** Use the gem's **index in the level's gem list** (0, 1, 2, ...). The list is built deterministically from `levels/builder.py`, so index N refers to the same gem on every client.

```python
# WRONG — different per process
self.network.send_gem(id(gem))

# CORRECT — same on every client
self.network.send_gem(gem_index)
```

---

## Learning Objectives

This project covers core concepts from CN321:

**Network Programming**
- TCP vs. UDP trade-offs (reliability vs. latency)
- Socket lifecycle: `bind` / `listen` / `accept` / `recv` / `send` / `sendto` / `recvfrom`
- Multi-protocol server (one process, two ports)
- Connection state management & graceful disconnect handling
- RTT measurement (PING/PONG)
- Auto-recovery from network failure

**Concurrency**
- Thread-per-client server pattern
- Daemon threads for background I/O
- `threading.Lock` for shared mutable state
- Non-blocking UI through background workers

**Protocol Design**
- JSON message envelopes with type-based routing
- Newline delimiter framing for stream-based TCP
- Optimistic local update + authoritative server broadcast
- Selective broadcast (`exclude_conn` / `exclude_player`) and inclusive broadcast
- Room-scoped message routing

---

## Troubleshooting

**Connection refused** — Ensure `server.py` is running before starting any client.

**Port already in use**
```bash
lsof -i :5555
lsof -i :5556
kill -9 <PID>
```

**Players not visible** — Check the server console — both clients must show `+ PN joined Room X`.

**Ping shows 0 ms** — Make sure you're on the latest code; older `int()` rounding has been replaced with `round(..., 2)`.

**Chat not working** — Verify the TCP connection (look for `Reconnecting...` HUD text); CHAT goes over TCP only.

**Stuck on lobby** — `get_room_info()` has a 2s timeout; if the server is unreachable it returns zeros and the lobby still loads.

---

## Possible Extensions

- Server-authoritative collision (anti-cheat)
- Player authentication / persistent profiles
- Spectator mode
- Replay system (record JSON message stream)
- Lag compensation / client-side prediction
- WebSocket gateway for browser clients
- Dockerized server deployment

---

## Course

**CN321 — Data Communication and Computer Networks** · Final Project · Group **MonoUnit**
