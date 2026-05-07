"""Read-only social signal context for the generic coastal forecast."""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from math import asin, cos, radians, sin, sqrt
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AreaAnchor:
    key: str
    latitude: float
    longitude: float
    family: str


AREA_ANCHORS = (
    AreaAnchor("st_helens", -41.3236, 148.2494, "east_coast"),
    AreaAnchor("binalong_bay", -41.2530, 148.3060, "east_coast"),
    AreaAnchor("eaglehawk_neck", -43.0333, 147.9333, "east_coast"),
    AreaAnchor("east_coast_tasmania", -41.9000, 148.2500, "east_coast"),
    AreaAnchor("hobart", -42.8821, 147.3272, "derwent"),
    AreaAnchor("derwent", -42.8770, 147.3510, "derwent"),
    AreaAnchor("sandy_bay", -42.9000, 147.3350, "derwent"),
    AreaAnchor("taroona", -42.9500, 147.3500, "derwent"),
    AreaAnchor("kangaroo_bluff", -42.8760, 147.3530, "derwent"),
    AreaAnchor("south_arm", -43.0300, 147.4200, "derwent"),
    AreaAnchor("white_beach", -43.1070, 147.7440, "east_coast"),
    AreaAnchor("kelso", -41.1020, 146.7760, "estuary"),
    AreaAnchor("tamar_river", -41.2100, 146.8200, "estuary"),
    AreaAnchor("launceston", -41.4332, 147.1441, "estuary"),
    AreaAnchor("tasmania", -42.0000, 147.0000, "tasmania"),
)
AREA_BY_KEY = {area.key: area for area in AREA_ANCHORS}
BROAD_AREAS = {"", "tasmania"}

CONFIDENCE_WEIGHT = {
    "high": 1.0,
    "medium": 0.7,
    "low": 0.35,
    "very_low": 0.15,
    "": 0.4,
}
SHORE_WEIGHT = {
    "shore": 1.0,
    "unknown": 0.65,
    "boat": 0.35,
    "mixed": 0.7,
    "": 0.6,
}


def default_social_data_dir() -> Path:
    project_root = Path(__file__).resolve().parents[1]
    return project_root.parent / "fishing-forecast" / "data" / "social_intel"


def _distance_km(first_lat: float, first_lon: float, second_lat: float, second_lon: float) -> float:
    earth_radius_km = 6371.0
    d_lat = radians(second_lat - first_lat)
    d_lon = radians(second_lon - first_lon)
    lat1 = radians(first_lat)
    lat2 = radians(second_lat)
    a = sin(d_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(d_lon / 2) ** 2
    return 2 * earth_radius_km * asin(sqrt(a))


def _nearest_anchor(lat: float, lon: float) -> AreaAnchor:
    return min(AREA_ANCHORS, key=lambda area: _distance_km(lat, lon, area.latitude, area.longitude))


def _parse_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def _load_rows(data_dir: Path) -> list[dict[str, str]]:
    signals_path = data_dir / "social_signals.csv"
    if not signals_path.exists():
        return []
    with signals_path.open("r", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def _area_relevance(row_area: str, nearest: AreaAnchor, lat: float, lon: float) -> float:
    area = (row_area or "").strip()
    if area == nearest.key:
        return 1.0
    if area in BROAD_AREAS:
        return 0.20 if nearest.family != "tasmania" else 0.35

    anchor = AREA_BY_KEY.get(area)
    if anchor is None:
        return 0.0
    if anchor.family == nearest.family:
        return 0.55

    distance = _distance_km(lat, lon, anchor.latitude, anchor.longitude)
    if distance <= 25:
        return 0.65
    if distance <= 60:
        return 0.35
    return 0.0


def _recency_weight(row_date: date, today: date, recent_days: int) -> float:
    age = (today - row_date).days
    if age < 0 or age > recent_days:
        return 0.0
    return max(0.15, 1.0 - (age / recent_days))


def _pulse_level(score: int) -> str:
    if score >= 65:
        return "high"
    if score >= 35:
        return "medium"
    if score >= 12:
        return "low"
    return "none"


def build_social_pulse(
    lat: float,
    lon: float,
    *,
    data_dir: Path | None = None,
    today: date | None = None,
    recent_days: int = 45,
) -> dict[str, Any]:
    """Summarize legacy social intel as read-only context for a searched coordinate."""
    resolved_today = today or date.today()
    resolved_data_dir = data_dir or default_social_data_dir()
    nearest = _nearest_anchor(lat, lon)
    rows = _load_rows(resolved_data_dir)

    if not rows:
        return {
            "available": False,
            "role": "context_only",
            "score_adjustment_allowed": False,
            "source": "legacy_social_intel",
            "message": "No structured social signal file was found.",
            "nearest_signal_area": nearest.key,
            "pulse_level": "none",
            "pulse_score": 0,
            "recent_report_count": 0,
        }

    weighted_total = 0.0
    recent_count = 0
    latest_seen: date | None = None
    species_counter: Counter[str] = Counter()
    platform_counter: Counter[str] = Counter()
    area_counter: Counter[str] = Counter()

    for row in rows:
        row_date = _parse_date(row.get("date", ""))
        if row_date is None:
            continue
        latest_seen = row_date if latest_seen is None else max(latest_seen, row_date)
        recency = _recency_weight(row_date, resolved_today, recent_days)
        if recency <= 0:
            continue

        relevance = _area_relevance(row.get("normalized_area", ""), nearest, lat, lon)
        if relevance <= 0:
            continue

        confidence = CONFIDENCE_WEIGHT.get((row.get("evidence_confidence") or "").strip().lower(), 0.4)
        shore = SHORE_WEIGHT.get((row.get("shore_vs_boat") or "").strip().lower(), 0.6)
        weight = recency * relevance * confidence * shore
        if weight <= 0:
            continue

        weighted_total += weight
        recent_count += 1
        platform_counter[row.get("source_platform", "") or "unknown"] += 1
        area_counter[row.get("normalized_area", "") or "unknown"] += 1
        for species in (row.get("species_mentions") or "").split(";"):
            species = species.strip()
            if species:
                species_counter[species] += 1

    pulse_score = round(min(100.0, weighted_total * 18.0))
    top_species = [{"species": species, "count": count} for species, count in species_counter.most_common(5)]
    platforms = [{"platform": platform, "count": count} for platform, count in platform_counter.most_common(5)]
    matched_areas = [{"area": area, "count": count} for area, count in area_counter.most_common(5)]

    return {
        "available": True,
        "role": "context_only",
        "score_adjustment_allowed": False,
        "source": "legacy_social_intel",
        "data_dir": str(resolved_data_dir),
        "nearest_signal_area": nearest.key,
        "nearest_signal_family": nearest.family,
        "latest_signal_date": None if latest_seen is None else latest_seen.isoformat(),
        "recent_window_days": recent_days,
        "recent_report_count": recent_count,
        "pulse_score": pulse_score,
        "pulse_level": _pulse_level(pulse_score),
        "top_species": top_species,
        "platforms": platforms,
        "matched_areas": matched_areas,
        "message": "Social signals are used as context only, not as direct score truth.",
    }
