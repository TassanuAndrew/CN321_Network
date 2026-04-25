"""
Network Client — TCP (reliable) + UDP (fast position)
"""
import socket
import threading
import json
import time


class NetworkClient:
    def __init__(self):
        self.tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.host = 'localhost'
        self.port = 5555
        self.connected = False
        self.player_id = None
        self.room_id   = None
        self.buffer    = ""
        self.ping_ms   = 0         # latest round-trip time in ms

        # Callbacks
        self.on_init         = None
        self.on_player_move  = None
        self.on_player_join  = None
        self.on_player_leave = None
        self.on_chat         = None
        self.on_gem_collected = None

    # ----------------------------------------------------------------- connect
    def connect(self, room_id=1):
        try:
            self.tcp.connect((self.host, self.port))
            # First message: room selection (server waits for this before INIT)
            self.tcp.send((json.dumps({"room_id": room_id}) + "\n").encode('utf-8'))
            self.connected = True
            threading.Thread(target=self._receive_tcp, daemon=True).start()
            threading.Thread(target=self._ping_loop,   daemon=True).start()
            print(f"Connected to {self.host}:{self.port}  |  Room {room_id}")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def _register_udp(self):
        """Tell server our UDP source port so it can map addr -> player_id."""
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

    def _process(self, msg):
        t = msg.get("type")
        if t == "INIT":
            self.player_id = msg.get("player_id")
            self.room_id   = msg.get("room_id", 1)
            self._register_udp()
            if self.on_init:
                self.on_init(msg)
        elif t == "PONG":
            sent = msg.get("timestamp", 0)
            self.ping_ms = int((time.time() - sent) * 1000)
        elif t == "PLAYER_MOVE"  and self.on_player_move:
            self.on_player_move(msg)
        elif t == "PLAYER_JOIN"  and self.on_player_join:
            self.on_player_join(msg)
        elif t == "PLAYER_LEAVE" and self.on_player_leave:
            self.on_player_leave(msg)
        elif t == "CHAT"         and self.on_chat:
            self.on_chat(msg)
        elif t == "GEM_COLLECTED" and self.on_gem_collected:
            self.on_gem_collected(msg)

    # ------------------------------------------------------------------- ping
    def _ping_loop(self):
        """Send a PING via TCP every second to measure RTT."""
        while self.connected:
            self._send_tcp({"type": "PING", "timestamp": time.time()})
            time.sleep(1)

    # ------------------------------------------------------------------- send
    def send_move(self, x, y):
        """Position goes over UDP — fast, drop-tolerant."""
        try:
            data = json.dumps({"type": "MOVE", "x": x, "y": y}).encode()
            self.udp.sendto(data, (self.host, self.port + 1))
        except Exception:
            pass

    def send_chat(self, text):
        self._send_tcp({"type": "CHAT", "text": text})

    def send_gem(self, gem_id):
        self._send_tcp({"type": "GEM", "gem_id": gem_id})

    def _send_tcp(self, data):
        if self.connected:
            try:
                self.tcp.send((json.dumps(data) + "\n").encode('utf-8'))
            except Exception:
                self.connected = False
