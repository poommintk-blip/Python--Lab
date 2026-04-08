"""
University Bus Real-Time Tracking System — BUS DRIVER CLIENT
=============================================================
พนักงานขับรถเชื่อมต่อ Server ผ่าน TCP Socket เพื่อ:
  - ส่ง GPS Location แบบ Real-time อัตโนมัติ
  - อัพเดตสถานะ (on_time / delayed / cancelled)
  - รายงานจุดจอดปัจจุบัน
"""

import socket
import json
import sys
import time
import threading
import random
import math
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
    GRAY   = "\033[90m"
    WHITE  = "\033[97m"

def clr(text, *codes):
    return "".join(codes) + str(text) + C.RESET


# ─── Route Simulation (GPS จำลอง) ───────────────────────────────────────────────
ROUTE_WAYPOINTS = {
    "A1": [
        (14.8800, 102.0160, "หอพัก A"),
        (14.8815, 102.0175, "ทางแยกกลาง"),
        (14.8830, 102.0190, "ลานจอดรถ"),
        (14.8845, 102.0205, "อาคารเรียนกลาง"),
    ],
    "A2": [
        (14.8760, 102.0130, "หอพัก B"),
        (14.8775, 102.0145, "สนามกีฬา"),
        (14.8790, 102.0160, "ลานกิจกรรม"),
        (14.8805, 102.0175, "คณะวิศวกรรมศาสตร์"),
    ],
    "B1": [
        (14.8850, 102.0100, "ประตูหลัก"),
        (14.8840, 102.0120, "ศูนย์บริการ"),
        (14.8830, 102.0140, "อาคารสำนักงาน"),
        (14.8820, 102.0160, "โรงอาหารกลาง"),
    ],
    "B2": [
        (14.8770, 102.0200, "สระว่ายน้ำ"),
        (14.8785, 102.0185, "อาคารกีฬา"),
        (14.8800, 102.0170, "ลานจอดรถใต้ดิน"),
        (14.8815, 102.0155, "ห้องสมุดกลาง"),
    ],
    "C1": [
        (14.8830, 102.0220, "คณะแพทย์"),
        (14.8815, 102.0205, "โรงพยาบาล"),
        (14.8800, 102.0190, "ตลาดในมหาวิทยาลัย"),
        (14.8785, 102.0175, "ประตูหน้า"),
    ],
}


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
        with self._lock:
            msg = json.dumps(data, ensure_ascii=False) + "\n"
            self.sock.sendall(msg.encode("utf-8"))
            response = b""
            while not response.endswith(b"\n"):
                chunk = self.sock.recv(4096)
                if not chunk:
                    raise ConnectionError("Server closed")
                response += chunk
            return json.loads(response.strip().decode("utf-8"))

    def close(self):
        if self.sock:
            self.sock.close()


# ─── GPS Auto-sender ────────────────────────────────────────────────────────────
class GPSSender:
    """ส่ง GPS Location อัตโนมัติตาม Route Waypoints"""

    def __init__(self, client: DriverClient, bus_id: str, route: str):
        self.client = client
        self.bus_id = bus_id
        self.route = route
        self.waypoints = ROUTE_WAYPOINTS.get(route, list(ROUTE_WAYPOINTS.values())[0])
        self.wp_idx = 0
        self.running = False
        self.interval = 5   # ส่งทุก 5 วินาที

    def _interpolate(self, a, b, t):
        """หาจุดระหว่าง 2 waypoints"""
        lat = a[0] + (b[0] - a[0]) * t
        lng = a[1] + (b[1] - a[1]) * t
        return lat, lng

    def send_loop(self):
        self.running = True
        progress = 0.0   # 0.0 → 1.0 ระหว่าง waypoints
        wp_count = len(self.waypoints)

        while self.running:
            wp_a = self.waypoints[self.wp_idx % wp_count]
            wp_b = self.waypoints[(self.wp_idx + 1) % wp_count]

            lat, lng = self._interpolate(wp_a, wp_b, progress)
            # เพิ่ม noise เล็กน้อย
            lat += random.uniform(-0.0002, 0.0002)
            lng += random.uniform(-0.0002, 0.0002)
            speed = random.uniform(20, 45)
            current_stop = wp_a[2]

            try:
                res = self.client.send({
                    "action": "UPDATE_LOCATION",
                    "bus_id": self.bus_id,
                    "latitude": round(lat, 6),
                    "longitude": round(lng, 6),
                    "speed": round(speed, 1),
                    "current_stop": current_stop,
                })
                ts = datetime.now().strftime("%H:%M:%S")
                status = "✅" if res["status"] == "ok" else "❌"
                print(f"  {status} [{ts}] ส่ง GPS → ({lat:.4f}, {lng:.4f})  "
                      f"ความเร็ว {speed:.1f} km/h  จุด: {current_stop}")
            except Exception as e:
                print(clr(f"  ⚠️  ส่ง GPS ล้มเหลว: {e}", C.RED))

            # เลื่อน progress
            progress += 0.25
            if progress >= 1.0:
                progress = 0.0
                self.wp_idx = (self.wp_idx + 1) % (wp_count - 1)

            time.sleep(self.interval)

    def stop(self):
        self.running = False


