import unittest

from coastal_fishing_forecast.structures import (
    fetch_combined_structure_facilities,
    normalize_list_mast_facilities,
    normalize_list_wildfisheries_sea_spots,
    normalize_osm_structure_facilities,
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

    def test_combined_fetch_includes_wildfisheries_first(self) -> None:
        calls = []

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

        original_wild = structures.fetch_list_wildfisheries_sea_spots
        original_mast = structures.fetch_list_mast_structure_facilities
        original_osm = structures.fetch_osm_structure_facilities
        try:
            structures.fetch_list_wildfisheries_sea_spots = fake_wild
            structures.fetch_list_mast_structure_facilities = fake_mast
            structures.fetch_osm_structure_facilities = fake_osm
            result = fetch_combined_structure_facilities(-42.8991036, 147.3389916, cache_enabled=False)
        finally:
            structures.fetch_list_wildfisheries_sea_spots = original_wild
            structures.fetch_list_mast_structure_facilities = original_mast
            structures.fetch_osm_structure_facilities = original_osm

        self.assertCountEqual(calls, ["wild", "mast", "osm"])
        self.assertEqual(result["sources"][0]["source"], "list_wildfisheries")
        self.assertEqual([source["source"] for source in result["sources"]], ["list_wildfisheries", "list_mast", "osm_overpass"])
        self.assertEqual(result["facilities"][0]["id"], "list_wildfisheries:33")

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
                        "distance_km": 0.77,
                    }
                ]
            }

        import coastal_fishing_forecast.structures as structures

        original_wild = structures.fetch_list_wildfisheries_sea_spots
        original_mast = structures.fetch_list_mast_structure_facilities
        original_osm = structures.fetch_osm_structure_facilities
        try:
            structures.fetch_list_wildfisheries_sea_spots = fake_wild
            structures.fetch_list_mast_structure_facilities = fake_mast
            structures.fetch_osm_structure_facilities = fake_osm
            result = fetch_combined_structure_facilities(-42.8991036, 147.3389916, cache_enabled=False)
        finally:
            structures.fetch_list_wildfisheries_sea_spots = original_wild
            structures.fetch_list_mast_structure_facilities = original_mast
            structures.fetch_osm_structure_facilities = original_osm

        self.assertEqual([item["id"] for item in result["facilities"]], ["list_wildfisheries:33"])


if __name__ == "__main__":
    unittest.main()
