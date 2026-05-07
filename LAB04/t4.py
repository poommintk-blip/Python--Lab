import asyncio

HOST = '0.0.0.0'
PORT = 9003
clients = {} # writer -> nickname [cite: 40, 50]

async def broadcast(message, sender=None): 
    dead_clients = []
    for writer in clients:
        if writer is sender:
            continue
        try:
            writer.write(message.encode())
            await writer.drain()
        except Exception:
            dead_clients.append(writer)
    
    # cleanup dead clients [cite: 41]
    for writer in dead_clients:
        if writer in clients:
            del clients[writer]

async def handle_client(reader, writer): 
    addr = writer.get_extra_info('peername')
    
    # รับ nickname จาก client [cite: 42]
    writer.write("Enter nickname: ".encode())
    await writer.drain()
    data = await reader.read(1024)
    if not data:
        writer.close()
        return
        
    nickname = data.decode().strip()
    # เพิ่มเข้า clients dict [cite: 42]
    clients[writer] = nickname
    
    # broadcast 'nickname joined!' [cite: 42, 50]
    print(f' [+] {nickname} connected from {addr}')
    await broadcast(f'{nickname} joined\n')
    
    try:
        while True:
            data = await reader.read(1024)
            if not data: 
                break
            # broadcast f'{nickname}: {data.decode()}' 
            msg = f'{nickname}: {data.decode()}'
            await broadcast(msg, sender=writer)
    finally:
        if writer in clients:
            nickname = clients[writer]
            del clients[writer]
            # broadcast 'nickname left' 
            print(f' [-] {nickname} disconnected')
            await broadcast(f'{nickname} left\n')
        
        writer.close()
        await writer.wait_closed() 

async def main():
    server = await asyncio.start_server(handle_client, HOST, PORT) 
    print(f' [CHAT SERVER] Asyncio Chat running on {HOST}:{PORT}')
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n [SERVER] Shutting down...")