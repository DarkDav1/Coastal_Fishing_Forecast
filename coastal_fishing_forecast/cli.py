"""Command-line entry points for previewing searched coordinates."""

from __future__ import annotations

import argparse
import json

from coastal_fishing_forecast.preview import build_preview


def main() -> None:
    parser = argparse.ArgumentParser(description="Generic coastal coordinate preview")
    parser.add_argument("lat", type=float, help="Latitude")
    parser.add_argument("lon", type=float, help="Longitude")
    parser.add_argument(
        "--environment-json",
        help="Optional JSON object with environment inputs such as wind_speed_knots, swell_height_m, pressure_hpa, tide_phase, and time_window.",
    )
    parser.add_argument(
        "--region",
        help="Optional generic region preset such as generic_coastal, open_coast, or sheltered_estuary.",
    )
    args = parser.parse_args()

    environment = json.loads(args.environment_json) if args.environment_json else None
    result = build_preview(args.lat, args.lon, environment=environment, region=args.region)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
