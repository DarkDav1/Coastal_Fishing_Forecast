"""Build WA DPIRD official FAD map candidates from the public ArcGIS layer."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen


SOURCE_URL = "https://www.dpird.wa.gov.au/individuals/recreational-fishing/recreational-fishing-initiatives/fish-aggregating-devices/"
LAYER_URL = "https://services.arcgis.com/NxaIos6bsLPQJAmb/arcgis/rest/services/Fish_Aggregation_Devices__(FADs)_Public_view_layer/FeatureServer/0"
OUTPUT_DIR = Path("docs/generated")
JSON_OUTPUT = OUTPUT_DIR / "wa_official_fad_spots_2026-05-22.json"
CSV_OUTPUT = OUTPUT_DIR / "wa_official_fad_spots_2026-05-22.csv"


def clean_id(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in value.lower())
    return "_".join(part for part in cleaned.split("_") if part)


def fetch_features() -> list[dict[str, object]]:
    params = urlencode({"f": "geojson", "where": "1=1", "outFields": "*", "returnGeometry": "true"})
    with urlopen(f"{LAYER_URL}/query?{params}", timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))["features"]


def build_rows() -> list[dict[str, object]]:
    rows = []
    for feature in fetch_features():
        props = feature["properties"]
        lon, lat = feature["geometry"]["coordinates"][:2]
        fad_id = str(props.get("FAD_ID") or props.get("OBJECTID"))
        location = props.get("Location") or "WA"
        status = props.get("Status") or "Unknown"
        rows.append(
            {
                "id": f"wa_official_fad:{clean_id(location)}:{clean_id(fad_id)}",
                "jurisdiction": "WA",
                "guide_name": "WA DPIRD fish aggregating devices",
                "spot_name": f"{location} FAD {fad_id}",
                "spot_type": "fad",
                "scope": "offshore_boat",
                "source_kind": "official_arcgis_fad_layer",
                "official_owner": "DPIRD Western Australia",
                "official_url": SOURCE_URL,
                "layer_url": LAYER_URL,
                "latitude": round(float(lat), 6),
                "longitude": round(float(lon), 6),
                "coordinate_role": "official_map_coordinate",
                "deployment_status": status,
                "planner_eligible": False,
                "map_eligible": True,
                "role": "offshore_boat_fishing_reference",
                "score_impact": "none",
                "review_status": "check_current_deployment_status_before_trip",
                "notes": "WA DPIRD public FAD map coordinate. Some FADs may be not deployed or broken free; use deployment_status before showing as active.",
            }
        )
    rows.sort(key=lambda row: (str(row["spot_name"]), str(row["deployment_status"])))
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
    statuses: dict[str, int] = {}
    for row_item in rows:
        statuses[str(row_item["deployment_status"])] = statuses.get(str(row_item["deployment_status"]), 0) + 1
    print(json.dumps({"rows": len(rows), "statuses": statuses}, indent=2))


if __name__ == "__main__":
    main()
