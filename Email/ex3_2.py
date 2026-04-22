import paramiko

SSH_HOST = 'digilab.sut.ac.th'
SSH_PORT = 2222
SSH_USER = 'student51' 
SSH_PASS = 'yoi7UGygDAqO3z' 

with open('sftp_test.txt', 'w') as f:
    f.write(f'SFTP upload from {SSH_USER}\n')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(SSH_HOST, port=SSH_PORT, username=SSH_USER, password=SSH_PASS)

sftp = client.open_sftp()

sftp.put('sftp_test.txt', 'upload/sftp_test.txt')
print('SFTP upload OK: sftp_test.txt → upload/sftp_test.txt') 

files = sftp.listdir('upload/')
print(f'Files in upload/: {files}')

sftp.close()
client.close()