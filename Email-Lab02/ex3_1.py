import paramiko

# ข้อมูลการเชื่อมต่อ 
SSH_HOST = 'digilab.sut.ac.th'
SSH_PORT = 2222
SSH_USER = 'student51' # เปลี่ยนเป็น username ของคุณ (เช่น student01-75) 
SSH_PASS = 'i7UGygDAqO3z' # เปลี่ยนเป็น password ของคุณ

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(SSH_HOST, port=SSH_PORT, username=SSH_USER, password=SSH_PASS, timeout=10)

for cmd in ['hostname', 'whoami', 'df -h']:
    _, out, stderr = client.exec_command(cmd)
    print(f'=== {cmd} ===')
    print(out.read().decode().strip())
    
client.close()
