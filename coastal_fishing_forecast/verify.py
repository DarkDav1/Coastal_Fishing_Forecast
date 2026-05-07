"""Verification runner for the generic coastal preview engine."""

from __future__ import annotations

import argparse
from datetime import date, timedelta
import sys
import unittest
from pathlib import Path
from typing import Any

from coastal_fishing_forecast.preview import build_preview
from coastal_fishing_forecast.tidesatlas import fetch_tidesatlas_events


SMOKE_CASES: tuple[dict[str, Any], ...] = (
    {
        "id": "coastal_preview",
        "lat": -33.7950,
        "lon": 151.2870,
        "expected_status": "ok",
        "expected_support_mode": "on_water",
    },
    {
        "id": "near_water_preview",
        "lat": -28.0167,
        "lon": 153.4000,
        "expected_status": "ok",
        "expected_support_mode": "near_water",
    },
    {
        "id": "tidal_corridor_preview",
        "lat": -33.9000,
        "lon": 151.0800,
        "expected_status": "ok",
        "expected_support_mode": "tidal_corridor",
    },
    {
        "id": "boundary_reject",
        "lat": -27.4705,
        "lon": 153.0260,
        "expected_status": "unsupported",
        "expected_support_mode": "unsupported",
    },
    {
        "id": "invalid_coordinate",
        "lat": 95.0,
        "lon": 151.0,
        "expected_status": "invalid_input",
        "expected_support_mode": "invalid_input",
    },
)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _run_unittest_suite(verbosity: int) -> bool:
    tests_dir = _project_root() / "tests"
    loader = unittest.TestLoader()
    suite = loader.discover(str(tests_dir))
    runner = unittest.TextTestRunner(verbosity=verbosity, stream=sys.stdout)
    return runner.run(suite).wasSuccessful()


def _run_smoke_cases(verbose: bool) -> bool:
    ok = True
    for case in SMOKE_CASES:
        result = build_preview(case["lat"], case["lon"])
        status = result["status"]
        support_mode = result["meta"]["support_profile"]["support_mode"]
        passed = status == case["expected_status"] and support_mode == case["expected_support_mode"]
        ok = ok and passed
        marker = "PASS" if passed else "FAIL"
        print(f"{marker} smoke:{case['id']} status={status} support_mode={support_mode}")
        if verbose and result["status"] == "ok":
            print(f"  dominant={result['overall_recommendation']['dominant_inferred_type']}")
            print(f"  score={result['overall_recommendation']['score']}")
    return ok


def _run_live_tidesatlas_check(verbose: bool) -> bool:
    start_date = date.today()
    end_date = start_date + timedelta(days=2)
    try:
        events, meta = fetch_tidesatlas_events(
            lat=-41.2530,
            lon=148.3060,
            start_date=start_date,
            end_date=end_date,
        )
    except Exception as exc:
        print(f"FAIL live:tidesatlas error={exc}")
        return False

    passed = len(events) >= 2 and all(event.event_type in {"high", "low"} for event in events)
    marker = "PASS" if passed else "FAIL"
    print(f"{marker} live:tidesatlas events={len(events)} range={start_date.isoformat()}..{end_date.isoformat()}")
    if verbose and meta.get("port"):
        print(f"  port={meta['port']}")
    if verbose and events:
        first = events[0]
        print(f"  first_event={first.event_type} {first.time.isoformat()} height_m={first.height_m}")
    return passed


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify the coastal preview engine")
    parser.add_argument("--skip-unittest", action="store_true", help="Run smoke checks only")
    parser.add_argument("--verbose", action="store_true", help="Print more smoke-check details")
    parser.add_argument(
        "--include-live-tides",
        action="store_true",
        help="Also verify live TidesAtlas access using TIDESATLAS_API_KEY.",
    )
    args = parser.parse_args()

    suite_ok = True
    if not args.skip_unittest:
        print("Running unittest regression suite...", flush=True)
        suite_ok = _run_unittest_suite(verbosity=2 if args.verbose else 1)

    print("Running engine smoke checks...", flush=True)
    smoke_ok = _run_smoke_cases(verbose=args.verbose)

    live_tide_ok = True
    if args.include_live_tides:
        print("Running live tide source checks...", flush=True)
        live_tide_ok = _run_live_tidesatlas_check(verbose=args.verbose)

    if suite_ok and smoke_ok and live_tide_ok:
        print("Engine verification passed.")
        return

    print("Engine verification failed.")
    sys.exit(1)


if __name__ == "__main__":
    main()
