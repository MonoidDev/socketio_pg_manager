import asyncio
import json
import traceback

import psycopg

from psycopg_pool import AsyncConnectionPool
from socketio.async_pubsub_manager import AsyncPubSubManager


class AsyncPgManager(AsyncPubSubManager):
    """Postgres based client manager for asyncio servers.

    This class implements a Postgres backend for event sharing across multiple
    processes.

    To use a Postgres backend, initialize the :class:`AsyncServer` instance as
    follows::

        server = socketio.AsyncServer(
            client_manager=socketio.AsyncPgManager('user=postgres password=postgres'))

    :param conninfo: The connection string (a postgresql:// url or a list of key=value pairs) to specify where and how to connect.
    :param pg_options: Additional keyword arguments to be passed to ``AsyncConnection.connect``
    :param channel: The channel name on which the server sends and receives
                    notifications. Must be the same in all the servers.
    :param write_only: If set to ``True``, only initialize to emit events. The
                       default of ``False`` initializes the class for emitting
                       and receiving.
    """

    name = "aiopg"

    def __init__(
        self,
        conninfo="",
        pg_options=None,
        channel="socketio",
        write_only=False,
        logger=None,
    ):
        if psycopg is None:
            raise RuntimeError(
                "Postgres package is not installed"
                '(Run "pip install psycopg" in your virtualenv).'
            )

        self.pg_options = pg_options or {}
        self.async_connection_pool = AsyncConnectionPool(conninfo, **self.pg_options, open=True)
        super().__init__(channel=channel, write_only=write_only, logger=logger)

    async def _publish(self, data):
        retry_count = 2

        for i in range(retry_count):
            try:
                async with self.async_connection_pool.connection() as aconn:
                    async with aconn.cursor() as acur:
                        await acur.execute(
                            f"SELECT pg_notify(%s, %s)",
                            (
                                self.channel,
                                json.dumps(data),
                            ),
                        )
                return
            except psycopg.OperationalError:
                self._get_logger().error(
                    f"Cannot publish to postgres..."
                    + (f"retrying {i + 1}" if i + 1 < retry_count else "giving up"),
                )
            except Exception as e:
                self._get_logger().error(
                    f"Cannot publish to postgres due to unknown error, giving up"
                )
                raise e

    async def _listen(self):
        retry_sleep = 1

        while True:
            try:
                async with self.async_connection_pool.connection() as aconn:
                    async with aconn.cursor() as acur:
                        await acur.execute(f"LISTEN {self.channel};")
                        await aconn.commit()
                        async for notify in aconn.notifies():
                            yield notify.payload
            except psycopg.OperationalError:
                self._get_logger().error(
                    "Cannot receive from postgres... "
                    "retrying in "
                    "{} secs".format(retry_sleep)
                )

                await asyncio.sleep(retry_sleep)

                retry_sleep *= 2
                if retry_sleep > 60:
                    retry_sleep = 60
                pass
            except:
                self._get_logger().error(
                    "Cannot listen due to error, aborting _listen."
                )
                traceback.print_exc()
                raise asyncio.CancelledError
