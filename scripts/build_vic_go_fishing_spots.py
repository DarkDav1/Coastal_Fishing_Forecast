"""Build spot-level Victoria VFA Go Fishing map candidates."""

from __future__ import annotations

import csv
import json
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


OUTPUT_DIR = Path("docs/generated")
JSON_OUTPUT = OUTPUT_DIR / "vic_go_fishing_spots_2026-05-22.json"
CSV_OUTPUT = OUTPUT_DIR / "vic_go_fishing_spots_2026-05-22.csv"
USER_AGENT = "CoastalFishingForecast/0.1 vic-guide-spot-coordinate-builder"

WESTERN_PORT_URL = "https://vfa.vic.gov.au/__data/assets/pdf_file/0011/951473/VFA4000.05.23-GoFishing_WesternPortBay_WEB.pdf"
SOUTH_WEST_URL = "https://vfa.vic.gov.au/__data/assets/pdf_file/0010/951472/VFA4000.05.23-GoFishing_SouthWest_WEB.pdf"
PORT_PHILLIP_URL = "https://vfa.vic.gov.au/recreational-fishing/fishing-locations/go-fishing-port-phillip-bay"


SPOTS = [
    ("Western Port Bay", WESTERN_PORT_URL, "Bittern", "beach", "coastal_estuary"),
    ("Western Port Bay", WESTERN_PORT_URL, "Corinella Jetty", "jetty", "coastal_estuary"),
    ("Western Port Bay", WESTERN_PORT_URL, "Cowes Jetty", "jetty", "coastal_estuary"),
    ("Western Port Bay", WESTERN_PORT_URL, "Flinders Pier", "pier", "coastal_estuary"),
    ("Western Port Bay", WESTERN_PORT_URL, "Hastings", "foreshore_pier", "coastal_estuary"),
    ("Western Port Bay", WESTERN_PORT_URL, "Merricks Beach", "beach", "coastal_estuary"),
    ("Western Port Bay", WESTERN_PORT_URL, "Rhyll Jetty", "jetty", "coastal_estuary"),
    ("Western Port Bay", WESTERN_PORT_URL, "San Remo Jetty", "jetty", "coastal_estuary"),
    ("Western Port Bay", WESTERN_PORT_URL, "Stony Point Pier", "pier", "coastal_estuary"),
    ("Western Port Bay", WESTERN_PORT_URL, "Tooradin Inlet", "inlet", "tidal_estuary"),
    ("South West", SOUTH_WEST_URL, "Anglesea River", "river_jetty", "tidal_estuary"),
    ("South West", SOUTH_WEST_URL, "Bridgewater Bay", "beach_bay", "coastal_estuary"),
    ("South West", SOUTH_WEST_URL, "Boggy Creek Curdievale", "fishing_platform", "tidal_estuary"),
    ("South West", SOUTH_WEST_URL, "Hopkins River Warrnambool", "river_platform", "tidal_estuary"),
    ("South West", SOUTH_WEST_URL, "Lake Bolac", "lake", "future_freshwater"),
    ("South West", SOUTH_WEST_URL, "Lake Bullen Merri Camperdown", "lake", "future_freshwater"),
    ("South West", SOUTH_WEST_URL, "Lake Hamilton", "lake", "future_freshwater"),
    ("South West", SOUTH_WEST_URL, "Lake Purrumbete Camperdown", "lake", "future_freshwater"),
    ("South West", SOUTH_WEST_URL, "Lake Wendouree Ballarat", "lake", "future_freshwater"),
    ("South West", SOUTH_WEST_URL, "Lorne Pier", "pier", "coastal_estuary"),
    ("South West", SOUTH_WEST_URL, "Martins Point Port Fairy", "river_mouth", "coastal_estuary"),
    ("South West", SOUTH_WEST_URL, "Nelson Glenelg River", "estuary_river", "tidal_estuary"),
    ("South West", SOUTH_WEST_URL, "Portland Lee Breakwater", "breakwater", "coastal_estuary"),
    ("Port Phillip Bay", PORT_PHILLIP_URL, "Queenscliff Pier", "pier", "coastal_estuary"),
    ("Port Phillip Bay", PORT_PHILLIP_URL, "Cunningham Pier", "pier", "coastal_estuary"),
    ("Port Phillip Bay", PORT_PHILLIP_URL, "Werribee River", "river_mouth", "tidal_estuary"),
    ("Port Phillip Bay", PORT_PHILLIP_URL, "Ferguson Street Pier", "pier", "coastal_estuary"),
    ("Port Phillip Bay", PORT_PHILLIP_URL, "Mordialloc Pier", "pier", "coastal_estuary"),
    ("Port Phillip Bay", PORT_PHILLIP_URL, "Patterson River", "estuary_river", "tidal_estuary"),
    ("Port Phillip Bay", PORT_PHILLIP_URL, "Mornington Pier", "pier", "coastal_estuary"),
    ("Port Phillip Bay", PORT_PHILLIP_URL, "Sorrento Pier", "pier", "coastal_estuary"),
]


