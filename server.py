# server_create.py
import socket
import json

SERVER_HOST = "サーバーのIPかドメイン"  # Renderのサーバー
SERVER_PORT = 5000

def create_room():
    room_name = input("部屋名を入力: ")
    room_pass = input("部屋パスワードを入力: ")
    admin_pass = input("管理者パスワードを入力: ")

    # Renderサーバーに送信
    data = {
        "cmd": "create_room",
        "room_name": room_name,
        "room_pass": room_pass,
        "admin_pass": admin_pass
    }

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((SERVER_HOST, SERVER_PORT))
    s.sendall(json.dumps(data).encode())
    print("部屋作成リクエスト送信完了")
    s.close()

if __name__ == "__main__":
    create_room()
