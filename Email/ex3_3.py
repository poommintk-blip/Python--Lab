import ftplib

FTP_HOST = 'digilab.sut.ac.th'
FTP_PORT = 2121
SSH_USER = 'student51'
SSH_PASS = 'yoi7UGygDAqO3z' 

with open('ftp_test.txt', 'w') as f:
    f.write(f'FTP upload from {SSH_USER}\n')

ftp = ftplib.FTP()
ftp.connect(FTP_HOST, FTP_PORT)

ftp.login(SSH_USER, SSH_PASS)
print('FTP connected')

ftp.cwd('upload/')

with open('ftp_test.txt', 'rb') as f:
    ftp.storbinary('STOR ftp_test.txt', f)

print('FTP upload OK: ftp_test.txt')

ftp.quit()