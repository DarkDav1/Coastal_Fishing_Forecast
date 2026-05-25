"""Build Queensland Moreton Bay artificial reef map candidates."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path


SOURCE_URL = "https://parks.qld.gov.au/parks/moreton-bay/zoning/trial_artificial_reef_program"
OUTPUT_DIR = Path("docs/generated")
JSON_OUTPUT = OUTPUT_DIR / "qld_moreton_bay_artificial_reef_spots_2026-05-22.json"
CSV_OUTPUT = OUTPUT_DIR / "qld_moreton_bay_artificial_reef_spots_2026-05-22.csv"


REEFS = {
    "Harry Atkinson Artificial Reef": {
        "map_url": "https://parks.qld.gov.au/__data/assets/pdf_file/0039/166899/harry-atkinson-art-reef-map.pdf",
        "points": [
            ("27° 24.262' S", "153° 18.704' E"),
            ("27° 24.537' S", "153° 18.527' E"),
            ("27° 24.439' S", "153° 18.450' E"),
            ("27° 24.404' S", "153° 18.386' E"),
            ("27° 24.532' S", "153° 18.304' E"),
            ("27° 24.350' S", "153° 18.675' E"),
            ("27° 24.201' S", "153° 18.740' E"),
            ("27° 24.370' S", "153° 18.358' E"),
            ("27° 24.549' S", "153° 18.211' E"),
            ("27° 24.654' S", "153° 18.413' E"),
            ("27° 24.341' S", "153° 18.752' E"),
            ("27° 24.604' S", "153° 18.411' E"),
        ],
    },
    "West Peel Artificial Reef": {
        "map_url": "https://parks.qld.gov.au/__data/assets/pdf_file/0025/165760/west-peel-art-reef-map.pdf",
        "points": [
            ("27° 30.232' S", "153° 18.800' E"),
            ("27° 30.350' S", "153° 18.772' E"),
            ("27° 30.275' S", "153° 18.700' E"),
            ("27° 30.075' S", "153° 18.802' E"),
            ("27° 30.002' S", "153° 18.715' E"),
            ("27° 29.880' S", "153° 18.725' E"),
            ("27° 29.963' S", "153° 18.686' E"),
            ("27° 30.036' S", "153° 18.686' E"),
            ("27° 30.040' S", "153° 18.779' E"),
            ("27° 30.127' S", "153° 18.804' E"),
            ("27° 30.276' S", "153° 18.855' E"),
            ("27° 30.185' S", "153° 18.867' E"),
            ("27° 29.997' S", "153° 18.890' E"),
            ("27° 29.921' S", "153° 18.849' E"),
            ("27° 30.117' S", "153° 18.702' E"),
            ("27° 30.155' S", "153° 18.699' E"),
            ("27° 30.025' S", "153° 18.899' E"),
            ("27° 29.939' S", "153° 18.756' E"),
            ("27° 29.878' S", "153° 18.891' E"),
        ],
    },
    "East Coochie Artificial Reef": {
        "map_url": "https://parks.qld.gov.au/__data/assets/pdf_file/0025/166327/east-coochie-art-reef-map.pdf",
        "points": [
            ("27° 34.106' S", "153° 21.094' E"),
            ("27° 34.055' S", "153° 21.108' E"),
            ("27° 34.010' S", "153° 21.131' E"),
            ("27° 34.058' S", "153° 21.163' E"),
            ("27° 34.059' S", "153° 21.201' E"),
            ("27° 34.129' S", "153° 21.151' E"),
            ("27° 34.108' S", "153° 21.180' E"),
            ("27° 34.283' S", "153° 21.036' E"),
            ("27° 34.310' S", "153° 20.970' E"),
            ("27° 34.293' S", "153° 21.082' E"),
            ("27° 34.050' S", "153° 21.256' E"),
            ("27° 33.974' S", "153° 21.135' E"),
            ("27° 34.297' S", "153° 20.911' E"),
            ("27° 34.273' S", "153° 20.961' E"),
            ("27° 34.222' S", "153° 21.005' E"),
            ("27° 34.143' S", "153° 21.040' E"),
            ("27° 34.159' S", "153° 21.117' E"),
            ("27° 34.208' S", "153° 21.072' E"),
        ],
    },
    "Wild Banks Artificial Reef": {
        "map_url": "https://parks.qld.gov.au/__data/assets/pdf_file/0031/165757/wild-banks-art-reef-map.pdf",
        "points": [
            ("26° 54.678' S", "153° 17.829' E"),
            ("26° 54.530' S", "153° 17.463' E"),
            ("26° 54.238' S", "153° 17.290' E"),
            ("26° 54.659' S", "153° 18.195' E"),
            ("26° 55.041' S", "153° 17.862' E"),
            ("26° 54.363' S", "153° 16.919' E"),
            ("26° 54.004' S", "153° 17.271' E"),
        ],
    },
    "North Moreton Artificial Reef": {
        "map_url": "https://parks.qld.gov.au/__data/assets/pdf_file/0021/166332/north-moreton-art-reef-map.pdf",
        "points": [
            ("26° 59.104' S", "153° 24.165' E"),
            ("26° 59.613' S", "153° 24.150' E"),
            ("26° 59.187' S", "153° 24.524' E"),
            ("26° 58.516' S", "153° 23.574' E"),
            ("26° 58.945' S", "153° 23.197' E"),
            ("26° 58.953' S", "153° 23.594' E"),
            ("26° 59.390' S", "153° 24.051' E"),
        ],
    },
    "South Stradbroke Artificial Reef": {
        "map_url": "https://parks.qld.gov.au/__data/assets/pdf_file/0039/166989/south-stradbroke-art-reef-map.pdf",
        "points": [
            ("27° 52.416' S", "153° 27.334' E"),
            ("27° 52.784' S", "153° 27.316' E"),
            ("27° 53.141' S", "153° 27.400' E"),
            ("27° 53.279' S", "153° 27.588' E"),
        ],
    },
    "Turner Artificial Reef": {
        "map_url": "https://parks.qld.gov.au/__data/assets/pdf_file/0029/164657/turner-art-reef-map.pdf",
        "points": [
            ("27° 11.660' S", "153° 7.804' E"),
            ("27° 11.705' S", "153° 7.732' E"),
            ("27° 11.703' S", "153° 7.813' E"),
            ("27° 11.834' S", "153° 7.724' E"),
            ("27° 11.851' S", "153° 7.783' E"),
            ("27° 11.887' S", "153° 7.747' E"),
        ],
    },
    "North Stradbroke Island Artificial Reef": {
        "map_url": "https://parks.qld.gov.au/__data/assets/pdf_file/0025/168253/mpmp-north-stradbroke-is-artificial-reef-map.pdf",
        "points": [
            ("27° 24.546' S", "153° 30.387' E"),
            ("27° 24.567' S", "153° 30.428' E"),
            ("27° 24.598' S", "153° 30.528' E"),
            ("27° 24.653' S", "153° 30.404' E"),
            ("27° 24.598' S", "153° 30.318' E"),
        ],
    },
}


def clean_id(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in value.lower())
    return "_".join(part for part in cleaned.split("_") if part)


def ddm_to_decimal(value: str) -> float:
    match = re.search(r"(\d+(?:\.\d+)?)°\s*(\d+(?:\.\d+)?)'\s*([NSEW])", value)
    if not match:
        raise ValueError(f"Unsupported coordinate: {value!r}")
    degrees = float(match.group(1))
    minutes = float(match.group(2))
    hemisphere = match.group(3)
    decimal = degrees + minutes / 60
    if hemisphere in {"S", "W"}:
        decimal *= -1
    return round(decimal, 6)


def build_rows() -> list[dict[str, object]]:
    rows = []
    for reef_name, detail in REEFS.items():
        for index, (lat_text, lon_text) in enumerate(detail["points"], start=1):
            rows.append(
                {
                    "id": f"qld_moreton_bay_artificial_reef:{clean_id(reef_name)}:{index:02d}",
                    "jurisdiction": "QLD",
                    "guide_name": "Moreton Bay artificial reefs",
                    "spot_name": f"{reef_name} cluster {index}",
                    "reef_name": reef_name,
                    "spot_type": "artificial_reef",
                    "scope": "offshore_boat",
                    "source_kind": "official_artificial_reef_map_coordinate",
                    "official_owner": "Queensland Government",
                    "official_url": SOURCE_URL,
                    "map_url": detail["map_url"],
                    "latitude": ddm_to_decimal(lat_text),
                    "longitude": ddm_to_decimal(lon_text),
                    "coordinate_role": "official_reef_coordinate",
                    "planner_eligible": False,
                    "map_eligible": True,
                    "role": "offshore_boat_fishing_reference",
                    "score_impact": "none",
                    "review_status": "check_current_restrictions_before_trip",
                    "notes": "Queensland Government Moreton Bay artificial reef map coordinate. Boat/offshore reference; not a shore fishing spot.",
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
