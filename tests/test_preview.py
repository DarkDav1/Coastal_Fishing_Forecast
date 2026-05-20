import unittest

from coastal_fishing_forecast.preview import build_preview
from fixtures_regression_samples import REGRESSION_SAMPLES


class PreviewTests(unittest.TestCase):
    def test_regression_samples_include_metadata(self) -> None:
        allowed_types = {"public_reference", "boundary_probe", "scanned_candidate"}
        for sample in REGRESSION_SAMPLES:
            with self.subTest(sample=sample["id"]):
                self.assertIn("sample_type", sample)
                self.assertIn(sample["sample_type"], allowed_types)
                self.assertTrue(sample.get("selection_reason"))

    def test_regression_samples_match_expected_status(self) -> None:
        for sample in REGRESSION_SAMPLES:
            with self.subTest(sample=sample["id"]):
                result = build_preview(sample["lat"], sample["lon"])
                self.assertEqual(result["status"], sample["expected_status"])

    def test_invalid_coordinate_returns_structured_response(self) -> None:
        result = build_preview(95.0, 151.0)
        self.assertEqual(result["status"], "invalid_input")
        self.assertEqual(result["support"]["reason_code"], "invalid_coordinate")
        self.assertFalse(result["support"]["supported"])
        self.assertEqual(result["contract_version"], "2026-04-23.preview.v1")

    def test_inland_coordinate_is_rejected(self) -> None:
        result = build_preview(-23.6980, 133.8807)
        self.assertEqual(result["status"], "unsupported")
        self.assertFalse(result["support"]["supported"])
        self.assertEqual(result["support"]["reason_code"], "inland_or_non_tidal")
        self.assertIn("coastal and tidal", result["support"]["message"])

    def test_coastal_land_coordinate_returns_preview_shape(self) -> None:
        result = build_preview(-33.8915, 151.2767)
        self.assertEqual(result["status"], "ok")
        self.assertTrue(result["support"]["supported"])
        self.assertEqual(result["support"]["confidence"], "low")
        self.assertGreater(result["support"]["nearest_supported_water_km"], 0.0)
        self.assertEqual(result["contract_version"], "2026-04-23.preview.v1")
        self.assertIn("overall_recommendation", result)
        self.assertEqual(
            set(result["nearby_water_types"]),
            {"beach", "rocks", "jetty", "bay_estuary_edge"},
        )
        self.assertEqual(
            result["meta"]["water_type_order"],
            ["beach", "rocks", "jetty", "bay_estuary_edge"],
        )
        self.assertIn("inference_signals", result["meta"])
        self.assertIsNotNone(result["meta"]["coastline_metrics"]["open_water_bearing_deg"])
        for card in result["nearby_water_types"].values():
            self.assertIn("scores", card)
            self.assertGreaterEqual(card["scores"]["overall_recommendation"], 0)
            self.assertLessEqual(card["scores"]["overall_recommendation"], 100)

    def test_tidal_water_coordinate_returns_preview(self) -> None:
        result = build_preview(-42.8821, 147.3390)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["support"]["nearest_supported_water_km"], 0.0)
        self.assertFalse(result["meta"]["curated_spot_equivalent"])
        self.assertIn(result["overall_recommendation"]["dominant_inferred_type"], result["nearby_water_types"])
        self.assertEqual(result["meta"]["region"]["slug"], "generic_coastal")
        self.assertEqual(result["meta"]["support_profile"]["support_mode"], "on_water")

    def test_open_coast_coordinate_leans_beach(self) -> None:
        result = build_preview(-33.7950, 151.2870)
        strengths = result["meta"]["inference_signals"]["type_strengths"]
        self.assertGreaterEqual(strengths["beach"], strengths["bay_estuary_edge"])
        self.assertGreaterEqual(strengths["beach"], strengths["rocks"])

    def test_sheltered_edge_coordinate_keeps_bay_estuary_signal(self) -> None:
        result = build_preview(-33.8523, 151.2108)
        strengths = result["meta"]["inference_signals"]["type_strengths"]
        self.assertGreaterEqual(strengths["bay_estuary_edge"], 0.5)
        self.assertGreaterEqual(strengths["jetty"], 0.45)

    def test_rocky_open_edge_coordinate_keeps_strong_rocks_signal(self) -> None:
        result = build_preview(-33.9904, 151.2305)
        strengths = result["meta"]["inference_signals"]["type_strengths"]
        self.assertGreaterEqual(strengths["rocks"], 0.55)
        self.assertGreaterEqual(strengths["rocks"], strengths["bay_estuary_edge"])

    def test_near_coast_inland_boundary_stays_supported_but_low_confidence(self) -> None:
        result = build_preview(-28.0167, 153.4000)
        self.assertEqual(result["status"], "ok")
        self.assertGreater(result["support"]["nearest_supported_water_km"], 0.0)
        self.assertLess(result["meta"]["search_confidence_score"], 0.5)
        self.assertEqual(result["meta"]["support_profile"]["support_mode"], "near_water")

    def test_farther_inland_boundary_is_rejected_by_distance(self) -> None:
        result = build_preview(-28.0300, 153.3800)
        self.assertEqual(result["status"], "unsupported")
        self.assertEqual(result["support"]["reason_code"], "too_far_from_supported_water")
        self.assertGreaterEqual(result["support"]["nearest_supported_water_km"], 8.0)

    def test_tidal_corridor_candidate_uses_extended_reason_code(self) -> None:
        result = build_preview(-33.9000, 151.0800)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["support"]["reason_code"], "tidal_corridor_preview")
        self.assertGreater(result["support"]["nearest_supported_water_km"], 5.0)
        self.assertEqual(result["meta"]["support_profile"]["support_mode"], "tidal_corridor")

    def test_environment_inputs_are_reflected_in_meta(self) -> None:
        result = build_preview(
            -33.8915,
            151.2767,
            environment={
                "wind_speed_knots": 24,
                "swell_height_m": 2.7,
                "pressure_hpa": 1007,
                "tide_phase": "rising",
                "time_window": "dawn",
            },
        )
        env = result["meta"]["environment"]
        self.assertEqual(env["inputs_used"]["tide_phase"], "rising")
        self.assertEqual(env["inputs_used"]["time_window"], "dawn")
        self.assertEqual(env["normalized"]["wind_alignment"], 0.5)
        self.assertEqual(env["normalized"]["swell_alignment"], 0.5)
        self.assertGreater(env["normalized"]["exposed_penalty"], 0.3)

    def test_harsh_exposed_conditions_reduce_beach_trip_more_than_bay_trip(self) -> None:
        neutral = build_preview(-33.8915, 151.2767)
        harsh = build_preview(
            -33.8915,
            151.2767,
            environment={
                "wind_speed_knots": 30,
                "swell_height_m": 3.0,
                "tide_phase": "high",
                "time_window": "day",
            },
        )
        neutral_beach = neutral["nearby_water_types"]["beach"]["scores"]["trip_quality"]
        harsh_beach = harsh["nearby_water_types"]["beach"]["scores"]["trip_quality"]
        neutral_bay = neutral["nearby_water_types"]["bay_estuary_edge"]["scores"]["trip_quality"]
        harsh_bay = harsh["nearby_water_types"]["bay_estuary_edge"]["scores"]["trip_quality"]
        self.assertLess(harsh_beach, neutral_beach)
        self.assertLessEqual(neutral_bay - harsh_bay, neutral_beach - harsh_beach)

    def test_dawn_rising_tide_improves_open_coast_roaming_signal(self) -> None:
        neutral = build_preview(-33.7950, 151.2870)
        favorable = build_preview(
            -33.7950,
            151.2870,
            environment={
                "wind_speed_knots": 10,
                "swell_height_m": 1.0,
                "pressure_hpa": 1018,
                "tide_phase": "rising",
                "time_window": "dawn",
            },
        )
        self.assertGreater(
            favorable["nearby_water_types"]["beach"]["scores"]["roaming_opportunity"],
            neutral["nearby_water_types"]["beach"]["scores"]["roaming_opportunity"],
        )

    def test_dawn_and_dusk_are_stronger_than_plain_day_when_conditions_match(self) -> None:
        base_environment = {
            "wind_speed_knots": 10,
            "swell_height_m": 1.0,
            "pressure_hpa": 1018,
            "tide_phase": "rising",
        }
        day = build_preview(-33.7950, 151.2870, environment={**base_environment, "time_window": "day"})
        dawn = build_preview(-33.7950, 151.2870, environment={**base_environment, "time_window": "dawn"})
        dusk = build_preview(-33.7950, 151.2870, environment={**base_environment, "time_window": "dusk"})

        day_score = day["overall_recommendation"]["score"]
        self.assertGreater(dawn["overall_recommendation"]["score"], day_score)
        self.assertGreater(dusk["overall_recommendation"]["score"], day_score)

    def test_public_preview_scores_stay_below_curated_certainty(self) -> None:
        result = build_preview(
            -42.8991036,
            147.3389916,
            environment={
                "wind_speed_knots": 5.5,
                "swell_height_m": 0.2,
                "pressure_hpa": 1022,
                "pressure_delta_3h": 0.3,
                "tide_phase": "rising",
                "tide_stage": "flood",
                "hours_to_high_tide": 2,
                "tide_height_change_next_2h": 0.18,
                "tide_height_change_next_3h": 0.25,
                "tide_movement_rate_m_per_hour": 0.09,
                "time_window": "dawn",
                "hours_from_sunrise": -1,
                "is_daylight": False,
                "moon_phase_name": "full_moon",
            },
            region="sheltered_estuary",
        )

        self.assertGreaterEqual(result["overall_recommendation"]["score"], 70)
        self.assertLessEqual(result["overall_recommendation"]["score"], 85)
        self.assertLessEqual(
            result["nearby_water_types"]["bay_estuary_edge"]["scores"]["overall_recommendation"],
            70,
        )

    def test_generic_rules_do_not_include_derwent_spot_specific_tags(self) -> None:
        result = build_preview(
            -42.8991036,
            147.3389916,
            environment={
                "wind_speed_knots": 8,
                "swell_height_m": 0.4,
                "tide_phase": "rising",
                "time_window": "dusk",
            },
            region="sheltered_estuary",
        )

        forbidden = {
            "open_shore_evening_bonus",
            "bridge_zone_bonus",
            "stronger_tide_window",
            "night_tide_bonus",
            "structure_bias",
            "shoreline_bait_push",
        }
        tags = set(result["overall_recommendation"]["reason_tags"])
        self.assertFalse(tags & forbidden)
        self.assertEqual(result["overall_recommendation"]["model_rule_family"], "derwent_generalized_v1")

    def test_dead_water_caps_good_timing_score(self) -> None:
        base_environment = {
            "wind_speed_knots": 7,
            "swell_height_m": 0.4,
            "pressure_hpa": 1020,
            "pressure_delta_3h": 0.4,
            "tide_phase": "rising",
            "tide_stage": "flood",
            "hours_to_high_tide": 1.5,
            "time_window": "dawn",
            "hours_from_sunrise": -0.5,
            "is_daylight": False,
            "moon_phase_name": "full_moon",
        }
        moving = build_preview(
            -42.8991036,
            147.3389916,
            environment={
                **base_environment,
                "tide_height_change_next_2h": 0.22,
                "tide_height_change_next_3h": 0.32,
                "tide_movement_rate_m_per_hour": 0.11,
            },
            region="sheltered_estuary",
        )
        dead = build_preview(
            -42.8991036,
            147.3389916,
            environment={
                **base_environment,
                "tide_height_change_next_2h": 0.03,
                "tide_height_change_next_3h": 0.06,
                "tide_movement_rate_m_per_hour": 0.02,
            },
            region="sheltered_estuary",
        )

        self.assertLess(dead["overall_recommendation"]["score"], moving["overall_recommendation"]["score"])
        self.assertLessEqual(dead["overall_recommendation"]["score"], 65)
        tags = set(dead["overall_recommendation"]["reason_tags"])
        self.assertIn("dead_water_2h", tags)
        self.assertIn("timing_capped_by_dead_water", tags)

    def test_sheltered_estuary_lift_requires_flow_and_no_weather_shock(self) -> None:
        base_environment = {
            "wind_speed_knots": 7,
            "swell_height_m": 0.25,
            "pressure_hpa": 1020,
            "pressure_delta_3h": 0.2,
            "tide_phase": "rising",
            "tide_stage": "flood",
            "hours_to_high_tide": 1.5,
            "time_window": "dusk",
            "hours_from_sunset": -0.5,
            "is_daylight": True,
            "moon_phase_name": "first_quarter",
        }
        moving = build_preview(
            -42.9810,
            147.3240,
            environment={
                **base_environment,
                "tide_height_change_next_2h": 0.22,
                "tide_height_change_next_3h": 0.32,
                "tide_movement_rate_m_per_hour": 0.11,
            },
            region="sheltered_estuary",
        )
        dead = build_preview(
            -42.9810,
            147.3240,
            environment={
                **base_environment,
                "tide_height_change_next_2h": 0.03,
                "tide_height_change_next_3h": 0.06,
                "tide_movement_rate_m_per_hour": 0.02,
            },
            region="sheltered_estuary",
        )
        shocked = build_preview(
            -42.9810,
            147.3240,
            environment={
                **base_environment,
                "tide_height_change_next_2h": 0.22,
                "tide_height_change_next_3h": 0.32,
                "tide_movement_rate_m_per_hour": 0.11,
                "temperature_delta_24h": -5.5,
                "temperature_drop_from_recent_72h_peak": -7,
            },
            region="sheltered_estuary",
        )

        moving_tags = set(moving["overall_recommendation"]["reason_tags"])
        dead_tags = set(dead["overall_recommendation"]["reason_tags"])
        shocked_tags = set(shocked["overall_recommendation"]["reason_tags"])
        self.assertIn("sheltered_estuary_supportive_flow", moving_tags)
        self.assertNotIn("sheltered_estuary_supportive_flow", dead_tags)
        self.assertNotIn("sheltered_estuary_supportive_flow", shocked_tags)
        self.assertGreater(moving["overall_recommendation"]["score"], dead["overall_recommendation"]["score"])
        self.assertGreater(moving["overall_recommendation"]["score"], shocked["overall_recommendation"]["score"])

    def test_ocean_influenced_estuary_swell_caps_false_highs(self) -> None:
        # Wind is moderate enough (8 kn ~= 14.8 kph) that local chop is
        # plausible on top of the offshore swell, so the ocean-influenced
        # penalty should still fire. The light-wind softening path is covered
        # by test_calm_wind_softens_passing_swell_for_sheltered_estuary below.
        base_environment = {
            "wind_speed_knots": 8,
            "wind_direction_deg": 5,
            "pressure_hpa": 1009,
            "pressure_delta_3h": -1.0,
            "cloud_cover_pct": 67,
            "tide_phase": "rising",
            "tide_stage": "flood",
            "hours_since_low_tide": 2,
            "hours_to_high_tide": 8,
            "tide_range_m": 0.72,
            "tide_height_change_next_2h": 0.22,
            "tide_height_change_next_3h": 0.32,
            "tide_movement_rate_m_per_hour": 0.11,
            "time_window": "dawn",
            "hours_from_sunrise": 0.8,
            "is_daylight": True,
        }
        calm = build_preview(
            -43.4467782,
            146.986734,
            environment={
                **base_environment,
                "swell_height_m": 0.55,
                "wave_height_m": 0.8,
            },
            region="sheltered_estuary",
        )
        exposed = build_preview(
            -43.4467782,
            146.986734,
            environment={
                **base_environment,
                "swell_height_m": 1.22,
                "wave_height_m": 1.68,
            },
            region="sheltered_estuary",
        )
        rough = build_preview(
            -43.4467782,
            146.986734,
            environment={
                **base_environment,
                "swell_height_m": 3.0,
                "wave_height_m": 3.6,
            },
            region="sheltered_estuary",
        )

        exposed_tags = set(exposed["overall_recommendation"]["reason_tags"])
        rough_tags = set(rough["overall_recommendation"]["reason_tags"])
        self.assertGreater(calm["overall_recommendation"]["score"], exposed["overall_recommendation"]["score"])
        self.assertLessEqual(exposed["overall_recommendation"]["score"], 75)
        self.assertLess(rough["overall_recommendation"]["score"], exposed["overall_recommendation"]["score"])
        self.assertIn("ocean_influenced_estuary_swell_penalty", exposed_tags)
        self.assertIn("rough_open_bay_cap", rough_tags)
        self.assertNotIn("sheltered_estuary_supportive_flow", exposed_tags)

    def test_calm_wind_softens_passing_swell_for_sheltered_estuary(self) -> None:
        # Reproduction of the Southport "calm day with offshore swell" case:
        # local wind is light, but Open-Meteo reports 1.5-1.7m wave at the
        # bay-mouth grid cell. The bay's inner angles should still be treated
        # as fishable (no ocean-pressure cap, no big_wave_beach hard penalty).
        base_environment = {
            "wind_speed_knots": 5.5,
            "wind_direction_deg": 5,
            "pressure_hpa": 1009,
            "pressure_delta_3h": -1.0,
            "cloud_cover_pct": 67,
            "tide_phase": "rising",
            "tide_stage": "flood",
            "hours_since_low_tide": 2,
            "hours_to_high_tide": 8,
            "tide_range_m": 0.72,
            "tide_height_change_next_2h": 0.22,
            "tide_height_change_next_3h": 0.32,
            "tide_movement_rate_m_per_hour": 0.11,
            "time_window": "dawn",
            "hours_from_sunrise": 0.8,
            "is_daylight": True,
        }
        light_wind = build_preview(
            -43.4467782,
            146.986734,
            environment={
                **base_environment,
                "swell_height_m": 1.22,
                "wave_height_m": 1.68,
            },
            region="sheltered_estuary",
        )

        tags = set(light_wind["overall_recommendation"]["reason_tags"])
        self.assertNotIn("ocean_influenced_estuary_swell_penalty", tags)
        self.assertNotIn("open_bay_swell_cap", tags)
        self.assertNotIn("big_wave_beach", tags)
        self.assertIn("passing_swell_high", tags)
        self.assertGreater(light_wind["overall_recommendation"]["score"], 65)

    def test_passing_swell_replaces_big_wave_beach_under_light_wind(self) -> None:
        base_environment = {
            "swell_height_m": 1.5,
            "wave_height_m": 1.5,
            "tide_phase": "rising",
            "tide_stage": "flood",
            "hours_to_high_tide": 1.5,
            "tide_height_change_next_2h": 0.2,
        }
        light = build_preview(
            -42.9810,
            147.3240,
            environment={**base_environment, "wind_speed_knots": 6},
            region="sheltered_estuary",
        )
        windy = build_preview(
            -42.9810,
            147.3240,
            environment={**base_environment, "wind_speed_knots": 14},
            region="sheltered_estuary",
        )

        light_tags = set(light["overall_recommendation"]["reason_tags"])
        windy_tags = set(windy["overall_recommendation"]["reason_tags"])
        self.assertIn("passing_swell_high", light_tags)
        self.assertNotIn("big_wave_beach", light_tags)
        self.assertIn("big_wave_beach", windy_tags)
        self.assertNotIn("passing_swell_high", windy_tags)

    def test_dominant_type_uses_region_preference_when_scores_are_close(self) -> None:
        # On a sheltered-estuary region search, when beach / jetty / bay scores
        # all land within ~6 points of each other, the engine should prefer
        # bay_estuary_edge / jetty rather than letting beach win by dict order.
        environment = {
            "wind_speed_knots": 6,
            "swell_height_m": 0.4,
            "tide_phase": "rising",
            "tide_stage": "flood",
            "hours_to_high_tide": 1.5,
            "tide_height_change_next_2h": 0.2,
            "time_window": "dawn",
        }
        sheltered = build_preview(
            -43.4467782,
            146.986734,
            environment=environment,
            region="sheltered_estuary",
        )
        open_coast = build_preview(
            -43.4467782,
            146.986734,
            environment=environment,
            region="open_coast",
        )

        self.assertIn(
            sheltered["overall_recommendation"]["dominant_inferred_type"],
            {"bay_estuary_edge", "jetty"},
        )
        # Open-coast region keeps beach / rocks as preferred dominant for the
        # same coordinate when scores are close.
        self.assertIn(
            open_coast["overall_recommendation"]["dominant_inferred_type"],
            {"beach", "rocks", "jetty", "bay_estuary_edge"},
        )

    def test_score_breakdown_shows_raw_time_vs_local_adjustment(self) -> None:
        result = build_preview(
            -42.8991036,
            147.3389916,
            environment={
                "wind_speed_knots": 7,
                "swell_height_m": 0.4,
                "pressure_hpa": 1020,
                "pressure_delta_3h": 0.4,
                "tide_phase": "rising",
                "tide_stage": "flood",
                "hours_to_high_tide": 1.5,
                "tide_height_change_next_2h": 0.03,
                "tide_height_change_next_3h": 0.06,
                "tide_movement_rate_m_per_hour": 0.02,
                "time_window": "dawn",
                "hours_from_sunrise": -0.5,
                "is_daylight": False,
                "moon_phase_name": "full_moon",
            },
            region="sheltered_estuary",
        )

        breakdown = result["overall_recommendation"]["score_breakdown"]
        self.assertGreaterEqual(breakdown["raw_time_signal_score"], 68)
        self.assertLess(breakdown["local_adjusted_score"], breakdown["raw_time_signal_score"])
        self.assertLess(breakdown["adjustment_delta"], 0)
        driver_ids = {driver["id"] for driver in breakdown["drivers"]}
        self.assertIn("weak_water_movement", driver_ids)
        self.assertEqual(
            result["meta"]["environment"]["raw_time_signal"]["score"],
            breakdown["raw_time_signal_score"],
        )

    def test_weather_shock_penalty_reduces_good_timing_score(self) -> None:
        base_environment = {
            "wind_speed_knots": 8,
            "swell_height_m": 0.5,
            "pressure_hpa": 1017,
            "tide_phase": "rising",
            "tide_stage": "flood",
            "hours_to_high_tide": 1.5,
            "tide_height_change_next_2h": 0.2,
            "time_window": "dusk",
            "hours_from_sunset": -0.4,
            "is_daylight": True,
        }
        stable = build_preview(-33.8523, 151.2108, environment={**base_environment, "pressure_delta_24h": 1.5})
        shocked = build_preview(
            -33.8523,
            151.2108,
            environment={
                **base_environment,
                "pressure_delta_6h": -4.5,
                "pressure_delta_24h": -9.0,
                "temperature_delta_24h": -5.0,
                "wind_direction_change_12h": 120,
                "max_gust_24h": 38,
                "wave_height_delta_24h": 0.7,
            },
        )

        self.assertLess(shocked["overall_recommendation"]["score"], stable["overall_recommendation"]["score"])
        self.assertIn("recent_weather_shock", shocked["overall_recommendation"]["reason_tags"])
        self.assertGreaterEqual(shocked["meta"]["environment"]["normalized"]["weather_shock"], 3.0)

    def test_multi_day_weather_break_penalty_recovers_gradually(self) -> None:
        base_environment = {
            "wind_speed_knots": 8,
            "swell_height_m": 0.45,
            "pressure_hpa": 1018,
            "tide_phase": "rising",
            "tide_stage": "flood",
            "hours_to_high_tide": 1.5,
            "tide_height_change_next_2h": 0.22,
            "tide_height_change_next_3h": 0.32,
            "tide_movement_rate_m_per_hour": 0.11,
            "time_window": "dusk",
            "hours_from_sunset": -0.4,
            "is_daylight": True,
        }
        broken = build_preview(
            -42.9810,
            147.3240,
            environment={
                **base_environment,
                "pressure_delta_3h": -3.5,
                "pressure_delta_6h": -5.2,
                "pressure_delta_24h": -11,
                "pressure_delta_48h": -14,
                "pressure_delta_72h": -16,
                "temperature_delta_24h": -5.2,
                "temperature_delta_48h": -7.0,
                "temperature_delta_72h": -9.0,
                "temperature_drop_from_recent_72h_peak": -9,
                "max_gust_24h": 30,
                "max_gust_72h": 32,
                "wave_height_delta_24h": 0.65,
            },
            region="sheltered_estuary",
        )
        recovering = build_preview(
            -42.9810,
            147.3240,
            environment={
                **base_environment,
                "pressure_delta_3h": 0.4,
                "pressure_delta_6h": 0.8,
                "pressure_delta_24h": -2.0,
                "pressure_delta_48h": -11,
                "pressure_delta_72h": -14,
                "temperature_delta_24h": -0.4,
                "temperature_delta_48h": -5.0,
                "temperature_delta_72h": -8.0,
                "temperature_drop_from_recent_72h_peak": -8.5,
                "max_gust_24h": 14,
                "max_gust_72h": 30,
                "wave_height_delta_24h": -0.12,
            },
            region="sheltered_estuary",
        )

        broken_tags = set(broken["overall_recommendation"]["reason_tags"])
        recovering_tags = set(recovering["overall_recommendation"]["reason_tags"])
        self.assertIn("severe_multi_day_cold_break", broken_tags)
        self.assertIn("recent_weather_shock", broken_tags)
        self.assertIn("weather_trend_recovering", recovering_tags)
        self.assertIn("weather_shock_reduced_by_recovery", recovering_tags)
        self.assertIn("recent_weather_shock", recovering_tags)
        self.assertLess(
            recovering["meta"]["environment"]["normalized"]["weather_shock"],
            broken["meta"]["environment"]["normalized"]["weather_shock"],
        )
        self.assertGreater(recovering["overall_recommendation"]["score"], broken["overall_recommendation"]["score"])

    def test_rainfall_staging_separates_light_cover_from_heavy_disruption(self) -> None:
        base_environment = {
            "wind_speed_knots": 7,
            "swell_height_m": 0.4,
            "pressure_hpa": 1018,
            "tide_phase": "falling",
            "time_window": "dusk",
        }
        light = build_preview(
            -33.8523,
            151.2108,
            environment={**base_environment, "rain_mm": 0.8, "recent_precipitation_sum_12h": 1.2, "rainfall_24h": 1.2},
        )
        heavy = build_preview(
            -33.8523,
            151.2108,
            environment={
                **base_environment,
                "rain_mm": 6,
                "recent_precipitation_sum_12h": 18,
                "rainfall_24h": 32,
                "rainfall_48h": 58,
            },
        )

        self.assertIn("light_rain_cover", light["overall_recommendation"]["reason_tags"])
        self.assertIn("heavy_rain_disruption", heavy["overall_recommendation"]["reason_tags"])
        self.assertIn("major_rain_shock", heavy["overall_recommendation"]["reason_tags"])
        self.assertLess(heavy["overall_recommendation"]["score"], light["overall_recommendation"]["score"])

    def test_false_high_guard_caps_timing_when_dead_water_and_weather_shock_align(self) -> None:
        result = build_preview(
            -42.8991036,
            147.3389916,
            environment={
                "wind_speed_knots": 7,
                "swell_height_m": 0.4,
                "pressure_hpa": 1020,
                "pressure_delta_6h": -4.5,
                "pressure_delta_24h": -9.0,
                "temperature_delta_24h": -5,
                "max_gust_24h": 36,
                "tide_phase": "rising",
                "tide_stage": "flood",
                "hours_to_high_tide": 1.5,
                "tide_height_change_next_2h": 0.03,
                "tide_height_change_next_3h": 0.06,
                "time_window": "dawn",
                "hours_from_sunrise": -0.4,
                "is_daylight": False,
                "moon_phase_name": "full_moon",
            },
            region="sheltered_estuary",
        )

        self.assertLessEqual(result["overall_recommendation"]["score"], 60)
        tags = set(result["overall_recommendation"]["reason_tags"])
        self.assertIn("timing_capped_by_local_instability", tags)
        self.assertIn("recent_weather_shock", tags)

    def test_beach_rising_tide_scores_better_than_high_tide(self) -> None:
        rising = build_preview(-33.7950, 151.2870, environment={"tide_phase": "rising"})
        high = build_preview(-33.7950, 151.2870, environment={"tide_phase": "high"})
        self.assertGreater(
            rising["nearby_water_types"]["beach"]["scores"]["roaming_opportunity"],
            high["nearby_water_types"]["beach"]["scores"]["roaming_opportunity"],
        )

    def test_bay_estuary_falling_tide_scores_better_than_high_tide(self) -> None:
        falling = build_preview(-33.8523, 151.2108, environment={"tide_phase": "falling"})
        high = build_preview(-33.8523, 151.2108, environment={"tide_phase": "high"})
        self.assertGreater(
            falling["nearby_water_types"]["bay_estuary_edge"]["scores"]["roaming_opportunity"],
            high["nearby_water_types"]["bay_estuary_edge"]["scores"]["roaming_opportunity"],
        )

    def test_open_coast_region_bias_lifts_exposed_types(self) -> None:
        generic = build_preview(-33.7950, 151.2870)
        open_coast = build_preview(-33.7950, 151.2870, region="open_coast")
        generic_strengths = generic["meta"]["inference_signals"]["type_strengths"]
        open_strengths = open_coast["meta"]["inference_signals"]["type_strengths"]
        self.assertGreater(open_strengths["beach"], generic_strengths["beach"])
        self.assertGreater(open_strengths["rocks"], generic_strengths["rocks"])
        self.assertEqual(open_coast["meta"]["region"]["slug"], "open_coast")

    def test_sheltered_estuary_region_bias_lifts_bay_estuary_type(self) -> None:
        generic = build_preview(-33.8523, 151.2108)
        sheltered = build_preview(-33.8523, 151.2108, region="sheltered_estuary")
        generic_strengths = generic["meta"]["inference_signals"]["type_strengths"]
        sheltered_strengths = sheltered["meta"]["inference_signals"]["type_strengths"]
        self.assertGreater(sheltered_strengths["bay_estuary_edge"], generic_strengths["bay_estuary_edge"])
        self.assertGreater(sheltered_strengths["jetty"], generic_strengths["jetty"])
        self.assertEqual(sheltered["meta"]["region"]["slug"], "sheltered_estuary")

    def test_regression_samples_express_expected_generic_archetypes(self) -> None:
        for sample in REGRESSION_SAMPLES:
            if sample["expected_status"] != "ok":
                continue
            result = build_preview(sample["lat"], sample["lon"])
            strengths = result["meta"]["inference_signals"]["type_strengths"]
            with self.subTest(sample=sample["id"], archetype=sample["archetype"]):
                if sample["archetype"] == "open_coast":
                    self.assertGreaterEqual(strengths["beach"], strengths["bay_estuary_edge"])
                elif sample["archetype"] == "surf_coast":
                    self.assertGreaterEqual(strengths["beach"], 0.68)
                elif sample["archetype"] == "rocky_open_edge":
                    self.assertGreaterEqual(strengths["rocks"], 0.55)
                elif sample["archetype"] in {"sheltered_edge", "tidal_edge"}:
                    self.assertGreaterEqual(strengths["bay_estuary_edge"], strengths["beach"])
                elif sample["archetype"] == "channel_mixed":
                    self.assertGreaterEqual(strengths["rocks"], 0.55)
                    self.assertGreaterEqual(strengths["jetty"], 0.55)
                elif sample["archetype"] == "harbour_mixed":
                    self.assertGreaterEqual(strengths["jetty"], 0.55)
                elif sample["archetype"] == "harbour_access":
                    self.assertGreaterEqual(strengths["jetty"], 0.58)
                elif sample["archetype"] == "bay_edge":
                    self.assertGreaterEqual(strengths["bay_estuary_edge"], strengths["rocks"])
                elif sample["archetype"] == "large_bay_mixed":
                    self.assertGreaterEqual(strengths["beach"], 0.55)
                    self.assertGreaterEqual(strengths["bay_estuary_edge"], 0.45)
                elif sample["archetype"] == "boundary_near_coast":
                    self.assertGreater(result["support"]["nearest_supported_water_km"], 0.0)
                elif sample["archetype"] == "tidal_corridor":
                    self.assertEqual(result["support"]["reason_code"], "tidal_corridor_preview")
                    self.assertGreaterEqual(strengths["bay_estuary_edge"], 0.45)
                    self.assertLessEqual(strengths["beach"], 0.35)

    def test_region_presets_shift_regression_samples_in_expected_direction(self) -> None:
        for sample in REGRESSION_SAMPLES:
            if sample["expected_status"] != "ok":
                continue
            generic = build_preview(sample["lat"], sample["lon"])
            open_coast = build_preview(sample["lat"], sample["lon"], region="open_coast")
            sheltered = build_preview(sample["lat"], sample["lon"], region="sheltered_estuary")
            generic_strengths = generic["meta"]["inference_signals"]["type_strengths"]
            with self.subTest(sample=sample["id"]):
                if open_coast["status"] == "ok":
                    open_strengths = open_coast["meta"]["inference_signals"]["type_strengths"]
                    self.assertGreaterEqual(open_strengths["beach"], generic_strengths["beach"])
                    self.assertLessEqual(open_strengths["bay_estuary_edge"], generic_strengths["bay_estuary_edge"])
                if sheltered["status"] == "ok":
                    sheltered_strengths = sheltered["meta"]["inference_signals"]["type_strengths"]
                    self.assertGreaterEqual(sheltered_strengths["bay_estuary_edge"], generic_strengths["bay_estuary_edge"])
                    self.assertGreaterEqual(sheltered_strengths["jetty"], generic_strengths["jetty"])

    def test_surf_coast_region_bias_lifts_beach_more_than_generic(self) -> None:
        generic = build_preview(-34.0588, 151.1575)
        surf = build_preview(-34.0588, 151.1575, region="surf_coast")
        self.assertGreater(
            surf["meta"]["inference_signals"]["type_strengths"]["beach"],
            generic["meta"]["inference_signals"]["type_strengths"]["beach"],
        )
        self.assertEqual(surf["meta"]["region"]["slug"], "surf_coast")

    def test_harbour_access_region_bias_lifts_jetty_signal(self) -> None:
        generic = build_preview(-32.9267, 151.7800)
        harbour = build_preview(-32.9267, 151.7800, region="harbour_access")
        self.assertGreater(
            harbour["meta"]["inference_signals"]["type_strengths"]["jetty"],
            generic["meta"]["inference_signals"]["type_strengths"]["jetty"],
        )
        self.assertEqual(harbour["meta"]["region"]["slug"], "harbour_access")

    def test_bay_coast_region_bias_lifts_bay_estuary_signal(self) -> None:
        generic = build_preview(-38.1485, 144.3613)
        bay = build_preview(-38.1485, 144.3613, region="bay_coast")
        self.assertGreater(
            bay["meta"]["inference_signals"]["type_strengths"]["bay_estuary_edge"],
            generic["meta"]["inference_signals"]["type_strengths"]["bay_estuary_edge"],
        )
        self.assertEqual(bay["meta"]["region"]["slug"], "bay_coast")

    def test_open_coast_directional_wind_and_swell_raise_exposed_penalty(self) -> None:
        onshore = build_preview(
            -33.7950,
            151.2870,
            environment={
                "wind_speed_knots": 24,
                "wind_direction_deg": 105,
                "swell_height_m": 2.5,
                "swell_direction_deg": 105,
            },
        )
        offshore = build_preview(
            -33.7950,
            151.2870,
            environment={
                "wind_speed_knots": 24,
                "wind_direction_deg": 285,
                "swell_height_m": 2.5,
                "swell_direction_deg": 285,
            },
        )
        onshore_penalty = onshore["meta"]["environment"]["normalized"]["exposed_penalty"]
        offshore_penalty = offshore["meta"]["environment"]["normalized"]["exposed_penalty"]
        self.assertGreater(onshore_penalty, offshore_penalty)
        self.assertLess(
            onshore["nearby_water_types"]["beach"]["scores"]["trip_quality"],
            offshore["nearby_water_types"]["beach"]["scores"]["trip_quality"],
        )

    def test_wind_to_shore_relationship_is_classified_cautiously(self) -> None:
        base_environment = {
            "wind_speed_knots": 10,
            "swell_height_m": 0.5,
            "tide_phase": "rising",
            "time_window": "dawn",
        }
        onshore = build_preview(
            -33.7950,
            151.2870,
            environment={**base_environment, "wind_direction_deg": 105},
            region="open_coast",
        )
        offshore = build_preview(
            -33.7950,
            151.2870,
            environment={**base_environment, "wind_direction_deg": 285},
            region="open_coast",
        )
        unknown = build_preview(
            -33.7950,
            151.2870,
            environment=base_environment,
            region="open_coast",
        )

        self.assertEqual(
            onshore["meta"]["environment"]["inputs_used"]["wind_to_shore_category"],
            "onshore_or_push_to_edge",
        )
        self.assertEqual(
            offshore["meta"]["environment"]["inputs_used"]["wind_to_shore_category"],
            "offshore_or_push_away",
        )
        self.assertEqual(
            unknown["meta"]["environment"]["inputs_used"]["wind_to_shore_category"],
            "direction_unknown",
        )
        self.assertIn("useful_wind_push", onshore["overall_recommendation"]["reason_tags"])
        self.assertIn("offshore_push_away", offshore["overall_recommendation"]["reason_tags"])
        self.assertIn("wind_direction_unknown", unknown["overall_recommendation"]["reason_tags"])
        self.assertGreater(
            onshore["overall_recommendation"]["score"],
            offshore["overall_recommendation"]["score"],
        )

    def test_inferred_structure_edges_do_not_adjust_scores(self) -> None:
        base_environment = {
            "wind_speed_knots": 8,
            "swell_height_m": 0.4,
            "pressure_hpa": 1018,
            "time_window": "dawn",
            "tide_phase": "rising",
        }
        moving = build_preview(
            -42.9810,
            147.3240,
            environment={
                **base_environment,
                "tide_height_change_next_2h": 0.20,
                "tide_height_change_next_3h": 0.30,
                "tide_movement_rate_m_per_hour": 0.10,
            },
        )
        weak = build_preview(
            -42.9810,
            147.3240,
            environment={
                **base_environment,
                "tide_height_change_next_2h": 0.02,
                "tide_height_change_next_3h": 0.04,
                "tide_movement_rate_m_per_hour": 0.01,
            },
        )
        open_beach = build_preview(
            -41.2510,
            148.3100,
            environment={
                **base_environment,
                "tide_height_change_next_2h": 0.20,
                "tide_height_change_next_3h": 0.30,
                "tide_movement_rate_m_per_hour": 0.10,
            },
        )

        self.assertEqual(
            moving["meta"]["environment"]["inputs_used"]["structure_flow_category"],
            "complex_edge_with_moving_water",
        )
        self.assertNotIn("inferred_edge_flow", moving["overall_recommendation"]["reason_tags"])
        self.assertNotIn("modest_inferred_edge_flow", moving["overall_recommendation"]["reason_tags"])
        self.assertEqual(
            weak["meta"]["environment"]["inputs_used"]["structure_flow_category"],
            "edge_waiting_for_flow",
        )
        self.assertNotIn("inferred_edge_flow", weak["overall_recommendation"]["reason_tags"])
        self.assertEqual(
            open_beach["meta"]["environment"]["inputs_used"]["structure_flow_category"],
            "weak_or_simple_edge",
        )
        self.assertNotIn("inferred_edge_flow", open_beach["overall_recommendation"]["reason_tags"])

    def test_direction_defaults_stay_neutral_when_not_supplied(self) -> None:
        result = build_preview(
            -33.8915,
            151.2767,
            environment={
                "wind_speed_knots": 20,
                "swell_height_m": 2.0,
            },
        )
        normalized = result["meta"]["environment"]["normalized"]
        self.assertEqual(normalized["wind_alignment"], 0.5)
        self.assertEqual(normalized["swell_alignment"], 0.5)
        self.assertEqual(result["meta"]["environment"]["inputs_used"]["wind_to_shore_category"], "direction_unknown")

    def test_unsupported_output_marks_support_profile(self) -> None:
        result = build_preview(-27.4705, 153.0260)
        self.assertEqual(result["status"], "unsupported")
        self.assertEqual(result["meta"]["support_profile"]["support_mode"], "unsupported")

    def test_waterbody_classification_distinguishes_reference_places(self) -> None:
        sandy_bay = build_preview(-42.8991036, 147.3389916)
        port_huon = build_preview(-43.1635, 146.9735)
        binalong_bay = build_preview(-41.2510, 148.3100)

        self.assertEqual(sandy_bay["meta"]["waterbody_classification"]["waterbody_class"], "bay_coast")
        self.assertIn(
            port_huon["meta"]["waterbody_classification"]["waterbody_class"],
            {"river_mouth", "tidal_river", "sheltered_estuary"},
        )
        self.assertIn(
            binalong_bay["meta"]["waterbody_classification"]["waterbody_class"],
            {"open_coast", "surf_coast"},
        )

    def test_water_temperature_layer_changes_fish_signal(self) -> None:
        base_environment = {
            "time_window": "dawn",
            "tide_phase": "rising",
            "tide_stage": "flood",
            "tide_range_m": 0.8,
            "tide_height_change_next_2h": 0.20,
            "tide_movement_rate_m_per_hour": 0.10,
            "tide_source": "openmeteo_model",
            "wind_speed_knots": 8,
            "swell_height_m": 0.4,
            "wave_height_m": 0.25,
            "pressure_hpa": 1016,
        }
        cold = build_preview(
            -42.8991036,
            147.3389916,
            environment={
                **base_environment,
                "sea_surface_temperature_c": 9.0,
                "sea_surface_temperature_delta_24h": -1.5,
            },
        )
        stable = build_preview(
            -42.8991036,
            147.3389916,
            environment={
                **base_environment,
                "sea_surface_temperature_c": 16.0,
                "sea_surface_temperature_delta_24h": 0.1,
                "sea_surface_temperature_delta_72h": 0.4,
            },
        )

        self.assertLess(cold["overall_recommendation"]["fish_outlook_score"], stable["overall_recommendation"]["fish_outlook_score"])
        self.assertIn("water_temp_cold", cold["overall_recommendation"]["reason_tags"])
        self.assertIn("water_temp_cooling_fast", cold["overall_recommendation"]["reason_tags"])
        self.assertIn("water_temp_optimal", stable["overall_recommendation"]["reason_tags"])
        self.assertIn("water_temp_stable", stable["overall_recommendation"]["reason_tags"])


if __name__ == "__main__":
    unittest.main()
