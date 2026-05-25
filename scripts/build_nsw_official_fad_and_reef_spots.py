"""Build NSW official FAD and estuarine artificial reef map candidates."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path


OUTPUT_DIR = Path("docs/generated")
JSON_OUTPUT = OUTPUT_DIR / "nsw_official_fad_and_reef_spots_2026-05-22.json"
CSV_OUTPUT = OUTPUT_DIR / "nsw_official_fad_and_reef_spots_2026-05-22.csv"
FAD_URL = "https://www.dpi.nsw.gov.au/fishing/recreational/resources/fish-aggregating-devices"
REEF_URL = "https://www.dpi.nsw.gov.au/fishing/recreational/resources/artificial-reef/estuarine-artificial-reefs"


FADS = [
    ("Tweed Heads", "28° 09.730'", "153° 41.000'", "Tweed Heads - 13.0", 64),
    ("Byron Bay", "28° 36.723'", "153° 42.758'", "Brunswick Heads - 17.0", 70),
    ("Ballina", "28° 54.430'", "153° 41.189'", "Richmond River - 14.0", 70),
    ("Evans Head", "29° 06.400'", "153° 36.200'", "Evans River - 17.0", 50),
    ("Yamba", "29° 37.268'", "153° 29.153'", "Clarence River - 23.0", 70),
    ("Wooli", "29° 52.703'", "153° 26.117'", "Wooli River - 16.0", 65),
    ("Coffs Harbour", "30° 14.858'", "153° 21.605'", "Coffs Harbour - 21", 85),
    ("Nambucca", "30° 39.622'", "153° 08.934'", "Nambucca River - 13.0", 60),
    ("South West Rocks", "30° 50.534'", "153° 11.803'", "Macleay River - 16.5", 104),
    ("Hat Head", "31° 00.636'", "153° 07.795'", "Korogoro Creek - 7.5", 85),
    ("Port Macquarie", "31° 26.439'", "153° 04.342'", "Hastings River - 16", 90),
    ("Laurieton", "31° 39.601'", "152° 56.235'", "Camden Haven - 10", 65),
    ("Crowdy Head", "31° 47.000'", "152° 55.200'", "Crowdy Harbour - 17", 79),
    ("Forster", "32° 13.211'", "152° 40.680'", "Cape Hawke Harbour - 16.5", 80),
    ("Wollongong", "34° 27.321'", "151° 04.308'", "Port Kembla - 15", 110),
    ("Shellharbour", "34° 33.720'", "151° 00.626'", "Shellharbour - 12", 105),
    ("Ulladulla", "35° 22.732'", "150° 41.776'", "Ulladulla Harbour - 20", 120),
    ("Batemans Bay", "35° 50.000'", "150° 22.630'", "Batemans Bay - 22", 120),
    ("Narooma", "36° 13.170'", "150° 17.450'", "Wagonga Inlet - 14", 120),
    ("Bermagui", "36° 25.320'", "150° 15.980'", "Bermagui - 17", 120),
    ("Far South Coast", "37° 01.317'", "150° 15.002'", "Eden - 30", 125),
    ("Trial Bay bait collection marker buoy", "30°52.760'", "153°03.110'", "Macleay River", 10),
]

ESTUARINE_REEFS = [
    ("Lake Macquarie", "33° 05.814'", "151° 36.891'", 520, "5"),
    ("Botany Bay", "33° 58.940'", "151° 13.447'", 400, "6-15"),
    ("Bellinger River 1", "30° 27.569'", "153° 02.360'", 50, "3"),
    ("Bellinger River 2", "30° 26.404'", "153° 01.110'", 50, "3"),
    ("Bellinger River 3", "30° 26.525'", "153° 00.786'", 50, "3"),
    ("St Georges Basin 1", "35° 07.449'", "150° 37.031'", 300, "4-6"),
    ("St Georges Basin 2", "35° 07.259'", "150° 37.928'", 300, "4-6"),
    ("Lake Conjola", "35° 15.628'", "150° 28.330'", 400, "4-8"),
    ("Merimbula Lake", "36° 53.918'", "149° 53.175'", 400, "5"),
]


def ddm_to_decimal(value: str, hemisphere: str) -> float:
    cleaned = value.replace("°", " ").replace("′", "'").replace("’", "'")
    match = re.search(r"(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)", cleaned)
    if not match:
        raise ValueError(value)
    decimal = float(match.group(1)) + float(match.group(2)) / 60
    if hemisphere in {"S", "W"}:
        decimal *= -1
    return round(decimal, 6)


def clean_id(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in value.lower())
    return "_".join(part for part in cleaned.split("_") if part)


def build_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, (name, lat, lon, access_distance, depth_m) in enumerate(FADS, start=1):
        rows.append(
            {
                "id": f"nsw_official_fad:{index:03d}:{clean_id(name)}",
                "jurisdiction": "NSW",
                "guide_name": "NSW official fish aggregating devices",
                "spot_name": name,
                "spot_type": "fad",
                "scope": "offshore_boat",
                "source_kind": "official_fad_coordinate_table",
                "official_owner": "NSW DPI / DPIRD",
                "official_url": FAD_URL,
                "latitude": ddm_to_decimal(lat, "S"),
                "longitude": ddm_to_decimal(lon, "E"),
                "coordinate_role": "official_coordinate",
                "distance_from_access": access_distance,
                "depth_m": depth_m,
                "planner_eligible": False,
                "map_eligible": True,
                "role": "offshore_boat_fishing_reference",
                "score_impact": "none",
                "review_status": "check_deployed_status_before_trip",
                "notes": "NSW official FAD coordinate. Offshore/boat-only reference; not a shore fishing spot.",
            }
        )
    for index, (name, lat, lon, reef_balls, depth_m) in enumerate(ESTUARINE_REEFS, start=1):
        rows.append(
            {
                "id": f"nsw_estuarine_artificial_reef:{index:03d}:{clean_id(name)}",
                "jurisdiction": "NSW",
                "guide_name": "NSW estuarine artificial reefs",
                "spot_name": name,
                "spot_type": "artificial_reef",
                "scope": "estuary_boat",
                "source_kind": "official_artificial_reef_coordinate_table",
                "official_owner": "NSW DPI / DPIRD",
                "official_url": REEF_URL,
                "latitude": ddm_to_decimal(lat, "S"),
                "longitude": ddm_to_decimal(lon, "E"),
                "coordinate_role": "official_coordinate",
                "reef_balls": reef_balls,
                "depth_m": depth_m,
                "planner_eligible": False,
                "map_eligible": True,
                "role": "offshore_boat_fishing_reference",
                "score_impact": "none",
                "review_status": "check_local_rules_and_navigation_before_trip",
                "notes": "NSW official estuarine artificial reef coordinate. Boat/estuary reference; not a shore access point.",
            }
        )
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
    print(json.dumps({"rows": len(rows)}, indent=2))


if __name__ == "__main__":
    main()
