"""CLI for date-range coordinate forecasts and replays."""

from __future__ import annotations

import argparse
import json

from coastal_fishing_forecast.forecast import TIME_WINDOWS, build_range_forecast


def main() -> None:
    parser = argparse.ArgumentParser(description="Generic coastal date-range forecast")
    parser.add_argument("lat", type=float, help="Latitude")
    parser.add_argument("lon", type=float, help="Longitude")
    parser.add_argument("--start-date", required=True, help="Start date, YYYY-MM-DD")
    parser.add_argument("--end-date", required=True, help="End date, YYYY-MM-DD")
    parser.add_argument(
        "--region",
        help="Optional generic region preset such as generic_coastal, open_coast, or sheltered_estuary.",
    )
    parser.add_argument(
        "--windows",
        default="morning,dusk",
        help=f"Comma-separated windows. Available: {','.join(TIME_WINDOWS)}",
    )
    parser.add_argument(
        "--condition-source",
        default="auto",
        choices=("auto", "archive", "forecast"),
        help="Weather source for Open-Meteo conditions.",
    )
    parser.add_argument(
        "--tide-events-json",
        help="Optional JSON array of real tide events: [{\"time\":\"...\",\"type\":\"high|low\",\"height_m\":1.2}]",
    )
    parser.add_argument(
        "--tide-events-file",
        help="Optional JSON or CSV file containing real tide events. Columns/keys: time, type, height_m.",
    )
    parser.add_argument(
        "--tide-source",
        default="auto",
        choices=("auto", "approximation", "openmeteo_model", "tidesatlas"),
        help="Tide source when no explicit tide events are supplied. auto uses low-cost Open-Meteo model tide when available, then falls back to approximation.",
    )
    parser.add_argument(
        "--tidesatlas-api-key",
        help="Optional TidesAtlas API key. If omitted, TIDESATLAS_API_KEY is used.",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable weather, marine, and tide API cache reads/writes.",
    )
    parser.add_argument(
        "--cache-dir",
        help="Optional cache directory. Defaults to .cache/coastal_fishing_forecast or COASTAL_FORECAST_CACHE_DIR.",
    )
    args = parser.parse_args()

    windows = tuple(part.strip() for part in args.windows.split(",") if part.strip())
    unknown_windows = sorted(set(windows) - set(TIME_WINDOWS))
    if unknown_windows:
        parser.error(f"Unknown windows: {', '.join(unknown_windows)}")

    if args.tide_events_json and args.tide_events_file:
        parser.error("Use only one of --tide-events-json or --tide-events-file")

    tide_events = json.loads(args.tide_events_json) if args.tide_events_json else None
    result = build_range_forecast(
        args.lat,
        args.lon,
        start_date=args.start_date,
        end_date=args.end_date,
        region=args.region,
        windows=windows,
        condition_source=args.condition_source,
        tide_events=tide_events,
        tide_events_file=args.tide_events_file,
        tide_source=args.tide_source,
        tidesatlas_api_key=args.tidesatlas_api_key,
        cache_enabled=not args.no_cache,
        cache_dir=args.cache_dir,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
