"""Tests for offline feedback analysis (Phase B of empirical calibration loop)."""

from __future__ import annotations

import unittest
from datetime import datetime

from coastal_fishing_forecast.feedback_analysis import (
    OUTCOME_TARGETS,
    PHASE_C_MIN_ROWS,
    PHASE_C_MIN_REGIONS,
    PHASE_C_MIN_DAYS_SPAN,
    _bias_summary,
    _date_span,
    _group_bias,
    _outcome_distribution,
    _phase_c_gate,
    _predicted_field_bias,
    _score_bucket_breakdown,
    _tag_enrichment,
    build_report,
    outcome_target,
    score_bucket,
    signed_deviation,
)


def _row(
    *,
    trip_date: str = "2026-04-20",
    region: str = "sheltered_estuary",
    score: int = 65,
    outcome: str = "ok",
    safety_flag: str = "low",
    dominant: str = "bay_estuary_edge",
    combo: str | None = None,
    tags: list[str] | None = None,
) -> dict:
    predicted = {
        "score": score,
        "safety_flag": safety_flag,
        "dominant_water_type": dominant,
        "key_reason_tags": tags or [],
    }
    if combo is not None:
        predicted["combo_release"] = combo
    return {
        "schema_version": "v1",
        "trip_date": trip_date,
        "trip_window": "morning",
        "lat": -42.89,
        "lon": 147.33,
        "region": region,
        "predicted": predicted,
        "outcome": outcome,
    }


class TargetAndDeviationTests(unittest.TestCase):
    def test_outcome_target_returns_known(self) -> None:
        for outcome, target in OUTCOME_TARGETS.items():
            self.assertEqual(outcome_target(outcome), target)

    def test_outcome_target_unknown_returns_none(self) -> None:
        self.assertIsNone(outcome_target("amazing_day"))

    def test_signed_deviation_positive_when_overpromised(self) -> None:
        # predicted=70, outcome=ok (target 45) -> +25
        self.assertEqual(signed_deviation(_row(score=70, outcome="ok")), 25)

    def test_signed_deviation_negative_when_underpromised(self) -> None:
        # predicted=60, outcome=great (target 85) -> -25
        self.assertEqual(signed_deviation(_row(score=60, outcome="great")), -25)

    def test_signed_deviation_returns_none_when_score_missing(self) -> None:
        row = _row()
        row["predicted"] = {}
        self.assertIsNone(signed_deviation(row))

    def test_signed_deviation_returns_none_for_unknown_outcome(self) -> None:
        self.assertIsNone(signed_deviation(_row(outcome="bad")))


class ScoreBucketTests(unittest.TestCase):
    def test_score_bucket_classifies_ranges(self) -> None:
        self.assertEqual(score_bucket(20), "< 50")
        self.assertEqual(score_bucket(49), "< 50")
        self.assertEqual(score_bucket(50), "50-64")
        self.assertEqual(score_bucket(64), "50-64")
        self.assertEqual(score_bucket(65), "65-79")
        self.assertEqual(score_bucket(79), "65-79")
        self.assertEqual(score_bucket(80), "80+")
        self.assertEqual(score_bucket(95), "80+")

    def test_score_bucket_handles_none(self) -> None:
        self.assertEqual(score_bucket(None), "unknown")


class DateSpanTests(unittest.TestCase):
    def test_date_span_inclusive(self) -> None:
        rows = [_row(trip_date="2026-04-20"), _row(trip_date="2026-04-25")]
        earliest, latest, days = _date_span(rows)
        self.assertEqual(earliest, "2026-04-20")
        self.assertEqual(latest, "2026-04-25")
        self.assertEqual(days, 6)

    def test_date_span_empty_returns_zero(self) -> None:
        self.assertEqual(_date_span([]), ("—", "—", 0))


class PhaseCGateTests(unittest.TestCase):
    def _meets_all_gates(self) -> list[dict]:
        rows: list[dict] = []
        regions = ["sheltered_estuary", "open_coast", "harbour_access"]
        for i in range(PHASE_C_MIN_ROWS):
            rows.append(
                _row(
                    trip_date=f"2026-04-{(i % 28) + 1:02d}",
                    region=regions[i % len(regions)],
                )
            )
        # Force a long span:
        rows[0]["trip_date"] = "2026-04-01"
        rows[-1]["trip_date"] = f"2026-05-{PHASE_C_MIN_DAYS_SPAN:02d}"
        return rows

    def test_phase_c_blocks_when_too_few_rows(self) -> None:
        ready, blockers = _phase_c_gate([_row()] * 3)
        self.assertFalse(ready)
        self.assertTrue(any("rows" in b for b in blockers))

    def test_phase_c_blocks_when_too_few_regions(self) -> None:
        rows = [_row(region="sheltered_estuary") for _ in range(PHASE_C_MIN_ROWS)]
        ready, blockers = _phase_c_gate(rows)
        self.assertFalse(ready)
        self.assertTrue(any("regions" in b for b in blockers))

    def test_phase_c_blocks_when_too_short_span(self) -> None:
        rows = [_row(trip_date="2026-04-20", region=f"r{i % 3}") for i in range(PHASE_C_MIN_ROWS)]
        ready, blockers = _phase_c_gate(rows)
        self.assertFalse(ready)
        self.assertTrue(any("days" in b for b in blockers))

    def test_phase_c_passes_when_all_thresholds_met(self) -> None:
        ready, blockers = _phase_c_gate(self._meets_all_gates())
        self.assertTrue(ready, f"Expected ready, got blockers: {blockers}")
        self.assertEqual(blockers, [])


