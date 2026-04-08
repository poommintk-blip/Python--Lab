"""
University Bus Real-Time Tracking System — CLIENT USER
=======================================================
ผู้ใช้ทั่วไปเชื่อมต่อ Server ผ่าน TCP Socket เพื่อ:
  - ดูข้อมูลรถเมล์ทุกคันแบบ Real-time
  - ติดตามรถเมล์สายที่สนใจ
  - สมัครรับอีเมลแจ้งเตือน
"""

import socket
import json
import sys
import time
import threading
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
    BLUE   = "\033[94m"
    CYAN   = "\033[96m"
    WHITE  = "\033[97m"
    GRAY   = "\033[90m"
    BG_BLUE = "\033[44m"


def clr(text, *codes):
    return "".join(codes) + str(text) + C.RESET


def status_color(status: str) -> str:
    colors = {
        "on_time":   C.GREEN,
        "delayed":   C.YELLOW,
        "cancelled": C.RED,
        "departed":  C.BLUE,
    }
    labels = {
        "on_time":   "✅ ตรงเวลา",
        "delayed":   "⏰ ล่าช้า",
        "cancelled": "🚫 ยกเลิก",
        "departed":  "🚌 ออกแล้ว",
    }
    c = colors.get(status, C.GRAY)
    label = labels.get(status, status)
    return clr(label, c, C.BOLD)


# ─── TCP Client ─────────────────────────────────────────────────────────────────
class BusClient:
    def __init__(self):
        self.sock = None
        self._lock = threading.Lock()

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(10)
        self.sock.connect((SERVER_HOST, SERVER_PORT))
        print(clr(f"เชื่อมต่อ Server {SERVER_HOST}:{SERVER_PORT} สำเร็จ", C.GREEN, C.BOLD))

    def send(self, data: dict) -> dict:
        with self._lock:
            msg = json.dumps(data, ensure_ascii=False) + "\n"
            self.sock.sendall(msg.encode("utf-8"))
            response = b""
            while not response.endswith(b"\n"):
                chunk = self.sock.recv(65536)
                if not chunk:
                    raise ConnectionError("Server closed connection")
                response += chunk
            return json.loads(response.strip().decode("utf-8"))

    def close(self):
        if self.sock:
            self.sock.close()


# ─── Display Helpers ────────────────────────────────────────────────────────────
def print_header():
    w = 60
    print("\n" + clr("─" * w, C.BLUE))
    print(clr("  🚌  University Bus Real-Time Tracking System", C.BOLD, C.WHITE))
    print(clr(f"  {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", C.GRAY))
    print(clr("─" * w, C.BLUE))


def print_bus_card(bus: dict):
    """แสดงข้อมูลรถเมล์แบบ Card"""
    sched = bus.get("schedule") or {}
    delay_txt = f" (+{bus['delay_minutes']} นาที)" if bus["delay_minutes"] > 0 else ""

    print(clr(f"\n  ┌─ {bus['bus_id']} │ สาย {bus['route']}", C.CYAN, C.BOLD))
    print(f"  │  สถานะ  : {status_color(bus['status'])}{delay_txt}")
    print(f"  │  คนขับ  : {bus['driver_name']}")
    if sched:
        print(f"  │  เส้นทาง: {sched.get('origin','?')} → {sched.get('destination','?')}")
        print(f"  │  เวลาออก: {sched.get('departure_time','?')}")
    print(f"  │  จอดที่  : {clr(bus['current_stop'], C.YELLOW)}")
    print(f"  │  ถัดไป  : {bus['next_stop']}")
    print(f"  │  ผู้โดยสาร: {bus['passengers']} คน  |  ความเร็ว: {bus['speed']:.1f} km/h")
    print(f"  │  GPS    : ({bus['latitude']:.4f}, {bus['longitude']:.4f})")
    print(clr(f"  └─ อัพเดต: {bus['last_updated']}", C.GRAY))


def print_menu():
    print(clr("\n╔══════════════════════════════╗", C.BLUE))
    print(clr("║       เมนูหลัก               ║", C.BLUE))
    print(clr("╠══════════════════════════════╣", C.BLUE))
    options = [
        ("1", "ดูรถเมล์ทุกคัน"),
        ("2", "ค้นหารถเมล์ตาม ID"),
        ("3", "ดูตารางเดินรถ"),
        ("4", "สมัครรับแจ้งเตือน Email"),
        ("5", "ยกเลิกการแจ้งเตือน"),
        ("6", "ติดตามรถเมล์แบบ Live (Auto-refresh)"),
        ("0", "ออกจากระบบ"),
    ]
    for key, label in options:
        print(f"║  {clr(key, C.CYAN, C.BOLD)}  {label:<24}║")
    print(clr("╚══════════════════════════════╝", C.BLUE))


