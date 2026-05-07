import asyncio

HOST = '0.0.0.0'
PORT = 9002

async def handle_client(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f' [+] Connected: {addr}')
    try:
        while True:
            # อ่าน data จาก reader (1024 bytes) 
            data = await reader.read(1024) 
            if not data: 
                break
            # เขียน data กลับไปหา client 
            writer.write(data)
            await writer.drain() 
    except Exception as e:
        print(f' [!] Error: {e}')
    finally:
        print(f' [-] Disconnected: {addr}')
        # ปิด connection [
        writer.close()
        await writer.wait_closed() [cite: 37]

async def main():
    # ใช้ asyncio.start_server [cite: 37]
    server = await asyncio.start_server(handle_client, HOST, PORT)
    print(f' [SERVER] Asyncio Echo running on {HOST}:{PORT}')
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n [SERVER] Stopped")