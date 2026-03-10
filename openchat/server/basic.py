import asyncio
import logging
import socket
import time

_BUFF_SIZE = 4096
logger = logging.getLogger(__name__)
FORMAT = '%(asctime)s - %(message)s'
logging.basicConfig(filename='myapp.log', level=logging.INFO, format=FORMAT)

# Protocol: 4-byte big-endian length prefix followed by UTF-8 payload
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
    message = data.decode('utf-8', errors='ignore')
    return message

async def send_message(writer: asyncio.StreamWriter, message: str):
    if message is None:
        message = ""
    data = message.encode('utf-8')
    header = len(data).to_bytes(4, 'big')
    writer.write(header + data)
    await writer.drain()


# Server state
USERS = {}  # uuid -> writer
CHATROOMS = {}  # room -> set(uuid)

def make_uuid(username: str) -> str:
    ts = str(int(time.time() * 10**6))
    return f"{username.strip()}_{ts[-6:]}"

class ChatServer:
    async def handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        peer = writer.get_extra_info('peername')
        try:
            await send_message(writer, "Choose a username:")
            username = await recv_message(reader)
            if not username:
                writer.close()
                await writer.wait_closed()
                return
            uuid = make_uuid(username)
            # ensure unique
            while uuid in USERS:
                uuid = make_uuid(username)
            USERS[uuid] = writer
            await send_message(writer, f"Welcome {uuid}!")
            logger.info(f"User connected: {uuid} from {peer}")
            # run client handler
            await self.client_loop(uuid, reader, writer)
        except Exception as e:
            logger.exception("Error handling connection")
        finally:
            # cleanup
            for room in list(CHATROOMS.keys()):
                if uuid in CHATROOMS[room]:
                    CHATROOMS[room].remove(uuid)
                    await self.broadcast(room, f"User {uuid} has left the room")
            USERS.pop(uuid, None)
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    async def client_loop(self, uuid: str, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        while True:
            msg = await recv_message(reader)
            if not msg:
                break
            logger.info(f"Received from {uuid}: {msg}")
            # Commands start with --
            if msg == "--list_rooms":
                rooms = "\n".join(CHATROOMS.keys()) or "No active chatrooms"
                await send_message(writer, rooms)
            elif msg.startswith("--create_room "):
                name = msg.split(" ", 1)[1]
                await self.create_room(name)
            elif msg.startswith("--join_room "):
                name = msg.split(" ", 1)[1]
                await self.join_room(uuid, name, writer)
            elif msg.startswith("--show_users "):
                name = msg.split(" ", 1)[1]
                users = CHATROOMS.get(name, set())
                await send_message(writer, "\n".join(users) or "No users")
            elif msg == "--close":
                await send_message(writer, "Goodbye")
                break
            elif msg.startswith("--msg "):
                # direct message --msg user_uuid message
                parts = msg.split(" ", 2)
                if len(parts) >= 3:
                    target, body = parts[1], parts[2]
                    await self.direct_message(uuid, target, body)
                else:
                    await send_message(writer, "Invalid direct message format")
            else:
                # treat as broadcast to all rooms that user is part of
                for room, members in CHATROOMS.items():
                    if uuid in members:
                        await self.broadcast(room, f"{uuid}: {msg}", exclude=uuid)

    async def create_room(self, name: str):
        if name in CHATROOMS:
            # announce
            for w in USERS.values():
                await send_message(w, f"Chatroom {name} already exists")
        else:
            CHATROOMS[name] = set()
            for w in USERS.values():
                await send_message(w, f"{name} chatroom is created")

    async def join_room(self, uuid: str, name: str, writer: asyncio.StreamWriter):
        if name not in CHATROOMS:
            await send_message(writer, f"Chatroom [{name}] does not exist")
            return
        members = CHATROOMS[name]
        if uuid in members:
            await send_message(writer, f"You are already in chatroom {name}")
            return
        members.add(uuid)
        await send_message(writer, f"Joined chatroom {name} successfully")
        await self.broadcast(name, f"{uuid} joined chatroom", exclude=uuid)

    async def broadcast(self, room: str, message: str, exclude: str = ""):
        members = CHATROOMS.get(room, set())
        for user in members:
            if user == exclude:
                continue
            w = USERS.get(user)
            if w:
                await send_message(w, message)

    async def direct_message(self, src: str, target: str, body: str):
        w = USERS.get(target)
        if w:
            await send_message(w, f"[PM]{src}: {body}")
        else:
            srcw = USERS.get(src)
            if srcw:
                await send_message(srcw, f"User {target} not found")


async def server(host: str, port: int):
    srv = ChatServer()
    server = await asyncio.start_server(srv.handle_connection, host=host, port=int(port), limit=_BUFF_SIZE)
    addr = ", ".join(str(sock.getsockname()) for sock in server.sockets)
    print(f"Server is running on {addr}")
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=12345)
    args = parser.parse_args()
    asyncio.run(server(args.host, args.port))
 

