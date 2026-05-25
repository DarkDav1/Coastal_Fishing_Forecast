import json
import unittest
from urllib.parse import parse_qs, urlparse

from coastal_fishing_forecast.structures import (
    fetch_combined_structure_facilities,
    fetch_qld_boating_facilities,
    normalize_list_mast_facilities,
    normalize_list_wildfisheries_sea_spots,
    normalize_nsw_boat_ramp_facilities,
    normalize_nt_public_boat_ramps,
    normalize_official_fishing_spots,
    normalize_osm_structure_facilities,
    normalize_qld_boating_facilities,
    normalize_sa_boat_ramp_facilities,
    normalize_vic_boating_facilities,
    normalize_wa_public_boat_ramps,
)


class StructureFacilityTests(unittest.TestCase):
    def test_osm_public_jetty_is_planner_eligible(self) -> None:
        payload = {
            "elements": [
                {
                    "type": "way",
                    "id": 208921096,
                    "center": {"lat": -42.8922322, "lon": 147.3378037},
                    "tags": {
                        "man_made": "pier",
                        "name": "Battery Point Public Jetty",
                    },
                }
            ]
        }

        facilities = normalize_osm_structure_facilities(payload, lat=-42.8991036, lon=147.3389916)

        self.assertEqual(facilities[0]["type"], "public_jetty")
        self.assertEqual(facilities[0]["access"], "public")
        self.assertTrue(facilities[0]["planner_eligible"])
        self.assertTrue(facilities[0]["map_eligible"])
        self.assertEqual(facilities[0]["role"], "public_fishing_access")

    def test_private_pier_is_not_public_jetty(self) -> None:
        payload = {
            "elements": [
                {
                    "type": "way",
                    "id": 169564861,
                    "center": {"lat": -42.9005236, "lon": 147.3327479},
                    "tags": {
                        "access": "private",
                        "man_made": "pier",
                    },
                }
            ]
        }

        facilities = normalize_osm_structure_facilities(payload, lat=-42.8991036, lon=147.3389916)

        self.assertEqual(facilities[0]["type"], "pier")
        self.assertEqual(facilities[0]["access"], "private")
        self.assertFalse(facilities[0]["planner_eligible"])
        self.assertFalse(facilities[0]["map_eligible"])
        self.assertEqual(facilities[0]["role"], "hidden")

    def test_osm_fishing_tag_is_planner_eligible_when_public(self) -> None:
        payload = {
            "elements": [
                {
                    "type": "node",
                    "id": 4242,
                    "lat": -42.895,
                    "lon": 147.335,
                    "tags": {
                        "access": "public",
                        "fishing": "yes",
                        "name": "Signed Fishing Platform",
                    },
                }
            ]
        }

        facilities = normalize_osm_structure_facilities(payload, lat=-42.8991036, lon=147.3389916)

        self.assertEqual(facilities[0]["type"], "fishing_platform")
        self.assertEqual(facilities[0]["label"], "Signed Fishing Platform")
        self.assertTrue(facilities[0]["planner_eligible"])
        self.assertTrue(facilities[0]["map_eligible"])
        self.assertEqual(facilities[0]["role"], "public_fishing_access")

    def test_list_mast_boat_ramp_is_public_access_but_not_jetty_advice(self) -> None:
        payload = {
            "features": [
                {
                    "attributes": {
                        "OBJECTID": 256,
                        "DESCRIPT": "Boat Ramp",
                        "NAME": None,
                    },
                    "geometry": {"x": 147.33208449055377, "y": -42.89874443445046},
                }
            ]
        }

        facilities = normalize_list_mast_facilities(payload, lat=-42.8991036, lon=147.3389916)

        self.assertEqual(facilities[0]["type"], "boat_ramp")
        self.assertEqual(facilities[0]["access"], "public")
        self.assertEqual(facilities[0]["source"], "list_mast")
        self.assertFalse(facilities[0]["planner_eligible"])
        self.assertTrue(facilities[0]["map_eligible"])
        self.assertEqual(facilities[0]["role"], "public_access_only")

    def test_osm_public_boat_ramp_is_map_only(self) -> None:
        payload = {
            "elements": [
                {
                    "type": "node",
                    "id": 8181,
                    "lat": -42.898,
                    "lon": 147.332,
                    "tags": {
                        "access": "public",
                        "fee": "no",
                        "leisure": "slipway",
                        "name": "Public Boat Ramp",
                    },
                }
            ]
        }

        facilities = normalize_osm_structure_facilities(payload, lat=-42.8991036, lon=147.3389916)

        self.assertEqual(facilities[0]["type"], "boat_ramp")
        self.assertEqual(facilities[0]["access"], "public")
        self.assertFalse(facilities[0]["planner_eligible"])
        self.assertTrue(facilities[0]["map_eligible"])
        self.assertEqual(facilities[0]["role"], "public_access_only")

    def test_osm_paid_boat_ramp_is_hidden(self) -> None:
        payload = {
            "elements": [
                {
                    "type": "node",
                    "id": 8282,
                    "lat": -42.898,
                    "lon": 147.332,
                    "tags": {
                        "access": "public",
                        "amenity": "boat_ramp",
                        "fee": "yes",
                        "name": "Paid Ramp",
                    },
                }
            ]
        }

        facilities = normalize_osm_structure_facilities(payload, lat=-42.8991036, lon=147.3389916)

        self.assertEqual(facilities[0]["type"], "boat_ramp")
        self.assertEqual(facilities[0]["access"], "private")
        self.assertFalse(facilities[0]["planner_eligible"])
        self.assertFalse(facilities[0]["map_eligible"])
        self.assertEqual(facilities[0]["role"], "hidden")

    def test_list_wildfisheries_sea_spot_is_planner_ready_public_access(self) -> None:
        payload = {
            "features": [
                {
                    "attributes": {
                        "OBJECTID": 33,
                        "SITE_LOCAT": "Purdon and Featherston Reserve, \nBattery Point",
                        "DESCRIPTIO": "This concrete jetty is 35 metres long by 4 metres wide.",
                        "TABLE_S": "Yes",
                        "RUBBISH_BI": "Yes",
                        "LIGHTING": "Yes",
                    },
                    "geometry": {"x": 147.33752, "y": -42.89205},
                }
            ]
        }

        facilities = normalize_list_wildfisheries_sea_spots(payload, lat=-42.8991036, lon=147.3389916)

        self.assertEqual(facilities[0]["id"], "list_wildfisheries:33")
        self.assertEqual(facilities[0]["label"], "Purdon and Featherston Reserve, Battery Point")
        self.assertEqual(facilities[0]["type"], "public_jetty")
        self.assertEqual(facilities[0]["access"], "public")
        self.assertEqual(facilities[0]["source"], "list_wildfisheries")
        self.assertTrue(facilities[0]["planner_eligible"])
        self.assertTrue(facilities[0]["map_eligible"])
        self.assertTrue(facilities[0]["amenities"]["lighting"])

    def test_nsw_official_boat_ramp_is_map_only_and_skips_fee_required(self) -> None:
        payload = {
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [153.465, -28.954]},
                    "properties": {"BOAT_RAMP_ID": 1, "DESCRIPTION": "East Wardell Boat Ramp", "FEE_PAYABLE": "No"},
                },
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [153.466, -28.954]},
                    "properties": {"BOAT_RAMP_ID": 2, "DESCRIPTION": "Paid Marina Ramp", "FEE_PAYABLE": "Yes"},
                },
            ]
        }

        facilities = normalize_nsw_boat_ramp_facilities(payload, lat=-28.954, lon=153.465, radius_m=2000)

        self.assertEqual(len(facilities), 1)
        self.assertEqual(facilities[0]["source"], "nsw_maritime_boat_ramps")
        self.assertEqual(facilities[0]["type"], "boat_ramp")
        self.assertFalse(facilities[0]["planner_eligible"])
        self.assertTrue(facilities[0]["map_eligible"])
        self.assertEqual(facilities[0]["role"], "public_access_only")

    def test_qld_official_boating_facility_keeps_boat_ramps_only(self) -> None:
        payload = {
            "results": [
                {
                    "name": "Hollywell, Jasmine Avenue",
                    "facility": "Boat Ramp",
                    "tmr_id": "GB81",
                    "latitude": -27.896231,
                    "longitude": 153.402644,
                },
                {
                    "name": "Pontoon only",
                    "facility": "Pontoon",
                    "latitude": -27.896,
                    "longitude": 153.403,
                },
            ]
        }

        facilities = normalize_qld_boating_facilities(payload, lat=-27.896, lon=153.403, radius_m=2000)

        self.assertEqual(len(facilities), 1)
        self.assertEqual(facilities[0]["source"], "qld_recreational_boating_facilities")
        self.assertEqual(facilities[0]["label"], "Hollywell, Jasmine Avenue")
        self.assertFalse(facilities[0]["planner_eligible"])

    def test_qld_fetch_paginates_official_api_limit(self) -> None:
        calls = []

        class FakeResponse:
            def __init__(self, payload):
                self.payload = payload

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return json.dumps(self.payload).encode("utf-8")

        def fake_urlopen(request, timeout=None):
            query = parse_qs(urlparse(request.full_url).query)
            offset = int(query.get("offset", ["0"])[0])
            calls.append(offset)
            records = [
                {
                    "name": "Ramp one",
                    "facility": "Boat Ramp",
                    "tmr_id": "one",
                    "latitude": -27.896,
                    "longitude": 153.403,
                },
                {
                    "name": "Ramp two",
                    "facility": "Boat Ramp",
                    "tmr_id": "two",
                    "latitude": -27.897,
                    "longitude": 153.404,
                },
            ]
            return FakeResponse({"total_count": len(records), "results": records[offset : offset + 1]})

        import coastal_fishing_forecast.structures as structures

        original_urlopen = structures.urlopen
        try:
            structures.urlopen = fake_urlopen
            result = fetch_qld_boating_facilities(-27.896, 153.403, radius_m=5000, cache_enabled=False)
        finally:
            structures.urlopen = original_urlopen

        self.assertEqual(calls, [0, 1])
        self.assertEqual([item["label"] for item in result["facilities"]], ["Ramp one", "Ramp two"])

    def test_vic_boating_facility_skips_closed_or_hidden_ramps(self) -> None:
        payload = [
            {
                "facilityId": "open-1",
                "name": "Anderson Inlet - Inverloch Ramp",
                "status": "Open",
                "pagestatus": "Show",
                "isDeleted": False,
                "latitude": -38.635665,
                "longitude": 145.733884,
            },
            {
                "facilityId": "closed-1",
                "name": "Closed Ramp",
                "status": "Closed",
                "pagestatus": "Show",
                "isDeleted": False,
                "latitude": -38.635,
                "longitude": 145.734,
            },
        ]

        facilities = normalize_vic_boating_facilities(payload, lat=-38.635, lon=145.734, radius_m=2000)

        self.assertEqual(len(facilities), 1)
        self.assertEqual(facilities[0]["source"], "vic_boating_facilities")
        self.assertEqual(facilities[0]["label"], "Anderson Inlet - Inverloch Ramp")
        self.assertEqual(facilities[0]["role"], "public_access_only")

    def test_wa_official_boat_ramp_is_map_only(self) -> None:
        payload = {
            "features": [
                {
                    "attributes": {
                        "objectid": 30,
                        "assetdesc": "Sealed Ramp",
                        "name_of_boat_ramp": "Ocean Reef boat ramp",
                    },
                    "geometry": {"x": 115.7282859, "y": -31.7614291},
                }
            ]
        }

        facilities = normalize_wa_public_boat_ramps(payload, lat=-31.7614, lon=115.7283, source_layer="sealed")

        self.assertEqual(facilities[0]["source"], "wa_public_boat_ramps")
        self.assertEqual(facilities[0]["label"], "Ocean Reef boat ramp")
        self.assertFalse(facilities[0]["planner_eligible"])
        self.assertTrue(facilities[0]["map_eligible"])

    def test_sa_official_boat_ramp_is_map_only_and_skips_closed(self) -> None:
        payload = {
            "features": [
                {
                    "attributes": {"OBJECTID": 1, "BOATRAMP": "Meningie", "COMMENTS": "2 ramps, open to public"},
                    "geometry": {"x": 139.3415665, "y": -35.6800331},
                },
                {
                    "attributes": {"OBJECTID": 2, "BOATRAMP": "Closed ramp", "COMMENTS": "closed"},
                    "geometry": {"x": 139.34, "y": -35.68},
                },
            ]
        }

        facilities = normalize_sa_boat_ramp_facilities(payload, lat=-35.68, lon=139.34)

        self.assertEqual(len(facilities), 1)
        self.assertEqual(facilities[0]["source"], "sa_boat_ramps")
        self.assertEqual(facilities[0]["label"], "Meningie")
        self.assertEqual(facilities[0]["role"], "public_access_only")

    def test_nt_public_boat_ramp_kml_is_map_only(self) -> None:
        payload = """<?xml version="1.0" encoding="UTF-8"?>
        <kml xmlns="http://www.opengis.net/kml/2.2">
          <Document>
            <Placemark>
              <name>Buffalo Creek ramp</name>
              <ExtendedData>
                <Data name="Status / Warning"><value>No access through creek mouth below 4m.</value></Data>
              </ExtendedData>
              <Point><coordinates>130.908237,-12.337675,0</coordinates></Point>
            </Placemark>
          </Document>
        </kml>"""

        facilities = normalize_nt_public_boat_ramps(payload, lat=-12.3377, lon=130.9082, radius_m=2000)

        self.assertEqual(facilities[0]["source"], "nt_public_boat_ramps")
        self.assertEqual(facilities[0]["label"], "Buffalo Creek ramp")
        self.assertFalse(facilities[0]["planner_eligible"])
        self.assertTrue(facilities[0]["map_eligible"])

    def test_official_fishing_spots_are_normalized_for_map_layer(self) -> None:
        rows = [
            {
                "id": "tas_hot_fishing_spots:001:test_jetty",
                "jurisdiction": "TAS",
                "guide_name": "Fishing Tasmania Hot Fishing Spots",
                "spot_name": "Test Jetty",
                "spot_type": "jetty",
                "source_kind": "official_hot_fishing_spots_page",
                "official_owner": "Fishing Tasmania",
                "latitude": -42.899,
                "longitude": 147.339,
                "planner_eligible": True,
                "map_eligible": True,
                "role": "public_fishing_access_candidate",
                "score_impact": "none",
            },
            {
                "id": "qld_official_fad:001:test_fad",
                "jurisdiction": "QLD",
                "guide_name": "Find a fish aggregating device",
                "spot_name": "Test FAD",
                "spot_type": "fad",
                "scope": "offshore_boat",
                "latitude": -42.9,
                "longitude": 147.34,
                "planner_eligible": False,
                "map_eligible": True,
                "role": "offshore_boat_fishing_reference",
                "score_impact": "none",
            },
        ]

        facilities = normalize_official_fishing_spots(rows, lat=-42.8991036, lon=147.3389916, radius_m=5000)

        self.assertEqual(len(facilities), 2)
        self.assertEqual(facilities[0]["source"], "official_fishing_spots")
        self.assertEqual(facilities[0]["type"], "public_jetty")
        self.assertEqual(facilities[0]["access"], "public")
        self.assertTrue(facilities[0]["planner_eligible"])
        self.assertEqual(facilities[0]["attributes"]["score_impact"], "none")
        self.assertEqual(facilities[1]["type"], "fad")
        self.assertEqual(facilities[1]["access"], "open_water")
        self.assertFalse(facilities[1]["planner_eligible"])
        self.assertTrue(facilities[1]["map_eligible"])

    def test_combined_fetch_includes_official_spots_first(self) -> None:
        calls = []

        def fake_official(*args, **kwargs):
            calls.append("official")
            return {"facilities": [{"id": "official_fishing_spots:1", "planner_eligible": True, "distance_km": 0.2, "label": "Official spot"}]}

        def fake_wild(*args, **kwargs):
            calls.append("wild")
            return {"facilities": [{"id": "list_wildfisheries:33", "planner_eligible": True, "distance_km": 0.7, "label": "Official"}]}

        def fake_mast(*args, **kwargs):
            calls.append("mast")
            return {"facilities": [{"id": "list_mast:1", "planner_eligible": False, "distance_km": 0.5, "label": "Ramp"}]}

        def fake_osm(*args, **kwargs):
            calls.append("osm")
            return {"facilities": []}

        import coastal_fishing_forecast.structures as structures

        original_official = structures.fetch_official_fishing_spot_facilities
        original_wild = structures.fetch_list_wildfisheries_sea_spots
        original_mast = structures.fetch_list_mast_structure_facilities
        original_osm = structures.fetch_osm_structure_facilities
        try:
            structures.fetch_official_fishing_spot_facilities = fake_official
            structures.fetch_list_wildfisheries_sea_spots = fake_wild
            structures.fetch_list_mast_structure_facilities = fake_mast
            structures.fetch_osm_structure_facilities = fake_osm
            result = fetch_combined_structure_facilities(-42.8991036, 147.3389916, cache_enabled=False)
        finally:
            structures.fetch_official_fishing_spot_facilities = original_official
            structures.fetch_list_wildfisheries_sea_spots = original_wild
            structures.fetch_list_mast_structure_facilities = original_mast
            structures.fetch_osm_structure_facilities = original_osm

        self.assertCountEqual(calls, ["official", "wild", "mast", "osm"])
        self.assertEqual(result["sources"][0]["source"], "official_fishing_spots")
        self.assertEqual([source["source"] for source in result["sources"]], ["official_fishing_spots", "list_wildfisheries", "list_mast", "osm_overpass"])
        self.assertEqual(result["facilities"][0]["id"], "official_fishing_spots:1")

    def test_combined_fetch_dedupes_nearby_public_fishing_access(self) -> None:
        def fake_wild(*args, **kwargs):
            return {
                "facilities": [
                    {
                        "id": "list_wildfisheries:33",
                        "type": "public_jetty",
                        "label": "Purdon and Featherston Reserve, Battery Point",
                        "access": "public",
                        "source": "list_wildfisheries",
                        "coordinates": {"latitude": -42.89205, "longitude": 147.33752},
                        "planner_eligible": True,
                        "map_eligible": True,
                        "distance_km": 0.793,
                    }
                ]
            }

        def fake_mast(*args, **kwargs):
            return {"facilities": []}

        def fake_osm(*args, **kwargs):
            return {
                "facilities": [
                    {
                        "id": "osm:way:208921096",
                        "type": "public_jetty",
                        "label": "Battery Point Public Jetty",
                        "access": "public",
                        "source": "osm_overpass",
                        "coordinates": {"latitude": -42.8922322, "longitude": 147.3378037},
                        "planner_eligible": True,
                        "map_eligible": True,
                        "distance_km": 0.77,
                    }
                ]
            }

        import coastal_fishing_forecast.structures as structures

        original_official = structures.fetch_official_fishing_spot_facilities
        original_wild = structures.fetch_list_wildfisheries_sea_spots
        original_mast = structures.fetch_list_mast_structure_facilities
        original_osm = structures.fetch_osm_structure_facilities
        try:
            structures.fetch_official_fishing_spot_facilities = lambda *args, **kwargs: {"facilities": []}
            structures.fetch_list_wildfisheries_sea_spots = fake_wild
            structures.fetch_list_mast_structure_facilities = fake_mast
            structures.fetch_osm_structure_facilities = fake_osm
            result = fetch_combined_structure_facilities(-42.8991036, 147.3389916, cache_enabled=False)
        finally:
            structures.fetch_official_fishing_spot_facilities = original_official
            structures.fetch_list_wildfisheries_sea_spots = original_wild
            structures.fetch_list_mast_structure_facilities = original_mast
            structures.fetch_osm_structure_facilities = original_osm

        self.assertEqual([item["id"] for item in result["facilities"]], ["list_wildfisheries:33"])

    def test_combined_fetch_uses_nsw_official_source_outside_tasmania(self) -> None:
        calls = []

        def fake_nsw(*args, **kwargs):
            calls.append("nsw")
            return {"facilities": [{"id": "nsw:1", "type": "boat_ramp", "access": "public", "map_eligible": True, "planner_eligible": False, "coordinates": {"latitude": -33.8, "longitude": 151.2}, "distance_km": 0.1, "label": "NSW Ramp"}]}

        def fake_osm(*args, **kwargs):
            calls.append("osm")
            return {"facilities": []}

        import coastal_fishing_forecast.structures as structures

        original_official = structures.fetch_official_fishing_spot_facilities
        original_nsw = structures.fetch_nsw_boat_ramp_facilities
        original_osm = structures.fetch_osm_structure_facilities
        try:
            structures.fetch_official_fishing_spot_facilities = lambda *args, **kwargs: {"facilities": []}
            structures.fetch_nsw_boat_ramp_facilities = fake_nsw
            structures.fetch_osm_structure_facilities = fake_osm
            result = fetch_combined_structure_facilities(-33.8, 151.2, cache_enabled=False)
        finally:
            structures.fetch_official_fishing_spot_facilities = original_official
            structures.fetch_nsw_boat_ramp_facilities = original_nsw
            structures.fetch_osm_structure_facilities = original_osm

        self.assertCountEqual(calls, ["nsw", "osm"])
        self.assertEqual(result["query"]["jurisdiction"], "nsw")
        self.assertEqual([source["source"] for source in result["sources"]], ["official_fishing_spots", "nsw_maritime_boat_ramps", "osm_overpass"])


if __name__ == "__main__":
    unittest.main()
