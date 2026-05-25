"""Combine generated official spot-level lists into one map feed."""

from __future__ import annotations

import csv
import json
from pathlib import Path


INPUTS = [
    Path("docs/generated/nsw_sydney_harbour_go_fishing_spots_2026-05-22.json"),
    Path("docs/generated/nsw_official_fad_and_reef_spots_2026-05-22.json"),
    Path("docs/generated/nsw_offshore_artificial_reef_spots_2026-05-22.json"),
    Path("docs/generated/vic_go_fishing_spots_2026-05-22.json"),
    Path("docs/generated/vic_recreational_reef_spots_2026-05-22.json"),
    Path("docs/generated/qld_official_fad_spots_2026-05-22.json"),
    Path("docs/generated/qld_moreton_bay_artificial_reef_spots_2026-05-22.json"),
    Path("docs/generated/nt_official_offshore_spots_2026-05-22.json"),
    Path("docs/generated/nt_land_based_spots_2026-05-22.json"),
    Path("docs/generated/wa_artificial_reef_spots_2026-05-22.json"),
    Path("docs/generated/wa_official_fad_spots_2026-05-22.json"),
    Path("docs/generated/tas_hot_fishing_spots_2026-05-22.json"),
    Path("docs/generated/sa_restored_reef_spots_2026-05-22.json"),
    Path("docs/generated/nt_sa_supplemental_fishing_spots_2026-05-22.json"),
    Path("docs/generated/au_relaxed_supplemental_fishing_spots_2026-05-24.json"),
]
OUTPUT_DIR = Path("docs/generated")
JSON_OUTPUT = OUTPUT_DIR / "official_fishing_spots_combined_2026-05-22.json"
CSV_OUTPUT = OUTPUT_DIR / "official_fishing_spots_combined_2026-05-22.csv"


def load_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in INPUTS:
        rows.extend(json.loads(path.read_text(encoding="utf-8")))
    rows.sort(key=lambda row: (str(row.get("jurisdiction")), str(row.get("guide_name")), str(row.get("spot_name"))))
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
    rows = load_rows()
    write_outputs(rows)
    missing = sum(1 for row in rows if row.get("latitude") is None or row.get("longitude") is None)
    print(json.dumps({"rows": len(rows), "missing_coordinates": missing}, indent=2))


if __name__ == "__main__":
    main()
