# task3_chat.py - Threaded Chat Room Server
import socket
import threading
from concurrent.futures import ThreadPoolExecutor

HOST = '0.0.0.0'
PORT = 9002
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

    except ConnectionResetError:
        pass
    finally:
        # เมื่อ disconnect ให้ลบออกจาก dict และแจ้งทุกคน
        with lock:
            if conn in clients:
                nickname = clients[conn]
                del clients[conn]
        
        leave_msg = f"[{nickname} left]"
        print(leave_msg) # แสดงที่ Server Terminal
        broadcast(leave_msg)
        conn.close()

# Main Server Setup
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # ป้องกัน Address already in use
server.bind((HOST, PORT))
server.listen(10)
print(f"[SERVER] Chat Room running on {PORT}...")

with ThreadPoolExecutor(max_workers=10) as pool:
    while True:
        conn, addr = server.accept()
        pool.submit(handle, conn, addr) # รัน handle ใน thread ใหม่