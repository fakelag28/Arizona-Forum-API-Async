import asyncio
import time
from collections import deque
from threading import Lock
from typing import Callable, Deque, Dict, Optional
from weakref import WeakKeyDictionary

import aiohttp

from arizona_forum_async.logging_config import LOGGER


DEFAULT_REQUEST_INTERVAL = 2.0
DEFAULT_MAX_REQUESTS = 30
DEFAULT_WINDOW_SECONDS = 60.0


def _get_running_loop():
    try:
        return asyncio.get_running_loop()
    except AttributeError:
        return asyncio.get_event_loop()


class RequestQueue:
    def __init__(
        self,
        interval: float = DEFAULT_REQUEST_INTERVAL,
        max_requests: Optional[int] = DEFAULT_MAX_REQUESTS,
        window_seconds: float = DEFAULT_WINDOW_SECONDS,
        clock: Optional[Callable[[], float]] = None,
    ) -> None:
        if interval < 0:
            raise ValueError("Интервал запросов не может быть отрицательным.")
        if max_requests is not None and max_requests <= 0:
            raise ValueError("Максимальное количество запросов должно быть положительным.")
        if window_seconds <= 0:
            raise ValueError("Окно ограничения должно быть положительным.")

        self.interval = float(interval)
        self.max_requests = max_requests
        self.window_seconds = float(window_seconds)
        self._clock = clock or time.monotonic
        self._waiters = deque()
        self._started: Deque[float] = deque()
        self._last_started: Optional[float] = None
        self._draining = False
        self._drainer = None

    async def acquire(self) -> None:
        loop = _get_running_loop()
        waiter = loop.create_future()
        self._waiters.append(waiter)
        LOGGER.debug("Запрос добавлен в очередь: ожидающих=%d", len(self._waiters))

        if not self._draining:
            self._draining = True
            self._drainer = asyncio.ensure_future(self._drain(), loop=loop)

        try:
            await waiter
        except asyncio.CancelledError:
            if not waiter.done():
                waiter.cancel()
            raise

    async def _drain(self) -> None:
        try:
            while self._waiters:
                waiter = self._waiters.popleft()
                if waiter.cancelled():
                    continue

                await self._wait_until_available()

                if waiter.cancelled():
                    continue

                started_at = self._clock()
                self._started.append(started_at)
                self._last_started = started_at
                waiter.set_result(None)
                LOGGER.debug(
                    "Запрос выпущен из очереди: интервал=%.3f",
                    self.interval,
                )
        finally:
            self._draining = False
            self._drainer = None
            if self._waiters:
                loop = _get_running_loop()
                self._draining = True
                self._drainer = asyncio.ensure_future(self._drain(), loop=loop)

    async def _wait_until_available(self) -> None:
        while True:
            now = self._clock()
            while self._started and now - self._started[0] >= self.window_seconds:
                self._started.popleft()

            delay = 0.0
            if self._last_started is not None:
                delay = max(delay, self.interval - (now - self._last_started))

            if self.max_requests is not None and len(self._started) >= self.max_requests:
                delay = max(delay, self._started[0] + self.window_seconds - now)

            if delay <= 0:
                return

            await asyncio.sleep(delay)

    def trace_config(self) -> aiohttp.TraceConfig:
        trace_config = aiohttp.TraceConfig()

        async def on_request_start(session, trace_config_ctx, params) -> None:
            await self.acquire()

        trace_config.on_request_start.append(on_request_start)
        return trace_config


_shared_queues: Dict[str, RequestQueue] = {}
_shared_queues_lock = Lock()
_session_queues = WeakKeyDictionary()


def get_shared_request_queue(proxy_key: Optional[str] = None) -> RequestQueue:
    key = proxy_key or "__direct__"
    with _shared_queues_lock:
        queue = _shared_queues.get(key)
        if queue is None:
            queue = RequestQueue()
            _shared_queues[key] = queue
        return queue


def register_session_queue(session, queue: RequestQueue) -> None:
    _session_queues[session] = queue


def get_session_queue(session) -> Optional[RequestQueue]:
    return _session_queues.get(session)
