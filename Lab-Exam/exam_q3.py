import socket
import threading
from concurrent.futures import ThreadPoolExecutor


# Global state
clients = {}  # conn -> username
clients_lock = threading.Lock()


def broadcast(message: str, exclude=None):
    """ส่งข้อความไปยัง client ทุกคน"""
    with clients_lock:
        for conn in list(clients.keys()):
            if conn == exclude:
                continue
            try:
                conn.sendall(message.encode("utf-8"))
            except Exception:
                pass


def broadcast_all(message: str):
    """ส่งข้อความไปยัง client ทุกคน (รวมตัวเอง)"""
    with clients_lock:
        for conn in list(clients.keys()):
            try:
                conn.sendall(message.encode("utf-8"))
            except Exception:
                pass


def handle_client(conn: socket.socket, addr):
    """จัดการ client แต่ละคน"""
    try:
        # ขอ username
        conn.sendall("Enter username: ".encode("utf-8"))
        username = conn.recv(1024).decode("utf-8").strip()

        if not username:
            conn.close()
            return

        # เพิ่มเข้า clients dict
        with clients_lock:
            clients[conn] = username

        # broadcast join
        join_msg = f"*** {username} joined the chat ***\n"
        broadcast_all(join_msg)

        # ลูปรับข้อความ
        while True:
            data = conn.recv(4096)
            if not data:
                break

            message = data.decode("utf-8").strip()

            if not message:
                continue

            if message == "/quit":
                break

            elif message == "/who":
                with clients_lock:
                    online = ", ".join(clients.values())
                conn.sendall(f"Online: {online}\n".encode("utf-8"))

            else:
                # broadcast ข้อความปกติ
                chat_msg = f"{username}: {message}\n"
                broadcast_all(chat_msg)

    except (ConnectionResetError, BrokenPipeError, OSError):
        pass
    finally:
        # ลบ client และ broadcast leave
        with clients_lock:
            username = clients.pop(conn, None)

        if username:
            leave_msg = f"*** {username} left the chat ***\n"
            broadcast_all(leave_msg)

        try:
            conn.close()
        except Exception:
            pass


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 9500))
    server.listen(10)

    print("[SERVER] Chat server running on 127.0.0.1:9500")

    with ThreadPoolExecutor(max_workers=10) as executor:
        while True:
            conn, addr = server.accept()
            print(f"[+] Connected: {addr}")
            executor.submit(handle_client, conn, addr)


if __name__ == "__main__":
    main()