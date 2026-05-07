import unittest
from unittest.mock import patch

from coastal_fishing_forecast.search_forecast import build_search_forecast_response
from test_forecast import _fixture_conditions


PLACE_SEARCH_FIXTURE = {
    "query": "Binalong Bay Tasmania",
    "provider": "nominatim",
    "results": [
        {
            "id": "nominatim:relation:1",
            "display_name": "Binalong Bay, Tasmania, Australia",
            "short_name": "Binalong Bay",
            "latitude": -41.24899,
            "longitude": 148.31215,
            "country": "Australia",
            "region": "Tasmania",
            "source": "nominatim",
            "confidence": None,
            "types": ["boundary", "administrative"],
            "bbox": None,
        },
        {
            "id": "nominatim:way:2",
            "display_name": "Binalong Bay beach, Tasmania, Australia",
            "short_name": "Binalong Bay",
            "latitude": -41.252011,
            "longitude": 148.304772,
            "country": "Australia",
            "region": "Tasmania",
            "source": "nominatim",
            "confidence": None,
            "types": ["natural", "beach"],
            "bbox": None,
        },
    ],
}


class SearchForecastTests(unittest.TestCase):
    def test_search_forecast_selects_supported_coastal_candidate(self) -> None:
        with patch("coastal_fishing_forecast.search_forecast.search_places", return_value=PLACE_SEARCH_FIXTURE):
            with patch("coastal_fishing_forecast.forecast.fetch_open_meteo_conditions", return_value=_fixture_conditions()):
                response = build_search_forecast_response(
                    "Binalong Bay Tasmania",
                    start_date="2026-04-20",
                    end_date="2026-04-20",
                    provider="nominatim",
                    region="open_coast",
                    windows=("morning",),
                    condition_source="archive",
                    tide_source="approximation",
                    cache_enabled=False,
                )

        self.assertEqual(response["contract_version"], "2026-04-28.search_forecast.v1")
        self.assertEqual(response["status"], "ok")
        self.assertEqual(response["selected_place"]["id"], "nominatim:way:2")
        self.assertGreater(
            response["selected_place"]["selection_score"],
            response["candidates"][1]["selection_score"],
        )
        self.assertTrue(response["selected_place"]["forecast_support"]["supported"])
        self.assertIsNotNone(response["forecast"])
        self.assertIsNotNone(response["plan"])
        self.assertEqual(response["plan"], response["forecast"]["plan"])
        self.assertEqual(response["forecast"]["api_contract_version"], "2026-04-27.frontend.v1")

    def test_search_forecast_returns_clear_status_when_no_results(self) -> None:
        with patch(
            "coastal_fishing_forecast.search_forecast.search_places",
            return_value={"query": "No place", "provider": "nominatim", "results": []},
        ):
            response = build_search_forecast_response(
                "No place",
                start_date="2026-04-20",
                end_date="2026-04-20",
                provider="nominatim",
                cache_enabled=False,
            )

        self.assertEqual(response["status"], "unsupported_or_no_result")
        self.assertIsNone(response["selected_place"])
        self.assertIsNone(response["forecast"])
        self.assertEqual(response["plan"]["recommendation"]["label"], "skip")
        self.assertIn("supported coastal or tidal", response["plan"]["primary_action"]["text"])


if __name__ == "__main__":
    unittest.main()
