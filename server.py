import socket
import threading
import json
import time
import numpy as np

# =========================
# プレイヤー管理
# =========================
class Player:
    def __init__(self, name, conn):
        self.name = name
        self.conn = conn
        self.pos = np.array([0.0,0.0])
        self.angle = 0.0
        self.room_id = None

# =========================
# 部屋管理
# =========================
class Room:
    def __init__(self, room_id, host: Player, room_pass=""):
        self.room_id = room_id
        self.host = host
        self.room_pass = room_pass
        self.players = [host]

    def remove_player(self, player):
        if player in self.players:
            self.players.remove(player)
        if player == self.host:
            return True  # 部屋削除フラグ
        return False

# =========================
# サーバー本体
# =========================
class Server:
    def __init__(self, host="0.0.0.0", port=5000):
        self.rooms = {}      # room_id: Room
        self.players = {}    # conn: Player
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((host, port))
        self.sock.listen(100)
        print(f"Server listening on {host}:{port}")

    def start(self):
        while True:
            conn, addr = self.sock.accept()
            player = Player("Unknown", conn)
            self.players[conn] = player
            threading.Thread(target=self.handle_client, args=(player,)).start()

    def handle_client(self, player):
        conn = player.conn
        while True:
            try:
                data = json.loads(conn.recv(4096).decode())
            except:
                self.disconnect_player(player)
                break

            cmd = data.get("cmd")
            # ===== 部屋作成 =====
            if cmd == "create_room":
                room_id = str(time.time())
                room = Room(room_id, player, data.get("room_pass",""))
                self.rooms[room_id] = room
                player.room_id = room_id
                conn.send(json.dumps({"status":"ok","room_id":room_id}).encode())

            # ===== 部屋参加 =====
            elif cmd == "join_room":
                room_id = data.get("room_id")
                room = self.rooms.get(room_id)
                if room:
                    room.players.append(player)
                    player.room_id = room_id
                    conn.send(json.dumps({"status":"ok"}).encode())
                else:
                    conn.send(json.dumps({"status":"fail","reason":"no room"}).encode())

            # ===== レース状態更新（TCPリレー） =====
            elif cmd == "update":
                room = self.rooms.get(player.room_id)
                if room:
                    msg = json.dumps({
                        "players": {
                            p.name: {"pos":p.pos.tolist(),"angle":p.angle} for p in room.players
                        }
                    })
                    for p in room.players:
                        if p != player:
                            p.conn.send(msg.encode())

            # ===== チャット =====
            elif cmd == "chat":
                room = self.rooms.get(player.room_id)
                if room:
                    msg = f"{data.get('name')}: {data.get('msg')}"
                    for p in room.players:
                        p.conn.send(json.dumps({"chat":msg}).encode())

    # ===== 切断処理 =====
    def disconnect_player(self, player):
        room = self.rooms.get(player.room_id)
        if room:
            delete_room = room.remove_player(player)
            if delete_room:
                del self.rooms[room.room_id]
        if player.conn in self.players:
            del self.players[player.conn]
        player.conn.close()
        print(f"Player {player.name} disconnected")

# =========================
# メイン処理
# =========================
if __name__ == "__main__":
    server = Server(host="0.0.0.0", port=5000)
    server.start()
