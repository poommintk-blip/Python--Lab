"""
University Bus Real-Time Tracking System — BUS DRIVER CLIENT (V2)
=============================================================
ดึงข้อมูลเส้นทางและป้ายจอดจาก Server โดยตรงเพื่อจำลองการวิ่ง
"""

import socket
import json
import sys
import time
import threading
import random
from datetime import datetime

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 9999

# ─── ANSI Colors ───────────────────────────────────────────────────────────────
class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    RED    = "\033[91m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    WHITE  = "\033[97m"
    GRAY   = "\033[90m"

def clr(text, *codes):
    return "".join(codes) + str(text) + C.RESET

# ─── TCP Client ─────────────────────────────────────────────────────────────────
class DriverClient:
    def __init__(self):
        self.sock = None
        self._lock = threading.Lock()

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(10)
        self.sock.connect((SERVER_HOST, SERVER_PORT))

    def send(self, data: dict) -> dict:
        """ส่งคำสั่ง JSON และรอรับผลลัพธ์แบบทีละบรรทัด"""
        with self._lock:
            try:
                msg = json.dumps(data, ensure_ascii=False) + "\n"
                self.sock.sendall(msg.encode("utf-8"))
                response = b""
                while not response.endswith(b"\n"):
                    chunk = self.sock.recv(4096)
                    if not chunk: break
                    response += chunk
                return json.loads(response.strip().decode("utf-8"))
            except Exception as e:
                return {"status": "error", "message": str(e)}

    def close(self):
        if self.sock: self.sock.close()

# ─── GPS Auto-sender ────────────────────────────────────────────────────────────
class GPSSender:
    def __init__(self, client: DriverClient, bus_id: str, stops: list):
        self.client = client
        self.bus_id = bus_id
        self.stops = stops  # รับรายชื่อป้ายมาจาก Server
        self.idx = 0
        self.running = False
        # พิกัดฐาน (กลาง มทส.)
        self.base_lat = 14.8800
        self.base_lng = 102.0160

    def send_loop(self):
        self.running = True
        print(clr(f"\n  📡 [{self.bus_id}] เริ่มส่ง GPS อัตโนมัติ...", C.GREEN))
        
        while self.running:
            current_stop = self.stops[self.idx % len(self.stops)]
            
            # จำลองพิกัด GPS แบบสุ่มขยับเล็กน้อยรอบๆ จุดฐาน
            lat = self.base_lat + random.uniform(-0.015, 0.015)
            lng = self.base_lng + random.uniform(-0.015, 0.015)
            speed = random.uniform(25, 55)

            payload = {
                "action": "UPDATE_LOCATION",
                "bus_id": self.bus_id,
                "latitude": round(lat, 6),
                "longitude": round(lng, 6),
                "speed": round(speed, 1),
                "current_stop": current_stop
            }

            res = self.client.send(payload)
            ts = datetime.now().strftime("%H:%M:%S")
            
            if res.get("status") == "ok":
                print(f"  ✅ [{ts}] จุดจอด: {clr(current_stop, C.YELLOW)} | ความเร็ว: {speed:.1f} km/h")
            else:
                print(clr(f"  ❌ [{ts}] อัพเดตล้มเหลว: {res.get('message')}", C.RED))

            # เลื่อนไปยังป้ายถัดไปในรอบหน้า
            self.idx = (self.idx + 1) % len(self.stops)
            
            # สุ่มเวลารอระหว่างป้าย 5-10 วินาที
            time.sleep(random.uniform(5, 50))
    
    def stop(self):
        self.running = False

# ─── Main Logic ────────────────────────────────────────────────────────────────
def main():
    print(clr("\n  🚌 University Bus Tracker — Driver Client V2", C.BOLD, C.WHITE))
    print(clr("  (Dynamic Route Synchronization Enabled)", C.GRAY))
    
    client = DriverClient()
    try:
        client.connect()
        print(clr("  ✅ เชื่อมต่อ Server สำเร็จ", C.GREEN))
    except Exception as e:
        print(clr(f"  ❌ ไม่สามารถเชื่อมต่อ Server: {e}", C.RED))
        return

    # 1. ดึงข้อมูลเส้นทางทั้งหมดจาก Server (R2 Sync)
    print(clr("  🔄 กำลังขอข้อมูลเส้นทางจาก Server...", C.GRAY))
    routes_res = client.send({"action": "GET_ROUTES"})
    
    if routes_res.get("status") != "ok":
        print(clr("  ❌ ดึงข้อมูลเส้นทางล้มเหลว!", C.RED))
        client.close()
        return

    routes_dict = routes_res.get("routes", {})
    available_routes = list(routes_dict.keys())

    # แสดงสายที่มีให้เลือก
    print(f"  สายรถที่เปิดบริการ: {clr(', '.join(available_routes), C.CYAN)}")
    
    route_choice = input(clr("  กรุณาเลือกสายที่ท่านขับ: ", C.BOLD)).strip().upper()
    if route_choice not in available_routes:
        print(clr(f"  ❌ ไม่พบสาย {route_choice} ในระบบ", C.RED))
        client.close()
        return

    bus_id = f"BUS-{route_choice}"
    stops = routes_dict[route_choice]["stops"]
    
    print(clr(f"  🗺️  เส้นทาง {route_choice}: {' ➔ '.join(stops)}", C.GRAY))

    # 2. เริ่มส่ง GPS
    gps_service = GPSSender(client, bus_id, stops)
    t_gps = threading.Thread(target=gps_service.send_loop, daemon=True)
    t_gps.start()

    # 3. เมนูควบคุม (Menu Loop)
    try:
        while True:
            print(clr(f"\n  [ ระบบคนขับ: {bus_id} ]", C.CYAN, C.BOLD))
            print("  1. ดูข้อมูลสถานะปัจจุบัน (จาก Server)")
            print("  0. ปิดระบบและออกจากโปรแกรม")
            
            choice = input(clr("  เลือกเมนู: ", C.WHITE)).strip()
            
            if choice == "1":
                status = client.send({"action": "GET_BUS", "bus_id": bus_id})
                if status.get("status") == "ok":
                    b = status["bus"]
                    print(clr(f"  📊 สถานะ: {b['status']} | ป้าย: {b['current_stop']} | ผู้โดยสาร: {b['passengers']}", C.YELLOW))
            elif choice == "0":
                break
    except KeyboardInterrupt:
        pass
    finally:
        gps_service.stop()
        client.close()
        print(clr("\n  👋 ออกจากระบบเรียบร้อยแล้ว", C.YELLOW))

if __name__ == "__main__":
    main()