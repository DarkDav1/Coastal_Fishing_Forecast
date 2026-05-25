"""Build a first official fishing-guide location list with map coordinates.

The list is guide-level, not final spot-level extraction. It follows the
Tasmania Hot Fishing Spots pattern and gives the frontend/import work a
coordinate-bearing starting point for each official guide area.
"""

from __future__ import annotations

import csv
import json
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


OUTPUT_DIR = Path("data/guides")
JSON_OUTPUT = OUTPUT_DIR / "official_fishing_guide_locations_2026-05-22.json"
CSV_OUTPUT = OUTPUT_DIR / "official_fishing_guide_locations_2026-05-22.csv"
DOCS_OUTPUT_DIR = Path("docs/generated")
DOCS_JSON_OUTPUT = DOCS_OUTPUT_DIR / "official_fishing_guide_locations_2026-05-22.json"
DOCS_CSV_OUTPUT = DOCS_OUTPUT_DIR / "official_fishing_guide_locations_2026-05-22.csv"
USER_AGENT = "CoastalFishingForecast/0.1 guide-source-coordinate-builder"


GUIDE_SEEDS = [
    {
        "jurisdiction": "TAS",
        "guide_name": "Bruny D'Entrecasteaux Region",
        "query": "Bruny Island D'Entrecasteaux Channel Tasmania Australia",
        "source_kind": "official_hot_fishing_spots_region",
        "official_owner": "Fishing Tasmania / NRE Tasmania",
        "official_url": "https://fishing.tas.gov.au/recreational-fishing/fishing-tips/hot-fishing-spots",
        "scope": "coastal_estuary",
        "priority": 1,
    },
    {
        "jurisdiction": "TAS",
        "guide_name": "Derwent River",
        "query": "Derwent River Hobart Tasmania Australia",
        "source_kind": "official_hot_fishing_spots_region",
        "official_owner": "Fishing Tasmania / NRE Tasmania",
        "official_url": "https://fishing.tas.gov.au/recreational-fishing/fishing-tips/hot-fishing-spots",
        "scope": "coastal_estuary",
        "priority": 1,
    },
    {
        "jurisdiction": "TAS",
        "guide_name": "East Coast Region",
        "query": "Bicheno Swansea Triabunna Orford Tasmania Australia",
        "source_kind": "official_hot_fishing_spots_region",
        "official_owner": "Fishing Tasmania / NRE Tasmania",
        "official_url": "https://fishing.tas.gov.au/recreational-fishing/fishing-tips/hot-fishing-spots",
        "scope": "coastal_estuary",
        "priority": 1,
    },
    {
        "jurisdiction": "TAS",
        "guide_name": "Tasman Peninsula Region",
        "query": "Eaglehawk Neck Tasman Peninsula Tasmania Australia",
        "source_kind": "official_hot_fishing_spots_region",
        "official_owner": "Fishing Tasmania / NRE Tasmania",
        "official_url": "https://fishing.tas.gov.au/recreational-fishing/fishing-tips/hot-fishing-spots",
        "scope": "coastal_estuary",
        "priority": 1,
    },
    {
        "jurisdiction": "TAS",
        "guide_name": "St Helens Region",
        "query": "St Helens Georges Bay Binalong Bay Tasmania Australia",
        "source_kind": "official_hot_fishing_spots_region",
        "official_owner": "Fishing Tasmania / NRE Tasmania",
        "official_url": "https://fishing.tas.gov.au/recreational-fishing/fishing-tips/hot-fishing-spots",
        "scope": "coastal_estuary",
        "priority": 1,
    },
    {
        "jurisdiction": "TAS",
        "guide_name": "North East Coast and Flinders Island",
        "query": "Bridport Musselroe Bay Flinders Island Tasmania Australia",
        "source_kind": "official_hot_fishing_spots_region",
        "official_owner": "Fishing Tasmania / NRE Tasmania",
        "official_url": "https://fishing.tas.gov.au/recreational-fishing/fishing-tips/hot-fishing-spots",
        "scope": "coastal_estuary",
        "priority": 1,
    },
    {
        "jurisdiction": "TAS",
        "guide_name": "Tamar River",
        "query": "Tamar River George Town Tasmania Australia",
        "source_kind": "official_hot_fishing_spots_region",
        "official_owner": "Fishing Tasmania / NRE Tasmania",
        "official_url": "https://fishing.tas.gov.au/recreational-fishing/fishing-tips/hot-fishing-spots",
        "scope": "coastal_estuary",
        "priority": 1,
    },
    {
        "jurisdiction": "TAS",
        "guide_name": "Devonport and Port Sorell Region",
        "query": "Devonport Port Sorell Tasmania Australia",
        "source_kind": "official_hot_fishing_spots_region",
        "official_owner": "Fishing Tasmania / NRE Tasmania",
        "official_url": "https://fishing.tas.gov.au/recreational-fishing/fishing-tips/hot-fishing-spots",
        "scope": "coastal_estuary",
        "priority": 1,
    },
    {
        "jurisdiction": "TAS",
        "guide_name": "North West Coast",
        "query": "Burnie Wynyard Stanley Tasmania Australia",
        "source_kind": "official_hot_fishing_spots_region",
        "official_owner": "Fishing Tasmania / NRE Tasmania",
        "official_url": "https://fishing.tas.gov.au/recreational-fishing/fishing-tips/hot-fishing-spots",
        "scope": "coastal_estuary",
        "priority": 1,
    },
    {
        "jurisdiction": "TAS",
        "guide_name": "King Island",
        "query": "King Island Tasmania Australia",
        "source_kind": "official_hot_fishing_spots_region",
        "official_owner": "Fishing Tasmania / NRE Tasmania",
        "official_url": "https://fishing.tas.gov.au/recreational-fishing/fishing-tips/hot-fishing-spots",
        "scope": "coastal_estuary",
        "priority": 1,
    },
    {
        "jurisdiction": "TAS",
        "guide_name": "Macquarie Harbour",
        "query": "Macquarie Harbour Strahan Tasmania Australia",
        "source_kind": "official_hot_fishing_spots_region",
        "official_owner": "Fishing Tasmania / NRE Tasmania",
        "official_url": "https://fishing.tas.gov.au/recreational-fishing/fishing-tips/hot-fishing-spots",
        "scope": "coastal_estuary",
        "priority": 1,
    },
    {
        "jurisdiction": "NSW",
        "guide_name": "Go Fishing - Sydney Harbour's Wharves, Piers and Parks",
        "query": "Sydney Harbour New South Wales Australia",
        "source_kind": "official_go_fishing_guide",
        "official_owner": "NSW DPI / DPIRD",
        "official_url": "https://www.dpi.nsw.gov.au/fishing/recreational/resources/info/fishing-locations/go-fishing-sydney-harbours-wharves%2C-piers-and-parks",
        "scope": "coastal_estuary",
        "priority": 1,
    },
    {
        "jurisdiction": "NSW",
        "guide_name": "Go Fishing - Botany Bay",
        "query": "Botany Bay New South Wales Australia",
        "source_kind": "official_go_fishing_guide",
        "official_owner": "NSW DPI / DPIRD",
        "official_url": "https://www.dpi.nsw.gov.au/fishing/recreational/resources/info/fishing-locations/go-fishing-botany-bay",
        "scope": "coastal_estuary",
        "priority": 1,
    },
    {
        "jurisdiction": "NSW",
        "guide_name": "Go Fishing - Jervis Bay",
        "query": "Jervis Bay New South Wales Australia",
        "source_kind": "official_go_fishing_guide",
        "official_owner": "NSW DPI / DPIRD",
        "official_url": "https://www.dpi.nsw.gov.au/fishing/recreational/resources/info",
        "scope": "coastal_estuary",
        "priority": 1,
    },
    {
        "jurisdiction": "NSW",
        "guide_name": "Go Fishing - Lake Macquarie",
        "query": "Lake Macquarie New South Wales Australia",
        "source_kind": "official_go_fishing_guide",
        "official_owner": "NSW DPI / DPIRD",
        "official_url": "https://www.dpi.nsw.gov.au/fishing/recreational/resources/info",
        "scope": "coastal_estuary",
        "priority": 1,
    },
    {
        "jurisdiction": "NSW",
        "guide_name": "Go Fishing - St Georges Basin",
        "query": "St Georges Basin New South Wales Australia",
        "source_kind": "official_go_fishing_guide",
        "official_owner": "NSW DPI / DPIRD",
        "official_url": "https://www.dpi.nsw.gov.au/fishing/recreational/resources/info",
        "scope": "coastal_estuary",
        "priority": 1,
    },
    {
        "jurisdiction": "NSW",
        "guide_name": "Go Fishing - Tuross Head",
        "query": "Tuross Head New South Wales Australia",
        "source_kind": "official_go_fishing_guide",
        "official_owner": "NSW DPI / DPIRD",
        "official_url": "https://www.dpi.nsw.gov.au/fishing/recreational/resources/info",
        "scope": "coastal_estuary",
        "priority": 1,
    },
    {
        "jurisdiction": "NSW",
        "guide_name": "Go Fishing - Middle and North Harbour Parks and Reserves",
        "query": "Middle Harbour Sydney New South Wales Australia",
        "source_kind": "official_go_fishing_guide",
        "official_owner": "NSW DPI / DPIRD",
        "official_url": "https://www.dpi.nsw.gov.au/fishing/recreational/resources/info",
        "scope": "coastal_estuary",
        "priority": 1,
    },
    {
        "jurisdiction": "NSW",
        "guide_name": "Go Fishing - Parramatta and Lane Cove Rivers' Wharves and Parks",
        "query": "Parramatta River Lane Cove River Sydney New South Wales Australia",
        "source_kind": "official_go_fishing_guide",
        "official_owner": "NSW DPI / DPIRD",
        "official_url": "https://www.dpi.nsw.gov.au/fishing/recreational/resources/info",
        "scope": "tidal_estuary",
        "priority": 1,
    },
    {
        "jurisdiction": "NSW",
        "guide_name": "Go Fishing - Coffs Coast",
        "query": "Coffs Coast New South Wales Australia",
        "source_kind": "official_go_fishing_guide",
        "official_owner": "NSW DPI / DPIRD",
        "official_url": "https://www.dpi.nsw.gov.au/fishing/recreational/resources/info",
        "scope": "coastal_estuary",
        "priority": 1,
    },
    {
        "jurisdiction": "NSW",
        "guide_name": "Go Fishing - Hawkesbury River",
        "query": "Hawkesbury River Broken Bay New South Wales Australia",
        "source_kind": "official_go_fishing_guide",
        "official_owner": "NSW DPI / DPIRD",
        "official_url": "https://www.dpi.nsw.gov.au/fishing/recreational/resources/info",
        "scope": "tidal_estuary",
        "priority": 1,
    },
    {
        "jurisdiction": "NSW",
        "guide_name": "Go Fishing - Bermagui",
        "query": "Bermagui New South Wales Australia",
        "source_kind": "official_go_fishing_guide",
        "official_owner": "NSW DPI / DPIRD",
        "official_url": "https://www.dpi.nsw.gov.au/fishing/recreational/resources/info",
        "scope": "coastal_estuary",
        "priority": 1,
    },
    {
        "jurisdiction": "NSW",
        "guide_name": "Go Fishing - Great Lakes",
        "query": "Great Lakes Forster Tuncurry New South Wales Australia",
        "source_kind": "official_go_fishing_guide",
        "official_owner": "NSW DPI / DPIRD",
        "official_url": "https://www.dpi.nsw.gov.au/fishing/recreational/resources/info",
        "scope": "coastal_estuary",
        "priority": 1,
    },
    {
        "jurisdiction": "NSW",
        "guide_name": "Go Fishing - Ulladulla",
        "query": "Ulladulla New South Wales Australia",
        "source_kind": "official_go_fishing_guide",
        "official_owner": "NSW DPI / DPIRD",
        "official_url": "https://www.dpi.nsw.gov.au/fishing/recreational/resources/info",
        "scope": "coastal_estuary",
        "priority": 1,
    },
    {
        "jurisdiction": "NSW",
        "guide_name": "Go Fishing - Port Macquarie",
        "query": "Port Macquarie New South Wales Australia",
        "source_kind": "official_go_fishing_guide",
        "official_owner": "NSW DPI / DPIRD",
        "official_url": "https://www.dpi.nsw.gov.au/fishing/recreational/resources/info",
        "scope": "coastal_estuary",
        "priority": 1,
    },
    {
        "jurisdiction": "NSW",
        "guide_name": "Go Fishing - Batemans Bay",
        "query": "Batemans Bay New South Wales Australia",
        "source_kind": "official_go_fishing_guide",
        "official_owner": "NSW DPI / DPIRD",
        "official_url": "https://www.dpi.nsw.gov.au/fishing/recreational/resources/info",
        "scope": "coastal_estuary",
        "priority": 1,
    },
    {
        "jurisdiction": "VIC",
        "guide_name": "Port Phillip Bay",
        "query": "Port Phillip Bay Victoria Australia",
        "source_kind": "official_fishing_locations_page",
        "official_owner": "Victorian Fisheries Authority",
        "official_url": "https://vfa.vic.gov.au/recreational-fishing/fishing-locations",
        "scope": "coastal_bay",
        "priority": 2,
    },
    {
        "jurisdiction": "VIC",
        "guide_name": "Western Port",
        "query": "Western Port Victoria Australia",
        "source_kind": "official_fishing_locations_page",
        "official_owner": "Victorian Fisheries Authority",
        "official_url": "https://vfa.vic.gov.au/recreational-fishing/fishing-locations",
        "scope": "coastal_bay",
        "priority": 2,
    },
    {
        "jurisdiction": "VIC",
        "guide_name": "Hopkins River",
        "query": "Hopkins River Warrnambool Victoria Australia",
        "source_kind": "official_fishing_locations_page",
        "official_owner": "Victorian Fisheries Authority",
        "official_url": "https://vfa.vic.gov.au/recreational-fishing/fishing-locations",
        "scope": "tidal_estuary",
        "priority": 2,
    },
    {
        "jurisdiction": "WA",
        "guide_name": "Recreational Fishing Location Guide",
        "query": "Western Australia coast Australia",
        "source_kind": "official_location_guide_pdf",
        "official_owner": "DPIRD Western Australia",
        "official_url": "https://library.dpird.wa.gov.au/fr_fop/58/",
        "scope": "coastal_statewide",
        "priority": 2,
    },
    {
        "jurisdiction": "NT",
        "guide_name": "Land Based Fishing Guide - Darwin and Beyond",
        "query": "Darwin Harbour Northern Territory Australia",
        "source_kind": "government_supported_land_based_guide",
        "official_owner": "AFANT with NT Government Recreational Fishing Grant support",
        "official_url": "https://afant.com.au/lbfg-darwin/",
        "scope": "coastal_estuary",
        "priority": 3,
    },
]


