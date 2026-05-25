"""Build national relaxed-scope public fishing map candidates."""

from __future__ import annotations

import csv
import json
from pathlib import Path


OUTPUT_DIR = Path("docs/generated")
JSON_OUTPUT = OUTPUT_DIR / "au_relaxed_supplemental_fishing_spots_2026-05-24.json"
CSV_OUTPUT = OUTPUT_DIR / "au_relaxed_supplemental_fishing_spots_2026-05-24.csv"

VISIT_NSW_EUROBODALLA_URL = "https://www.visitnsw.com/destinations/south-coast/batemans-bay-and-eurobodalla/fishing"
VISIT_NSW_EXPERT_URL = "https://www.visitnsw.com/articles/experts-guide-to-fishing-nsw"
VISIT_NSW_CENTRAL_COAST_URL = "https://www.visitnsw.com/destinations/central-coast"
QLD_TRADE_BROCHURE_URL = "https://teq.queensland.com/content/dam/teq/corporate/corporate-searchable-assets/trade/sales-tools/2020_Queensland_Trade_Brochure.pdf"
QLD_DRIVE_MAP_URL = "https://www.queensland.com/content/dam/teq/consumer/global/documents/1714%20TEQ%20Drive%20Map%202024%20-%20online%20version.pdf"
VISIT_VICTORIA_FISHING_URL = "https://www.visitvictoria.com/see-and-do/outdoor-and-adventure/fishing"
VISIT_VICTORIA_PORTSEA_URL = "https://www.visitvictoria.com/regions/Mornington-Peninsula/See-and-do/Nature-and-wildlife/Beaches-and-coastlines/Portsea-Pier"
TOURISM_WA_DERBY_URL = "https://www.westernaustralia.com/en/attraction/derby-jetty/56b266deaeeeaaf773cf9966"
TOURISM_WA_ROCKINGHAM_URL = "https://www.westernaustralia.com/en/attraction/rockingham_jetty/5a0282b35981ef004149527d"
TOURISM_WA_PEPPERMINT_URL = "https://www.westernaustralia.com/en/Attraction/Peppermint_Grove_Beach/56b268c67b935fbe730e7eb8"
TOURISM_WA_PORT_GREGORY_URL = "https://www.westernaustralia.com/sg/places/port-gregory/56b267a32cbcbe7073ae1802"
TOURISM_WA_URL = "https://www.westernaustralia.com"


