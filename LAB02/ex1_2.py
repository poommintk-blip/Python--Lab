import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

EMAIL = 'B6803612@g.sut.ac.th'
PASS = 'isls yxuv zdtb tomy'  # App Password จาก Gmail

# สร้างไฟล์ทดสอบ
with open('report.txt', 'w', encoding='utf-8') as f:
    f.write('Lab02 Report\nTimestamp: 2025-04-20\n')
    
msg = MIMEMultipart('mixed')
msg['From'] = EMAIL
msg['To'] = EMAIL
msg['Subject'] = 'Lab02 Report'

# HTML body
html = '''<html><body>
    <h2 style="color:#2E75B6">Lab02 Report</h2>
    <p>ดู report ในไฟล์แนบ</p>
</body></html>'''
msg.attach(MIMEText(html, 'html', 'utf-8'))

# Attachment
with open('report.txt', 'rb') as f:
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', 'attachment; filename="report.txt"')
    msg.attach(part)
    
# TODO: ส่งด้วย SMTP_SSL เหมือน 1.1
try:
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
        s.login(EMAIL, PASS)
        s.sendmail(EMAIL, EMAIL, msg.as_string())
    print('HTML Email with attachment sent!') 
    
except Exception as e:
    print(f'Error: {e}')