"""Build NT official land-based fishing map candidates."""

from __future__ import annotations

import csv
import json
from pathlib import Path


OUTPUT_DIR = Path("docs/generated")
JSON_OUTPUT = OUTPUT_DIR / "nt_land_based_spots_2026-05-22.json"
CSV_OUTPUT = OUTPUT_DIR / "nt_land_based_spots_2026-05-22.csv"

STOKES_URL = "https://www.waterfront.nt.gov.au/stokes-hill-wharf"
PARKS_URL = "https://nt.gov.au/parks/safety-rules/boating-and-fishing-in-parks"
MANDORAH_URL = "https://infrastructure.nt.gov.au/project/mandorah-marine-facilities"


SPOTS = [
    ("Stokes Hill Wharf fishing platform", "wharf_fishing_platform", STOKES_URL, -12.46864, 130.850749, "tidal_estuary"),
    ("Rapid Creek fishing platform", "fishing_platform", PARKS_URL, -12.402471, 130.878903, "tidal_estuary"),
    ("Lee Point Rocks", "rocky_shoreline", PARKS_URL, -12.328281, 130.896014, "coastal_estuary"),
    ("Mandorah Jetty", "jetty", MANDORAH_URL, -12.443088, 130.768237, "coastal_estuary"),
]


def clean_id(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in value.lower())
    return "_".join(part for part in cleaned.split("_") if part)


def build_rows() -> list[dict[str, object]]:
    rows = []
    for index, (name, spot_type, url, lat, lon, scope) in enumerate(SPOTS, start=1):
        rows.append(
            {
                "id": f"nt_land_based:{index:03d}:{clean_id(name)}",
                "jurisdiction": "NT",
                "guide_name": "NT official land-based fishing references",
                "spot_name": name,
                "spot_type": spot_type,
                "scope": scope,
                "source_kind": "official_land_based_fishing_reference",
                "official_owner": "Northern Territory Government / Darwin Waterfront Corporation",
                "official_url": url,
                "latitude": lat,
                "longitude": lon,
                "coordinate_role": "spot_candidate",
                "planner_eligible": True,
                "map_eligible": True,
                "role": "public_fishing_access_candidate",
                "score_impact": "none",
                "review_status": "needs_current_access_crocodile_and_closure_check",
                "notes": "Official/government page names this as a fishing location or permitted fishing area. Verify on-site signage and crocodile safety before user-facing planning.",
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
