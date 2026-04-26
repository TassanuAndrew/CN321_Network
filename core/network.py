"""
Network Client — TCP (reliable) + UDP (fast position)
Features: auto-reconnect, room info
"""
import socket
import threading
import json
import time


class NetworkClient:
    def __init__(self):
        self.tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.host = '192.168.0.11'
        self.port = 5555
        self.connected   = False
        self.player_id   = None
        self.room_id     = None
        self.room_counts = {1: 0, 2: 0, 3: 0}   # filled by get_room_info()
        self.buffer      = ""
        self.ping_ms     = 0.0

        # Reconnect state
        self.reconnecting       = False
        self.reconnect_attempts = 0

        # Callbacks
        self.on_init          = None
        self.on_player_move   = None
        self.on_player_join   = None
        self.on_player_leave  = None
        self.on_chat          = None
        self.on_gem_collected  = None
        self.on_next_level     = None
        self.on_enemy_stomped  = None
        self.on_reconnected    = None

    # --------------------------------------------------------- step 1: info
    def get_room_info(self):
        """Open a temporary connection just to read ROOM_INFO, then close it.
        Can be called multiple times (e.g. lobby refresh). Returns room_counts dict."""
        try:
            tmp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tmp.settimeout(2.0)
            tmp.connect((self.host, self.port))
            buf = ""
            while "\n" not in buf:
                chunk = tmp.recv(1024).decode('utf-8')
                if not chunk:
                    break
                buf += chunk
            tmp.close()   # close without sending room_id → server discards this connection
            msg = json.loads(buf.split("\n")[0])
            if msg.get("type") == "ROOM_INFO":
                self.room_counts = {int(k): v for k, v in msg.get("rooms", {}).items()}
        except Exception:
            self.room_counts = {1: 0, 2: 0, 3: 0}
        return self.room_counts

    # --------------------------------------------------------- step 2: join
    def join_room(self, room_id):
        """Create a fresh connection, read ROOM_INFO, then send room selection."""
        try:
            self.tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp.connect((self.host, self.port))
            # Server sends ROOM_INFO first — read and discard
            self.tcp.settimeout(2.0)
            buf = ""
            while "\n" not in buf:
                chunk = self.tcp.recv(1024).decode('utf-8')
                if not chunk:
                    break
                buf += chunk
            self.tcp.settimeout(None)
            # Send room selection
            self.room_id = room_id
            self.tcp.send((json.dumps({"room_id": room_id}) + "\n").encode('utf-8'))
            self.connected = True
            threading.Thread(target=self._receive_tcp, daemon=True).start()
            threading.Thread(target=self._ping_loop,   daemon=True).start()
            print(f"Joined Room {room_id}")
            return True
        except Exception as e:
            print(f"join_room failed: {e}")
            return False

    # --------------------------------------------------- register UDP addr
    def _register_udp(self):
        try:
            data = json.dumps({"type": "UDP_REGISTER", "player_id": self.player_id}).encode()
            self.udp.sendto(data, (self.host, self.port + 1))
        except Exception:
            pass

    # --------------------------------------------------------------- receive
    def _receive_tcp(self):
        while self.connected:
            try:
                data = self.tcp.recv(4096).decode('utf-8')
                if not data:
                    self.connected = False
                    break
                self.buffer += data
                while '\n' in self.buffer:
                    line, self.buffer = self.buffer.split('\n', 1)
                    if line.strip():
                        try:
                            self._process(json.loads(line))
                        except Exception:
                            pass
            except Exception:
                self.connected = False
                break

        # Connection dropped — start auto-reconnect
        if not self.reconnecting:
            self.reconnecting = True
            self.reconnect_attempts = 0
            threading.Thread(target=self._reconnect_loop, daemon=True).start()

    def _reconnect_loop(self):
        """Try to reconnect every 3 seconds until success."""
        while not self.connected:
            self.reconnect_attempts += 1
            time.sleep(3)
            try:
                # New sockets
                self.tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

                self.tcp.connect((self.host, self.port))

                # Receive ROOM_INFO that server sends first
                self.tcp.settimeout(3.0)
                buf = ""
                while "\n" not in buf:
                    chunk = self.tcp.recv(1024).decode('utf-8')
                    if not chunk:
                        raise Exception("No data")
                    buf += chunk
                self.tcp.settimeout(None)

                # Re-join same room
                self.tcp.send((json.dumps({"room_id": self.room_id}) + "\n").encode('utf-8'))
                self.connected   = True
                self.reconnecting = False
                self.buffer      = ""

                threading.Thread(target=self._receive_tcp, daemon=True).start()
                threading.Thread(target=self._ping_loop,   daemon=True).start()

                print(f"Reconnected to Room {self.room_id} (attempt {self.reconnect_attempts})")

                if self.on_reconnected:
                    self.on_reconnected()
            except Exception:
                pass   # try again

    def _process(self, msg):
        t = msg.get("type")
        if t == "INIT":
            self.player_id = msg.get("player_id")
            self.room_id   = msg.get("room_id", self.room_id)
            self._register_udp()
            if self.on_init:
                self.on_init(msg)
        elif t == "PONG":
            sent = msg.get("timestamp", 0)
            self.ping_ms = round((time.time() - sent) * 1000, 2)
        elif t == "PLAYER_MOVE"   and self.on_player_move:
            self.on_player_move(msg)
        elif t == "PLAYER_JOIN"   and self.on_player_join:
            self.on_player_join(msg)
        elif t == "PLAYER_LEAVE"  and self.on_player_leave:
            self.on_player_leave(msg)
        elif t == "CHAT"          and self.on_chat:
            self.on_chat(msg)
        elif t == "GEM_COLLECTED" and self.on_gem_collected:
            self.on_gem_collected(msg)
        elif t == "NEXT_LEVEL"    and self.on_next_level:
            self.on_next_level(msg)
        elif t == "ENEMY_STOMPED" and self.on_enemy_stomped:
            self.on_enemy_stomped(msg)

    # ---------------------------------------------------------------- ping
    def _ping_loop(self):
        while self.connected:
            self._send_tcp({"type": "PING", "timestamp": time.time()})
            time.sleep(1)

    # --------------------------------------------------------------- send
    def send_move(self, x, y):
        try:
            data = json.dumps({"type": "MOVE", "x": x, "y": y}).encode()
            self.udp.sendto(data, (self.host, self.port + 1))
        except Exception:
            pass

    def send_chat(self, text):
        self._send_tcp({"type": "CHAT", "text": text})

    def send_gem(self, gem_id):
        self._send_tcp({"type": "GEM", "gem_id": gem_id})

    def send_next_level(self, level):
        self._send_tcp({"type": "NEXT_LEVEL", "level": level})

    def send_enemy_stomp(self, enemy_idx):
        self._send_tcp({"type": "ENEMY_STOMPED", "enemy_idx": enemy_idx})

    def _send_tcp(self, data):
        if self.connected:
            try:
                self.tcp.send((json.dumps(data) + "\n").encode('utf-8'))
            except Exception:
                self.connected = False
