"""Frontend-oriented response facade for forecast consumers."""

from __future__ import annotations

import math
from datetime import date
from pathlib import Path
from typing import Any, Mapping

from coastal_fishing_forecast.forecast import build_range_forecast
from coastal_fishing_forecast.github_models import GitHubModelsError, generate_github_models_explanation_text
from coastal_fishing_forecast.planner import build_fishing_plan
from coastal_fishing_forecast.preview import build_preview
from coastal_fishing_forecast.social_pulse import build_compact_pin_pulse, build_social_pulse
from coastal_fishing_forecast.structures import (
    fetch_combined_structure_facilities,
    fetch_list_mast_structure_facilities,
    fetch_list_wildfisheries_sea_spots,
    fetch_osm_structure_facilities,
)


PIN_FORECAST_EARTH_RADIUS_KM = 6371.0


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    dphi = math.radians(float(lat2) - float(lat1))
    dlam = math.radians(float(lon2) - float(lon1))
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2.0 * PIN_FORECAST_EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def _pin_environment_from_best_window(range_forecast: Mapping[str, Any]) -> Mapping[str, Any] | None:
    """Pull the environment dict from the search center's best window.

    Pins reuse this environment so we don't re-fetch weather / marine / tide
    for every map pin (the data is location-coarse anyway). Each pin still
    runs build_preview with its own coordinate so geometry signals
    (exposure / shelter / coastline complexity / open water bearing) are
    pin-specific.
    """
    best = _best_window(list(range_forecast.get("windows") or []))
    if best is None:
        return None
    env = best.get("environment")
    return env if isinstance(env, Mapping) else None


def _pin_forecast(
    *,
    pin_lat: float,
    pin_lon: float,
    search_lat: float,
    search_lon: float,
    environment: Mapping[str, Any] | None,
    region: str | None,
) -> dict[str, Any]:
    """Run a per-pin preview using the search center's environment.

    Returns a compact forecast dict suitable for embedding inside a
    structure_facilities entry. Always returns a dict (never None) so the
    frontend can rely on the field shape; sets `available: False` when the
    pin coordinate is outside supported scope.
    """
    distance_km_from_search = _haversine_km(search_lat, search_lon, pin_lat, pin_lon)
    base = {
        "available": False,
        "distance_km_from_search": round(distance_km_from_search, 2),
    }
    if environment is None:
        base["reason"] = "no_environment"
        return base
    try:
        preview = build_preview(pin_lat, pin_lon, environment=environment, region=region)
    except (TypeError, ValueError, KeyError):
        base["reason"] = "preview_error"
        return base
    status = preview.get("status")
    if status != "ok":
        support = preview.get("support") or {}
        base["reason"] = support.get("reason_code") or status or "unsupported"
        meta = preview.get("meta") or {}
        support_profile = meta.get("support_profile") or {}
        if support_profile.get("support_mode"):
            base["support_mode"] = support_profile["support_mode"]
        return base
    overall = preview.get("overall_recommendation") or {}
    meta = preview.get("meta") or {}
    support_profile = meta.get("support_profile") or {}
    # Pin-level social pulse: context_only, never adjusts the score. Crawler
    # coverage is sparse, so most pins will land with available=false; that
    # is the correct silent default rather than a fake signal.
    try:
        pin_pulse = build_compact_pin_pulse(pin_lat, pin_lon)
    except (OSError, ValueError, TypeError):
        pin_pulse = None
    return {
        "available": True,
        "distance_km_from_search": round(distance_km_from_search, 2),
        "score": overall.get("score"),
        "label": overall.get("label"),
        "fish_outlook_score": overall.get("fish_outlook_score"),
        "comfort_score": overall.get("comfort_score"),
        "comfort_factors": overall.get("comfort_factors", []),
        "safety_flag": overall.get("safety_flag"),
        "safety_factors": overall.get("safety_factors", []),
        "dominant_water_type": overall.get("dominant_inferred_type"),
        "waterbody_class": (meta.get("waterbody_classification") or {}).get("waterbody_class"),
        "classification_confidence": (meta.get("waterbody_classification") or {}).get("classification_confidence"),
        "fish_profile": (meta.get("environment") or {}).get("inputs_used", {}).get("fish_profile"),
        "support_mode": support_profile.get("support_mode"),
        "search_confidence_score": meta.get("search_confidence_score"),
        "recent_social_pulse": pin_pulse,
        "reason_summary": "Pin-specific geometry, shared weather/tide with search center.",
    }


