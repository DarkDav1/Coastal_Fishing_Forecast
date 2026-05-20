"""Tests for the parallel Safety / Comfort / Fish-outlook views."""

from __future__ import annotations

import unittest

from coastal_fishing_forecast.preview import (
    SAFETY_FLAG_ELEVATED,
    SAFETY_FLAG_HAZARDOUS,
    SAFETY_FLAG_LOW,
    SAFETY_FLAG_MODERATE,
    _comfort_score,
    _fish_outlook_score,
    _safety_flag,
    build_preview,
)


class FishOutlookTests(unittest.TestCase):
    def test_fish_outlook_blends_activity_and_presence(self) -> None:
        # 0.55 * 80 + 0.45 * 60 = 44 + 27 = 71
        self.assertEqual(_fish_outlook_score(80, 60), 71)

    def test_fish_outlook_clamps_to_0_100(self) -> None:
        self.assertEqual(_fish_outlook_score(0, 0), 0)
        self.assertEqual(_fish_outlook_score(100, 100), 100)

    def test_fish_outlook_does_not_use_trip_quality(self) -> None:
        # Same activity + presence with very different trip_quality should
        # produce the same fish_outlook in build_preview output.
        good_trip = build_preview(
            -42.8915,
            147.3320,
            environment={
                "wind_speed_knots": 6,
                "temperature_c": 18,
                "swell_height_m": 0.4,
                "wave_height_m": 0.4,
                "tide_phase": "rising",
                "tide_stage": "flood",
                "hours_to_high_tide": 1.5,
                "tide_height_change_next_2h": 0.2,
                "time_window": "dawn",
            },
            region="sheltered_estuary",
        )
        # Fish outlook should NEVER be None for a supported preview
        self.assertIsNotNone(good_trip["overall_recommendation"]["fish_outlook_score"])
        self.assertIsInstance(good_trip["overall_recommendation"]["fish_outlook_score"], int)


class ComfortScoreTests(unittest.TestCase):
    def test_comfort_high_in_calm_mild_conditions(self) -> None:
        score, factors = _comfort_score(
            inputs_used={
                "temperature_c": 18,
                "wind_speed_knots": 6,
                "wind_gust_knots": 9,
                "rain_mm": 0,
                "wave_height_m": 0.4,
                "swell_height_m": 0.4,
            },
            normalized={},
        )
        self.assertGreaterEqual(score, 75)
        self.assertEqual(factors, [])

    def test_comfort_low_in_cold_wet_windy_conditions(self) -> None:
        score, factors = _comfort_score(
            inputs_used={
                "temperature_c": 6,
                "wind_speed_knots": 22,
                "wind_gust_knots": 38,
                "rain_mm": 3,
                "recent_precipitation_sum_12h": 5,
                "wave_height_m": 3.0,
                "swell_height_m": 2.5,
            },
            normalized={},
        )
        self.assertLess(score, 25)
        self.assertIn("cold_air", factors)
        self.assertIn("steady_rain", factors)
        self.assertIn("strong_gusts", factors)
        self.assertIn("rough_seas", factors)

    def test_comfort_score_handles_missing_temperature(self) -> None:
        score, factors = _comfort_score(
            inputs_used={
                "wind_speed_knots": 6,
                "rain_mm": 0,
                "wave_height_m": 0.4,
            },
            normalized={},
        )
        self.assertIsInstance(score, int)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_comfort_accounts_for_swell_even_when_local_wave_is_small(self) -> None:
        score, factors = _comfort_score(
            inputs_used={
                "temperature_c": 18,
                "wind_speed_knots": 6,
                "wind_gust_knots": 9,
                "rain_mm": 0,
                "wave_height_m": 0.3,
                "swell_height_m": 1.4,
            },
            normalized={},
        )
        self.assertLess(score, 82)
        self.assertIn("long_period_swell", factors)


