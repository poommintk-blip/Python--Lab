import paramiko

# ข้อมูลการเชื่อมต่อ [cite: 479, 498-502]
SSH_HOST = 'digilab.sut.ac.th'
SSH_PORT = 2222
SSH_USER = 'student51' # เปลี่ยนเป็น username ของคุณ (เช่น student01-75) [cite: 501]
SSH_PASS = 'yoi7UGygDAqO3z'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(SSH_HOST, port=SSH_PORT,username=SSH_USER, password=SSH_PASS)
commands = ['hostname', 'whoami', 'df -h']

for cmd in commands:
    stdin, out, stderr = client.exec_command(cmd)
    print(f'=== {cmd} ===')
    print(out.read().decode().strip())
    
client.close()