MANUAL_COORDINATES = {
    "Bruny Island D'Entrecasteaux Channel Tasmania Australia": (-43.1600, 147.2800, "manual_region_centroid"),
    "Bicheno Swansea Triabunna Orford Tasmania Australia": (-42.0800, 148.0500, "manual_region_centroid"),
    "Eaglehawk Neck Tasman Peninsula Tasmania Australia": (-43.0300, 147.9200, "manual_region_centroid"),
    "St Helens Georges Bay Binalong Bay Tasmania Australia": (-41.3100, 148.2800, "manual_region_centroid"),
    "Bridport Musselroe Bay Flinders Island Tasmania Australia": (-40.4300, 148.1400, "manual_region_centroid"),
    "Tamar River George Town Tasmania Australia": (-41.1000, 146.8500, "manual_region_centroid"),
    "Devonport Port Sorell Tasmania Australia": (-41.1700, 146.4300, "manual_region_centroid"),
    "Burnie Wynyard Stanley Tasmania Australia": (-40.9000, 145.5200, "manual_region_centroid"),
    "Macquarie Harbour Strahan Tasmania Australia": (-42.2500, 145.3200, "manual_region_centroid"),
    "Parramatta River Lane Cove River Sydney New South Wales Australia": (-33.8250, 151.0900, "manual_region_centroid"),
    "Hawkesbury River Broken Bay New South Wales Australia": (-33.5500, 151.2400, "manual_region_centroid"),
    "Western Australia coast Australia": (-26.0000, 121.0000, "manual_statewide_centroid"),
    "Coffs Coast New South Wales Australia": (-30.2963, 153.1135, "manual_region_centroid"),
    "Great Lakes Forster Tuncurry New South Wales Australia": (-32.1810, 152.5110, "manual_region_centroid"),
}


