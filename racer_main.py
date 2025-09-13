# racer_main.py
import pygame, socket, threading, json, time
from pathlib import Path

# --- 基本設定 ---
WIDTH, HEIGHT = 1200, 700
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Racer 2D Prototype")
clock = pygame.time.Clock()
FONT = pygame.font.SysFont("DejaVuSans", 18)

# --- アセット ---
ASSETS = Path("./assets")
car_img = pygame.Surface((80,40))
car_img.fill((200,50,50))
other_img = pygame.Surface((80,40))
other_img.fill((50,50,200))
track_img = pygame.Surface((WIDTH, HEIGHT))
track_img.fill((50,50,50))

# --- プレイヤー ---
player = {"x":200.0,"y":200.0,"angle":0.0,"speed":0.0,"name":"Player"}
others = {}  # 他プレイヤー状態

# --- ネットワーク ---
SERVER_HOST = "サーバーのIPかドメイン"
SERVER_PORT = 5000
sock = None
connected = False

def network_listen():
    global others
    while connected:
        try:
            data = sock.recv(4096)
            if not data:
                break
            msg = json.loads(data.decode())
            cmd = msg.get("cmd")
            if cmd == "state":
                others[msg["name"]] = msg["data"]
            elif cmd == "chat":
                print(f"{msg['name']}: {msg['text']}")
        except:
            pass

def connect_to_server(name, room):
    global sock, connected
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER_HOST, SERVER_PORT))
    connected = True
    # 登録
    sock.sendall(json.dumps({"cmd":"register","name":name,"room":room}).encode())
    threading.Thread(target=network_listen, daemon=True).start()

def send_state():
    if connected:
        try:
            sock.sendall(json.dumps({"cmd":"state","data":player}).encode())
        except:
            pass

# --- AI（簡易） ---
class AIPlayer:
    def __init__(self,name,x,y,behavior="normal"):
        self.name = name
        self.x, self.y = x,y
        self.behavior = behavior
    def update(self,dt):
        if self.behavior=="aggressive":
            self.x += 180*dt
        elif self.behavior=="cautious":
            self.x += 80*dt
        else:
            self.x += 120*dt

ai_players = [AIPlayer("AI1",300,300,"aggressive"),
              AIPlayer("AI2",500,400,"cautious")]

# --- ゴースト ---
ghost = []
def save_ghost():
    Path("ghosts").mkdir(exist_ok=True)
    import json
    json.dump(ghost, open(f"ghosts/{player['name']}.json","w"), indent=2)

# --- メインループ ---
running = True
state = "menu"  # menu, play, lobby

while running:
    dt = clock.tick(60)/1000
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    if state=="play":
        if keys[pygame.K_w]:
            player["y"] -= 180*dt
        if keys[pygame.K_s]:
            player["y"] += 120*dt
        if keys[pygame.K_a]:
            player["x"] -= 160*dt
        if keys[pygame.K_d]:
            player["x"] += 160*dt
        ghost.append({"x":player["x"],"y":player["y"],"t":time.time()})
        send_state()
        for ai in ai_players:
            ai.update(dt)

    # --- 描画 ---
    screen.blit(track_img,(0,0))
    # 他プレイヤー
    for k,v in others.items():
        pygame.draw.rect(screen,(50,50,200),(v["x"],v["y"],80,40))
        screen.blit(FONT.render(k,True,(255,255,255)),(v["x"],v["y"]-18))
    # AI
    for ai in ai_players:
        pygame.draw.rect(screen,(50,180,50),(ai.x,ai.y,80,40))
        screen.blit(FONT.render(ai.name,True,(255,255,255)),(ai.x,ai.y-18))
    # 自分
    screen.blit(car_img,(player["x"],player["y"]))
    screen.blit(FONT.render(player["name"],True,(255,255,255)),(player["x"],player["y"]-18))
    pygame.display.flip()

# 終了時
if connected:
    sock.sendall(json.dumps({"cmd":"leave"}).encode())
pygame.quit()
