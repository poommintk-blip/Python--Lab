# task2_pool_client.py
import socket
import time

HOST, PORT = '127.0.0.1', 9001

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    for i in range(3):
        msg = f'Message {i+1} from client'
        s.sendall(msg.encode())
        
        # รับข้อมูลและแสดงผลตามฟอร์แมตในรูป
        response = s.recv(1024).decode()
        print(f"Echo: {response}")
        
        time.sleep(1)