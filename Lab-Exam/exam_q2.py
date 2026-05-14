import smtplib
import imaplib
import email
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.header import decode_header, make_header


def main():
    # รับข้อมูลจาก input (ไม่ hardcode password)
    user_email = input("Enter your Gmail: ").strip()
    app_password = input("Enter your App Password: ").strip()

    # ==============================
    # ส่วนที่ 1: ส่ง Email พร้อม Attachment
    # ==============================
    print("[1/2] Creating exam_log.txt...")
    with open("exam_log.txt", "w", encoding="utf-8") as f:
        f.write("Network Programming Exam - ภูมมินทร์ ติคำรัมย์")

    print("[1/2] Sending email with attachment...")

    msg = MIMEMultipart()
    msg["From"] = user_email
    msg["To"] = user_email
    msg["Subject"] = "Exam Q2 Report"

    # Body เป็น HTML
    html_body = """
    <html>
    <body>
        <h2>Exam Q2 Report</h2>
        <p>This is the exam report for Network Programming course.</p>
        <p>Sent automatically by exam_q2.py</p>
    </body>
    </html>
    """
    msg.attach(MIMEText(html_body, "html"))

    # แนบไฟล์ exam_log.txt
    with open("exam_log.txt", "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        "attachment; filename=exam_log.txt"
    )
    msg.attach(part)

    # ส่งผ่าน SMTP_SSL
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(user_email, app_password)
        server.send_message(msg)

    print("[1/2] Email sent!")
    print()

    # ==============================
    # ส่วนที่ 2: อ่าน Email ด้วย IMAP
    # ==============================
    print("[2/2] Connecting to IMAP...")

    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(user_email, app_password)
    mail.select("INBOX")

    # ค้นหาด้วย SUBJECT
    status, messages = mail.search(None, 'SUBJECT "Exam Q2 Report"')

    if status != "OK" or not messages[0]:
        print("[2/2] No matching emails found.")
        mail.logout()
        return

    msg_ids = messages[0].split()
    print(f"[2/2] Found {len(msg_ids)} matching email(s)")

    # ดึง email ฉบับล่าสุด
    latest_id = msg_ids[-1]
    status, msg_data = mail.fetch(latest_id, "(RFC822)")

    raw_email = msg_data[0][1]
    email_msg = email.message_from_bytes(raw_email)

    # Decode subject
    subject = str(make_header(decode_header(email_msg["Subject"])))
    from_addr = str(make_header(decode_header(email_msg["From"])))
    date = email_msg["Date"]

    print(f"=== Latest Exam Q2 Report ===")
    print(f"From: {from_addr}")
    print(f"Subject: {subject}")
    print(f"Date: {date}")

    # Mark as Seen
    mail.store(latest_id, "+FLAGS", "\\Seen")
    print("[2/2] Marked as Seen")

    mail.logout()
    print()
    print("Done")


if __name__ == "__main__":
    main()