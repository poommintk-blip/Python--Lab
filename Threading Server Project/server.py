"""
University Bus Real-Time Tracking System — SERVER
==================================================
R1: TCP Socket — รับ Client เชื่อมต่อและส่งคำสั่ง
R2: Public API  — ดึงข้อมูล real-time (จำลองด้วย MockAPI)
R3: SMTP Email  — ส่งอีเมลแจ้งเตือนอัตโนมัติ
R4: Threading   — รองรับ Client หลายคนพร้อมกัน
"""

import socket
import threading
import json
import smtplib
import time
import logging
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass, field, asdict
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
SMTP_USER = "your_email@gmail.com"       # ← เปลี่ยนเป็น Email ของคุณ
SMTP_PASS = "your_app_password"          # ← เปลี่ยนเป็น App Password
SMTP_FROM = "Bus Tracker <your_email@gmail.com>"

# ─── Data Models ───────────────────────────────────────────────────────────────
@dataclass
class BusSchedule:
    """ตารางเวลารถเมล์"""
    route: str
    departure_time: str   # "HH:MM"
    origin: str
    destination: str


@dataclass
class BusStatus:
    """สถานะรถเมล์แบบ Real-time"""
    bus_id: str
    route: str
    driver_name: str
    latitude: float
    longitude: float
    speed: float
    status: str           # "on_time" | "delayed" | "cancelled" | "departed"
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
subscribers: dict[str, list[str]] = {}   # email → [bus_id, ...]
clients_lock = threading.Lock()
bus_lock = threading.Lock()
subscribers_lock = threading.Lock()
active_clients: list[socket.socket] = []


# ─── Mock API (แทน Public API จริง) ───────────────────────────────────────────
class MockBusAPI:
    """จำลอง Public API สำหรับข้อมูลรถเมล์ (R2)"""
    ROUTES = {
        "A1": BusSchedule("A1", "07:00", "หอพัก A", "อาคารเรียนกลาง"),
        "A2": BusSchedule("A2", "08:30", "หอพัก B", "คณะวิศวกรรมศาสตร์"),
        "B1": BusSchedule("B1", "09:00", "ประตูหลัก", "โรงอาหารกลาง"),
        "B2": BusSchedule("B2", "10:30", "สระว่ายน้ำ", "ห้องสมุดกลาง"),
        "C1": BusSchedule("C1", "12:00", "คณะแพทย์", "ประตูหน้า"),
    }
    STOPS = [
        "ประตูหลัก", "หอพัก A", "หอพัก B", "อาคารเรียนกลาง",
        "คณะวิศวกรรมศาสตร์", "โรงอาหารกลาง", "ห้องสมุดกลาง",
        "สระว่ายน้ำ", "คณะแพทย์", "ประตูหน้า",
    ]
    DRIVERS = ["สมชาย ใจดี", "วิชัย มั่นคง", "ประสิทธิ์ รวดเร็ว", "อนันต์ ซื่อสัตย์", "บุญมี ขยัน"]

    @staticmethod
    def fetch_all_buses() -> list[BusStatus]:
        """ดึงข้อมูลรถเมล์ทุกคัน (จำลอง)"""
        buses = []
        for i, (route, schedule) in enumerate(MockBusAPI.ROUTES.items()):
            bus_id = f"BUS-{route}"
            # จำลองสถานการณ์ต่าง ๆ
            rand = random.random()
            if rand < 0.1:
                status, delay = "cancelled", 0
            elif rand < 0.3:
                status = "delayed"
                delay = random.randint(5, 30)
            else:
                status, delay = "on_time", 0

            stop_idx = random.randint(0, len(MockBusAPI.STOPS) - 2)
            bus = BusStatus(
                bus_id=bus_id,
                route=route,
                driver_name=MockBusAPI.DRIVERS[i % len(MockBusAPI.DRIVERS)],
                latitude=14.8800 + random.uniform(-0.02, 0.02),
                longitude=102.0160 + random.uniform(-0.02, 0.02),
                speed=random.uniform(0, 60) if status != "cancelled" else 0,
                status=status,
                delay_minutes=delay,
                current_stop=MockBusAPI.STOPS[stop_idx],
                next_stop=MockBusAPI.STOPS[stop_idx + 1],
                passengers=random.randint(0, 40),
                last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                schedule=schedule,
            )
            buses.append(bus)
        return buses


