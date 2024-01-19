import socketio
import socketio_pg_manager

client_manager = socketio_pg_manager.AsyncPgManager(
    pg_options=dict(user="postgres", password="postgres")
)
sio = socketio.AsyncServer(async_mode="aiohttp", client_manager=client_manager)
