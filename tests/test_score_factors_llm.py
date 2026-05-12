"""Tests for score-factors LLM payload aggregation."""

import unittest

from coastal_fishing_forecast.score_factors_llm import aggregate_windows_stats, build_score_factors_payload


def _sample_window(**kwargs):
    base = {
        "time_window": "morning",
        "conditions": {
            "wind": {"speed_knots": 10.0, "gust_knots": 18.0},
            "swell": {"height_m": 1.2, "wave_height_m": 1.0},
            "air": {"temperature_c": 12.0, "rain_mm": 0.5},
            "pressure_hpa": 1013.0,
            "weather_trend": {"shock_score": 1.5, "change_notes": ["Cooling trend"]},
            "tide": {"phase": "rising", "movement_rate_m_per_hour": 0.12, "range_m": 0.8},
        },
    }
    base.update(kwargs)
    return base


class AggregateWindowsStatsTests(unittest.TestCase):
    def test_empty_windows(self) -> None:
        stats = aggregate_windows_stats([])
        self.assertEqual(stats["tide_movement_rate_abs_max_m_per_h"], 0)
        self.assertEqual(stats["weather_shock_max"], 0)

    def test_aggregates_reasonable(self) -> None:
        windows = [_sample_window(), _sample_window()]
        stats = aggregate_windows_stats(windows)
        self.assertEqual(stats["wind_speed_avg_knots"], 10.0)
        self.assertGreaterEqual(stats["wind_gust_max_knots"], 18.0)
        self.assertGreater(stats["tide_movement_rate_abs_max_m_per_h"], 0)
        self.assertIn("rising", stats["tide_phases_observed"])

    def test_build_payload_includes_notes(self) -> None:
        payload = build_score_factors_payload(
            lang="en",
            date_iso="2026-05-12",
            windows=[_sample_window()],
        )
        self.assertEqual(payload["lang"], "en")
        self.assertEqual(payload["date"], "2026-05-12")
        self.assertIn("aggregates", payload)
        self.assertEqual(payload["weather_change_notes"], ["Cooling trend"])


if __name__ == "__main__":
    unittest.main()