# ─── Email Service (R3) ────────────────────────────────────────────────────────
class EmailService:
    @staticmethod
    def send(to_email: str, subject: str, body_html: str):
        """ส่งอีเมลแจ้งเตือน"""
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
        """สร้าง HTML สำหรับอีเมลแจ้งเตือน"""
        icons = {"delayed": "⏰", "cancelled": "🚫", "departed": "🚌"}
        icon = icons.get(alert_type, "ℹ️")

        if alert_type == "delayed":
            subject = f"{icon} รถเมล์สาย {bus.route} ล่าช้า {bus.delay_minutes} นาที"
            detail = f"รถเมล์สาย <b>{bus.route}</b> ล่าช้า <b>{bus.delay_minutes} นาที</b><br>ตำแหน่งปัจจุบัน: {bus.current_stop}"
        elif alert_type == "cancelled":
            subject = f"{icon} รถเมล์สาย {bus.route} ยกเลิกการวิ่ง"
            detail = f"รถเมล์สาย <b>{bus.route}</b> ไม่สามารถให้บริการได้ในวันนี้"
        else:
            subject = f"{icon} รถเมล์สาย {bus.route} ออกแล้ว"
            detail = f"รถเมล์สาย <b>{bus.route}</b> ออกจาก <b>{bus.current_stop}</b> แล้ว"

        schedule = bus.schedule
        sched_info = ""
        if schedule:
            sched_info = f"""
            <tr><td style="padding:4px 8px;color:#888">เส้นทาง</td>
                <td style="padding:4px 8px">{schedule.origin} → {schedule.destination}</td></tr>
            <tr><td style="padding:4px 8px;color:#888">เวลาออก</td>
                <td style="padding:4px 8px">{schedule.departure_time}</td></tr>"""

        html = f"""
        <div style="font-family:'Segoe UI',sans-serif;max-width:520px;margin:auto;
                    border:1px solid #e0e0e0;border-radius:12px;overflow:hidden">
          <div style="background:#1a3a5c;padding:20px 24px;color:white">
            <h2 style="margin:0;font-size:20px">{icon} University Bus Tracker</h2>
            <p style="margin:4px 0 0;opacity:.75;font-size:13px">การแจ้งเตือนอัตโนมัติ</p>
          </div>
          <div style="padding:24px;background:#fafafa">
            <p style="font-size:16px;margin-top:0">{detail}</p>
            <table style="width:100%;border-collapse:collapse;background:white;
                          border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.1)">
              <tr style="background:#f0f4f8">
                <td colspan="2" style="padding:8px 12px;font-weight:bold;font-size:13px">
                  🚌 สาย {bus.route} — {bus.bus_id}
                </td>
              </tr>
              <tr><td style="padding:4px 8px;color:#888">คนขับ</td>
                  <td style="padding:4px 8px">{bus.driver_name}</td></tr>
              <tr><td style="padding:4px 8px;color:#888">สถานะ</td>
                  <td style="padding:4px 8px">{bus.status}</td></tr>
              <tr><td style="padding:4px 8px;color:#888">จอดอยู่ที่</td>
                  <td style="padding:4px 8px">{bus.current_stop}</td></tr>
              <tr><td style="padding:4px 8px;color:#888">จุดถัดไป</td>
                  <td style="padding:4px 8px">{bus.next_stop}</td></tr>
              {sched_info}
              <tr><td style="padding:4px 8px;color:#888">อัพเดตล่าสุด</td>
                  <td style="padding:4px 8px;font-size:12px">{bus.last_updated}</td></tr>
            </table>
          </div>
          <div style="padding:12px 24px;background:#eef2f7;font-size:11px;color:#999;text-align:center">
            University Bus Tracking System • อีเมลนี้ส่งโดยระบบอัตโนมัติ กรุณาอย่าตอบกลับ
          </div>
        </div>"""
        return subject, html


