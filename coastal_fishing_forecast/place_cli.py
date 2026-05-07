"""CLI for place search resolution."""

from __future__ import annotations

import argparse
import json

from coastal_fishing_forecast.places import search_places


def _parse_proximity(value: str | None) -> tuple[float, float] | None:
    if not value:
        return None
    lat_text, lon_text = value.split(",", 1)
    return float(lat_text), float(lon_text)


def main() -> None:
    parser = argparse.ArgumentParser(description="Resolve a place query into candidate coordinates")
    parser.add_argument("query", help="Place search query")
    parser.add_argument("--provider", default="mapbox", choices=("mapbox", "nominatim"), help="Place search provider")
    parser.add_argument("--country", default="au", help="Optional country filter, default au")
    parser.add_argument("--proximity", help="Optional lat,lon proximity bias")
    parser.add_argument("--limit", type=int, default=5, help="Maximum result count")
    parser.add_argument("--language", default="en", help="Result language")
    parser.add_argument("--mapbox-token", help="Optional Mapbox access token. If omitted, MAPBOX_ACCESS_TOKEN is used.")
    parser.add_argument("--no-cache", action="store_true", help="Disable place search cache")
    parser.add_argument("--cache-dir", help="Optional cache directory")
    args = parser.parse_args()

    result = search_places(
        args.query,
        provider=args.provider,
        access_token=args.mapbox_token,
        country=args.country,
        proximity=_parse_proximity(args.proximity),
        limit=args.limit,
        language=args.language,
        cache_enabled=not args.no_cache,
        cache_dir=args.cache_dir,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
