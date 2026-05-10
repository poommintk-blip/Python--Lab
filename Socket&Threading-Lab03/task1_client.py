import socket

HOST = '127.0.0.1'
PORT = 9000
MESSAGES = ['Hello Server!', 'How are you?', 'Goodbye!']

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    
    # แสดงผลหัวข้อตามรูป
    print("=== TCP Echo Test ===")

    for msg in MESSAGES:
        # ส่งข้อมูล
        s.sendall(msg.encode())
        print(f"Sent:      {msg}") # เว้นวรรคให้ตรงตามรูป
        
        # รับข้อมูลกลับ
        data = s.recv(1024)
        print(f"Received:  {data.decode()}") # เว้นวรรคให้ตรงตามรูป

# เมื่อรันเสร็จ โปรแกรมจะจบการทำงานตามรูป