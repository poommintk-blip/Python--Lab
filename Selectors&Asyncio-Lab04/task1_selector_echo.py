import socket
import selectors

HOST = '0.0.0.0'
PORT = 9000

sel = selectors.DefaultSelector() 

def accept(sock, mask):
    conn, addr = sock.accept()
    print(f' [+] Connected: {addr}')
    # ตั้งค่าเป็น non-blocking socket 
    conn.setblocking(False) 
    # register conn ใน selector ด้วย EVENT_READ และ callback read 
    sel.register(conn, selectors.EVENT_READ, read)

def read(conn, mask):
    try:
        data = conn.recv(1024)
        if data:
            # echo data กลับไปหา client 
            conn.sendall(data)
        else:
            # เมื่อ client disconnect ต้อง unregister และ close 
            print(f' [-] Closing connection')
            sel.unregister(conn)
            conn.close()
    except Exception as e:
        print(f' [!] Error: {e}')
        sel.unregister(conn)
        conn.close()

# Setup server socket
server = socket.socket()
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen()
# server socket ต้อง setblocking(False) 
server.setblocking(False)

# register server socket เพื่อรอรับการเชื่อมต่อใหม่
sel.register(server, selectors.EVENT_READ, accept) 
print(f' [SERVER] Selector Echo running on {HOST}:{PORT}')
print(f' [SERVER] Press Ctrl+C to stop')

# Event Loop 
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