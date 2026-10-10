import asyncio
import hashlib
import os
import re
import struct
import time
from typing import Optional

import aiohttp
import yarl

from arizona_forum_async.consts import DEFAULT_USER_AGENT, MAIN_URL
from arizona_forum_async.consts import SUPPORTED_PROXY_SCHEMES
from arizona_forum_async.exceptions import IncorrectProxyData
from arizona_forum_async.logging_config import LOGGER
from arizona_forum_async.request_queue import (
    RequestQueue,
    get_shared_request_queue,
    get_session_queue,
    register_session_queue,
)

CLEARANCE_COOKIE = "__Host-l7_clearance"

CHALLENGE_MARKER = 'id="l7-config"'

_CONFIG_RE = re.compile(
    r'data-([\w-]+)=(?:"([^"]*)"|\'([^\']*)\'|\s*([^\s>]+))'
)

_PACK_II = struct.Struct(">II").pack
_UNPACK_I = struct.Struct(">I").unpack

_CHALLENGE_RETRY_DELAYS = (0.0, 2.0, 5.0)

_BROWSER_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
}


def _parse_config(html: str) -> dict:
    config = {}
    for key, double, single, bare in _CONFIG_RE.findall(html):
        config[key] = double or single or bare
    return config


def _looks_like_challenge(body: str) -> bool:
    if CHALLENGE_MARKER in body or CHALLENGE_MARKER.replace('"', "'") in body:
        return True
    config = _parse_config(body)
    return "init" in config and "verify" in config and "confirm" in config


def _clearance_value(session: aiohttp.ClientSession) -> Optional[str]:
    cookie = session.cookie_jar.filter_cookies(yarl.URL(MAIN_URL)).get(CLEARANCE_COOKIE)
    if cookie is None:
        return None
    return getattr(cookie, "value", cookie)


def _normalize_proxy(proxy: Optional[str]) -> Optional[str]:
    if proxy is None:
        return None
    proxy = proxy.strip()
    if not proxy:
        return None
    if "://" not in proxy:
        proxy = "http://" + proxy
    scheme = proxy.split("://", 1)[0].lower()
    if scheme not in SUPPORTED_PROXY_SCHEMES:
        raise IncorrectProxyData(
            proxy,
            f"схема '{scheme}' не поддерживается, допустимо: "
            + ", ".join(SUPPORTED_PROXY_SCHEMES),
        )
    return proxy


def build_session(
    proxy: Optional[str] = None,
    request_queue: Optional[RequestQueue] = None,
    **kwargs,
) -> aiohttp.ClientSession:
    proxy = _normalize_proxy(proxy)
    headers = dict(_BROWSER_HEADERS)
    headers.update(kwargs.pop("headers", None) or {})
    kwargs["headers"] = headers
    if proxy is not None:
        from aiohttp_socks import ProxyConnector

        kwargs["connector"] = ProxyConnector.from_url(proxy)
    queue = request_queue or get_shared_request_queue(proxy)
    trace_configs = list(kwargs.pop("trace_configs", None) or ())
    trace_configs.append(queue.trace_config())
    trace_configs.append(_request_logging_trace_config())
    kwargs["trace_configs"] = trace_configs
    session = aiohttp.ClientSession(**kwargs)
    register_session_queue(session, queue)
    return session


def _request_logging_trace_config() -> aiohttp.TraceConfig:
    trace_config = aiohttp.TraceConfig()

    async def on_request_start(session, trace_config_ctx, params) -> None:
        trace_config_ctx.started_at = time.monotonic()
        trace_config_ctx.method = params.method
        trace_config_ctx.path = params.url.path

    async def on_request_end(session, trace_config_ctx, params) -> None:
        started_at = getattr(trace_config_ctx, "started_at", None)
        duration = time.monotonic() - started_at if started_at else 0.0
        message = (
            "HTTP %s %s -> %s за %.3fs",
            getattr(trace_config_ctx, "method", params.method),
            getattr(trace_config_ctx, "path", params.url.path),
            params.response.status,
            duration,
        )
        if params.response.status >= 400:
            LOGGER.warning(*message)
        else:
            LOGGER.debug(*message)

    async def on_request_exception(session, trace_config_ctx, params) -> None:
        LOGGER.error(
            "Ошибка HTTP %s %s: %s",
            getattr(trace_config_ctx, "method", "UNKNOWN"),
            getattr(trace_config_ctx, "path", ""),
            type(params.exception).__name__,
        )

    trace_config.on_request_start.append(on_request_start)
    trace_config.on_request_end.append(on_request_end)
    trace_config.on_request_exception.append(on_request_exception)
    return trace_config


async def _request(session: aiohttp.ClientSession, method: str, *args, **kwargs):
    if get_session_queue(session) is None:
        await get_shared_request_queue().acquire()
    return getattr(session, method)(*args, **kwargs)


def _worker(job):
    nonce_hex, hi, lo_start, lo_end, mask = job
    prefix = bytes.fromhex(nonce_hex)
    sha256 = hashlib.sha256
    pack = _PACK_II
    unpack = _UNPACK_I
    for lo in range(lo_start, lo_end):
        if unpack(sha256(prefix + pack(hi, lo)).digest()[:4])[0] & mask == 0:
            return (hi << 32) | lo
    return None


