"""Build Victoria VFA recreational reef map candidates."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path


OUTPUT_DIR = Path("docs/generated")
JSON_OUTPUT = OUTPUT_DIR / "vic_recreational_reef_spots_2026-05-22.json"
CSV_OUTPUT = OUTPUT_DIR / "vic_recreational_reef_spots_2026-05-22.csv"

CORIO_URL = "https://vfa.vic.gov.au/recreational-fishing/fishing-locations/recreational-fishing-reefs/corio-bay-rocky-reefs"
BOAT_REEFS_URL = "https://vfa.vic.gov.au/recreational-fishing/fishing-locations/recreational-fishing-reefs/boat-based-reefs"
KINGFISH_URL = "https://vfa.vic.gov.au/recreational-fishing/fishing-locations/recreational-fishing-reefs/kingfish-reefs-in-port-phillip"
KAYAKER_URL = "https://vfa.vic.gov.au/recreational-fishing/fishing-locations/recreational-fishing-reefs/kayakers-reef"
TORQUAY_URL = "https://vfa.vic.gov.au/recreational-fishing/fishing-locations/recreational-fishing-reefs/torquay-offshore-recreational-fishing-reef"


SPOTS = [
    ("Merv's Reef", "Corio Bay Rocky Reefs", CORIO_URL, "shore_reachable_reef", "38° 07.228' S", "144° 21.658' E", "coastal_estuary"),
    ("Moolap Reef", "Corio Bay Rocky Reefs", CORIO_URL, "artificial_reef", "38° 06.374' S", "144° 28.581' E", "coastal_estuary"),
    ("Wilson's Reef", "Corio Bay Rocky Reefs", CORIO_URL, "artificial_reef", "38° 03.436' S", "144° 36.588' E", "coastal_estuary"),
    ("Rhys Reef - Aspendale Far North Pallet Ball", "Port Phillip Bay boat based reefs", BOAT_REEFS_URL, "artificial_reef", "38° 02.152' S", "145° 04.616' E", "coastal_estuary"),
    ("Rhys Reef - Aspendale Far East Pallet Ball", "Port Phillip Bay boat based reefs", BOAT_REEFS_URL, "artificial_reef", "38° 02.168' S", "145° 04.636' E", "coastal_estuary"),
    ("Rhys Reef - Aspendale Far South Pallet Ball", "Port Phillip Bay boat based reefs", BOAT_REEFS_URL, "artificial_reef", "38° 02.184' S", "145° 04.615' E", "coastal_estuary"),
    ("Rhys Reef - Aspendale Far West Pallet Ball", "Port Phillip Bay boat based reefs", BOAT_REEFS_URL, "artificial_reef", "38° 02.167' S", "145° 04.596' E", "coastal_estuary"),
    ("Tedesco Reef - Seaford Far North Pallet Ball", "Port Phillip Bay boat based reefs", BOAT_REEFS_URL, "artificial_reef", "38° 05.229' S", "145° 05.954' E", "coastal_estuary"),
    ("Tedesco Reef - Seaford Far East Pallet Ball", "Port Phillip Bay boat based reefs", BOAT_REEFS_URL, "artificial_reef", "38° 05.246' S", "145° 05.974' E", "coastal_estuary"),
    ("Tedesco Reef - Seaford Far South Pallet Ball", "Port Phillip Bay boat based reefs", BOAT_REEFS_URL, "artificial_reef", "38° 05.261' S", "145° 05.953' E", "coastal_estuary"),
    ("Tedesco Reef - Seaford Far West Pallet Ball", "Port Phillip Bay boat based reefs", BOAT_REEFS_URL, "artificial_reef", "38° 05.245' S", "145° 05.934' E", "coastal_estuary"),
    ("Yakka Reef - Frankston Far North Pallet Ball", "Port Phillip Bay boat based reefs", BOAT_REEFS_URL, "artificial_reef", "38° 08.467' S", "145° 05.480' E", "coastal_estuary"),
    ("Yakka Reef - Frankston Far East Pallet Ball", "Port Phillip Bay boat based reefs", BOAT_REEFS_URL, "artificial_reef", "38° 08.483' S", "145° 05.500' E", "coastal_estuary"),
    ("Yakka Reef - Frankston Far South Pallet Ball", "Port Phillip Bay boat based reefs", BOAT_REEFS_URL, "artificial_reef", "38° 08.499' S", "145° 05.479' E", "coastal_estuary"),
    ("Yakka Reef - Frankston Far West Pallet Ball", "Port Phillip Bay boat based reefs", BOAT_REEFS_URL, "artificial_reef", "38° 08.482' S", "145° 05.459' E", "coastal_estuary"),
    ("Kayaker's Reef", "Kayaker's Reef", KAYAKER_URL, "kayak_reef", "37° 51.370' S", "144° 56.810' E", "coastal_estuary"),
    ("Torquay Offshore Reef boundary 1", "Torquay Offshore Recreational Fishing Reef", TORQUAY_URL, "artificial_reef_boundary", "38° 19.828' S", "144° 22.500' E", "offshore_boat"),
    ("Torquay Offshore Reef boundary 2", "Torquay Offshore Recreational Fishing Reef", TORQUAY_URL, "artificial_reef_boundary", "38° 19.942' S", "144° 22.600' E", "offshore_boat"),
    ("Torquay Offshore Reef boundary 3", "Torquay Offshore Recreational Fishing Reef", TORQUAY_URL, "artificial_reef_boundary", "38° 20.184' S", "144° 22.320' E", "offshore_boat"),
    ("Torquay Offshore Reef boundary 4", "Torquay Offshore Recreational Fishing Reef", TORQUAY_URL, "artificial_reef_boundary", "38° 20.065' S", "144° 22.225' E", "offshore_boat"),
]

KINGFISH_MODULES = [
    (1, 38, 17.94690, 144, 40.65402),
    (2, 38, 17.95332, 144, 40.65378),
    (3, 38, 17.95350, 144, 40.66200),
    (4, 38, 17.94702, 144, 40.66224),
    (5, 38, 17.96166, 144, 40.62438),
    (6, 38, 17.96814, 144, 40.62414),
    (7, 38, 17.96832, 144, 40.63242),
    (8, 38, 17.96184, 144, 40.63260),
    (9, 38, 17.93562, 144, 40.61088),
    (10, 38, 17.94210, 144, 40.61064),
    (11, 38, 17.94228, 144, 40.61892),
    (12, 38, 17.93580, 144, 40.61910),
    (13, 38, 17.92146, 144, 40.64304),
    (14, 38, 17.92794, 144, 40.64286),
    (15, 38, 17.92812, 144, 40.65108),
    (16, 38, 17.92164, 144, 40.65126),
]


def clean_id(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in value.lower())
    return "_".join(part for part in cleaned.split("_") if part)


def ddm_to_decimal(value: str) -> float:
    match = re.search(r"(\d+(?:\.\d+)?)°\s*(\d+(?:\.\d+)?)'?\s*([NSEW])", value)
    if not match:
        raise ValueError(value)
    degrees = float(match.group(1))
    minutes = float(match.group(2))
    hemisphere = match.group(3)
    decimal = degrees + minutes / 60
    if hemisphere in {"S", "W"}:
        decimal *= -1
    return round(decimal, 6)


def build_rows() -> list[dict[str, object]]:
    rows = []
    for index, (name, guide_name, official_url, spot_type, lat_text, lon_text, scope) in enumerate(SPOTS, start=1):
        rows.append(row(index, name, guide_name, official_url, spot_type, ddm_to_decimal(lat_text), ddm_to_decimal(lon_text), scope))
    offset = len(rows)
    for module, lat_deg, lat_min, lon_deg, lon_min in KINGFISH_MODULES:
        name = f"Kingfish Reef module {module}"
        rows.append(
            row(
                offset + module,
                name,
                "Kingfish reefs in Port Phillip",
                KINGFISH_URL,
                "kingfish_artificial_reef_module",
                round(-(lat_deg + lat_min / 60), 6),
                round(lon_deg + lon_min / 60, 6),
                "offshore_boat",
            )
        )
    return rows


def row(index: int, name: str, guide_name: str, official_url: str, spot_type: str, lat: float, lon: float, scope: str) -> dict[str, object]:
    planner_eligible = spot_type == "shore_reachable_reef"
    return {
        "id": f"vic_recreational_reef:{index:03d}:{clean_id(name)}",
        "jurisdiction": "VIC",
        "guide_name": guide_name,
        "spot_name": name,
        "spot_type": spot_type,
        "scope": scope,
        "source_kind": "official_recreational_reef_coordinate",
        "official_owner": "Victorian Fisheries Authority",
        "official_url": official_url,
        "latitude": lat,
        "longitude": lon,
        "coordinate_role": "official_reef_coordinate",
        "planner_eligible": planner_eligible,
        "map_eligible": True,
        "role": "public_fishing_access_candidate" if planner_eligible else "offshore_boat_fishing_reference",
        "score_impact": "none",
        "review_status": "check_current_rules_access_and_weather_before_trip",
        "notes": "VFA recreational fishing reef coordinate. Keep as a map/reference layer unless shore access is explicit.",
    }


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
