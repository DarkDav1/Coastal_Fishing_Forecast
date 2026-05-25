"""Build relaxed-scope NT and SA public fishing map candidates."""

from __future__ import annotations

import csv
import json
from pathlib import Path


OUTPUT_DIR = Path("docs/generated")
JSON_OUTPUT = OUTPUT_DIR / "nt_sa_supplemental_fishing_spots_2026-05-22.json"
CSV_OUTPUT = OUTPUT_DIR / "nt_sa_supplemental_fishing_spots_2026-05-22.csv"

NT_PARKS_URL = "https://nt.gov.au/parks/safety-rules/boating-and-fishing-in-parks"
AFANT_URL = "https://afant.com.au/lbfg-darwin/"
NT_TOURISM_URL = "https://northernterritory.com/darwin-and-surrounds/see-and-do/fishing"
SA_MARINE_PARKS_URL = "https://www.marineparks.sa.gov.au/enjoy/fishing"
ELLISTON_URL = "https://elliston.com.au/attractions/fishing-information/"
FLEURIEU_URL = "https://www.visitfleurieucoast.com.au/webdata/resources/files/A35%20Local%20Fishing%20Spots.pdf"
SA_TOURISM_URL = "https://southaustralia.com"
WEARESA_URL = "https://www.weare.sa.gov.au/news/2023/q4/top-fishing-spots-in-south-australia"
CEDUNA_TOURISM_URL = "https://www.cedunatourism.com.au/denial-bay-collection-1/denial-bay-jetty"


