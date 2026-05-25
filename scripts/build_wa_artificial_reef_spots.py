"""Build WA official artificial reef map candidates from DPIRD."""

from __future__ import annotations

import csv
import html
from html.parser import HTMLParser
import json
import re
from pathlib import Path
from urllib.request import Request, urlopen


SOURCE_URL = "https://www.dpird.wa.gov.au/individuals/recreational-fishing/recreational-fishing-initiatives/artificial-reefs/"
ARCGIS_LAYER_URL = "https://services.arcgis.com/NxaIos6bsLPQJAmb/arcgis/rest/services/Artificial_Reefs/FeatureServer/0"
OUTPUT_DIR = Path("docs/generated")
JSON_OUTPUT = OUTPUT_DIR / "wa_artificial_reef_spots_2026-05-22.json"
CSV_OUTPUT = OUTPUT_DIR / "wa_artificial_reef_spots_2026-05-22.csv"

EXTRA_ARCGIS_REEFS = [
    ("Dampier Artificial Reef", -20.4353, 116.5631, 35, "DPIRD public artificial reefs ArcGIS layer"),
]


def fetch_html() -> str:
    request = Request(SOURCE_URL, headers={"User-Agent": "Mozilla/5.0 CoastalFishingForecast/0.1"})
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def text_from_html(fragment: str) -> str:
    return " ".join(html.unescape(re.sub(r"<.*?>", " ", fragment)).split())


def ddm_to_decimal(value: str, hemisphere: str) -> float:
    match = re.search(r"(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)", value.replace("°", " "))
    if not match:
        raise ValueError(value)
    decimal = float(match.group(1)) + float(match.group(2)) / 60
    if hemisphere in {"S", "W"}:
        decimal *= -1
    return round(decimal, 6)


def clean_id(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in value.lower())
    return "_".join(part for part in cleaned.split("_") if part)


def extract_items() -> list[tuple[str, str, str]]:
    text = fetch_html()
    pattern = re.compile(
        r'<div class="card__title">(.*?)</div>.*?<div class="card__desc">(.*?)</div>',
        re.S,
    )
    items = []
    for raw_title, raw_desc in pattern.findall(text):
        title = text_from_html(raw_title).replace("NEW! ", "")
        desc = text_from_html(raw_desc)
        if "Coordinates:" not in desc:
            continue
        coord_text = desc.split("Coordinates:", 1)[1].split("Depth:", 1)[0].strip()
        depth_text = desc.split("Depth:", 1)[1].split(" ", 2)[:2] if "Depth:" in desc else []
        depth = " ".join(depth_text)
        items.append((title, coord_text, depth))
    return items


def coordinate_pairs(coord_text: str) -> list[tuple[float, float, str]]:
    pairs = []
    # Examples include centre points and the Rottnest two-tower record.
    for lat_text, lon_text in re.findall(
        r"(\d+°\s*\d+(?:\.\d+)?'?\s*S).*?(\d+°\s*\d+(?:\.\d+)?'?\s*E)",
        coord_text,
        re.I,
    ):
        pairs.append((ddm_to_decimal(lat_text, "S"), ddm_to_decimal(lon_text, "E"), coord_text))
    return pairs


def build_rows() -> list[dict[str, object]]:
    rows = []
    for item_index, (title, coord_text, depth) in enumerate(extract_items(), start=1):
        pairs = coordinate_pairs(coord_text)
        for coord_index, (lat, lon, raw_coord) in enumerate(pairs, start=1):
            suffix = "" if len(pairs) == 1 else f" tower {coord_index}"
            spot_name = f"{title}{suffix}"
            rows.append(
                {
                    "id": f"wa_artificial_reef:{item_index:03d}:{coord_index:02d}:{clean_id(spot_name)}",
                    "jurisdiction": "WA",
                    "guide_name": "WA official artificial reefs",
                    "spot_name": spot_name,
                    "spot_type": "artificial_reef",
                    "scope": "offshore_boat",
                    "source_kind": "official_artificial_reef_coordinate_page",
                    "official_owner": "DPIRD Western Australia",
                    "official_url": SOURCE_URL,
                    "latitude": lat,
                    "longitude": lon,
                    "coordinate_role": "official_coordinate",
                    "depth_m": depth,
                    "raw_coordinate_text": raw_coord,
                    "planner_eligible": False,
                    "map_eligible": True,
                    "role": "offshore_boat_fishing_reference",
                    "score_impact": "none",
                    "review_status": "check_weather_safety_and_rules_before_trip",
                    "notes": "WA DPIRD official artificial reef coordinate. Boat/offshore reference; not a shore fishing spot.",
                }
            )
    existing_names = {row["spot_name"] for row in rows}
    for title, lat, lon, depth, note in EXTRA_ARCGIS_REEFS:
        if title in existing_names:
            continue
        rows.append(
            {
                "id": f"wa_artificial_reef:{len(rows) + 1:03d}:01:{clean_id(title)}",
                "jurisdiction": "WA",
                "guide_name": "WA official artificial reefs",
                "spot_name": title,
                "spot_type": "artificial_reef",
                "scope": "offshore_boat",
                "source_kind": "official_artificial_reef_arcgis_layer",
                "official_owner": "DPIRD Western Australia",
                "official_url": ARCGIS_LAYER_URL,
                "latitude": lat,
                "longitude": lon,
                "coordinate_role": "official_coordinate",
                "depth_m": depth,
                "raw_coordinate_text": note,
                "planner_eligible": False,
                "map_eligible": True,
                "role": "offshore_boat_fishing_reference",
                "score_impact": "none",
                "review_status": "check_weather_safety_and_rules_before_trip",
                "notes": "WA DPIRD official artificial reef coordinate from the public ArcGIS reef layer. Boat/offshore reference; not a shore fishing spot.",
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
