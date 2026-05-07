import unittest
from unittest.mock import patch

from coastal_fishing_forecast.github_models import GitHubModelsError
from coastal_fishing_forecast.planner import build_fishing_plan


def _payload(**overrides):
    payload = {
        "hero": {
            "score": 54,
            "best_window": {
                "time_window": "morning",
                "dominant_water_type": "beach",
                "score": 54,
                "behavior_groups": [{"label": "Beach roaming fish"}],
                "conditions": {
                    "wind": {"speed_knots": 8},
                    "swell": {"height_m": 1.0},
                    "tide": {"phase": "rising", "source": "openmeteo_model"},
                },
            },
        },
        "confidence": {"label": "medium", "score": 64},
        "tide_verification": {"status": "model_estimated", "source": "openmeteo_model"},
        "explanation": {
            "risks": ["Tide phase is inferred from model sea-level data, not a local tide station."],
            "alternatives": [{"label": "Estuary edge", "score": 52}],
        },
    }
    payload.update(overrides)
    return payload


class PlannerTests(unittest.TestCase):
    def test_supported_forecast_gets_action_plan_without_changing_score(self) -> None:
        payload = _payload()
        plan = build_fishing_plan(payload)

        self.assertEqual(plan["source"], "rule_based")
        self.assertEqual(plan["recommendation"]["score"], payload["hero"]["score"])
        self.assertEqual(plan["primary_action"]["water_type"], "beach")
        self.assertEqual(plan["backup_action"]["water_type"], "Estuary edge")
        self.assertFalse(plan["safety_rules"]["score_modified"])
        self.assertTrue(plan["safety_rules"]["terrain_claims_guarded"])
        self.assertIn("jetty", plan["terrain_certainty"]["forbidden_claims"])

    def test_low_confidence_plan_uses_cautious_preview_language(self) -> None:
        plan = build_fishing_plan(_payload(confidence={"label": "low", "score": 42}))

        self.assertEqual(plan["recommendation"]["label"], "maybe")
        self.assertIn("lower-confidence preview", plan["primary_action"]["text"])
        self.assertIn("Lower confidence", plan["confidence_note"])

    def test_rule_based_plan_softens_unconfirmed_structure_wording(self) -> None:
        payload = _payload()
        payload["hero"]["best_window"]["dominant_water_type"] = "jetty"
        payload["explanation"]["alternatives"] = [{"label": "Jetty / wharf", "score": 52}]

        plan = build_fishing_plan(payload)

        self.assertNotIn("jetty", plan["primary_action"]["text"].lower())
        self.assertNotIn("wharf", plan["backup_action"]["text"].lower())
        self.assertIn("structure-style edge", plan["primary_action"]["text"])

    def test_model_tide_warning_is_preserved(self) -> None:
        plan = build_fishing_plan(_payload())

        self.assertIn("model sea-level", plan["confidence_note"])
        self.assertIn("Open-Meteo model", plan["data_source_note"])

    def test_remote_station_warning_is_preserved(self) -> None:
        plan = build_fishing_plan(
            _payload(
                tide_verification={
                    "status": "live_verified_remote_station",
                    "source": "tidesatlas",
                    "station_distance_km": 100.0,
                }
            )
        )

        self.assertIn("distant station", plan["confidence_note"])
        self.assertIn("100.0 km", plan["data_source_note"])

    def test_unsupported_forecast_does_not_generate_fishing_advice(self) -> None:
        plan = build_fishing_plan(
            {
                "hero": {"best_window": None},
                "confidence": {"label": "unsupported", "score": 0},
                "tide_verification": {"status": "estimated"},
            }
        )

        self.assertEqual(plan["recommendation"]["label"], "skip")
        self.assertIsNone(plan["primary_action"]["water_type"])
        self.assertIn("supported coastal or tidal", plan["primary_action"]["text"])

    def test_llm_provider_falls_back_without_external_model(self) -> None:
        with patch(
            "coastal_fishing_forecast.planner.generate_github_models_plan_text",
            side_effect=GitHubModelsError("missing token"),
        ):
            plan = build_fishing_plan(_payload(), planner_provider="llm")

        self.assertEqual(plan["source"], "rule_based_fallback")
        self.assertEqual(plan["planner_provider"], "rule_based")

    def test_github_models_provider_uses_allowed_text_without_overwriting_scores(self) -> None:
        with patch(
            "coastal_fishing_forecast.planner.generate_github_models_plan_text",
            return_value={
                "recommendation_summary": "Use the morning window, but keep this as a preview.",
                "primary_action_text": "Start with the beach signal, then reassess locally.",
                "backup_action_text": "Shift to the estuary edge if the beach looks exposed.",
                "avoid": ["Do not treat this as a confirmed hotspot."],
                "risks": ["Model tide is not station verified."],
                "confidence_note": "Model-enhanced wording; forecast confidence is unchanged.",
                "data_source_note": "Uses forecast fields only.",
                "score": 99,
            },
        ):
            plan = build_fishing_plan(_payload(), planner_provider="github_models")

        self.assertEqual(plan["source"], "github_models")
        self.assertEqual(plan["planner_provider"], "github_models")
        self.assertEqual(plan["recommendation"]["score"], 54)
        self.assertEqual(plan["primary_action"]["score"], 54)
        self.assertEqual(plan["recommendation"]["summary"], "Use the morning window, but keep this as a preview.")
        self.assertEqual(plan["primary_action"]["text"], "Start with the beach signal, then reassess locally.")
        self.assertFalse(plan["safety_rules"]["score_modified"])
        self.assertTrue(plan["safety_rules"]["terrain_claims_guarded"])

    def test_github_models_provider_falls_back_on_unconfirmed_structure_claims(self) -> None:
        with patch(
            "coastal_fishing_forecast.planner.generate_github_models_plan_text",
            return_value={
                "recommendation_summary": "Fish the morning near jetties and wharves.",
                "primary_action_text": "Start beside the pier.",
            },
        ):
            plan = build_fishing_plan(_payload(), planner_provider="github_models")

        self.assertEqual(plan["source"], "rule_based_fallback")
        self.assertEqual(plan["planner_provider"], "rule_based")
        self.assertNotIn("pier", plan["primary_action"]["text"].lower())
        self.assertIn("jetty", plan["terrain_certainty"]["forbidden_claims"])

    def test_private_boat_ramp_does_not_allow_public_jetty_claims(self) -> None:
        payload = _payload(
            structure_facilities=[
                {"type": "boat_ramp", "access": "private", "status": "confirmed"},
            ]
        )
        with patch(
            "coastal_fishing_forecast.planner.generate_github_models_plan_text",
            return_value={"primary_action_text": "Fish beside the public jetty."},
        ):
            plan = build_fishing_plan(payload, planner_provider="github_models")

        self.assertEqual(plan["source"], "rule_based_fallback")
        self.assertIn("boat_ramp", plan["terrain_certainty"]["confirmed_features"])
        self.assertIn("public jetty", plan["terrain_certainty"]["forbidden_claims"])

    def test_public_jetty_allows_public_jetty_claims(self) -> None:
        payload = _payload(
            structure_facilities=[
                {"type": "public_jetty", "access": "public", "status": "confirmed"},
            ]
        )
        with patch(
            "coastal_fishing_forecast.planner.generate_github_models_plan_text",
            return_value={"primary_action_text": "Fish beside the mapped public jetty, then reassess."},
        ):
            plan = build_fishing_plan(payload, planner_provider="github_models")

        self.assertEqual(plan["source"], "github_models")
        self.assertIn("public_jetty", plan["terrain_certainty"]["confirmed_features"])
        self.assertNotIn("public jetty", plan["terrain_certainty"]["forbidden_claims"])
        self.assertIn("public jetty", plan["primary_action"]["text"])

    def test_github_models_provider_cannot_weaken_tide_source_warning(self) -> None:
        with patch(
            "coastal_fishing_forecast.planner.generate_github_models_plan_text",
            return_value={
                "confidence_note": "Confidence is medium.",
                "data_source_note": "Uses Open-Meteo data.",
                "risks": [],
            },
        ):
            plan = build_fishing_plan(_payload(), planner_provider="github_models")

        self.assertEqual(plan["source"], "github_models")
        self.assertIn("model sea-level", plan["confidence_note"])
        self.assertIn("not a local station", plan["data_source_note"])
        self.assertIn("not a local tide station", " ".join(plan["risks"]))

    def test_github_models_provider_falls_back_on_invalid_json_shape(self) -> None:
        with patch(
            "coastal_fishing_forecast.planner.generate_github_models_plan_text",
            return_value={"score": 100},
        ):
            plan = build_fishing_plan(_payload(), planner_provider="github_models")

        self.assertEqual(plan["source"], "rule_based_fallback")
        self.assertEqual(plan["planner_provider"], "rule_based")
        self.assertEqual(plan["recommendation"]["score"], 54)

    def test_github_models_provider_falls_back_on_adapter_error(self) -> None:
        with patch(
            "coastal_fishing_forecast.planner.generate_github_models_plan_text",
            side_effect=TimeoutError("timeout"),
        ):
            plan = build_fishing_plan(_payload(), planner_provider="github_models")

        self.assertEqual(plan["source"], "rule_based_fallback")
        self.assertEqual(plan["primary_action"]["water_type"], "beach")


if __name__ == "__main__":
    unittest.main()
