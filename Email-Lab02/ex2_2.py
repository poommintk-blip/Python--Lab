import imaplib
import email
from email.header import decode_header, make_header

EMAIL = 'poommin.tk@gmail.com'
PASS = 'uvta yuyz ylah ovws'  # App Password จาก Gmail


def decode_str(value):
    """decode encoded header ให้เป็น string ปกติ"""
    return str(make_header(decode_header(value or '')))

def get_body(msg):
    """ดึง plain text body จาก email (handle multipart) [cite: 595, 596]"""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type() 
            if ctype == 'text/plain' and 'attachment' not in str(part.get('Content-Disposition')):
                charset = part.get_content_charset() or 'utf-8' 
                return part.get_payload(decode=True).decode(charset, errors='replace')
    else:
        charset = msg.get_content_charset() or 'utf-8'
        return msg.get_payload(decode=True).decode(charset, errors='replace')
    return ''

mail = imaplib.IMAP4_SSL('imap.gmail.com')
mail.login(EMAIL, PASS)
mail.select('inbox') 

_, ids = mail.search(None, 'UNSEEN')
nums = ids[0].split()
print(f'UNSEEN: {len(nums)} emails')

for i, num in enumerate(nums, 1):
    _, md = mail.fetch(num, '(RFC822)') 
    msg = email.message_from_bytes(md[0][1]) 
    print(f'--- Email {i} ---') 
    
    print(f'From: {decode_str(msg["From"])}')
    print(f'Subject: {decode_str(msg["Subject"])}')
    print(f'Body: {get_body(msg)[:200]}') 
    
    
    mail.store(num, '+FLAGS', '\\Seen')
    
mail.logout() [cite: 518, 627]