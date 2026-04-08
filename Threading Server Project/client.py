import socket
import json

HOST = '127.0.0.1'
PORT = 9999

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    client.connect((HOST, PORT))
    print("--- เชื่อมต่อ Server สำเร็จ ---")
    print("ส่งคำสั่งแบบ JSON เช่น: {\"action\":\"PING\"} หรือ {\"action\":\"GET_ROUTES\"}")

    while True:
        msg = input("Enter message: ")
        if not msg:
            continue
            
        # ✅ แก้ไข: เพิ่ม \n เพื่อให้ Server รู้ว่าจบคำสั่งหนึ่งบรรทัด
        full_msg = msg + "\n"  # เติมตัวขึ้นบรรทัดใหม่
        client.send(full_msg.encode('utf-8'))

        # รอรับข้อมูลตอบกลับ
        response = client.recv(4096)
        if not response:
            print("Server ปิดการเชื่อมต่อ")
            break
            
        print("Server:", response.decode('utf-8').strip())

except ConnectionRefusedError:
    print("❌ Error: ไม่สามารถเชื่อมต่อได้ (เช็กว่ารัน Server หรือยัง?)")
except KeyboardInterrupt:
    print("\nปิดการเชื่อมต่อ...")
finally:
    client.close()