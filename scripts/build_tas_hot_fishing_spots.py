"""Build Tasmania Fishing Tasmania Hot Fishing Spots map candidates."""

from __future__ import annotations

import csv
import json
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


OUTPUT_DIR = Path("docs/generated")
JSON_OUTPUT = OUTPUT_DIR / "tas_hot_fishing_spots_2026-05-22.json"
CSV_OUTPUT = OUTPUT_DIR / "tas_hot_fishing_spots_2026-05-22.csv"
USER_AGENT = "CoastalFishingForecast/0.1 tas-hotspot-coordinate-builder"


REGION_URLS = {
    "Bruny D'Entrecasteaux Region": "https://fishing.tas.gov.au/recreational-fishing/fishing-tips/hot-fishing-spots/fishing-around-the-bruny-dentrecasteaux-region",
    "Derwent River": "https://fishing.tas.gov.au/recreational-fishing/fishing-tips/hot-fishing-spots/fishing-around-the-derwent-river",
    "East Coast Region": "https://fishing.tas.gov.au/recreational-fishing/fishing-tips/hot-fishing-spots/fishing-around-the-east-coast-region",
    "Tasman Peninsula Region": "https://fishing.tas.gov.au/recreational-fishing/fishing-tips/hot-fishing-spots/fishing-around-the-tasman-peninsula-region",
    "St Helens Region": "https://fishing.tas.gov.au/recreational-fishing/fishing-tips/hot-fishing-spots/fishing-around-st-helens",
    "North East Coast and Flinders Island": "https://fishing.tas.gov.au/recreational-fishing/fishing-tips/hot-fishing-spots/fishing-around-the-north-east-coast-and-flinders-island",
    "Tamar River": "https://fishing.tas.gov.au/recreational-fishing/fishing-tips/hot-fishing-spots/fishing-around-the-tamar-river",
    "Devonport and Port Sorell Region": "https://fishing.tas.gov.au/recreational-fishing/fishing-tips/hot-fishing-spots/fishing-around-devonport-and-port-sorell",
    "North West Coast": "https://fishing.tas.gov.au/recreational-fishing/fishing-tips/hot-fishing-spots/fishing-around-the-north-west-coast",
    "King Island": "https://fishing.tas.gov.au/recreational-fishing/fishing-tips/hot-fishing-spots/fishing-around-king-island",
    "Macquarie Harbour": "https://fishing.tas.gov.au/recreational-fishing/fishing-tips/hot-fishing-spots/macquarie-harbour",
}