def _solve_sync(nonce_hex: str, difficulty: int, workers: Optional[int] = None) -> int:
    mask = (0xFFFFFFFF << (32 - difficulty)) & 0xFFFFFFFF
    workers = workers or min(os.cpu_count() or 1, 16)

    import multiprocessing

    if workers <= 1 or multiprocessing.current_process().name != "MainProcess":
        return _worker((nonce_hex, 0, 0, 0x100000000, mask))

    step = 0x100000000 // workers
    jobs = [
        (nonce_hex, 0, i * step, (i + 1) * step, mask)
        for i in range(workers)
    ]
    ctx = multiprocessing.get_context("spawn")
    with ctx.Pool(workers) as pool:
        for found in pool.imap_unordered(_worker, jobs):
            if found is not None:
                pool.terminate()
                return found
    raise RuntimeError("PoW: подходящий counter не найден")


async def _solve(nonce_hex: str, difficulty: int) -> int:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _solve_sync, nonce_hex, difficulty)


class L7ChallengeError(Exception):
    pass


async def _read_config(session: aiohttp.ClientSession) -> dict:
    async with await _request(session, "get", f"{MAIN_URL}/") as resp:
        resp.raise_for_status()
        body = await resp.text(errors="replace")
    config = _parse_config(body)
    if "init" not in config or "verify" not in config or "confirm" not in config:
        raise L7ChallengeError("Не удалось прочитать конфигурацию L7-челленджа.")
    return config


async def _is_challenged(session: aiohttp.ClientSession) -> bool:
    async with await _request(
        session,
        "get",
        f"{MAIN_URL}/",
        allow_redirects=False,
    ) as resp:
        if resp.status != 200:
            return False
        if "application/json" in resp.headers.get("Content-Type", ""):
            try:
                data = await resp.json(content_type=None)
            except Exception:
                return False
            return isinstance(data, dict) and data.get("error") == "challenge"
        body = await resp.text(errors="replace")
    return _looks_like_challenge(body)


async def _solve_with_config(
    session: aiohttp.ClientSession,
    config: dict,
) -> str:
    flow = config.get("flow", "")
    last_error = None

    for delay in _CHALLENGE_RETRY_DELAYS:
        if delay:
            await asyncio.sleep(delay)
        started = time.perf_counter()
        try:
            async with await _request(
                session,
                "post",
                f"{MAIN_URL}{config['init']}",
                json={"webdriver": False, "automation": [], "flow": flow},
                headers={"Accept": "application/json"},
            ) as resp:
                if resp.status == 429:
                    last_error = L7ChallengeError("Слишком много попыток (429).")
                    continue
                if resp.status != 200:
                    last_error = L7ChallengeError(f"/init вернул {resp.status}")
                    continue
                challenge = await resp.json(content_type=None)

            counter = await _solve(challenge["nonce"], int(challenge["difficulty"]))
            solve_ms = max(int((time.perf_counter() - started) * 1000), 1)

            async with await _request(
                session,
                "post",
                f"{MAIN_URL}{config['verify']}",
                json={
                    "token": challenge["token"],
                    "counter": str(counter),
                    "solve_ms": solve_ms,
                    "flow": challenge.get("flow") or flow,
                    "delivery": "",
                },
                headers={"Accept": "application/json"},
            ) as resp:
                if resp.status != 200:
                    last_error = L7ChallengeError(f"/verify вернул {resp.status}")
                    continue
                verify = await resp.json(content_type=None)

            receipt = verify.get("receipt")
            if not receipt:
                last_error = L7ChallengeError(
                    "В ответе /verify отсутствует receipt."
                )
                continue

            async with await _request(
                session,
                "post",
                f"{MAIN_URL}{config['confirm']}",
                json={"receipt": receipt},
                headers={"Accept": "application/json"},
            ) as resp:
                if resp.status != 200:
                    last_error = L7ChallengeError(f"/confirm вернул {resp.status}")
                    continue

            clearance = _clearance_value(session)
            if clearance is None:
                last_error = L7ChallengeError(
                    "Куки __Host-l7_clearance не выставлена после /confirm."
                )
                continue
            return clearance
        except (aiohttp.ClientError, L7ChallengeError, KeyError, ValueError) as e:
            last_error = e

    raise L7ChallengeError(
        f"Не удалось пройти L7-челлендж после {len(_CHALLENGE_RETRY_DELAYS)} попыток: {last_error}"
    )


async def solve_challenge(session: aiohttp.ClientSession) -> str:
    config = await _read_config(session)
    return await _solve_with_config(session, config)


async def bypass_async(session: Optional[aiohttp.ClientSession] = None) -> str:
    own_session = session is None
    if own_session:
        session = build_session(headers={"user-agent": DEFAULT_USER_AGENT})
    try:
        LOGGER.debug("Проверка L7-челленджа")
        if await _is_challenged(session):
            LOGGER.info("Обнаружен L7-челлендж, запускается решение")
            await solve_challenge(session)
        return _clearance_value(session)
    finally:
        if own_session:
            await session.close()


async def bypass_async_with_cookiejar(proxy: Optional[str] = None):
    session = build_session(proxy, headers={"user-agent": DEFAULT_USER_AGENT})
    try:
        if await _is_challenged(session):
            await solve_challenge(session)
        return _clearance_value(session)
    finally:
        await session.close()
