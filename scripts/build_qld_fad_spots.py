"""Build Queensland official FAD map candidates from the government table."""

from __future__ import annotations

import csv
from html.parser import HTMLParser
import html
import json
import re
from pathlib import Path
from urllib.request import Request, urlopen


SOURCE_URL = "https://www.qld.gov.au/recreation/activities/boating-fishing/rec-fishing/fish-aggregating-devices/locations"
OUTPUT_DIR = Path("docs/generated")
JSON_OUTPUT = OUTPUT_DIR / "qld_official_fad_spots_2026-05-22.json"
CSV_OUTPUT = OUTPUT_DIR / "qld_official_fad_spots_2026-05-22.csv"
USER_AGENT = "CoastalFishingForecast/0.1 qld-fad-builder"


class TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tables: list[list[list[str]]] = []
        self.current_table: list[list[str]] | None = None
        self.current_row: list[str] | None = None
        self.current_cell: list[str] | None = None
        self.in_cell = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            self.current_table = []
        elif tag == "tr" and self.current_table is not None:
            self.current_row = []
        elif tag in {"td", "th"} and self.current_row is not None:
            self.current_cell = []
            self.in_cell = True

    def handle_data(self, data: str) -> None:
        if self.in_cell and self.current_cell is not None:
            self.current_cell.append(data)

    def handle_entityref(self, name: str) -> None:
        if self.in_cell and self.current_cell is not None:
            self.current_cell.append(html.unescape(f"&{name};"))

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self.current_cell is not None and self.current_row is not None:
            value = " ".join("".join(self.current_cell).replace("\xa0", " ").split())
            self.current_row.append(value)
            self.current_cell = None
            self.in_cell = False
        elif tag == "tr" and self.current_row is not None and self.current_table is not None:
            if self.current_row:
                self.current_table.append(self.current_row)
            self.current_row = None
        elif tag == "table" and self.current_table is not None:
            self.tables.append(self.current_table)
            self.current_table = None


def ddm_to_decimal(value: str, *, default_hemisphere: str) -> float:
    cleaned = html.unescape(value).replace("°", " ").replace("′", "'").replace("’", "'")
    match = re.search(r"(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)'?\s*([NSEW])?", cleaned, re.I)
    if not match:
        raise ValueError(f"Unsupported coordinate: {value!r}")
    degrees = float(match.group(1))
    minutes = float(match.group(2))
    hemisphere = (match.group(3) or default_hemisphere).upper()
    decimal = degrees + minutes / 60
    if hemisphere in {"S", "W"}:
        decimal *= -1
    return round(decimal, 6)


def clean_id(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in value.lower())
    return "_".join(part for part in cleaned.split("_") if part)


def fetch_tables() -> list[list[list[str]]]:
    request = Request(SOURCE_URL, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=30) as response:
        text = response.read().decode("utf-8", errors="replace")
    parser = TableParser()
    parser.feed(text)
    return parser.tables


def build_rows() -> list[dict[str, object]]:
    rows = []
    for table in fetch_tables():
        for cells in table[1:]:
            if len(cells) < 6:
                continue
            fad_type, name, lat_text, lon_text, distance_text, depth_text = cells[:6]
            if "FAD" not in name:
                continue
            rows.append(
                {
                    "id": f"qld_official_fad:{clean_id(name)}",
                    "jurisdiction": "QLD",
                    "guide_name": "Find a fish aggregating device",
                    "spot_name": name,
                    "spot_type": "fad",
                    "fad_type": fad_type,
                    "scope": "offshore_boat",
                    "source_kind": "official_fad_coordinate_table",
                    "official_owner": "Queensland Government",
                    "official_url": SOURCE_URL,
                    "latitude": ddm_to_decimal(lat_text, default_hemisphere="S"),
                    "longitude": ddm_to_decimal(lon_text, default_hemisphere="E"),
                    "coordinate_role": "official_coordinate",
                    "distance_from_access_nm": distance_text,
                    "depth_m": depth_text,
                    "planner_eligible": False,
                    "map_eligible": True,
                    "role": "offshore_boat_fishing_reference",
                    "score_impact": "none",
                    "review_status": "check_deployed_status_before_trip",
                    "notes": "Queensland Government FAD coordinate. Offshore/boat-only reference; not a shore fishing spot.",
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
