import ftplib

from ex3_2 import SSH_PASS, SSH_USER

FTP_HOST = 'digilab.sut.ac.th'
FTP_PORT = 2121
FTP_USER = 'student51'
FTP_PASS = 'i7UGygDAqO3z' 

with open('ftp_test.txt', 'w') as f:
    f.write(f'FTP upload from {FTP_USER}\n')

ftp = ftplib.FTP()
ftp.connect(FTP_HOST, FTP_PORT)

ftp.login(FTP_USER, FTP_PASS)
print('FTP connected')

ftp.cwd('upload/')

with open('ftp_test.txt', 'rb') as f:
    ftp.storbinary('STOR ftp_test.txt', f)

print('FTP upload OK: ftp_test.txt')

ftp.quit()