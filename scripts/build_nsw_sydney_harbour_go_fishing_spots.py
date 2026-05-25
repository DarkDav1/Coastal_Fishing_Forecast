"""Build spot-level NSW Sydney Harbour Go Fishing map candidates.

This is the first spot-level pass below the guide-area list. The source names
come from the NSW DPI "Go Fishing - Sydney Harbour's Wharves, Piers and Parks"
guide map labels.
"""

from __future__ import annotations

import csv
import json
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


OUTPUT_DIR = Path("docs/generated")
JSON_OUTPUT = OUTPUT_DIR / "nsw_sydney_harbour_go_fishing_spots_2026-05-22.json"
CSV_OUTPUT = OUTPUT_DIR / "nsw_sydney_harbour_go_fishing_spots_2026-05-22.csv"
USER_AGENT = "CoastalFishingForecast/0.1 nsw-guide-spot-coordinate-builder"
OFFICIAL_URL = "https://www.dpi.nsw.gov.au/fishing/recreational/resources/info/fishing-locations/go-fishing-sydney-harbours-wharves%2C-piers-and-parks"
GUIDE_NAME = "Go Fishing - Sydney Harbour's Wharves, Piers and Parks"
GUIDE_CENTER = (-33.839694, 151.186615)


SPOTS = [
    ("Watsons Bay", "wharf_reserve"),
    ("Watsons Bay Ferry Wharf", "ferry_wharf"),
    ("Vaucluse Nielsen Park", "park_reserve"),
    ("Cobblers Beach Inner Middle Head", "shoreline"),
    ("Obelisk Beach Middle Head", "shoreline"),
    ("Balmoral Beach Baths", "beach_baths"),
    ("Clifton Gardens Wharf", "wharf"),
    ("Taylors Bay Point", "shoreline"),
    ("Rose Bay Ferry Wharf", "ferry_wharf"),
    ("Lyne Park Rose Bay", "park_reserve"),
    ("Bradleys Head", "shoreline"),
    ("Double Bay Ferry Wharf", "ferry_wharf"),
    ("Whiting Beach Sydney Harbour", "beach"),
    ("Little Sirius Point", "shoreline"),
    ("McKell Park Darling Point", "park_reserve"),
    ("Darling Point Ferry Wharf", "ferry_wharf"),
    ("Yarranabbe Park", "park_reserve"),
    ("Rushcutters Bay Park", "park_reserve"),
    ("South Mosman Ferry Wharf", "ferry_wharf"),
    ("Mosman Bay Ferry Wharf", "ferry_wharf"),
    ("Old Cremorne Ferry Wharf", "ferry_wharf"),
    ("Cremorne Point Ferry Wharf", "ferry_wharf"),
    ("Cremorne Point Reserve", "park_reserve"),
    ("Garden Island Ferry Wharf Sydney", "ferry_wharf"),
    ("Kurraba Point Reserve", "park_reserve"),
    ("Kurraba Point Ferry Wharf", "ferry_wharf"),
    ("Neutral Bay Ferry Wharf", "ferry_wharf"),
    ("Kesterton Park", "park_reserve"),
    ("North Sydney Ferry Wharf", "ferry_wharf"),
    ("Wrixton Park", "park_reserve"),
    ("Kirribilli Ferry Wharf", "ferry_wharf"),
    ("Lady Gowrie Lookout", "lookout_reserve"),
    ("Beulah Street Wharf", "wharf"),
    ("Jeffrey Street Wharf", "wharf"),
    ("Circular Quay Ferry Wharf", "ferry_wharf"),
    ("Milsons Point Ferry Wharf", "ferry_wharf"),
    ("Lavender Bay", "bay_reserve"),
    ("McMahons Point Public Wharf", "wharf"),
    ("McMahons Point Ferry Wharf", "ferry_wharf"),
    ("Walsh Bay Pier 2 and 3", "pier"),
    ("Walsh Bay Pier 7 and 8", "pier"),
    ("Blues Point Reserve", "park_reserve"),
    ("Henry Lawson Avenue Park McMahons Point", "park_reserve"),
    ("Sawmillers Reserve", "park_reserve"),
    ("Pyrmont Bay Ferry Wharf", "ferry_wharf"),
    ("Metcalfe Park Pyrmont", "park_reserve"),
    ("Ballaarat Park Pyrmont", "park_reserve"),
    ("Jones Bay Wharf", "wharf"),
    ("Illoura Reserve Balmain East", "park_reserve"),
    ("Balmain East Ferry Wharf", "ferry_wharf"),
    ("Lookes Avenue Reserve Balmain East", "park_reserve"),
    ("Simmons Point Reserve Balmain East", "park_reserve"),
    ("Pirrama Park Pyrmont", "park_reserve"),
    ("Waterfront Park Pyrmont", "park_reserve"),
    ("Bicentennial Park Glebe", "park_reserve"),
    ("Balmain Ferry Wharf", "ferry_wharf"),
    ("Ballast Point Park", "park_reserve"),
    ("Balls Head Reserve", "park_reserve"),
    ("Berry Island Reserve", "park_reserve"),
    ("Greenwich Sailing Club", "sailing_club"),
    ("Birchgrove Ferry Wharf", "ferry_wharf"),
    ("Yurulbin Park", "park_reserve"),
    ("Elkington Park", "park_reserve"),
    ("White Horse Point Balmain", "shoreline"),
    ("Greenwich Point Ferry Wharf", "ferry_wharf"),
    ("Shell Park Greenwich", "park_reserve"),
    ("Bayview Park Greenwich", "park_reserve"),
    ("Northwood Wharf", "wharf"),
    ("Woolwich Ferry Wharf", "ferry_wharf"),
    ("Clarkes Point Reserve", "park_reserve"),
]


