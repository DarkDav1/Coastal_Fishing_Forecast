"""CLI for regression replay."""

from __future__ import annotations

import argparse
from datetime import date
import json
import sys

from coastal_fishing_forecast.regression_replay import run_regression_replay


def _parse_date(value: str | None) -> date | None:
    return None if value is None else date.fromisoformat(value)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run search-to-forecast regression replay without TidesAtlas usage")
    parser.add_argument("--start-date", help="Start date, YYYY-MM-DD. Defaults to recent archive window.")
    parser.add_argument("--end-date", help="End date, YYYY-MM-DD. Defaults to recent archive window.")
    parser.add_argument("--provider", default="nominatim", choices=("nominatim", "mapbox"))
    parser.add_argument("--cache-dir", help="Optional cache directory")
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--fail-on-error", action="store_true", help="Exit non-zero if any case fails")
    args = parser.parse_args()

    result = run_regression_replay(
        start_date=_parse_date(args.start_date),
        end_date=_parse_date(args.end_date),
        provider=args.provider,
        cache_dir=args.cache_dir,
        cache_enabled=not args.no_cache,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    if args.fail_on_error and result["summary"]["failed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
