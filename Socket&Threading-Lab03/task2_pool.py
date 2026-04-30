import socket, time
from concurrent.futures import ThreadPoolExecutor

HOST = '0.0.0.0'
PORT = 9001
MAX_WORKERS = 10

def handle_client(conn, addr):
    # TODO: print connected, loop recv/sendall, print disconnected
    print(f"[SERVER] Connected: {addr}")
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            conn.sendall(data)
    finally:
        conn.close() # ปิด connection เมื่อเสร็จสิ้น
        print(f"[SERVER] Disconnected: {addr}")

def run_server():
    # TODO: สร้าง server socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"[SERVER] Listening on {HOST}:{PORT} (max {MAX_WORKERS} workers)")

        # TODO: ใช้ ThreadPoolExecutor(max_workers=MAX_WORKERS)
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # TODO: loop accept() และ pool.submit(handle_client, conn, addr)
            while True:
                conn, addr = s.accept()
                executor.submit(handle_client, conn, addr)

def run_client():
    # Client code
    C_HOST, C_PORT = '127.0.0.1', 9001
    with socket.socket() as s:
        s.connect((C_HOST, C_PORT))
        for i in range(3):
            msg = f'Message {i+1} from client'
            s.sendall(msg.encode())
            print('Echo:', s.recv(1024).decode())
            time.sleep(1)

if __name__ == "__main__":
    mode = input("Run with Server or Client (S/C)? ").strip().lower()
    if mode == 's':
        print("Starting Server...")
        run_server() # เรียกฟังก์ชัน Server
    elif mode == 'c':
        print("Starting Client...")
        run_client() # เรียกฟังก์ชัน Client
    else:
        print("Please choose 'S' for Server or 'C' for Client.")
