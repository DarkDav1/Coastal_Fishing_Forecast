"""CLI to record one feedback row from stdin JSON.

Used by the local web API server (`apps/web/server/api-server.mjs`) and
also runnable manually for local testing:

    echo '{"trip_date":"2026-05-08","trip_window":"morning",...}' | coastal-feedback

The CLI always writes JSON to stdout (either the stored record or an
error object with `error` + `message` fields) and exits 0 on success,
non-zero on validation / IO failure.
"""

from __future__ import annotations

import json
import sys

from coastal_fishing_forecast.feedback import (
    FeedbackValidationError,
    record_feedback,
)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv

    if args:
        raw = args[0]
    else:
        raw = sys.stdin.read()

    if not raw or not raw.strip():
        sys.stdout.write(json.dumps({"error": "empty_payload"}))
        sys.stdout.write("\n")
        return 1

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        sys.stdout.write(json.dumps({"error": "invalid_json", "message": str(exc)}))
        sys.stdout.write("\n")
        return 1

    try:
        record = record_feedback(payload)
    except FeedbackValidationError as exc:
        sys.stdout.write(json.dumps({"error": "feedback_invalid", "message": str(exc)}))
        sys.stdout.write("\n")
        return 1
    except OSError as exc:
        sys.stdout.write(json.dumps({"error": "feedback_io", "message": str(exc)}))
        sys.stdout.write("\n")
        return 1

    sys.stdout.write(json.dumps(record))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
