import socket
import json
import time

def start_driver():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('127.0.0.1', 9999))
    
    bus_id = input("ระบุรหัสรถเมล์ (เช่น BUS-A1): ")
    
    while True:
        print(f"\n--- เมนูคนขับ ({bus_id}) ---")
        print("1. อัปเดตตำแหน่งปกติ")
        print("2. แจ้งเตือนรถกำลังจะออก!")
        print("0. ออกจากระบบ")
        
        choice = input("เลือกเมนู: ")
        
        if choice == "1":
            loc = input("ป้อนจุดจอดปัจจุบัน: ")
            payload = {"action": "DRIVER_UPDATE", "bus_id": bus_id, "current_stop": loc, "send_alert": False}
        elif choice == "2":
            loc = input("ยืนยันจุดจอดที่กำลังจะออก: ")
            payload = {"action": "DRIVER_UPDATE", "bus_id": bus_id, "current_stop": loc, "send_alert": True}
        elif choice == "0": break
        else: continue

        client.sendall(json.dumps(payload).encode('utf-8'))
        res = client.recv(1024).decode('utf-8')
        print(f"Server ตอบกลับ: {res}")

if __name__ == "__main__":
    start_driver()