def geocode(query: str) -> dict[str, object]:
    if query in MANUAL_COORDINATES:
        lat, lon, status = MANUAL_COORDINATES[query]
        return {
            "latitude": lat,
            "longitude": lon,
            "geocode_status": status,
            "geocode_label": query,
        }

    url = "https://nominatim.openstreetmap.org/search?" + urlencode(
        {"q": query, "format": "jsonv2", "limit": "1", "countrycodes": "au"}
    )
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not payload:
        return {
            "latitude": None,
            "longitude": None,
            "geocode_status": "not_found",
            "geocode_label": query,
        }
    match = payload[0]
    return {
        "latitude": round(float(match["lat"]), 6),
        "longitude": round(float(match["lon"]), 6),
        "geocode_status": "nominatim_first_match",
        "geocode_label": match.get("display_name") or query,
    }


def source_id(seed: dict[str, object]) -> str:
    base = f"{seed['jurisdiction']}:{seed['guide_name']}".lower()
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in base)
    return "_".join(part for part in cleaned.split("_") if part)


def build_rows() -> list[dict[str, object]]:
    rows = []
    for index, seed in enumerate(GUIDE_SEEDS, start=1):
        coords = geocode(str(seed["query"]))
        rows.append(
            {
                "id": source_id(seed),
                "jurisdiction": seed["jurisdiction"],
                "guide_name": seed["guide_name"],
                "source_kind": seed["source_kind"],
                "official_owner": seed["official_owner"],
                "official_url": seed["official_url"],
                "scope": seed["scope"],
                "priority": seed["priority"],
                "latitude": coords["latitude"],
                "longitude": coords["longitude"],
                "coordinate_role": "guide_area_center",
                "geocode_query": seed["query"],
                "geocode_status": coords["geocode_status"],
                "geocode_label": coords["geocode_label"],
                "spot_extraction_status": "guide_level_only",
                "notes": "First-pass map coordinate for the official guide area; extract individual spots separately.",
            }
        )
        if index < len(GUIDE_SEEDS):
            time.sleep(1.1)
    return rows


def write_outputs(rows: list[dict[str, object]]) -> None:
    for output_dir, json_output, csv_output in (
        (OUTPUT_DIR, JSON_OUTPUT, CSV_OUTPUT),
        (DOCS_OUTPUT_DIR, DOCS_JSON_OUTPUT, DOCS_CSV_OUTPUT),
    ):
        output_dir.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        with csv_output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)


def main() -> None:
    rows = build_rows()
    write_outputs(rows)
    missing = [row for row in rows if row["latitude"] is None or row["longitude"] is None]
    print(json.dumps({"rows": len(rows), "missing_coordinates": len(missing)}, indent=2))


if __name__ == "__main__":
    main()
