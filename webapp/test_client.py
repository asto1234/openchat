import argparse
import time
import socketio


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--username', '-u', default='bot_b')
    p.add_argument('--host', '-h', default='http://localhost')
    p.add_argument('--port', '-p', type=int, default=5000)
    p.add_argument('--room', '-r', default='room1')
    args = p.parse_args()

    url = f"{args.host}:{args.port}"
    sio = socketio.Client()


    @sio.event
    def connect():
        print(f"Connected to {url}")
        sio.emit('set_username', {'username': args.username})
        time.sleep(0.2)
        # create room if missing, then join
        sio.emit('create_room', {'room': args.room})
        time.sleep(0.2)
        sio.emit('join_room', {'room': args.room})
        time.sleep(0.2)
        sio.emit('send_message', {'room': args.room, 'message': f'Hello from {args.username}'})


    @sio.on('room_msg')
    def on_room_msg(data):
        print(f"[room_msg] {data}")


    @sio.on('rooms')
    def on_rooms(data):
        print(f"[rooms] {data}")


    @sio.on('user_list')
    def on_user_list(data):
        print(f"[users] {data}")


    @sio.event
    def disconnect():
        print('Disconnected')

    try:
        sio.connect(url)
    except Exception as e:
        print('Connection error:', e)
        return

    try:
        # run until interrupted, send a heartbeat message occasionally
        while True:
            time.sleep(10)
            sio.emit('send_message', {'room': args.room, 'message': f'ping from {args.username}'})
    except KeyboardInterrupt:
        print('Interrupted, disconnecting')
    finally:
        sio.disconnect()


if __name__ == '__main__':
    main()
