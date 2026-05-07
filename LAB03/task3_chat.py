# task3_chat.py - Threaded Chat Room Server
import socket
import threading
from concurrent.futures import ThreadPoolExecutor

HOST_ADDR = '0.0.0.0'
PORT_ADDR = 9002
clients = {}  # เก็บข้อมูล conn -> nickname
lock = threading.Lock() # ใช้ Lock ป้องกัน Race Condition

def broadcast(msg, sender=None):
    # TODO: ส่ง msg ไปยัง clients ทุกคน ยกเว้น sender
    # TODO: ใช้ lock เมื่ออ่าน clients dict
    """ส่งข้อความให้ทุกคนในห้องแชท ยกเว้นผู้ส่ง (ถ้ากำหนด)"""
    with lock: # ใช้ lock เมื่อเข้าถึง clients dictionary
        for conn in clients:
            if conn != sender:
                try:
                    conn.sendall(msg.encode())
                except:
                    pass

def handle(conn, addr):
    try:
        # R1: รับ nickname ก่อนเริ่มคุย
        nickname = conn.recv(1024).decode().strip()
        
        with lock:
            clients[conn] = nickname # เพิ่มลงใน dict
            
        # R3: แจ้งทุกคนเมื่อมีคนเข้าห้อง
        join_msg = f"[{nickname} joined]"
        print(join_msg) # แสดงที่ Server Terminal
        broadcast(join_msg)

        # R2: loop รับข้อความแล้ว broadcast
        while True:
            data = conn.recv(1024)
            if not data:
                break
            
            msg = data.decode().strip()
            # รูปแบบ nickname: ข้อความ
            broadcast_msg = f"{nickname}: {msg}"
            broadcast(broadcast_msg, sender=conn)

    except (ConnectionResetError, BrokenPipeError):
        pass
    finally:
        # เมื่อ disconnect ให้ลบออกจาก dict และแจ้งทุกคน
        nickname = "Anonymous"
        with lock:
            if conn in clients:
                nickname = clients[conn]
                del clients[conn]
        
        leave_msg = f"[{nickname} left]"
        print(leave_msg) # แสดงที่ Server Terminal
        broadcast(leave_msg)
        conn.close()

def run_server():
    # Main Server Setup
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # ป้องกัน Address already in use
    server.bind((HOST_ADDR, PORT_ADDR))
    server.listen(10)
    print(f"[SERVER] Chat Room running on {PORT_ADDR}...")

    with ThreadPoolExecutor(max_workers=10) as pool:
        while True:
            conn, addr = server.accept()
            pool.submit(handle, conn, addr) # รัน handle ใน thread ใหม่

def receive_messages(s):
    """ฟังก์ชันสำหรับรอรับข้อความจาก Server ตลอดเวลา"""
    while True:
        try:
            data = s.recv(1024)
            if not data:
                print("\n[INFO] Disconnected from server.")
                break
            # ใช้ \r เพื่อให้พิมพ์ทับเครื่องหมาย > ตอนที่มีข้อความเข้า
            print(f"\r{data.decode()}\n> ", end="") 
        except:
            break

def run_client():
    C_HOST = '127.0.0.1'
    C_PORT = 9002
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((C_HOST, C_PORT))
            
            # ส่ง Nickname เป็นอย่างแรกตาม R1
            nickname = input("Enter nickname: ")
            s.sendall(nickname.encode())

            # สร้าง Thread สำหรับรับข้อมูลเพื่อไม่ให้ block การพิมพ์ input
            threading.Thread(target=receive_messages, args=(s,), daemon=True).start()

            # Loop สำหรับส่งข้อความ
            print("Type messages below (or '/quit' to exit):")
            while True:
                msg = input("> ")
                if msg.lower() == '/quit':
                    break
                if msg.strip(): # ส่งเฉพาะเมื่อมีข้อความ
                    s.sendall(msg.encode())
        except ConnectionRefusedError:
            print("[ERROR] Could not connect to server. Is it running?")

if __name__ == "__main__":
    # ส่วนนี้จะทำงานเป็นอย่างแรกเพื่อถามโหมดการรัน
    mode = input("Run with Server or Client (S/C)? ").strip().lower()
    if mode == 's':
        print("Starting Server...")
        run_server() 
    elif mode == 'c':
        print("Starting Client...")
        run_client()
    else:
        print("Please choose 'S' for Server or 'C' for Client.")