SPOTS = [
    ("Bruny D'Entrecasteaux Region", "Dru Point", "park_reserve"),
    ("Bruny D'Entrecasteaux Region", "Margate Wharf", "wharf"),
    ("Bruny D'Entrecasteaux Region", "Kettering", "foreshore"),
    ("Bruny D'Entrecasteaux Region", "Woodbridge", "foreshore"),
    ("Bruny D'Entrecasteaux Region", "Roberts Point", "jetty"),
    ("Bruny D'Entrecasteaux Region", "Dennes Point", "shoreline"),
    ("Bruny D'Entrecasteaux Region", "Adventure Bay", "beach_bay"),
    ("Bruny D'Entrecasteaux Region", "Cloudy Bay Lagoon", "lagoon"),
    ("Bruny D'Entrecasteaux Region", "Gordon Jetty", "jetty"),
    ("Bruny D'Entrecasteaux Region", "Trial Bay", "bay"),
    ("Bruny D'Entrecasteaux Region", "Huon Estuary", "estuary"),
    ("Bruny D'Entrecasteaux Region", "Southport", "foreshore"),
    ("Derwent River", "Dowsing Point", "shoreline"),
    ("Derwent River", "Botanical Gardens", "park_reserve"),
    ("Derwent River", "Tasman Bridge", "bridge"),
    ("Derwent River", "Regatta Grounds", "park_reserve"),
    ("Derwent River", "Sandy Bay", "foreshore"),
    ("Derwent River", "Taroona", "foreshore"),
    ("Derwent River", "Alum Cliffs", "shoreline"),
    ("Derwent River", "Browns River", "river_mouth"),
    ("Derwent River", "Kingston", "foreshore"),
    ("Derwent River", "Blackmans Bay", "beach_bay"),
    ("Derwent River", "South Arm Jetty", "jetty"),
    ("Derwent River", "Opossum Bay Jetty", "jetty"),
    ("Derwent River", "Ralphs Bay", "bay"),
    ("Derwent River", "Bellerive Bluff", "shoreline"),
    ("Derwent River", "Lindisfarne", "foreshore"),
    ("Derwent River", "Otago Bay", "bay"),
    ("Derwent River", "Old Beach", "foreshore"),
    ("Derwent River", "Bridgewater", "foreshore"),
    ("East Coast Region", "Waubs Bay", "bay"),
    ("East Coast Region", "The Gulch Wharf", "wharf"),
    ("East Coast Region", "Coles Bay Jetty", "jetty"),
    ("East Coast Region", "Swanwick", "foreshore"),
    ("East Coast Region", "Swansea Pier", "pier"),
    ("East Coast Region", "Little Swanport", "estuary"),
    ("East Coast Region", "Triabunna", "foreshore"),
    ("East Coast Region", "Prosser River", "river_mouth"),
    ("East Coast Region", "Earlham Lagoon", "lagoon"),
    ("Tasman Peninsula Region", "Cremorne Narrows", "narrows"),
    ("Tasman Peninsula Region", "McGees Bridge", "bridge"),
    ("Tasman Peninsula Region", "Lewisham", "foreshore"),
    ("Tasman Peninsula Region", "Carlton River", "river_mouth"),
    ("Tasman Peninsula Region", "Primrose Sands", "beach"),
    ("Tasman Peninsula Region", "Dunalley Canal", "canal"),
    ("Tasman Peninsula Region", "Marion Bay Spit", "spit"),
    ("Tasman Peninsula Region", "Pirates Bay Jetty", "jetty"),
    ("Tasman Peninsula Region", "Fortescue Bay", "bay"),
    ("Tasman Peninsula Region", "Port Arthur", "foreshore"),
    ("Tasman Peninsula Region", "White Beach", "beach"),
    ("Tasman Peninsula Region", "Nubeena", "foreshore"),
    ("Tasman Peninsula Region", "Taranna", "foreshore"),
    ("St Helens Region", "St Helens Wharf", "wharf"),
    ("St Helens Region", "Beauty Bay", "bay"),
    ("St Helens Region", "Kirwans Beach", "beach"),
    ("St Helens Region", "Talbot Street", "shoreline"),
    ("St Helens Region", "Cunninghams Jetty", "jetty"),
    ("St Helens Region", "Stieglitz Jetty", "jetty"),
    ("St Helens Region", "Akaroa", "foreshore"),
    ("St Helens Region", "Burns Bay", "bay"),
    ("St Helens Region", "Maurouard Beach", "beach"),
    ("St Helens Region", "Dora Point", "shoreline"),
    ("St Helens Region", "Binalong Bay", "beach_bay"),
    ("North East Coast and Flinders Island", "Bridport", "foreshore"),
    ("North East Coast and Flinders Island", "Waterhouse", "shoreline"),
    ("North East Coast and Flinders Island", "Tomahawk", "foreshore"),
    ("North East Coast and Flinders Island", "Petal Point", "shoreline"),
    ("North East Coast and Flinders Island", "Little Musselroe Bay", "bay"),
    ("North East Coast and Flinders Island", "Great Musselroe Bay", "bay"),
    ("North East Coast and Flinders Island", "Eddystone Point", "shoreline"),
    ("North East Coast and Flinders Island", "Ansons Bay", "bay"),
    ("North East Coast and Flinders Island", "Whitemark Wharf", "wharf"),
    ("North East Coast and Flinders Island", "Lady Barron Wharf", "wharf"),
    ("North East Coast and Flinders Island", "Settlement Point", "shoreline"),
    ("North East Coast and Flinders Island", "Palana", "beach"),
    ("North East Coast and Flinders Island", "North East River", "river_mouth"),
    ("Tamar River", "Greens Beach", "beach"),
    ("Tamar River", "Kelso Jetty", "jetty"),
    ("Tamar River", "Clarence Point", "shoreline"),
    ("Tamar River", "Beauty Point Wharf", "wharf"),
    ("Tamar River", "Sidmouth", "foreshore"),
    ("Tamar River", "Deviot Pontoon", "pontoon"),
    ("Tamar River", "Hillwood", "foreshore"),
    ("Tamar River", "George Town", "foreshore"),
    ("Tamar River", "Low Head Pilot Station", "shoreline"),
    ("Tamar River", "Beechford", "beach"),
    ("Tamar River", "Weymouth", "beach"),
    ("Tamar River", "Bellingham", "beach"),
    ("Devonport and Port Sorell Region", "Bakers Beach", "beach"),
    ("Devonport and Port Sorell Region", "Squeaking Point Jetty", "jetty"),
    ("Devonport and Port Sorell Region", "Port Sorell Jetty", "jetty"),
    ("Devonport and Port Sorell Region", "Moorlands Beach", "beach"),
    ("Devonport and Port Sorell Region", "Reg Hope Park", "park_reserve"),
    ("Devonport and Port Sorell Region", "Horsehead Creek", "creek_mouth"),
    ("Devonport and Port Sorell Region", "Mussel Rock Lighthouse", "shoreline"),
    ("Devonport and Port Sorell Region", "Mersey Bluff", "shoreline"),
    ("Devonport and Port Sorell Region", "Don Heads", "shoreline"),
    ("Devonport and Port Sorell Region", "Turners Beach", "beach"),
    ("Devonport and Port Sorell Region", "Leven River", "river_mouth"),
    ("North West Coast", "Burnie Boat Ramp", "boat_ramp_named_in_guide"),
    ("North West Coast", "Cooee Point", "shoreline"),
    ("North West Coast", "Doctors Rocks", "shoreline"),
    ("North West Coast", "Wynyard Wharf", "wharf"),
    ("North West Coast", "Boat Harbour", "beach_bay"),
    ("North West Coast", "Sisters Beach", "beach"),
    ("North West Coast", "Rocky Cape", "shoreline"),
    ("North West Coast", "Stanley Wharf", "wharf"),
    ("North West Coast", "East Inlet", "inlet"),
    ("North West Coast", "West Inlet", "inlet"),
    ("North West Coast", "Godfreys Beach", "beach"),
    ("North West Coast", "Duck Bay", "bay"),
    ("North West Coast", "Montagu", "foreshore"),
    ("North West Coast", "Arthur River", "river_mouth"),
    ("North West Coast", "Marrawah", "beach"),
    ("King Island", "Grassy Jetty", "jetty"),
    ("King Island", "Bold Head", "shoreline"),
    ("King Island", "Naracoopa Jetty", "jetty"),
    ("King Island", "Sea Elephant", "shoreline"),
    ("King Island", "Lavinia Point", "shoreline"),
    ("King Island", "Three Sisters", "shoreline"),
    ("King Island", "Phoques Bay", "bay"),
    ("King Island", "Currie", "foreshore"),
    ("King Island", "British Admiral Point", "shoreline"),
    ("Macquarie Harbour", "Ocean Beach", "beach"),
    ("Macquarie Harbour", "Macquarie Heads", "shoreline"),
    ("Macquarie Harbour", "Swan Basin", "basin"),
    ("Macquarie Harbour", "Strahan Public Jetty", "jetty"),
    ("Macquarie Harbour", "Regatta Point", "shoreline"),
    ("Macquarie Harbour", "Lettes Bay", "bay"),
    ("Macquarie Harbour", "Kellys Basin", "basin"),
    ("Macquarie Harbour", "Cape Sorell", "shoreline"),
]