SPOTS = [
    # NSW relaxed-scope references from Visit NSW coastal fishing articles.
    ("NSW", "Durras Lake", "lake_estuary", "tidal_estuary", VISIT_NSW_EUROBODALLA_URL, -35.646591, 150.295607, "state_tourism_public_fishing_reference", "Visit NSW"),
    ("NSW", "Tuross Head jetties", "jetty", "coastal_estuary", VISIT_NSW_EUROBODALLA_URL, -36.059449, 150.138117, "state_tourism_public_fishing_reference", "Visit NSW"),
    ("NSW", "Mossy Point - Tomaga River", "river_jetty", "tidal_estuary", VISIT_NSW_EUROBODALLA_URL, -35.8390, 150.1790, "state_tourism_public_fishing_reference", "Visit NSW"),
    ("NSW", "Clyde River jetties", "river_jetty", "tidal_estuary", VISIT_NSW_EUROBODALLA_URL, -35.682591, 150.147971, "state_tourism_public_fishing_reference", "Visit NSW"),
    ("NSW", "Potato Point", "surf_beach", "coastal_estuary", VISIT_NSW_EUROBODALLA_URL, -36.096494, 150.135012, "state_tourism_public_fishing_reference", "Visit NSW"),
    ("NSW", "North Head Moruya", "headland_beach", "coastal_estuary", VISIT_NSW_EUROBODALLA_URL, -35.907283, 150.098116, "state_tourism_public_fishing_reference", "Visit NSW"),
    ("NSW", "Coffs Harbour Jetty", "jetty", "coastal_estuary", VISIT_NSW_EXPERT_URL, -30.304621, 153.142314, "state_tourism_public_fishing_reference", "Visit NSW"),
    ("NSW", "The Entrance Channel", "tidal_channel", "tidal_estuary", VISIT_NSW_CENTRAL_COAST_URL, -33.3430, 151.5010, "state_tourism_public_fishing_reference", "Visit NSW"),
    ("NSW", "Long Jetty", "jetty", "tidal_estuary", VISIT_NSW_CENTRAL_COAST_URL, -33.3547, 151.4884, "state_tourism_public_fishing_reference", "Visit NSW"),
    ("NSW", "Bateau Bay Beach", "beach", "coastal_estuary", VISIT_NSW_CENTRAL_COAST_URL, -33.384006, 151.483102, "state_tourism_public_fishing_reference", "Visit NSW"),
    ("NSW", "Jervis Bay", "bay", "coastal_estuary", VISIT_NSW_EXPERT_URL, -35.05666, 150.726202, "state_tourism_public_fishing_reference", "Visit NSW"),
    ("NSW", "Bermagui Harbour", "harbour", "coastal_estuary", VISIT_NSW_EXPERT_URL, -36.424889, 150.072448, "state_tourism_public_fishing_reference", "Visit NSW"),
    # Queensland relaxed-scope references from TEQ / Queensland tourism material.
    ("QLD", "Urangan Pier", "pier", "coastal_estuary", QLD_TRADE_BROCHURE_URL, -25.279588, 152.90592, "state_tourism_public_fishing_reference", "Queensland / TEQ"),
    ("QLD", "Shorncliffe Pier", "pier", "coastal_estuary", QLD_TRADE_BROCHURE_URL, -27.3277, 153.0834, "state_tourism_public_fishing_reference", "Queensland / TEQ"),
    ("QLD", "Woody Point Jetty", "jetty", "coastal_estuary", QLD_TRADE_BROCHURE_URL, -27.264133, 153.103056, "state_tourism_public_fishing_reference", "Queensland / TEQ"),
    ("QLD", "Redcliffe Jetty", "jetty", "coastal_estuary", QLD_TRADE_BROCHURE_URL, -27.226252, 153.116521, "state_tourism_public_fishing_reference", "Queensland / TEQ"),
    ("QLD", "Tallebudgera Creek", "tidal_creek", "tidal_estuary", QLD_DRIVE_MAP_URL, -28.123204, 153.444629, "state_tourism_public_fishing_reference", "Queensland / TEQ"),
    ("QLD", "Currumbin Creek", "tidal_creek", "tidal_estuary", QLD_DRIVE_MAP_URL, -28.136624, 153.471919, "state_tourism_public_fishing_reference", "Queensland / TEQ"),
    ("QLD", "Noosa River Mouth", "river_mouth", "tidal_estuary", QLD_DRIVE_MAP_URL, -26.3860, 153.0950, "state_tourism_public_fishing_reference", "Queensland / TEQ"),
    ("QLD", "Pumicestone Passage", "passage", "tidal_estuary", QLD_DRIVE_MAP_URL, -26.881799, 153.116145, "state_tourism_public_fishing_reference", "Queensland / TEQ"),
    ("QLD", "Tin Can Bay", "bay", "coastal_estuary", QLD_DRIVE_MAP_URL, -25.882854, 152.946179, "state_tourism_public_fishing_reference", "Queensland / TEQ"),
    ("QLD", "Round Hill Creek", "tidal_creek", "tidal_estuary", QLD_DRIVE_MAP_URL, -24.190217, 151.866046, "state_tourism_public_fishing_reference", "Queensland / TEQ"),
    ("QLD", "Agnes Water Beach", "beach", "coastal_estuary", QLD_DRIVE_MAP_URL, -24.198786, 151.901008, "state_tourism_public_fishing_reference", "Queensland / TEQ"),
    ("QLD", "Boyne Island", "estuary_coast", "coastal_estuary", QLD_DRIVE_MAP_URL, -23.924915, 151.32469, "state_tourism_public_fishing_reference", "Queensland / TEQ"),
    ("QLD", "Tannum Sands", "beach_estuary", "coastal_estuary", QLD_DRIVE_MAP_URL, -23.991104, 151.380872, "state_tourism_public_fishing_reference", "Queensland / TEQ"),
    ("QLD", "Lucinda Jetty", "jetty", "coastal_estuary", QLD_DRIVE_MAP_URL, -18.5200, 146.3330, "state_tourism_public_fishing_reference", "Queensland / TEQ"),
    ("QLD", "Cardwell Jetty", "jetty", "coastal_estuary", QLD_DRIVE_MAP_URL, -18.262549, 146.026513, "state_tourism_public_fishing_reference", "Queensland / TEQ"),
    ("QLD", "Palm Cove Jetty", "jetty", "coastal_estuary", QLD_DRIVE_MAP_URL, -16.739873, 145.673195, "state_tourism_public_fishing_reference", "Queensland / TEQ"),
    ("QLD", "Port Douglas Sugar Wharf", "wharf", "coastal_estuary", QLD_DRIVE_MAP_URL, -16.4808, 145.4620, "state_tourism_public_fishing_reference", "Queensland / TEQ"),
    ("QLD", "Bowen Jetty", "jetty", "coastal_estuary", QLD_DRIVE_MAP_URL, -20.0140, 148.2470, "state_tourism_public_fishing_reference", "Queensland / TEQ"),
    # Victoria relaxed-scope references from Visit Victoria coastal fishing material.
    ("VIC", "Rosebud Pier", "pier", "coastal_estuary", VISIT_VICTORIA_FISHING_URL, -38.351811, 144.907995, "state_tourism_public_fishing_reference", "Visit Victoria"),
    ("VIC", "Portsea Pier", "pier", "coastal_estuary", VISIT_VICTORIA_PORTSEA_URL, -38.318047, 144.713354, "state_tourism_public_fishing_reference", "Visit Victoria"),
    ("VIC", "Apollo Bay Harbour", "harbour", "coastal_estuary", VISIT_VICTORIA_FISHING_URL, -38.758445, 143.676959, "state_tourism_public_fishing_reference", "Visit Victoria"),
    ("VIC", "Lakes Entrance", "estuary_entrance", "tidal_estuary", VISIT_VICTORIA_FISHING_URL, -37.877796, 148.002392, "state_tourism_public_fishing_reference", "Visit Victoria"),
    ("VIC", "Newhaven Jetty", "jetty", "coastal_estuary", VISIT_VICTORIA_FISHING_URL, -38.512879, 145.362819, "state_tourism_public_fishing_reference", "Visit Victoria"),
    ("VIC", "Pearl Point Cape Conran", "surf_beach", "coastal_estuary", VISIT_VICTORIA_FISHING_URL, -37.78836, 148.769409, "state_tourism_public_fishing_reference", "Visit Victoria"),
    ("VIC", "Loch Sport Beach", "beach", "coastal_estuary", VISIT_VICTORIA_FISHING_URL, -38.0610, 147.5700, "state_tourism_public_fishing_reference", "Visit Victoria"),
    ("VIC", "Inverloch", "estuary_coast", "coastal_estuary", VISIT_VICTORIA_FISHING_URL, -38.633158, 145.72795, "state_tourism_public_fishing_reference", "Visit Victoria"),
    ("VIC", "Corinella", "estuary_coast", "coastal_estuary", VISIT_VICTORIA_FISHING_URL, -38.414581, 145.431202, "state_tourism_public_fishing_reference", "Visit Victoria"),
    ("VIC", "Port Welshpool Long Jetty", "jetty", "coastal_estuary", VISIT_VICTORIA_FISHING_URL, -38.701372, 146.452619, "state_tourism_public_fishing_reference", "Visit Victoria"),
    ("VIC", "Mallacoota Inlet", "inlet", "tidal_estuary", VISIT_VICTORIA_FISHING_URL, -37.468458, 149.68357, "state_tourism_public_fishing_reference", "Visit Victoria"),
    ("VIC", "St Kilda Pier", "pier", "coastal_estuary", VISIT_VICTORIA_FISHING_URL, -37.863774, 144.965679, "state_tourism_public_fishing_reference", "Visit Victoria"),
    # WA relaxed-scope references from Tourism WA attraction and destination pages.
    ("WA", "Derby Jetty", "jetty", "coastal_estuary", TOURISM_WA_DERBY_URL, -17.291568, 123.606927, "state_tourism_public_fishing_reference", "Tourism Western Australia"),
    ("WA", "Rockingham Jetty", "jetty", "coastal_estuary", TOURISM_WA_ROCKINGHAM_URL, -32.275469, 115.726684, "state_tourism_public_fishing_reference", "Tourism Western Australia"),
    ("WA", "Peppermint Grove Beach", "beach", "coastal_estuary", TOURISM_WA_PEPPERMINT_URL, -33.527989, 115.50725, "state_tourism_public_fishing_reference", "Tourism Western Australia"),
    ("WA", "Port Gregory Jetty", "jetty", "coastal_estuary", TOURISM_WA_PORT_GREGORY_URL, -28.1910, 114.2530, "state_tourism_public_fishing_reference", "Tourism Western Australia"),
    ("WA", "Busselton Jetty", "jetty", "coastal_estuary", TOURISM_WA_URL, -33.637326, 115.340753, "state_tourism_public_fishing_reference", "Tourism Western Australia"),
    ("WA", "Broome Town Beach Jetty", "jetty", "coastal_estuary", TOURISM_WA_URL, -17.9650, 122.2360, "state_tourism_public_fishing_reference", "Tourism Western Australia"),
    ("WA", "Carnarvon One Mile Jetty", "jetty", "coastal_estuary", TOURISM_WA_URL, -24.8900, 113.6530, "state_tourism_public_fishing_reference", "Tourism Western Australia"),
    ("WA", "Jurien Bay Jetty", "jetty", "coastal_estuary", TOURISM_WA_URL, -30.3023, 115.036102, "state_tourism_public_fishing_reference", "Tourism Western Australia"),
    ("WA", "Ocean Beach Denmark", "beach", "coastal_estuary", TOURISM_WA_URL, -34.981021, 117.338936, "state_tourism_public_fishing_reference", "Tourism Western Australia"),
    ("WA", "Emu Point Albany", "beach_point", "coastal_estuary", TOURISM_WA_URL, -34.9967, 117.945513, "state_tourism_public_fishing_reference", "Tourism Western Australia"),
    ("WA", "Taylor Street Jetty Esperance", "jetty", "coastal_estuary", TOURISM_WA_URL, -33.8600, 121.8930, "state_tourism_public_fishing_reference", "Tourism Western Australia"),
    ("WA", "Kalbarri River Mouth", "river_mouth", "tidal_estuary", TOURISM_WA_URL, -27.7110, 114.1640, "state_tourism_public_fishing_reference", "Tourism Western Australia"),
    ("WA", "Geraldton Fishermans Wharf", "wharf", "coastal_estuary", TOURISM_WA_URL, -28.7770, 114.6020, "state_tourism_public_fishing_reference", "Tourism Western Australia"),
    ("WA", "Hamelin Bay", "bay", "coastal_estuary", TOURISM_WA_URL, -34.220276, 115.031347, "state_tourism_public_fishing_reference", "Tourism Western Australia"),
    ("WA", "Augusta Boat Harbour", "harbour", "coastal_estuary", TOURISM_WA_URL, -34.353593, 115.167237, "state_tourism_public_fishing_reference", "Tourism Western Australia"),
]


def clean_id(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in value.lower())
    return "_".join(part for part in cleaned.split("_") if part)


def build_rows() -> list[dict[str, object]]:
    rows = []
    for index, (jurisdiction, name, spot_type, scope, url, lat, lon, source_kind, owner) in enumerate(SPOTS, start=1):
        rows.append(
            {
                "id": f"au_relaxed_supplemental:{index:03d}:{jurisdiction.lower()}:{clean_id(name)}",
                "jurisdiction": jurisdiction,
                "guide_name": "National relaxed-scope public fishing references",
                "spot_name": name,
                "spot_type": spot_type,
                "scope": scope,
                "source_kind": source_kind,
                "official_owner": owner,
                "official_url": url,
                "latitude": lat,
                "longitude": lon,
                "coordinate_role": "supplemental_spot_candidate",
                "planner_eligible": True,
                "map_eligible": True,
                "role": "supplemental_public_fishing_access_candidate",
                "score_impact": "none",
                "review_status": "needs_access_closure_and_local_rules_check",
                "notes": "Relaxed-scope public fishing reference. Use as a map candidate only until current access, closures, and local rules are checked.",
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
