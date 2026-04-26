"""
Socket Server for Multiplayer Game
Features: TCP + UDP hybrid, Room system, Ping/Pong
"""
import socket
import threading
import json
import time

class GameServer:
    def __init__(self, host='192.168.0.11', port=5555):
        self.host = host
        self.port = port
        self.tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.clients = {}       # conn -> {"id", "room", "name"}
        self.rooms = {
            1: {"players": {}, "gems": []},
            2: {"players": {}, "gems": []},
            3: {"players": {}, "gems": []},
        }
        self.udp_clients = {}   # addr -> {"player_id", "room_id"}
        self.running = True
        self.client_counter = 0
        self.lock = threading.Lock()

    def start(self):
        self.tcp_server.bind((self.host, self.port))
        self.udp_server.bind((self.host, self.port + 1))
        self.tcp_server.listen(10)

        print("=" * 60)
        print("MULTIPLAYER GAME SERVER")
        print("=" * 60)
        print(f"TCP : {self.host}:{self.port}     (chat, gems, events)")
        print(f"UDP : {self.host}:{self.port + 1}     (position updates)")
        print("Rooms: 1, 2, 3  |  Waiting for players...")
        print("=" * 60)

        threading.Thread(target=self.handle_udp, daemon=True).start()

        while self.running:
            try:
                conn, addr = self.tcp_server.accept()
                threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()
            except Exception:
                pass

    # ------------------------------------------------------------------ UDP --
    def handle_udp(self):
        while self.running:
            try:
                data, addr = self.udp_server.recvfrom(1024)
                message = json.loads(data.decode('utf-8'))
                msg_type = message.get("type")

                if msg_type == "UDP_REGISTER":
                    player_id = message.get("player_id")
                    room_id = None
                    with self.lock:
                        for client in self.clients.values():
                            if client["id"] == player_id:
                                room_id = client["room"]
                                break
                    if room_id:
                        self.udp_clients[addr] = {"player_id": player_id, "room_id": room_id}
                        print(f"  UDP registered: {player_id} (Room {room_id})")

                elif msg_type == "MOVE":
                    info = self.udp_clients.get(addr)
                    if info:
                        player_id = info["player_id"]
                        room_id   = info["room_id"]
                        x, y = message.get("x"), message.get("y")
                        with self.lock:
                            if room_id in self.rooms and player_id in self.rooms[room_id]["players"]:
                                self.rooms[room_id]["players"][player_id]["x"] = x
                                self.rooms[room_id]["players"][player_id]["y"] = y
                        self.broadcast_room(
                            {"type": "PLAYER_MOVE", "player_id": player_id, "x": x, "y": y},
                            room_id=room_id, exclude_player=player_id
                        )
            except Exception:
                pass

    # ------------------------------------------------------------------ TCP --
    def handle_client(self, conn, addr):
        # Send room player counts first so client can show them in lobby
        with self.lock:
            room_counts = {str(k): len(v["players"]) for k, v in self.rooms.items()}
        self.send_to_client(conn, {"type": "ROOM_INFO", "rooms": room_counts})

        # Wait for room selection from client
        try:
            buf = ""
            while "\n" not in buf:
                chunk = conn.recv(1024).decode('utf-8')
                if not chunk:
                    conn.close()
                    return
                buf += chunk
            # skip the ROOM_INFO echo if client sends it back (shouldn't happen)
            for line in buf.split("\n"):
                line = line.strip()
                if line:
                    msg = json.loads(line)
                    if "room_id" in msg:
                        room_id = int(msg["room_id"]) if msg["room_id"] in (1, 2, 3) else 1
                        break
            else:
                room_id = 1
        except Exception:
            conn.close()
            return

        with self.lock:
            self.client_counter += 1
            player_id   = f"P{self.client_counter}"
            player_name = f"Player{self.client_counter}"
            start_x = 100 + (self.client_counter - 1) * 50
            self.clients[conn] = {"id": player_id, "room": room_id, "name": player_name}
            self.rooms[room_id]["players"][player_id] = {"x": start_x, "y": 500, "name": player_name}

        print(f"  + {player_id} ({player_name}) joined Room {room_id} from {addr}")

        self.send_to_client(conn, {
            "type": "INIT",
            "player_id": player_id,
            "room_id": room_id,
            "game_state": {"players": self.rooms[room_id]["players"]}
        })
        self.broadcast_room(
            {"type": "PLAYER_JOIN", "player_id": player_id,
             "player_data": self.rooms[room_id]["players"][player_id]},
            room_id=room_id, exclude_conn=conn
        )

        buf = ""
        try:
            while self.running:
                data = conn.recv(4096)
                if not data:
                    break
                buf += data.decode('utf-8')
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    if line.strip():
                        try:
                            self.process_message(conn, json.loads(line))
                        except Exception:
                            pass
        except Exception:
            pass
        finally:
            self.disconnect_client(conn)

    def process_message(self, conn, message):
        client = self.clients.get(conn)
        if not client:
            return
        player_id = client["id"]
        room_id   = client["room"]
        msg_type  = message.get("type")

        if msg_type == "MOVE":
            x, y = message.get("x"), message.get("y")
            with self.lock:
                if player_id in self.rooms[room_id]["players"]:
                    self.rooms[room_id]["players"][player_id]["x"] = x
                    self.rooms[room_id]["players"][player_id]["y"] = y
            self.broadcast_room(
                {"type": "PLAYER_MOVE", "player_id": player_id, "x": x, "y": y},
                room_id=room_id, exclude_conn=conn
            )

        elif msg_type == "CHAT":
            text = message.get("text", "")
            name = client["name"]
            print(f"  [Room {room_id}] {name}: {text}")
            self.broadcast_room(
                {"type": "CHAT", "player_id": player_id, "name": name, "text": text},
                room_id=room_id
            )

        elif msg_type == "GEM":
            gem_id = message.get("gem_id")
            with self.lock:
                if gem_id not in self.rooms[room_id]["gems"]:
                    self.rooms[room_id]["gems"].append(gem_id)
                    should_broadcast = True
                else:
                    should_broadcast = False
            if should_broadcast:
                # Exclude sender — they already updated locally (optimistic)
                self.broadcast_room(
                    {"type": "GEM_COLLECTED", "player_id": player_id, "gem_id": gem_id},
                    room_id=room_id, exclude_conn=conn
                )

        elif msg_type == "ENEMY_STOMPED":
            enemy_idx = message.get("enemy_idx")
            self.broadcast_room(
                {"type": "ENEMY_STOMPED", "enemy_idx": enemy_idx},
                room_id=room_id, exclude_conn=conn
            )

        elif msg_type == "NEXT_LEVEL":
            level = message.get("level", 1)
            with self.lock:
                self.rooms[room_id]["gems"] = []   # reset for new level
            print(f"  [Room {room_id}] {player_id} → NEXT_LEVEL {level}")
            self.broadcast_room({"type": "NEXT_LEVEL", "level": level}, room_id=room_id)

        elif msg_type == "PING":
            # Echo timestamp back immediately
            self.send_to_client(conn, {"type": "PONG", "timestamp": message.get("timestamp")})

    # ------------------------------------------------------------ helpers ----
    def send_to_client(self, conn, data):
        try:
            conn.send((json.dumps(data) + "\n").encode('utf-8'))
        except Exception:
            pass

    def broadcast_room(self, data, room_id, exclude_conn=None, exclude_player=None):
        payload = (json.dumps(data) + "\n").encode('utf-8')
        with self.lock:
            targets = list(self.clients.items())
        for conn, client in targets:
            if client["room"] != room_id:
                continue
            if conn == exclude_conn:
                continue
            if exclude_player and client["id"] == exclude_player:
                continue
            try:
                conn.send(payload)
            except Exception:
                pass

    def disconnect_client(self, conn):
        with self.lock:
            if conn not in self.clients:
                return
            client    = self.clients.pop(conn)
            player_id = client["id"]
            room_id   = client["room"]
            self.rooms[room_id]["players"].pop(player_id, None)

        print(f"  - {player_id} left Room {room_id}")
        self.broadcast_room({"type": "PLAYER_LEAVE", "player_id": player_id}, room_id=room_id)
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    server = GameServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nServer shut down.")
