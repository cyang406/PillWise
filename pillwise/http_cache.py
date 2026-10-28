"""Tiny JSON cache for RxNorm / openFDA so the demo works offline. Owner: A.

get_json(namespace, url, params, *, secret_params=None, slim=None) -> dict
    - returns the cached file under settings.cache_dir/<namespace>/<hash>.json if present
    - otherwise fetches with httpx (unless settings.offline), saves, returns
    - secret_params (e.g. an API key) are sent but never part of the cache key or the file
    - slim(data) -> data trims a large response before it is cached and returned
Cached files are committed to git before the demo (they are public data).
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from typing import Any

from pillwise.config import get_settings


def _key(url: str, params: dict[str, Any] | None) -> str:
    raw = url + "?" + json.dumps(params or {}, sort_keys=True)
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


def get_json(
    namespace: str,
    url: str,
    params: dict[str, Any] | None = None,
    timeout: float = 15.0,
    *,
    secret_params: dict[str, Any] | None = None,
    slim: Callable[[dict], dict] | None = None,
) -> dict:
    settings = get_settings()
    path = settings.cache_dir / namespace / f"{_key(url, params)}.json"
    if path.exists():
        return json.loads(path.read_text())
    if settings.offline:
        raise LookupError(f"offline and not cached: {namespace} {url} {params}")
    import httpx

    resp = httpx.get(url, params={**(params or {}), **(secret_params or {})}, timeout=timeout)
    if resp.status_code == 404:  # openFDA answers "no matches" with 404; cache it as empty
        data: dict = {}
    else:
        resp.raise_for_status()
        data = resp.json()
    if slim is not None:
        data = slim(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))
    return data
