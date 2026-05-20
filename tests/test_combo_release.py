"""Tests for combo release: confidence-gated upper-cap unlock."""

from __future__ import annotations

import copy
import unittest

from coastal_fishing_forecast.api import (
    COMBO_HARD_CEILING,
    _apply_combo_release,
    _location_combo_prerequisites,
    _window_combo_evaluation,
    build_frontend_forecast_response,
)
from test_forecast import _fixture_conditions


def _combo_ready_window(
    *,
    score: int = 82,
    activity: int = 82,
    presence: int = 80,
    trip: int = 72,
    dominant: str = "bay_estuary_edge",
    reason_tags: list[str] | None = None,
    inputs_overrides: dict | None = None,
    normalized_overrides: dict | None = None,
    support_mode: str = "on_water",
    search_confidence: float = 0.60,
    open_water_bearing_deg: float | None = 113.0,
) -> dict:
    if reason_tags is None:
        reason_tags = [
            "sunrise_window",
            "rising_tide_window",
            "stable_pressure_bonus",
            "moderate_wind_bonus",
        ]
    inputs_used = {
        "wind_to_shore_category": "side_shore_with_ripple",
        "structure_flow_category": "complex_edge_with_moving_water",
        "wave_height_m": 0.5,
        "swell_height_m": 0.4,
        "wind_speed_knots": 10.0,
    }
    if inputs_overrides:
        inputs_used.update(inputs_overrides)
    normalized = {"weather_shock": 0.0}
    if normalized_overrides:
        normalized.update(normalized_overrides)
    return {
        "date": "2026-04-20",
        "time_window": "morning",
        "preview": {
            "status": "ok",
            "overall_recommendation": {
                "label": "Promising nearby options",
                "score": score,
                "activity_score": activity,
                "presence_score": presence,
                "trip_quality_score": trip,
                "dominant_inferred_type": dominant,
                "reason_tags": list(reason_tags),
            },
            "meta": {
                "support_profile": {"support_mode": support_mode},
                "search_confidence_score": search_confidence,
                "coastline_metrics": {"open_water_bearing_deg": open_water_bearing_deg},
                "environment": {
                    "inputs_used": inputs_used,
                    "normalized": normalized,
                },
            },
        },
    }


def _range_forecast(
    window: dict,
    *,
    tide_source: str = "tide_events",
    tide_provider: dict | None = None,
    extra_windows: list[dict] | None = None,
    hourly: list[dict] | None = None,
) -> dict:
    windows = [window, *(extra_windows or [])]
    score = window["preview"]["overall_recommendation"]["score"]
    return {
        "data_sources": {
            "tide": tide_source,
            "conditions": "open_meteo",
            "tide_provider": tide_provider,
        },
        "summary": {
            "average_score": float(score),
            "best_windows": [
                {
                    "date": window["date"],
                    "time_window": window["time_window"],
                    "score": score,
                }
            ],
        },
        "windows": windows,
        "hourly_activity": hourly or [],
    }


