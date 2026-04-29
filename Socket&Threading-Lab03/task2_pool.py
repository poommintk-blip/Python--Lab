# task2_pool.py — Multi-client Echo Server
import socket
from concurrent.futures import ThreadPoolExecutor

HOST = '0.0.0.0'
PORT = 9001
MAX_WORKERS = 10

def handle_client(conn, addr):
    # TODO: print connected, loop recv/sendall, print disconnected
    conn, addr = conn, addr
    print(f"[SERVER] Connected: {addr}")
    try: 
        while True:
            data = conn.recv(1024)
            if not data:
                break
            
            # ส่งข้อมูลกลับ (Echo)
            conn.sendall(data)
    except ConnectionResetError:
        pass
    finally:
        conn.close()
        
# TODO: สร้าง server socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(5)

print(f"[SERVER] Listening on {HOST}:{PORT} (max {MAX_WORKERS} workers)")

# TODO: ใช้ ThreadPoolExecutor(max_workers=MAX_WORKERS)
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
    try:
        while True:
            # รับ connection ด้วย accept()
            conn, addr = server_socket.accept()
            pool.submit(handle_client, conn, addr)
    except KeyboardInterrupt:
        print("\n[SERVER] Stopping...")
    finally:
        server_socket.close()
# TODO: loop accept() และ pool.submit(handle_client, conn, addr)