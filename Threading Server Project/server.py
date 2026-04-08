"""
University Bus Real-Time Tracking System — SERVER (V2 - Dynamic Movement)
==================================================
R1: TCP Socket — รับ Client เชื่อมต่อและส่งคำสั่ง
R2: Public API  — ข้อมูล Real-time แบบอิสระต่อกันรายคัน
R3: SMTP Email  — ส่งอีเมลแจ้งเตือนอัตโนมัติ
R4: Threading   — รองรับ Client หลายคน และแยก Thread อัพเดตรถแต่ละคัน
"""

import socket
import threading
import json
import smtplib
import time
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass, asdict
from typing import Optional
import random

# ─── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("server.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

# ─── Config ────────────────────────────────────────────────────────────────────
HOST = "127.0.0.1"
PORT = 9999

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "poommin.tk@gmail.com"       
SMTP_PASS = ""          
SMTP_FROM = "Bus Tracker <poommin.tk@gmail.com>"

# ─── Data Models ───────────────────────────────────────────────────────────────
@dataclass
class BusSchedule:
    route: str
    departure_time: str
    origin: str
    destination: str

@dataclass
class BusStatus:
    bus_id: str
    route: str
    driver_name: str
    latitude: float
    longitude: float
    speed: float
    status: str           
    delay_minutes: int
    current_stop: str
    next_stop: str
    passengers: int
    last_updated: str
    schedule: Optional[BusSchedule] = None

    def to_dict(self):
        d = asdict(self)
        if self.schedule:
            d["schedule"] = asdict(self.schedule)
        return d

# ─── Shared State ──────────────────────────────────────────────────────────────
bus_db: dict[str, BusStatus] = {}
subscribers: dict[str, list[str]] = {}
clients_lock = threading.Lock()
bus_lock = threading.Lock()
subscribers_lock = threading.Lock()
active_clients: list[socket.socket] = []

# ─── Mock API & Movement Logic ───────────────────────────────────────────────
class MockBusAPI:
    """จำลองเส้นทางและจุดจอดจริงของแต่ละสาย"""
    ROUTE_DETAILS = {
        "A1": ["หอพัก 5", "อาคารเรียนรวม 1", "ตึกวิศวกรรมศาสตร์", "หอพัก 5"],
        "A2": ["หอพัก 13", "อาคารเรียนรวม 2", "โรงอาหารเรียนรวม 1", "หอพัก 13"],
        "B10": ["ประตู 4", "โรงอาหารเรียนรวม 1", "อาคารบรรณสาร", "ประตู 4"],
        "B20": ["สนามกีฬา", "อาคารบรรณสาร", "โรงพยาบาล ม.ท.ส.", "สนามกีฬา"],
        "C100": ["โรงพยาบาล ม.ท.ส.", "ประตู 1", "ประตู 2", "ประตู 3", "โรงพยาบาล ม.ท.ส."]
    }
    
    DRIVERS = ["สมชาย ใจดี", "วิชัย มั่นคง", "ประสิทธิ์ รวดเร็ว", "อนันต์ ซื่อสัตย์", "บุญมี ขยัน"]
    
    # เก็บตำแหน่งป้ายปัจจุบันของรถแต่ละคัน {bus_id: current_stop_index}
    _bus_progress = {f"BUS-{r}": 0 for r in ROUTE_DETAILS.keys()}

    @classmethod
    def fetch_single_bus(cls, route: str) -> BusStatus:
        """สร้างข้อมูลจำลองการเคลื่อนที่ของรถรายคัน"""
        bus_id = f"BUS-{route}"
        stops = cls.ROUTE_DETAILS[route]
        
        # อัพเดตตำแหน่งป้าย (ขยับไปป้ายถัดไป)
        current_idx = cls._bus_progress[bus_id]
        next_idx = (current_idx + 1) % len(stops)
        cls._bus_progress[bus_id] = next_idx
        
        # จำลองสถานะ
        rand = random.random()
        if rand < 0.05:
            status, delay = "cancelled", 0
        elif rand < 0.15:
            status, delay = "delayed", random.randint(5, 20)
        else:
            status, delay = "on_time", 0

        return BusStatus(
            bus_id=bus_id,
            route=route,
            driver_name=random.choice(cls.DRIVERS),
            latitude=14.8800 + random.uniform(-0.01, 0.01),
            longitude=102.0160 + random.uniform(-0.01, 0.01),
            speed=random.uniform(20, 50) if status != "cancelled" else 0,
            status=status,
            delay_minutes=delay,
            current_stop=stops[current_idx],
            next_stop=stops[next_idx],
            passengers=random.randint(0, 40),
            last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            schedule=BusSchedule(route, "08:00", stops[0], stops[-1])
        )

# ─── Email Service ────────────────────────────────────────────────────────
class EmailService:
    @staticmethod
    def send(to_email: str, subject: str, body_html: str):
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = SMTP_FROM
            msg["To"] = to_email
            msg.attach(MIMEText(body_html, "html", "utf-8"))

            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
                server.sendmail(SMTP_USER, to_email, msg.as_string())
            log.info(f"📧 Email sent → {to_email} | {subject}")
        except Exception as e:
            log.warning(f"⚠️  Email failed → {to_email}: {e}")

    @staticmethod
    def build_alert_html(bus: BusStatus, alert_type: str) -> tuple[str, str]:
        icons = {"delayed": "⏰", "cancelled": "🚫", "departed": "🚌"}
        icon = icons.get(alert_type, "ℹ️")
        subject = f"{icon} Bus Alert: สาย {bus.route} ({alert_type})"
        
        html = f"""
        <div style="font-family:sans-serif; border:1px solid #ccc; padding:20px; border-radius:10px;">
            <h2 style="color:#1a3a5c;">{icon} สถานะรถเมล์สาย {bus.route}</h2>
            <p>สถานะปัจจุบัน: <b>{bus.status}</b></p>
            <p>ตำแหน่ง: {bus.current_stop} -> {bus.next_stop}</p>
            <p>อัพเดตเมื่อ: {bus.last_updated}</p>
        </div>
        """
        return subject, html

