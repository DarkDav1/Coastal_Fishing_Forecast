"""Public coastal structure lookup from OpenStreetMap/Overpass."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from math import atan2, cos, radians, sin, sqrt
import json
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from coastal_fishing_forecast.cache import get_json_cache, set_json_cache


OVERPASS_ENDPOINT = "https://overpass-api.de/api/interpreter"
LIST_MAST_BOAT_RAMPS_ENDPOINT = "https://services.thelist.tas.gov.au/arcgis/rest/services/Public/TopographyAndRelief/MapServer/33/query"
LIST_WILDFISHERIES_SEA_SPOTS_ENDPOINT = "https://services.thelist.tas.gov.au/arcgis/rest/services/Public/WildFisheries/MapServer/0/query"
STRUCTURE_CONTRACT_VERSION = "2026-04-28.structure_facilities.v1"
PUBLIC_ACCESS_VALUES = {"public", "yes", "permissive", "designated"}
PRIVATE_ACCESS_VALUES = {"private", "no", "customers"}
PLANNER_ELIGIBLE_TYPES = {
    "beach_access",
    "fishing_platform",
    "official_fishing_spot",
    "public_jetty",
    "rocky_shoreline",
}
MAP_ELIGIBLE_TYPES = PLANNER_ELIGIBLE_TYPES | {"boat_ramp"}
NEAR_DUPLICATE_DISTANCE_KM = 0.08


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * radius_km * atan2(sqrt(a), sqrt(1 - a))


def _overpass_query(lat: float, lon: float, radius_m: int) -> str:
    return f"""
