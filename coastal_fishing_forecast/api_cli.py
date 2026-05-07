"""CLI for frontend-oriented forecast responses."""

from __future__ import annotations

import argparse
import json

from coastal_fishing_forecast.api import build_frontend_forecast_response
from coastal_fishing_forecast.forecast import TIME_WINDOWS


def main() -> None:
    parser = argparse.ArgumentParser(description="Frontend-oriented coastal forecast API response")
    parser.add_argument("lat", type=float, help="Latitude")
    parser.add_argument("lon", type=float, help="Longitude")
    parser.add_argument("--start-date", required=True, help="Start date, YYYY-MM-DD")
    parser.add_argument("--end-date", required=True, help="End date, YYYY-MM-DD")
    parser.add_argument("--region", help="Optional generic region preset.")
    parser.add_argument("--windows", default="morning,dusk", help=f"Comma-separated windows. Available: {','.join(TIME_WINDOWS)}")
    parser.add_argument("--condition-source", default="auto", choices=("auto", "archive", "forecast"))
    parser.add_argument("--tide-events-json", help="Optional JSON array of real tide events.")
    parser.add_argument("--tide-events-file", help="Optional JSON or CSV file containing real tide events.")
    parser.add_argument("--tide-source", default="auto", choices=("auto", "approximation", "openmeteo_model", "tidesatlas"))
    parser.add_argument("--tidesatlas-api-key", help="Optional TidesAtlas API key.")
    parser.add_argument("--planner-provider", default="rule_based", choices=("rule_based", "llm", "github_models"))
    parser.add_argument("--explanation-provider", default="rule_based", choices=("rule_based", "llm", "github_models"))
    parser.add_argument("--structure-facilities-json", help="Optional JSON array of mapped public structures for planner/map display.")
    parser.add_argument("--structure-source", default="none", choices=("none", "osm", "list_mast", "auto"), help="Optional automatic public structure lookup source.")
    parser.add_argument("--structure-radius-m", type=int, default=1200, help="Radius for automatic structure lookup.")
    parser.add_argument("--no-cache", action="store_true", help="Disable cache reads/writes.")
    parser.add_argument("--cache-dir", help="Optional cache directory.")
    args = parser.parse_args()

    if args.tide_events_json and args.tide_events_file:
        parser.error("Use only one of --tide-events-json or --tide-events-file")

    windows = tuple(part.strip() for part in args.windows.split(",") if part.strip())
    unknown_windows = sorted(set(windows) - set(TIME_WINDOWS))
    if unknown_windows:
        parser.error(f"Unknown windows: {', '.join(unknown_windows)}")

    tide_events = json.loads(args.tide_events_json) if args.tide_events_json else None
    structure_facilities = json.loads(args.structure_facilities_json) if args.structure_facilities_json else None
    response = build_frontend_forecast_response(
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
        planner_provider=args.planner_provider,
        explanation_provider=args.explanation_provider,
        structure_facilities=structure_facilities,
        structure_source=args.structure_source,
        structure_radius_m=args.structure_radius_m,
        cache_enabled=not args.no_cache,
        cache_dir=args.cache_dir,
    )
    print(json.dumps(response, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
