# task3_asyncio_echo.py
import asyncio
from http import server
HOST = '0.0.0.0'
PORT = 9002

async def handle_client(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f'[+] Connected: {addr}')
    
    try:
        while True:
            # TODO: อ่าน data จาก reader (1024 bytes)
            data = await reader.read(1024)
            # TODO: ถา้ data ว่าง → break
            if not data:
                break
            # TODO: เขยีน data กลบัไป writer
            writer.write(data)
            # TODO: await writer.drain()
            await writer.drain()
 
    except Exception as e:
        print(f'[!] Error: {e}')
    finally:
        print(f'[-] Disconnected: {addr}')
        # TODO: ปิด writer + await wait_closed()
        writer.close()
        try:
            await writer.wait_closed()
        except Exception as e:
            pass # Already closed

async def main():
    server = await asyncio.start_server(handle_client, HOST, PORT)
    print(f'[SERVER] Asyncio Echo running on {HOST}:{PORT}')
    async with server:
        await server.serve_forever()

asyncio.run(main())