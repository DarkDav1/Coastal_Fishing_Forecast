import tempfile
import unittest
from unittest.mock import patch

from coastal_fishing_forecast.api import _weather_change_notes, build_frontend_forecast_response
from coastal_fishing_forecast.cache import get_json_cache, set_json_cache
from coastal_fishing_forecast.tides import parse_tide_events
from test_forecast import _fixture_conditions


class CacheAndApiTests(unittest.TestCase):
    def test_json_cache_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as cache_dir:
            params = {"url": "https://example.test/data"}
            data = {"ok": True, "value": 42}

            set_json_cache("demo", params, data, cache_dir=cache_dir)
            cached = get_json_cache("demo", params, cache_dir=cache_dir)

        self.assertEqual(cached, data)

    def test_frontend_forecast_response_is_card_oriented(self) -> None:
        response = build_frontend_forecast_response(
            -41.2530,
            148.3060,
            start_date="2026-04-20",
            end_date="2026-04-21",
            region="open_coast",
            windows=("morning", "dusk"),
            condition_data=_fixture_conditions(),
            cache_enabled=False,
        )

        self.assertEqual(response["api_contract_version"], "2026-04-27.frontend.v1")
        self.assertIn("hero", response)
        self.assertIn("plan", response)
        self.assertIn("explanation", response)
        self.assertEqual(response["location"]["source"], "coordinate_input")
        self.assertIn("confidence", response)
        self.assertIn("tide_verification", response)
        self.assertIn("daily_forecast", response)
        self.assertIn("hourly_activity", response)
        self.assertIn("social_pulse", response)
        self.assertEqual(len(response["daily_forecast"]), 2)
        self.assertEqual(len(response["hourly_activity"]), 48)
        self.assertIsInstance(response["hourly_activity"][13]["score"], int)
        self.assertIn("conditions", response["daily_forecast"][0]["windows"][0])
        self.assertIn("expanded_water_types", response["daily_forecast"][0]["windows"][0])
        self.assertIn("behavior_groups", response["daily_forecast"][0]["windows"][0])
        self.assertIn("score_breakdown", response["daily_forecast"][0]["windows"][0])
        self.assertIn("raw_time_signal", response["daily_forecast"][0]["windows"][0]["conditions"]["formula"])
        self.assertIn("weather_trend", response["daily_forecast"][0]["windows"][0]["conditions"])
        self.assertIn("wind", response["daily_forecast"][0]["windows"][0]["conditions"])
        self.assertIn("swell", response["daily_forecast"][0]["windows"][0]["conditions"])
        self.assertIn("tide", response["daily_forecast"][0]["windows"][0]["conditions"])
        self.assertTrue(response["modules"]["weather"])
        self.assertTrue(response["modules"]["marine"])
        self.assertTrue(response["modules"]["tide"])
        self.assertTrue(response["modules"]["plan"])
        self.assertTrue(response["modules"]["expanded_water_types"])
        self.assertTrue(response["modules"]["behavior_groups"])
        self.assertTrue(response["modules"]["confidence"])
        self.assertTrue(response["modules"]["explanation"])
        self.assertIn("social_pulse", response["modules"])
        self.assertEqual(response["social_pulse"]["role"], "context_only")
        self.assertFalse(response["social_pulse"]["score_adjustment_allowed"])
        self.assertIn("why_this_window", response["explanation"])
        self.assertIn("risks", response["explanation"])
        self.assertEqual(response["plan"]["recommendation"]["score"], response["hero"]["score"])
        self.assertEqual(response["plan"]["primary_action"]["water_type"], response["hero"]["best_window"]["dominant_water_type"])

    def test_frontend_response_accepts_real_tide_events(self) -> None:
        response = build_frontend_forecast_response(
            -41.2530,
            148.3060,
            start_date="2026-04-20",
            end_date="2026-04-20",
            region="open_coast",
            windows=("morning",),
            condition_data=_fixture_conditions(),
            tide_events=[
                {"time": "2026-04-20T05:00:00+10:00", "type": "low"},
                {"time": "2026-04-20T11:00:00+10:00", "type": "high"},
            ],
            cache_enabled=False,
        )

        self.assertEqual(response["location"]["display_name"], "-41.2530, 148.3060")
        self.assertEqual(response["location"]["source"], "coordinate_input")
        self.assertEqual(response["tide_verification"]["status"], "provided_events")
        self.assertGreaterEqual(response["confidence"]["score"], 55)
        self.assertEqual(response["plan"]["data_source_note"], "Tide data came from supplied tide events.")
        behavior_keys = {group["key"] for group in response["daily_forecast"][0]["windows"][0]["behavior_groups"]}
        self.assertIn("beach_roaming_fish", behavior_keys)

    def test_remote_tidesatlas_station_lowers_tide_verification(self) -> None:
        events = parse_tide_events(
            [
                {"time": "2026-04-20T05:00:00+10:00", "type": "low"},
                {"time": "2026-04-20T11:00:00+10:00", "type": "high"},
            ]
        )
        with patch(
            "coastal_fishing_forecast.forecast.fetch_tidesatlas_events",
            return_value=(events, {"provider": "tidesatlas", "port": {"name": "Remote"}, "port_distance_km": 100.0}),
        ):
            response = build_frontend_forecast_response(
                -41.2530,
                148.3060,
                start_date="2026-04-20",
                end_date="2026-04-20",
                region="open_coast",
                windows=("morning",),
                condition_data=_fixture_conditions(),
                tide_source="tidesatlas",
                tidesatlas_api_key="test-key",
                cache_enabled=False,
            )

        self.assertEqual(response["tide_verification"]["status"], "live_verified_remote_station")
        self.assertEqual(response["tide_verification"]["station_distance_km"], 100.0)
        self.assertIn("distant", response["confidence"]["factors"][-1])
        self.assertIn("distant station", response["plan"]["confidence_note"])

    def test_frontend_response_marks_openmeteo_model_tide_in_plan(self) -> None:
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

        self.assertEqual(response["tide_verification"]["status"], "model_estimated")
        self.assertIn("model sea-level", response["plan"]["confidence_note"])
        self.assertEqual(response["daily_forecast"][0]["best_window"]["conditions"]["tide"]["source"], "openmeteo_model")
        self.assertLessEqual(response["confidence"]["score"], 60)
        self.assertIn("model-estimated", " ".join(response["confidence"]["limitations"]))

    def test_confidence_is_separate_from_visible_score_when_evidence_is_uncertain(self) -> None:
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

        self.assertIsNotNone(response["hero"]["score"])
        self.assertLessEqual(response["confidence"]["score"], 60)
        self.assertIn("caps_applied", response["confidence"])
        cap_reasons = " ".join(item["reason"] for item in response["confidence"]["caps_applied"])
        self.assertIn("Model sea-level", cap_reasons)

    def test_frontend_response_accepts_public_jetty_structure_layer(self) -> None:
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
                    "id": "osm:way:123",
                    "type": "public_jetty",
                    "label": "Mapped public jetty",
                    "access": "public",
                    "status": "confirmed",
                }
            ],
            cache_enabled=False,
        )

        self.assertTrue(response["modules"]["map"])
        self.assertEqual(response["structure_facilities"][0]["type"], "public_jetty")
        self.assertIn("public_jetty", response["plan"]["terrain_certainty"]["confirmed_features"])
        self.assertNotIn("public jetty", response["plan"]["terrain_certainty"]["forbidden_claims"])

    def test_github_models_explanation_rewrites_text_only(self) -> None:
        model_text = {
            "why_this_window": [
                "Morning is the clearest available window in this forecast.",
                "The score reflects the local water and wind checks rather than time alone.",
            ],
            "score_story": "The engine kept the score fixed and only rewrote the explanation.",
            "local_adjustment_summary": "Local modifiers are summarized without changing the forecast.",
        }
        with patch("coastal_fishing_forecast.api.generate_github_models_explanation_text", return_value=model_text):
            response = build_frontend_forecast_response(
                -41.2530,
                148.3060,
                start_date="2026-04-20",
                end_date="2026-04-20",
                region="open_coast",
                windows=("morning",),
                condition_data=_fixture_conditions(),
                explanation_provider="github_models",
                cache_enabled=False,
            )

        self.assertEqual(response["explanation"]["source"], "github_models")
        self.assertEqual(response["explanation"]["why_this_window"], model_text["why_this_window"])
        self.assertEqual(response["explanation"]["score_story"], model_text["score_story"])
        self.assertIn("risks", response["explanation"])
        self.assertEqual(response["plan"]["recommendation"]["score"], response["hero"]["score"])

    def test_github_models_explanation_input_hides_internal_scoring_terms(self) -> None:
        captured = {}

        def fake_explanation(payload):
            captured["payload"] = payload
            return {
                "why_this_window": [
                    "Morning has the best mix of conditions.",
                    "Moving water helps, while the broader weather keeps the advice cautious.",
                ]
            }

        with patch("coastal_fishing_forecast.api.generate_github_models_explanation_text", side_effect=fake_explanation):
            build_frontend_forecast_response(
                -41.2530,
                148.3060,
                start_date="2026-04-20",
                end_date="2026-04-20",
                region="open_coast",
                windows=("morning",),
                condition_data=_fixture_conditions(),
                explanation_provider="github_models",
                cache_enabled=False,
            )

        serialized = str(captured["payload"]).lower()
        self.assertNotIn("raw_time", serialized)
        self.assertNotIn("score_breakdown", serialized)
        self.assertNotIn("reason_tags", serialized)
        self.assertIn("plain_score_context", serialized)
        self.assertIn("weather_trend", serialized)

    def test_weather_change_notes_make_trend_human_readable(self) -> None:
        notes = _weather_change_notes(
            {
                "temperature_drop_from_recent_72h_peak": -6.2,
                "pressure_delta_24h": -9.1,
                "wind_direction_change_12h": 120,
                "rainfall_24h": 34,
            }
        )

        joined = " ".join(notes).lower()
        self.assertIn("temperature", joined)
        self.assertIn("pressure", joined)
        self.assertIn("wind direction", joined)
        self.assertIn("rain", joined)

    def test_github_models_explanation_filters_internal_jargon(self) -> None:
        with patch(
            "coastal_fishing_forecast.api.generate_github_models_explanation_text",
            return_value={
                "why_this_window": [
                    "The raw time signal is strong.",
                    "The score_breakdown says water helped.",
                ],
                "local_adjustment_summary": "Moving water helped, but recent weather kept the advice cautious.",
            },
        ):
            response = build_frontend_forecast_response(
                -41.2530,
                148.3060,
                start_date="2026-04-20",
                end_date="2026-04-20",
                region="open_coast",
                windows=("morning",),
                condition_data=_fixture_conditions(),
                explanation_provider="github_models",
                cache_enabled=False,
            )

        self.assertEqual(response["explanation"]["source"], "github_models")
        self.assertNotIn("raw time signal", " ".join(response["explanation"]["why_this_window"]).lower())
        self.assertIn("Moving water helped", response["explanation"]["local_adjustment_summary"])

    def test_github_models_explanation_falls_back_when_invalid(self) -> None:
        with patch("coastal_fishing_forecast.api.generate_github_models_explanation_text", return_value={"why_this_window": ["too short"]}):
            response = build_frontend_forecast_response(
                -41.2530,
                148.3060,
                start_date="2026-04-20",
                end_date="2026-04-20",
                region="open_coast",
                windows=("morning",),
                condition_data=_fixture_conditions(),
                explanation_provider="github_models",
                cache_enabled=False,
            )

        self.assertEqual(response["explanation"]["source"], "rule_based")
        self.assertNotIn("score_story", response["explanation"])

    def test_github_models_explanation_can_keep_rule_reasons_and_add_score_story(self) -> None:
        with patch(
            "coastal_fishing_forecast.api.generate_github_models_explanation_text",
            return_value={
                "why_this_window": ["too short"],
                "local_adjustment_summary": "Good light was moderated by the local movement checks.",
            },
        ):
            response = build_frontend_forecast_response(
                -41.2530,
                148.3060,
                start_date="2026-04-20",
                end_date="2026-04-20",
                region="open_coast",
                windows=("morning",),
                condition_data=_fixture_conditions(),
                explanation_provider="github_models",
                cache_enabled=False,
            )

        self.assertEqual(response["explanation"]["source"], "github_models")
        self.assertGreaterEqual(len(response["explanation"]["why_this_window"]), 2)
        self.assertIn("local movement", response["explanation"]["local_adjustment_summary"])

    def test_frontend_response_can_fetch_osm_structures(self) -> None:
        with patch(
            "coastal_fishing_forecast.api.fetch_osm_structure_facilities",
            return_value={
                "source": "osm_overpass",
                "facilities": [
                    {
                        "id": "osm:way:208921096",
                        "type": "public_jetty",
                        "label": "Battery Point Public Jetty",
                        "access": "public",
                        "status": "confirmed",
                        "planner_eligible": True,
                    }
                ],
            },
        ):
            response = build_frontend_forecast_response(
                -42.8991036,
                147.3389916,
                start_date="2026-04-20",
                end_date="2026-04-20",
                region="sheltered_estuary",
                windows=("morning",),
                condition_data=_fixture_conditions(),
                structure_source="osm",
                cache_enabled=False,
            )

        self.assertTrue(response["modules"]["map"])
        self.assertEqual(response["structure_facilities"][0]["label"], "Battery Point Public Jetty")
        self.assertIn("mapped public jetty", response["plan"]["primary_action"]["text"])
        self.assertIn("Battery Point Public Jetty", response["plan"]["primary_action"]["confirmed_structure"])

    def test_frontend_response_can_fetch_combined_structure_sources(self) -> None:
        with patch(
            "coastal_fishing_forecast.api.fetch_combined_structure_facilities",
            return_value={
                "source": "combined",
                "sources": [
                    {"source": "list_mast", "status": "ok", "count": 1},
                    {"source": "osm_overpass", "status": "ok", "count": 1},
                ],
                "facilities": [
                    {
                        "id": "osm:way:208921096",
                        "type": "public_jetty",
                        "label": "Battery Point Public Jetty",
                        "access": "public",
                        "status": "confirmed",
                        "planner_eligible": True,
                    },
                    {
                        "id": "list_mast:256",
                        "type": "boat_ramp",
                        "label": "Boat Ramp",
                        "access": "public",
                        "status": "confirmed",
                        "planner_eligible": False,
                    },
                ],
            },
        ):
            response = build_frontend_forecast_response(
                -42.8991036,
                147.3389916,
                start_date="2026-04-20",
                end_date="2026-04-20",
                region="sheltered_estuary",
                windows=("morning",),
                condition_data=_fixture_conditions(),
                structure_source="auto",
                cache_enabled=False,
            )

        self.assertEqual(response["structure_data"]["source"], "combined")
        self.assertEqual(len(response["structure_facilities"]), 2)
        self.assertIn("mapped public jetty", response["plan"]["primary_action"]["text"])
        self.assertIn("Battery Point Public Jetty", response["plan"]["primary_action"]["confirmed_structure"])


if __name__ == "__main__":
    unittest.main()
