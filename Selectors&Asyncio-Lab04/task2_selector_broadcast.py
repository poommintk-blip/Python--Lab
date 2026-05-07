import socket
import selectors

HOST = '0.0.0.0'
PORT = 9001

sel = selectors.DefaultSelector()
clients = set() # เก็บ client socket ทั้งหมด [cite: 18]

def accept(sock, mask):
    conn, addr = sock.accept()
    print(f' [+] Connected: {addr}')
    conn.setblocking(False)
    sel.register(conn, selectors.EVENT_READ, read)
    # เพิ่ม conn เข้า clients set [cite: 25]
    clients.add(conn)

def read(conn, mask):
    try:
        data = conn.recv(1024)
        if data:
            addr = conn.getpeername()
            msg = f'{addr}: {data.decode()}'
            print(f' [*] Broadcast: {msg}')
            # broadcast ข้อความให้ทุกคน ยกเว้น sender [cite: 18]
            for client in clients:
                if client is not conn:
                    try:
                        client.sendall(msg.encode())
                    except:
                        pass
        else:
            disconnect(conn)
    except Exception:
        disconnect(conn)

def disconnect(conn):
    try:
        print(f' [-] Disconnected: {conn.getpeername()}')
    except:
        print(f' [-] Disconnected')
    # ลบ conn ออกจาก clients, unregister และ close [cite: 25]
    if conn in clients:
        clients.remove(conn)
    sel.unregister(conn)
    conn.close()

# Setup server socket + event Loop
server = socket.socket()
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen()
server.setblocking(False)
sel.register(server, selectors.EVENT_READ, accept)

print(f' [SERVER] Selector Broadcast running on {HOST}:{PORT}')
try:
    while True:
        events = sel.select()
        for key, mask in events:
            callback = key.data
            callback(key.fileobj, mask)
except KeyboardInterrupt:
    print("\n [SERVER] Shutting down...")
finally:
    sel.close()