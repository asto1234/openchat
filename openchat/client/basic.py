import asyncio
import sys

_BUFF_SIZE = 4096

async def recv_message(reader: asyncio.StreamReader) -> str:
    try:
        header = await reader.readexactly(4)
    except (asyncio.IncompleteReadError, ConnectionResetError):
        return ""
    length = int.from_bytes(header, 'big')
    if length == 0:
        return ""
    try:
        data = await reader.readexactly(length)
    except (asyncio.IncompleteReadError, ConnectionResetError):
        return ""
    return data.decode('utf-8', errors='ignore')

async def send_message(writer: asyncio.StreamWriter, message: str):
    if message is None:
        message = ""
    data = message.encode('utf-8')
    header = len(data).to_bytes(4, 'big')
    writer.write(header + data)
    await writer.drain()

async def read_from_server(reader: asyncio.StreamReader):
    while True:
        msg = await recv_message(reader)
        if not msg:
            print("Connection closed by server")
            break
        print(f"[server] {msg}")

async def send_user_input(writer: asyncio.StreamWriter):
    try:
        while True:
            # Use blocking input in a thread to avoid blocking the event loop
            line = await asyncio.to_thread(input, ">")
            if not line:
                continue
            await send_message(writer, line)
            if line == "--close":
                break
    except (EOFError, KeyboardInterrupt):
        await send_message(writer, "--close")

async def client(host: str, port: int):
    reader, writer = await asyncio.open_connection(host, int(port))
    # receive greeting
    greeting = await recv_message(reader)
    if greeting:
        print(greeting)
    # send username
    username = await asyncio.to_thread(input, "Username: ")
    await send_message(writer, username)
    welcome = await recv_message(reader)
    if welcome:
        print(welcome)

    # start read and write tasks
    read_task = asyncio.create_task(read_from_server(reader))
    write_task = asyncio.create_task(send_user_input(writer))
    done, pending = await asyncio.wait([read_task, write_task], return_when=asyncio.FIRST_COMPLETED)
    for task in pending:
        task.cancel()
    try:
        writer.close()
        await writer.wait_closed()
    except Exception:
        pass


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python client.py <host> <port>")
        sys.exit(1)
    host = sys.argv[1]
    port = int(sys.argv[2])
    asyncio.run(client(host, port))
    