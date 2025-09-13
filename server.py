# server.py - Render向け部屋管理付きリレーサーバー
import socket, threading, json

HOST = "0.0.0.0"
PORT = 5000

rooms = {}  # 部屋名 -> {"admin_pw":..., "join_pw":..., "clients": []}
lock = threading.Lock()

def handle_client(conn, addr):
    player_name = None
    room_name = None
    try:
        while True:
            data = conn.recv(4096)
            if not data:
                break
            msg = json.loads(data.decode())
            cmd = msg.get("cmd")
            
            # 部屋一覧送信
            if cmd=="get_rooms":
                with lock:
                    room_list = [{"name":r,"join_pw":bool(rooms[r]["join_pw"])} for r in rooms]
                conn.send(json.dumps({"cmd":"room_list","rooms":room_list}).encode())
            
            # 部屋作成
            elif cmd=="create_room":
                rname = msg.get("room")
                admin_pw = msg.get("admin_pw")
                join_pw = msg.get("join_pw")
                with lock:
                    if rname not in rooms:
                        rooms[rname] = {"admin_pw":admin_pw,"join_pw":join_pw,"clients":[]}
                        conn.send(json.dumps({"cmd":"room_created","room":rname}).encode())
                    else:
                        conn.send(json.dumps({"cmd":"error","msg":"Room exists"}).encode())
            
            # 部屋入室
            elif cmd=="join_room":
                rname = msg.get("room")
                pname = msg.get("name")
                pw = msg.get("join_pw")
                with lock:
                    room = rooms.get(rname)
                    if not room:
                        conn.send(json.dumps({"cmd":"error","msg":"Room not found"}).encode())
                        continue
                    if room["join_pw"] and room["join_pw"] != pw:
                        conn.send(json.dumps({"cmd":"error","msg":"Wrong password"}).encode())
                        continue
                    room["clients"].append({"conn":conn,"name":pname})
                    player_name = pname
                    room_name = rname
                    conn.send(json.dumps({"cmd":"joined","room":rname}).encode())
            
            # 管理者認証
            elif cmd=="admin_auth":
                rname = msg.get("room")
                pw = msg.get("admin_pw")
                with lock:
                    room = rooms.get(rname)
                    if room and room["admin_pw"]==pw:
                        conn.send(json.dumps({"cmd":"admin_ok"}).encode())
                    else:
                        conn.send(json.dumps({"cmd":"admin_fail"}).encode())
            
            # ブロードキャスト
            elif cmd=="broadcast":
                rname = msg.get("room")
                data_to_send = json.dumps(msg)
                with lock:
                    room = rooms.get(rname)
                    if room:
                        for c in room["clients"]:
                            if c["conn"] != conn:
                                try:
                                    c["conn"].sendall(data_to_send.encode())
                                except:
                                    pass
    except Exception as e:
        print("クライアント処理中エラー:", e)
    finally:
        with lock:
            if room_name and player_name:
                room = rooms.get(room_name)
                if room:
                    room["clients"] = [c for c in room["clients"] if c["conn"]!=conn]
        conn.close()
        print(f"切断: {addr}")

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
    s.bind((HOST, PORT))
    s.listen()
    print(f"サーバー起動: {HOST}:{PORT}")
    try:
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client,args=(conn,addr),daemon=True).start()
    except KeyboardInterrupt:
        print("サーバー停止中…")
    finally:
        s.close()

if __name__=="__main__":
    main()
