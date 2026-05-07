# task1_echo.py — TCP Echo Server
import socket

HOST = '0.0.0.0'
PORT = 9000

def run_server():
    # TODO: สร้าง socket, bind, listen Slide: P.13
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # เพิ่ม option เพื่อให้สามารถ reuse address ได้
        s.bind((HOST, PORT))
        s.listen()
        
        print(f"[SERVER] Listening on {HOST}:{PORT}")

    # TODO: รับ connection ด้วย accept()
        conn, addr = s.accept()
        with conn:
            print(f"[SERVER] Connected: {addr}")
            
    # TODO: loop recv() และ sendall() จนกว่า client disconnect
            while True:
                data = conn.recv(1024)
                if not data:
                    break
            
                conn.sendall(data)
                
            # แสดงผลเมื่อ Client ตัดการเชื่อมต่อ
            print("[SERVER] Disconnected")

def run_client():
    C_HOST = '127.0.0.1'
    C_PORT = 9000
    MESSAGES = ['Hello Server!', 'How are you?', 'Goodbye!']

    # TODO: สร้าง socket และ connect
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((C_HOST, C_PORT))
        
        # แสดงผลหัวข้อตามรูป
        print("=== TCP Echo Test ===")
        
    # TODO: loop ส่ง message แต่ละอัน และ print response
        for msg in MESSAGES:
            # ส่งข้อมูล
            s.sendall(msg.encode())
            print(f"Sent:      {msg}")
            
            # รับข้อมูลกลับ
            data = s.recv(1024)
            print(f"Received:  {data.decode()}")

if __name__ == "__main__":
    mode = input("Run with Server or Client (S/C)? ").strip().lower()
    if mode == 's':
        print("Starting Server...")
        run_server() # เรียกใช้ฟังก์ชันที่สร้างไว้
    elif mode == 'c':
        print("Starting Client...")
        run_client() # เรียกใช้ฟังก์ชันที่สร้างไว้
    else:
        print("Please choose 'S' for Server or 'C' for Client.")