class AggregationTests(unittest.TestCase):
    def test_outcome_distribution_counts_correctly(self) -> None:
        rows = [
            _row(outcome="ok"),
            _row(outcome="ok"),
            _row(outcome="great"),
            _row(outcome="skunked"),
        ]
        dist = _outcome_distribution(rows)
        self.assertEqual(dist["ok"], 2)
        self.assertEqual(dist["great"], 1)
        self.assertEqual(dist["skunked"], 1)

    def test_bias_summary_no_data_returns_n_zero(self) -> None:
        self.assertEqual(_bias_summary([]), {"n": 0})

    def test_bias_summary_calculates_mean_median_abs(self) -> None:
        # deviations: +25, -25, 0
        rows = [
            _row(score=70, outcome="ok"),  # +25
            _row(score=60, outcome="great"),  # -25
            _row(score=65, outcome="decent"),  # 0
        ]
        summary = _bias_summary(rows)
        self.assertEqual(summary["n"], 3)
        self.assertEqual(summary["mean"], 0.0)
        self.assertEqual(summary["median"], 0.0)
        self.assertAlmostEqual(summary["mean_abs"], 50 / 3, places=1)

    def test_score_bucket_breakdown_distributes_correctly(self) -> None:
        rows = [
            _row(score=82, outcome="great"),
            _row(score=68, outcome="decent"),
            _row(score=68, outcome="skunked"),
            _row(score=55, outcome="ok"),
        ]
        buckets = _score_bucket_breakdown(rows)
        self.assertEqual(buckets["80+"]["great"], 1)
        self.assertEqual(buckets["65-79"]["decent"], 1)
        self.assertEqual(buckets["65-79"]["skunked"], 1)
        self.assertEqual(buckets["50-64"]["ok"], 1)

    def test_group_bias_aggregates_by_region(self) -> None:
        rows = [
            _row(region="open_coast", score=80, outcome="skunked"),  # +60
            _row(region="open_coast", score=80, outcome="skunked"),  # +60
            _row(region="sheltered_estuary", score=65, outcome="decent"),  # 0
        ]
        result = _group_bias(rows, "region")
        self.assertEqual(result["open_coast"]["n"], 2)
        self.assertEqual(result["open_coast"]["mean_dev"], 60.0)
        self.assertEqual(result["sheltered_estuary"]["mean_dev"], 0.0)

    def test_predicted_field_bias_aggregates_by_safety_flag(self) -> None:
        rows = [
            _row(safety_flag="low", score=65, outcome="decent"),  # 0
            _row(safety_flag="elevated", score=80, outcome="skunked"),  # +60
        ]
        result = _predicted_field_bias(rows, "safety_flag")
        self.assertEqual(result["low"]["mean_dev"], 0.0)
        self.assertEqual(result["elevated"]["mean_dev"], 60.0)


class TagEnrichmentTests(unittest.TestCase):
    def test_tag_enrichment_finds_top_tags(self) -> None:
        rows = [
            _row(outcome="great", tags=["sunrise_window", "rising_tide_window"]),
            _row(outcome="great", tags=["sunrise_window", "stable_pressure_bonus"]),
            _row(outcome="ok", tags=["plain_day_penalty"]),
        ]
        tags = _tag_enrichment(rows, ("great",))
        tag_names = [t[0] for t in tags]
        self.assertEqual(tag_names[0], "sunrise_window")
        self.assertEqual(tags[0][1], 2)  # 2/2 great rows
        self.assertEqual(tags[0][2], 2)  # bucket size
        self.assertNotIn("plain_day_penalty", tag_names)

    def test_tag_enrichment_empty_target_returns_empty(self) -> None:
        rows = [_row(outcome="ok")]
        self.assertEqual(_tag_enrichment(rows, ("great",)), [])


class BuildReportTests(unittest.TestCase):
    def test_empty_rows_emits_no_data_message(self) -> None:
        report = build_report([], source_path="/tmp/x.jsonl", now=datetime(2026, 5, 7))
        self.assertIn("No feedback yet", report)
        self.assertIn(f"{PHASE_C_MIN_ROWS} rows", report)
        self.assertIn(f"{PHASE_C_MIN_REGIONS} regions", report)

    def test_report_includes_phase_c_gate_when_below_threshold(self) -> None:
        rows = [_row()] * 5
        report = build_report(rows, source_path="x", now=datetime(2026, 5, 7))
        self.assertIn("⚠️", report)
        self.assertIn("Not yet ready for calibration", report)

    def test_report_includes_bias_summary(self) -> None:
        rows = [
            _row(score=80, outcome="ok"),
            _row(score=70, outcome="ok"),
        ]
        report = build_report(rows, source_path="x", now=datetime(2026, 5, 7))
        self.assertIn("mean signed deviation", report)
        self.assertIn("Outcome distribution", report)

    def test_report_handles_missing_optional_fields(self) -> None:
        # Older rows without combo_release or safety_flag must not crash.
        row = _row()
        del row["predicted"]["safety_flag"]
        del row["predicted"]["dominant_water_type"]
        del row["region"]
        report = build_report([row], source_path="x", now=datetime(2026, 5, 7))
        self.assertIn("Outcome distribution", report)


if __name__ == "__main__":
    unittest.main()
