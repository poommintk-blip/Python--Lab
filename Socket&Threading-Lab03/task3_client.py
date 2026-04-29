import socket
import threading

HOST = '127.0.0.1'
PORT = 9002

def receive_messages(s):
    """ฟังก์ชันสำหรับรอรับข้อความจาก Server ตลอดเวลา"""
    while True:
        try:
            data = s.recv(1024)
            if not data:
                break
            print(data.decode())
        except:
            break

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    
    # ส่ง Nickname เป็นอย่างแรกตาม R1
    nickname = input("Enter nickname: ")
    s.sendall(nickname.encode())

    # สร้าง Thread สำหรับรับข้อมูลเพื่อไม่ให้ block การพิมพ์ input
    threading.Thread(target=receive_messages, args=(s,), daemon=True).start()

    # Loop สำหรับส่งข้อความ
    while True:
        try:
            msg = input()
            if msg.lower() == '/quit':
                break
            s.sendall(msg.encode())
        except EOFError:
            break