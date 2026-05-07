"""Offline analysis of feedback rows (Phase B of empirical calibration loop).

This module is intentionally **read-only**: it never modifies any algorithm
constants. Phase C (calibration) is a separate, manual decision after the
analyst reviews this report and confirms the data is sufficient.

Usage from CLI:

    coastal-analyze-feedback                 # default path data/feedback.jsonl
    coastal-analyze-feedback --path X.jsonl
    coastal-analyze-feedback > report.md

Phase C gate: the report explicitly states whether the dataset is large
enough for calibration, so we don't accidentally tune on noise.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean, median
from typing import Any, Iterable, Mapping

from coastal_fishing_forecast.feedback import (
    FEEDBACK_SCHEMA_VERSION,
    FeedbackValidationError,
    read_feedback,
)


# Map outcome -> target score for predicted-vs-actual deviation analysis.
# These targets are intentionally cautious: searched-coordinate scores are
# capped at 86.5, so even 'great' lands at 85 not 95. Bumping these
# numbers retroactively would silently change calibration conclusions, so
# treat this dict as part of the analysis contract.
OUTCOME_TARGETS: Mapping[str, int] = {
    "skunked": 20,
    "ok": 45,
    "decent": 65,
    "great": 85,
}
OUTCOME_ORDER: tuple[str, ...] = ("skunked", "ok", "decent", "great")

# Phase C gate. Matches docs/feedback_schema_v1_2026-05-07.md.
PHASE_C_MIN_ROWS = 50
PHASE_C_MIN_REGIONS = 3
PHASE_C_MIN_DAYS_SPAN = 14

SCORE_BUCKETS: tuple[tuple[str, int, int], ...] = (
    ("< 50", 0, 49),
    ("50-64", 50, 64),
    ("65-79", 65, 79),
    ("80+", 80, 100),
)


def outcome_target(outcome: str) -> int | None:
    return OUTCOME_TARGETS.get(outcome)


def signed_deviation(row: Mapping[str, Any]) -> int | None:
    """predicted.score - outcome_target. Positive = engine over-promised."""
    predicted = row.get("predicted") or {}
    score = predicted.get("score")
    target = outcome_target(str(row.get("outcome") or ""))
    if score is None or target is None:
        return None
    try:
        return int(score) - int(target)
    except (TypeError, ValueError):
        return None


def score_bucket(score: int | None) -> str:
    if score is None:
        return "unknown"
    for label, lower, upper in SCORE_BUCKETS:
        if lower <= score <= upper:
            return label
    return "unknown"


def _format_pct(numerator: int, denominator: int) -> str:
    if denominator <= 0:
        return "—"
    return f"{(numerator * 100 // denominator)}%"


def _format_signed(value: float) -> str:
    return f"{'+' if value >= 0 else ''}{value:.1f}"


def _markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return ""
    sep = ["---"] * len(headers)
    out = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(sep) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(row) + " |")
    return "\n".join(out)


def _date_span(rows: list[Mapping[str, Any]]) -> tuple[str, str, int]:
    dates = []
    for row in rows:
        raw = row.get("trip_date")
        if not raw:
            continue
        try:
            dates.append(datetime.strptime(str(raw), "%Y-%m-%d").date())
        except ValueError:
            continue
    if not dates:
        return ("—", "—", 0)
    earliest = min(dates)
    latest = max(dates)
    return (earliest.isoformat(), latest.isoformat(), (latest - earliest).days + 1)


def _phase_c_gate(rows: list[Mapping[str, Any]]) -> tuple[bool, list[str]]:
    blockers: list[str] = []
    if len(rows) < PHASE_C_MIN_ROWS:
        blockers.append(f"need >= {PHASE_C_MIN_ROWS} rows (have {len(rows)})")
    regions = {row.get("region") for row in rows if row.get("region")}
    if len(regions) < PHASE_C_MIN_REGIONS:
        blockers.append(f"need >= {PHASE_C_MIN_REGIONS} regions (have {len(regions)})")
    _, _, days = _date_span(rows)
    if days < PHASE_C_MIN_DAYS_SPAN:
        blockers.append(f"need >= {PHASE_C_MIN_DAYS_SPAN} days span (have {days})")
    return (len(blockers) == 0, blockers)


def _outcome_distribution(rows: list[Mapping[str, Any]]) -> Counter[str]:
    return Counter(str(row.get("outcome") or "") for row in rows)


def _bias_summary(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    deviations = [signed_deviation(row) for row in rows]
    deviations = [d for d in deviations if d is not None]
    if not deviations:
        return {"n": 0}
    return {
        "n": len(deviations),
        "mean": round(mean(deviations), 2),
        "median": round(median(deviations), 2),
        "mean_abs": round(mean(abs(d) for d in deviations), 2),
    }


def _score_bucket_breakdown(rows: list[Mapping[str, Any]]) -> dict[str, Counter[str]]:
    buckets: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        predicted = row.get("predicted") or {}
        score = predicted.get("score")
        try:
            score_int: int | None = None if score is None else int(score)
        except (TypeError, ValueError):
            score_int = None
        outcome = str(row.get("outcome") or "")
        if not outcome:
            continue
        buckets[score_bucket(score_int)][outcome] += 1
    return buckets


def _group_bias(rows: list[Mapping[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    """Average signed deviation grouped by row[key] (e.g. 'region')."""
    grouped: dict[str, list[int]] = defaultdict(list)
    outcomes_by_group: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        bucket_value = row.get(key)
        if bucket_value is None:
            continue
        outcomes_by_group[str(bucket_value)][str(row.get("outcome") or "")] += 1
        dev = signed_deviation(row)
        if dev is not None:
            grouped[str(bucket_value)].append(dev)

    result: dict[str, dict[str, Any]] = {}
    for group, deviations in grouped.items():
        result[group] = {
            "n": len(deviations),
            "mean_dev": round(mean(deviations), 2) if deviations else None,
            "outcomes": dict(outcomes_by_group[group]),
        }
    return result


def _predicted_field_bias(
    rows: list[Mapping[str, Any]], predicted_key: str
) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[int]] = defaultdict(list)
    outcomes_by_group: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        predicted = row.get("predicted") or {}
        bucket_value = predicted.get(predicted_key)
        if bucket_value is None:
            continue
        outcomes_by_group[str(bucket_value)][str(row.get("outcome") or "")] += 1
        dev = signed_deviation(row)
        if dev is not None:
            grouped[str(bucket_value)].append(dev)

    result: dict[str, dict[str, Any]] = {}
    for group, deviations in grouped.items():
        result[group] = {
            "n": len(deviations) if deviations else sum(outcomes_by_group[group].values()),
            "mean_dev": round(mean(deviations), 2) if deviations else None,
            "outcomes": dict(outcomes_by_group[group]),
        }
    return result


def _tag_enrichment(
    rows: list[Mapping[str, Any]],
    target_outcomes: Iterable[str],
    min_appearances: int = 1,
) -> list[tuple[str, int, int]]:
    """Top tags appearing in any of the target outcome buckets.

    Returns list of (tag, appearances, bucket_size) sorted by frequency
    descending.
    """
    target_set = set(target_outcomes)
    bucket_rows = [row for row in rows if str(row.get("outcome") or "") in target_set]
    bucket_size = len(bucket_rows)
    if bucket_size == 0:
        return []
    counter: Counter[str] = Counter()
    for row in bucket_rows:
        predicted = row.get("predicted") or {}
        tags = predicted.get("key_reason_tags") or []
        if not isinstance(tags, list):
            continue
        counter.update(str(t) for t in tags)
    return [
        (tag, count, bucket_size)
        for tag, count in counter.most_common()
        if count >= min_appearances
    ]


def _format_bucket_table(buckets: dict[str, Counter[str]]) -> str:
    headers = ["Predicted", "n", *OUTCOME_ORDER, "Mode actual"]
    rows: list[list[str]] = []
    for label, _, _ in SCORE_BUCKETS:
        bucket = buckets.get(label, Counter())
        total = sum(bucket.values())
        if total == 0:
            continue
        most_common = bucket.most_common(1)[0][0] if bucket else "—"
        rows.append(
            [
                label,
                str(total),
                *[str(bucket.get(outcome, 0)) for outcome in OUTCOME_ORDER],
                most_common,
            ]
        )
    return _markdown_table(headers, rows)


def _format_group_bias_table(group_data: dict[str, dict[str, Any]], group_label: str) -> str:
    if not group_data:
        return ""
    headers = [group_label, "n", "mean dev", *OUTCOME_ORDER]
    rows: list[list[str]] = []
    for group_name in sorted(group_data.keys(), key=lambda g: -group_data[g]["n"]):
        info = group_data[group_name]
        outcomes = info["outcomes"]
        mean_dev = info["mean_dev"]
        rows.append(
            [
                group_name,
                str(info["n"]),
                "—" if mean_dev is None else _format_signed(mean_dev),
                *[str(outcomes.get(outcome, 0)) for outcome in OUTCOME_ORDER],
            ]
        )
    return _markdown_table(headers, rows)


def build_report(
    rows: list[Mapping[str, Any]],
    *,
    source_path: str = "(unknown)",
    now: datetime | None = None,
) -> str:
    """Build a markdown analysis report. Pure function (no IO)."""
    timestamp = (now or datetime.utcnow()).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines: list[str] = []
    lines.append("# Coastal Fishing Forecast — Feedback Analysis")
    lines.append("")
    lines.append(f"Generated: {timestamp}")
    lines.append(f"Path: `{source_path}`")
    lines.append(f"Rows: {len(rows)} (schema {FEEDBACK_SCHEMA_VERSION})")

    if not rows:
        lines.append("")
        lines.append("**No feedback yet.** Once users start submitting trip outcomes, this")
        lines.append("report will populate. Phase C calibration cannot start until the")
        lines.append(
            f"dataset reaches >= {PHASE_C_MIN_ROWS} rows across >= {PHASE_C_MIN_REGIONS} "
            f"regions over >= {PHASE_C_MIN_DAYS_SPAN} days."
        )
        return "\n".join(lines) + "\n"

    earliest, latest, span = _date_span(rows)
    lines.append(f"Date span: {earliest} → {latest} ({span} days)")
    lines.append("")

    # Phase C gate
    ready, blockers = _phase_c_gate(rows)
    lines.append("## Phase C readiness")
    lines.append("")
    if ready:
        lines.append("✅ Dataset meets the Phase C calibration gate. The analyst may now")
        lines.append("review the breakdowns below and propose targeted constant changes.")
    else:
        lines.append("⚠️  Not yet ready for calibration. Blockers:")
        for blocker in blockers:
            lines.append(f"  - {blocker}")
        lines.append("")
        lines.append("Continue collecting; analysis below is **directional only** at this size.")
    lines.append("")

    # Outcome distribution
    distribution = _outcome_distribution(rows)
    total = sum(distribution.values())
    lines.append("## Outcome distribution")
    lines.append("")
    distribution_rows = [
        [
            outcome,
            str(distribution.get(outcome, 0)),
            _format_pct(distribution.get(outcome, 0), total),
        ]
        for outcome in OUTCOME_ORDER
        if distribution.get(outcome, 0) > 0
    ]
    lines.append(_markdown_table(["Outcome", "Count", "%"], distribution_rows))
    lines.append("")

    # Bias summary
    bias = _bias_summary(rows)
    lines.append("## Predicted vs actual bias")
    lines.append("")
    if bias["n"] == 0:
        lines.append("(no rows with both predicted score and outcome)")
    else:
        lines.append(
            "Method: per-row deviation = `predicted.score - outcome_target` "
            "where targets are skunked=20, ok=45, decent=65, great=85."
        )
        lines.append("Positive mean = engine over-promises; negative = under-promises.")
        lines.append("")
        lines.append(f"- mean signed deviation: **{_format_signed(bias['mean'])}**")
        lines.append(f"- median signed deviation: **{_format_signed(bias['median'])}**")
        lines.append(f"- mean absolute deviation: **{bias['mean_abs']:.1f}**")
    lines.append("")

    # Score bucket sanity
    buckets = _score_bucket_breakdown(rows)
    bucket_table = _format_bucket_table(buckets)
    if bucket_table:
        lines.append("## Score-bucket sanity")
        lines.append("")
        lines.append("Do high predictions actually correlate with great outcomes?")
        lines.append("")
        lines.append(bucket_table)
        lines.append("")

    # Region breakdown
    region_bias = _group_bias(rows, "region")
    region_table = _format_group_bias_table(region_bias, "Region")
    if region_table:
        lines.append("## Region breakdown")
        lines.append("")
        lines.append(region_table)
        lines.append("")

    # Dominant water type breakdown
    dominant_bias = _predicted_field_bias(rows, "dominant_water_type")
    dominant_table = _format_group_bias_table(dominant_bias, "Dominant type")
    if dominant_table:
        lines.append("## Dominant water type breakdown")
        lines.append("")
        lines.append(dominant_table)
        lines.append("")

    # Safety flag breakdown
    safety_bias = _predicted_field_bias(rows, "safety_flag")
    safety_table = _format_group_bias_table(safety_bias, "Safety flag")
    if safety_table:
        lines.append("## Safety flag vs outcome")
        lines.append("")
        lines.append(safety_table)
        lines.append("")
        lines.append(
            "Note: hazardous days rarely appear in feedback (people don't fish in "
            "hazardous conditions). Sparse data in elevated/hazardous rows is expected."
        )
        lines.append("")

    # Combo release breakdown
    combo_bias = _predicted_field_bias(rows, "combo_release")
    combo_table = _format_group_bias_table(combo_bias, "Combo release")
    if combo_table:
        lines.append("## Combo release vs outcome")
        lines.append("")
        lines.append(combo_table)
        lines.append("")

    # Tag enrichment
    great_tags = _tag_enrichment(rows, ("great",), min_appearances=1)
    skunked_tags = _tag_enrichment(rows, ("skunked",), min_appearances=1)
    if great_tags or skunked_tags:
        lines.append("## Reason-tag enrichment")
        lines.append("")
        if great_tags:
            lines.append(f"Top tags in `great` bucket (n={great_tags[0][2]}):")
            for tag, count, bucket_size in great_tags[:8]:
                lines.append(f"  * {tag} ({count}/{bucket_size} = {_format_pct(count, bucket_size)})")
            lines.append("")
        if skunked_tags:
            lines.append(f"Top tags in `skunked` bucket (n={skunked_tags[0][2]}):")
            for tag, count, bucket_size in skunked_tags[:8]:
                lines.append(f"  * {tag} ({count}/{bucket_size} = {_format_pct(count, bucket_size)})")
            lines.append("")
        lines.append("Treat these as suggestive only at small sample sizes.")
        lines.append("")

    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Analyze user feedback rows and emit a markdown report."
    )
    parser.add_argument(
        "--path",
        default=None,
        help="Path to the feedback jsonl file (default: data/feedback.jsonl).",
    )
    args = parser.parse_args(argv)

    try:
        rows = read_feedback(path=args.path)
    except FeedbackValidationError as exc:
        print(f"Failed to read feedback: {exc}", file=sys.stderr)
        return 2

    source_path = str(args.path) if args.path else "data/feedback.jsonl"
    sys.stdout.write(build_report(rows, source_path=source_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
