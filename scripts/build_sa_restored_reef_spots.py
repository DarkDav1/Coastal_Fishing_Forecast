"""Build South Australia official restored reef map references."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path


OUTPUT_DIR = Path("docs/generated")
JSON_OUTPUT = OUTPUT_DIR / "sa_restored_reef_spots_2026-05-22.json"
CSV_OUTPUT = OUTPUT_DIR / "sa_restored_reef_spots_2026-05-22.csv"

WINDARA_SOURCE_URL = "https://dit.sa.gov.au/news/feed?a=408138"
WINDARA_CONTEXT_URL = "https://www.environment.sa.gov.au/goodliving/posts/2019/05/windara-reef"

SPOTS = [
    (
        "Windara Reef",
        "restored_shellfish_reef",
        "34°30.496' S",
        "137°53.953' E",
        WINDARA_SOURCE_URL,
        WINDARA_CONTEXT_URL,
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
    for index, (name, spot_type, lat, lon, url, context_url) in enumerate(SPOTS, start=1):
        rows.append(
            {
                "id": f"sa_restored_reef:{index:03d}:{clean_id(name)}",
                "jurisdiction": "SA",
                "guide_name": "South Australia restored shellfish reefs",
                "spot_name": name,
                "spot_type": spot_type,
                "scope": "coastal_estuary",
                "source_kind": "official_restored_reef_coordinate_reference",
                "official_owner": "South Australian Government",
                "official_url": url,
                "context_url": context_url,
                "latitude": ddm_to_decimal(lat),
                "longitude": ddm_to_decimal(lon),
                "coordinate_role": "official_coordinate_reference",
                "planner_eligible": False,
                "map_eligible": True,
                "role": "reef_context_reference",
                "score_impact": "none",
                "review_status": "check_current_marine_park_rules_before_trip",
                "notes": "Government coordinate reference for Windara Reef. Treat as a context/map reference until current fishing rules and access are verified.",
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
