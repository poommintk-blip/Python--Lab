import asyncio
import requests
from datetime import datetime


seq_counter = 0


def fetch_btc_price() -> str:
    """Fetch ราคา BTC จาก CoinGecko API (blocking)"""
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": "bitcoin", "vs_currencies": "usd"}

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        price = data["bitcoin"]["usd"]
        return f"{price:,.2f}"
    except requests.exceptions.Timeout:
        return "N/A"
    except requests.exceptions.HTTPError:
        return "N/A"
    except requests.exceptions.RequestException:
        return "N/A"
    except (KeyError, ValueError):
        return "N/A"


def send_email_dry_run(seq: int, message: str, btc_price: str,
                       timestamp: str):
    """Mode B: Print แทนส่ง email จริง"""
    print(f"[EMAIL DRY-RUN] To: admin@example.com")
    print(f"Subject: Alert Notification #{seq}")
    print(f"Body:")
    print(f"  Message: {message}")
    print(f"  BTC: ${btc_price}")
    print(f"  Time: {timestamp}")


def write_log(seq: int, btc_price: str, message: str, timestamp: str):
    """เขียน log ลงไฟล์ alerts.log"""
    log_line = (
        f"{timestamp} | seq={seq} | btc={btc_price} | msg={message}\n"
    )
    with open("alerts.log", "a", encoding="utf-8") as f:
        f.write(log_line)


async def handle_client(reader: asyncio.StreamReader,
                        writer: asyncio.StreamWriter):
    """จัดการ client แต่ละคน"""
    global seq_counter

    addr = writer.get_extra_info("peername")
    print(f"[+] Connected: {addr}")

    try:
        while True:
            data = await reader.read(4096)
            if not data:
                break

            message = data.decode("utf-8").strip()

            if not message:
                continue

            # ตรวจสอบว่าขึ้นต้นด้วย 'ALERT:'
            if not message.startswith("ALERT:"):
                writer.write("INVALID\n".encode("utf-8"))
                await writer.drain()
                continue

            # Parse message
            alert_msg = message[len("ALERT:"):].strip()

            # เพิ่ม sequence
            seq_counter += 1
            seq = seq_counter

            print(f"[{seq}] Processing: {alert_msg}")

            # Fetch BTC price (wrap ด้วย asyncio.to_thread)
            btc_price = await asyncio.to_thread(fetch_btc_price)
            print(f"[{seq}] BTC: ${btc_price}")

            # Timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # ส่ง email (dry-run, wrap ด้วย asyncio.to_thread)
            await asyncio.to_thread(
                send_email_dry_run, seq, alert_msg, btc_price, timestamp
            )
            print(f"[{seq}] Email sent (dry-run)")

            # เขียน log
            await asyncio.to_thread(
                write_log, seq, btc_price, alert_msg, timestamp
            )
            print(f"[{seq}] Logged to alerts.log")

            # ตอบกลับ client
            response = f"OK {seq}\n"
            writer.write(response.encode("utf-8"))
            await writer.drain()

    except (ConnectionResetError, BrokenPipeError,
            asyncio.IncompleteReadError):
        pass
    finally:
        print(f"[-] Disconnected: {addr}")
        writer.close()
        await writer.wait_closed()


async def main():
    server = await asyncio.start_server(
        handle_client, "127.0.0.1", 9700
    )
    print("[NOTIFICATION] Listening on 127.0.0.1:9700")

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())