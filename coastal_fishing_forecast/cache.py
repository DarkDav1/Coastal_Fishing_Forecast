"""Small JSON file cache for external forecast data."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping


CACHE_DIR_ENV = "COASTAL_FORECAST_CACHE_DIR"
DEFAULT_CACHE_DIR = ".cache/coastal_fishing_forecast"


def resolve_cache_dir(cache_dir: str | Path | None = None) -> Path:
    configured = cache_dir or os.environ.get(CACHE_DIR_ENV) or DEFAULT_CACHE_DIR
    return Path(configured)


def cache_key(namespace: str, params: Mapping[str, Any]) -> str:
    payload = json.dumps(params, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]
    return f"{namespace}-{digest}"


def get_json_cache(
    namespace: str,
    params: Mapping[str, Any],
    *,
    cache_dir: str | Path | None = None,
    ttl_seconds: int | None = None,
) -> dict[str, Any] | None:
    path = resolve_cache_dir(cache_dir) / f"{cache_key(namespace, params)}.json"
    if not path.exists():
        return None

    payload = json.loads(path.read_text(encoding="utf-8"))
    if ttl_seconds is None:
        return payload["data"]

    created_at = datetime.fromisoformat(payload["created_at"])
    if datetime.now(timezone.utc) - created_at > timedelta(seconds=ttl_seconds):
        return None
    return payload["data"]


def set_json_cache(
    namespace: str,
    params: Mapping[str, Any],
    data: Mapping[str, Any],
    *,
    cache_dir: str | Path | None = None,
) -> None:
    directory = resolve_cache_dir(cache_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{cache_key(namespace, params)}.json"
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "namespace": namespace,
        "params": dict(params),
        "data": data,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
