"""Public coastal structure lookup from OpenStreetMap/Overpass."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from math import atan2, cos, radians, sin, sqrt
import json
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from coastal_fishing_forecast.cache import get_json_cache, set_json_cache


OVERPASS_ENDPOINT = "https://overpass-api.de/api/interpreter"
LIST_MAST_BOAT_RAMPS_ENDPOINT = "https://services.thelist.tas.gov.au/arcgis/rest/services/Public/TopographyAndRelief/MapServer/33/query"
LIST_WILDFISHERIES_SEA_SPOTS_ENDPOINT = "https://services.thelist.tas.gov.au/arcgis/rest/services/Public/WildFisheries/MapServer/0/query"
NSW_MARITIME_BOAT_RAMPS_GEOJSON_ENDPOINT = "https://opendata.transport.nsw.gov.au/data/dataset/912cd680-15ed-4be5-9d09-1a9d0f15e6ee/resource/7c4ca115-ee33-4f6e-9821-b75040ba5cf6/download/boating_ramps.geojson"
QLD_RECREATIONAL_BOATING_FACILITIES_ENDPOINT = "https://queensland.opendatasoft.com/api/explore/v2.1/catalog/datasets/recreational-boating-facilities-queensland/records"
VIC_BOATING_FACILITIES_ENDPOINT = "https://www.boating.vic.gov.au/api/v1/facilities"
WA_PUBLIC_BOAT_RAMPS_ARCGIS_BASE = "https://public-services.slip.wa.gov.au/public/rest/services/SLIP_Public_Services/Infrastructure_and_Utilities/MapServer"
SA_TOPOGRAPHIC_BOAT_RAMPS_ENDPOINT = "https://maps.sa.gov.au/arcgis/rest/services/BaseMaps/Topographic_wmas/MapServer/47/query"
NT_PUBLIC_BOAT_RAMPS_KML_ENDPOINT = "https://www.google.com/maps/d/kml?mid=1vaBET4keIKNQy1bJXgPfoofMk9c&forcekml=1"
OFFICIAL_FISHING_SPOTS_RESOURCE = Path(__file__).with_name("resources") / "official_fishing_spots_2026-05-24.json"
STRUCTURE_CONTRACT_VERSION = "2026-04-28.structure_facilities.v1"
PUBLIC_ACCESS_VALUES = {"public", "yes", "permissive", "designated"}
PRIVATE_ACCESS_VALUES = {"private", "no", "customers"}
FEE_REQUIRED_VALUES = {"yes", "required", "true", "1", "paid", "fee"}
PLANNER_ELIGIBLE_TYPES = {
    "beach_access",
    "fishing_platform",
    "official_fishing_spot",
    "public_jetty",
    "rocky_shoreline",
}
MAP_ELIGIBLE_TYPES = PLANNER_ELIGIBLE_TYPES | {"boat_ramp"}
NEAR_DUPLICATE_DISTANCE_KM = 0.08
POINT_SPECIFIC_OFFICIAL_COORDINATE_ROLES = {
    "official_coordinate",
    "official_coordinate_reference",
    "official_map_coordinate",
    "official_reef_coordinate",
}
POINT_SPECIFIC_OFFICIAL_SPOT_TYPES = {
    "boat_ramp",
    "artificial_reef",
    "breakwater",
    "bridge",
    "fad",
    "ferry_wharf",
    "fishing_platform",
    "jetty",
    "kingfish_artificial_reef_module",
    "pier",
    "pontoon",
    "public_jetty",
    "public_pier",
    "public_wharf",
    "wharf",
}
POINT_SPECIFIC_OFFICIAL_LABEL_TERMS = (
    "boat ramp",
    "breakwater",
    "bridge",
    "fishing platform",
    "jetty",
    "pier",
    "pontoon",
    "ramp",
    "wharf",
)
AREA_STYLE_OFFICIAL_LABEL_TERMS = ("jetties", "wharves")
WA_PUBLIC_BOAT_RAMPS_LAYERS = {
    "sealed": 49,
    "unsealed": 50,
    "paddle_craft": 51,
}
JURISDICTION_BBOXES = (
    ("tas", -44.0, -39.0, 143.5, 148.9),
    ("act", -36.1, -35.0, 148.7, 149.5),
    ("nt", -26.2, -10.0, 129.0, 138.2),
    ("vic", -39.4, -33.8, 140.8, 150.2),
    ("nsw", -37.7, -28.0, 140.8, 154.2),
    ("qld", -29.4, -9.0, 137.0, 154.2),
    ("sa", -38.4, -25.8, 129.0, 141.1),
    ("wa", -35.2, -13.0, 112.0, 129.1),
)


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * radius_km * atan2(sqrt(a), sqrt(1 - a))


def _jurisdiction_for_coordinates(lat: float, lon: float) -> str:
    for jurisdiction, min_lat, max_lat, min_lon, max_lon in JURISDICTION_BBOXES:
        if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
            return jurisdiction
    return "unknown"


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
  node(around:{radius_m},{lat},{lon})["amenity"="boat_ramp"];
  way(around:{radius_m},{lat},{lon})["amenity"="boat_ramp"];
  relation(around:{radius_m},{lat},{lon})["amenity"="boat_ramp"];
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
    fee = str(tags.get("fee") or "").lower()
    name = str(tags.get("name") or "").lower()
    if fee in FEE_REQUIRED_VALUES:
        return "private"
    if access in PRIVATE_ACCESS_VALUES:
        return "private"
    if access in PUBLIC_ACCESS_VALUES:
        return "public"
    if "public jetty" in name or "public pier" in name or "public wharf" in name:
        return "public"
    return "unknown"


def _facility_type(tags: Mapping[str, Any], public_access_status: str) -> str | None:
    amenity = str(tags.get("amenity") or "").lower()
    man_made = str(tags.get("man_made") or "").lower()
    leisure = str(tags.get("leisure") or "").lower()
    sport = str(tags.get("sport") or "").lower()
    fishing = str(tags.get("fishing") or "").lower()
    if man_made in {"pier", "jetty"}:
        return "public_jetty" if public_access_status == "public" else "pier"
    if leisure == "slipway" or amenity == "boat_ramp":
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


@lru_cache(maxsize=1)
def _official_fishing_spot_rows(resource_path: str = str(OFFICIAL_FISHING_SPOTS_RESOURCE)) -> tuple[Mapping[str, Any], ...]:
    path = Path(resource_path)
    if not path.exists():
        return ()
    rows = json.loads(path.read_text(encoding="utf-8"))
    return tuple(row for row in rows if isinstance(row, Mapping))


def _official_spot_facility_type(spot_type: Any) -> str:
    text = _text_value(spot_type).lower()
    if "boat_ramp" in text:
        return "boat_ramp"
    if text == "fad":
        return "fad"
    if "reef" in text:
        return "artificial_reef"
    if any(word in text for word in ("jetty", "pier", "wharf", "pontoon", "breakwater", "harbour")):
        return "public_jetty"
    if "beach" in text:
        return "beach_access"
    if any(word in text for word in ("rock", "headland", "shoreline", "ledge")):
        return "rocky_shoreline"
    return "official_fishing_spot"


def _official_spot_access(row: Mapping[str, Any], facility_type: str) -> str:
    if facility_type in {"fad", "artificial_reef"} or str(row.get("scope") or "").endswith("_boat"):
        return "open_water"
    return "public"


def _official_spot_is_point_specific(row: Mapping[str, Any]) -> bool:
    role = _text_value(row.get("role")).lower()
    if role == "future_freshwater_reference":
        return False

    coordinate_role = _text_value(row.get("coordinate_role")).lower()
    if coordinate_role in POINT_SPECIFIC_OFFICIAL_COORDINATE_ROLES:
        return True

    spot_type = _text_value(row.get("spot_type")).lower()
    label = _text_value(row.get("spot_name")).lower()
    if any(term in label for term in AREA_STYLE_OFFICIAL_LABEL_TERMS):
        return False
    if spot_type in POINT_SPECIFIC_OFFICIAL_SPOT_TYPES:
        return True
    return any(term in label for term in POINT_SPECIFIC_OFFICIAL_LABEL_TERMS)


def normalize_official_fishing_spots(
    rows: tuple[Mapping[str, Any], ...] | list[Mapping[str, Any]],
    *,
    lat: float,
    lon: float,
    radius_m: int,
) -> list[dict[str, Any]]:
    facilities = []
    for row in rows:
        if not row.get("map_eligible", True):
            continue
        if not _official_spot_is_point_specific(row):
            continue
        try:
            facility_lat = float(row["latitude"])
            facility_lon = float(row["longitude"])
        except (KeyError, TypeError, ValueError):
            continue
        distance_km = _distance_km(lat, lon, facility_lat, facility_lon)
        if distance_km > radius_m / 1000:
            continue
        facility_type = _official_spot_facility_type(row.get("spot_type"))
        access = _official_spot_access(row, facility_type)
        planner_eligible = access == "public" and bool(row.get("planner_eligible")) and facility_type in PLANNER_ELIGIBLE_TYPES
        role = _text_value(row.get("role")) or ("public_fishing_access" if planner_eligible else "map_reference")
        facilities.append(
            {
                "id": f"official_fishing_spots:{row.get('id')}",
                "type": facility_type,
                "label": _clean_label(row.get("spot_name"), "Mapped fishing spot"),
                "access": access,
                "status": "confirmed" if not role.startswith("supplemental_") else "needs_review",
                "source": "official_fishing_spots",
                "coordinates": {"latitude": facility_lat, "longitude": facility_lon},
                "distance_km": round(distance_km, 3),
                "planner_eligible": planner_eligible,
                "map_eligible": True,
                "role": role,
                "attributes": {
                    "jurisdiction": row.get("jurisdiction"),
                    "guide_name": row.get("guide_name"),
                    "source_kind": row.get("source_kind"),
                    "official_owner": row.get("official_owner"),
                    "official_url": row.get("official_url"),
                    "score_impact": row.get("score_impact"),
                    "review_status": row.get("review_status"),
                },
            }
        )
    facilities.sort(key=lambda item: (not item["planner_eligible"], item["distance_km"], item["label"]))
    return facilities


def _public_boat_ramp_facility(
    *,
    source: str,
    source_id: Any,
    label: Any,
    facility_lat: float,
    facility_lon: float,
    query_lat: float,
    query_lon: float,
    attributes: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": f"{source}:{source_id}",
        "type": "boat_ramp",
        "label": _clean_label(label, "Public boat ramp"),
        "access": "public",
        "status": "confirmed",
        "source": source,
        "coordinates": {"latitude": facility_lat, "longitude": facility_lon},
        "distance_km": round(_distance_km(query_lat, query_lon, facility_lat, facility_lon), 3),
        "attributes": dict(attributes or {}),
        "planner_eligible": False,
        "map_eligible": True,
        "role": "public_access_only",
    }


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


def _geojson_point_coordinates(feature: Mapping[str, Any]) -> tuple[float, float] | None:
    geometry = feature.get("geometry")
    if not isinstance(geometry, Mapping):
        return None
    if geometry.get("type") != "Point":
        return None
    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list | tuple) or len(coordinates) < 2:
        return None
    return float(coordinates[1]), float(coordinates[0])


def _arcgis_point_coordinates(feature: Mapping[str, Any]) -> tuple[float, float] | None:
    geometry = feature.get("geometry")
    if not isinstance(geometry, Mapping):
        return None
    if "x" in geometry and "y" in geometry:
        return float(geometry["y"]), float(geometry["x"])
    return None


def _text_value(value: Any) -> str:
    return str(value or "").strip()


def _is_fee_required(value: Any) -> bool:
    return _text_value(value).lower() in FEE_REQUIRED_VALUES


def normalize_nsw_boat_ramp_facilities(
    payload: Mapping[str, Any],
    *,
    lat: float,
    lon: float,
    radius_m: int,
) -> list[dict[str, Any]]:
    facilities = []
    for feature in payload.get("features", []):
        if not isinstance(feature, Mapping):
            continue
        coords = _geojson_point_coordinates(feature)
        if coords is None:
            continue
        facility_lat, facility_lon = coords
        if _distance_km(lat, lon, facility_lat, facility_lon) > radius_m / 1000:
            continue
        properties = feature.get("properties") or {}
        if not isinstance(properties, Mapping):
            properties = {}
        if _is_fee_required(properties.get("FEE_PAYABLE")):
            continue
        label = properties.get("DESCRIPTION") or properties.get("SUBURB") or "NSW boat ramp"
        facilities.append(
            _public_boat_ramp_facility(
                source="nsw_maritime_boat_ramps",
                source_id=properties.get("BOAT_RAMP_ID") or properties.get("OBJECTID") or label,
                label=label,
                facility_lat=facility_lat,
                facility_lon=facility_lon,
                query_lat=lat,
                query_lon=lon,
                attributes=properties,
            )
        )
    facilities.sort(key=lambda item: (item["distance_km"], item["label"]))
    return facilities


def normalize_qld_boating_facilities(
    payload: Mapping[str, Any],
    *,
    lat: float,
    lon: float,
    radius_m: int,
) -> list[dict[str, Any]]:
    facilities = []
    for record in payload.get("results", []):
        if not isinstance(record, Mapping):
            continue
        facility = _text_value(record.get("facility")).lower()
        if "boat ramp" not in facility and "canoe ramp" not in facility:
            continue
        facility_lat = record.get("latitude")
        facility_lon = record.get("longitude")
        if facility_lat is None or facility_lon is None:
            point = record.get("geo_point_2d") or {}
            if isinstance(point, Mapping):
                facility_lat = point.get("lat")
                facility_lon = point.get("lon")
        if facility_lat is None or facility_lon is None:
            continue
        facility_lat = float(facility_lat)
        facility_lon = float(facility_lon)
        if _distance_km(lat, lon, facility_lat, facility_lon) > radius_m / 1000:
            continue
        label = record.get("name") or record.get("location") or "Queensland boat ramp"
        facilities.append(
            _public_boat_ramp_facility(
                source="qld_recreational_boating_facilities",
                source_id=record.get("tmr_id") or label,
                label=label,
                facility_lat=facility_lat,
                facility_lon=facility_lon,
                query_lat=lat,
                query_lon=lon,
                attributes=record,
            )
        )
    facilities.sort(key=lambda item: (item["distance_km"], item["label"]))
    return facilities


def normalize_vic_boating_facilities(
    payload: list[Any],
    *,
    lat: float,
    lon: float,
    radius_m: int,
) -> list[dict[str, Any]]:
    facilities = []
    for record in payload:
        if not isinstance(record, Mapping):
            continue
        facility_lat = record.get("latitude")
        facility_lon = record.get("longitude")
        if facility_lat is None or facility_lon is None:
            continue
        facility_lat = float(facility_lat)
        facility_lon = float(facility_lon)
        if _distance_km(lat, lon, facility_lat, facility_lon) > radius_m / 1000:
            continue
        if bool(record.get("isDeleted")) or _text_value(record.get("pagestatus")).lower() == "hide":
            continue
        if _text_value(record.get("status")).lower() == "closed":
            continue
        label = record.get("name") or record.get("commonName") or "Victoria boat ramp"
        facilities.append(
            _public_boat_ramp_facility(
                source="vic_boating_facilities",
                source_id=record.get("facilityId") or label,
                label=label,
                facility_lat=facility_lat,
                facility_lon=facility_lon,
                query_lat=lat,
                query_lon=lon,
                attributes=record,
            )
        )
    facilities.sort(key=lambda item: (item["distance_km"], item["label"]))
    return facilities


def normalize_wa_public_boat_ramps(
    payload: Mapping[str, Any],
    *,
    lat: float,
    lon: float,
    source_layer: str,
) -> list[dict[str, Any]]:
    facilities = []
    for feature in payload.get("features", []):
        if not isinstance(feature, Mapping):
            continue
        coords = _arcgis_point_coordinates(feature)
        if coords is None:
            continue
        attributes = feature.get("attributes") or {}
        if not isinstance(attributes, Mapping):
            attributes = {}
        facility_lat, facility_lon = coords
        label = attributes.get("name_of_boat_ramp") or attributes.get("assetdesc") or f"WA {source_layer} boat ramp"
        source_id = attributes.get("objectid") or attributes.get("ci_id") or label
        facilities.append(
            _public_boat_ramp_facility(
                source="wa_public_boat_ramps",
                source_id=f"{source_layer}:{source_id}",
                label=label,
                facility_lat=facility_lat,
                facility_lon=facility_lon,
                query_lat=lat,
                query_lon=lon,
                attributes={**dict(attributes), "source_layer": source_layer},
            )
        )
    facilities.sort(key=lambda item: (item["distance_km"], item["label"]))
    return facilities


def normalize_sa_boat_ramp_facilities(
    payload: Mapping[str, Any],
    *,
    lat: float,
    lon: float,
) -> list[dict[str, Any]]:
    facilities = []
    for feature in payload.get("features", []):
        if not isinstance(feature, Mapping):
            continue
        coords = _arcgis_point_coordinates(feature)
        if coords is None:
            continue
        attributes = feature.get("attributes") or {}
        if not isinstance(attributes, Mapping):
            attributes = {}
        facility_lat, facility_lon = coords
        comments = _text_value(attributes.get("COMMENTS")).lower()
        if "private" in comments or "closed" in comments:
            continue
        label = attributes.get("BOATRAMP") or "SA boat ramp"
        facilities.append(
            _public_boat_ramp_facility(
                source="sa_boat_ramps",
                source_id=attributes.get("OBJECTID") or label,
                label=label,
                facility_lat=facility_lat,
                facility_lon=facility_lon,
                query_lat=lat,
                query_lon=lon,
                attributes=attributes,
            )
        )
    facilities.sort(key=lambda item: (item["distance_km"], item["label"]))
    return facilities


def normalize_nt_public_boat_ramps(
    payload: str,
    *,
    lat: float,
    lon: float,
    radius_m: int,
) -> list[dict[str, Any]]:
    facilities = []
    namespace = {"kml": "http://www.opengis.net/kml/2.2"}
    root = ET.fromstring(payload)
    for placemark in root.findall(".//kml:Placemark", namespace):
        name_node = placemark.find("kml:name", namespace)
        coordinates_node = placemark.find(".//kml:Point/kml:coordinates", namespace)
        if name_node is None or coordinates_node is None or not coordinates_node.text:
            continue
        coordinate_parts = coordinates_node.text.strip().split(",")
        if len(coordinate_parts) < 2:
            continue
        facility_lon = float(coordinate_parts[0])
        facility_lat = float(coordinate_parts[1])
        if _distance_km(lat, lon, facility_lat, facility_lon) > radius_m / 1000:
            continue
        attributes = {}
        for data_node in placemark.findall(".//kml:Data", namespace):
            key = data_node.attrib.get("name")
            value_node = data_node.find("kml:value", namespace)
            if key and value_node is not None:
                attributes[key] = value_node.text or ""
        warning = _text_value(attributes.get("Status / Warning")).lower()
        if "closed" in warning and "reopened" not in warning:
            continue
        label = name_node.text or "NT public boat ramp"
        facilities.append(
            _public_boat_ramp_facility(
                source="nt_public_boat_ramps",
                source_id=label,
                label=label,
                facility_lat=facility_lat,
                facility_lon=facility_lon,
                query_lat=lat,
                query_lon=lon,
                attributes=attributes,
            )
        )
    facilities.sort(key=lambda item: (item["distance_km"], item["label"]))
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
    if facility_type in {"fad", "artificial_reef"}:
        return facility_type
    return facility_type


def _near_duplicate_facility(item: Mapping[str, Any], existing: Mapping[str, Any]) -> bool:
    if not item.get("map_eligible") or not existing.get("map_eligible"):
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


def fetch_nsw_boat_ramp_facilities(
    lat: float,
    lon: float,
    *,
    radius_m: int = 2000,
    endpoint: str = NSW_MARITIME_BOAT_RAMPS_GEOJSON_ENDPOINT,
    timeout_seconds: int = 30,
    cache_enabled: bool = True,
    cache_dir: str | Path | None = None,
) -> dict[str, Any]:
    cache_params = {
        "endpoint": endpoint,
        "contract_version": STRUCTURE_CONTRACT_VERSION,
        "scope": "all_nsw_boat_ramps",
    }
    raw_payload = None
    if cache_enabled:
        raw_payload = get_json_cache(
            "nsw_boat_ramps_catalog",
            cache_params,
            cache_dir=cache_dir,
            ttl_seconds=7 * 24 * 3600,
        )

    if raw_payload is None:
        request = Request(endpoint, headers={"User-Agent": "coastal-fishing-forecast/0.1"}, method="GET")
        with urlopen(request, timeout=timeout_seconds) as response:
            raw_payload = json.loads(response.read().decode("utf-8"))
        if cache_enabled:
            set_json_cache("nsw_boat_ramps_catalog", cache_params, raw_payload, cache_dir=cache_dir)

    return {
        "contract_version": STRUCTURE_CONTRACT_VERSION,
        "source": "nsw_maritime_boat_ramps",
        "query": {"latitude": lat, "longitude": lon, "radius_m": radius_m},
        "facilities": normalize_nsw_boat_ramp_facilities(raw_payload, lat=lat, lon=lon, radius_m=radius_m),
    }


def fetch_qld_boating_facilities(
    lat: float,
    lon: float,
    *,
    radius_m: int = 2000,
    endpoint: str = QLD_RECREATIONAL_BOATING_FACILITIES_ENDPOINT,
    timeout_seconds: int = 30,
    cache_enabled: bool = True,
    cache_dir: str | Path | None = None,
) -> dict[str, Any]:
    cache_params = {
        "endpoint": endpoint,
        "contract_version": STRUCTURE_CONTRACT_VERSION,
        "scope": "all_qld_recreational_boating_facilities",
    }
    raw_payload = None
    if cache_enabled:
        raw_payload = get_json_cache(
            "qld_recreational_boating_facilities_catalog",
            cache_params,
            cache_dir=cache_dir,
            ttl_seconds=7 * 24 * 3600,
        )

    if raw_payload is None:
        results = []
        total_count = None
        offset = 0
        page_size = 100
        while total_count is None or offset < total_count:
            request = Request(
                f"{endpoint}?{urlencode({'limit': str(page_size), 'offset': str(offset)})}",
                headers={"User-Agent": "coastal-fishing-forecast/0.1"},
                method="GET",
            )
            with urlopen(request, timeout=timeout_seconds) as response:
                page_payload = json.loads(response.read().decode("utf-8"))
            page_results = page_payload.get("results") or []
            total_count = int(page_payload.get("total_count") or len(page_results))
            results.extend(page_results)
            if not page_results:
                break
            offset += len(page_results)
        raw_payload = {"total_count": total_count or len(results), "results": results}
        if cache_enabled:
            set_json_cache("qld_recreational_boating_facilities_catalog", cache_params, raw_payload, cache_dir=cache_dir)

    return {
        "contract_version": STRUCTURE_CONTRACT_VERSION,
        "source": "qld_recreational_boating_facilities",
        "query": {"latitude": lat, "longitude": lon, "radius_m": radius_m},
        "facilities": normalize_qld_boating_facilities(raw_payload, lat=lat, lon=lon, radius_m=radius_m),
    }


def fetch_vic_boating_facilities(
    lat: float,
    lon: float,
    *,
    radius_m: int = 2000,
    endpoint: str = VIC_BOATING_FACILITIES_ENDPOINT,
    timeout_seconds: int = 30,
    cache_enabled: bool = True,
    cache_dir: str | Path | None = None,
) -> dict[str, Any]:
    cache_params = {
        "endpoint": endpoint,
        "contract_version": STRUCTURE_CONTRACT_VERSION,
        "scope": "all_vic_boating_facilities",
    }
    raw_payload = None
    if cache_enabled:
        raw_payload = get_json_cache(
            "vic_boating_facilities_catalog",
            cache_params,
            cache_dir=cache_dir,
            ttl_seconds=6 * 3600,
        )

    if raw_payload is None:
        request = Request(endpoint, headers={"User-Agent": "coastal-fishing-forecast/0.1"}, method="GET")
        with urlopen(request, timeout=timeout_seconds) as response:
            raw_payload = json.loads(response.read().decode("utf-8"))
        if cache_enabled:
            set_json_cache("vic_boating_facilities_catalog", cache_params, raw_payload, cache_dir=cache_dir)

    return {
        "contract_version": STRUCTURE_CONTRACT_VERSION,
        "source": "vic_boating_facilities",
        "query": {"latitude": lat, "longitude": lon, "radius_m": radius_m},
        "facilities": normalize_vic_boating_facilities(raw_payload, lat=lat, lon=lon, radius_m=radius_m),
    }


def fetch_wa_public_boat_ramps(
    lat: float,
    lon: float,
    *,
    radius_m: int = 2000,
    endpoint: str = WA_PUBLIC_BOAT_RAMPS_ARCGIS_BASE,
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
        cached = get_json_cache("wa_public_boat_ramps", params, cache_dir=cache_dir, ttl_seconds=7 * 24 * 3600)
        if cached is not None:
            return cached

    facilities: list[dict[str, Any]] = []
    layer_counts: dict[str, int] = {}
    for layer_name, layer_id in WA_PUBLIC_BOAT_RAMPS_LAYERS.items():
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
            "resultRecordCount": "200",
        }
        request = Request(
            f"{endpoint}/{layer_id}/query?{urlencode(query_params)}",
            headers={"User-Agent": "coastal-fishing-forecast/0.1"},
            method="GET",
        )
        with urlopen(request, timeout=timeout_seconds) as response:
            raw_payload = json.loads(response.read().decode("utf-8"))
        if raw_payload.get("error"):
            raise ValueError(f"WA boat ramp query failed: {raw_payload['error']}")
        normalized = normalize_wa_public_boat_ramps(raw_payload, lat=lat, lon=lon, source_layer=layer_name)
        layer_counts[layer_name] = len(normalized)
        facilities.extend(normalized)

    result = {
        "contract_version": STRUCTURE_CONTRACT_VERSION,
        "source": "wa_public_boat_ramps",
        "query": {"latitude": lat, "longitude": lon, "radius_m": radius_m, "layer_counts": layer_counts},
        "facilities": facilities,
    }
    if cache_enabled:
        set_json_cache("wa_public_boat_ramps", params, result, cache_dir=cache_dir)
    return result


def fetch_sa_boat_ramp_facilities(
    lat: float,
    lon: float,
    *,
    radius_m: int = 2000,
    endpoint: str = SA_TOPOGRAPHIC_BOAT_RAMPS_ENDPOINT,
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
        cached = get_json_cache("sa_boat_ramps", params, cache_dir=cache_dir, ttl_seconds=7 * 24 * 3600)
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
        "resultRecordCount": "200",
    }
    request = Request(
        f"{endpoint}?{urlencode(query_params)}",
        headers={"User-Agent": "coastal-fishing-forecast/0.1"},
        method="GET",
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        raw_payload = json.loads(response.read().decode("utf-8"))
    if raw_payload.get("error"):
        raise ValueError(f"SA boat ramp query failed: {raw_payload['error']}")

    result = {
        "contract_version": STRUCTURE_CONTRACT_VERSION,
        "source": "sa_boat_ramps",
        "query": {"latitude": lat, "longitude": lon, "radius_m": radius_m},
        "facilities": normalize_sa_boat_ramp_facilities(raw_payload, lat=lat, lon=lon),
    }
    if cache_enabled:
        set_json_cache("sa_boat_ramps", params, result, cache_dir=cache_dir)
    return result


def fetch_nt_public_boat_ramps(
    lat: float,
    lon: float,
    *,
    radius_m: int = 2000,
    endpoint: str = NT_PUBLIC_BOAT_RAMPS_KML_ENDPOINT,
    timeout_seconds: int = 30,
    cache_enabled: bool = True,
    cache_dir: str | Path | None = None,
) -> dict[str, Any]:
    cache_params = {
        "endpoint": endpoint,
        "contract_version": STRUCTURE_CONTRACT_VERSION,
        "scope": "all_nt_public_boat_ramps",
    }
    raw_payload = None
    if cache_enabled:
        raw_payload = get_json_cache(
            "nt_public_boat_ramps_catalog",
            cache_params,
            cache_dir=cache_dir,
            ttl_seconds=24 * 3600,
        )

    if raw_payload is None:
        request = Request(endpoint, headers={"User-Agent": "coastal-fishing-forecast/0.1"}, method="GET")
        with urlopen(request, timeout=timeout_seconds) as response:
            raw_payload = {"kml": response.read().decode("utf-8")}
        if cache_enabled:
            set_json_cache("nt_public_boat_ramps_catalog", cache_params, raw_payload, cache_dir=cache_dir)

    return {
        "contract_version": STRUCTURE_CONTRACT_VERSION,
        "source": "nt_public_boat_ramps",
        "query": {"latitude": lat, "longitude": lon, "radius_m": radius_m},
        "facilities": normalize_nt_public_boat_ramps(raw_payload["kml"], lat=lat, lon=lon, radius_m=radius_m),
    }


def fetch_official_fishing_spot_facilities(
    lat: float,
    lon: float,
    *,
    radius_m: int = 5000,
    timeout_seconds: int = 30,
    cache_enabled: bool = True,
    cache_dir: str | Path | None = None,
) -> dict[str, Any]:
    del timeout_seconds, cache_enabled, cache_dir
    rows = _official_fishing_spot_rows()
    facilities = normalize_official_fishing_spots(rows, lat=lat, lon=lon, radius_m=radius_m)
    return {
        "contract_version": STRUCTURE_CONTRACT_VERSION,
        "source": "official_fishing_spots",
        "query": {
            "latitude": lat,
            "longitude": lon,
            "radius_m": radius_m,
            "catalog_count": len(rows),
        },
        "facilities": facilities,
    }


def _official_fetchers_for_jurisdiction(jurisdiction: str) -> tuple[tuple[str, Any], ...]:
    if jurisdiction == "tas":
        return (
            ("list_wildfisheries", fetch_list_wildfisheries_sea_spots),
            ("list_mast", fetch_list_mast_structure_facilities),
        )
    if jurisdiction == "nsw":
        return (("nsw_maritime_boat_ramps", fetch_nsw_boat_ramp_facilities),)
    if jurisdiction == "qld":
        return (("qld_recreational_boating_facilities", fetch_qld_boating_facilities),)
    if jurisdiction == "vic":
        return (("vic_boating_facilities", fetch_vic_boating_facilities),)
    if jurisdiction == "wa":
        return (("wa_public_boat_ramps", fetch_wa_public_boat_ramps),)
    if jurisdiction == "sa":
        return (("sa_boat_ramps", fetch_sa_boat_ramp_facilities),)
    if jurisdiction == "nt":
        return (("nt_public_boat_ramps", fetch_nt_public_boat_ramps),)
    return ()


def fetch_combined_structure_facilities(
    lat: float,
    lon: float,
    *,
    radius_m: int = 1200,
    timeout_seconds: int = 8,
    cache_enabled: bool = True,
    cache_dir: str | Path | None = None,
) -> dict[str, Any]:
    jurisdiction = _jurisdiction_for_coordinates(lat, lon)
    fetchers = (
        ("official_fishing_spots", fetch_official_fishing_spot_facilities),
        *_official_fetchers_for_jurisdiction(jurisdiction),
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
        "query": {"latitude": lat, "longitude": lon, "radius_m": radius_m, "jurisdiction": jurisdiction},
        "facilities": _dedupe_facilities(facilities),
    }
