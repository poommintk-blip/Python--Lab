import asyncio

message_count = 0

async def handle_client(reader: asyncio.StreamReader,
                        writer: asyncio.StreamWriter):
    """จัดการ client แต่ละคน"""
    global message_count

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

            if message == "STATS":
                # ไม่นับรวมใน count
                response = f"Total messages: {message_count}\n"
                writer.write(response.encode("utf-8"))
                await writer.drain()
            else:
                # นับ message และ echo กลับ
                message_count += 1
                response = f"#{message_count}: {message}\n"
                writer.write(response.encode("utf-8"))
                await writer.drain()

    except (ConnectionResetError, BrokenPipeError, asyncio.IncompleteReadError):
        pass
    finally:
        print(f"[-] Disconnected: {addr}")
        writer.close()
        await writer.wait_closed()


async def main():
    server = await asyncio.start_server(
        handle_client, "127.0.0.1", 9600
    )
    print("[SERVER] Asyncio Echo Server running on 127.0.0.1:9600")

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())