import socket
import threading
import json
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

#  R4: Threading - รองรับการเชื่อมต่อพร้อมกัน
#  R3: SMTP Email - ส่งอีเมลอัตโนมัติเมื่อถึงเวลารถออก

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

BUS_DB = {}
SUBSCRIBERS = {} # [cite: 53] เก็บ Email ของ Client เพื่อใช้แจ้งเตือน

def send_email(to_email, bus_id, stop_name):
    """ฟังก์ชันหลักสำหรับส่งการแจ้งเตือนทาง E-mail [cite: 24, 52]"""
    try:
        msg = MIMEMultipart()
        msg['Subject'] = f"แจ้งเตือน: รถเมล์สาย {bus_id} กำลังออกจากจุด {stop_name}"
        body = f"เรียน ผู้ใช้งาน\nขณะนี้รถเมล์ {bus_id} กำลังจะออกจาก {stop_name} โปรดเตรียมตัวเดินทาง"
        msg.attach(MIMEText(body, 'plain'))
        # หมายเหตุ: นายสหรัฐ (R3) ต้องเพิ่มการตั้งค่า SMTP จริงที่นี่ 
        log.info(f"📧 ส่งอีเมลแจ้งเตือนไปที่ {to_email} สำหรับรถ {bus_id}")
    except Exception as e:
        log.error(f"⚠️ ระบบส่งอีเมลล้มเหลว: {e}")

class CommandHandler:
    """ศูนย์กลางการประมวลผลคำสั่งจาก Actor ต่างๆ [cite: 50]"""
    def handle(self, cmd, addr):
        action = cmd.get("action")
        
        # สำหรับ Bus Driver (พนักงานขับรถ) [cite: 30]
        if action == "DRIVER_UPDATE":
            bus_id = cmd.get("bus_id")
            stop = cmd.get("current_stop")
            BUS_DB[bus_id] = {"location": stop, "last_seen": str(datetime.now())}
            
            # คนขับสั่งแจ้งเตือนเมื่อรถจะออกจากจุด 
            if cmd.get("send_alert"):
                log.info(f"🔔 พนักงานขับรถ {bus_id} แจ้งเตือนรถออกจาก {stop}")
                self.dispatch_alerts(bus_id, stop)
            return {"status": "ok", "message": "Location updated"}

        # สำหรับ Client User (ผู้ใช้ทั่วไป) เพื่อติดตามรถ [cite: 24, 27]
        elif action == "USER_TRACK":
            return {"status": "ok", "buses": BUS_DB}

        # การสมัครรับแจ้งเตือนสำหรับลูกค้า [cite: 53]
        elif action == "SUBSCRIBE":
            email = cmd.get("email")
            SUBSCRIBERS[email] = cmd.get("bus_ids", ["ALL"])
            return {"status": "ok", "message": "Subscribed"}

        return {"status": "error", "message": "Unknown action"}

    def dispatch_alerts(self, bus_id, stop):
        """กระจายแจ้งเตือนไปยังลูกค้าที่สมัครไว้ [cite: 50]"""
        for email, target_buses in SUBSCRIBERS.items():
            if bus_id in target_buses or "ALL" in target_buses:
                # ใช้ Threading เพื่อไม่ให้การส่งเมลไปขัดจังหวะการรับส่งข้อมูลหลัก 
                threading.Thread(target=send_email, args=(email, bus_id, stop)).start()

def handle_client(conn, addr):
    handler = CommandHandler()
    try:
        while True:
            data = conn.recv(4096).decode('utf-8')
            if not data: break
            cmd = json.loads(data)
            response = handler.handle(cmd, addr)
            conn.sendall((json.dumps(response) + "\n").encode('utf-8'))
    except Exception as e:
        log.error(f"❌ Error handling client {addr}: {e}")
    finally:
        conn.close()

def main():
    #  R1: TCP Socket เชื่อมต่อระหว่าง Client-Server
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # แก้ไขปัญหา Address already in use
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind(('0.0.0.0', 9999))
        server.listen(50)
        log.info("🚌 Server ระบบรถเมล์ V2 พร้อมใช้งาน (Port 9999)")
        while True:
            conn, addr = server.accept()
            #  R4: นายภูมมินทร์ดูแลส่วน Threading
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    except Exception as e:
        log.critical(f"💥 ไม่สามารถเริ่ม Server ได้: {e}")
    finally:
        server.close()

if __name__ == "__main__":
    main()