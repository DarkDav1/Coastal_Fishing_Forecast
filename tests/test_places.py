import tempfile
import unittest
from unittest.mock import patch

from coastal_fishing_forecast.places import normalize_mapbox_response, normalize_nominatim_response, search_places


MAPBOX_FIXTURE = {
    "features": [
        {
            "id": "place.123",
            "text": "Bay of Fires",
            "place_name": "Bay of Fires, Tasmania, Australia",
            "place_type": ["place"],
            "relevance": 0.91,
            "center": [148.306, -41.253],
            "bbox": [148.0, -41.5, 148.6, -41.0],
            "context": [
                {"id": "region.1", "text": "Tasmania"},
                {"id": "country.1", "text": "Australia"},
            ],
        }
    ]
}

NOMINATIM_FIXTURE = [
    {
        "osm_type": "relation",
        "osm_id": 456,
        "name": "St Helens",
        "display_name": "St Helens, Break O'Day Council, Tasmania, Australia",
        "lat": "-41.3206",
        "lon": "148.2497",
        "class": "place",
        "type": "town",
        "boundingbox": ["-41.35", "-41.29", "148.22", "148.28"],
        "address": {
            "state": "Tasmania",
            "country": "Australia",
        },
    }
]


class PlaceSearchTests(unittest.TestCase):
    def test_mapbox_response_normalizes_to_candidate_coordinates(self) -> None:
        result = normalize_mapbox_response("Bay of Fires", MAPBOX_FIXTURE)

        self.assertEqual(result["provider"], "mapbox")
        self.assertEqual(result["query"], "Bay of Fires")
        self.assertEqual(result["results"][0]["display_name"], "Bay of Fires, Tasmania, Australia")
        self.assertEqual(result["results"][0]["short_name"], "Bay of Fires")
        self.assertEqual(result["results"][0]["latitude"], -41.253)
        self.assertEqual(result["results"][0]["longitude"], 148.306)
        self.assertEqual(result["results"][0]["region"], "Tasmania")

    def test_missing_mapbox_token_fails_clearly(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(ValueError, "Missing Mapbox access token"):
                search_places("Bay of Fires")

    def test_nominatim_response_normalizes_to_candidate_coordinates(self) -> None:
        result = normalize_nominatim_response("St Helens Tasmania", NOMINATIM_FIXTURE)

        self.assertEqual(result["provider"], "nominatim")
        self.assertEqual(result["results"][0]["display_name"], "St Helens, Break O'Day Council, Tasmania, Australia")
        self.assertEqual(result["results"][0]["short_name"], "St Helens")
        self.assertEqual(result["results"][0]["latitude"], -41.3206)
        self.assertEqual(result["results"][0]["longitude"], 148.2497)
        self.assertEqual(result["results"][0]["region"], "Tasmania")
        self.assertIn("place", result["results"][0]["types"])

    def test_place_search_uses_cache(self) -> None:
        with tempfile.TemporaryDirectory() as cache_dir:
            with patch(
                "coastal_fishing_forecast.places._load_json",
                return_value=MAPBOX_FIXTURE,
            ) as load_json:
                first = search_places(
                    "Bay of Fires",
                    access_token="test-token",
                    cache_dir=cache_dir,
                )
                second = search_places(
                    "Bay of Fires",
                    access_token="test-token",
                    cache_dir=cache_dir,
                )

        self.assertEqual(first, second)
        self.assertEqual(load_json.call_count, 1)

    def test_nominatim_search_uses_cache_without_key(self) -> None:
        with tempfile.TemporaryDirectory() as cache_dir:
            with patch(
                "coastal_fishing_forecast.places._load_json",
                return_value=NOMINATIM_FIXTURE,
            ) as load_json:
                first = search_places(
                    "St Helens Tasmania",
                    provider="nominatim",
                    cache_dir=cache_dir,
                )
                second = search_places(
                    "St Helens Tasmania",
                    provider="nominatim",
                    cache_dir=cache_dir,
                )

        self.assertEqual(first, second)
        self.assertEqual(load_json.call_count, 1)


if __name__ == "__main__":
    unittest.main()
