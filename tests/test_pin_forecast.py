"""Tests for per-map-pin forecasting.

The map shows fishing access points (jetties, ramps, beaches) discovered
near the searched coordinate. Before this feature each pin shared the
search center's score, which silently misrepresented pins that face open
water differently from the searched coordinate. Per-pin forecasting runs
build_preview at the pin's own coordinate, sharing the search center's
weather/marine/tide environment but recomputing geometry signals.
"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from coastal_fishing_forecast.api import (
    _augment_facilities_with_pin_forecast,
    _haversine_km,
    _pin_environment_from_best_window,
    _pin_forecast,
    build_frontend_forecast_response,
)
from test_forecast import _fixture_conditions


class HaversineTests(unittest.TestCase):
    def test_haversine_zero_for_same_point(self) -> None:
        self.assertEqual(_haversine_km(-42.88, 147.33, -42.88, 147.33), 0.0)

    def test_haversine_known_distance(self) -> None:
        # Sandy Bay -> Bellerive Pier ~ 3.3 km
        d = _haversine_km(-42.8915, 147.3320, -42.8865, 147.3722)
        self.assertGreater(d, 2.5)
        self.assertLess(d, 4.5)


class PinEnvironmentTests(unittest.TestCase):
    def test_returns_none_when_no_windows(self) -> None:
        self.assertIsNone(_pin_environment_from_best_window({"windows": []}))

    def test_returns_environment_from_best_window(self) -> None:
        forecast = {
            "windows": [
                {
                    "preview": {
                        "status": "ok",
                        "overall_recommendation": {"trip_quality_score": 60, "score": 60, "label": "x"},
                    },
                    "environment": {"wind_speed_knots": 8},
                }
            ]
        }
        env = _pin_environment_from_best_window(forecast)
        self.assertEqual(env, {"wind_speed_knots": 8})


class PinForecastTests(unittest.TestCase):
    def test_pin_forecast_returns_available_for_supported_coord(self) -> None:
        env = {
            "wind_speed_knots": 6,
            "wind_direction_deg": 180,
            "temperature_c": 16,
            "swell_height_m": 0.4,
            "wave_height_m": 0.4,
            "tide_phase": "rising",
            "tide_stage": "flood",
            "hours_to_high_tide": 1.5,
            "tide_height_change_next_2h": 0.2,
            "time_window": "dawn",
        }
        result = _pin_forecast(
            pin_lat=-42.8915,
            pin_lon=147.3320,
            search_lat=-42.8915,
            search_lon=147.3320,
            environment=env,
            region="sheltered_estuary",
        )
        self.assertTrue(result["available"])
        self.assertIsInstance(result["score"], int)
        self.assertIn(result["safety_flag"], {"low", "moderate", "elevated", "hazardous"})
        self.assertIn("fish_outlook_score", result)
        self.assertIn("comfort_score", result)
        self.assertIn("dominant_water_type", result)
        self.assertEqual(result["distance_km_from_search"], 0.0)

    def test_pin_forecast_records_distance_from_search_center(self) -> None:
        env = {"wind_speed_knots": 6, "swell_height_m": 0.4, "tide_phase": "rising"}
        result = _pin_forecast(
            pin_lat=-42.8865,
            pin_lon=147.3722,
            search_lat=-42.8915,
            search_lon=147.3320,
            environment=env,
            region="sheltered_estuary",
        )
        self.assertGreater(result["distance_km_from_search"], 2.5)
        self.assertLess(result["distance_km_from_search"], 4.5)

    def test_pin_forecast_unsupported_when_pin_inland(self) -> None:
        env = {"wind_speed_knots": 6, "swell_height_m": 0.4, "tide_phase": "rising"}
        result = _pin_forecast(
            pin_lat=-25.2744,  # Alice Springs (deep inland)
            pin_lon=133.7751,
            search_lat=-42.8915,
            search_lon=147.3320,
            environment=env,
            region="sheltered_estuary",
        )
        self.assertFalse(result["available"])
        self.assertIn("reason", result)

    def test_pin_forecast_no_environment_returns_unavailable(self) -> None:
        result = _pin_forecast(
            pin_lat=-42.8915,
            pin_lon=147.3320,
            search_lat=-42.8915,
            search_lon=147.3320,
            environment=None,
            region="sheltered_estuary",
        )
        self.assertFalse(result["available"])
        self.assertEqual(result["reason"], "no_environment")

    def test_pin_forecast_uses_pin_specific_geometry(self) -> None:
        # Sheltered point inside Hobart's River Derwent vs an open-facing
        # coordinate further south should produce different dominant types
        # even when the environment dict is identical (same weather).
        env = {
            "wind_speed_knots": 6,
            "wind_direction_deg": 180,
            "swell_direction_deg": 220,
            "temperature_c": 16,
            "swell_height_m": 0.4,
            "wave_height_m": 0.4,
            "tide_phase": "rising",
            "tide_stage": "flood",
            "hours_to_high_tide": 1.5,
            "tide_height_change_next_2h": 0.2,
            "time_window": "dawn",
        }
        sheltered = _pin_forecast(
            pin_lat=-42.8915,  # Sandy Bay (River Derwent)
            pin_lon=147.3320,
            search_lat=-42.8915,
            search_lon=147.3320,
            environment=env,
            region="sheltered_estuary",
        )
        open_facing = _pin_forecast(
            pin_lat=-43.4467782,  # Southport (faces open ocean)
            pin_lon=146.986734,
            search_lat=-42.8915,
            search_lon=147.3320,
            environment=env,
            region="sheltered_estuary",
        )
        # Both are supported but their geometry signals differ enough that
        # the pin_forecast results must not be byte-equal (different
        # exposure / shelter / coastline_complexity flow into the score).
        self.assertTrue(sheltered["available"])
        self.assertTrue(open_facing["available"])
        self.assertGreater(open_facing["distance_km_from_search"], 60)
        # Geometry-derived signals must differ between an inner-river point
        # and a coastline-facing point, even when the score happens to land
        # at the same calibration tier. We check the geometry-pure outputs:
        # support_mode (on_water vs near_water vs tidal_corridor) and
        # search_confidence_score (a direct function of accessibility +
        # nearest-water + on-water status).
        differs = (
            sheltered["support_mode"] != open_facing["support_mode"]
            or sheltered["search_confidence_score"] != open_facing["search_confidence_score"]
        )
        self.assertTrue(
            differs,
            f"Geometry signals identical: sheltered={sheltered}, open={open_facing}",
        )


class AugmentFacilitiesTests(unittest.TestCase):
    def test_augment_attaches_pin_forecast_to_each_facility(self) -> None:
        forecast = {
            "windows": [
                {
                    "preview": {
                        "status": "ok",
                        "overall_recommendation": {"trip_quality_score": 60, "score": 60, "label": "x"},
                    },
                    "environment": {
                        "wind_speed_knots": 6,
                        "swell_height_m": 0.4,
                        "tide_phase": "rising",
                        "time_window": "dawn",
                    },
                }
            ]
        }
        facilities = [
            {
                "id": "test:1",
                "type": "public_jetty",
                "label": "Test jetty",
                "coordinates": {"latitude": -42.8915, "longitude": 147.3320},
            },
            {
                "id": "test:2",
                "type": "boat_ramp",
                "label": "Test ramp",
                "coordinates": {"latitude": -42.8865, "longitude": 147.3722},
            },
        ]
        augmented = _augment_facilities_with_pin_forecast(
            facilities,
            range_forecast=forecast,
            region="sheltered_estuary",
            search_lat=-42.8915,
            search_lon=147.3320,
        )
        self.assertEqual(len(augmented), 2)
        for fac in augmented:
            self.assertIn("pin_forecast", fac)
            self.assertIn("available", fac["pin_forecast"])

    def test_augment_handles_missing_coordinates(self) -> None:
        forecast = {"windows": []}
        facilities = [{"id": "no_coords", "type": "boat_ramp"}]
        augmented = _augment_facilities_with_pin_forecast(
            facilities,
            range_forecast=forecast,
            region="sheltered_estuary",
            search_lat=-42.0,
            search_lon=147.0,
        )
        self.assertEqual(augmented[0]["id"], "no_coords")
        self.assertNotIn("pin_forecast", augmented[0])

    def test_augment_returns_unchanged_when_no_facilities(self) -> None:
        result = _augment_facilities_with_pin_forecast(
            [],
            range_forecast={"windows": []},
            region=None,
            search_lat=0.0,
            search_lon=0.0,
        )
        self.assertEqual(result, [])


class FrontendResponseIntegrationTests(unittest.TestCase):
    def test_frontend_response_keeps_facilities_context_only(self) -> None:
        response = build_frontend_forecast_response(
            -41.2530,
            148.3060,
            start_date="2026-04-20",
            end_date="2026-04-20",
            region="open_coast",
            windows=("morning",),
            condition_data=_fixture_conditions(),
            structure_facilities=[
                {
                    "id": "osm:way:42",
                    "type": "public_jetty",
                    "label": "Test jetty",
                    "access": "public",
                    "status": "confirmed",
                    "coordinates": {"latitude": -41.252, "longitude": 148.310},
                    "distance_km": 0.15,
                }
            ],
            cache_enabled=False,
        )
        facilities = response["structure_facilities"]
        self.assertEqual(len(facilities), 1)
        self.assertNotIn("pin_forecast", facilities[0])

    def test_frontend_response_no_facilities_no_pin_forecast(self) -> None:
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
        self.assertEqual(response["structure_facilities"], [])


if __name__ == "__main__":
    unittest.main()