MANUAL_COORDINATES = {
    "Cobblers Beach Inner Middle Head": (-33.8247, 151.2595),
    "Obelisk Beach Middle Head": (-33.8222, 151.2608),
    "Clifton Gardens Wharf": (-33.8402, 151.2564),
    "Taylors Bay Point": (-33.8490, 151.2534),
    "Whiting Beach Sydney Harbour": (-33.8492, 151.2446),
    "Darling Point Ferry Wharf": (-33.8674, 151.2392),
    "South Mosman Ferry Wharf": (-33.8413, 151.2349),
    "North Sydney Ferry Wharf": (-33.8418, 151.2070),
    "Old Cremorne Ferry Wharf": (-33.8428, 151.2264),
    "Cremorne Point Ferry Wharf": (-33.8479, 151.2296),
    "Cremorne Point Reserve": (-33.8472, 151.2294),
    "Kurraba Point Ferry Wharf": (-33.8420, 151.2226),
    "Garden Island Ferry Wharf Sydney": (-33.8661, 151.2259),
    "Walsh Bay Pier 2 and 3": (-33.8564, 151.2030),
    "Walsh Bay Pier 7 and 8": (-33.8546, 151.2010),
    "Henry Lawson Avenue Park McMahons Point": (-33.8469, 151.2046),
    "Lookes Avenue Reserve Balmain East": (-33.8553, 151.1904),
    "White Horse Point Balmain": (-33.8496, 151.1801),
    "Greenwich Sailing Club": (-33.8399, 151.1852),
    "Bayview Park Greenwich": (-33.8351, 151.1842),
    "Jeffrey Street Wharf": (-33.8475, 151.2117),
}


def query_variants(name: str) -> list[str]:
    variants = [
        name,
        name.replace("Ferry Wharf", "Wharf"),
        name.replace("Public Wharf", "Wharf"),
        name.replace("Sydney Harbour", ""),
    ]
    if "McMahons Point" in name:
        variants.append(name.replace("McMahons Point ", ""))
    if "Greenwich" in name:
        variants.append(name.replace("Greenwich", ""))
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
    queries = []
    for variant in query_variants(name):
        queries.extend(
            [
                f"{variant}, Sydney Harbour, NSW, Australia",
                f"{variant}, Sydney, NSW, Australia",
                f"{variant}, New South Wales, Australia",
            ]
        )
    for query in queries:
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
        "latitude": GUIDE_CENTER[0],
        "longitude": GUIDE_CENTER[1],
        "geocode_status": "guide_center_fallback_needs_review",
        "geocode_label": "Sydney Harbour guide center fallback",
    }


def clean_id(name: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in name.lower())
    return "_".join(part for part in cleaned.split("_") if part)


def build_rows() -> list[dict[str, object]]:
    rows = []
    for index, (name, spot_type) in enumerate(SPOTS, start=1):
        coords = geocode(name)
        rows.append(
            {
                "id": f"nsw_sydney_harbour_go_fishing:{index:03d}:{clean_id(name)}",
                "jurisdiction": "NSW",
                "guide_name": GUIDE_NAME,
                "spot_name": name,
                "spot_type": spot_type,
                "scope": "coastal_estuary",
                "source_kind": "official_go_fishing_guide_map_label",
                "official_owner": "NSW DPI / DPIRD",
                "official_url": OFFICIAL_URL,
                "latitude": coords["latitude"],
                "longitude": coords["longitude"],
                "coordinate_role": "spot_candidate",
                "geocode_status": coords["geocode_status"],
                "geocode_label": coords["geocode_label"],
                "planner_eligible": True,
                "map_eligible": True,
                "role": "public_fishing_access_candidate",
                "score_impact": "none",
                "review_status": "needs_access_and_closure_check",
                "notes": "Named on NSW DPI Go Fishing Sydney Harbour guide map; verify local access, signage, and closures before user-facing planning.",
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
    fallback_count = sum(1 for row in rows if row["geocode_status"] == "guide_center_fallback_needs_review")
    print(json.dumps({"rows": len(rows), "fallback_coordinates": fallback_count}, indent=2))


if __name__ == "__main__":
    main()