class ComboReleaseUnitTests(unittest.TestCase):
    def test_combo_triggers_when_non_structure_axes_align_with_real_tide(self) -> None:
        window = _combo_ready_window()
        forecast = _range_forecast(window)
        original_score = window["preview"]["overall_recommendation"]["score"]

        summary = _apply_combo_release(forecast)

        boosted = forecast["windows"][0]["preview"]["overall_recommendation"]
        self.assertTrue(summary["applied"])
        self.assertEqual(summary["windows_boosted"], 1)
        self.assertEqual(summary["best_tag"], "strong_alignment_window")
        self.assertGreater(boosted["score"], original_score)
        self.assertLessEqual(boosted["score"], COMBO_HARD_CEILING)
        self.assertIn("strong_alignment_window", boosted["reason_tags"])
        self.assertEqual(boosted["combo_release"]["tag"], "strong_alignment_window")
        self.assertEqual(boosted["combo_release"]["original_score"], original_score)

    def test_combo_uses_strong_tag_when_only_three_axes_align(self) -> None:
        window = _combo_ready_window(
            inputs_overrides={"structure_flow_category": "weak_or_simple_edge"},
        )
        forecast = _range_forecast(window)

        _apply_combo_release(forecast)

        boosted = forecast["windows"][0]["preview"]["overall_recommendation"]
        self.assertEqual(boosted["combo_release"]["tag"], "strong_alignment_window")
        self.assertEqual(boosted["combo_release"]["boost"], 5)

    def test_combo_blocked_when_tide_is_model_estimated(self) -> None:
        window = _combo_ready_window()
        forecast = _range_forecast(window, tide_source="openmeteo_model")
        original = copy.deepcopy(window["preview"]["overall_recommendation"])

        summary = _apply_combo_release(forecast)

        self.assertFalse(summary["applied"])
        self.assertEqual(forecast["windows"][0]["preview"]["overall_recommendation"], original)

    def test_combo_blocked_when_tide_is_approximation(self) -> None:
        window = _combo_ready_window()
        forecast = _range_forecast(window, tide_source="astronomical_approximation")

        summary = _apply_combo_release(forecast)

        self.assertFalse(summary["applied"])

    def test_combo_blocked_when_tide_station_is_remote(self) -> None:
        window = _combo_ready_window()
        forecast = _range_forecast(
            window,
            tide_source="tidesatlas",
            tide_provider={"port_distance_km": 100.0},
        )

        summary = _apply_combo_release(forecast)

        self.assertFalse(summary["applied"])

    def test_combo_allows_local_tidesatlas_station(self) -> None:
        window = _combo_ready_window()
        forecast = _range_forecast(
            window,
            tide_source="tidesatlas",
            tide_provider={"port_distance_km": 12.0},
        )

        summary = _apply_combo_release(forecast)

        self.assertTrue(summary["applied"])

    def test_combo_blocked_when_support_is_only_near_water(self) -> None:
        window = _combo_ready_window(support_mode="near_water")
        forecast = _range_forecast(window)

        summary = _apply_combo_release(forecast)

        self.assertFalse(summary["applied"])

    def test_combo_blocked_when_search_confidence_is_low(self) -> None:
        window = _combo_ready_window(search_confidence=0.40)
        forecast = _range_forecast(window)

        summary = _apply_combo_release(forecast)

        self.assertFalse(summary["applied"])

    def test_combo_blocked_when_open_water_bearing_unknown(self) -> None:
        window = _combo_ready_window(open_water_bearing_deg=None)
        forecast = _range_forecast(window)

        summary = _apply_combo_release(forecast)

        self.assertFalse(summary["applied"])

    def test_combo_blocked_when_wind_geometry_uncertain(self) -> None:
        window = _combo_ready_window(
            inputs_overrides={"wind_to_shore_category": "geometry_uncertain"},
        )
        forecast = _range_forecast(window)

        summary = _apply_combo_release(forecast)

        self.assertFalse(summary["applied"])

    def test_combo_blocked_by_offshore_wind_category(self) -> None:
        window = _combo_ready_window(
            inputs_overrides={"wind_to_shore_category": "offshore_or_push_away"},
        )
        forecast = _range_forecast(window)

        summary = _apply_combo_release(forecast)

        self.assertFalse(summary["applied"])

    def test_combo_blocked_when_recent_weather_shock(self) -> None:
        window = _combo_ready_window(
            reason_tags=[
                "sunrise_window",
                "rising_tide_window",
                "stable_pressure_bonus",
                "recent_weather_shock",
            ],
        )
        forecast = _range_forecast(window)

        summary = _apply_combo_release(forecast)

        self.assertFalse(summary["applied"])

    def test_combo_blocked_when_normalized_weather_shock_high(self) -> None:
        window = _combo_ready_window(normalized_overrides={"weather_shock": 2.0})
        forecast = _range_forecast(window)

        summary = _apply_combo_release(forecast)

        self.assertFalse(summary["applied"])

    def test_combo_blocked_when_pre_combo_scores_below_gate(self) -> None:
        window = _combo_ready_window(score=70, activity=70, presence=68, trip=60)
        forecast = _range_forecast(window)

        summary = _apply_combo_release(forecast)

        self.assertFalse(summary["applied"])

    def test_combo_blocked_when_only_two_axes_align(self) -> None:
        window = _combo_ready_window(
            reason_tags=["sunrise_window", "rising_tide_window"],
            inputs_overrides={"structure_flow_category": "weak_or_simple_edge"},
        )
        forecast = _range_forecast(window)

        summary = _apply_combo_release(forecast)

        self.assertFalse(summary["applied"])

    def test_combo_blocked_for_open_coast_with_large_wave(self) -> None:
        window = _combo_ready_window(
            dominant="beach",
            inputs_overrides={"wave_height_m": 1.2, "swell_height_m": 1.0},
        )
        forecast = _range_forecast(window)

        summary = _apply_combo_release(forecast)

        self.assertFalse(summary["applied"])

    def test_combo_blocked_for_open_coast_with_strong_wind(self) -> None:
        window = _combo_ready_window(
            dominant="rocks",
            inputs_overrides={"wind_speed_knots": 18.0},
        )
        forecast = _range_forecast(window)

        summary = _apply_combo_release(forecast)

        self.assertFalse(summary["applied"])

    def test_combo_allows_open_coast_with_calm_wave_and_wind(self) -> None:
        window = _combo_ready_window(
            dominant="beach",
            inputs_overrides={"wave_height_m": 0.4, "wind_speed_knots": 8.0},
        )
        forecast = _range_forecast(window)

        summary = _apply_combo_release(forecast)

        self.assertTrue(summary["applied"])

    def test_combo_score_capped_at_hard_ceiling(self) -> None:
        window = _combo_ready_window(score=92, activity=92, presence=90, trip=86)
        forecast = _range_forecast(window)

        _apply_combo_release(forecast)

        score = forecast["windows"][0]["preview"]["overall_recommendation"]["score"]
        self.assertLessEqual(score, COMBO_HARD_CEILING)

    def test_combo_recomputes_summary_average_when_window_boosted(self) -> None:
        window = _combo_ready_window(score=82)
        original_average = window["preview"]["overall_recommendation"]["score"]
        forecast = _range_forecast(window)
        forecast["summary"]["average_score"] = float(original_average)

        _apply_combo_release(forecast)

        boosted = forecast["windows"][0]["preview"]["overall_recommendation"]["score"]
        self.assertEqual(forecast["summary"]["average_score"], float(boosted))
        self.assertEqual(forecast["summary"]["best_windows"][0]["score"], boosted)

    def test_combo_does_not_touch_internal_layered_scores(self) -> None:
        window = _combo_ready_window()
        forecast = _range_forecast(window)
        original_layers = {
            "activity_score": window["preview"]["overall_recommendation"]["activity_score"],
            "presence_score": window["preview"]["overall_recommendation"]["presence_score"],
            "trip_quality_score": window["preview"]["overall_recommendation"]["trip_quality_score"],
        }

        _apply_combo_release(forecast)

        boosted = forecast["windows"][0]["preview"]["overall_recommendation"]
        for key, value in original_layers.items():
            self.assertEqual(boosted[key], value, f"Combo must not mutate {key}")

    def test_combo_applies_to_qualifying_hourly_points(self) -> None:
        window = _combo_ready_window()
        hourly = [
            {
                "date": "2026-04-20",
                "hour": 7,
                "score": 80,
                "activity_score": 80,
                "tide_source": "tide_events",
                "rule_tags": [
                    "sunrise_window",
                    "rising_tide_window",
                    "stable_pressure_bonus",
                ],
            },
            {
                "date": "2026-04-20",
                "hour": 14,
                "score": 70,
                "activity_score": 70,
                "tide_source": "tide_events",
                "rule_tags": ["plain_day_penalty"],
            },
            {
                "date": "2026-04-20",
                "hour": 20,
                "score": 80,
                "activity_score": 80,
                "tide_source": "tide_events",
                "rule_tags": [
                    "sunset_window",
                    "rising_tide_window",
                    "recent_weather_shock",
                ],
            },
        ]
        forecast = _range_forecast(window, hourly=hourly)

        _apply_combo_release(forecast)

        self.assertGreater(hourly[0]["score"], 80)
        self.assertEqual(hourly[1]["score"], 70)
        self.assertEqual(hourly[2]["score"], 80)
        self.assertIn("rare_alignment_window", hourly[0]["rule_tags"])

    def test_location_prereqs_returns_none_for_unsupported_preview(self) -> None:
        result = _location_combo_prerequisites(
            {"status": "unsupported", "meta": {"support_profile": {"support_mode": "unsupported"}}},
            {"tide": "tide_events", "conditions": "open_meteo"},
        )
        self.assertIsNone(result)

    def test_window_evaluation_returns_zero_when_prereqs_none(self) -> None:
        window = _combo_ready_window()
        boost, tag = _window_combo_evaluation(window["preview"], None)
        self.assertEqual(boost, 0)
        self.assertIsNone(tag)


class ComboReleaseIntegrationTests(unittest.TestCase):
    def test_default_fixture_does_not_trigger_combo_with_model_tide(self) -> None:
        response = build_frontend_forecast_response(
            -41.2530,
            148.3060,
            start_date="2026-04-20",
            end_date="2026-04-20",
            region="open_coast",
            windows=("morning",),
            condition_data=_fixture_conditions(),
            tide_source="openmeteo_model",
            cache_enabled=False,
        )

        self.assertFalse(response["combo_release"]["applied"])
        self.assertEqual(response["combo_release"]["windows_boosted"], 0)

    def test_combo_release_field_exists_in_response(self) -> None:
        response = build_frontend_forecast_response(
            -41.2530,
            148.3060,
            start_date="2026-04-20",
            end_date="2026-04-20",
            region="open_coast",
            windows=("morning",),
            condition_data=_fixture_conditions(),
            cache_enabled=False,
        )

        combo = response["combo_release"]
        self.assertIn("applied", combo)
        self.assertIn("windows_boosted", combo)
        self.assertIn("hours_boosted", combo)
        self.assertIn("best_tag", combo)


if __name__ == "__main__":
    unittest.main()