# ─── Feature Functions ──────────────────────────────────────────────────────────
def show_all_buses(client: BusClient):
    print(clr("\n🔄 กำลังดึงข้อมูล...", C.GRAY))
    res = client.send({"action": "GET_ALL_BUSES"})
    if res["status"] != "ok":
        print(clr(f"❌ {res.get('message')}", C.RED))
        return
    buses = res["buses"]
    print_header()
    print(clr(f"  พบรถเมล์ทั้งหมด {res['count']} คัน", C.WHITE, C.BOLD))
    for bus in buses:
        print_bus_card(bus)
    print()


def search_bus(client: BusClient):
    bus_id = input(clr("  ป้อน Bus ID (เช่น BUS-A1): ", C.CYAN)).strip().upper()
    if not bus_id.startswith("BUS-"):
        bus_id = "BUS-" + bus_id
    res = client.send({"action": "GET_BUS", "bus_id": bus_id})
    if res["status"] != "ok":
        print(clr(f"  ❌ {res.get('message')}", C.RED))
        return
    print_bus_card(res["bus"])


def show_routes(client: BusClient):
    res = client.send({"action": "GET_ROUTES"})
    if res["status"] != "ok":
        return
    print(clr("\n  📋 ตารางเดินรถ", C.BOLD, C.WHITE))
    print(clr("  " + "─" * 50, C.BLUE))
    header = f"  {'สาย':<6} {'เวลา':<8} {'ต้นทาง':<18} {'ปลายทาง'}"
    print(clr(header, C.CYAN))
    print(clr("  " + "─" * 50, C.GRAY))
    for route, info in res["routes"].items():
        print(f"  {clr(route, C.YELLOW, C.BOLD):<6} "
              f"{info['departure_time']:<8} "
              f"{info['origin']:<18} {info['destination']}")
    print()


def subscribe_email(client: BusClient):
    email = input(clr("  ป้อน Email ของคุณ: ", C.CYAN)).strip()
    if not email:
        return
    print(clr("  เลือกสาย (เว้นวรรคคั่น เช่น A1 B1) หรือ Enter เพื่อรับทุกสาย: ", C.CYAN), end="")
    routes_input = input().strip().upper()

    if routes_input:
        bus_ids = [f"BUS-{r}" for r in routes_input.split()]
    else:
        bus_ids = ["ALL"]

    res = client.send({"action": "SUBSCRIBE", "email": email, "bus_ids": bus_ids})
    color = C.GREEN if res["status"] == "ok" else C.RED
    print(clr(f"  {'✅' if res['status']=='ok' else '❌'} {res['message']}", color))


def unsubscribe_email(client: BusClient):
    email = input(clr("  ป้อน Email ที่ต้องการยกเลิก: ", C.CYAN)).strip()
    res = client.send({"action": "UNSUBSCRIBE", "email": email})
    color = C.GREEN if res["status"] == "ok" else C.RED
    print(clr(f"  {'✅' if res['status']=='ok' else '❌'} {res['message']}", color))


def live_track(client: BusClient):
    print(clr("  กด Ctrl+C เพื่อหยุด Live tracking", C.GRAY))
    bus_filter = input(clr("  Bus ID ที่ต้องการติดตาม (Enter = ทุกคัน): ", C.CYAN)).strip().upper()
    if bus_filter and not bus_filter.startswith("BUS-"):
        bus_filter = "BUS-" + bus_filter

    try:
        while True:
            # Clear screen
            print("\033[2J\033[H", end="")
            if bus_filter:
                res = client.send({"action": "GET_BUS", "bus_id": bus_filter})
                if res["status"] == "ok":
                    print_header()
                    print_bus_card(res["bus"])
            else:
                show_all_buses(client)
            print(clr(f"  🔄 Auto-refresh ทุก 5 วินาที | กด Ctrl+C เพื่อหยุด", C.GRAY))
            time.sleep(5)
    except KeyboardInterrupt:
        print(clr("\n  ⏹️  หยุด Live tracking", C.YELLOW))


# ─── Main Loop ──────────────────────────────────────────────────────────────────
def main():
    client = BusClient()
    try:
        client.connect()
    except Exception as e:
        print(clr(f"❌ ไม่สามารถเชื่อมต่อ Server ได้: {e}", C.RED))
        sys.exit(1)

    actions = {
        "1": show_all_buses,
        "2": search_bus,
        "3": show_routes,
        "4": subscribe_email,
        "5": unsubscribe_email,
        "6": live_track,
    }

    try:
        while True:
            print_menu()
            choice = input(clr("  เลือกเมนู: ", C.BOLD)).strip()
            if choice == "0":
                print(clr("  👋 ออกจากระบบ", C.YELLOW))
                break
            fn = actions.get(choice)
            if fn:
                fn(client)
            else:
                print(clr("  ❌ เมนูไม่ถูกต้อง", C.RED))
    except KeyboardInterrupt:
        print(clr("\n  👋 ออกจากระบบ", C.YELLOW))
    finally:
        client.close()


if __name__ == "__main__":
    main()