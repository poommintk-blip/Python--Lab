import socket
import dns.resolver
import paramiko
import smtplib
import os
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# ข้อมูล Email (Part 1)
EMAIL = 'B6803612@sut.ac.th' # เปลี่ยนเป็น Email ของคุณ
EMAIL_PASS = 'isls yxuv zdtb tomy' # App Password 16 หลักของคุณ 

# ข้อมูล SSH/SFTP (Part 3)
SSH_HOST = 'digilab.sut.ac.th'
SSH_PORT = 2222
SSH_USER = 'student51' # เปลี่ยนเป็น Username ของคุณ 
SSH_PASS = 'i7UGygDAqO3z' # เปลี่ยนเป็น Password ของคุณ

def automated_monitor():
    # 1. รับชื่อ server และทำ DNS Lookup (Part 4) 
    target_server = input('Enter server to monitor: ')
    print(f'[DNS] Querying A record for {target_server}...')
    try:
        answers = dns.resolver.resolve(target_server, 'A')
        server_ip = str(answers[0])
        print(f'[DNS] Found IP: {server_ip}')
    except Exception as e:
        print(f'[DNS] Error: {e}')
        server_ip = "Unknown IP"

    # 2. SSH เข้า Server เพื่อรันคำสั่ง (Part 3) 
    print(f'[SSH] Connecting to {SSH_HOST}:{SSH_PORT}...')
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) 
        ssh.connect(SSH_HOST, port=SSH_PORT, username=SSH_USER, password=SSH_PASS, timeout=10) 
        print(f'[SSH] Connected to {SSH_HOST}')

        # รันคำสั่ง uptime และ df -h 
        _, stdout_uptime, _ = ssh.exec_command('uptime')
        uptime_res = stdout_uptime.read().decode().strip()
        
        _, stdout_df, _ = ssh.exec_command('df -h')
        df_res = stdout_df.read().decode().strip()
        print('[SSH] df -h and uptime collected') 

        # 3. บันทึกผลลงไฟล์ (Part 1.2) 
        filename = f'report_{SSH_USER}.txt'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"Automated Server Report\n") 
            f.write(f"Server: {target_server} ({server_ip})\n") 
            f.write(f"Report Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"[Uptime]\n{uptime_res}\n\n")
            f.write(f"[Disk Usage]\n{df_res}\n") 
        print(f'[FILE] Saved {filename}') 

        # 4. SFTP อัปโหลดไฟล์ไปเก็บเป็น Log (Part 3.2)
        sftp = ssh.open_sftp() 
        remote_path = f'upload/{filename}'
        sftp.put(filename, remote_path) 
        print(f'[SFTP] Uploaded {filename} to {remote_path}') 
        sftp.close()
        ssh.close()

        # 5. ส่ง Email แจ้ง Admin พร้อมแนบไฟล์ (Part 1.2) 
        msg = MIMEMultipart() 
        msg['From'] = EMAIL
        msg['To'] = EMAIL # ส่งหาตัวเองตามโจทย์ 
        msg['Subject'] = f'Server Report: {target_server}' 
        
        body = f"พบเอกสารรายงานเซิร์ฟเวอร์ประจำวันของ {target_server} อยู่ในไฟล์แนบ" 
        msg.attach(MIMEText(body, 'plain', 'utf-8')) 

        with open(filename, 'rb') as f:
            part = MIMEBase('application', 'octet-stream') 
            part.set_payload(f.read()) 
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{filename}"') 
            msg.attach(part) 

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server: 
            server.login(EMAIL, EMAIL_PASS) 
            server.sendmail(EMAIL, EMAIL, msg.as_string())
        print(f'[EMAIL] Report sent to {EMAIL}') 

    except Exception as e:
        print(f'Critical Error: {e}') 

if __name__ == "__main__":
    automated_monitor()
    print("Done.") 
