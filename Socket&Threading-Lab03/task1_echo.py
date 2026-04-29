# task1_echo.py — TCP Echo Server
import socket

HOST = '0.0.0.0'
PORT = 9000

# task1_echo.py — TCP Echo Server
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen(1)
    
    print(f"[SERVER] Listening on {HOST}:{PORT}")

# TODO: รับ connection ด้วย accept()
    conn, addr = s.accept()
    with conn:
  
        print(f"[SERVER] Connected: {addr}")
        
# TODO: รับ connection ด้วย accept()
        while True:
            data = conn.recv(1024)
            if not data:
                break
        
            conn.sendall(data)
            
        # แสดงผลเมื่อ Client ตัดการเชื่อมต่อ
        print("[SERVER] Disconnected")