# ─── Manual Controls ────────────────────────────────────────────────────────────
def show_status(client: DriverClient, bus_id: str):
    res = client.send({"action": "GET_BUS", "bus_id": bus_id})
    if res["status"] == "ok":
        bus = res["bus"]
        print(clr(f"\n  📊 สถานะรถ {bus_id}", C.BOLD, C.WHITE))
        print(f"  สถานะ  : {bus['status']}")
        print(f"  จุดปัจจุบัน: {bus['current_stop']} → {bus['next_stop']}")
        print(f"  ผู้โดยสาร : {bus['passengers']} คน")
        print(f"  อัพเดตล่าสุด: {bus['last_updated']}\n")


def driver_menu(client: DriverClient, bus_id: str, gps: GPSSender):
    while True:
        print(clr("\n  ═══ เมนูคนขับรถ ═══", C.CYAN, C.BOLD))
        print(f"  บัส: {clr(bus_id, C.YELLOW, C.BOLD)}")
        print("  1  ดูสถานะรถของตัวเอง")
        print("  2  หยุดส่ง GPS อัตโนมัติ")
        print("  3  เริ่มส่ง GPS อัตโนมัติ")
        print("  0  ออกจากระบบ")

        choice = input(clr("  เลือก: ", C.CYAN)).strip()

        if choice == "1":
            show_status(client, bus_id)
        elif choice == "2":
            gps.stop()
            print(clr("  ⏹️  หยุดส่ง GPS แล้ว", C.YELLOW))
        elif choice == "3":
            if not gps.running:
                t = threading.Thread(target=gps.send_loop, daemon=True)
                t.start()
                print(clr("  ▶️  เริ่มส่ง GPS แล้ว", C.GREEN))
        elif choice == "0":
            gps.stop()
            print(clr("  👋 ออกจากระบบ", C.YELLOW))
            break


# ─── Main ────────────────────────────────────────────────────────────────────────
def main():
    print(clr("\n  🚌 University Bus Tracker — Driver Client", C.BOLD, C.WHITE))
    print(clr("  ─" * 30, C.CYAN))

    # เลือกสาย
    routes = list(ROUTE_WAYPOINTS.keys())
    print(f"  สายที่มี: {', '.join(routes)}")
    route = input(clr("  เลือกสาย (เช่น A1): ", C.CYAN)).strip().upper()
    if route not in routes:
        print(clr(f"  ❌ ไม่มีสาย {route}", C.RED))
        sys.exit(1)

    bus_id = f"BUS-{route}"
    driver_name = input(clr("  ชื่อคนขับ: ", C.CYAN)).strip() or "ไม่ระบุ"

    # เชื่อมต่อ Server
    client = DriverClient()
    try:
        client.connect()
        print(clr(f"  ✅ เชื่อมต่อ Server สำเร็จ", C.GREEN, C.BOLD))
    except Exception as e:
        print(clr(f"  ❌ ไม่สามารถเชื่อมต่อ: {e}", C.RED))
        sys.exit(1)

    print(clr(f"\n  🛞  บัส {bus_id} | คนขับ: {driver_name}", C.WHITE, C.BOLD))
    print(clr("  📡 เริ่มส่ง GPS Location อัตโนมัติทุก 5 วินาที...\n", C.GREEN))

    gps = GPSSender(client, bus_id, route)

    # เริ่ม GPS thread
    t_gps = threading.Thread(target=gps.send_loop, daemon=True)
    t_gps.start()

    # เปิดเมนูคนขับ
    try:
        driver_menu(client, bus_id, gps)
    except KeyboardInterrupt:
        gps.stop()
        print(clr("\n  👋 ออกจากระบบ", C.YELLOW))
    finally:
        client.close()


if __name__ == "__main__":
    main()