# ─── Background Services ────────────────────────────────────────────────────────
class BusUpdateService:
    """อัพเดตข้อมูลรถเมล์จาก API ทุก 10 วินาที (R2)"""
    def __init__(self):
        self._prev_status: dict[str, str] = {}

    def run(self):
        log.info("🔄 BusUpdateService started")
        while True:
            try:
                buses = MockBusAPI.fetch_all_buses()
                with bus_lock:
                    for bus in buses:
                        bus_db[bus.bus_id] = bus

                self._check_alerts(buses)
                log.info(f"📡 Updated {len(buses)} buses")
            except Exception as e:
                log.error(f"BusUpdateService error: {e}")
            time.sleep(10)

    def _check_alerts(self, buses: list[BusStatus]):
        """ตรวจสอบและส่งอีเมลแจ้งเตือน (R3)"""
        with subscribers_lock:
            subs = dict(subscribers)

        for bus in buses:
            prev = self._prev_status.get(bus.bus_id)

            # ตรวจสอบการเปลี่ยนแปลงสถานะ
            if prev != bus.status:
                if bus.status in ("delayed", "cancelled", "departed"):
                    self._send_alerts(bus, bus.status, subs)
                self._prev_status[bus.bus_id] = bus.status

    def _send_alerts(self, bus: BusStatus, alert_type: str, subs: dict):
        for email, bus_ids in subs.items():
            if bus.bus_id in bus_ids or "ALL" in bus_ids:
                subject, html = EmailService.build_alert_html(bus, alert_type)
                t = threading.Thread(target=EmailService.send, args=(email, subject, html), daemon=True)
                t.start()


# ─── Command Handler ────────────────────────────────────────────────────────────
class CommandHandler:
    """จัดการคำสั่งจาก Client"""

    def handle(self, cmd: dict) -> dict:
        action = cmd.get("action", "")
        handlers = {
            "GET_ALL_BUSES":    self._get_all_buses,
            "GET_BUS":          self._get_bus,
            "UPDATE_LOCATION":  self._update_location,   # Bus Driver
            "SUBSCRIBE":        self._subscribe,
            "UNSUBSCRIBE":      self._unsubscribe,
            "GET_ROUTES":       self._get_routes,
            "PING":             self._ping,
        }
        fn = handlers.get(action)
        if not fn:
            return {"status": "error", "message": f"Unknown action: {action}"}
        return fn(cmd)

    def _get_all_buses(self, _) -> dict:
        with bus_lock:
            return {
                "status": "ok",
                "buses": [b.to_dict() for b in bus_db.values()],
                "count": len(bus_db),
                "timestamp": datetime.now().isoformat(),
            }

    def _get_bus(self, cmd: dict) -> dict:
        bus_id = cmd.get("bus_id", "")
        with bus_lock:
            bus = bus_db.get(bus_id)
        if not bus:
            return {"status": "error", "message": f"Bus {bus_id} not found"}
        return {"status": "ok", "bus": bus.to_dict()}

    def _update_location(self, cmd: dict) -> dict:
        """Bus Driver ส่ง GPS มาอัพเดต"""
        bus_id = cmd.get("bus_id")
        lat = cmd.get("latitude")
        lng = cmd.get("longitude")
        speed = cmd.get("speed", 0)
        current_stop = cmd.get("current_stop", "")

        if not all([bus_id, lat is not None, lng is not None]):
            return {"status": "error", "message": "Missing bus_id/latitude/longitude"}

        with bus_lock:
            if bus_id not in bus_db:
                return {"status": "error", "message": f"Bus {bus_id} not registered"}
            bus_db[bus_id].latitude = lat
            bus_db[bus_id].longitude = lng
            bus_db[bus_id].speed = speed
            if current_stop:
                bus_db[bus_id].current_stop = current_stop
            bus_db[bus_id].last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        log.info(f"📍 {bus_id} location updated → ({lat:.4f}, {lng:.4f}) speed={speed:.1f}km/h")
        return {"status": "ok", "message": "Location updated"}

    def _subscribe(self, cmd: dict) -> dict:
        email = cmd.get("email", "")
        bus_ids = cmd.get("bus_ids", ["ALL"])   # ["ALL"] หรือ ["BUS-A1","BUS-B1"]
        if not email:
            return {"status": "error", "message": "email required"}
        with subscribers_lock:
            subscribers[email] = bus_ids
        log.info(f"📬 Subscribed: {email} → {bus_ids}")
        return {"status": "ok", "message": f"Subscribed {email} to {bus_ids}"}

    def _unsubscribe(self, cmd: dict) -> dict:
        email = cmd.get("email", "")
        with subscribers_lock:
            removed = subscribers.pop(email, None)
        return {"status": "ok" if removed else "error",
                "message": "Unsubscribed" if removed else "Email not found"}

    def _get_routes(self, _) -> dict:
        routes = {r: asdict(s) for r, s in MockBusAPI.ROUTES.items()}
        return {"status": "ok", "routes": routes}

    def _ping(self, _) -> dict:
        return {"status": "ok", "message": "pong", "server_time": datetime.now().isoformat()}


