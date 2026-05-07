"""Place search resolver for frontend search flows.

This module is intentionally separate from the forecast engine. It resolves
human place queries into candidate coordinates; forecast scoring still starts
from latitude and longitude.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from coastal_fishing_forecast.cache import get_json_cache, set_json_cache


MAPBOX_TOKEN_ENV = "MAPBOX_ACCESS_TOKEN"
MAPBOX_GEOCODING_URL = "https://api.mapbox.com/geocoding/v5/mapbox.places"
NOMINATIM_SEARCH_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_USER_AGENT = "coastal-fishing-forecast-dev/0.1"
DEFAULT_COUNTRY_FILTER = "au"
DEFAULT_LANGUAGE = "en"
COASTAL_TYPE_HINTS = {
    "beach",
    "bay",
    "cape",
    "coastline",
    "water",
    "natural",
    "strait",
    "island",
    "harbour",
    "marina",
    "pier",
}


def _load_json(url: str, timeout_seconds: int, headers: Mapping[str, str] | None = None) -> Any:
    request = Request(url, headers=dict(headers or {}))
    with urlopen(request, timeout=timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))


def _mapbox_url(
    *,
    query: str,
    access_token: str,
    country: str | None,
    proximity: tuple[float, float] | None,
    limit: int,
    language: str,
) -> str:
    params: dict[str, Any] = {
        "access_token": access_token,
        "autocomplete": "true",
        "limit": limit,
        "language": language,
    }
    if country:
        params["country"] = country
    if proximity:
        params["proximity"] = f"{proximity[1]},{proximity[0]}"
    return f"{MAPBOX_GEOCODING_URL}/{quote(query)}.json?{urlencode(params)}"


def _nominatim_url(
    *,
    query: str,
    country: str | None,
    limit: int,
    language: str,
) -> str:
    params: dict[str, Any] = {
        "q": query,
        "format": "jsonv2",
        "addressdetails": 1,
        "limit": limit,
        "accept-language": language,
    }
    if country:
        params["countrycodes"] = country
    return f"{NOMINATIM_SEARCH_URL}?{urlencode(params)}"


def _context_value(feature: Mapping[str, Any], prefix: str) -> str | None:
    for item in feature.get("context", []):
        item_id = str(item.get("id", ""))
        if item_id.startswith(prefix):
            return item.get("text")
    return None


def normalize_mapbox_feature(feature: Mapping[str, Any]) -> dict[str, Any]:
    center = feature.get("center") or [None, None]
    lon, lat = center[0], center[1]
    place_type = list(feature.get("place_type", []))
    return {
        "id": feature.get("id"),
        "display_name": feature.get("place_name"),
        "short_name": feature.get("text"),
        "latitude": lat,
        "longitude": lon,
        "country": _context_value(feature, "country") or feature.get("properties", {}).get("short_code"),
        "region": _context_value(feature, "region"),
        "source": "mapbox",
        "confidence": round(float(feature.get("relevance", 0.0)), 2),
        "types": place_type,
        "bbox": feature.get("bbox"),
    }


def normalize_mapbox_response(query: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    results = [
        normalize_mapbox_feature(feature)
        for feature in payload.get("features", [])
        if feature.get("center")
    ]
    return {
        "query": query,
        "provider": "mapbox",
        "results": results,
    }


def normalize_nominatim_item(item: Mapping[str, Any]) -> dict[str, Any]:
    address = item.get("address", {})
    return {
        "id": f"nominatim:{item.get('osm_type')}:{item.get('osm_id')}",
        "display_name": item.get("display_name"),
        "short_name": item.get("name") or item.get("display_name", "").split(",", 1)[0],
        "latitude": float(item["lat"]),
        "longitude": float(item["lon"]),
        "country": address.get("country"),
        "region": address.get("state") or address.get("region"),
        "source": "nominatim",
        "confidence": None,
        "types": [value for value in (item.get("class"), item.get("type")) if value],
        "bbox": [float(value) for value in item.get("boundingbox", [])] if item.get("boundingbox") else None,
    }


def normalize_nominatim_response(query: str, payload: list[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "query": query,
        "provider": "nominatim",
        "results": [normalize_nominatim_item(item) for item in payload if item.get("lat") and item.get("lon")],
    }


def search_places(
    query: str,
    *,
    provider: str = "mapbox",
    access_token: str | None = None,
    country: str | None = DEFAULT_COUNTRY_FILTER,
    proximity: tuple[float, float] | None = None,
    limit: int = 5,
    language: str = DEFAULT_LANGUAGE,
    cache_enabled: bool = True,
    cache_dir: str | Path | None = None,
    timeout_seconds: int = 15,
) -> dict[str, Any]:
    if provider not in {"mapbox", "nominatim"}:
        raise ValueError("provider must be one of: mapbox, nominatim")

    normalized_query = query.strip()
    if not normalized_query:
        raise ValueError("query must not be empty")

    cache_params = {
        "provider": provider,
        "query": normalized_query,
        "country": country,
        "proximity": proximity,
        "limit": limit,
        "language": language,
    }
    if cache_enabled:
        cached = get_json_cache("place_search", cache_params, cache_dir=cache_dir, ttl_seconds=86400)
        if cached is not None:
            return cached

    if provider == "mapbox":
        token = access_token or os.environ.get(MAPBOX_TOKEN_ENV)
        if not token:
            raise ValueError(f"Missing Mapbox access token. Set {MAPBOX_TOKEN_ENV} or pass --mapbox-token.")
        url = _mapbox_url(
            query=normalized_query,
            access_token=token,
            country=country,
            proximity=proximity,
            limit=limit,
            language=language,
        )
        payload = _load_json(url, timeout_seconds)
        result = normalize_mapbox_response(normalized_query, payload)
    else:
        url = _nominatim_url(
            query=normalized_query,
            country=country,
            limit=limit,
            language=language,
        )
        payload = _load_json(url, timeout_seconds, headers={"User-Agent": NOMINATIM_USER_AGENT})
        result = normalize_nominatim_response(normalized_query, payload)
    if cache_enabled:
        set_json_cache("place_search", cache_params, result, cache_dir=cache_dir)
    return result


def coastal_candidate_score(candidate: Mapping[str, Any]) -> float:
    score = 0.0
    types = {str(item).lower() for item in candidate.get("types", [])}
    if types & COASTAL_TYPE_HINTS:
        score += 20.0
    if "administrative" in types or "boundary" in types:
        score -= 6.0
    if candidate.get("bbox"):
        score += 2.0
    confidence = candidate.get("confidence")
    if isinstance(confidence, int | float):
        score += float(confidence) * 10.0
    return score


def rank_place_candidates(candidates: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    ranked = []
    for candidate in candidates:
        item = dict(candidate)
        item["coastal_candidate_score"] = round(coastal_candidate_score(candidate), 2)
        ranked.append(item)
    return sorted(ranked, key=lambda item: item["coastal_candidate_score"], reverse=True)
