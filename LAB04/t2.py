import socket
import selectors

HOST = '0.0.0.0'
PORT = 9001

sel = selectors.DefaultSelector()
clients = set()  # Store all active client sockets

def accept(sock, mask):
    conn, addr = sock.accept()
    print(f'[+] Connected: {addr}')
    conn.setblocking(False)
    
    # Register for reading
    sel.register(conn, selectors.EVENT_READ, read)
    
    # TODO: Add conn to clients list when they join
    clients.add(conn)

def read(conn, mask):
    try:
        data = conn.recv(1024)
        if data:
            addr = conn.getpeername()
            msg = f'[{addr}] {data.decode().strip()}'
            print(f"Broadcasting: {msg}")
            
            # TODO: Broadcast msg to every client except the sender
            for client in list(clients):
                if client is not conn:
                    try:
                        client.sendall(msg.encode() + b'\n')
                    except Exception:
                        disconnect(client)
        else:
            disconnect(conn)
    except Exception:
        disconnect(conn)

def disconnect(conn):
    # Try to get the address before closing for a better log message
    try:
        addr = conn.getpeername()
        print(f'[-] Disconnected: {addr}')
    except:
        print(f'[-] Disconnected: unknown')

    # TODO: Remove from set and unregister
    clients.discard(conn)
    try:
        sel.unregister(conn)
    except Exception:
        pass # Already unregistered
    conn.close()

# --- TODO: Setup Server Socket ---
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen()
server.setblocking(False)

sel.register(server, selectors.EVENT_READ, accept)
print(f'[SERVER] Broadcast Hub running on {HOST}:{PORT}')

# --- TODO: Event Loop ---
try:
    while True:
        events = sel.select(timeout=None)
        for key, mask in events:
            callback = key.data
            callback(key.fileobj, mask)
except KeyboardInterrupt:
    print("\n[SERVER] Shutting down.")
finally:
    sel.close()