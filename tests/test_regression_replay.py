import unittest
from datetime import date
from unittest.mock import patch

from coastal_fishing_forecast.regression_replay import DEFAULT_REPLAY_CASES, run_regression_replay


def _forecast_response(query: str, dominant_type: str = "bay_estuary_edge") -> dict:
    return {
        "status": "ok",
        "selected_place": {
            "id": f"fixture:{query}",
            "display_name": query,
            "latitude": -41.25,
            "longitude": 148.30,
            "types": ["beach"],
            "selection_score": 150.0,
            "forecast_support": {
                "supported": True,
                "reason_code": "coastal_or_tidal_preview",
                "nearest_supported_water_km": 0.5,
                "message": "Supported fixture.",
            },
        },
        "forecast": {
            "summary": {
                "best_windows": [
                    {
                        "dominant_inferred_type": dominant_type,
                        "score": 62,
                    }
                ],
            },
            "tide_verification": {"status": "estimated"},
            "confidence": {"score": 58, "label": "medium"},
        },
    }


class RegressionReplayTests(unittest.TestCase):
    def test_replay_uses_cached_approximation_path_and_summarizes_passes(self) -> None:
        calls = []

        def fake_search_forecast(query: str, **kwargs) -> dict:
            calls.append((query, kwargs))
            if query.startswith(("Alice Springs", "Lake Eildon", "Dubbo")):
                return {
                    "status": "unsupported_or_no_result",
                    "selected_place": None,
                    "forecast": None,
                }
            dominant = "beach" if "Binalong" in query else "bay_estuary_edge"
            return _forecast_response(query, dominant)

        with patch(
            "coastal_fishing_forecast.regression_replay.build_search_forecast_response",
            side_effect=fake_search_forecast,
        ):
            result = run_regression_replay(
                start_date=date(2026, 4, 20),
                end_date=date(2026, 4, 20),
                cache_enabled=True,
            )

        self.assertEqual(result["summary"]["total"], len(DEFAULT_REPLAY_CASES))
        self.assertEqual(result["summary"]["failed"], 0)
        self.assertEqual(result["input"]["tide_source"], "approximation")
        self.assertIn("by_category", result["summary"])
        self.assertEqual(result["results"][0]["forecast_summary"]["tide_status"], "estimated")
        self.assertEqual(result["results"][0]["selected_place"]["support"]["supported"], True)
        self.assertTrue(calls)
        for _, kwargs in calls:
            self.assertEqual(kwargs["tide_source"], "approximation")
            self.assertEqual(kwargs["condition_source"], "archive")
            self.assertTrue(kwargs["cache_enabled"])

    def test_replay_marks_unexpected_unsupported_forecast_as_failed(self) -> None:
        with patch(
            "coastal_fishing_forecast.regression_replay.build_search_forecast_response",
            return_value={
                "status": "unsupported_or_no_result",
                "selected_place": None,
                "forecast": None,
            },
        ):
            result = run_regression_replay(
                start_date=date(2026, 4, 20),
                end_date=date(2026, 4, 20),
                cache_enabled=False,
            )

        expected_rejects = sum(1 for case in DEFAULT_REPLAY_CASES if case.expected_status == "unsupported_or_no_result")
        self.assertEqual(result["summary"]["passed"], expected_rejects)
        self.assertEqual(result["summary"]["failed"], len(DEFAULT_REPLAY_CASES) - expected_rejects)
        self.assertEqual(result["results"][0]["forecast_summary"], None)
        self.assertTrue(result["results"][0]["failure_reasons"])


if __name__ == "__main__":
    unittest.main()
