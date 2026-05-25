"""Build NSW official offshore artificial reef map candidates."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path


OUTPUT_DIR = Path("docs/generated")
JSON_OUTPUT = OUTPUT_DIR / "nsw_offshore_artificial_reef_spots_2026-05-22.json"
CSV_OUTPUT = OUTPUT_DIR / "nsw_offshore_artificial_reef_spots_2026-05-22.csv"

SPOTS = [
    (
        "Sydney Offshore Artificial Reef",
        "https://www.dpi.nsw.gov.au/fishing/recreational/resources/artificial-reef/sydney-offshore-artificial-reef",
        "Sydney offshore artificial reef",
        "33°50.797' S",
        "151°17.988' E",
        "38",
    ),
    (
        'Southern Sydney "JD" Offshore Artificial Reef - Northern Patch',
        "https://www.dpi.nsw.gov.au/fishing/recreational/resources/artificial-reef/southern-sydney",
        'Southern Sydney "JD" offshore artificial reef',
        "34°05.659' S",
        "151°10.657' E",
        "30",
    ),
    (
        'Southern Sydney "JD" Offshore Artificial Reef - Southern Patch',
        "https://www.dpi.nsw.gov.au/fishing/recreational/resources/artificial-reef/southern-sydney",
        'Southern Sydney "JD" offshore artificial reef',
        "34°05.932' S",
        "151°10.439' E",
        "30",
    ),
    (
        "Wollongong Offshore Artificial Reef tower 1",
        "https://www.dpi.nsw.gov.au/fishing/recreational/resources/artificial-reef/wollongong-offshore-artificial-reef",
        "Wollongong offshore artificial reef",
        "34°31.081' S",
        "150°54.883' E",
        "32",
    ),
    (
        "Wollongong Offshore Artificial Reef tower 2",
        "https://www.dpi.nsw.gov.au/fishing/recreational/resources/artificial-reef/wollongong-offshore-artificial-reef",
        "Wollongong offshore artificial reef",
        "34°31.182' S",
        "150°54.795' E",
        "32",
    ),
    (
        "Terrigal Offshore Artificial Reef tower 1",
        "https://www.dpi.nsw.gov.au/fishing/recreational/resources/artificial-reef/terrigal-offshore-artificial-reef",
        "Terrigal offshore artificial reef",
        "33°27.607' S",
        "151°30.473' E",
        "47-48",
    ),
    (
        "Terrigal Offshore Artificial Reef tower 2",
        "https://www.dpi.nsw.gov.au/fishing/recreational/resources/artificial-reef/terrigal-offshore-artificial-reef",
        "Terrigal offshore artificial reef",
        "33°27.593' S",
        "151°30.431' E",
        "47-48",
    ),
    (
        "Port Macquarie Offshore Artificial Reef",
        "https://www.dpi.nsw.gov.au/fishing/recreational/resources/artificial-reef/port-macquarie-recreational-fishing-reef",
        "Port Macquarie offshore artificial reef",
        "31°25.044' S",
        "152°58.950' E",
        "46",
    ),
    (
        "Merimbula Offshore Artificial Reef tower 1",
        "https://www.dpi.nsw.gov.au/fishing/recreational/resources/artificial-reef/merimbula-offshore-artificial-reef",
        "Merimbula offshore artificial reef",
        "36°54.826' S",
        "149°56.245' E",
        "32",
    ),
    (
        "Merimbula Offshore Artificial Reef tower 2",
        "https://www.dpi.nsw.gov.au/fishing/recreational/resources/artificial-reef/merimbula-offshore-artificial-reef",
        "Merimbula offshore artificial reef",
        "36°54.870' S",
        "149°56.265' E",
        "32",
    ),
]


def clean_id(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in value.lower())
    return "_".join(part for part in cleaned.split("_") if part)


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


def build_rows() -> list[dict[str, object]]:
    rows = []
    for index, (name, url, guide_name, lat, lon, depth_m) in enumerate(SPOTS, start=1):
        rows.append(
            {
                "id": f"nsw_offshore_artificial_reef:{index:03d}:{clean_id(name)}",
                "jurisdiction": "NSW",
                "guide_name": guide_name,
                "spot_name": name,
                "spot_type": "artificial_reef",
                "scope": "offshore_boat",
                "source_kind": "official_offshore_artificial_reef_page",
                "official_owner": "NSW DPI / DPIRD",
                "official_url": url,
                "latitude": ddm_to_decimal(lat),
                "longitude": ddm_to_decimal(lon),
                "coordinate_role": "official_reef_coordinate",
                "depth_m": depth_m,
                "planner_eligible": False,
                "map_eligible": True,
                "role": "offshore_boat_fishing_reference",
                "score_impact": "none",
                "review_status": "check_weather_safety_and_rules_before_trip",
                "notes": "NSW official offshore artificial reef coordinate. Boat/offshore reference; not a shore access point.",
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
