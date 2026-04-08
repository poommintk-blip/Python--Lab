import socket
import threading

HOST = '127.0.0.1'
PORT = 9999

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")

    while True:
        try:
            data = conn.recv(1024)
            if not data:
                break

            message = data.decode()
            print(f"[{addr}] {message}")

            # ตอบกลับ client
            response = f"Server received: {message}"
            conn.send(response.encode())

        except:
            break

    print(f"[DISCONNECTED] {addr}")
    conn.close()


# เริ่ม Server
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()

    print(f"[STARTED] Server running on {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()

        # สร้าง thread ใหม่
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")


if __name__ == "__main__":
    start_server()