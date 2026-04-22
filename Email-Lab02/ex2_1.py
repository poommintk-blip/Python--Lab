import imaplib, email
from email.header import decode_header, make_header

EMAIL = 'poommin.tk@gmail.com'
PASS = 'uvta yuyz ylah ovws'  # App Password จาก Gmail

def decode_str(value):
    """decode encoded header ให้เป็น string ปกติ"""
    return str(make_header(decode_header(value or '')))

mail = imaplib.IMAP4_SSL('imap.gmail.com')
mail.login(EMAIL, PASS)
mail.select('inbox')

_, data = mail.search(None, 'ALL')
ids = data[0].split()
latest5 = ids[-5:]

print('=== 5 latest emails ===')
for i, num in enumerate(reversed(latest5), 1):
    _, md = mail.fetch(num, '(RFC822)')
    msg = email.message_from_bytes(md[0][1])
    print(f'[{i}] From: {decode_str(msg["From"])}')
    print(f' Subject: {decode_str(msg["Subject"])}')
    print(f' Date: {msg["Date"]}')

mail.logout()