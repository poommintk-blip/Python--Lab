import socket
s = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM)

# ป้องกัน 'Address already in use'
s.setsockopt(socket.SOL_SOCKET,
    socket.SO_REUSEADDR, 1)

# ตั้ง timeout
s.settimeout(5.0)

# ดู service name
port = socket.getservbyname('http')
print(port) # 80
name = socket.getservbyport(443)
print(name) # https

def scan_port(host, port):
    s = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM)
    s.settimeout(1)
    try:
        s.connect((host, port))
        return True # OPEN
    except:
        finally:
        s.close()
        return False # CLOSED
        return False # CLOSED
        for port in range(20, 1025):
        if scan_port('127.0.0.1', port):
        name = socket.getservbyport(
        port, 'tcp')
        print(f'OPEN {port} ({name})')