MANUAL_COORDINATES = {
    "Bellerive Bluff": (-42.87647, 147.36381),
    "Botanical Gardens": (-42.8645, 147.3318),
    "Regatta Grounds": (-42.8706, 147.3342),
    "The Gulch Wharf": (-41.8795, 148.3023),
    "Swansea Pier": (-42.1224, 148.0746),
    "Earlham Lagoon": (-42.6250, 147.9150),
    "Cremorne Narrows": (-42.9430, 147.5300),
    "Dunalley Canal": (-42.8888, 147.8057),
    "Marion Bay Spit": (-42.8010, 147.8900),
    "Kirwans Beach": (-41.3235, 148.2860),
    "Talbot Street": (-41.3249, 148.2532),
    "Cunninghams Jetty": (-41.3280, 148.2540),
    "Stieglitz Jetty": (-41.3260, 148.2923),
    "Whitemark Wharf": (-40.1210, 148.0180),
    "Lady Barron Wharf": (-40.2110, 148.2410),
    "Settlement Point": (-40.0950, 148.0020),
    "Palana": (-39.7540, 147.8890),
    "North East River": (-39.7620, 148.0150),
    "Deviot Pontoon": (-41.2647, 146.9565),
    "Low Head Pilot Station": (-41.0546, 146.7929),
    "Moorlands Beach": (-41.1560, 146.5700),
    "Reg Hope Park": (-41.2345, 146.4150),
    "Mussel Rock Lighthouse": (-41.1528, 146.4230),
    "East Inlet": (-40.7600, 145.2600),
    "West Inlet": (-40.7700, 145.2250),
    "Grassy Jetty": (-40.0636, 144.0571),
    "Bold Head": (-39.9950, 143.8400),
    "Naracoopa Jetty": (-39.9220, 144.1180),
    "Sea Elephant": (-39.7850, 144.0750),
    "Three Sisters": (-39.7800, 143.9200),
    "Phoques Bay": (-39.666667, 143.930556),
    "British Admiral Point": (-40.1050, 143.8650),
    "Ocean Beach": (-42.1630, 145.2230),
    "Macquarie Heads": (-42.2120, 145.2050),
    "Swan Basin": (-42.2500, 145.4000),
    "Strahan Public Jetty": (-42.1515, 145.3278),
    "Regatta Point": (-42.1790, 145.3190),
    "Lettes Bay": (-42.1910, 145.3440),
    "Kellys Basin": (-42.2710, 145.6270),
    "Cape Sorell": (-42.1980, 145.1680),
}


