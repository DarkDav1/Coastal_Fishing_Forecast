"""Frontend-oriented response facade for forecast consumers."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any, Mapping

from coastal_fishing_forecast.forecast import build_range_forecast
from coastal_fishing_forecast.github_models import GitHubModelsError, generate_github_models_explanation_text
from coastal_fishing_forecast.planner import build_fishing_plan
from coastal_fishing_forecast.social_pulse import build_social_pulse
from coastal_fishing_forecast.structures import (
    fetch_combined_structure_facilities,
    fetch_list_mast_structure_facilities,
    fetch_list_wildfisheries_sea_spots,
    fetch_osm_structure_facilities,
)


API_CONTRACT_VERSION = "2026-04-27.frontend.v1"
FRONTEND_STRUCTURE_RADIUS_KM = 5.0
WATER_TYPE_LABELS = {
    "beach": "Beach",
    "rocks": "Rocks",
    "jetty": "Jetty",
    "bay_estuary_edge": "Bay / estuary edge",
}
NEGATIVE_REASON_MARKERS = (
    "penalty",
    "caution",
    "dirty",
    "dead",
    "exposed",
    "cap",
    "weak",
    "hard",
    "slack",
    "small",
    "cold",
    "shock",
    "rapid",
    "severe",
    "gust",
    "big_wave",
    "swell",
    "rough",
    "trend_break",
    "interrupted",
)
SUPPORTED_EXPLANATION_PROVIDERS = {"rule_based", "github_models", "llm"}
INTERNAL_EXPLANATION_TERMS = (
    "raw time signal",
    "raw_time",
    "local_adjusted",
    "score_breakdown",
    "reason_tags",
    "rule_tags",
    "scoring rule",
    "model rule",
    "adjustment_delta",
    "driver",
    "原始时间分",
    "本地修正分",
    "规则标签",
    "评分规则",
)

# Combo release: when the engine is genuinely confident AND the day already
# scores high, lift the public preview cap of 86.5 up to a hard ceiling of 95.
# Confidence stays internal (never shown to the user); it only acts as a gate
# that unlocks an upper boost when several independent axes align.
COMBO_HARD_CEILING = 95
COMBO_GATE_ACTIVITY = 78
COMBO_GATE_PRESENCE = 74
COMBO_GATE_TRIP_QUALITY = 68
COMBO_GATE_SEARCH_CONFIDENCE = 0.55
COMBO_REMOTE_STATION_KM = 50.0
REAL_TIDE_SOURCES = frozenset({"tidesatlas", "tide_events", "tide_events_file"})
COMBO_BLOCKING_TAGS = frozenset(
    {
        "recent_weather_shock",
        "strong_wind_penalty",
        "harsh_midday_penalty",
        "heavy_rain_disruption",
        "strong_rain_penalty",
        "major_rain_shock",
        "big_wave_beach",
        "ocean_influenced_estuary_swell_penalty",
        "open_bay_swell_cap",
        "rough_open_bay_cap",
        "trend_breaking_cold_change",
        "severe_multi_day_cold_break",
        "rapid_pressure_change_24h",
        "rapid_pressure_change_6h",
        "multi_day_pressure_break",
        "strong_wind_shift",
        "recent_heavy_rain_shock",
        "multi_day_rain_disruption",
        "dead_water_2h",
        "weak_tide_movement_3h",
        "weak_tide_rate",
        "small_tide_range",
        "slack_tide_penalty",
        "offshore_push_away",
        "wind_presentation_penalty",
        "rapid_temperature_drop",
    }
)
COMBO_MOVEMENT_TAGS = frozenset(
    {"rising_tide_window", "early_flood_bonus", "strong_local_tide_flow", "large_tide_range", "falling_tide_window"}
)
COMBO_TIMING_TAGS = frozenset({"sunrise_window", "sunset_window", "dawn_window", "dusk_window"})
COMBO_WEATHER_CLEAN_TAGS = frozenset(
    {
        "stable_pressure_bonus",
        "moderate_wind_bonus",
        "cloud_cover_bonus",
        "water_temp_optimal",
        "pressure_rising",
        "pressure_falling",
        "weather_recovery_window",
    }
)
COMBO_STRUCTURE_CATEGORIES = frozenset({"complex_edge_with_moving_water", "modest_edge_flow"})
COMBO_BLOCKING_WIND_CATEGORIES = frozenset(
    {"direction_unknown", "geometry_uncertain", "offshore_or_push_away", "exposed_presentation_risk"}
)
COMBO_OPEN_COAST_TYPES = frozenset({"beach", "rocks"})
COMBO_OPEN_COAST_MAX_WAVE_M = 0.8
COMBO_OPEN_COAST_MAX_WIND_KNOTS = 14.0


def _location(lat: float, lon: float) -> dict[str, Any]:
    return {
        "display_name": f"{lat:.4f}, {lon:.4f}",
        "source": "coordinate_input",
        "coordinates": {"latitude": lat, "longitude": lon},
    }


def _best_window(windows: list[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    ok_windows = [window for window in windows if window["preview"]["status"] == "ok"]
    if not ok_windows:
        return None
    return max(ok_windows, key=lambda window: window["preview"]["overall_recommendation"].get("trip_quality_score") or 0)


def _tide_verification(data_sources: Mapping[str, Any]) -> dict[str, Any]:
    tide_source = data_sources.get("tide")
    if tide_source == "tidesatlas":
        provider = data_sources.get("tide_provider") or {}
        port_distance = provider.get("port_distance_km")
        if port_distance is not None and float(port_distance) > 50.0:
            return {
                "status": "live_verified_remote_station",
                "source": "tidesatlas",
                "message": "Real tide events came from TidesAtlas, but the selected tide station is distant from the searched coordinate.",
                "station_distance_km": port_distance,
            }
        return {
            "status": "live_verified",
            "source": "tidesatlas",
            "message": "Real tide events came from TidesAtlas.",
            "station_distance_km": port_distance,
        }
    if tide_source in {"tide_events", "tide_events_file"}:
        return {
            "status": "provided_events",
            "source": tide_source,
            "message": "Real tide events were supplied to the engine.",
        }
    if tide_source == "openmeteo_model":
        return {
            "status": "model_estimated",
            "source": "openmeteo_model",
            "message": "Tide phase is inferred from Open-Meteo model sea-level data, not a local tide station.",
        }
    return {
        "status": "estimated",
        "source": "astronomical_approximation",
        "message": "Tide phase is estimated, not verified against a real tide table.",
    }


def _confidence(range_forecast: Mapping[str, Any]) -> dict[str, Any]:
    best = _best_window(list(range_forecast["windows"]))
    if best is None:
        return {"score": 0, "label": "unsupported", "factors": ["Location is unsupported."]}

    preview = best["preview"]
    data_sources = range_forecast["data_sources"]
    support_mode = preview["meta"]["support_profile"]["support_mode"]
    search_confidence = float(preview["meta"].get("search_confidence_score", 0.35))
    tide_status = _tide_verification(data_sources)["status"]
    model_environment = preview.get("meta", {}).get("environment", {})
    inputs_used = model_environment.get("inputs_used", {})
    normalized = model_environment.get("normalized", {})
    coastline_metrics = preview.get("meta", {}).get("coastline_metrics", {})

    score = 25 + (search_confidence * 30)
    factors = ["Searched-coordinate forecast, not a curated hotspot."]
    limitations: list[str] = []
    caps: list[dict[str, Any]] = []

    def apply_cap(cap: int, reason: str) -> None:
        caps.append({"cap": cap, "reason": reason})

    if support_mode == "on_water":
        score += 14
        factors.append("Coordinate is on supported coastal or tidal water.")
    elif support_mode == "near_water":
        score += 8
        factors.append("Coordinate is near supported coastal or tidal water.")
    elif support_mode == "tidal_corridor":
        score += 4
        factors.append("Coordinate uses cautious tidal-corridor support.")

    if data_sources.get("conditions") == "open_meteo":
        score += 10
        factors.append("Weather and marine conditions are loaded from an external provider.")
    if tide_status in {"live_verified", "provided_events"}:
        score += 16
        factors.append("Tide phase is based on real high/low tide events.")
    elif tide_status == "live_verified_remote_station":
        score += 8
        factors.append("Tide phase is based on real high/low tide events, but the tide station is distant.")
    elif tide_status == "model_estimated":
        score += 7
        factors.append("Tide phase is inferred from model sea-level data, not a local tide station.")
        limitations.append("Tide timing is model-estimated rather than verified against a local tide station.")
        apply_cap(60, "Model sea-level tide proxy.")
    else:
        score += 3
        factors.append("Tide phase is estimated, lowering confidence.")
        limitations.append("Tide timing is estimated rather than verified.")
        apply_cap(52, "Estimated tide phase.")

    if tide_status == "live_verified_remote_station":
        limitations.append("Tide events came from a distant station.")
        apply_cap(64, "Distant tide station.")

    if data_sources.get("conditions") != "open_meteo":
        limitations.append("Weather and marine conditions were supplied or replayed rather than freshly fetched by the API.")

    if int(data_sources.get("weather_trend_lookback_days") or 0) < 3:
        limitations.append("Recent multi-day weather trend history is incomplete.")
        apply_cap(58, "Incomplete recent weather trend.")

    wind_category = str(inputs_used.get("wind_to_shore_category") or "")
    if wind_category in {"direction_unknown", "geometry_uncertain"}:
        limitations.append("Wind-to-shore relationship is uncertain for this coordinate.")
        apply_cap(62, "Uncertain wind-to-shore geometry.")

    if coastline_metrics.get("open_water_bearing_deg") is None:
        limitations.append("Broad shoreline direction could not be inferred confidently.")
        apply_cap(58, "Unclear broad shoreline direction.")

    if search_confidence < 0.45:
        limitations.append("The searched point is supported, but the local water/shoreline match is broad.")
        apply_cap(54, "Low searched-coordinate geometry confidence.")

    if float(normalized.get("weather_shock", 0.0) or 0.0) >= 3.0:
        limitations.append("Recent weather changed enough to make the local bite less certain.")
        apply_cap(60, "Recent weather instability.")

    structure_category = str(inputs_used.get("structure_flow_category") or "")
    if structure_category in {"complex_edge_with_moving_water", "modest_edge_flow"}:
        limitations.append("Structure and edge effects are inferred from broad shoreline shape, not confirmed as exact features.")
        apply_cap(64, "Inferred structure or edge-water signal.")

    cap_value = min([82, *[item["cap"] for item in caps]])
    final_score = round(max(0, min(cap_value, score)))
    label = "medium" if final_score >= 60 else "low"
    return {
        "score": final_score,
        "label": label,
        "factors": factors,
        "limitations": limitations,
        "caps_applied": caps,
    }


def _expanded_water_types(window: Mapping[str, Any]) -> list[dict[str, Any]]:
    scores = window.get("water_type_scores", {})
    tide_phase = window["environment"].get("tide_phase")
    expanded = [
        {
            "key": "surf_beach",
            "label": "Surf beach",
            "parent": "beach",
            "score": scores.get("beach"),
            "derived": True,
        },
        {
            "key": "open_rocks",
            "label": "Open rocks",
            "parent": "rocks",
            "score": scores.get("rocks"),
            "derived": True,
        },
        {
            "key": "jetty_wharf",
            "label": "Jetty / wharf",
            "parent": "jetty",
            "score": scores.get("jetty"),
            "derived": True,
        },
        {
            "key": "bay_edge",
            "label": "Bay edge",
            "parent": "bay_estuary_edge",
            "score": scores.get("bay_estuary_edge"),
            "derived": True,
        },
        {
            "key": "estuary_edge",
            "label": "Estuary edge",
            "parent": "bay_estuary_edge",
            "score": None if scores.get("bay_estuary_edge") is None else scores["bay_estuary_edge"] + (2 if tide_phase in {"rising", "falling"} else -2),
            "derived": True,
        },
        {
            "key": "channel_edge",
            "label": "Channel edge",
            "parent": "bay_estuary_edge",
            "score": None
            if scores.get("bay_estuary_edge") is None or scores.get("jetty") is None
            else round((scores["bay_estuary_edge"] + scores["jetty"]) / 2),
            "derived": True,
        },
    ]
    return sorted(
        [item for item in expanded if item["score"] is not None],
        key=lambda item: item["score"],
        reverse=True,
    )


def _behavior_groups(window: Mapping[str, Any]) -> list[dict[str, Any]]:
    scores = window.get("water_type_scores", {})
    groups = [
        {
            "key": "beach_roaming_fish",
            "label": "Beach roaming fish",
            "score": scores.get("beach"),
            "reason": "Best represented by open beach movement and roaming opportunity.",
        },
        {
            "key": "estuary_resident_fish",
            "label": "Estuary resident fish",
            "score": scores.get("bay_estuary_edge"),
            "reason": "Best represented by bay and estuary-edge holding water.",
        },
        {
            "key": "structure_fish",
            "label": "Structure fish",
            "score": max(scores.get("jetty", 0), scores.get("bay_estuary_edge", 0)),
            "reason": "Best represented by jetties, wharves, edges, and nearby structure.",
        },
        {
            "key": "rock_edge_fish",
            "label": "Rock edge fish",
            "score": scores.get("rocks"),
            "reason": "Best represented by exposed rock-edge opportunity.",
        },
    ]
    return sorted(
        [group for group in groups if group["score"] is not None],
        key=lambda group: group["score"],
        reverse=True,
    )


def _number(value: Any) -> float | None:
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None


def _weather_change_notes(inputs_used: Mapping[str, Any]) -> list[str]:
    notes: list[str] = []
    temperature_drop = _number(inputs_used.get("temperature_drop_from_recent_72h_peak"))
    temperature_delta_24h = _number(inputs_used.get("temperature_delta_24h"))
    pressure_delta_6h = _number(inputs_used.get("pressure_delta_6h"))
    pressure_delta_24h = _number(inputs_used.get("pressure_delta_24h"))
    wind_direction_change = _number(inputs_used.get("wind_direction_change_12h"))
    rainfall_24h = _number(inputs_used.get("rainfall_24h"))
    rainfall_72h = _number(inputs_used.get("rainfall_72h"))
    max_gust_24h = _number(inputs_used.get("max_gust_24h"))
    wave_height_delta_24h = _number(inputs_used.get("wave_height_delta_24h"))

    if temperature_drop is not None and temperature_drop <= -4.5:
        notes.append("Air temperature has dropped sharply from the recent warm period.")
    elif temperature_delta_24h is not None and temperature_delta_24h <= -4:
        notes.append("Air temperature has fallen noticeably over the last day.")

    if pressure_delta_24h is not None and abs(pressure_delta_24h) >= 8:
        notes.append("Pressure has moved quickly over the last day.")
    elif pressure_delta_6h is not None and abs(pressure_delta_6h) >= 4:
        notes.append("Pressure is changing quickly in the current window.")

    if wind_direction_change is not None and wind_direction_change >= 90:
        notes.append("Wind direction has shifted strongly in the last half day.")

    if rainfall_24h is not None and rainfall_24h >= 30:
        notes.append("Heavy recent rain may have disrupted inshore water conditions.")
    elif rainfall_72h is not None and rainfall_72h >= 45:
        notes.append("Recent multi-day rain may still be affecting the water.")

    if max_gust_24h is not None and max_gust_24h * 1.852 >= 45:
        notes.append("Recent strong gusts may have unsettled exposed water.")

    if wave_height_delta_24h is not None and abs(wave_height_delta_24h) >= 0.6:
        notes.append("The sea state has changed quickly compared with the previous day.")

    return notes[:5]


def _condition_strip(window: Mapping[str, Any]) -> dict[str, Any]:
    env = window["environment"]
    model_environment = window.get("preview", {}).get("meta", {}).get("environment", {})
    inputs_used = model_environment.get("inputs_used", {})
    normalized = model_environment.get("normalized", {})
    generic_rules = model_environment.get("generic_rules", {})
    return {
        "wind": {
            "speed_knots": env["wind_speed_knots"],
            "direction_deg": env["wind_direction_deg"],
            "gust_knots": inputs_used.get("wind_gust_knots"),
            "recent_max_12h": inputs_used.get("recent_wind_max_12h"),
            "onshore_knots": inputs_used.get("wind_onshore_knots"),
            "offshore_knots": inputs_used.get("wind_offshore_knots"),
            "alongshore_knots": inputs_used.get("wind_alongshore_knots"),
        },
        "swell": {
            "height_m": env["swell_height_m"],
            "direction_deg": env["swell_direction_deg"],
            "wave_height_m": inputs_used.get("wave_height_m"),
            "wave_height_delta_24h": inputs_used.get("wave_height_delta_24h"),
        },
        "pressure_hpa": env["pressure_hpa"],
        "pressure_delta_3h": inputs_used.get("pressure_delta_3h"),
        "weather_trend": {
            "pressure_delta_6h": inputs_used.get("pressure_delta_6h"),
            "pressure_delta_24h": inputs_used.get("pressure_delta_24h"),
            "pressure_delta_48h": inputs_used.get("pressure_delta_48h"),
            "pressure_delta_72h": inputs_used.get("pressure_delta_72h"),
            "temperature_delta_24h": inputs_used.get("temperature_delta_24h"),
            "temperature_delta_48h": inputs_used.get("temperature_delta_48h"),
            "temperature_delta_72h": inputs_used.get("temperature_delta_72h"),
            "temperature_drop_from_recent_72h_peak": inputs_used.get("temperature_drop_from_recent_72h_peak"),
            "wind_direction_change_12h": inputs_used.get("wind_direction_change_12h"),
            "max_gust_24h": inputs_used.get("max_gust_24h"),
            "max_gust_72h": inputs_used.get("max_gust_72h"),
            "rainfall_24h": inputs_used.get("rainfall_24h"),
            "rainfall_48h": inputs_used.get("rainfall_48h"),
            "rainfall_72h": inputs_used.get("rainfall_72h"),
            "change_notes": _weather_change_notes(inputs_used),
        },
        "air": {
            "temperature_c": inputs_used.get("temperature_c"),
            "rain_mm": inputs_used.get("rain_mm"),
            "precipitation_mm": inputs_used.get("precipitation_mm"),
            "recent_precipitation_sum_12h": inputs_used.get("recent_precipitation_sum_12h"),
            "cloud_cover_pct": inputs_used.get("cloud_cover_pct"),
        },
        "marine": {
            "sea_surface_temperature_c": inputs_used.get("sea_surface_temperature_c"),
        },
        "tide": {
            "phase": env["tide_phase"],
            "source": window["tide_source"],
            "stage": inputs_used.get("tide_stage"),
            "range_m": inputs_used.get("tide_range_m"),
            "height_m": inputs_used.get("tide_height_m"),
            "movement_rate_m_per_hour": inputs_used.get("tide_movement_rate_m_per_hour"),
            "hours_to_high_tide": inputs_used.get("hours_to_high_tide"),
            "hours_to_low_tide": inputs_used.get("hours_to_low_tide"),
            "hours_since_low_tide": inputs_used.get("hours_since_low_tide"),
        },
        "solar": {
            "hour_of_day": inputs_used.get("hour_of_day"),
            "hours_from_sunrise": inputs_used.get("hours_from_sunrise"),
            "hours_from_sunset": inputs_used.get("hours_from_sunset"),
            "hours_from_solar_noon": inputs_used.get("hours_from_solar_noon"),
            "is_daylight": inputs_used.get("is_daylight"),
        },
        "moon": {
            "phase_name": inputs_used.get("moon_phase_name"),
            "illumination_pct": inputs_used.get("moon_illumination_pct"),
        },
        "formula": {
            "normalized": normalized,
            "raw_time_signal": model_environment.get("raw_time_signal"),
            "rules": generic_rules.get("rules", []),
            "score_delta": generic_rules.get("score_delta"),
            "family": generic_rules.get("family"),
        },
    }


def _split_reason_tags(tags: list[str]) -> tuple[list[str], list[str]]:
    negative: list[str] = []
    positive: list[str] = []
    for tag in tags:
        target = negative if any(marker in tag for marker in NEGATIVE_REASON_MARKERS) else positive
        target.append(tag)
    return positive, negative


def _window_card(window: Mapping[str, Any]) -> dict[str, Any]:
    preview = window["preview"]
    overall = preview.get("overall_recommendation") or {}
    positive_tags, negative_tags = _split_reason_tags(overall.get("reason_tags", []))
    water_scores = [
        {
            "key": key,
            "label": WATER_TYPE_LABELS.get(key, key),
            "score": score,
        }
        for key, score in window.get("water_type_scores", {}).items()
    ]
    water_scores.sort(key=lambda item: item["score"], reverse=True)
    return {
        "date": window["date"],
        "time_window": window["time_window"],
        "representative_time": window["representative_time"],
        "status": preview["status"],
        "score": overall.get("score"),
        "activity_score": overall.get("activity_score"),
        "presence_score": overall.get("presence_score"),
        "trip_quality_score": overall.get("trip_quality_score"),
        "big_fish_near_shore": overall.get("big_fish_near_shore"),
        "label": overall.get("label"),
        "model_rule_family": overall.get("model_rule_family"),
        "score_breakdown": overall.get("score_breakdown"),
        "reason_tags": overall.get("reason_tags", []),
        "positive_reason_tags": positive_tags,
        "negative_reason_tags": negative_tags,
        "dominant_water_type": overall.get("dominant_inferred_type"),
        "water_type_scores": water_scores,
        "expanded_water_types": _expanded_water_types(window),
        "behavior_groups": _behavior_groups(window),
        "conditions": _condition_strip(window),
    }


def _daily_cards(windows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_date: dict[str, list[Mapping[str, Any]]] = {}
    for window in windows:
        by_date.setdefault(window["date"], []).append(window)

    cards = []
    for day, day_windows in sorted(by_date.items()):
        best = _best_window(list(day_windows))
        cards.append(
            {
                "date": day,
                "best_window": None if best is None else _window_card(best),
                "windows": [_window_card(window) for window in day_windows],
            }
        )
    return cards


def _hero(range_forecast: Mapping[str, Any]) -> dict[str, Any]:
    best = _best_window(list(range_forecast["windows"]))
    if best is None:
        return {
            "score": None,
            "label": "Unsupported location",
            "headline": "This location is outside the current coastal and tidal forecast scope.",
            "best_window": None,
        }

    overall = best["preview"]["overall_recommendation"]
    dominant = WATER_TYPE_LABELS.get(overall["dominant_inferred_type"], overall["dominant_inferred_type"])
    return {
        "score": overall["score"],
        "label": overall["label"],
        "headline": f"{dominant} is the strongest nearby option.",
        "best_window": _window_card(best),
    }


def _rule_based_explanation(range_forecast: Mapping[str, Any]) -> dict[str, Any]:
    best = _best_window(list(range_forecast["windows"]))
    if best is None:
        return {
            "source": "rule_based",
            "explanation_provider": "rule_based",
            "why_this_window": ["No supported coastal or tidal forecast window was available."],
            "risks": ["The searched coordinate is outside the current supported scope."],
            "alternatives": [],
        }

    card = _window_card(best)
    conditions = card["conditions"]
    risks = []
    if conditions["tide"]["source"] == "astronomical_approximation":
        risks.append("Tide phase is estimated, so tide-sensitive guidance has lower confidence.")
    if conditions["tide"]["source"] == "openmeteo_model":
        risks.append("Tide phase is inferred from model sea-level data, not a local tide station.")
    if conditions["swell"]["height_m"] >= 1.8:
        risks.append("Higher swell may reduce comfort and safety on exposed beaches and rocks.")
    if conditions["wind"]["speed_knots"] >= 18:
        risks.append("Stronger wind may reduce trip quality, especially on exposed water.")
    if not risks:
        risks.append("No major broad-condition risk was detected for the best window.")

    alternatives = [
        {
            "label": item["label"],
            "score": item["score"],
            "reason": "Secondary inferred water type to consider nearby.",
        }
        for item in card["expanded_water_types"][1:4]
    ]
    return {
        "source": "rule_based",
        "explanation_provider": "rule_based",
        "why_this_window": [
            f"{card['time_window']} has the strongest overall score in this forecast range.",
            f"{card['dominant_water_type']} is the leading broad water-type signal.",
            f"{card['behavior_groups'][0]['label']} is the strongest fish-behavior group.",
        ],
        "risks": risks,
        "alternatives": alternatives,
    }


def _time_signal_note(label: str | None) -> str:
    return {
        "strong_time_signal": "The time of day itself is helpful.",
        "useful_time_signal": "The time of day gives some support.",
        "neutral_time_signal": "The time of day is fairly neutral.",
        "weak_time_signal": "The time of day is not a major advantage.",
    }.get(str(label or ""), "The time of day is fairly neutral.")


def _plain_score_context(card: Mapping[str, Any]) -> dict[str, Any]:
    breakdown = card.get("score_breakdown") or {}
    helped_by: list[str] = []
    held_back_by: list[str] = []
    for driver in breakdown.get("drivers") or []:
        if not isinstance(driver, Mapping):
            continue
        label = str(driver.get("label") or "").strip()
        if not label:
            continue
        if driver.get("type") == "positive":
            helped_by.append(label)
        elif driver.get("type") == "negative":
            held_back_by.append(label)

    return {
        "final_score": card.get("score"),
        "score_label": card.get("label"),
        "time_of_day_note": _time_signal_note(breakdown.get("raw_time_signal_label")),
        "helped_by": helped_by[:4],
        "held_back_by": held_back_by[:4],
    }


def _plain_conditions_for_explanation(conditions: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(conditions, Mapping):
        return {}
    return {
        "wind": conditions.get("wind"),
        "swell": conditions.get("swell"),
        "pressure_hpa": conditions.get("pressure_hpa"),
        "pressure_delta_3h": conditions.get("pressure_delta_3h"),
        "weather_trend": conditions.get("weather_trend"),
        "air": conditions.get("air"),
        "marine": conditions.get("marine"),
        "tide": conditions.get("tide"),
        "solar": conditions.get("solar"),
        "moon": conditions.get("moon"),
    }


def _frontend_structure_facility(item: Mapping[str, Any]) -> dict[str, Any]:
    """Keep only structure fields the app renders or planner needs."""
    compact: dict[str, Any] = {
        "id": item.get("id"),
        "type": item.get("type"),
        "label": item.get("label"),
        "access": item.get("access"),
        "status": item.get("status"),
        "source": item.get("source"),
        "distance_km": item.get("distance_km"),
        "planner_eligible": item.get("planner_eligible"),
        "map_eligible": item.get("map_eligible"),
        "role": item.get("role"),
    }
    coordinates = item.get("coordinates")
    if isinstance(coordinates, Mapping):
        compact["coordinates"] = {
            "latitude": coordinates.get("latitude"),
            "longitude": coordinates.get("longitude"),
        }
    return {key: value for key, value in compact.items() if value is not None}


def _is_frontend_structure_facility(item: Mapping[str, Any]) -> bool:
    distance_km = item.get("distance_km")
    if distance_km is None:
        return True
    try:
        return float(distance_km) <= FRONTEND_STRUCTURE_RADIUS_KM
    except (TypeError, ValueError):
        return True


def _frontend_structure_data(data: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if data is None:
        return None
    compact = {
        "contract_version": data.get("contract_version"),
        "source": data.get("source"),
        "status": data.get("status"),
        "sources": data.get("sources"),
        "query": data.get("query"),
    }
    return {key: value for key, value in compact.items() if value is not None}


def _whitelisted_explanation_input(rule_explanation: Mapping[str, Any], range_forecast: Mapping[str, Any]) -> dict[str, Any]:
    best = _best_window(list(range_forecast["windows"]))
    if best is None:
        return {"rule_explanation": rule_explanation}
    card = _window_card(best)
    return {
        "best_window": {
            "date": card.get("date"),
            "time_window": card.get("time_window"),
            "score": card.get("score"),
            "activity_score": card.get("activity_score"),
            "presence_score": card.get("presence_score"),
            "trip_quality_score": card.get("trip_quality_score"),
            "label": card.get("label"),
            "dominant_water_type": card.get("dominant_water_type"),
            "behavior_groups": card.get("behavior_groups"),
            "plain_score_context": _plain_score_context(card),
        },
        "conditions": _plain_conditions_for_explanation(card.get("conditions")),
        "rule_explanation": {
            "why_this_window": rule_explanation.get("why_this_window"),
            "risks": rule_explanation.get("risks"),
            "alternatives": rule_explanation.get("alternatives"),
        },
        "data_sources": {
            "conditions": range_forecast.get("data_sources", {}).get("conditions"),
            "tide": range_forecast.get("data_sources", {}).get("tide"),
        },
    }


def _clean_explanation_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    if _has_internal_explanation_terms(cleaned):
        return None
    return cleaned if cleaned else None


def _has_internal_explanation_terms(value: str) -> bool:
    lowered = value.lower()
    return any(term in lowered for term in INTERNAL_EXPLANATION_TERMS)


def _clean_explanation_list(value: Any) -> list[str] | None:
    if not isinstance(value, list):
        return None
    cleaned = [
        item.strip()
        for item in value
        if isinstance(item, str) and item.strip() and not _has_internal_explanation_terms(item)
    ]
    if not 2 <= len(cleaned) <= 4:
        return None
    return cleaned


def _merge_model_explanation(rule_explanation: Mapping[str, Any], model_text: Mapping[str, Any]) -> dict[str, Any]:
    why_this_window = _clean_explanation_list(model_text.get("why_this_window"))
    score_story = _clean_explanation_text(model_text.get("score_story"))
    local_adjustment_summary = _clean_explanation_text(model_text.get("local_adjustment_summary"))
    if why_this_window is None and score_story is None and local_adjustment_summary is None:
        raise ValueError("GitHub Models explanation response did not include usable explanation fields.")
    merged = dict(rule_explanation)
    merged["source"] = "github_models"
    merged["explanation_provider"] = "github_models"
    if why_this_window is not None:
        merged["why_this_window"] = why_this_window
    if score_story:
        merged["score_story"] = score_story
    if local_adjustment_summary:
        merged["local_adjustment_summary"] = local_adjustment_summary
    return merged


def _explanation(range_forecast: Mapping[str, Any], *, explanation_provider: str = "rule_based") -> dict[str, Any]:
    if explanation_provider not in SUPPORTED_EXPLANATION_PROVIDERS:
        raise ValueError("explanation_provider must be one of: rule_based, llm, github_models")

    rule_explanation = _rule_based_explanation(range_forecast)
    if explanation_provider == "rule_based":
        return rule_explanation

    try:
        model_input = _whitelisted_explanation_input(rule_explanation, range_forecast)
        model_text = generate_github_models_explanation_text(model_input)
        return _merge_model_explanation(rule_explanation, model_text)
    except (GitHubModelsError, OSError, TimeoutError, ValueError, KeyError, TypeError):
        return rule_explanation


def _location_combo_prerequisites(
    preview: Mapping[str, Any] | None,
    data_sources: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Location-level gates that don't change between windows.

    Returns the prerequisites bundle when the location qualifies for combo
    release evaluation, or None when any structural gate fails. This is the
    "confidence" half of the combo: only locations with on-water support,
    real tide events, and clear shoreline geometry are eligible.
    """
    if not preview or preview.get("status") != "ok":
        return None
    meta = preview.get("meta") or {}
    support_profile = meta.get("support_profile") or {}
    if support_profile.get("support_mode") != "on_water":
        return None
    tide_source = data_sources.get("tide")
    if tide_source not in REAL_TIDE_SOURCES:
        return None
    if tide_source == "tidesatlas":
        provider = data_sources.get("tide_provider") or {}
        port_distance = provider.get("port_distance_km")
        try:
            if port_distance is not None and float(port_distance) > COMBO_REMOTE_STATION_KM:
                return None
        except (TypeError, ValueError):
            return None
    search_confidence = float(meta.get("search_confidence_score") or 0.0)
    if search_confidence < COMBO_GATE_SEARCH_CONFIDENCE:
        return None
    coastline = meta.get("coastline_metrics") or {}
    if coastline.get("open_water_bearing_deg") is None:
        return None
    return {"search_confidence": search_confidence}