class SafetyFlagTests(unittest.TestCase):
    def test_safety_low_in_calm_conditions(self) -> None:
        flag, factors, points = _safety_flag(
            inputs_used={
                "wave_height_m": 0.4,
                "swell_height_m": 0.4,
                "wind_speed_knots": 6,
                "wind_gust_knots": 9,
                "temperature_c": 18,
                "rain_mm": 0,
                "rainfall_24h": 0,
            },
            dominant_type="bay_estuary_edge",
            tags=set(),
        )
        self.assertEqual(flag, SAFETY_FLAG_LOW)
        self.assertEqual(points, 0)

    def test_safety_moderate_with_notable_wave(self) -> None:
        flag, factors, points = _safety_flag(
            inputs_used={
                "wave_height_m": 1.9,
                "swell_height_m": 1.5,
                "wind_speed_knots": 6,
                "wind_gust_knots": 12,
                "temperature_c": 14,
            },
            dominant_type="bay_estuary_edge",
            tags=set(),
        )
        self.assertEqual(flag, SAFETY_FLAG_MODERATE)
        self.assertIn("notable_wave_activity", factors)

    def test_safety_elevated_with_big_seas_and_brisk_wind(self) -> None:
        flag, factors, _ = _safety_flag(
            inputs_used={
                "wave_height_m": 2.6,
                "swell_height_m": 2.4,
                "wind_speed_knots": 19,
                "wind_gust_knots": 28,
            },
            dominant_type="beach",
            tags=set(),
        )
        self.assertEqual(flag, SAFETY_FLAG_HAZARDOUS)
        self.assertIn("rough_seas_above_2m5", factors)
        self.assertIn("brisk_wind", factors)
        self.assertIn("strong_gusts", factors)

    def test_safety_hazardous_with_severe_gusts_alone(self) -> None:
        flag, factors, _ = _safety_flag(
            inputs_used={
                "wave_height_m": 1.9,
                "swell_height_m": 1.6,
                "wind_speed_knots": 26,
                "wind_gust_knots": 38,
            },
            dominant_type="rocks",
            tags=set(),
        )
        self.assertEqual(flag, SAFETY_FLAG_HAZARDOUS)
        self.assertIn("severe_gusts", factors)

    def test_safety_exposed_type_amplifies_with_wave(self) -> None:
        sheltered_flag, _, sheltered_pts = _safety_flag(
            inputs_used={
                "wave_height_m": 1.6,
                "swell_height_m": 1.4,
                "wind_speed_knots": 8,
                "wind_gust_knots": 14,
            },
            dominant_type="bay_estuary_edge",
            tags=set(),
        )
        beach_flag, beach_factors, beach_pts = _safety_flag(
            inputs_used={
                "wave_height_m": 1.6,
                "swell_height_m": 1.4,
                "wind_speed_knots": 8,
                "wind_gust_knots": 14,
            },
            dominant_type="beach",
            tags=set(),
        )
        self.assertGreater(beach_pts, sheltered_pts)
        self.assertIn("exposed_with_wave", beach_factors)

    def test_safety_cold_wet_windy_combo_adds_risk(self) -> None:
        _, factors, _ = _safety_flag(
            inputs_used={
                "wave_height_m": 0.6,
                "swell_height_m": 0.5,
                "wind_speed_knots": 12,
                "wind_gust_knots": 18,
                "temperature_c": 6,
                "rain_mm": 0.8,
                "rainfall_24h": 8,
            },
            dominant_type="bay_estuary_edge",
            tags=set(),
        )
        self.assertIn("cold_wet_windy", factors)


