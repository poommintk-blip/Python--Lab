# task1_selector_echo.py
import socket
import selectors
from t2 import disconnect

HOST = '0.0.0.0'
PORT = 9000

sel = selectors.DefaultSelector()

def accept(sock, mask):
    conn, addr = sock.accept()
    print(f'[+] Connected: {addr}')
    # TODO: setblocking(False) ให้ conn
    conn.setblocking(False)
    # TODO: register conn เขา้ selector ดว้ย EVENT_READ → callback read
    sel.register(conn, selectors.EVENT_READ, read)

def read(conn, mask):
    try:
        data = conn.recv(1024)
        if data:
            # TODO: echo data กลบัไปหา client
                conn.sendall(data)
        else:
            # TODO: unregister + close
            sel.unregister(conn)
            disconnect(conn)
    except Exception:
        # TODO: handle error — unregister + close
        sel.unregister(conn)
        conn.close()
        print(f'[-] Disconnected: {conn.getpeername()}')  

# Setup server socket
server = socket.socket()
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen()
server.setblocking(False)

sel.register(server, selectors.EVENT_READ, accept)
print(f'[SERVER] Selector Echo running on {HOST}:{PORT}')

# Event loop
while True:
    for key, mask in sel.select():
        callback = key.data
        callback(key.fileobj, mask)