def _window_combo_evaluation(
    preview: Mapping[str, Any],
    prereqs: Mapping[str, Any] | None,
) -> tuple[int, str | None]:
    """Per-window combo evaluation. Returns (boost, tag) or (0, None)."""
    if prereqs is None:
        return 0, None
    overall = preview.get("overall_recommendation") or {}
    if not overall:
        return 0, None
    activity = float(overall.get("activity_score") or 0)
    presence = float(overall.get("presence_score") or 0)
    trip = float(overall.get("trip_quality_score") or 0)
    if activity < COMBO_GATE_ACTIVITY or presence < COMBO_GATE_PRESENCE or trip < COMBO_GATE_TRIP_QUALITY:
        return 0, None

    meta = preview.get("meta") or {}
    environment = meta.get("environment") or {}
    inputs_used = environment.get("inputs_used") or {}
    normalized = environment.get("normalized") or {}
    tags = set(overall.get("reason_tags") or [])

    if tags & COMBO_BLOCKING_TAGS:
        return 0, None
    if float(normalized.get("weather_shock") or 0.0) >= 1.5:
        return 0, None

    wind_category = str(inputs_used.get("wind_to_shore_category") or "")
    if wind_category in COMBO_BLOCKING_WIND_CATEGORIES:
        return 0, None

    movement_aligned = bool(tags & COMBO_MOVEMENT_TAGS)
    timing_aligned = bool(tags & COMBO_TIMING_TAGS)
    weather_clean_axis = bool(tags & COMBO_WEATHER_CLEAN_TAGS)
    structure_category = str(inputs_used.get("structure_flow_category") or "")
    structure_aligned = structure_category in COMBO_STRUCTURE_CATEGORIES
    aligned = sum((movement_aligned, timing_aligned, weather_clean_axis, structure_aligned))
    if aligned < 3:
        return 0, None

    dominant_type = overall.get("dominant_inferred_type")
    if dominant_type in COMBO_OPEN_COAST_TYPES:
        wave = float(inputs_used.get("wave_height_m") or inputs_used.get("swell_height_m") or 0.0)
        wind_kts = float(inputs_used.get("wind_speed_knots") or 0.0)
        if wave > COMBO_OPEN_COAST_MAX_WAVE_M or wind_kts > COMBO_OPEN_COAST_MAX_WIND_KNOTS:
            return 0, None

    if aligned >= 4:
        return 8, "rare_alignment_window"
    return 5, "strong_alignment_window"


