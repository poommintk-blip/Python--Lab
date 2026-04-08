import socket

HOST = '127.0.0.1'
PORT = 9999

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

while True:
    msg = input("Enter message: ")
    client.send(msg.encode())

    response = client.recv(1024)
    print("Server:", response.decode())