[out:json][timeout:25];
(
  node(around:{radius_m},{lat},{lon})["man_made"="pier"];
  way(around:{radius_m},{lat},{lon})["man_made"="pier"];
  relation(around:{radius_m},{lat},{lon})["man_made"="pier"];
  node(around:{radius_m},{lat},{lon})["man_made"="jetty"];
  way(around:{radius_m},{lat},{lon})["man_made"="jetty"];
  relation(around:{radius_m},{lat},{lon})["man_made"="jetty"];
  node(around:{radius_m},{lat},{lon})["leisure"="slipway"];
  way(around:{radius_m},{lat},{lon})["leisure"="slipway"];
  relation(around:{radius_m},{lat},{lon})["leisure"="slipway"];
  node(around:{radius_m},{lat},{lon})["leisure"="fishing"];
  way(around:{radius_m},{lat},{lon})["leisure"="fishing"];
  relation(around:{radius_m},{lat},{lon})["leisure"="fishing"];
  node(around:{radius_m},{lat},{lon})["sport"="fishing"];
  way(around:{radius_m},{lat},{lon})["sport"="fishing"];
  relation(around:{radius_m},{lat},{lon})["sport"="fishing"];
  node(around:{radius_m},{lat},{lon})["fishing"];
  way(around:{radius_m},{lat},{lon})["fishing"];
  relation(around:{radius_m},{lat},{lon})["fishing"];
);
out center tags;
"""


def _element_coordinates(element: Mapping[str, Any]) -> tuple[float, float] | None:
    if "lat" in element and "lon" in element:
        return float(element["lat"]), float(element["lon"])
    center = element.get("center")
    if isinstance(center, Mapping) and "lat" in center and "lon" in center:
        return float(center["lat"]), float(center["lon"])
    return None


def _public_access_status(tags: Mapping[str, Any]) -> str:
    access = str(tags.get("access") or "").lower()
    name = str(tags.get("name") or "").lower()
    if access in PRIVATE_ACCESS_VALUES:
        return "private"
    if access in PUBLIC_ACCESS_VALUES:
        return "public"
    if "public jetty" in name or "public pier" in name or "public wharf" in name:
        return "public"
    return "unknown"


def _facility_type(tags: Mapping[str, Any], public_access_status: str) -> str | None:
    man_made = str(tags.get("man_made") or "").lower()
    leisure = str(tags.get("leisure") or "").lower()
    sport = str(tags.get("sport") or "").lower()
    fishing = str(tags.get("fishing") or "").lower()
    if man_made in {"pier", "jetty"}:
        return "public_jetty" if public_access_status == "public" else "pier"
    if leisure == "slipway":
        return "boat_ramp"
    if leisure == "fishing" or sport == "fishing" or fishing in {"yes", "designated", "permissive"}:
        return "fishing_platform" if public_access_status == "public" else "fishing_access"
    return None


def _planner_eligible(facility_type: str, access: str) -> bool:
    return access == "public" and facility_type in PLANNER_ELIGIBLE_TYPES


def _map_eligible(facility_type: str, access: str) -> bool:
    return access == "public" and facility_type in MAP_ELIGIBLE_TYPES


def _facility_role(facility_type: str, access: str) -> str:
    if _planner_eligible(facility_type, access):
        return "public_fishing_access"
    if _map_eligible(facility_type, access):
        return "public_access_only"
    return "hidden"


def _label_for(tags: Mapping[str, Any], facility_type: str) -> str:
    if tags.get("name"):
        return str(tags["name"])
    labels = {
        "public_jetty": "Mapped public jetty",
        "pier": "Mapped pier, public access unknown",
        "boat_ramp": "Mapped boat ramp",
        "fishing_platform": "Mapped public fishing platform",
        "fishing_access": "Mapped fishing access, public access unknown",
    }
    return labels.get(facility_type, facility_type.replace("_", " "))


def normalize_osm_structure_facilities(
    payload: Mapping[str, Any],
    *,
    lat: float,
    lon: float,
) -> list[dict[str, Any]]:
    facilities = []
    for element in payload.get("elements", []):
        if not isinstance(element, Mapping):
            continue
        tags = element.get("tags") or {}
        if not isinstance(tags, Mapping):
            continue
        coords = _element_coordinates(element)
        if coords is None:
            continue
        facility_lat, facility_lon = coords
        public_access_status = _public_access_status(tags)
        facility_type = _facility_type(tags, public_access_status)
        if facility_type is None:
            continue
        planner_eligible = _planner_eligible(facility_type, public_access_status)
        map_eligible = _map_eligible(facility_type, public_access_status)
        facilities.append(
            {
                "id": f"osm:{element.get('type')}:{element.get('id')}",
                "type": facility_type,
                "label": _label_for(tags, facility_type),
                "access": public_access_status,
                "status": "confirmed",
                "source": "osm_overpass",
                "coordinates": {"latitude": facility_lat, "longitude": facility_lon},
                "distance_km": round(_distance_km(lat, lon, facility_lat, facility_lon), 3),
                "tags": dict(tags),
                "planner_eligible": planner_eligible,
                "map_eligible": map_eligible,
                "role": _facility_role(facility_type, public_access_status),
            }
        )
    facilities.sort(key=lambda item: (not item["planner_eligible"], item["distance_km"], item["label"]))
    return facilities


def _mast_facility_type(description: str) -> str:
    lowered = description.lower()
    if "jetty" in lowered or "wharf" in lowered or "pier" in lowered:
        return "public_jetty"
    if "slipway" in lowered or "ramp" in lowered:
        return "boat_ramp"
    return "marine_facility"


def _text_has_any(value: str, words: tuple[str, ...]) -> bool:
    lowered = value.lower()
    return any(word in lowered for word in words)


def _wildfisheries_spot_type(site: str, description: str) -> str:
    text = f"{site} {description}"
    if _text_has_any(text, ("jetty", "wharf", "pier")):
        return "public_jetty"
    if _text_has_any(text, ("platform",)):
        return "fishing_platform"
    if _text_has_any(text, ("breakwater", "rocky", "rock ", "rocks", "ledge", "headland")):
        return "rocky_shoreline"
    if _text_has_any(text, ("beach", "shore")):
        return "beach_access"
    return "official_fishing_spot"


def _clean_label(value: Any, fallback: str) -> str:
    text = str(value or fallback)
    return " ".join(text.replace("\n", " ").split())


def _yes_no_facility(attributes: Mapping[str, Any], key: str) -> bool:
    return str(attributes.get(key) or "").strip().lower() in {"yes", "y", "true", "1"}


def normalize_list_wildfisheries_sea_spots(
    payload: Mapping[str, Any],
    *,
    lat: float,
    lon: float,
) -> list[dict[str, Any]]:
    facilities = []
    for feature in payload.get("features", []):
        if not isinstance(feature, Mapping):
            continue
        attributes = feature.get("attributes") or {}
        geometry = feature.get("geometry") or {}
        if not isinstance(attributes, Mapping) or not isinstance(geometry, Mapping):
            continue
        if "x" not in geometry or "y" not in geometry:
            continue
        facility_lat = float(geometry["y"])
        facility_lon = float(geometry["x"])
        site = _clean_label(attributes.get("SITE_LOCAT"), "Official sea fishing spot")
        description = _clean_label(attributes.get("DESCRIPTIO"), "")
        facility_type = _wildfisheries_spot_type(site, description)
        planner_eligible = _planner_eligible(facility_type, "public")
        map_eligible = _map_eligible(facility_type, "public")
        facilities.append(
            {
                "id": f"list_wildfisheries:{attributes.get('OBJECTID')}",
                "type": facility_type,
                "label": site,
                "access": "public",
                "status": "confirmed",
                "source": "list_wildfisheries",
                "coordinates": {"latitude": facility_lat, "longitude": facility_lon},
                "distance_km": round(_distance_km(lat, lon, facility_lat, facility_lon), 3),
                "attributes": dict(attributes),
                "planner_eligible": planner_eligible,
                "map_eligible": map_eligible,
                "role": "public_fishing_access" if planner_eligible else _facility_role(facility_type, "public"),
                "amenities": {
                    "bbq": _yes_no_facility(attributes, "BBQ_FACILI"),
                    "table": _yes_no_facility(attributes, "TABLE_S"),
                    "cleaning": _yes_no_facility(attributes, "CLEANING_F"),
                    "toilets": _yes_no_facility(attributes, "TOILETS"),
                    "rubbish_bin": _yes_no_facility(attributes, "RUBBISH_BI"),
                    "signage": _yes_no_facility(attributes, "FISHERIES_"),
                    "shelter": _yes_no_facility(attributes, "SHELTER"),
                    "lighting": _yes_no_facility(attributes, "LIGHTING"),
                    "water": _yes_no_facility(attributes, "WATER"),
                    "seat": _yes_no_facility(attributes, "SEAT"),
                },
            }
        )
    facilities.sort(key=lambda item: (not item["planner_eligible"], item["distance_km"], item["label"]))
    return facilities


def normalize_list_mast_facilities(
    payload: Mapping[str, Any],
    *,
    lat: float,
    lon: float,
) -> list[dict[str, Any]]:
    facilities = []
    for feature in payload.get("features", []):
        if not isinstance(feature, Mapping):
            continue
        attributes = feature.get("attributes") or {}
        geometry = feature.get("geometry") or {}
        if not isinstance(attributes, Mapping) or not isinstance(geometry, Mapping):
            continue
        if "x" not in geometry or "y" not in geometry:
            continue
        facility_lat = float(geometry["y"])
        facility_lon = float(geometry["x"])
        description = str(attributes.get("DESCRIPT") or "Marine facility")
        facility_type = _mast_facility_type(description)
        label = str(attributes.get("NAME") or description)
        planner_eligible = _planner_eligible(facility_type, "public")
        map_eligible = _map_eligible(facility_type, "public")
        facilities.append(
            {
                "id": f"list_mast:{attributes.get('OBJECTID') or attributes.get('INFRA_ID')}",
                "type": facility_type,
                "label": label,
                "access": "public",
                "status": "confirmed",
                "source": "list_mast",
                "coordinates": {"latitude": facility_lat, "longitude": facility_lon},
                "distance_km": round(_distance_km(lat, lon, facility_lat, facility_lon), 3),
                "attributes": dict(attributes),
                "planner_eligible": planner_eligible,
                "map_eligible": map_eligible,
                "role": _facility_role(facility_type, "public"),
            }
        )
    facilities.sort(key=lambda item: (not item["planner_eligible"], item["distance_km"], item["label"]))
    return facilities


def _dedupe_facilities(facilities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen = set()
    for item in facilities:
        coords = item.get("coordinates") or {}
        key = (
            item.get("type"),
            round(float(coords.get("latitude", 0)), 4),
            round(float(coords.get("longitude", 0)), 4),
            item.get("label"),
        )
        if key in seen:
            continue
        if any(_near_duplicate_facility(item, existing) for existing in deduped):
            continue
        seen.add(key)
        deduped.append(item)
    deduped.sort(key=lambda item: (not item.get("planner_eligible"), item.get("distance_km", 999), item.get("label") or ""))
    return deduped


def _facility_coords(item: Mapping[str, Any]) -> tuple[float, float] | None:
    coords = item.get("coordinates")
    if not isinstance(coords, Mapping):
        return None
    latitude = coords.get("latitude")
    longitude = coords.get("longitude")
    if latitude is None or longitude is None:
        return None
    return float(latitude), float(longitude)


def _facility_group(item: Mapping[str, Any]) -> str:
    facility_type = str(item.get("type") or "")
    if facility_type in {"public_jetty", "public_pier", "public_wharf", "fishing_platform", "official_fishing_spot"}:
        return "fixed_fishing_structure"
    if facility_type in {"beach_access", "rocky_shoreline"}:
        return facility_type
    return facility_type


def _near_duplicate_facility(item: Mapping[str, Any], existing: Mapping[str, Any]) -> bool:
    if not item.get("planner_eligible") or not existing.get("planner_eligible"):
        return False
    if item.get("access") != "public" or existing.get("access") != "public":
        return False
    if _facility_group(item) != _facility_group(existing):
        return False
    item_coords = _facility_coords(item)
    existing_coords = _facility_coords(existing)
    if item_coords is None or existing_coords is None:
        return False
    return _distance_km(*item_coords, *existing_coords) <= NEAR_DUPLICATE_DISTANCE_KM


def fetch_osm_structure_facilities(
    lat: float,
    lon: float,
    *,
    radius_m: int = 1200,
    endpoint: str = OVERPASS_ENDPOINT,
    timeout_seconds: int = 30,
    cache_enabled: bool = True,
    cache_dir: str | Path | None = None,
) -> dict[str, Any]:
    params = {
        "lat": round(lat, 5),
        "lon": round(lon, 5),
        "radius_m": radius_m,
        "endpoint": endpoint,
        "contract_version": STRUCTURE_CONTRACT_VERSION,
    }
    if cache_enabled:
        cached = get_json_cache("osm_structures", params, cache_dir=cache_dir, ttl_seconds=7 * 24 * 3600)
        if cached is not None:
            return cached

    query = _overpass_query(lat, lon, radius_m)
    request = Request(
        endpoint,
        data=urlencode({"data": query}).encode("utf-8"),
        headers={"User-Agent": "coastal-fishing-forecast/0.1"},
        method="POST",
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        raw_payload = json.loads(response.read().decode("utf-8"))

    result = {
        "contract_version": STRUCTURE_CONTRACT_VERSION,
        "source": "osm_overpass",
        "query": {"latitude": lat, "longitude": lon, "radius_m": radius_m},
        "facilities": normalize_osm_structure_facilities(raw_payload, lat=lat, lon=lon),
    }
    if cache_enabled:
        set_json_cache("osm_structures", params, result, cache_dir=cache_dir)
    return result


def fetch_list_mast_structure_facilities(
    lat: float,
    lon: float,
    *,
    radius_m: int = 2000,
    endpoint: str = LIST_MAST_BOAT_RAMPS_ENDPOINT,
    timeout_seconds: int = 30,
    cache_enabled: bool = True,
    cache_dir: str | Path | None = None,
) -> dict[str, Any]:
    params = {
        "lat": round(lat, 5),
        "lon": round(lon, 5),
        "radius_m": radius_m,
        "endpoint": endpoint,
        "contract_version": STRUCTURE_CONTRACT_VERSION,
    }
    if cache_enabled:
        cached = get_json_cache("list_mast_structures", params, cache_dir=cache_dir, ttl_seconds=7 * 24 * 3600)
        if cached is not None:
            return cached

    query_params = {
        "f": "json",
        "where": "1=1",
        "outFields": "*",
        "returnGeometry": "true",
        "geometry": f"{lon},{lat}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "distance": str(radius_m),
        "units": "esriSRUnit_Meter",
        "outSR": "4326",
    }
    request = Request(
        f"{endpoint}?{urlencode(query_params)}",
        headers={"User-Agent": "coastal-fishing-forecast/0.1"},
        method="GET",
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        raw_payload = json.loads(response.read().decode("utf-8"))

    if raw_payload.get("error"):
        raise ValueError(f"LIST/MAST query failed: {raw_payload['error']}")

    result = {
        "contract_version": STRUCTURE_CONTRACT_VERSION,
        "source": "list_mast",
        "query": {"latitude": lat, "longitude": lon, "radius_m": radius_m},
        "facilities": normalize_list_mast_facilities(raw_payload, lat=lat, lon=lon),
    }
    if cache_enabled:
        set_json_cache("list_mast_structures", params, result, cache_dir=cache_dir)
    return result


def fetch_list_wildfisheries_sea_spots(
    lat: float,
    lon: float,
    *,
    radius_m: int = 2000,
    endpoint: str = LIST_WILDFISHERIES_SEA_SPOTS_ENDPOINT,
    timeout_seconds: int = 30,
    cache_enabled: bool = True,
    cache_dir: str | Path | None = None,
) -> dict[str, Any]:
    # Cache the official catalogue once, then compute distance from the active search
    # point on each forecast request.
    cache_params = {
        "endpoint": endpoint,
        "contract_version": STRUCTURE_CONTRACT_VERSION,
        "scope": "all_sea_fishing_spots",
    }
    raw_payload = None
    if cache_enabled:
        cached = get_json_cache(
            "list_wildfisheries_sea_spots_catalog",
            cache_params,
            cache_dir=cache_dir,
            ttl_seconds=7 * 24 * 3600,
        )
        if cached is not None:
            raw_payload = cached

    if raw_payload is None:
        features = []
        result_offset = 0
        page_size = 2000
        while True:
            query_params = {
                "f": "json",
                "where": "1=1",
                "outFields": "*",
                "returnGeometry": "true",
                "outSR": "4326",
                "resultOffset": str(result_offset),
                "resultRecordCount": str(page_size),
            }
            request = Request(
                f"{endpoint}?{urlencode(query_params)}",
                headers={"User-Agent": "coastal-fishing-forecast/0.1"},
                method="GET",
            )
            with urlopen(request, timeout=timeout_seconds) as response:
                page_payload = json.loads(response.read().decode("utf-8"))

            if page_payload.get("error"):
                raise ValueError(f"LIST WildFisheries query failed: {page_payload['error']}")

            page_features = page_payload.get("features") or []
            features.extend(page_features)
            if not page_payload.get("exceededTransferLimit") or len(page_features) < page_size:
                raw_payload = {**page_payload, "features": features, "exceededTransferLimit": False}
                break
            result_offset += page_size

    if raw_payload.get("error"):
        raise ValueError(f"LIST WildFisheries query failed: {raw_payload['error']}")

    if cache_enabled:
        set_json_cache("list_wildfisheries_sea_spots_catalog", cache_params, raw_payload, cache_dir=cache_dir)

    result = {
        "contract_version": STRUCTURE_CONTRACT_VERSION,
        "source": "list_wildfisheries",
        "query": {
            "latitude": lat,
            "longitude": lon,
            "radius_m": radius_m,
            "scope": "all_sea_fishing_spots",
            "catalog_count": len(raw_payload.get("features") or []),
        },
        "facilities": normalize_list_wildfisheries_sea_spots(raw_payload, lat=lat, lon=lon),
    }
    return result


def fetch_combined_structure_facilities(
    lat: float,
    lon: float,
    *,
    radius_m: int = 1200,
    timeout_seconds: int = 8,
    cache_enabled: bool = True,
    cache_dir: str | Path | None = None,
) -> dict[str, Any]:
    fetchers = (
        ("list_wildfisheries", fetch_list_wildfisheries_sea_spots),
        ("list_mast", fetch_list_mast_structure_facilities),
        ("osm_overpass", fetch_osm_structure_facilities),
    )
    source_results: dict[str, dict[str, Any]] = {}
    facilities: list[dict[str, Any]] = []

    def run_fetch(source_name: str, fetcher) -> tuple[str, dict[str, Any]]:
        try:
            result = fetcher(
                lat,
                lon,
                radius_m=radius_m,
                timeout_seconds=timeout_seconds,
                cache_enabled=cache_enabled,
                cache_dir=cache_dir,
            )
            return source_name, {"source": source_name, "status": "ok", "result": result}
        except (OSError, TimeoutError, ValueError, KeyError, TypeError) as exc:
            return source_name, {"source": source_name, "status": "unavailable", "message": str(exc)}

    with ThreadPoolExecutor(max_workers=len(fetchers)) as executor:
        futures = [executor.submit(run_fetch, source_name, fetcher) for source_name, fetcher in fetchers]
        for future in futures:
            source_name, source_result = future.result()
            source_results[source_name] = source_result

    sources = []
    for source_name, _fetcher in fetchers:
        source_result = source_results[source_name]
        if source_result["status"] == "ok":
            result = source_result["result"]
            sources.append({"source": source_name, "status": "ok", "count": len(result["facilities"])})
            facilities.extend(result["facilities"])
        else:
            sources.append({
                "source": source_name,
                "status": "unavailable",
                "message": str(source_result.get("message") or ""),
            })

    return {
        "contract_version": STRUCTURE_CONTRACT_VERSION,
        "source": "combined",
        "sources": sources,
        "query": {"latitude": lat, "longitude": lon, "radius_m": radius_m},
        "facilities": _dedupe_facilities(facilities),
    }