def _augment_facilities_with_pin_forecast(
    facilities: list[dict[str, Any]],
    *,
    range_forecast: Mapping[str, Any],
    region: str | None,
    search_lat: float,
    search_lon: float,
) -> list[dict[str, Any]]:
    if not facilities:
        return facilities
    environment = _pin_environment_from_best_window(range_forecast)
    augmented: list[dict[str, Any]] = []
    for facility in facilities:
        coords = facility.get("coordinates") if isinstance(facility, Mapping) else None
        pin_lat = coords.get("latitude") if isinstance(coords, Mapping) else None
        pin_lon = coords.get("longitude") if isinstance(coords, Mapping) else None
        next_facility = dict(facility)
        if pin_lat is not None and pin_lon is not None:
            try:
                next_facility["pin_forecast"] = _pin_forecast(
                    pin_lat=float(pin_lat),
                    pin_lon=float(pin_lon),
                    search_lat=search_lat,
                    search_lon=search_lon,
                    environment=environment,
                    region=region,
                )
            except (TypeError, ValueError):
                pass
        augmented.append(next_facility)
    return augmented


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
    "cool",
    "hot",
    "shock",
    "rapid",
    "severe",
    "gust",
    "low_confidence",
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
        "low_confidence_current",
        "water_temp_cold",
        "water_temp_cooling_fast",
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
        "water_temp_stable",
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


def _window_selection_score(window: Mapping[str, Any]) -> float:
    overall = window["preview"]["overall_recommendation"]
    activity = overall.get("activity_score")
    presence = overall.get("presence_score")
    trip_quality = overall.get("trip_quality_score")
    if activity is None or presence is None or trip_quality is None:
        return float(overall.get("score") or 0)
    return (float(activity) * 0.40) + (float(presence) * 0.35) + (float(trip_quality) * 0.25)


