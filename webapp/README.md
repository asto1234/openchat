Openchat Web UI

This folder contains a minimal Flask + Socket.IO web UI that integrates the chat server logic.

Quick start

1. Install dependencies (prefer a virtualenv):

```bash
pip install -r requirements.txt
```

2. Run the web app:

```bash
python -m webapp.app
```

3. Open http://localhost:5000 in your browser.

Notes
- This in-memory implementation is for demonstration. For production, persist state and run behind a proper WSGI server.
- The web UI uses Socket.IO; it's integrated into the Flask process rather than the earlier raw TCP server. You can adapt the existing `server.py` to bridge TCP<->Socket.IO if you prefer separate backends.
 
Scaling across multiple instances (share rooms/users)

By default each Flask instance keeps in-memory state, so two separate instances (different ports) will not share rooms or user lists. To have multiple instances share state you can run a Redis server and set the `REDIS_URL` environment variable before starting each instance. Example using Docker:

```bash
# run Redis (Docker)
docker run -d -p 6379:6379 --name openchat-redis redis:7

# start instance 1
REDIS_URL=redis://localhost:6379/0 python webapp/app.py 5000

# start instance 2
REDIS_URL=redis://localhost:6379/0 python webapp/app.py 5001
```

With `REDIS_URL` set, Flask-SocketIO uses Redis as a message queue so events (rooms, user list, messages) propagate between instances.
