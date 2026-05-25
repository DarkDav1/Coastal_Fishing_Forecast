"""Build NT official FAD and artificial reef map candidates."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path


OUTPUT_DIR = Path("docs/generated")
JSON_OUTPUT = OUTPUT_DIR / "nt_official_offshore_spots_2026-05-22.json"
CSV_OUTPUT = OUTPUT_DIR / "nt_official_offshore_spots_2026-05-22.csv"
FAD_URL = "https://nt.gov.au/marine/recreational-fishing/when-and-where-to-fish/fish-aggregating-device"
REEF_URL = "https://nt.gov.au/marine/recreational-fishing/when-and-where-to-fish/rules-for-fishing-in-specific-areas"


SPOTS = [
    ("FAD 1", "fad", FAD_URL, "12°09.500'S", "130°44.833'E", None, "pelagic FAD"),
    ("FAD 2", "fad", FAD_URL, "12°08.933'S", "130°44.833'E", None, "pelagic FAD"),
    ("FAD 3", "fad", FAD_URL, "12°10.300'S", "130°38.500'E", None, "pelagic FAD"),
    ("FAD 4", "fad", FAD_URL, "12°06.667'S", "130°34.133'E", None, "pelagic FAD"),
    ("Lee Point Wide", "artificial_reef", REEF_URL, "12 10.083'S", "130 47.033'E", 28, "engineered reef complex"),
    ("Gutters central", "artificial_reef", REEF_URL, "12 09.459'S", "130 34.655'E", 28, "engineered reef complex"),
    ("Dundee Wide", "artificial_reef", REEF_URL, "12 44.445'S", "130 10.387'E", 16, "engineered reef complex"),
    ("Adelaide River Mouth", "artificial_reef", REEF_URL, "12 07.587'S", "131 11.545'E", 16, "engineered reef complex"),
    ("Marchart 3", "artificial_reef", REEF_URL, "12° 10.275'S", "130° 40.635'E", 25, "Fenton Patches reef"),
    ("Bus Stop Reef", "artificial_reef", REEF_URL, "12° 11.163'S", "130° 41.165'E", 25, "Fenton Patches reef"),
    ("Pipeline Reef", "artificial_reef", REEF_URL, "12° 11.669'S", "130° 40.390'E", 25, "Fenton Patches reef"),
    ("Galah and Heron", "artificial_reef", REEF_URL, "12° 9.701'S", "130° 40.750'E", 25, "Fenton Patches reef"),
    ("Cockatoo and Mudlark", "artificial_reef", REEF_URL, "12° 10.097'S", "130° 39.732'E", 25, "Fenton Patches reef"),
    ("Amanda Lee", "artificial_reef", REEF_URL, "12° 09.691'S", "130° 40.721'E", 25, "Fenton Patches reef"),
    ("Antares and Steel Barge", "artificial_reef", REEF_URL, "12° 09.937'S", "130° 41.363'E", 25, "Fenton Patches reef"),
    ("Amelia C and Merindah Pearl", "artificial_reef", REEF_URL, "12° 09.810'S", "130° 41.409'E", 25, "Fenton Patches reef"),
    ("Ham Luong", "artificial_reef", REEF_URL, "12° 28.65'S", "130° 47.9'E", 24, "Darwin Harbour artificial reef"),
    ("John Holland Barge", "artificial_reef", REEF_URL, "12° 28.55'S", "130° 47.88'E", 24, "Darwin Harbour artificial reef"),
    ("Medkhanun 3", "artificial_reef", REEF_URL, "12° 28.710'S", "130° 48.145'E", 20, "Darwin Harbour artificial reef"),
    ("Bottlewasher Reef", "artificial_reef", REEF_URL, "12° 18.159'S", "130° 51.765'E", 15, "Lee Point artificial reef"),
    ("Truck Tipper Reef", "artificial_reef", REEF_URL, "12° 17.979'S", "130° 50.370'E", 15, "Lee Point artificial reef"),
    ("Rick Mills Reef", "artificial_reef", REEF_URL, "12° 18.451'S", "130° 48.872'E", 15, "Lee Point artificial reef"),
]


def ddm_to_decimal(value: str) -> float:
    cleaned = value.replace("°", " ").replace("′", "'").replace("’", "'")
    match = re.search(r"(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)'?\s*([NSEW])", cleaned, re.I)
    if not match:
        raise ValueError(value)
    degrees = float(match.group(1))
    minutes = float(match.group(2))
    hemisphere = match.group(3).upper()
    decimal = degrees + minutes / 60
    if hemisphere in {"S", "W"}:
        decimal *= -1
    return round(decimal, 6)


def clean_id(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in value.lower())
    return "_".join(part for part in cleaned.split("_") if part)


def build_rows() -> list[dict[str, object]]:
    rows = []
    for index, (name, spot_type, official_url, lat_text, lon_text, depth_m, group) in enumerate(SPOTS, start=1):
        rows.append(
            {
                "id": f"nt_official_offshore:{index:03d}:{clean_id(name)}",
                "jurisdiction": "NT",
                "guide_name": "NT official artificial reefs and FADs",
                "spot_name": name,
                "spot_type": spot_type,
                "group": group,
                "scope": "offshore_boat",
                "source_kind": "official_coordinate_list",
                "official_owner": "Northern Territory Government",
                "official_url": official_url,
                "latitude": ddm_to_decimal(lat_text),
                "longitude": ddm_to_decimal(lon_text),
                "coordinate_role": "official_coordinate",
                "depth_m": depth_m,
                "planner_eligible": False,
                "map_eligible": True,
                "role": "offshore_boat_fishing_reference",
                "score_impact": "none",
                "review_status": "check_weather_safety_and_closures_before_trip",
                "notes": "NT Government coordinate. Offshore/boat-only reference; not a shore fishing spot.",
            }
        )
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
    print(json.dumps({"rows": len(rows)}, indent=2))


if __name__ == "__main__":
    main()
