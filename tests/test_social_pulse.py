import csv
import tempfile
import unittest
from datetime import date
from pathlib import Path

from coastal_fishing_forecast.social_pulse import build_social_pulse


class SocialPulseTests(unittest.TestCase):
    def test_social_pulse_summarizes_recent_nearby_signals_as_context_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            data_dir = Path(tmp_dir)
            with (data_dir / "social_signals.csv").open("w", encoding="utf-8", newline="") as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=[
                        "date",
                        "source_platform",
                        "normalized_area",
                        "shore_vs_boat",
                        "species_mentions",
                        "evidence_confidence",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "date": "2026-04-19",
                        "source_platform": "facebook",
                        "normalized_area": "binalong_bay",
                        "shore_vs_boat": "shore",
                        "species_mentions": "australian_salmon;kingfish",
                        "evidence_confidence": "high",
                    }
                )
                writer.writerow(
                    {
                        "date": "2026-04-15",
                        "source_platform": "xiaohongshu",
                        "normalized_area": "east_coast_tasmania",
                        "shore_vs_boat": "unknown",
                        "species_mentions": "squid",
                        "evidence_confidence": "medium",
                    }
                )
                writer.writerow(
                    {
                        "date": "2025-12-01",
                        "source_platform": "facebook",
                        "normalized_area": "binalong_bay",
                        "shore_vs_boat": "shore",
                        "species_mentions": "old_signal",
                        "evidence_confidence": "high",
                    }
                )

            pulse = build_social_pulse(
                -41.2530,
                148.3060,
                data_dir=data_dir,
                today=date(2026, 5, 1),
                recent_days=45,
            )

        self.assertTrue(pulse["available"])
        self.assertEqual(pulse["role"], "context_only")
        self.assertFalse(pulse["score_adjustment_allowed"])
        self.assertEqual(pulse["nearest_signal_area"], "binalong_bay")
        self.assertEqual(pulse["latest_signal_date"], "2026-04-19")
        self.assertEqual(pulse["recent_report_count"], 2)
        self.assertGreater(pulse["pulse_score"], 0)
        self.assertNotEqual(pulse["pulse_level"], "none")
        self.assertEqual(pulse["platforms"][0]["platform"], "facebook")
        species = {item["species"] for item in pulse["top_species"]}
        self.assertIn("australian_salmon", species)
        self.assertNotIn("old_signal", species)

    def test_social_pulse_is_safe_when_legacy_file_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            pulse = build_social_pulse(
                -41.2530,
                148.3060,
                data_dir=Path(tmp_dir),
                today=date(2026, 5, 1),
            )

        self.assertFalse(pulse["available"])
        self.assertEqual(pulse["role"], "context_only")
        self.assertFalse(pulse["score_adjustment_allowed"])
        self.assertEqual(pulse["recent_report_count"], 0)
        self.assertEqual(pulse["pulse_level"], "none")


if __name__ == "__main__":
    unittest.main()
