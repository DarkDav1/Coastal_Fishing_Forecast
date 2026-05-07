"""Regression replay for the public search-to-forecast flow."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from coastal_fishing_forecast.search_forecast import build_search_forecast_response


@dataclass(frozen=True)
class ReplayCase:
    id: str
    query: str
    region: str
    category: str
    expected_status: str = "ok"
    expected_dominant_types: tuple[str, ...] = ("beach", "bay_estuary_edge", "jetty", "rocks")
    note: str = ""


DEFAULT_REPLAY_CASES: tuple[ReplayCase, ...] = (
    ReplayCase(
        "binalong_bay",
        "Binalong Bay Tasmania",
        "open_coast",
        "open_beach",
        expected_dominant_types=("beach",),
        note="Open Tasmanian beach candidate should stay beach-led.",
    ),
    ReplayCase("st_helens", "St Helens Tasmania", "sheltered_estuary", "estuary_town"),
    ReplayCase("coles_bay", "Coles Bay Tasmania", "bay_coast", "bay_edge"),
    ReplayCase("fremantle", "Fremantle Western Australia", "harbour_access", "harbour_city"),
    ReplayCase("sydney_harbour", "Sydney Harbour Australia", "harbour_access", "harbour_water"),
    ReplayCase("Torquay Surf Beach Victoria", "Torquay Surf Beach Victoria", "surf_coast", "surf_beach"),
    ReplayCase("Noosa Heads Queensland", "Noosa Heads Queensland", "bay_coast", "coastal_headland"),
    ReplayCase("Port Macquarie Breakwall NSW", "Port Macquarie Breakwall NSW", "harbour_access", "jetty_breakwall"),
    ReplayCase(
        "alice_springs",
        "Alice Springs Northern Territory",
        "generic_coast",
        "inland_reject",
        expected_status="unsupported_or_no_result",
        note="Far inland places must not receive a coastal forecast.",
    ),
    ReplayCase(
        "lake_eildon",
        "Lake Eildon Victoria",
        "generic_coast",
        "inland_lake_reject",
        expected_status="unsupported_or_no_result",
        note="Inland lakes are outside v1 scope.",
    ),
    ReplayCase(
        "dubbo",
        "Dubbo New South Wales",
        "generic_coast",
        "inland_town_reject",
        expected_status="unsupported_or_no_result",
        note="Inland towns should fail support checks.",
    ),
)


def _default_dates() -> tuple[date, date]:
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=2)
    return start, end


def _case_result(case: ReplayCase, response: dict[str, Any]) -> dict[str, Any]:
    expected = {
        "status": case.expected_status,
        "dominant_types": list(case.expected_dominant_types),
        "note": case.note,
    }
    if response["status"] != "ok" or response["forecast"] is None:
        passed = response["status"] == case.expected_status
        return {
            "id": case.id,
            "query": case.query,
            "category": case.category,
            "passed": passed,
            "status": response["status"],
            "expected": expected,
            "failure_reasons": [] if passed else [f"Expected status {case.expected_status}, got {response['status']}."],
            "selected_place": _summarize_place(response.get("selected_place")),
            "forecast_summary": None,
        }

    forecast = response["forecast"]
    summary = forecast["summary"]
    best = summary["best_windows"][0] if summary["best_windows"] else None
    dominant = None if best is None else best["dominant_inferred_type"]
    score = None if best is None else best["score"]
    passed = (
        response["status"] == case.expected_status
        and dominant in case.expected_dominant_types
        and score is not None
        and 0 <= score <= 100
    )
    failure_reasons = []
    if response["status"] != case.expected_status:
        failure_reasons.append(f"Expected status {case.expected_status}, got {response['status']}.")
    if dominant not in case.expected_dominant_types:
        failure_reasons.append(f"Expected dominant type in {case.expected_dominant_types}, got {dominant}.")
    if score is None or not 0 <= score <= 100:
        failure_reasons.append(f"Expected score from 0 to 100, got {score}.")
    return {
        "id": case.id,
        "query": case.query,
        "category": case.category,
        "passed": passed,
        "status": response["status"],
        "expected": expected,
        "failure_reasons": failure_reasons,
        "selected_place": _summarize_place(response["selected_place"]),
        "forecast_summary": {
            "dominant_inferred_type": dominant,
            "score": score,
            "tide_status": forecast["tide_verification"]["status"],
            "confidence": forecast["confidence"],
        },
    }


def _summarize_place(place: Any) -> dict[str, Any] | None:
    if not isinstance(place, dict):
        return None
    support = place.get("forecast_support") or {}
    return {
        "id": place.get("id"),
        "display_name": place.get("display_name"),
        "latitude": place.get("latitude"),
        "longitude": place.get("longitude"),
        "types": place.get("types"),
        "selection_score": place.get("selection_score"),
        "support": {
            "supported": support.get("supported"),
            "reason_code": support.get("reason_code"),
            "nearest_supported_water_km": support.get("nearest_supported_water_km"),
            "message": support.get("message"),
        },
    }


def run_regression_replay(
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    provider: str = "nominatim",
    cache_dir: str | Path | None = None,
    cache_enabled: bool = True,
) -> dict[str, Any]:
    start, end = (start_date, end_date) if start_date and end_date else _default_dates()
    results = []
    for case in DEFAULT_REPLAY_CASES:
        response = build_search_forecast_response(
            case.query,
            start_date=start,
            end_date=end,
            provider=provider,
            region=case.region,
            windows=("morning", "dusk"),
            condition_source="archive",
            tide_source="approximation",
            cache_enabled=cache_enabled,
            cache_dir=cache_dir,
        )
        results.append(_case_result(case, response))

    return {
        "contract_version": "2026-04-28.regression_replay.v1",
        "input": {
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "provider": provider,
            "tide_source": "approximation",
        },
        "summary": {
            "passed": sum(1 for item in results if item["passed"]),
            "failed": sum(1 for item in results if not item["passed"]),
            "total": len(results),
            "by_category": _summary_by_category(results),
        },
        "results": results,
    }


def _summary_by_category(results: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    summary: dict[str, dict[str, int]] = {}
    for item in results:
        category = item["category"]
        if category not in summary:
            summary[category] = {"passed": 0, "failed": 0, "total": 0}
        summary[category]["total"] += 1
        if item["passed"]:
            summary[category]["passed"] += 1
        else:
            summary[category]["failed"] += 1
    return summary