# ─── Client Thread (R1 + R4) ───────────────────────────────────────────────────
def handle_client(conn: socket.socket, addr: tuple):
    """จัดการ Client แต่ละคนในเธรดแยก (R4)"""
    handler = CommandHandler()
    log.info(f"🔌 Client connected: {addr}")

    with clients_lock:
        active_clients.append(conn)

    try:
        buffer = ""
        while True:
            data = conn.recv(4096)
            if not data:
                break

            buffer += data.decode("utf-8", errors="replace")

            # รองรับหลาย JSON ในคราวเดียว
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                try:
                    cmd = json.loads(line)
                    result = handler.handle(cmd)
                    response = json.dumps(result, ensure_ascii=False) + "\n"
                    conn.sendall(response.encode("utf-8"))
                except json.JSONDecodeError:
                    err = json.dumps({"status": "error", "message": "Invalid JSON"}) + "\n"
                    conn.sendall(err.encode("utf-8"))

    except (ConnectionResetError, BrokenPipeError):
        pass
    except Exception as e:
        log.error(f"Client {addr} error: {e}")
    finally:
        with clients_lock:
            if conn in active_clients:
                active_clients.remove(conn)
        conn.close()
        log.info(f"🔌 Client disconnected: {addr}")


# ─── Main Server ────────────────────────────────────────────────────────────────
def main():
    log.info("=" * 55)
    log.info("  🚌 University Bus Real-Time Tracking SERVER")
    log.info(f"  Listening on {HOST}:{PORT}")
    log.info("=" * 55)

    # เริ่ม background service อัพเดตข้อมูล (R2)
    updater = BusUpdateService()
    t_update = threading.Thread(target=updater.run, daemon=True)
    t_update.start()

    # รอให้ข้อมูลโหลดครั้งแรก
    time.sleep(2)

    # เริ่ม TCP Server (R1, R4)
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((HOST, PORT))
    server_sock.listen(50)

    log.info("✅ Server ready — waiting for connections...")

    try:
        while True:
            conn, addr = server_sock.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()
            with clients_lock:
                log.info(f"👥 Active clients: {len(active_clients)}")
    except KeyboardInterrupt:
        log.info("🛑 Server shutting down...")
    finally:
        server_sock.close()


if __name__ == "__main__":
    main()
