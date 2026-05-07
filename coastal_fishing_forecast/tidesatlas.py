"""TidesAtlas API adapter."""

from __future__ import annotations

from datetime import date
import json
import math
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from coastal_fishing_forecast.cache import get_json_cache, set_json_cache
from coastal_fishing_forecast.tides import TideEvent, parse_tide_events


TIDESATLAS_API_URL = "https://tidesatlas.com/api/v1/tides"
TIDESATLAS_API_KEY_ENV = "TIDESATLAS_API_KEY"
TIDESATLAS_MAX_DAYS = 14
EARTH_RADIUS_KM = 6371.0


def _distance_km(first_lat: float, first_lon: float, second_lat: float, second_lon: float) -> float:
    lat1 = math.radians(first_lat)
    lat2 = math.radians(second_lat)
    dlat = math.radians(second_lat - first_lat)
    dlon = math.radians(second_lon - first_lon)
    a = math.sin(dlat / 2.0) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2.0) ** 2
    return EARTH_RADIUS_KM * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


def _date_range_chunks(start_date: date, end_date: date, chunk_days: int) -> list[tuple[date, date]]:
    chunks = []
    current = start_date
    while current <= end_date:
        chunk_end = min(date.fromordinal(current.toordinal() + chunk_days - 1), end_date)
        chunks.append((current, chunk_end))
        current = date.fromordinal(chunk_end.toordinal() + 1)
    return chunks


def normalize_tidesatlas_response(payload: dict[str, Any]) -> list[TideEvent]:
    raw_events = []
    for extreme in payload.get("extremes", []):
        raw_events.append(
            {
                "time": extreme.get("datetime"),
                "type": extreme.get("type"),
                "height_m": extreme.get("height_m"),
            }
        )
    return parse_tide_events(raw_events)


def fetch_tidesatlas_events(
    *,
    lat: float,
    lon: float,
    start_date: date,
    end_date: date,
    api_key: str | None = None,
    timeout_seconds: int = 20,
    api_url: str = TIDESATLAS_API_URL,
    cache_enabled: bool = True,
    cache_dir: str | Path | None = None,
) -> tuple[list[TideEvent], dict[str, Any]]:
    key = api_key or os.environ.get(TIDESATLAS_API_KEY_ENV)
    if not key:
        raise ValueError(f"Missing TidesAtlas API key. Set {TIDESATLAS_API_KEY_ENV} or pass --tidesatlas-api-key.")
    if end_date < start_date:
        raise ValueError("end_date must be on or after start_date")

    events: list[TideEvent] = []
    last_port: dict[str, Any] | None = None
    for chunk_start, chunk_end in _date_range_chunks(start_date, end_date, TIDESATLAS_MAX_DAYS):
        days = (chunk_end - chunk_start).days + 1
        params = {
            "lat": lat,
            "lon": lon,
            "date": chunk_start.isoformat(),
            "days": days,
            "format": "json",
        }
        url = f"{api_url}?{urlencode(params)}"
        cached = get_json_cache("tidesatlas", {"url": url}, cache_dir=cache_dir, ttl_seconds=None) if cache_enabled else None
        if cached is None:
            request = Request(
                url,
                headers={"X-API-Key": key, "Accept": "application/json"},
            )
            with urlopen(request, timeout=timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
            if cache_enabled:
                set_json_cache("tidesatlas", {"url": url}, payload, cache_dir=cache_dir)
        else:
            payload = cached
        events.extend(normalize_tidesatlas_response(payload))
        if isinstance(payload.get("port"), dict):
            last_port = payload["port"]

    port_distance_km = None
    if last_port and last_port.get("lat") is not None and last_port.get("lon") is not None:
        port_distance_km = round(_distance_km(lat, lon, float(last_port["lat"]), float(last_port["lon"])), 1)

    return sorted(events, key=lambda event: event.time), {
        "provider": "tidesatlas",
        "port": last_port,
        "port_distance_km": port_distance_km,
        "date_range": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        },
    }
