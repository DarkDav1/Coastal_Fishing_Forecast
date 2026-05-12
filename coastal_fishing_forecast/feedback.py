"""Feedback collection for the empirical calibration loop (Phase A).

Stores user-reported trip outcomes alongside the engine's predicted scores.
Phase A only collects data; Phase B and C analyze and calibrate. The
storage format is intentionally a JSON Lines file so it survives schema
evolution: each row carries its own `schema_version` and a verbatim
`predicted` block, so historical rows stay interpretable when the engine
changes.

Bumping `FEEDBACK_SCHEMA_VERSION` is a breaking-style change. NEVER mutate
the meaning of an existing field; only ever add new optional fields. If a
real breaking change is needed, introduce v2 and read both versions.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4


FEEDBACK_SCHEMA_VERSION = "v1"
FEEDBACK_PATH_ENV = "COASTAL_FORECAST_FEEDBACK_PATH"
DEFAULT_FEEDBACK_PATH = "data/feedback.jsonl"
ALLOWED_OUTCOMES = frozenset({"skunked", "ok", "decent", "great"})
ALLOWED_TIME_WINDOWS = frozenset({"pre_dawn", "dawn", "morning", "day", "dusk", "night"})
SUPPORTED_SAFETY_FLAGS = frozenset({"low", "moderate", "elevated", "hazardous"})
MAX_NOTES_LENGTH = 120


class FeedbackValidationError(ValueError):
    """Raised when a feedback payload fails schema validation."""


def resolve_feedback_path(path: str | Path | None = None) -> Path:
    configured = path or os.environ.get(FEEDBACK_PATH_ENV) or DEFAULT_FEEDBACK_PATH
    return Path(configured)


def _require(payload: Mapping[str, Any], key: str) -> Any:
    if key not in payload:
        raise FeedbackValidationError(f"Missing required field: {key}")
    value = payload[key]
    if value is None or (isinstance(value, str) and value.strip() == ""):
        raise FeedbackValidationError(f"Field {key} cannot be empty")
    return value


def validate_feedback_payload(payload: Mapping[str, Any]) -> None:
    if not isinstance(payload, Mapping):
        raise FeedbackValidationError("Feedback payload must be a JSON object")

    trip_date = str(_require(payload, "trip_date"))
    try:
        datetime.strptime(trip_date, "%Y-%m-%d")
    except ValueError as exc:
        raise FeedbackValidationError("trip_date must be YYYY-MM-DD format") from exc

    trip_window = str(_require(payload, "trip_window")).strip().lower()
    if trip_window not in ALLOWED_TIME_WINDOWS:
        raise FeedbackValidationError(
            f"trip_window must be one of {sorted(ALLOWED_TIME_WINDOWS)}"
        )

    try:
        lat = float(_require(payload, "lat"))
        lon = float(_require(payload, "lon"))
    except (TypeError, ValueError) as exc:
        raise FeedbackValidationError("lat / lon must be numeric") from exc
    if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
        raise FeedbackValidationError("lat / lon out of valid range")

    outcome = str(_require(payload, "outcome")).strip().lower()
    if outcome not in ALLOWED_OUTCOMES:
        raise FeedbackValidationError(
            f"outcome must be one of {sorted(ALLOWED_OUTCOMES)}"
        )

    predicted = payload.get("predicted")
    if not isinstance(predicted, Mapping):
        raise FeedbackValidationError("predicted must be a JSON object")
    if "score" not in predicted:
        raise FeedbackValidationError("predicted.score is required")
    try:
        int(predicted["score"])
    except (TypeError, ValueError) as exc:
        raise FeedbackValidationError("predicted.score must be an integer") from exc

    if "safety_flag" in predicted and predicted.get("safety_flag") is not None:
        flag = str(predicted["safety_flag"]).lower()
        if flag not in SUPPORTED_SAFETY_FLAGS:
            raise FeedbackValidationError(
                f"predicted.safety_flag must be one of {sorted(SUPPORTED_SAFETY_FLAGS)}"
            )

    notes = payload.get("outcome_notes")
    if notes is not None and not isinstance(notes, str):
        raise FeedbackValidationError("outcome_notes must be a string")
    if isinstance(notes, str) and len(notes) > MAX_NOTES_LENGTH:
        raise FeedbackValidationError(
            f"outcome_notes must be {MAX_NOTES_LENGTH} characters or fewer"
        )


def record_feedback(
    payload: Mapping[str, Any],
    *,
    path: str | Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Validate, enrich with metadata, and append to the jsonl store."""
    validate_feedback_payload(payload)

    timestamp = now or datetime.now(timezone.utc)
    record: dict[str, Any] = {
        "schema_version": FEEDBACK_SCHEMA_VERSION,
        "report_id": payload.get("report_id") or uuid4().hex,
        "submitted_at": timestamp.isoformat(),
        "trip_date": str(payload["trip_date"]),
        "trip_window": str(payload["trip_window"]).strip().lower(),
        "lat": float(payload["lat"]),
        "lon": float(payload["lon"]),
        "region": payload.get("region"),
        "predicted": dict(payload["predicted"]),
        "outcome": str(payload["outcome"]).strip().lower(),
    }
    if payload.get("outcome_notes") is not None:
        record["outcome_notes"] = str(payload["outcome_notes"])

    target = resolve_feedback_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)

    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True))
        handle.write("\n")

    return record


def read_feedback(path: str | Path | None = None) -> list[dict[str, Any]]:
    """Read all feedback rows. Returns [] if the file does not exist yet."""
    target = resolve_feedback_path(path)
    if not target.exists():
        return []
    rows: list[dict[str, Any]] = []
    with target.open("r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, start=1):
            stripped = raw.strip()
            if not stripped:
                continue
            try:
                rows.append(json.loads(stripped))
            except json.JSONDecodeError as exc:
                raise FeedbackValidationError(
                    f"Corrupt feedback row at line {line_number}: {exc}"
                ) from exc
    return rows