def _best_window(windows: list[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    ok_windows = [window for window in windows if window["preview"]["status"] == "ok"]
    if not ok_windows:
        return None
    return max(ok_windows, key=_window_selection_score)


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

    current_confidence = str(inputs_used.get("tide_current_confidence") or "low")
    waterbody_class = str(inputs_used.get("waterbody_class") or "")
    if current_confidence == "low" and waterbody_class in {"river_mouth", "tidal_river"}:
        limitations.append("River and estuary current strength is inferred from tide height, not measured current.")
        apply_cap(62, "Low-confidence river/estuary current proxy.")

    temperature_confidence = str(inputs_used.get("temperature_confidence") or "low")
    if temperature_confidence == "low":
        limitations.append("Water-temperature trend is incomplete for this window.")
        apply_cap(68, "Incomplete water-temperature trend.")

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

    def environment_or_input(key: str) -> Any:
        value = env.get(key)
        return value if value is not None else inputs_used.get(key)

    return {
        "wind": {
            "speed_knots": env["wind_speed_knots"],
            "direction_deg": env["wind_direction_deg"],
            "gust_knots": environment_or_input("wind_gust_knots"),
            "recent_max_12h": environment_or_input("recent_wind_max_12h"),
            "onshore_knots": inputs_used.get("wind_onshore_knots"),
            "offshore_knots": inputs_used.get("wind_offshore_knots"),
            "alongshore_knots": inputs_used.get("wind_alongshore_knots"),
        },
        "swell": {
            "height_m": env["swell_height_m"],
            "direction_deg": env["swell_direction_deg"],
            "wave_height_m": environment_or_input("wave_height_m"),
            "wave_height_delta_24h": environment_or_input("wave_height_delta_24h"),
            "source": environment_or_input("wave_data_source"),
        },
        "pressure_hpa": env["pressure_hpa"],
        "pressure_delta_3h": environment_or_input("pressure_delta_3h"),
        "weather_trend": {
            "pressure_delta_6h": environment_or_input("pressure_delta_6h"),
            "pressure_delta_24h": environment_or_input("pressure_delta_24h"),
            "pressure_delta_48h": environment_or_input("pressure_delta_48h"),
            "pressure_delta_72h": environment_or_input("pressure_delta_72h"),
            "temperature_delta_24h": environment_or_input("temperature_delta_24h"),
            "temperature_delta_48h": environment_or_input("temperature_delta_48h"),
            "temperature_delta_72h": environment_or_input("temperature_delta_72h"),
            "temperature_drop_from_recent_72h_peak": environment_or_input("temperature_drop_from_recent_72h_peak"),
            "wind_direction_change_12h": environment_or_input("wind_direction_change_12h"),
            "max_gust_24h": environment_or_input("max_gust_24h"),
            "max_gust_72h": environment_or_input("max_gust_72h"),
            "rainfall_24h": environment_or_input("rainfall_24h"),
            "rainfall_48h": environment_or_input("rainfall_48h"),
            "rainfall_72h": environment_or_input("rainfall_72h"),
            "change_notes": _weather_change_notes(inputs_used),
        },
        "air": {
            "temperature_c": environment_or_input("temperature_c"),
            "rain_mm": environment_or_input("rain_mm"),
            "precipitation_mm": environment_or_input("precipitation_mm"),
            "recent_precipitation_sum_12h": environment_or_input("recent_precipitation_sum_12h"),
            "cloud_cover_pct": environment_or_input("cloud_cover_pct"),
        },
        "marine": {
            "sea_surface_temperature_c": environment_or_input("sea_surface_temperature_c"),
            "sea_surface_temperature_delta_24h": environment_or_input("sea_surface_temperature_delta_24h"),
            "sea_surface_temperature_delta_72h": environment_or_input("sea_surface_temperature_delta_72h"),
            "water_temperature_signal": environment_or_input("water_temperature_signal"),
            "water_temperature_trend": environment_or_input("water_temperature_trend"),
            "temperature_confidence": environment_or_input("temperature_confidence"),
        },
        "tide": {
            "phase": env["tide_phase"],
            "source": window["tide_source"],
            "stage": environment_or_input("tide_stage"),
            "range_m": environment_or_input("tide_range_m"),
            "height_m": environment_or_input("tide_height_m"),
            "movement_rate_m_per_hour": environment_or_input("tide_movement_rate_m_per_hour"),
            "current_confidence": environment_or_input("tide_current_confidence"),
            "current_strength_proxy": environment_or_input("current_strength_proxy"),
            "current_source_note": environment_or_input("current_source_note"),
            "hours_to_high_tide": environment_or_input("hours_to_high_tide"),
            "hours_to_low_tide": environment_or_input("hours_to_low_tide"),
            "hours_since_low_tide": environment_or_input("hours_since_low_tide"),
        },
        "solar": {
            "hour_of_day": environment_or_input("hour_of_day"),
            "hours_from_sunrise": environment_or_input("hours_from_sunrise"),
            "hours_from_sunset": environment_or_input("hours_from_sunset"),
            "hours_from_solar_noon": environment_or_input("hours_from_solar_noon"),
            "is_daylight": environment_or_input("is_daylight"),
        },
        "moon": {
            "phase_name": environment_or_input("moon_phase_name"),
            "illumination_pct": environment_or_input("moon_illumination_pct"),
        },
        "formula": {
            "normalized": normalized,
            "raw_time_signal": model_environment.get("raw_time_signal"),
            "rules": generic_rules.get("rules", []),
            "score_delta": generic_rules.get("score_delta"),
            "family": generic_rules.get("family"),
        },
        "classification": window.get("preview", {}).get("meta", {}).get("waterbody_classification"),
        "fish_profile": environment_or_input("fish_profile"),
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
    meta = preview.get("meta") or {}
    classification = meta.get("waterbody_classification") or {}
    inputs_used = (meta.get("environment") or {}).get("inputs_used", {})
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
        "fish_outlook_score": overall.get("fish_outlook_score"),
        "comfort_score": overall.get("comfort_score"),
        "comfort_factors": overall.get("comfort_factors", []),
        "safety_flag": overall.get("safety_flag"),
        "safety_factors": overall.get("safety_factors", []),
        "label": overall.get("label"),
        "model_rule_family": overall.get("model_rule_family"),
        "score_breakdown": overall.get("score_breakdown"),
        "reason_tags": overall.get("reason_tags", []),
        "positive_reason_tags": positive_tags,
        "negative_reason_tags": negative_tags,
        "dominant_water_type": overall.get("dominant_inferred_type"),
        "waterbody_class": classification.get("waterbody_class"),
        "classification_confidence": classification.get("classification_confidence"),
        "classification_reasons": classification.get("classification_reasons", []),
        "manual_region_override": classification.get("manual_region_override"),
        "fish_profile": inputs_used.get("fish_profile"),
        "water_type_scores": water_scores,
        "expanded_water_types": _expanded_water_types(window),
        "conditions": _condition_strip(window),
    }


def _fish_signal_from_mapping(value: Mapping[str, Any]) -> float | None:
    fish = _number(value.get("fish_outlook_score"))
    if fish is not None:
        return fish
    activity = _number(value.get("activity_score"))
    presence = _number(value.get("presence_score"))
    if activity is not None and presence is not None:
        return (activity * 0.55) + (presence * 0.45)
    return _number(value.get("score"))


def _average_float(values: list[float]) -> float | None:
    return None if not values else sum(values) / len(values)


def _daily_fish_signal(
    day: str,
    day_windows: list[Mapping[str, Any]],
    hourly_activity: list[Mapping[str, Any]],
) -> dict[str, Any]:
    hourly_values = [
        value
        for value in (_fish_signal_from_mapping(point) for point in hourly_activity if point.get("date") == day)
        if value is not None
    ]
    window_values = [
        value
        for value in (_fish_signal_from_mapping((window["preview"].get("overall_recommendation") or {})) for window in day_windows)
        if value is not None
    ]
    signal_values = hourly_values or window_values
    if not signal_values:
        return {
            "day_score": None,
            "fish_day_score": None,
            "best_window_score": None,
            "average_window_score": None,
            "hourly_peak_score": None,
            "hourly_mean_score": None,
            "daily_score_note": "No supported fish-signal data for this date.",
        }

    ordered = sorted(signal_values, reverse=True)
    peak = ordered[0]
    top_count = min(4, len(ordered))
    top_average = sum(ordered[:top_count]) / top_count
    mean = sum(signal_values) / len(signal_values)
    score = (peak * 0.48) + (top_average * 0.32) + (mean * 0.20)

    strong_hours = sum(1 for value in signal_values if value >= 60)
    usable_hours = sum(1 for value in signal_values if value >= 50)
    if peak < 50:
        score = min(score, 42)
    elif peak < 58 and mean < 42:
        score = min(score, 45)
    elif peak < 62 and mean < 40:
        score = min(score, 48)
    elif peak < 58 and strong_hours == 0:
        score = min(score, 50)
    elif strong_hours <= 1 and mean < 45:
        score = min(score, 50)
    elif usable_hours <= 3 and mean < 48:
        score = min(score, 58)

    notes: list[str] = []
    if strong_hours <= 1:
        notes.append("Only one short window clears a strong fish signal.")
    if mean < 45:
        notes.append("Most of the day remains weak even if one window improves.")
    if peak < 50:
        notes.append("No convincing bite window appears in the hourly curve.")
    if not notes:
        notes.append("Daily score blends peak window strength with whole-day support.")

    return {
        "day_score": round(max(0, min(100, score))),
        "fish_day_score": round(max(0, min(100, score))),
        "best_window_score": round(max(window_values) if window_values else peak),
        "average_window_score": None if not window_values else round(_average_float(window_values) or 0),
        "hourly_peak_score": None if not hourly_values else round(max(hourly_values)),
        "hourly_mean_score": None if not hourly_values else round(_average_float(hourly_values) or 0),
        "daily_score_note": " ".join(notes),
    }


def _daily_cards(
    windows: list[Mapping[str, Any]],
    hourly_activity: list[Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    by_date: dict[str, list[Mapping[str, Any]]] = {}
    for window in windows:
        by_date.setdefault(window["date"], []).append(window)

    cards = []
    hourly = list(hourly_activity or [])
    for day, day_windows in sorted(by_date.items()):
        best = _best_window(list(day_windows))
        daily_signal = _daily_fish_signal(day, list(day_windows), hourly)
        cards.append(
            {
                "date": day,
                **daily_signal,
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
    meta = best["preview"].get("meta") or {}
    classification = meta.get("waterbody_classification") or {}
    inputs_used = (meta.get("environment") or {}).get("inputs_used", {})
    dominant = WATER_TYPE_LABELS.get(overall["dominant_inferred_type"], overall["dominant_inferred_type"])
    return {
        "score": overall["score"],
        "label": overall["label"],
        "fish_outlook_score": overall.get("fish_outlook_score"),
        "comfort_score": overall.get("comfort_score"),
        "trip_quality_score": overall.get("trip_quality_score"),
        "safety_flag": overall.get("safety_flag"),
        "safety_factors": overall.get("safety_factors", []),
        "comfort_factors": overall.get("comfort_factors", []),
        "waterbody_class": classification.get("waterbody_class"),
        "classification_confidence": classification.get("classification_confidence"),
        "fish_profile": inputs_used.get("fish_profile"),
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
    swell_height = _number(conditions["swell"].get("height_m"))
    if swell_height is not None and swell_height >= 1.8:
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
    attributes = item.get("attributes")
    if isinstance(attributes, Mapping):
        compact["attributes"] = {
            key: value
            for key, value in attributes.items()
            if key in {"jurisdiction", "guide_name", "source_kind", "official_owner", "official_url", "score_impact", "review_status"}
            and value is not None
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


def _primary_classification(range_forecast: Mapping[str, Any]) -> dict[str, Any] | None:
    best = _best_window(list(range_forecast["windows"]))
    if best is None:
        return None
    preview = best.get("preview") or {}
    meta = preview.get("meta") or {}
    classification = dict(meta.get("waterbody_classification") or {})
    inputs_used = (meta.get("environment") or {}).get("inputs_used", {})
    if inputs_used.get("fish_profile") is not None:
        classification["fish_profile"] = inputs_used.get("fish_profile")
    return classification or None


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
            "waterbody_class": card.get("waterbody_class"),
            "fish_profile": card.get("fish_profile"),
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
    if str(inputs_used.get("tide_current_confidence") or "low") == "low" and str(inputs_used.get("waterbody_class") or "") in {
        "river_mouth",
        "tidal_river",
    }:
        return 0, None
    if str(inputs_used.get("water_temperature_signal") or "") == "cold":
        return 0, None

    movement_aligned = bool(tags & COMBO_MOVEMENT_TAGS)
    timing_aligned = bool(tags & COMBO_TIMING_TAGS)
    weather_clean_axis = bool(tags & COMBO_WEATHER_CLEAN_TAGS)
    aligned = sum((movement_aligned, timing_aligned, weather_clean_axis))
    if aligned < 3:
        return 0, None

    dominant_type = overall.get("dominant_inferred_type")
    if dominant_type in COMBO_OPEN_COAST_TYPES:
        wave = float(inputs_used.get("wave_height_m") or inputs_used.get("swell_height_m") or 0.0)
        wind_kts = float(inputs_used.get("wind_speed_knots") or 0.0)
        if wave > COMBO_OPEN_COAST_MAX_WAVE_M or wind_kts > COMBO_OPEN_COAST_MAX_WIND_KNOTS:
            return 0, None

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
        "classification": _primary_classification(range_forecast),
        "hero": _hero(range_forecast),
        "explanation": _explanation(range_forecast, explanation_provider=explanation_provider),
        "summary": range_forecast["summary"],
        "daily_forecast": _daily_cards(
            list(range_forecast["windows"]),
            hourly_activity=list(range_forecast.get("hourly_activity", [])),
        ),
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
            "confidence": True,
            "explanation": True,
            "social_pulse": bool(social_pulse.get("available")),
        },
    }
    response["plan"] = build_fishing_plan(response, planner_provider=planner_provider)
    return response
