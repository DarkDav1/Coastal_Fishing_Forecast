"""Combined place-search to forecast product flow."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any, Mapping

from coastal_fishing_forecast.api import build_frontend_forecast_response
from coastal_fishing_forecast.places import rank_place_candidates, search_places
from coastal_fishing_forecast.planner import build_fishing_plan
from coastal_fishing_forecast.preview import build_preview


SEARCH_FORECAST_CONTRACT_VERSION = "2026-04-28.search_forecast.v1"


def _candidate_support(candidate: Mapping[str, Any], region: str | None) -> dict[str, Any]:
    preview = build_preview(float(candidate["latitude"]), float(candidate["longitude"]), region=region)
    return {
        "status": preview["status"],
        "supported": preview["support"]["supported"],
        "reason_code": preview["support"]["reason_code"],
        "message": preview["support"]["message"],
        "nearest_supported_water_km": preview["support"]["nearest_supported_water_km"],
    }


def _select_supported_candidate(candidates: list[Mapping[str, Any]], region: str | None) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    evaluated = []
    for candidate in rank_place_candidates(candidates):
        support = _candidate_support(candidate, region)
        item = dict(candidate)
        item["forecast_support"] = support
        support_mode_bonus = {
            "coastal_or_tidal_preview": 35.0,
            "tidal_corridor_preview": 24.0,
            "too_far_from_supported_water": -20.0,
            "inland_or_non_tidal": -30.0,
            "invalid_coordinate": -50.0,
        }.get(str(support["reason_code"]), 0.0)
        distance = support.get("nearest_supported_water_km")
        distance_bonus = max(0.0, 10.0 - (float(distance) * 2.0)) if distance is not None else 0.0
        support_bonus = 100.0 if support["supported"] else 0.0
        item["selection_score"] = round(item["coastal_candidate_score"] + support_bonus + support_mode_bonus + distance_bonus, 2)
        evaluated.append(item)

    evaluated.sort(key=lambda item: item["selection_score"], reverse=True)
    selected = next((candidate for candidate in evaluated if candidate["forecast_support"]["supported"]), None)
    return selected, evaluated


def build_search_forecast_response(
    query: str,
    *,
    start_date: str | date,
    end_date: str | date,
    provider: str = "nominatim",
    access_token: str | None = None,
    country: str | None = "au",
    proximity: tuple[float, float] | None = None,
    place_limit: int = 5,
    language: str = "en",
    region: str | None = None,
    windows: tuple[str, ...] = ("morning", "dusk"),
    condition_source: str = "auto",
    tide_events: list[Mapping[str, Any]] | None = None,
    tide_events_file: str | None = None,
    tide_source: str = "auto",
    tidesatlas_api_key: str | None = None,
    planner_provider: str = "rule_based",
    structure_facilities: list[Mapping[str, Any]] | None = None,
    structure_source: str = "none",
    structure_radius_m: int = 1200,
    cache_enabled: bool = True,
    cache_dir: str | Path | None = None,
) -> dict[str, Any]:
    place_search = search_places(
        query,
        provider=provider,
        access_token=access_token,
        country=country,
        proximity=proximity,
        limit=place_limit,
        language=language,
        cache_enabled=cache_enabled,
        cache_dir=cache_dir,
    )
    selected, candidates = _select_supported_candidate(place_search["results"], region)
    forecast = None
    plan = None
    if selected is not None:
        forecast = build_frontend_forecast_response(
            float(selected["latitude"]),
            float(selected["longitude"]),
            start_date=start_date,
            end_date=end_date,
            region=region,
            windows=windows,
            condition_source=condition_source,
            tide_events=tide_events,
            tide_events_file=tide_events_file,
            tide_source=tide_source,
            tidesatlas_api_key=tidesatlas_api_key,
            planner_provider=planner_provider,
            structure_facilities=structure_facilities,
            structure_source=structure_source,
            structure_radius_m=structure_radius_m,
            cache_enabled=cache_enabled,
            cache_dir=cache_dir,
        )
        plan = forecast["plan"]
    else:
        plan = build_fishing_plan(
            {
                "hero": {"best_window": None},
                "confidence": {"label": "unsupported", "score": 0},
                "tide_verification": {"status": "estimated", "source": "none"},
            },
            planner_provider=planner_provider,
        )

    return {
        "contract_version": SEARCH_FORECAST_CONTRACT_VERSION,
        "query": query,
        "provider": provider,
        "selected_place": selected,
        "candidates": candidates,
        "forecast": forecast,
        "plan": plan,
        "status": "ok" if forecast is not None else "unsupported_or_no_result",
    }