def _apply_window_combo(
    window: Mapping[str, Any],
    prereqs: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    preview = window.get("preview") or {}
    boost, tag = _window_combo_evaluation(preview, prereqs)
    if boost <= 0 or tag is None:
        return None
    overall = preview.get("overall_recommendation")
    if not overall:
        return None
    original = int(overall.get("score") or 0)
    new_score = min(COMBO_HARD_CEILING, original + boost)
    if new_score <= original:
        return None
    overall["score"] = new_score
    existing_tags = list(overall.get("reason_tags") or [])
    if tag not in existing_tags:
        existing_tags.append(tag)
        overall["reason_tags"] = existing_tags
    overall["combo_release"] = {
        "applied": True,
        "tag": tag,
        "boost": boost,
        "original_score": original,
        "boosted_score": new_score,
    }
    return overall["combo_release"]


def _hourly_combo_axes(rule_tags: set[str]) -> int:
    return sum(
        (
            bool(rule_tags & COMBO_MOVEMENT_TAGS),
            bool(rule_tags & COMBO_TIMING_TAGS),
            bool(rule_tags & COMBO_WEATHER_CLEAN_TAGS),
        )
    )


def _apply_hourly_combo(
    point: dict[str, Any],
    prereqs: Mapping[str, Any] | None,
) -> bool:
    if prereqs is None:
        return False
    activity = point.get("activity_score") or 0
    if activity < COMBO_GATE_ACTIVITY:
        return False
    rule_tags = set(point.get("rule_tags") or [])
    if rule_tags & COMBO_BLOCKING_TAGS:
        return False
    aligned = _hourly_combo_axes(rule_tags)
    if aligned < 2:
        return False
    original = int(point.get("score") or 0)
    boost = 7 if aligned >= 3 else 4
    new_score = min(COMBO_HARD_CEILING, original + boost)
    if new_score <= original:
        return False
    point["score"] = new_score
    tag = "rare_alignment_window" if aligned >= 3 else "strong_alignment_window"
    if tag not in rule_tags:
        existing = list(point.get("rule_tags") or [])
        existing.append(tag)
        point["rule_tags"] = existing
    return True


def _apply_combo_release(range_forecast: dict[str, Any]) -> dict[str, Any]:
    """Apply combo release to a range forecast in place.

    Returns a small summary dict with how many windows / hours were boosted.
    Mutates the dict so downstream hero / window cards / planner pick up the
    boosted scores naturally.
    """
    summary: dict[str, Any] = {
        "applied": False,
        "windows_boosted": 0,
        "hours_boosted": 0,
        "best_tag": None,
    }
    data_sources = range_forecast.get("data_sources") or {}
    windows = range_forecast.get("windows") or []
    if not windows:
        return summary

    prereqs = _location_combo_prerequisites(windows[0].get("preview"), data_sources)

    boosted_tags: list[str] = []
    for window in windows:
        result = _apply_window_combo(window, prereqs)
        if result is not None:
            summary["windows_boosted"] += 1
            boosted_tags.append(result["tag"])

    hourly = range_forecast.get("hourly_activity") or []
    for point in hourly:
        if _apply_hourly_combo(point, prereqs):
            summary["hours_boosted"] += 1

    if summary["windows_boosted"] == 0 and summary["hours_boosted"] == 0:
        return summary

    summary["applied"] = True
    if "rare_alignment_window" in boosted_tags:
        summary["best_tag"] = "rare_alignment_window"
    elif boosted_tags:
        summary["best_tag"] = "strong_alignment_window"

    if summary["windows_boosted"] > 0:
        forecast_summary = range_forecast.get("summary") or {}
        supported = [w for w in windows if (w.get("preview") or {}).get("status") == "ok"]
        if supported:
            scores = [
                int((w["preview"].get("overall_recommendation") or {}).get("score") or 0)
                for w in supported
            ]
            if scores:
                forecast_summary["average_score"] = round(sum(scores) / len(scores), 1)
        for entry in forecast_summary.get("best_windows", []):
            for window in windows:
                if window.get("date") == entry.get("date") and window.get("time_window") == entry.get("time_window"):
                    new_score = (window["preview"].get("overall_recommendation") or {}).get("score")
                    if new_score is not None:
                        entry["score"] = new_score
                    break

    return summary


def build_frontend_forecast_response(
    lat: float,
    lon: float,
    *,
    start_date: str | date,
    end_date: str | date,
    region: str | None = None,
    windows: tuple[str, ...] = ("morning", "dusk"),
    condition_data: Mapping[str, Any] | None = None,
    condition_source: str = "auto",
    tide_events: list[Mapping[str, Any]] | None = None,
    tide_events_file: str | None = None,
    tide_source: str = "auto",
    tidesatlas_api_key: str | None = None,
    planner_provider: str = "rule_based",
    explanation_provider: str = "rule_based",
    structure_facilities: list[Mapping[str, Any]] | None = None,
    structure_source: str = "none",
    structure_radius_m: int = 1200,
    cache_enabled: bool = True,
    cache_dir: str | Path | None = None,
) -> dict[str, Any]:
    range_forecast = build_range_forecast(
        lat,
        lon,
        start_date=start_date,
        end_date=end_date,
        region=region,
        windows=windows,
        condition_data=condition_data,
        condition_source=condition_source,
        tide_events=tide_events,
        tide_events_file=tide_events_file,
        tide_source=tide_source,
        tidesatlas_api_key=tidesatlas_api_key,
        cache_enabled=cache_enabled,
        cache_dir=cache_dir,
    )
    combo_release = _apply_combo_release(range_forecast)
    resolved_structure_facilities = list(structure_facilities or [])
    structure_data = None
    structure_fetchers = {
        "osm": fetch_osm_structure_facilities,
        "list_mast": fetch_list_mast_structure_facilities,
        "list_wildfisheries": fetch_list_wildfisheries_sea_spots,
        "auto": fetch_combined_structure_facilities,
    }
    if structure_source in structure_fetchers and not resolved_structure_facilities:
        try:
            structure_data = structure_fetchers[structure_source](
                lat,
                lon,
                radius_m=structure_radius_m,
                cache_enabled=cache_enabled,
                cache_dir=cache_dir,
            )
            resolved_structure_facilities = structure_data["facilities"]
        except (OSError, TimeoutError, ValueError, KeyError, TypeError):
            structure_data = {
                "source": structure_source,
                "status": "unavailable",
                "facilities": [],
            }

    social_pulse = build_social_pulse(lat, lon)
    frontend_structure_facilities = [
        _frontend_structure_facility(item)
        for item in resolved_structure_facilities
        if _is_frontend_structure_facility(item)
    ]

    response = {
        "api_contract_version": API_CONTRACT_VERSION,
        "forecast_contract_version": range_forecast["contract_version"],
        "input": range_forecast["input"],
        "location": _location(lat, lon),
        "data_sources": range_forecast["data_sources"],
        "tide_verification": _tide_verification(range_forecast["data_sources"]),
        "confidence": _confidence(range_forecast),
        "combo_release": combo_release,
        "hero": _hero(range_forecast),
        "explanation": _explanation(range_forecast, explanation_provider=explanation_provider),
        "summary": range_forecast["summary"],
        "daily_forecast": _daily_cards(list(range_forecast["windows"])),
        "hourly_activity": range_forecast.get("hourly_activity", []),
        "structure_facilities": frontend_structure_facilities,
        "structure_data": _frontend_structure_data(structure_data),
        "social_pulse": social_pulse,
        "modules": {
            "recommendation": True,
            "daily_cards": True,
            "window_cards": True,
            "weather": True,
            "marine": True,
            "tide": True,
            "map": bool(frontend_structure_facilities),
            "plan": True,
            "expanded_water_types": True,
            "behavior_groups": True,
            "confidence": True,
            "explanation": True,
            "social_pulse": bool(social_pulse.get("available")),
        },
    }
    response["plan"] = build_fishing_plan(response, planner_provider=planner_provider)
    return response
