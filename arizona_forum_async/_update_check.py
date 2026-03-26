from __future__ import annotations

import json
import tempfile
import threading
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from packaging.version import InvalidVersion, Version

_DIST_NAME = "arizona-forum-api-async"
_VERSION_URL = "https://raw.githubusercontent.com/fakelag28/Arizona-Forum-API-Async/main/version.txt"

_CACHE_TTL_SECONDS = 60 * 60 * 12
_CACHE_FILE = Path(tempfile.gettempdir()) / "arizona_forum_api_async_update_check.json"

_started = False
_lock = threading.Lock()


def check_for_updates_async(current_version: str) -> None:
    global _started

    with _lock:
        if _started:
            return
        _started = True

    thread = threading.Thread(
        target=_check_and_print,
        args=(current_version,),
        daemon=True
    )
    thread.start()


def _check_and_print(current_version: str) -> None:
    try:
        installed = _parse_version(current_version)
        if installed is None:
            return

        latest_str = _get_cached_latest_version()
        if latest_str is None:
            latest_str = _fetch_latest_version_from_repo_file()
            if latest_str is None:
                return
            _save_cache(latest_str)

        latest = _parse_version(latest_str)
        if latest is None:
            return

        if latest > installed:
            print(
                f"[Arizona-Forum-API-Async] Доступно обновление: {installed} -> {latest}. "
                f"Обновить: pip install -U {_DIST_NAME}"
            )
    except Exception as e:
        print(f"[Arizona-Forum-API-Async] Ошибка проверки обновления: {e}")


def _parse_version(value: str) -> Version | None:
    try:
        return Version(str(value).strip())
    except (InvalidVersion, TypeError, ValueError):
        return None


def _fetch_latest_version_from_repo_file() -> str | None:
    req = Request(
        _VERSION_URL,
        headers={"User-Agent": _DIST_NAME},
    )

    try:
        with urlopen(req, timeout=3) as response:
            text = response.read().decode("utf-8").strip()
    except (HTTPError, URLError, TimeoutError, UnicodeDecodeError):
        return None

    if not text:
        return None

    first_line = text.splitlines()[0].strip()
    return first_line or None


def _get_cached_latest_version() -> str | None:
    try:
        if not _CACHE_FILE.exists():
            return None

        payload = json.loads(_CACHE_FILE.read_text("utf-8"))
        checked_at = float(payload.get("checked_at", 0))
        latest = str(payload.get("latest", "")).strip()

        if not latest:
            return None

        if (time.time() - checked_at) > _CACHE_TTL_SECONDS:
            return None

        return latest
    except Exception:
        return None


def _save_cache(latest: str) -> None:
    try:
        payload = {
            "latest": latest,
            "checked_at": time.time(),
        }
        _CACHE_FILE.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass