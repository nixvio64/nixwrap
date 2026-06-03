"""TCP client for Rocket League's Stats API.

Connects to the game's local JSON-over-TCP socket, parses events,
and dispatches them to registered callbacks or an async iterator.
"""

from __future__ import annotations

import asyncio
import json
import socket
import threading
import time
from typing import AsyncIterator, Callable

from nixwrap.stats._parser import parse_message, extract_json_objects
from nixwrap.stats._models import StatsEvent


class StatsClient:
    """Client for Rocket League's built-in Stats API.

    Connects to the local TCP socket that RL opens when
    PacketSendRate > 0 is configured in DefaultStatsAPI.ini.

    Supports callback-based and async-iterator-based consumption.

    Parameters
    host:
        IP address (default 127.0.0.1).
    port:
        Port (default 49123, RL's default).

    Usage (callbacks):

        client = StatsClient()
        client.on("GoalScored", lambda evt: print(f"Goal by {evt.scorer.name}!"))
        client.start()
        # ... app runs ...
        client.stop()

    Usage (async):

        client = StatsClient()
        client.start()
        async for event in client.events():
            print(event.event_type)
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 49123) -> None:
        self._host = host
        self._port = port
        self._sock: socket.socket | None = None
        self._running = False
        self._thread: threading.Thread | None = None

        # Callbacks
        self._general_callbacks: list[Callable[[StatsEvent], None]] = []
        self._typed_callbacks: dict[str, list[Callable]] = {}
        self._lock = threading.Lock()

        # Async
        self._async_queue: asyncio.Queue[StatsEvent] | None = None
        self._async_loop: asyncio.AbstractEventLoop | None = None

    # Connection management

    @property
    def connected(self) -> bool:
        return self._sock is not None and self._running

    def connect(self) -> None:
        """Blocking: open the TCP connection and perform the HTTP handshake."""
        self.disconnect()
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.settimeout(5)
        self._sock.connect((self._host, self._port))
        # RL Stats API expects a bare HTTP GET upgrade, not WebSocket
        self._sock.sendall(
            b"GET / HTTP/1.1\r\n"
            b"Host: localhost\r\n"
            b"Connection: keep-alive\r\n"
            b"\r\n"
        )
        self._sock.settimeout(None)  # back to blocking for recv

    def disconnect(self) -> None:
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None
        self._running = False

    def start(self) -> None:
        """Start the background reader thread.

        Automatically connects if not already connected.
        """
        if self._running:
            return
        if not self._sock:
            self.connect()
        self._running = True
        self._thread = threading.Thread(target=self._reader_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the reader thread and disconnect."""
        self._running = False
        self.disconnect()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    # Callback registration

    def on_event(self, callback: Callable[[StatsEvent], None]) -> None:
        """Register a callback for *all* event types."""
        with self._lock:
            self._general_callbacks.append(callback)

    def on(self, event_type: str,
           callback: Callable[[StatsEvent], None]) -> None:
        """Register a callback for a specific event type.

        Example: client.on("GoalScored", my_handler)
        """
        with self._lock:
            self._typed_callbacks.setdefault(event_type, []).append(callback)

    # Async iteration

    async def events(self) -> AsyncIterator[StatsEvent]:
        """Async iterator over incoming Stats API events.

        Requires start() to be called first.
        """
        self._async_loop = asyncio.get_running_loop()
        self._async_queue = asyncio.Queue()
        try:
            while self._running:
                try:
                    event = await self._async_queue.get()
                    yield event
                except asyncio.CancelledError:
                    break
        finally:
            self._async_queue = None
            self._async_loop = None

    async def __aiter__(self) -> AsyncIterator[StatsEvent]:
        async for event in self.events():
            yield event

    # Context manager

    def __enter__(self) -> StatsClient:
        self.start()
        return self

    def __exit__(self, *args) -> None:
        self.stop()

    # Internals

    def _reader_loop(self) -> None:
        """Background thread: read from socket, parse, dispatch."""
        buf = b""
        last_connect_attempt = 0.0

        while self._running:
            try:
                if self._sock is None:
                    if time.time() - last_connect_attempt > 2.0:
                        try:
                            self.connect()
                            last_connect_attempt = time.time()
                        except OSError:
                            time.sleep(2)
                            continue
                    else:
                        time.sleep(0.5)
                        continue

                chunk = self._sock.recv(65536)
                if not chunk:
                    # Connection closed by game
                    self._sock = None
                    buf = b""
                    continue

                buf += chunk
                objects, buf = extract_json_objects(buf)
                for raw in objects:
                    try:
                        event = parse_message(raw)
                        self._dispatch(event)
                    except Exception:
                        pass  # silently skip malformed messages

                if len(buf) > 1_000_000:
                    buf = b""

            except (OSError, ConnectionError):
                self._sock = None
                buf = b""
                time.sleep(2)

    def _dispatch(self, event: StatsEvent) -> None:
        """Dispatch an event to all registered callbacks and async queue."""
        # Sync callbacks (under lock copy)
        with self._lock:
            general = list(self._general_callbacks)
            typed = list(self._typed_callbacks.get(event.event_type, []))
            typed_all = list(self._typed_callbacks.get("*", []))

        for cb in general:
            try:
                cb(event)
            except Exception:
                pass
        for cb in typed + typed_all:
            try:
                cb(event)
            except Exception:
                pass

        # Async queue
        loop = self._async_loop
        queue = self._async_queue
        if loop and queue:
            try:
                loop.call_soon_threadsafe(
                    queue.put_nowait, event
                )
            except asyncio.QueueFull:
                pass