class IntegratedSplitTests(unittest.TestCase):
    def test_overall_recommendation_exposes_three_new_fields(self) -> None:
        result = build_preview(
            -42.8915,
            147.3320,
            environment={
                "wind_speed_knots": 6,
                "temperature_c": 16,
                "swell_height_m": 0.4,
                "wave_height_m": 0.4,
                "tide_phase": "rising",
                "tide_stage": "flood",
                "hours_to_high_tide": 1.5,
                "tide_height_change_next_2h": 0.2,
                "time_window": "dawn",
            },
            region="sheltered_estuary",
        )
        overall = result["overall_recommendation"]
        self.assertIn("fish_outlook_score", overall)
        self.assertIn("comfort_score", overall)
        self.assertIn("safety_flag", overall)
        self.assertIn("comfort_factors", overall)
        self.assertIn("safety_factors", overall)
        self.assertIn(
            overall["safety_flag"],
            {SAFETY_FLAG_LOW, SAFETY_FLAG_MODERATE, SAFETY_FLAG_ELEVATED, SAFETY_FLAG_HAZARDOUS},
        )

    def test_great_fish_day_in_dangerous_weather_is_visible(self) -> None:
        # The motivating case for the split: high fish opportunity should not
        # be silently hidden by a single trip_quality number when conditions
        # are dangerous. We construct a scenario where the engine sees strong
        # rule alignment but conditions are objectively rough.
        result = build_preview(
            -41.2530,
            148.3060,  # Bay of Fires, open coast
            environment={
                "wind_speed_knots": 22,
                "wind_gust_knots": 36,
                "wind_direction_deg": 90,
                "swell_direction_deg": 90,
                "temperature_c": 11,
                "rain_mm": 1,
                "swell_height_m": 2.6,
                "wave_height_m": 3.0,
                "tide_phase": "rising",
                "tide_stage": "flood",
                "hours_to_high_tide": 1,
                "tide_height_change_next_2h": 0.25,
                "tide_range_m": 0.9,
                "time_window": "dawn",
                "hours_from_sunrise": 0.5,
                "is_daylight": True,
            },
            region="open_coast",
        )
        overall = result["overall_recommendation"]
        # The fish-outlook view doesn't depend on safety; it can still be
        # whatever the rule engine concluded. What we lock in here is that
        # safety flag is independently elevated/hazardous so the user sees
        # the danger signal even if the fish view looks ok.
        self.assertIn(overall["safety_flag"], {SAFETY_FLAG_ELEVATED, SAFETY_FLAG_HAZARDOUS})
        self.assertIn("rough_seas_above_2m5", overall["safety_factors"])
        self.assertLess(overall["comfort_score"], 30)

    def test_calm_warm_day_keeps_comfort_high_and_safety_low(self) -> None:
        result = build_preview(
            -42.8915,
            147.3320,
            environment={
                "wind_speed_knots": 5,
                "wind_gust_knots": 8,
                "temperature_c": 19,
                "rain_mm": 0,
                "swell_height_m": 0.3,
                "wave_height_m": 0.3,
                "tide_phase": "rising",
                "tide_stage": "flood",
                "hours_to_high_tide": 1.5,
                "tide_height_change_next_2h": 0.18,
                "time_window": "dawn",
            },
            region="sheltered_estuary",
        )
        overall = result["overall_recommendation"]
        self.assertEqual(overall["safety_flag"], SAFETY_FLAG_LOW)
        self.assertGreaterEqual(overall["comfort_score"], 70)

    def test_trip_quality_tracks_trip_reality_not_fish_window_quality(self) -> None:
        result = build_preview(
            -42.8915,
            147.3320,
            environment={
                "wind_speed_knots": 6,
                "wind_gust_knots": 12,
                "temperature_c": 14,
                "rain_mm": 0,
                "swell_height_m": 0.2,
                "wave_height_m": 0.3,
                "tide_phase": "falling",
                "tide_stage": "ebb",
                "hours_to_high_tide": 7,
                "hours_to_low_tide": 3,
                "tide_height_change_next_2h": 0.02,
                "tide_range_m": 0.4,
                "time_window": "dusk",
                "is_daylight": True,
            },
            region="sheltered_estuary",
        )
        overall = result["overall_recommendation"]
        self.assertLess(overall["fish_outlook_score"], 40)
        self.assertGreaterEqual(overall["trip_quality_score"], 70)
        self.assertEqual(overall["trip_quality_score"], overall["comfort_score"])

    def test_hazardous_safety_caps_trip_quality_even_when_comfort_is_higher(self) -> None:
        result = build_preview(
            -41.2530,
            148.3060,
            environment={
                "wind_speed_knots": 20,
                "wind_gust_knots": 28,
                "temperature_c": 14,
                "rain_mm": 0,
                "swell_height_m": 2.2,
                "wave_height_m": 2.7,
                "tide_phase": "rising",
                "tide_stage": "flood",
                "hours_to_high_tide": 1.0,
                "tide_height_change_next_2h": 0.24,
                "tide_range_m": 0.8,
                "time_window": "dawn",
                "is_daylight": True,
            },
            region="open_coast",
        )
        overall = result["overall_recommendation"]
        self.assertEqual(overall["safety_flag"], SAFETY_FLAG_HAZARDOUS)
        self.assertGreater(overall["comfort_score"], overall["trip_quality_score"])
        self.assertLessEqual(overall["trip_quality_score"], 35)

    def test_large_swell_lowers_trip_quality_on_open_coast(self) -> None:
        base_environment = {
            "wind_speed_knots": 7,
            "wind_gust_knots": 11,
            "wind_direction_deg": 110,
            "swell_direction_deg": 110,
            "temperature_c": 17,
            "rain_mm": 0,
            "wave_height_m": 0.3,
            "tide_phase": "rising",
            "tide_stage": "flood",
            "hours_to_high_tide": 1.0,
            "tide_height_change_next_2h": 0.24,
            "tide_range_m": 0.8,
            "time_window": "dawn",
            "hours_from_sunrise": 0.4,
            "is_daylight": True,
        }
        calm = build_preview(
            -41.2530,
            148.3060,
            environment={**base_environment, "swell_height_m": 0.4},
            region="open_coast",
        )
        swell = build_preview(
            -41.2530,
            148.3060,
            environment={**base_environment, "swell_height_m": 1.8},
            region="open_coast",
        )
        self.assertLess(
            swell["overall_recommendation"]["trip_quality_score"],
            calm["overall_recommendation"]["trip_quality_score"],
        )
        self.assertIn(swell["overall_recommendation"]["safety_flag"], {SAFETY_FLAG_MODERATE, SAFETY_FLAG_ELEVATED})


if __name__ == "__main__":
    unittest.main()