# ─── Background Services ────────────────────────────────────────────────────────
class BusUpdateService:
    """แยก Thread ให้รถแต่ละคันอัพเดตด้วยเวลาที่ต่างกัน"""
    def __init__(self):
        self._prev_status: dict[str, str] = {}

    def run(self):
        log.info("🔄 BusUpdateService started (Independent Threads)")
        for route in MockBusAPI.ROUTE_DETAILS.keys():
            t = threading.Thread(target=self._bus_runner, args=(route,), daemon=True)
            t.start()

    def _bus_runner(self, route: str):
        bus_id = f"BUS-{route}"
        while True:
            try:
                # สุ่มเวลารอระหว่างป้าย (20 - 60 วินาที) ทำให้รถแต่ละคันไม่พร้อมกัน
                wait_time = random.uniform(20, 60)
                time.sleep(wait_time)

                new_data = MockBusAPI.fetch_single_bus(route)
                
                with bus_lock:
                    bus_db[bus_id] = new_data

                self._check_single_alert(new_data)
                log.info(f"📡 {bus_id} moved to {new_data.current_stop} (Next in {wait_time:.1f}s)")
            except Exception as e:
                log.error(f"Error in runner {bus_id}: {e}")

    def _check_single_alert(self, bus: BusStatus):
        prev = self._prev_status.get(bus.bus_id)
        if prev != bus.status:
            if bus.status in ("delayed", "cancelled"):
                with subscribers_lock:
                    subs = dict(subscribers)
                self._send_alerts(bus, bus.status, subs)
            self._prev_status[bus.bus_id] = bus.status

    def _send_alerts(self, bus: BusStatus, alert_type: str, subs: dict):
        for email, bus_ids in subs.items():
            if bus.bus_id in bus_ids or "ALL" in bus_ids:
                subject, html = EmailService.build_alert_html(bus, alert_type)
                threading.Thread(target=EmailService.send, args=(email, subject, html), daemon=True).start()

# ─── Command Handler ────────────────────────────────────────────────────────────
class CommandHandler:
    def handle(self, cmd: dict) -> dict:
        action = cmd.get("action", "")
        handlers = {
            "GET_ALL_BUSES":    self._get_all_buses,
            "GET_BUS":          self._get_bus,
            "SUBSCRIBE":        self._subscribe,
            "UNSUBSCRIBE":      self._unsubscribe,
            "GET_ROUTES":       self._get_routes,
            "PING":             self._ping,
        }
        fn = handlers.get(action)
        return fn(cmd) if fn else {"status": "error", "message": "Unknown action"}

    def _get_all_buses(self, _) -> dict:
        with bus_lock:
            return {"status": "ok", "buses": [b.to_dict() for b in bus_db.values()], "count": len(bus_db)}

    def _get_bus(self, cmd: dict) -> dict:
        bus_id = cmd.get("bus_id", "")
        with bus_lock:
            bus = bus_db.get(bus_id)
        return {"status": "ok", "bus": bus.to_dict()} if bus else {"status": "error", "message": "Not found"}

    def _subscribe(self, cmd: dict) -> dict:
        email, bus_ids = cmd.get("email"), cmd.get("bus_ids", ["ALL"])
        with subscribers_lock:
            subscribers[email] = bus_ids
        return {"status": "ok", "message": "Subscribed successfully"}

    def _unsubscribe(self, cmd: dict) -> dict:
        email = cmd.get("email")
        with subscribers_lock:
            subscribers.pop(email, None)
        return {"status": "ok", "message": "Unsubscribed"}

    def _get_routes(self, _) -> dict:
        routes = {r: {"stops": s} for r, s in MockBusAPI.ROUTE_DETAILS.items()}
        return {"status": "ok", "routes": routes}

    def _ping(self, _) -> dict:
        return {"status": "ok", "message": "pong"}

# ─── Client Thread ──────────────────────────────────────────────────────────
def handle_client(conn: socket.socket, addr: tuple):
    handler = CommandHandler()
    log.info(f"🔌 Client connected: {addr}")
    with clients_lock:
        active_clients.append(conn)
    try:
        buffer = ""
        while True:
            data = conn.recv(4096)
            if not data: break
            buffer += data.decode("utf-8", errors="replace")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if not line.strip(): continue
                cmd = json.loads(line)
                response = json.dumps(handler.handle(cmd), ensure_ascii=False) + "\n"
                conn.sendall(response.encode("utf-8"))
    except Exception as e:
        log.error(f"Client {addr} error: {e}")
    finally:
        with clients_lock:
            if conn in active_clients: active_clients.remove(conn)
        conn.close()
        log.info(f"🔌 Client disconnected: {addr}")

# ─── Main Server ────────────────────────────────────────────────────────────────
def main():
    log.info("🚌 University Bus SERVER V2 (Dynamic Running)")
    
    updater = BusUpdateService()
    updater.run() # เริ่มแยก Thread อัพเดตรถรายคัน

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((HOST, PORT))
    server_sock.listen(50)

    log.info(f"✅ Server ready on {HOST}:{PORT}")

    try:
        while True:
            conn, addr = server_sock.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        log.info("🛑 Shutting down...")
    finally:
        server_sock.close()

if __name__ == "__main__":
    main()