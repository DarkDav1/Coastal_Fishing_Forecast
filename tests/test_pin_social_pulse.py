"""Tests for pin-level social pulse.

Locks the contract that pin_forecast carries a compact `recent_social_pulse`
sub-object derived from the same crawler data as build_social_pulse, but
with the smaller per-pin window and a stable shape suitable for a map
badge. Crucially: pin pulse is never allowed to adjust the score
(`score_adjustment_allowed: False`).
"""

from __future__ import annotations

import csv
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from coastal_fishing_forecast.api import _pin_forecast, build_frontend_forecast_response
from coastal_fishing_forecast.social_pulse import (
    PIN_PULSE_RECENT_DAYS,
    PIN_PULSE_TOP_SPECIES,
    build_compact_pin_pulse,
    default_social_data_dir,
)
from test_forecast import _fixture_conditions


SIGNAL_FIELDS = (
    "date",
    "source_platform",
    "normalized_area",
    "shore_vs_boat",
    "species_mentions",
    "evidence_confidence",
)


def _write_signals(data_dir: Path, rows: list[dict[str, str]]) -> None:
    target = data_dir / "social_signals.csv"
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(SIGNAL_FIELDS))
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in SIGNAL_FIELDS})


class CompactPinPulseTests(unittest.TestCase):
    def test_no_data_returns_none_level_and_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pulse = build_compact_pin_pulse(
                -42.9000,
                147.3350,
                data_dir=Path(tmp),
                today=date(2026, 5, 1),
            )
        self.assertFalse(pulse["available"])
        self.assertEqual(pulse["level"], "none")
        self.assertEqual(pulse["report_count"], 0)
        self.assertEqual(pulse["top_species"], [])
        self.assertFalse(pulse["score_adjustment_allowed"])
        self.assertEqual(pulse["source"], "context_only")
        # Even when unavailable, identity context is filled
        self.assertEqual(pulse["nearest_anchor"], "sandy_bay")

    def test_recent_local_signals_produce_pulse(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            _write_signals(
                data_dir,
                [
                    {
                        "date": "2026-04-19",
                        "source_platform": "facebook",
                        "normalized_area": "sandy_bay",
                        "shore_vs_boat": "shore",
                        "species_mentions": "bream;flathead",
                        "evidence_confidence": "high",
                    },
                    {
                        "date": "2026-04-15",
                        "source_platform": "xiaohongshu",
                        "normalized_area": "derwent",
                        "shore_vs_boat": "shore",
                        "species_mentions": "bream",
                        "evidence_confidence": "medium",
                    },
                ],
            )
            pulse = build_compact_pin_pulse(
                -42.9000,
                147.3350,
                data_dir=data_dir,
                today=date(2026, 5, 1),
            )
        self.assertTrue(pulse["available"])
        self.assertNotEqual(pulse["level"], "none")
        self.assertEqual(pulse["report_count"], 2)
        self.assertIn("bream", pulse["top_species"])
        self.assertEqual(pulse["nearest_anchor"], "sandy_bay")

    def test_old_signals_outside_window_are_dropped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            _write_signals(
                data_dir,
                [
                    {
                        "date": "2024-01-01",  # ~2 years old
                        "source_platform": "facebook",
                        "normalized_area": "sandy_bay",
                        "shore_vs_boat": "shore",
                        "species_mentions": "trout",
                        "evidence_confidence": "high",
                    }
                ],
            )
            pulse = build_compact_pin_pulse(
                -42.9000,
                147.3350,
                data_dir=data_dir,
                today=date(2026, 5, 1),
            )
        self.assertFalse(pulse["available"])
        self.assertEqual(pulse["report_count"], 0)
        self.assertEqual(pulse["top_species"], [])

    def test_distant_areas_with_no_relation_are_dropped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            # Tamar river signals when searching Sandy Bay (different family).
            _write_signals(
                data_dir,
                [
                    {
                        "date": "2026-04-19",
                        "source_platform": "facebook",
                        "normalized_area": "tamar_river",
                        "shore_vs_boat": "shore",
                        "species_mentions": "bream",
                        "evidence_confidence": "high",
                    }
                ],
            )
            pulse = build_compact_pin_pulse(
                -42.9000,
                147.3350,
                data_dir=data_dir,
                today=date(2026, 5, 1),
            )
        # The default _area_relevance at >60km cross-family returns 0,
        # so nothing should match.
        self.assertFalse(pulse["available"])

    def test_top_species_capped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            rows = []
            for i, species in enumerate(("bream", "flathead", "salmon", "squid", "snapper")):
                rows.append(
                    {
                        "date": f"2026-04-{i + 10}",
                        "source_platform": "facebook",
                        "normalized_area": "sandy_bay",
                        "shore_vs_boat": "shore",
                        "species_mentions": species,
                        "evidence_confidence": "high",
                    }
                )
            _write_signals(data_dir, rows)
            pulse = build_compact_pin_pulse(
                -42.9000,
                147.3350,
                data_dir=data_dir,
                today=date(2026, 5, 1),
            )
        self.assertTrue(pulse["available"])
        self.assertLessEqual(len(pulse["top_species"]), PIN_PULSE_TOP_SPECIES)

    def test_score_adjustment_never_allowed_field(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            _write_signals(
                data_dir,
                [
                    {
                        "date": "2026-04-19",
                        "normalized_area": "sandy_bay",
                        "evidence_confidence": "high",
                        "shore_vs_boat": "shore",
                        "species_mentions": "bream",
                    }
                ],
            )
            pulse = build_compact_pin_pulse(
                -42.9000,
                147.3350,
                data_dir=data_dir,
                today=date(2026, 5, 1),
            )
        # Hard contract: never lets a caller set it to True.
        self.assertIs(pulse["score_adjustment_allowed"], False)
        self.assertEqual(pulse["source"], "context_only")

    def test_window_default_matches_constant(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pulse = build_compact_pin_pulse(
                -42.9000,
                147.3350,
                data_dir=Path(tmp),
                today=date(2026, 5, 1),
            )
        self.assertEqual(pulse["recent_window_days"], PIN_PULSE_RECENT_DAYS)


class DefaultSocialDataDirTests(unittest.TestCase):
    def test_prefers_repo_local_when_present(self) -> None:
        # The cloud agent has data/social_intel/ committed in main.
        # default_social_data_dir should pick repo-local first when it
        # exists; otherwise fall back to the legacy sibling layout.
        path = default_social_data_dir()
        self.assertIsInstance(path, Path)
        # Both choices end with social_intel
        self.assertEqual(path.name, "social_intel")


class PinForecastSocialPulseIntegrationTests(unittest.TestCase):
    def test_pin_forecast_includes_recent_social_pulse_field(self) -> None:
        env = {
            "wind_speed_knots": 6,
            "swell_height_m": 0.4,
            "wave_height_m": 0.4,
            "tide_phase": "rising",
            "tide_stage": "flood",
            "hours_to_high_tide": 1.5,
            "tide_height_change_next_2h": 0.2,
            "time_window": "dawn",
        }
        result = _pin_forecast(
            pin_lat=-42.9000,
            pin_lon=147.3350,
            search_lat=-42.9000,
            search_lon=147.3350,
            environment=env,
            region="sheltered_estuary",
        )
        self.assertTrue(result["available"])
        self.assertIn("recent_social_pulse", result)
        pulse = result["recent_social_pulse"]
        self.assertIn("level", pulse)
        self.assertIn("report_count", pulse)
        self.assertIn("top_species", pulse)
        self.assertIn("score_adjustment_allowed", pulse)
        self.assertFalse(pulse["score_adjustment_allowed"])

    def test_pin_forecast_pulse_uses_pin_coord_not_search_center(self) -> None:
        # Sandy Bay (search center, derwent family) and Binalong Bay (pin,
        # east coast family) should resolve to different nearest_anchor
        # entries — proving the pulse is computed at the pin coord.
        env = {
            "wind_speed_knots": 6,
            "swell_height_m": 0.4,
            "wave_height_m": 0.4,
            "tide_phase": "rising",
            "tide_stage": "flood",
            "hours_to_high_tide": 1.5,
            "tide_height_change_next_2h": 0.2,
            "time_window": "dawn",
        }
        sandy = _pin_forecast(
            pin_lat=-42.9000,
            pin_lon=147.3350,
            search_lat=-42.9000,
            search_lon=147.3350,
            environment=env,
            region="sheltered_estuary",
        )
        binalong = _pin_forecast(
            pin_lat=-41.2530,
            pin_lon=148.3060,
            search_lat=-42.9000,
            search_lon=147.3350,
            environment=env,
            region="sheltered_estuary",
        )
        self.assertNotEqual(
            sandy["recent_social_pulse"]["nearest_anchor"],
            binalong["recent_social_pulse"]["nearest_anchor"],
        )


class FrontendResponsePinPulseIntegrationTests(unittest.TestCase):
    def test_response_facilities_remain_context_only(self) -> None:
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
                    "id": "test:1",
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


if __name__ == "__main__":
    unittest.main()
