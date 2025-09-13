# racer_main.py (拡張版)
import pygame, socket, threading, json, time
from pathlib import Path

WIDTH, HEIGHT = 1200, 700
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Racer 2D Extended")
clock = pygame.time.Clock()
FONT = pygame.font.SysFont("DejaVuSans", 18)

# --- アセット ---
ASSETS = Path("./assets")
car_img = pygame.Surface((80,40)); car_img.fill((200,50,50))
other_img = pygame.Surface((80,40)); other_img.fill((50,50,200))
track_img = pygame.Surface((WIDTH, HEIGHT)); track_img.fill((50,50,50))

# --- プレイヤー ---
player = {"x":200.0,"y":200.0,"angle":0.0,"speed":0.0,"gear":1,"handbrake":False,"name":"Player"}
others = {}  # 他プレイヤー状態

# --- チャットUI ---
chat_lines = []
chat_input = ""
chat_active = False

# --- ネットワーク ---
SERVER_HOST = "サーバーIP"
SERVER_PORT = 5000
sock = None
connected = False

def network_listen():
    global others, chat_lines
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
                chat_lines.append(f"{msg['name']}: {msg['text']}")
                if len(chat_lines)>6:
                    chat_lines.pop(0)
        except:
            pass

def connect_to_server(name, room):
    global sock, connected
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER_HOST, SERVER_PORT))
    connected = True
    sock.sendall(json.dumps({"cmd":"register","name":name,"room":room}).encode())
    threading.Thread(target=network_listen, daemon=True).start()

def send_state():
    if connected:
        try:
            sock.sendall(json.dumps({"cmd":"state","data":player}).encode())
        except:
            pass

def send_chat(text):
    if connected:
        sock.sendall(json.dumps({"cmd":"chat","text":text,"name":player["name"]}).encode())

# --- AI ---
class AIPlayer:
    def __init__(self,name,x,y,behavior="normal"):
        self.name = name; self.x,self.y=x,y; self.behavior=behavior
    def update(self,dt):
        self.x += {"aggressive":180,"normal":120,"cautious":80}[self.behavior]*dt

ai_players = [AIPlayer("AI1",300,300,"aggressive"), AIPlayer("AI2",500,400,"cautious")]

# --- ゴースト ---
ghost = []
def save_ghost():
    Path("ghosts").mkdir(exist_ok=True)
    import json
    json.dump(ghost, open(f"ghosts/{player['name']}.json","w"), indent=2)

# --- メインループ ---
running = True
state = "play"
while running:
    dt = clock.tick(60)/1000
    for ev in pygame.event.get():
        if ev.type==pygame.QUIT:
            running=False
        elif ev.type==pygame.KEYDOWN:
            if chat_active:
                if ev.key==pygame.K_RETURN:
                    send_chat(chat_input)
                    chat_input=""
                    chat_active=False
                elif ev.key==pygame.K_BACKSPACE:
                    chat_input = chat_input[:-1]
                else:
                    chat_input += ev.unicode
            else:
                if ev.key==pygame.K_RETURN:
                    chat_active=True
                if ev.key==pygame.K_g:
                    save_ghost()

    # --- プレイヤー操作 ---
    keys = pygame.key.get_pressed()
    # ギア・速度
    if keys[pygame.K_w]:
        player["speed"] += player["gear"]*50*dt
    if keys[pygame.K_s]:
        player["speed"] -= player["gear"]*50*dt
    # ドリフト
    drift = keys[pygame.K_LSHIFT]
    if keys[pygame.K_a]:
        player["x"] -= (160*(0.5 if drift else 1))*dt
    if keys[pygame.K_d]:
        player["x"] += (160*(0.5 if drift else 1))*dt
    player["y"] += player["speed"]*dt
    ghost.append({"x":player["x"],"y":player["y"],"t":time.time()})
    send_state()
    for ai in ai_players:
        ai.update(dt)

    # --- 描画 ---
    screen.blit(track_img,(0,0))
    for k,v in others.items():
        pygame.draw.rect(screen,(50,50,200),(v["x"],v["y"],80,40))
        screen.blit(FONT.render(k,True,(255,255,255)),(v["x"],v["y"]-18))
    for ai in ai_players:
        pygame.draw.rect(screen,(50,180,50),(ai.x,ai.y,80,40))
        screen.blit(FONT.render(ai.name,True,(255,255,255)),(ai.x,ai.y-18))
    screen.blit(car_img,(player["x"],player["y"]))
    screen.blit(FONT.render(player["name"],True,(255,255,255)),(player["x"],player["y"]-18))

    # --- チャット描画 ---
    y0 = HEIGHT - 140
    for i,line in enumerate(chat_lines):
        screen.blit(FONT.render(line,True,(255,255,255)),(20,y0+i*20))
    if chat_active:
        screen.blit(FONT.render("> "+chat_input,True,(255,255,0)),(20,HEIGHT-20))

    pygame.display.flip()

# --- 終了 ---
if connected:
    sock.sendall(json.dumps({"cmd":"leave"}).encode())
pygame.quit()