MANUAL_COORDINATES = {
    "Boggy Creek Curdievale": (-38.5144, 142.8822),
    "Martins Point Port Fairy": (-38.3892, 142.2447),
    "Portland Lee Breakwater": (-38.3478, 141.6165),
    "Tooradin Inlet": (-38.2148, 145.3823),
    "Queenscliff Pier": (-38.2670, 144.6626),
    "Cunningham Pier": (-38.1445, 144.3615),
    "Werribee River": (-37.9660, 144.6900),
    "Ferguson Street Pier": (-37.8639, 144.9068),
    "Mordialloc Pier": (-38.0066, 145.0861),
    "Patterson River": (-38.0665, 145.1240),
    "Mornington Pier": (-38.2142, 145.0345),
    "Sorrento Pier": (-38.3383, 144.7430),
}


def query_variants(name: str) -> list[str]:
    variants = [
        name,
        name.replace(" Jetty", ""),
        name.replace(" Pier", ""),
        name.replace(" Camperdown", ""),
        name.replace(" Warrnambool", ""),
        name.replace(" Glenelg River", ""),
    ]
    seen = []
    for variant in variants:
        cleaned = " ".join(variant.split())
        if cleaned and cleaned not in seen:
            seen.append(cleaned)
    return seen


def geocode(name: str) -> dict[str, object]:
    if name in MANUAL_COORDINATES:
        lat, lon = MANUAL_COORDINATES[name]
        return {
            "latitude": lat,
            "longitude": lon,
            "geocode_status": "manual_spot_coordinate",
            "geocode_label": name,
        }

    for variant in query_variants(name):
        for query in (
            f"{variant}, Victoria, Australia",
            f"{variant}, VIC, Australia",
            f"{variant}, Australia",
        ):
            url = "https://nominatim.openstreetmap.org/search?" + urlencode(
                {"q": query, "format": "jsonv2", "limit": "1", "countrycodes": "au"}
            )
            request = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
            if payload:
                match = payload[0]
                return {
                    "latitude": round(float(match["lat"]), 6),
                    "longitude": round(float(match["lon"]), 6),
                    "geocode_status": "nominatim_first_match",
                    "geocode_label": match.get("display_name") or query,
                }
            time.sleep(1.1)
    return {
        "latitude": None,
        "longitude": None,
        "geocode_status": "not_found_needs_review",
        "geocode_label": name,
    }


def clean_id(name: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in name.lower())
    return "_".join(part for part in cleaned.split("_") if part)


def build_rows() -> list[dict[str, object]]:
    rows = []
    for index, (guide_name, official_url, spot_name, spot_type, scope) in enumerate(SPOTS, start=1):
        coords = geocode(spot_name)
        rows.append(
            {
                "id": f"vic_go_fishing:{index:03d}:{clean_id(spot_name)}",
                "jurisdiction": "VIC",
                "guide_name": f"Go Fishing - {guide_name}",
                "spot_name": spot_name,
                "spot_type": spot_type,
                "scope": scope,
                "source_kind": "official_go_fishing_guide_map_label",
                "official_owner": "Victorian Fisheries Authority",
                "official_url": official_url,
                "latitude": coords["latitude"],
                "longitude": coords["longitude"],
                "coordinate_role": "spot_candidate",
                "geocode_status": coords["geocode_status"],
                "geocode_label": coords["geocode_label"],
                "planner_eligible": scope != "future_freshwater",
                "map_eligible": True,
                "role": "public_fishing_access_candidate" if scope != "future_freshwater" else "future_freshwater_reference",
                "score_impact": "none",
                "review_status": "needs_access_and_closure_check",
                "notes": "Named in a VFA Go Fishing guide. Verify local access, signage, and marine park or closure rules before user-facing planning.",
            }
        )
        if index < len(SPOTS):
            time.sleep(1.1)
    return rows


def write_outputs(rows: list[dict[str, object]]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_OUTPUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with CSV_OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rows = build_rows()
    write_outputs(rows)
    missing = sum(1 for row in rows if row["latitude"] is None or row["longitude"] is None)
    print(json.dumps({"rows": len(rows), "missing_coordinates": missing}, indent=2))


if __name__ == "__main__":
    main()
