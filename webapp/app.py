try:
    import eventlet
    eventlet.monkey_patch()
except Exception:
    pass

from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room
import time
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'openchat-secret'
# Use eventlet for production-style concurrency; install via requirements.txt
# To synchronize state across multiple running instances (so rooms/users are shared),
# set the REDIS_URL environment variable (e.g. redis://localhost:6379/0) and a
# Redis server must be reachable. Flask-SocketIO will use it as a message queue.
redis_url = os.environ.get('REDIS_URL')
if redis_url:
    socketio = SocketIO(app, cors_allowed_origins='*', async_mode='eventlet', message_queue=redis_url)
else:
    socketio = SocketIO(app, cors_allowed_origins='*', async_mode='eventlet')

# Simple in-memory state
SID_TO_USER = {}      # sid -> username
USER_TO_SID = {}      # username -> sid
ROOMS = {}            # room -> set(usernames)


def make_uuid(username: str) -> str:
    ts = str(int(time.time() * 10**6))
    return f"{username.strip()}_{ts[-6:]}"


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('connect')
def handle_connect():
    emit('server_msg', 'Welcome! Set your username with `set_username` event')
    socketio.emit('user_list', list(USER_TO_SID.keys()))
    socketio.emit('rooms', list(ROOMS.keys()))


from flask import request

@socketio.on('set_username')
def handle_set_username(data):
    username = data.get('username', '').strip()
    if not username:
        emit('error', 'Username cannot be empty')
        return
    # prevent duplicate usernames
    if username in USER_TO_SID:
        emit('error', 'Username already taken')
        return
    sid = request.sid
    SID_TO_USER[sid] = username
    USER_TO_SID[username] = sid
    emit('welcome', {'username': username})
    socketio.emit('user_list', list(USER_TO_SID.keys()), broadcast=True)


@socketio.on('list_rooms')
def handle_list_rooms():
    emit('rooms', list(ROOMS.keys()))


@socketio.on('create_room')
def handle_create_room(data):
    name = data.get('room')
    if not name:
        emit('error', 'Room name required')
        return
    if name in ROOMS:
        emit('error', f'Room {name} already exists')
        return
    ROOMS[name] = set()
    socketio.emit('rooms', list(ROOMS.keys()), broadcast=True)


@socketio.on('join_room')
def handle_join_room(data):
    name = data.get('room')
    if name not in ROOMS:
        emit('error', f'Chatroom [{name}] does not exist')
        return
    from flask import request
    sid = request.sid
    user = SID_TO_USER.get(sid)
    if not user:
        emit('error', 'Set username first')
        return
    ROOMS[name].add(user)
    join_room(name)
    emit('joined', {'room': name})
    socketio.emit('room_msg', {'room': name, 'msg': f'{user} joined chatroom'}, room=name)


@socketio.on('leave_room')
def handle_leave_room(data):
    name = data.get('room')
    from flask import request
    sid = request.sid
    user = SID_TO_USER.get(sid)
    if name in ROOMS and user in ROOMS[name]:
        ROOMS[name].remove(user)
        leave_room(name)
        socketio.emit('room_msg', {'room': name, 'msg': f'{user} left chatroom'}, room=name)


@socketio.on('send_message')
def handle_send_message(data):
    room = data.get('room')
    message = data.get('message')
    from flask import request
    sid = request.sid
    user = SID_TO_USER.get(sid, 'unknown')
    if room and room in ROOMS:
        socketio.emit('room_msg', {'room': room, 'msg': f'{user}: {message}'}, room=room)
    else:
        emit('error', 'Room not found')


@socketio.on('direct_message')
def handle_direct_message(data):
    target = data.get('target')
    message = data.get('message')
    from flask import request
    sid = request.sid
    src = SID_TO_USER.get(sid)
    if not src:
        emit('error', 'Set username first')
        return
    target_sid = USER_TO_SID.get(target)
    if not target_sid:
        emit('error', f'User {target} not found')
        return
    socketio.emit('private_msg', {'from': src, 'msg': message}, room=target_sid)


@socketio.on('disconnect')
def handle_disconnect():
    from flask import request
    sid = request.sid
    user = SID_TO_USER.pop(sid, None)
    if user:
        USER_TO_SID.pop(user, None)
        # remove from rooms
        for room, members in list(ROOMS.items()):
            if user in members:
                members.remove(user)
                socketio.emit('room_msg', {'room': room, 'msg': f'User {user} has left the room'}, room=room)
        socketio.emit('user_list', list(USER_TO_SID.keys()), broadcast=True)


if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    # If UI_ONLY is set, run only the Flask UI (no Socket.IO background service).
    # This is useful for testing the web UI without socket features.
    if os.environ.get('UI_ONLY') == '1':
        app.run(host='0.0.0.0', port=port, debug=True)
    else:
        # Prefer eventlet WSGI server for websocket support when available.
        try:
            import eventlet
            import eventlet.wsgi

            eventlet.monkey_patch()
            eventlet.wsgi.server(eventlet.listen(('0.0.0.0', port)), app)
        except Exception:
            # Fallback to socketio.run which may select a different server.
            socketio.run(app, host='0.0.0.0', port=port, debug=True)
