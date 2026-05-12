"""Weather and marine condition loading for range forecasts."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen

from coastal_fishing_forecast.cache import get_json_cache, set_json_cache


OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_MARINE_URL = "https://marine-api.open-meteo.com/v1/marine"


def _load_json(url: str, timeout_seconds: int) -> dict[str, Any]:
    with urlopen(url, timeout=timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))


def _load_json_cached(
    *,
    url: str,
    timeout_seconds: int,
    namespace: str,
    cache_enabled: bool,
    cache_dir: str | Path | None,
    ttl_seconds: int | None,
) -> dict[str, Any]:
    params = {"url": url}
    if cache_enabled:
        cached = get_json_cache(namespace, params, cache_dir=cache_dir, ttl_seconds=ttl_seconds)
        if cached is not None:
            return cached
    data = _load_json(url, timeout_seconds)
    if cache_enabled:
        set_json_cache(namespace, params, data, cache_dir=cache_dir)
    return data


def _weather_url(
    *,
    lat: float,
    lon: float,
    start_date: date,
    end_date: date,
    source: str,
) -> str:
    endpoint = OPEN_METEO_ARCHIVE_URL if source == "archive" else OPEN_METEO_FORECAST_URL
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "hourly": "temperature_2m,surface_pressure,wind_speed_10m,wind_direction_10m,wind_gusts_10m,precipitation,rain,cloud_cover",
        "daily": "sunrise,sunset",
        "wind_speed_unit": "kn",
        "timezone": "Australia/Hobart",
    }
    return f"{endpoint}?{urlencode(params)}"


def _marine_url(*, lat: float, lon: float, start_date: date, end_date: date) -> str:
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "hourly": "wave_height,wave_period,swell_wave_height,swell_wave_direction,wind_wave_height,sea_surface_temperature,sea_level_height_msl",
        "timezone": "Australia/Hobart",
        "cell_selection": "sea",
    }
    return f"{OPEN_METEO_MARINE_URL}?{urlencode(params)}"


def resolve_weather_source(start_date: date, end_date: date, today: date | None = None) -> str:
    today = today or date.today()
    return "archive" if end_date < today else "forecast"


def fetch_open_meteo_conditions(
    *,
    lat: float,
    lon: float,
    start_date: date,
    end_date: date,
    source: str = "auto",
    timeout_seconds: int = 20,
    cache_enabled: bool = True,
    cache_dir: str | Path | None = None,
) -> dict[str, Any]:
    resolved_source = resolve_weather_source(start_date, end_date) if source == "auto" else source
    if resolved_source not in {"archive", "forecast"}:
        raise ValueError("source must be one of: auto, archive, forecast")

    weather_url = _weather_url(
        lat=lat,
        lon=lon,
        start_date=start_date,
        end_date=end_date,
        source=resolved_source,
    )
    marine_url = _marine_url(lat=lat, lon=lon, start_date=start_date, end_date=end_date)
    ttl_seconds = None if resolved_source == "archive" else 3600
    weather = _load_json_cached(
        url=weather_url,
        timeout_seconds=timeout_seconds,
        namespace="open_meteo_weather",
        cache_enabled=cache_enabled,
        cache_dir=cache_dir,
        ttl_seconds=ttl_seconds,
    )
    marine = _load_json_cached(
        url=marine_url,
        timeout_seconds=timeout_seconds,
        namespace="open_meteo_marine",
        cache_enabled=cache_enabled,
        cache_dir=cache_dir,
        ttl_seconds=ttl_seconds,
    )
    return {
        "provider": "open_meteo",
        "weather_source": resolved_source,
        "cache_enabled": cache_enabled,
        "weather_hourly": weather["hourly"],
        "weather_daily": weather.get("daily", {}),
        "marine_hourly": marine["hourly"],
        "units": {
            "weather": weather.get("hourly_units", {}),
            "marine": marine.get("hourly_units", {}),
        },
    }