def cached_coordinates() -> dict[str, dict[str, object]]:
    if not JSON_OUTPUT.exists():
        return {}
    rows = json.loads(JSON_OUTPUT.read_text(encoding="utf-8"))
    return {
        row["spot_name"]: row
        for row in rows
        if row.get("latitude") is not None and row.get("longitude") is not None
    }


CACHED_COORDINATES = cached_coordinates()


def clean_id(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in value.lower())
    return "_".join(part for part in cleaned.split("_") if part)


def query_variants(region: str, spot_name: str) -> list[str]:
    variants = [spot_name]
    if "Jetty" in spot_name:
        variants.append(spot_name.replace("Jetty", ""))
    if "Wharf" in spot_name:
        variants.append(spot_name.replace("Wharf", ""))
    if region == "King Island":
        variants = [f"{variant}, King Island" for variant in variants]
    elif region == "North East Coast and Flinders Island" and spot_name in {
        "Whitemark Wharf",
        "Lady Barron Wharf",
        "Settlement Point",
        "Palana",
        "North East River",
    }:
        variants = [f"{variant}, Flinders Island" for variant in variants]
    elif region == "Macquarie Harbour":
        variants = [f"{variant}, Macquarie Harbour" for variant in variants]
    return list(dict.fromkeys(" ".join(variant.split()) for variant in variants))


def geocode(region: str, spot_name: str) -> dict[str, object]:
    if spot_name in MANUAL_COORDINATES:
        lat, lon = MANUAL_COORDINATES[spot_name]
        return {
            "latitude": lat,
            "longitude": lon,
            "geocode_status": "manual_spot_coordinate",
            "geocode_label": spot_name,
        }
    if spot_name in CACHED_COORDINATES:
        cached = CACHED_COORDINATES[spot_name]
        return {
            "latitude": cached["latitude"],
            "longitude": cached["longitude"],
            "geocode_status": cached.get("geocode_status", "cached_coordinate"),
            "geocode_label": cached.get("geocode_label") or spot_name,
        }

    for variant in query_variants(region, spot_name):
        for query in (
            f"{variant}, Tasmania, Australia",
            f"{variant}, TAS, Australia",
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
        "geocode_label": spot_name,
    }


def build_rows() -> list[dict[str, object]]:
    rows = []
    for index, (region, spot_name, spot_type) in enumerate(SPOTS, start=1):
        coords = geocode(region, spot_name)
        map_only = spot_type == "boat_ramp_named_in_guide"
        rows.append(
            {
                "id": f"tas_hot_fishing_spots:{index:03d}:{clean_id(region)}:{clean_id(spot_name)}",
                "jurisdiction": "TAS",
                "guide_name": f"Fishing Tasmania Hot Fishing Spots - {region}",
                "spot_name": spot_name,
                "spot_type": spot_type,
                "scope": "coastal_estuary",
                "source_kind": "official_hot_fishing_spots_page",
                "official_owner": "Fishing Tasmania / NRE Tasmania",
                "official_url": REGION_URLS[region],
                "latitude": coords["latitude"],
                "longitude": coords["longitude"],
                "coordinate_role": "spot_candidate",
                "geocode_status": coords["geocode_status"],
                "geocode_label": coords["geocode_label"],
                "planner_eligible": not map_only,
                "map_eligible": True,
                "role": "public_access_only" if map_only else "public_fishing_access_candidate",
                "score_impact": "none",
                "review_status": "needs_access_and_closure_check",
                "notes": "Named by Fishing Tasmania Hot Fishing Spots. Verify current rules, health alerts, closures, and local access before user-facing planning.",
            }
        )
        if index < len(SPOTS):
            time.sleep(1.1)
    return rows


def write_outputs(rows: list[dict[str, object]]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_OUTPUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    fieldnames = sorted({key for row in rows for key in row})
    with CSV_OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rows = build_rows()
    write_outputs(rows)
    missing = sum(1 for row in rows if row["latitude"] is None or row["longitude"] is None)
    print(json.dumps({"rows": len(rows), "missing_coordinates": missing}, indent=2))


if __name__ == "__main__":
    main()
