"""Tests for feedback collection (Phase A of empirical calibration loop)."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from coastal_fishing_forecast.feedback import (
    FEEDBACK_SCHEMA_VERSION,
    FeedbackValidationError,
    read_feedback,
    record_feedback,
    resolve_feedback_path,
    validate_feedback_payload,
)


def _valid_payload(**overrides) -> dict:
    base = {
        "trip_date": "2026-05-08",
        "trip_window": "morning",
        "lat": -42.8915,
        "lon": 147.3320,
        "region": "sheltered_estuary",
        "predicted": {
            "score": 65,
            "fish_outlook_score": 67,
            "comfort_score": 70,
            "safety_flag": "low",
            "dominant_water_type": "bay_estuary_edge",
            "key_reason_tags": ["sunrise_window", "rising_tide_window"],
        },
        "outcome": "decent",
    }
    base.update(overrides)
    return base


class ValidateFeedbackPayloadTests(unittest.TestCase):
    def test_minimal_payload_is_valid(self) -> None:
        payload = {
            "trip_date": "2026-05-08",
            "trip_window": "morning",
            "lat": -42.0,
            "lon": 147.0,
            "predicted": {"score": 60},
            "outcome": "ok",
        }
        validate_feedback_payload(payload)

    def test_missing_required_field_fails(self) -> None:
        for missing_key in ("trip_date", "trip_window", "lat", "lon", "outcome"):
            payload = _valid_payload()
            del payload[missing_key]
            with self.assertRaises(FeedbackValidationError):
                validate_feedback_payload(payload)

    def test_bad_trip_date_format_fails(self) -> None:
        with self.assertRaises(FeedbackValidationError):
            validate_feedback_payload(_valid_payload(trip_date="May 8 2026"))

    def test_bad_trip_window_fails(self) -> None:
        with self.assertRaises(FeedbackValidationError):
            validate_feedback_payload(_valid_payload(trip_window="midnight_snack"))

    def test_out_of_range_coordinates_fail(self) -> None:
        with self.assertRaises(FeedbackValidationError):
            validate_feedback_payload(_valid_payload(lat=91))
        with self.assertRaises(FeedbackValidationError):
            validate_feedback_payload(_valid_payload(lon=181))

    def test_non_numeric_coordinates_fail(self) -> None:
        with self.assertRaises(FeedbackValidationError):
            validate_feedback_payload(_valid_payload(lat="not-a-number"))

    def test_bad_outcome_fails(self) -> None:
        with self.assertRaises(FeedbackValidationError):
            validate_feedback_payload(_valid_payload(outcome="amazing_day"))

    def test_predicted_must_be_dict(self) -> None:
        with self.assertRaises(FeedbackValidationError):
            validate_feedback_payload(_valid_payload(predicted="65"))

    def test_predicted_score_required(self) -> None:
        with self.assertRaises(FeedbackValidationError):
            validate_feedback_payload(_valid_payload(predicted={"fish_outlook_score": 67}))

    def test_predicted_score_must_be_int_like(self) -> None:
        with self.assertRaises(FeedbackValidationError):
            validate_feedback_payload(_valid_payload(predicted={"score": "high"}))

    def test_invalid_safety_flag_fails(self) -> None:
        payload = _valid_payload()
        payload["predicted"]["safety_flag"] = "crazy_dangerous"
        with self.assertRaises(FeedbackValidationError):
            validate_feedback_payload(payload)

    def test_long_notes_fails(self) -> None:
        with self.assertRaises(FeedbackValidationError):
            validate_feedback_payload(_valid_payload(outcome_notes="a" * 200))

    def test_non_string_notes_fails(self) -> None:
        with self.assertRaises(FeedbackValidationError):
            validate_feedback_payload(_valid_payload(outcome_notes=42))


class RecordFeedbackTests(unittest.TestCase):
    def test_record_appends_jsonl_with_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "feedback.jsonl"
            result = record_feedback(_valid_payload(), path=path)
            self.assertEqual(result["schema_version"], FEEDBACK_SCHEMA_VERSION)
            self.assertIn("report_id", result)
            self.assertIn("submitted_at", result)
            self.assertEqual(result["outcome"], "decent")

            rows = read_feedback(path=path)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["report_id"], result["report_id"])

    def test_record_creates_parent_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "deep" / "nested" / "feedback.jsonl"
            record_feedback(_valid_payload(), path=path)
            self.assertTrue(path.exists())

    def test_multiple_records_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "feedback.jsonl"
            record_feedback(_valid_payload(outcome="great"), path=path)
            record_feedback(_valid_payload(outcome="skunked"), path=path)
            record_feedback(_valid_payload(outcome="ok"), path=path)

            rows = read_feedback(path=path)
            self.assertEqual([r["outcome"] for r in rows], ["great", "skunked", "ok"])

    def test_invalid_payload_does_not_create_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "feedback.jsonl"
            with self.assertRaises(FeedbackValidationError):
                record_feedback({"trip_window": "morning"}, path=path)
            self.assertFalse(path.exists())

    def test_record_id_persists_when_supplied(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "feedback.jsonl"
            payload = _valid_payload(report_id="my-uuid-1234")
            result = record_feedback(payload, path=path)
            self.assertEqual(result["report_id"], "my-uuid-1234")

    def test_now_override_used_for_submitted_at(self) -> None:
        fixed = datetime(2026, 5, 8, 12, 0, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "feedback.jsonl"
            result = record_feedback(_valid_payload(), path=path, now=fixed)
            self.assertEqual(result["submitted_at"], "2026-05-08T12:00:00+00:00")

    def test_predicted_block_preserved_verbatim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "feedback.jsonl"
            payload = _valid_payload(
                predicted={
                    "score": 75,
                    "fish_outlook_score": 76,
                    "comfort_score": 70,
                    "safety_flag": "moderate",
                    "safety_factors": ["notable_wave_activity"],
                    "combo_release": "rare_alignment_window",
                    "dominant_water_type": "jetty",
                    "key_reason_tags": ["sunrise_window", "early_flood_bonus"],
                }
            )
            result = record_feedback(payload, path=path)

            rows = read_feedback(path=path)
            self.assertEqual(rows[0]["predicted"], result["predicted"])
            self.assertEqual(rows[0]["predicted"]["combo_release"], "rare_alignment_window")
            self.assertEqual(rows[0]["predicted"]["safety_factors"], ["notable_wave_activity"])

    def test_outcome_notes_optional_and_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "feedback.jsonl"
            payload = _valid_payload(outcome_notes="Two flathead at the marina, slack tide.")
            result = record_feedback(payload, path=path)
            self.assertEqual(result["outcome_notes"], "Two flathead at the marina, slack tide.")


class ReadFeedbackTests(unittest.TestCase):
    def test_missing_file_returns_empty_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "no_such.jsonl"
            self.assertEqual(read_feedback(path=path), [])

    def test_blank_lines_are_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "feedback.jsonl"
            record_feedback(_valid_payload(), path=path)
            with path.open("a") as handle:
                handle.write("\n\n")
            record_feedback(_valid_payload(outcome="great"), path=path)

            rows = read_feedback(path=path)
            self.assertEqual(len(rows), 2)

    def test_corrupt_jsonl_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "feedback.jsonl"
            path.write_text("{not valid json}\n")
            with self.assertRaises(FeedbackValidationError):
                read_feedback(path=path)


class ResolveFeedbackPathTests(unittest.TestCase):
    def test_explicit_path_wins(self) -> None:
        explicit = Path("/tmp/explicit.jsonl")
        self.assertEqual(resolve_feedback_path(explicit), explicit)

    def test_env_override(self) -> None:
        import os

        original = os.environ.get("COASTAL_FORECAST_FEEDBACK_PATH")
        try:
            os.environ["COASTAL_FORECAST_FEEDBACK_PATH"] = "/tmp/env_path.jsonl"
            self.assertEqual(resolve_feedback_path(), Path("/tmp/env_path.jsonl"))
        finally:
            if original is None:
                os.environ.pop("COASTAL_FORECAST_FEEDBACK_PATH", None)
            else:
                os.environ["COASTAL_FORECAST_FEEDBACK_PATH"] = original


if __name__ == "__main__":
    unittest.main()
