import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

EMAIL = 'B6803612@g.sut.ac.th'
PASS = 'isls yxuv zdtb tomy'  # App Password จาก Gmail

def send_email(to, subject, body):
    msg = MIMEMultipart()
    msg['From'] = EMAIL
    msg['To'] = to
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
        s.login(EMAIL, PASS)
        s.sendmail(EMAIL, to, msg.as_string())
        print('Email sent!')
    
# TODO: เรียกใช้ send_email() ส่งหา email ตัวเอง
send_email('B6803612@g.sut.ac.th',
           'Test Email',
           'สวัสดีครับ นี่คือการทดสอบส่งอีเมลจาก Python สำเร็จแล้วครับ!')