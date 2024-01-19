Socket PG Manager
===============

Postgres client manager for [python-socketio](https://python-socketio.readthedocs.io/).

# Install

```bash
python3 -m pip install -r socketio-pg-manager
```

# Usage

## Asynchronous Usage

When you are using `python-socketio` and you have multiple instances of your socketio server, simply pass `AsyncPgManager` to the constructor of `AsyncServer` 

```python
import socketio
import socketio_pg_manager

client_manager = socketio_pg_manager.AsyncPgManager(
    pg_options=dict(user="postgres", password="postgres")
)
sio = socketio.AsyncServer(async_mode="aiohttp", client_manager=client_manager)
```

For details, see [Using a Message Queue](https://python-socketio.readthedocs.io/en/stable/server.html#using-a-message-queue).

## Synchronous Usage

Not available now.

# How it works

`AsyncPgManager` is an implementation subtyping to `AsyncPubSubManager` of `python-socketio`. It creates a connection to your postgres database and listens on `LISTEN channel`, and publish any data using `NOTIFY channel, payload`.