SPOTS = [
    # NT.gov parks and reserve fishing sites.
    ("NT", "Buffalo Creek Rock Bar", "rock_bar", "tidal_estuary", NT_PARKS_URL, -12.3360, 130.9270, "official_parks_fishing_site", "Northern Territory Government"),
    ("NT", "Howard River Beach - Shoal Bay Coastal Reserve", "beach_river", "tidal_estuary", NT_PARKS_URL, -12.2450, 131.0480, "official_parks_fishing_site", "Northern Territory Government"),
    ("NT", "Howard River Beach - Tree Point Conservation Reserve", "beach_river", "tidal_estuary", NT_PARKS_URL, -12.2350, 131.0650, "official_parks_fishing_site", "Northern Territory Government"),
    ("NT", "Port Essington", "bay_coast", "coastal_estuary", NT_PARKS_URL, -11.23292, 132.14989, "official_parks_fishing_site", "Northern Territory Government"),
    ("NT", "Caiman Creek", "creek_mouth", "tidal_estuary", NT_PARKS_URL, -11.248546, 132.209626, "official_parks_fishing_site", "Northern Territory Government"),
    ("NT", "Scott's Creek", "creek_mouth", "tidal_estuary", NT_PARKS_URL, -12.7050, 131.3190, "official_parks_fishing_site", "Northern Territory Government"),
    ("NT", "Cape Hotham", "headland_coast", "coastal_estuary", NT_PARKS_URL, -12.0450, 131.3050, "official_parks_fishing_site", "Northern Territory Government"),
    ("NT", "Shady Camp saltwater", "tidal_river", "tidal_estuary", NT_PARKS_URL, -12.2760, 131.8560, "official_parks_fishing_site", "Northern Territory Government"),
    ("NT", "Stuart's Tree Fishing Camp", "tidal_river", "tidal_estuary", NT_PARKS_URL, -12.1690, 131.6900, "official_parks_fishing_site", "Northern Territory Government"),
    ("NT", "Channel Point Coastal Reserve", "coastal_reserve", "coastal_estuary", NT_PARKS_URL, -13.170263, 130.137131, "official_parks_fishing_site", "Northern Territory Government"),
    # Relaxed public-guide Darwin area additions.
    ("NT", "Dundee Beach", "beach", "coastal_estuary", AFANT_URL, -12.731014, 130.358574, "government_supported_public_guide_reference", "AFANT / NT Recreational Fishing Grant"),
    ("NT", "East Point Rocks", "rocky_shoreline", "coastal_estuary", AFANT_URL, -12.404497, 130.811705, "government_supported_public_guide_reference", "AFANT / NT Recreational Fishing Grant"),
    ("NT", "Nightcliff Jetty", "jetty", "coastal_estuary", AFANT_URL, -12.378925, 130.84194, "government_supported_public_guide_reference", "AFANT / NT Recreational Fishing Grant"),
    ("NT", "Cullen Bay rock wall", "breakwater", "coastal_estuary", AFANT_URL, -12.452372, 130.822843, "government_supported_public_guide_reference", "AFANT / NT Recreational Fishing Grant"),
    ("NT", "Elizabeth River Bridge", "bridge", "tidal_estuary", AFANT_URL, -12.5440, 130.9560, "government_supported_public_guide_reference", "AFANT / NT Recreational Fishing Grant"),
    ("NT", "Channel Island Bridge", "bridge", "tidal_estuary", AFANT_URL, -12.5530, 130.8720, "government_supported_public_guide_reference", "AFANT / NT Recreational Fishing Grant"),
    ("NT", "Fannie Bay shoreline", "shoreline", "coastal_estuary", NT_TOURISM_URL, -12.4260, 130.8360, "supplemental_public_fishing_guide", "Northern Territory tourism / public guide"),
    # SA Marine Parks and government/tourism/public guide additions.
    ("SA", "Waitpinga Beach", "surf_beach", "coastal_estuary", SA_MARINE_PARKS_URL, -35.636031, 138.504843, "government_public_fishing_experience_reference", "South Australian Marine Parks"),
    ("SA", "Locks Well Beach", "surf_beach", "coastal_estuary", SA_MARINE_PARKS_URL, -33.743098, 135.0247, "government_public_fishing_experience_reference", "South Australian Marine Parks"),
    ("SA", "Browns Beach", "surf_beach", "coastal_estuary", SA_MARINE_PARKS_URL, -35.2470, 136.8310, "government_public_fishing_experience_reference", "South Australian Marine Parks"),
    ("SA", "Second Valley Jetty", "jetty", "coastal_estuary", SA_MARINE_PARKS_URL, -35.5150, 138.2190, "government_public_fishing_experience_reference", "South Australian Marine Parks"),
    ("SA", "Stenhouse Bay Jetty", "jetty", "coastal_estuary", SA_MARINE_PARKS_URL, -35.27954, 136.943274, "government_public_fishing_experience_reference", "South Australian Parks"),
    ("SA", "Elliston Jetty", "jetty", "coastal_estuary", ELLISTON_URL, -33.638954, 134.87966, "local_tourism_fishing_guide", "Elliston official tourism"),
    ("SA", "Waterloo Bay South Point", "rock_ledge", "coastal_estuary", ELLISTON_URL, -33.632928, 134.880896, "local_tourism_fishing_guide", "Elliston official tourism"),
    ("SA", "Boords Beach", "beach_reef", "coastal_estuary", ELLISTON_URL, -33.661378, 134.89407, "local_tourism_fishing_guide", "Elliston official tourism"),
    ("SA", "Anxious Bay", "bay", "coastal_estuary", ELLISTON_URL, -33.33425, 134.64656, "local_tourism_fishing_guide", "Elliston official tourism"),
    ("SA", "Sheringa Beach", "surf_beach", "coastal_estuary", ELLISTON_URL, -33.871897, 135.170897, "local_tourism_fishing_guide", "Elliston official tourism"),
    ("SA", "Normanville Jetty", "jetty", "coastal_estuary", FLEURIEU_URL, -35.445288, 138.307605, "local_tourism_fishing_guide", "District Council of Yankalilla / Visit Fleurieu Coast"),
    ("SA", "Rapid Bay Jetty", "jetty", "coastal_estuary", FLEURIEU_URL, -35.521366, 138.185362, "local_tourism_fishing_guide", "District Council of Yankalilla / Visit Fleurieu Coast"),
    ("SA", "Cape Jervis Jetty", "jetty", "coastal_estuary", FLEURIEU_URL, -35.6039, 138.0967, "local_tourism_fishing_guide", "District Council of Yankalilla / Visit Fleurieu Coast"),
    ("SA", "Beachport Jetty", "jetty", "coastal_estuary", SA_TOURISM_URL, -37.48425, 140.018142, "state_tourism_fishing_reference", "South Australian tourism"),
    ("SA", "Port Germein Jetty", "jetty", "coastal_estuary", SA_TOURISM_URL, -33.029603, 137.995686, "state_tourism_fishing_reference", "South Australian tourism"),
    ("SA", "Whyalla Jetty", "jetty", "coastal_estuary", WEARESA_URL, -33.0346, 137.5840, "state_government_public_fishing_reference", "Government of South Australia / WE ARE.SA"),
    ("SA", "Port Hughes Jetty", "jetty", "coastal_estuary", SA_TOURISM_URL, -34.0730, 137.5500, "state_tourism_fishing_reference", "South Australian tourism"),
    ("SA", "Moonta Bay Jetty", "jetty", "coastal_estuary", SA_TOURISM_URL, -34.054321, 137.558551, "state_tourism_fishing_reference", "South Australian tourism"),
    ("SA", "Wallaroo Jetty", "jetty", "coastal_estuary", SA_TOURISM_URL, -33.929781, 137.626416, "state_tourism_fishing_reference", "South Australian tourism"),
    ("SA", "Edithburgh Jetty", "jetty", "coastal_estuary", SA_TOURISM_URL, -35.084796, 137.749608, "state_tourism_fishing_reference", "South Australian tourism"),
    ("SA", "Ardrossan Jetty", "jetty", "coastal_estuary", SA_TOURISM_URL, -34.423907, 137.923852, "state_tourism_fishing_reference", "South Australian tourism"),
    ("SA", "Glenelg Jetty", "jetty", "coastal_estuary", SA_TOURISM_URL, -34.980486, 138.509295, "state_tourism_fishing_reference", "South Australian tourism"),
    ("SA", "Semaphore Jetty", "jetty", "coastal_estuary", SA_TOURISM_URL, -34.837593, 138.477127, "state_tourism_fishing_reference", "South Australian tourism"),
    ("SA", "Grange Jetty", "jetty", "coastal_estuary", SA_TOURISM_URL, -34.902595, 138.487388, "state_tourism_fishing_reference", "South Australian tourism"),
    ("SA", "Brighton Jetty", "jetty", "coastal_estuary", SA_TOURISM_URL, -35.017455, 138.512613, "state_tourism_fishing_reference", "South Australian tourism"),
    ("SA", "Port Noarlunga Jetty", "jetty", "coastal_estuary", SA_TOURISM_URL, -35.149089, 138.466117, "state_tourism_fishing_reference", "South Australian tourism"),
    ("SA", "Emu Bay Jetty", "jetty", "coastal_estuary", SA_TOURISM_URL, -35.591278, 137.50624, "state_tourism_fishing_reference", "South Australian tourism"),
    ("SA", "Kingscote Jetty", "jetty", "coastal_estuary", SA_TOURISM_URL, -35.6540, 137.6400, "state_tourism_fishing_reference", "South Australian tourism"),
    ("SA", "American River Wharf", "wharf", "coastal_estuary", SA_TOURISM_URL, -35.7770, 137.7750, "state_tourism_fishing_reference", "South Australian tourism"),
    ("SA", "Denial Bay Jetty", "jetty", "coastal_estuary", CEDUNA_TOURISM_URL, -32.1000, 133.5750, "local_tourism_fishing_guide", "Ceduna Tourism"),
    ("SA", "Ceduna Jetty", "jetty", "coastal_estuary", SA_TOURISM_URL, -32.1260, 133.6720, "state_tourism_fishing_reference", "South Australian tourism"),
    ("SA", "Tumby Bay Jetty", "jetty", "coastal_estuary", SA_TOURISM_URL, -34.377616, 136.105514, "state_tourism_fishing_reference", "South Australian tourism"),
    ("SA", "Port Neill Jetty", "jetty", "coastal_estuary", SA_TOURISM_URL, -34.1160, 136.3490, "state_tourism_fishing_reference", "South Australian tourism"),
    ("SA", "Venus Bay Jetty", "jetty", "coastal_estuary", SA_TOURISM_URL, -33.2300, 134.6750, "state_tourism_fishing_reference", "South Australian tourism"),
    ("SA", "Port Kenny Jetty", "jetty", "coastal_estuary", SA_TOURISM_URL, -33.1680, 134.6920, "state_tourism_fishing_reference", "South Australian tourism"),
    ("SA", "Sugars Beach", "beach_river_mouth", "tidal_estuary", WEARESA_URL, -35.552618, 138.887819, "state_government_public_fishing_reference", "Government of South Australia / WE ARE.SA"),
    ("SA", "Goolwa Beach", "surf_beach", "coastal_estuary", SA_TOURISM_URL, -35.514152, 138.760957, "state_tourism_fishing_reference", "South Australian tourism"),
    ("SA", "Murray Mouth", "river_mouth", "tidal_estuary", SA_TOURISM_URL, -35.539164, 138.875548, "state_tourism_fishing_reference", "South Australian tourism"),
]


def clean_id(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in value.lower())
    return "_".join(part for part in cleaned.split("_") if part)


def build_rows() -> list[dict[str, object]]:
    rows = []
    for index, (jurisdiction, name, spot_type, scope, url, lat, lon, source_kind, owner) in enumerate(SPOTS, start=1):
        is_nt = jurisdiction == "NT"
        rows.append(
            {
                "id": f"{jurisdiction.lower()}_supplemental_fishing:{index:03d}:{clean_id(name)}",
                "jurisdiction": jurisdiction,
                "guide_name": "Relaxed-scope public fishing references",
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
                "review_status": "needs_crocodile_access_and_closure_check" if is_nt else "needs_access_closure_and_local_rules_check",
                "notes": "Relaxed-scope fishing reference. Use as a map candidate only until current access, closures, and local rules are checked.",
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
