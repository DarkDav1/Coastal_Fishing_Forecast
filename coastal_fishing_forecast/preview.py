"""Coordinate preview path for generic coastal search results."""

from __future__ import annotations

from dataclasses import dataclass, replace
import math
from typing import Any, Mapping

from global_land_mask import globe
from coastal_fishing_forecast.regions import RegionConfig, get_region_config

EARTH_RADIUS_KM = 6371.0
DIRECT_NEARBY_WATER_KM = 5.0
EXTENDED_TIDAL_PREVIEW_KM = 8.0
SEARCH_DISTANCES_KM = (0.5, 1.5, 3.0, 5.0, 8.0, 12.0, 20.0)
ANALYSIS_RINGS_KM = (3.0, 8.0, 15.0)
BEARINGS = tuple(range(0, 360, 30))
CONTRACT_VERSION = "2026-04-23.preview.v1"
PREVIEW_MODE = "search_preview"
SUPPORTED_REASON_CODE = "coastal_or_tidal_preview"
EXTENDED_SUPPORTED_REASON_CODE = "tidal_corridor_preview"
UNSUPPORTED_REASON_CODE = "inland_or_non_tidal"
DISTANCE_UNSUPPORTED_REASON_CODE = "too_far_from_supported_water"
INVALID_REASON_CODE = "invalid_coordinate"
PREVIEW_CONFIDENCE = "low"
HIGH_CONFIDENCE = "high"
WATER_TYPE_KEYS = ("beach", "rocks", "jetty", "bay_estuary_edge")
WATERBODY_CLASSES = (
    "open_coast",
    "surf_coast",
    "bay_coast",
    "sheltered_estuary",
    "river_mouth",
    "tidal_river",
    "harbour_access",
    "unsupported",
)
SUPPORT_MODE_ON_WATER = "on_water"
SUPPORT_MODE_NEAR_WATER = "near_water"
SUPPORT_MODE_TIDAL_CORRIDOR = "tidal_corridor"
SUPPORT_MODE_UNSUPPORTED = "unsupported"
SUPPORT_MODE_INVALID = "invalid_input"


@dataclass(frozen=True)
class RingSample:
    distance_km: float
    water_fraction: float
    transition_ratio: float


@dataclass(frozen=True)
class GlobalSignals:
    inner_water_fraction: float
    mid_water_fraction: float
    outer_water_fraction: float
    coastline_complexity: float
    open_water_bearing_deg: float | None
    coastal_edge_signal: float
    exposure: float
    shelter: float
    accessibility: float
    search_confidence_score: float


@dataclass(frozen=True)
class TypeSignals:
    beach: float
    rocks: float
    jetty: float
    bay_estuary_edge: float


@dataclass(frozen=True)
class WaterbodyClassification:
    waterbody_class: str
    confidence: float
    reasons: tuple[str, ...]
    recommended_region: str
    manual_region_override: str | None = None


@dataclass(frozen=True)
class EnvironmentInputs:
    temperature_c: float | None = None
    wind_speed_knots: float = 12.0
    wind_direction_deg: float | None = None
    wind_gust_knots: float | None = None
    recent_wind_max_12h: float | None = None
    swell_height_m: float | None = None
    swell_direction_deg: float | None = None
    wave_height_m: float | None = None
    wave_height_delta_24h: float | None = None
    wave_data_source: str | None = None
    sea_surface_temperature_c: float | None = None
    sea_surface_temperature_delta_24h: float | None = None
    sea_surface_temperature_delta_72h: float | None = None
    pressure_hpa: float = 1015.0
    pressure_delta_3h: float | None = None
    pressure_delta_6h: float | None = None
    pressure_delta_24h: float | None = None
    pressure_delta_48h: float | None = None
    pressure_delta_72h: float | None = None
    temperature_delta_24h: float | None = None
    temperature_delta_48h: float | None = None
    temperature_delta_72h: float | None = None
    temperature_drop_from_recent_72h_peak: float | None = None
    wind_direction_change_12h: float | None = None
    max_gust_24h: float | None = None
    max_gust_72h: float | None = None
    precipitation_mm: float = 0.0
    rain_mm: float = 0.0
    recent_precipitation_sum_12h: float | None = None
    rainfall_24h: float | None = None
    rainfall_48h: float | None = None
    rainfall_72h: float | None = None
    cloud_cover_pct: float | None = None
    tide_phase: str = "mid"
    tide_stage: str = "unknown"
    hours_to_high_tide: float | None = None
    hours_to_low_tide: float | None = None
    hours_since_low_tide: float | None = None
    hours_since_high_tide: float | None = None
    tide_range_m: float | None = None
    tide_height_m: float | None = None
    tide_height_change_next_2h: float | None = None
    tide_height_change_next_3h: float | None = None
    tide_height_change_prev_2h: float | None = None
    tide_movement_rate_m_per_hour: float | None = None
    tide_source: str | None = None
    tide_current_confidence: str = "low"
    current_strength_proxy: float | None = None
    current_source_note: str | None = None
    time_window: str = "day"
    hour_of_day: float | None = None
    hours_from_sunrise: float | None = None
    hours_from_sunset: float | None = None
    hours_from_solar_noon: float | None = None
    is_daylight: bool | None = None
    moon_phase_fraction: float | None = None
    moon_phase_name: str | None = None
    moon_illumination_pct: float | None = None
    waterbody_class: str = "generic_coastal"
    fish_profile: str = "generic_estuary"
    water_temperature_signal: str = "unknown"
    water_temperature_trend: str = "unknown"
    temperature_confidence: str = "low"
    rule_family: str = "generic_coastal_v1"


def _clamp(value: float, lower: float = 0.0, upper: float = 100.0) -> int:
    return round(max(lower, min(upper, value)))


def _normalize(value: float, lower: float, upper: float) -> float:
    if upper <= lower:
        return 0.0
    return max(0.0, min(1.0, (value - lower) / (upper - lower)))


def _offset_coordinate(lat: float, lon: float, bearing_deg: float, distance_km: float) -> tuple[float, float]:
    lat1 = math.radians(lat)
    lon1 = math.radians(lon)
    bearing = math.radians(bearing_deg)
    angular_distance = distance_km / EARTH_RADIUS_KM

    lat2 = math.asin(
        math.sin(lat1) * math.cos(angular_distance)
        + math.cos(lat1) * math.sin(angular_distance) * math.cos(bearing)
    )
    lon2 = lon1 + math.atan2(
        math.sin(bearing) * math.sin(angular_distance) * math.cos(lat1),
        math.cos(angular_distance) - math.sin(lat1) * math.sin(lat2),
    )

    lon_deg = (math.degrees(lon2) + 540.0) % 360.0 - 180.0
    return math.degrees(lat2), lon_deg


def _is_water(lat: float, lon: float) -> bool:
    return bool(globe.is_ocean(lat, lon))


def _sample_ring(lat: float, lon: float, distance_km: float) -> RingSample:
    samples = []
    for bearing in BEARINGS:
        sample_lat, sample_lon = _offset_coordinate(lat, lon, bearing, distance_km)
        samples.append(_is_water(sample_lat, sample_lon))

    water_fraction = sum(samples) / len(samples)
    transitions = sum(
        1 for idx, value in enumerate(samples) if value != samples[(idx + 1) % len(samples)]
    )
    return RingSample(
        distance_km=distance_km,
        water_fraction=water_fraction,
        transition_ratio=transitions / len(samples),
    )


def _wrap_degrees(value: float) -> float:
    return value % 360.0


def _normalize_direction(value: Any) -> float | None:
    if value is None:
        return None
    return _wrap_degrees(float(value))


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes"}:
            return True
        if normalized in {"false", "0", "no"}:
            return False
    return None


def _angular_distance_deg(first: float, second: float) -> float:
    difference = abs(first - second) % 360.0
    return min(difference, 360.0 - difference)


def _angular_distance_signed(first: float, second: float) -> float:
    return ((first - second + 180.0) % 360.0) - 180.0


def _mean_water_bearing(lat: float, lon: float, distance_km: float) -> float | None:
    x_total = 0.0
    y_total = 0.0
    for bearing in BEARINGS:
        sample_lat, sample_lon = _offset_coordinate(lat, lon, bearing, distance_km)
        if _is_water(sample_lat, sample_lon):
            radians = math.radians(bearing)
            x_total += math.cos(radians)
            y_total += math.sin(radians)

    if abs(x_total) < 1e-6 and abs(y_total) < 1e-6:
        return None
    return _wrap_degrees(math.degrees(math.atan2(y_total, x_total)))


def _estimate_open_water_bearing(lat: float, lon: float) -> float | None:
    weighted_vectors: list[tuple[float, float]] = []
    for weight, distance_km in ((0.8, ANALYSIS_RINGS_KM[0]), (1.0, ANALYSIS_RINGS_KM[1]), (1.2, ANALYSIS_RINGS_KM[2])):
        bearing = _mean_water_bearing(lat, lon, distance_km)
        if bearing is None:
            continue
        radians = math.radians(bearing)
        weighted_vectors.append((weight * math.cos(radians), weight * math.sin(radians)))

    if not weighted_vectors:
        return None

    x_total = sum(vector[0] for vector in weighted_vectors)
    y_total = sum(vector[1] for vector in weighted_vectors)
    if abs(x_total) < 1e-6 and abs(y_total) < 1e-6:
        return None
    return _wrap_degrees(math.degrees(math.atan2(y_total, x_total)))


def _find_nearest_water_km(lat: float, lon: float) -> float | None:
    if _is_water(lat, lon):
        return 0.0

    for distance_km in SEARCH_DISTANCES_KM:
        for bearing in BEARINGS:
            sample_lat, sample_lon = _offset_coordinate(lat, lon, bearing, distance_km)
            if _is_water(sample_lat, sample_lon):
                return distance_km
    return None


def _compute_global_signals(lat: float, lon: float, nearest_water_km: float, on_water: bool) -> GlobalSignals:
    rings = [_sample_ring(lat, lon, distance_km) for distance_km in ANALYSIS_RINGS_KM]
    inner_water = rings[0].water_fraction
    mid_water = rings[1].water_fraction
    outer_water = rings[2].water_fraction
    complexity = sum(ring.transition_ratio for ring in rings) / len(rings)
    open_water_bearing_deg = _estimate_open_water_bearing(lat, lon)
    coastal_edge_signal = max(0.0, 1.0 - abs(mid_water - 0.5) * 2.0)
    exposure = outer_water
    shelter = max(0.0, 1.0 - exposure)
    accessibility = 1.0 - _normalize(nearest_water_km, 0.0, DIRECT_NEARBY_WATER_KM)
    search_confidence = 0.35 + (0.15 * accessibility) + (0.10 if on_water else 0.0)
    return GlobalSignals(
        inner_water_fraction=inner_water,
        mid_water_fraction=mid_water,
        outer_water_fraction=outer_water,
        coastline_complexity=complexity,
        open_water_bearing_deg=open_water_bearing_deg,
        coastal_edge_signal=coastal_edge_signal,
        exposure=exposure,
        shelter=shelter,
        accessibility=accessibility,
        search_confidence_score=search_confidence,
    )


def _classify_waterbody(
    signals: GlobalSignals,
    *,
    nearest_water_km: float,
    on_water: bool,
    manual_region: str | None,
) -> WaterbodyClassification:
    """Classify the broad waterbody before applying fish/tide rules.

    This is intentionally conservative: broad land-mask geometry can separate
    exposed coast from sheltered/river-like water, but it cannot prove a named
    habitat feature or fishing structure.
    """
    inner = signals.inner_water_fraction
    mid = signals.mid_water_fraction
    outer = signals.outer_water_fraction
    complexity = signals.coastline_complexity
    exposure = signals.exposure
    shelter = signals.shelter
    access = signals.accessibility
    reasons: list[str] = []

    if nearest_water_km > EXTENDED_TIDAL_PREVIEW_KM:
        return WaterbodyClassification(
            waterbody_class="unsupported",
            confidence=0.9,
            reasons=("searched point is too far from supported coastal or tidal water",),
            recommended_region="generic_coastal",
            manual_region_override=manual_region,
        )

    if not on_water and nearest_water_km > DIRECT_NEARBY_WATER_KM and shelter >= 0.55 and complexity >= 0.35:
        reasons.append("nearby water is sheltered and narrow enough for tidal-corridor support")
        waterbody_class = "tidal_river"
    elif shelter >= 0.82 and outer <= 0.18 and mid <= 0.26:
        reasons.append("very sheltered narrow water indicates a tidal river or upper estuary")
        waterbody_class = "tidal_river" if inner <= 0.24 else "river_mouth"
    elif shelter >= 0.72 and complexity >= 0.42 and outer <= 0.34:
        reasons.append("high shelter and complex coastline indicate a river-mouth or tidal-river setting")
        waterbody_class = "tidal_river" if inner <= 0.42 else "river_mouth"
    elif shelter >= 0.62 and complexity >= 0.34:
        reasons.append("sheltered water with coastline complexity indicates an estuary or protected bay edge")
        waterbody_class = "sheltered_estuary"
    elif shelter >= 0.48 and outer <= 0.58:
        reasons.append("moderate shelter and limited outer water indicate bay-coast conditions")
        waterbody_class = "bay_coast"
    elif exposure >= 0.72 and complexity <= 0.30:
        reasons.append("high exposure and simple shoreline indicate surf or open coast")
        waterbody_class = "surf_coast"
    elif exposure >= 0.58:
        reasons.append("broad outer-water exposure indicates open coast")
        waterbody_class = "open_coast"
    elif complexity >= 0.46 and access >= 0.45:
        reasons.append("complex accessible edge indicates harbour-like access water")
        waterbody_class = "harbour_access"
    else:
        reasons.append("mixed coastline geometry falls back to generic bay/coastal scoring")
        waterbody_class = "bay_coast"

    if manual_region:
        reasons.append(f"manual region override requested: {manual_region}")

    confidence = 0.42
    confidence += 0.16 if on_water else 0.06 if nearest_water_km <= DIRECT_NEARBY_WATER_KM else 0.0
    confidence += min(0.18, abs(exposure - shelter) * 0.20)
    confidence += min(0.14, complexity * 0.14)
    if waterbody_class in {"river_mouth", "tidal_river"}:
        confidence -= 0.08  # geometry-only river/estuary distinction is inherently softer.

    return WaterbodyClassification(
        waterbody_class=waterbody_class,
        confidence=round(_clamp_unit(confidence), 2),
        reasons=tuple(reasons),
        recommended_region=waterbody_class if waterbody_class in WATERBODY_CLASSES else "generic_coastal",
        manual_region_override=manual_region,
    )


def _default_fish_profile(waterbody_class: str) -> str:
    if waterbody_class in {"river_mouth", "tidal_river", "sheltered_estuary", "harbour_access"}:
        return "generic_estuary"
    if waterbody_class in {"open_coast", "surf_coast"}:
        return "salmon_pelagic"
    if waterbody_class == "bay_coast":
        return "flathead"
    return "generic_estuary"


def _infer_type_signals(signals: GlobalSignals) -> TypeSignals:
    return TypeSignals(
        beach=max(
            0.0,
            0.50 * signals.exposure + 0.30 * signals.coastal_edge_signal + 0.20 * signals.accessibility,
        ),
        rocks=max(
            0.0,
            0.40 * signals.exposure + 0.35 * signals.coastline_complexity + 0.25 * signals.accessibility,
        ),
        jetty=max(
            0.0,
            0.35 * signals.coastal_edge_signal
            + 0.30 * signals.coastline_complexity
            + 0.20 * signals.shelter
            + 0.15 * signals.accessibility,
        ),
        bay_estuary_edge=max(
            0.0,
            0.45 * signals.shelter
            + 0.35 * signals.coastline_complexity
            + 0.20 * signals.accessibility,
        ),
    )


def _apply_region_bias(type_signals: TypeSignals, region_config: RegionConfig) -> TypeSignals:
    return TypeSignals(
        beach=_clamp_unit(type_signals.beach * region_config.beach_bias),
        rocks=_clamp_unit(type_signals.rocks * region_config.rocks_bias),
        jetty=_clamp_unit(type_signals.jetty * region_config.jetty_bias),
        bay_estuary_edge=_clamp_unit(type_signals.bay_estuary_edge * region_config.bay_estuary_bias),
    )


def _build_water_type_card(
    *,
    name: str,
    resident: float,
    roaming: float,
    trip: float,
    inference_strength: float,
    reasons: list[str],
) -> dict:
    resident = _calibrate_public_preview_score(resident)
    roaming = _calibrate_public_preview_score(roaming)
    trip = _calibrate_public_preview_score(trip)
    overall = (0.35 * resident) + (0.35 * roaming) + (0.30 * trip)
    return {
        "available": inference_strength >= 0.2,
        "confidence": PREVIEW_CONFIDENCE,
        "inference_strength": round(inference_strength, 2),
        "scores": {
            "resident_opportunity": _clamp(resident),
            "roaming_opportunity": _clamp(roaming),
            "trip_quality": _clamp(trip),
            "overall_recommendation": _clamp(overall),
        },
        "reason_summary": reasons,
        "notes": [
            f"{name} is inferred from broad coastline shape only.",
            "This preview is less certain than a curated local spot.",
        ],
    }


def _clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, value))


def _normalize_environment(environment: Mapping[str, Any] | None) -> EnvironmentInputs:
    if environment is None:
        return EnvironmentInputs()

    tide_phase = str(environment.get("tide_phase", "mid")).strip().lower() or "mid"
    if tide_phase not in {"low", "rising", "high", "falling", "mid"}:
        tide_phase = "mid"

    time_window = str(environment.get("time_window", "day")).strip().lower() or "day"
    if time_window not in {"pre_dawn", "dawn", "day", "dusk", "night"}:
        time_window = "day"

    return EnvironmentInputs(
        wind_speed_knots=float(environment.get("wind_speed_knots", 12.0)),
        wind_direction_deg=_normalize_direction(environment.get("wind_direction_deg")),
        temperature_c=_optional_float(environment.get("temperature_c")),
        wind_gust_knots=_optional_float(environment.get("wind_gust_knots")),
        recent_wind_max_12h=_optional_float(environment.get("recent_wind_max_12h")),
        swell_height_m=_optional_float(environment.get("swell_height_m")),
        swell_direction_deg=_normalize_direction(environment.get("swell_direction_deg")),
        wave_height_m=_optional_float(environment.get("wave_height_m")),
        wave_height_delta_24h=_optional_float(environment.get("wave_height_delta_24h")),
        wave_data_source=str(environment.get("wave_data_source") or "provided"),
        sea_surface_temperature_c=_optional_float(environment.get("sea_surface_temperature_c")),
        sea_surface_temperature_delta_24h=_optional_float(environment.get("sea_surface_temperature_delta_24h")),
        sea_surface_temperature_delta_72h=_optional_float(environment.get("sea_surface_temperature_delta_72h")),
        pressure_hpa=float(environment.get("pressure_hpa", 1015.0)),
        pressure_delta_3h=_optional_float(environment.get("pressure_delta_3h")),
        pressure_delta_6h=_optional_float(environment.get("pressure_delta_6h")),
        pressure_delta_24h=_optional_float(environment.get("pressure_delta_24h")),
        pressure_delta_48h=_optional_float(environment.get("pressure_delta_48h")),
        pressure_delta_72h=_optional_float(environment.get("pressure_delta_72h")),
        temperature_delta_24h=_optional_float(environment.get("temperature_delta_24h")),
        temperature_delta_48h=_optional_float(environment.get("temperature_delta_48h")),
        temperature_delta_72h=_optional_float(environment.get("temperature_delta_72h")),
        temperature_drop_from_recent_72h_peak=_optional_float(environment.get("temperature_drop_from_recent_72h_peak")),
        wind_direction_change_12h=_optional_float(environment.get("wind_direction_change_12h")),
        max_gust_24h=_optional_float(environment.get("max_gust_24h")),
        max_gust_72h=_optional_float(environment.get("max_gust_72h")),
        precipitation_mm=float(environment.get("precipitation_mm", 0.0) or 0.0),
        rain_mm=float(environment.get("rain_mm", 0.0) or 0.0),
        recent_precipitation_sum_12h=_optional_float(environment.get("recent_precipitation_sum_12h")),
        rainfall_24h=_optional_float(environment.get("rainfall_24h")),
        rainfall_48h=_optional_float(environment.get("rainfall_48h")),
        rainfall_72h=_optional_float(environment.get("rainfall_72h")),
        cloud_cover_pct=_optional_float(environment.get("cloud_cover_pct")),
        tide_phase=tide_phase,
        tide_stage=str(environment.get("tide_stage", "unknown")).strip().lower() or "unknown",
        hours_to_high_tide=_optional_float(environment.get("hours_to_high_tide")),
        hours_to_low_tide=_optional_float(environment.get("hours_to_low_tide")),
        hours_since_low_tide=_optional_float(environment.get("hours_since_low_tide")),
        hours_since_high_tide=_optional_float(environment.get("hours_since_high_tide")),
        tide_range_m=_optional_float(environment.get("tide_range_m")),
        tide_height_m=_optional_float(environment.get("tide_height_m")),
        tide_height_change_next_2h=_optional_float(environment.get("tide_height_change_next_2h")),
        tide_height_change_next_3h=_optional_float(environment.get("tide_height_change_next_3h")),
        tide_height_change_prev_2h=_optional_float(environment.get("tide_height_change_prev_2h")),
        tide_movement_rate_m_per_hour=_optional_float(environment.get("tide_movement_rate_m_per_hour")),
        tide_source=str(environment.get("tide_source") or "") or None,
        tide_current_confidence=str(environment.get("tide_current_confidence") or "low"),
        current_strength_proxy=_optional_float(environment.get("current_strength_proxy")),
        current_source_note=str(environment.get("current_source_note") or "") or None,
        time_window=time_window,
        hour_of_day=_optional_float(environment.get("hour_of_day")),
        hours_from_sunrise=_optional_float(environment.get("hours_from_sunrise")),
        hours_from_sunset=_optional_float(environment.get("hours_from_sunset")),
        hours_from_solar_noon=_optional_float(environment.get("hours_from_solar_noon")),
        is_daylight=_as_bool(environment.get("is_daylight")),
        moon_phase_fraction=_optional_float(environment.get("moon_phase_fraction")),
        moon_phase_name=str(environment.get("moon_phase_name") or "") or None,
        moon_illumination_pct=_optional_float(environment.get("moon_illumination_pct")),
        waterbody_class=str(environment.get("waterbody_class") or "generic_coastal"),
        fish_profile=str(environment.get("fish_profile") or "generic_estuary"),
        water_temperature_signal=str(environment.get("water_temperature_signal") or "unknown"),
        water_temperature_trend=str(environment.get("water_temperature_trend") or "unknown"),
        temperature_confidence=str(environment.get("temperature_confidence") or "low"),
        rule_family=str(environment.get("rule_family", "generic_coastal_v1")),
    )


def _current_strength_proxy(environment: EnvironmentInputs) -> float | None:
    candidates = [
        environment.current_strength_proxy,
        None if environment.tide_height_change_next_2h is None else environment.tide_height_change_next_2h / 0.28,
        None if environment.tide_height_change_next_3h is None else environment.tide_height_change_next_3h / 0.38,
        None if environment.tide_movement_rate_m_per_hour is None else environment.tide_movement_rate_m_per_hour / 0.14,
    ]
    values = [float(value) for value in candidates if value is not None]
    if not values:
        return None
    return round(_clamp_unit(max(values)), 2)


def _tide_current_context(environment: EnvironmentInputs, waterbody_class: str) -> dict[str, Any]:
    tide_source = (environment.tide_source or "").lower()
    if tide_source == "tidesatlas":
        confidence = "medium"
        note = "Tide events are API-backed; current strength is still inferred from local tide-height movement."
    elif tide_source in {"tide_events", "tide_events_file"}:
        confidence = "medium"
        note = "Tide events are supplied; current strength is inferred from tide-height movement."
    elif tide_source == "openmeteo_model":
        confidence = "low"
        note = "Open-Meteo sea-level is a tide proxy, not measured local current."
    else:
        confidence = "low"
        note = "Current strength is estimated from broad tide timing only."

    proxy = _current_strength_proxy(environment)
    if proxy is None:
        proxy = {
            "low": 0.18,
            "rising": 0.58,
            "falling": 0.50,
            "high": 0.18,
            "mid": 0.34,
        }.get(environment.tide_phase, 0.30)
        if environment.tide_stage == "slack":
            proxy = min(proxy, 0.18)

    if waterbody_class in {"river_mouth", "tidal_river"} and confidence == "low":
        note = f"{note} River/estuary current timing can lag tide height, so high scores are capped."

    return {
        "tide_current_confidence": confidence,
        "current_strength_proxy": round(_clamp_unit(proxy), 2),
        "current_source_note": note,
    }


def _water_temperature_context(environment: EnvironmentInputs, fish_profile: str) -> dict[str, Any]:
    temp = environment.sea_surface_temperature_c
    delta_24h = environment.sea_surface_temperature_delta_24h
    delta_72h = environment.sea_surface_temperature_delta_72h
    if temp is None:
        return {
            "signal": "unknown",
            "trend": "unknown",
            "confidence": "low",
            "score_delta": 0,
            "rules": [{"id": "water_temp_missing", "label": "Water temperature unavailable", "score_delta": 0}],
        }

    profile_ranges = {
        "flathead": (15.0, 23.0),
        "bream_estuary": (13.0, 22.0),
        "salmon_pelagic": (11.0, 18.5),
        "mulloway": (16.0, 23.5),
        "rocks_reef": (12.0, 19.0),
        "generic_estuary": (13.0, 21.0),
    }
    low, high = profile_ranges.get(fish_profile, profile_ranges["generic_estuary"])
    rules: list[dict[str, Any]] = []
    score_delta = 0
    if temp < low - 3.0:
        signal = "cold"
        score_delta -= 7
        _add_rule(rules, "water_temp_cold", -7, "Cold water for target profile")
    elif temp < low:
        signal = "cool"
        score_delta -= 3
        _add_rule(rules, "water_temp_cool", -3, "Cool water for target profile")
    elif low <= temp <= high:
        signal = "optimal"
        score_delta += 4
        _add_rule(rules, "water_temp_optimal", 4, "Productive water temperature")
    elif temp <= high + 3.0:
        signal = "warm"
        score_delta -= 1
        _add_rule(rules, "water_temp_warm", -1, "Warm water for target profile")
    else:
        signal = "hot"
        score_delta -= 5
        _add_rule(rules, "water_temp_hot", -5, "Very warm water for target profile")

    trend = "stable"
    if delta_24h is not None and delta_24h <= -1.2:
        trend = "cooling_fast"
        score_delta -= 4
        _add_rule(rules, "water_temp_cooling_fast", -4, "Water temperature has fallen quickly")
    elif delta_24h is not None and delta_24h >= 1.5:
        trend = "warming_fast"
        score_delta -= 2
        _add_rule(rules, "water_temp_warming_fast", -2, "Water temperature has risen quickly")
    elif delta_72h is not None and abs(delta_72h) <= 1.0 and signal in {"optimal", "cool", "warm"}:
        trend = "stable"
        score_delta += 2
        _add_rule(rules, "water_temp_stable", 2, "Stable water temperature")
    elif delta_72h is None and delta_24h is None:
        trend = "unknown"

    confidence = "medium" if delta_24h is not None or delta_72h is not None else "low"
    return {
        "signal": signal,
        "trend": trend,
        "confidence": confidence,
        "score_delta": score_delta,
        "rules": rules,
    }


def _enrich_environment(
    environment: EnvironmentInputs,
    *,
    classification: WaterbodyClassification,
    effective_region_slug: str,
) -> EnvironmentInputs:
    fish_profile = environment.fish_profile
    if fish_profile in {"", "generic_estuary"} and classification.waterbody_class != "generic_coastal":
        fish_profile = _default_fish_profile(classification.waterbody_class)

    current = _tide_current_context(environment, classification.waterbody_class)
    temp = _water_temperature_context(environment, fish_profile)
    return replace(
        environment,
        waterbody_class=classification.waterbody_class,
        fish_profile=fish_profile,
        tide_current_confidence=current["tide_current_confidence"],
        current_strength_proxy=current["current_strength_proxy"],
        current_source_note=current["current_source_note"],
        water_temperature_signal=temp["signal"],
        water_temperature_trend=temp["trend"],
        temperature_confidence=temp["confidence"],
        rule_family=environment.rule_family,
    )


def _directional_alignment(open_water_bearing_deg: float | None, forcing_direction_deg: float | None) -> float:
    if open_water_bearing_deg is None or forcing_direction_deg is None:
        return 0.5
    distance = _angular_distance_deg(open_water_bearing_deg, forcing_direction_deg)
    return round(max(0.0, math.cos(math.radians(distance))), 2)


def _wind_system_fit(
    *,
    wind_speed_knots: float,
    wind_direction_deg: float | None,
    open_water_bearing_deg: float | None,
    wind_onshore_knots: float | None,
    wind_offshore_knots: float | None,
    wind_alongshore_knots: float | None,
) -> float:
    if wind_direction_deg is None or open_water_bearing_deg is None:
        return 0.5

    wind_kph = wind_speed_knots * 1.852
    if wind_kph < 4:
        return 0.42
    if wind_kph > 35:
        return 0.22
    if wind_offshore_knots is not None and wind_offshore_knots >= 8 and wind_kph >= 12:
        return 0.34
    if wind_onshore_knots is not None and wind_onshore_knots >= 4:
        return 0.72 if wind_kph <= 22 else 0.52
    if wind_alongshore_knots is not None and wind_alongshore_knots >= 4:
        return 0.66 if wind_kph <= 25 else 0.48
    return 0.5


def _wind_to_shore_context(
    *,
    environment: EnvironmentInputs,
    signals: GlobalSignals,
    wind_onshore_knots: float | None,
    wind_offshore_knots: float | None,
    wind_alongshore_knots: float | None,
) -> dict[str, Any]:
    wind_kph = environment.wind_speed_knots * 1.852
    if environment.wind_direction_deg is None or signals.open_water_bearing_deg is None:
        return {
            "category": "direction_unknown",
            "score": 0.5,
            "rules": [{"id": "wind_direction_unknown", "score_delta": 0, "label": "Wind direction not available"}],
        }
    if signals.search_confidence_score < 0.35:
        return {
            "category": "geometry_uncertain",
            "score": 0.5,
            "rules": [{"id": "wind_geometry_uncertain", "score_delta": 0, "label": "Broad shoreline geometry"}],
        }
    if wind_kph < 4:
        return {"category": "too_light_to_organise_edge", "score": 0.42, "rules": []}
    if wind_kph > 35:
        return {
            "category": "exposed_presentation_risk",
            "score": 0.22,
            "rules": [{"id": "wind_presentation_penalty", "score_delta": -4, "label": "Wind likely hurts presentation"}],
        }
    if wind_offshore_knots is not None and wind_offshore_knots >= 8 and wind_kph >= 12:
        return {
            "category": "offshore_or_push_away",
            "score": 0.34,
            "rules": [{"id": "offshore_push_away", "score_delta": -4, "label": "Wind may not support this shoreline"}],
        }
    if wind_onshore_knots is not None and wind_onshore_knots >= 4:
        score = 0.72 if wind_kph <= 22 else 0.52
        delta = 3 if wind_kph <= 22 else 1
        return {
            "category": "onshore_or_push_to_edge",
            "score": score,
            "rules": [{"id": "useful_wind_push", "score_delta": delta, "label": "Wind direction may support this edge"}],
        }
    if wind_alongshore_knots is not None and wind_alongshore_knots >= 4:
        score = 0.66 if wind_kph <= 25 else 0.48
        delta = 2 if wind_kph <= 25 else 0
        return {
            "category": "side_shore_with_ripple",
            "score": score,
            "rules": [{"id": "side_shore_ripple", "score_delta": delta, "label": "Side-shore wind may organise an edge"}],
        }
    return {"category": "direction_neutral", "score": 0.5, "rules": []}


def _structure_flow_context(signals: GlobalSignals, tide_movement: float) -> dict[str, Any]:
    structure_edge_signal = _clamp_unit(
        (0.65 * signals.coastline_complexity)
        + (0.20 * signals.shelter)
        + (0.15 * signals.coastal_edge_signal)
    )
    interaction = _clamp_unit(structure_edge_signal * tide_movement)
    if structure_edge_signal < 0.34:
        return {
            "category": "weak_or_simple_edge",
            "structure_edge_signal": structure_edge_signal,
            "interaction": interaction,
            "rules": [],
        }
    if tide_movement < 0.46:
        return {
            "category": "edge_waiting_for_flow",
            "structure_edge_signal": structure_edge_signal,
            "interaction": interaction,
            "rules": [],
        }
    if interaction >= 0.38:
        return {
            "category": "complex_edge_with_moving_water",
            "structure_edge_signal": structure_edge_signal,
            "interaction": interaction,
            "rules": [],
        }
    if interaction >= 0.32:
        return {
            "category": "modest_edge_flow",
            "structure_edge_signal": structure_edge_signal,
            "interaction": interaction,
            "rules": [],
        }
    return {
        "category": "edge_flow_neutral",
        "structure_edge_signal": structure_edge_signal,
        "interaction": interaction,
        "rules": [],
    }


def _add_rule(rules: list[dict[str, Any]], rule_id: str, delta: float, label: str) -> None:
    rules.append({"id": rule_id, "score_delta": delta, "label": label})


def _recent_rainfall_amounts(environment: EnvironmentInputs) -> tuple[float, float, float]:
    current_rain = max(environment.precipitation_mm, environment.rain_mm)
    rain_12h = environment.recent_precipitation_sum_12h
    if rain_12h is None:
        rain_12h = current_rain
    rain_24h = environment.rainfall_24h if environment.rainfall_24h is not None else max(current_rain, rain_12h)
    rain_48h = environment.rainfall_48h if environment.rainfall_48h is not None else rain_24h
    return float(current_rain), float(rain_24h), float(rain_48h)


def _weather_recovery_multiplier(environment: EnvironmentInputs, rules: list[dict[str, Any]]) -> float:
    recovery_points = 0.0

    if environment.temperature_drop_from_recent_72h_peak is not None and environment.temperature_drop_from_recent_72h_peak <= -4.5:
        if environment.temperature_delta_24h is not None:
            if environment.temperature_delta_24h >= -1.0:
                recovery_points += 1.2
            elif environment.temperature_delta_24h >= -2.0:
                recovery_points += 0.6

    pressure_trend_values = [
        abs(value)
        for value in (
            environment.pressure_delta_24h,
            environment.pressure_delta_48h,
            environment.pressure_delta_72h,
        )
        if value is not None
    ]
    if pressure_trend_values and max(pressure_trend_values) >= 10:
        if environment.pressure_delta_3h is not None and abs(environment.pressure_delta_3h) < 1.5:
            recovery_points += 0.5
        if environment.pressure_delta_6h is not None and abs(environment.pressure_delta_6h) < 2.0:
            recovery_points += 0.7

    if environment.max_gust_72h is not None and environment.max_gust_72h * 1.852 >= 45:
        if environment.max_gust_24h is not None and environment.max_gust_24h * 1.852 < 35:
            recovery_points += 0.6

    if environment.rainfall_72h is not None and environment.rainfall_72h >= 45:
        rainfall_24h = environment.rainfall_24h if environment.rainfall_24h is not None else 0.0
        if rainfall_24h < 8:
            recovery_points += 0.7

    if environment.wave_height_delta_24h is not None and environment.wave_height_delta_24h <= -0.08:
        recovery_points += 0.4

    if recovery_points >= 2.2:
        _add_rule(rules, "weather_trend_recovering", 0, "Weather trend is recovering")
        return 0.55
    if recovery_points >= 1.2:
        _add_rule(rules, "partial_weather_recovery", 0, "Weather trend is partly recovering")
        return 0.72
    if recovery_points >= 0.6:
        _add_rule(rules, "early_weather_recovery", 0, "Weather trend is starting to recover")
        return 0.85
    return 1.0


def _weather_shock_rules(environment: EnvironmentInputs) -> tuple[float, list[dict[str, Any]]]:
    shock = 0.0
    rules: list[dict[str, Any]] = []

    pressure_delta_candidates = [
        value
        for value in (
            environment.pressure_delta_24h,
            environment.pressure_delta_48h,
            environment.pressure_delta_72h,
        )
        if value is not None
    ]
    max_pressure_break = max((abs(value) for value in pressure_delta_candidates), default=0.0)
    if environment.pressure_delta_24h is not None and abs(environment.pressure_delta_24h) >= 8:
        shock += 1.5
        _add_rule(rules, "rapid_pressure_change_24h", 0, "Large 24h pressure change")
    if max_pressure_break >= 12:
        shock += 1.25
        _add_rule(rules, "multi_day_pressure_break", 0, "Multi-day pressure trend break")
    elif max_pressure_break >= 10 and not any(rule["id"] == "rapid_pressure_change_24h" for rule in rules):
        shock += 1.0
        _add_rule(rules, "multi_day_pressure_break", 0, "Multi-day pressure trend break")
    if environment.pressure_delta_6h is not None and abs(environment.pressure_delta_6h) >= 4:
        shock += 1.0
        _add_rule(rules, "rapid_pressure_change_6h", 0, "Fast pressure change")

    temperature_delta_candidates = [
        value
        for value in (
            environment.temperature_delta_24h,
            environment.temperature_delta_48h,
            environment.temperature_delta_72h,
        )
        if value is not None
    ]
    strongest_temperature_drop = min(temperature_delta_candidates) if temperature_delta_candidates else None
    if strongest_temperature_drop is not None and strongest_temperature_drop <= -4:
        shock += 1.0
        _add_rule(rules, "rapid_temperature_drop", 0, "Recent temperature drop")
    if environment.temperature_drop_from_recent_72h_peak is not None:
        if environment.temperature_drop_from_recent_72h_peak <= -8:
            shock += 2.75
            _add_rule(rules, "severe_multi_day_cold_break", 0, "Severe break from recent warm trend")
        elif environment.temperature_drop_from_recent_72h_peak <= -6:
            shock += 2.25
            _add_rule(rules, "trend_breaking_cold_change", 0, "Sharp break from recent warm trend")
        elif environment.temperature_drop_from_recent_72h_peak <= -4.5:
            shock += 1.1
            _add_rule(rules, "recent_warm_trend_interrupted", 0, "Recent warm trend interrupted")
    if environment.wind_direction_change_12h is not None and environment.wind_direction_change_12h >= 90:
        shock += 1.0
        _add_rule(rules, "strong_wind_shift", 0, "Recent wind direction shift")

    gust_kph = None if environment.max_gust_24h is None else environment.max_gust_24h * 1.852
    gust_72h_kph = None if environment.max_gust_72h is None else environment.max_gust_72h * 1.852
    if gust_kph is not None:
        if gust_kph >= 65:
            shock += 2.0
            _add_rule(rules, "recent_severe_gusts", 0, "Recent severe gusts")
        elif gust_kph >= 45:
            shock += 1.0
            _add_rule(rules, "recent_heavy_gusts", 0, "Recent heavy gusts")
    elif gust_72h_kph is not None and gust_72h_kph >= 65:
        shock += 0.75
        _add_rule(rules, "multi_day_recent_severe_gusts", 0, "Severe gusts earlier in the trend window")

    _current_rain, rainfall_24h, _rainfall_48h = _recent_rainfall_amounts(environment)
    if rainfall_24h >= 30:
        shock += 1.5
        _add_rule(rules, "recent_heavy_rain_shock", 0, "Heavy rain in the last day")
    elif environment.rainfall_72h is not None and environment.rainfall_72h >= 45:
        shock += 0.75
        _add_rule(rules, "multi_day_rain_disruption", 0, "Multi-day rain disruption")
    if environment.wave_height_delta_24h is not None and abs(environment.wave_height_delta_24h) >= 0.6:
        shock += 1.0
        _add_rule(rules, "rapid_wave_change", 0, "Rapid sea-state change")

    raw_shock = shock
    if shock >= 1.5:
        shock *= _weather_recovery_multiplier(environment, rules)
        if shock < raw_shock:
            _add_rule(rules, "weather_shock_reduced_by_recovery", 0, "Weather shock is easing")

    if shock < 1.5:
        return round(shock, 2), rules
    if shock < 2.5:
        penalty = -8
    elif shock < 4.0:
        penalty = -14
    elif shock < 5.5:
        penalty = -22
    else:
        penalty = -30
    _add_rule(rules, "recent_weather_shock", penalty, "Recent weather instability")
    return round(shock, 2), rules


def _raw_time_signal_context(environment: EnvironmentInputs) -> dict[str, Any]:
    rules: list[dict[str, Any]] = []

    if environment.hours_from_sunrise is not None and abs(environment.hours_from_sunrise) <= 1.5:
        _add_rule(rules, "raw_sunrise_window", 14, "Around sunrise")
    elif environment.time_window == "dawn":
        _add_rule(rules, "raw_dawn_window", 12, "Early light window")

    if environment.hours_from_sunset is not None and abs(environment.hours_from_sunset) <= 1.5:
        _add_rule(rules, "raw_sunset_window", 14, "Around sunset")
    elif environment.time_window == "dusk":
        _add_rule(rules, "raw_dusk_window", 12, "Late light window")

    if environment.moon_phase_name in {"new_moon", "full_moon"}:
        _add_rule(rules, "raw_major_moon_phase", 5, "Major moon phase")
        if environment.is_daylight is False and environment.moon_phase_name == "new_moon":
            _add_rule(rules, "raw_dark_moon_night", 3, "Dark moon night")
        if environment.is_daylight is False and environment.moon_phase_name == "full_moon":
            _add_rule(rules, "raw_full_moon_night", 3, "Bright full-moon night")

    if environment.hours_from_solar_noon is not None:
        if environment.is_daylight and abs(environment.hours_from_solar_noon) <= 2:
            _add_rule(rules, "raw_midday_penalty", -10, "Bright midday period")
    elif environment.time_window == "day":
        _add_rule(rules, "raw_plain_day", -5, "Plain daylight period")

    score_delta = sum(rule["score_delta"] for rule in rules)
    score = _clamp(50.0 + score_delta)
    if score >= 68:
        label = "strong_time_signal"
    elif score >= 56:
        label = "useful_time_signal"
    elif score >= 45:
        label = "neutral_time_signal"
    else:
        label = "weak_time_signal"
    return {
        "score": score,
        "label": label,
        "score_delta": score_delta,
        "rules": rules,
        "reason_tags": [rule["id"] for rule in rules],
    }


def _generic_coastal_rules(environment: EnvironmentInputs) -> dict[str, Any]:
    """Generic coastal rules with spot-specific logic removed.

    This keeps the proven rule shape: light changes, moving tide, manageable
    wind, sea state, pressure trend, and seasonal context. It intentionally
    avoids private-engine named-spot adjustments.
    """
    rules: list[dict[str, Any]] = []

    if environment.hours_from_sunrise is not None and abs(environment.hours_from_sunrise) <= 1.5:
        _add_rule(rules, "sunrise_window", 10, "Around sunrise")
    elif environment.time_window == "dawn":
        _add_rule(rules, "dawn_window", 8, "Early light window")

    if environment.hours_from_sunset is not None and abs(environment.hours_from_sunset) <= 1.5:
        _add_rule(rules, "sunset_window", 10, "Around sunset")
    elif environment.time_window == "dusk":
        _add_rule(rules, "dusk_window", 8, "Late light window")

    if environment.moon_phase_name in {"new_moon", "full_moon"}:
        _add_rule(rules, "major_moon_phase_bonus", 4, "Major moon phase")
        if environment.is_daylight is False and environment.moon_phase_name == "new_moon":
            _add_rule(rules, "dark_moon_night_bonus", 3, "Dark moon night")
        if environment.is_daylight is False and environment.moon_phase_name == "full_moon":
            _add_rule(rules, "full_moon_night_bonus", 3, "Bright full-moon night")

    if environment.hours_from_solar_noon is not None:
        if environment.is_daylight and abs(environment.hours_from_solar_noon) <= 2:
            _add_rule(rules, "harsh_midday_penalty", -8, "Bright midday period")
    elif environment.time_window == "day":
        _add_rule(rules, "plain_day_penalty", -4, "Plain daylight period")

    if environment.tide_stage == "flood":
        if environment.hours_to_high_tide is not None and environment.hours_to_high_tide <= 2:
            _add_rule(rules, "rising_tide_window", 12, "Flood tide approaching high")
        if environment.hours_since_low_tide is not None and environment.hours_since_low_tide <= 2:
            _add_rule(rules, "early_flood_bonus", 8, "Early flood after low")
    elif environment.tide_stage == "ebb":
        if environment.hours_to_low_tide is not None and environment.hours_to_low_tide <= 2:
            _add_rule(rules, "falling_tide_window", 5, "Ebb tide approaching low")
    elif environment.tide_stage == "slack":
        _add_rule(rules, "slack_tide_penalty", -6, "Slack water")
    elif environment.tide_phase == "rising":
        _add_rule(rules, "rising_tide_proxy", 7, "Moving flood tide")
    elif environment.tide_phase == "falling":
        _add_rule(rules, "falling_tide_proxy", 4, "Moving ebb tide")

    if environment.tide_range_m is not None:
        if environment.tide_range_m > 0.6:
            _add_rule(rules, "large_tide_range", 5, "Larger tide movement")
        elif environment.tide_range_m < 0.3:
            _add_rule(rules, "small_tide_range", -3, "Small tide movement")
    if environment.tide_height_change_next_2h is not None and environment.tide_height_change_next_2h < 0.05:
        _add_rule(rules, "dead_water_2h", -12, "Very weak local tide movement")
    elif environment.tide_height_change_next_3h is not None and environment.tide_height_change_next_3h < 0.08:
        _add_rule(rules, "weak_tide_movement_3h", -8, "Weak local tide movement")
    if environment.tide_movement_rate_m_per_hour is not None and environment.tide_movement_rate_m_per_hour < 0.03:
        _add_rule(rules, "weak_tide_rate", -5, "Slow tide-height change")
    if environment.tide_height_change_next_2h is not None and environment.tide_height_change_next_2h >= 0.12:
        _add_rule(rules, "strong_local_tide_flow", 4, "Strong local tide movement")
    if environment.tide_current_confidence == "low" and (
        environment.current_strength_proxy is None or environment.current_strength_proxy < 0.42
    ):
        _add_rule(rules, "low_confidence_current", -2, "Current strength is only weakly supported")

    wind_kph = environment.wind_speed_knots * 1.852
    if 5 <= wind_kph <= 12:
        _add_rule(rules, "moderate_wind_bonus", 4, "Manageable wind")
    elif 12 < wind_kph <= 20:
        _add_rule(rules, "light_wind_ok", 1, "Fishable wind")
    elif wind_kph > 20:
        _add_rule(rules, "strong_wind_penalty", -10, "Strong wind")
    if environment.wind_gust_knots is not None and environment.wind_gust_knots * 1.852 > 40:
        _add_rule(rules, "gust_penalty", -5, "Strong gusts")

    if environment.pressure_delta_3h is not None:
        if abs(environment.pressure_delta_3h) < 1.5:
            _add_rule(rules, "stable_pressure_bonus", 2, "Stable pressure")
        elif environment.pressure_delta_3h >= 1.5:
            _add_rule(rules, "pressure_rising", 2, "Rising pressure")
        elif environment.pressure_delta_3h <= -1.5:
            _add_rule(rules, "pressure_falling", 2, "Falling pressure")
        if abs(environment.pressure_delta_3h) >= 4:
            _add_rule(rules, "sharp_pressure_shift_flag", -2, "Sharp pressure shift")

    if environment.cloud_cover_pct is not None and 30 <= environment.cloud_cover_pct <= 80:
        _add_rule(rules, "cloud_cover_bonus", 4, "Moderate cloud cover")
    current_rain, rainfall_24h, rainfall_48h = _recent_rainfall_amounts(environment)
    wind_kph = environment.wind_speed_knots * 1.852
    if 0.1 <= current_rain <= 2 and wind_kph <= 25:
        _add_rule(rules, "light_rain_cover", 2, "Light rain cover")
    if 2 <= rainfall_24h <= 15 and wind_kph <= 25:
        _add_rule(rules, "moderate_rain_edge_opportunity", 0, "Moderate rain may help sheltered edges")
    if rainfall_24h >= 25:
        _add_rule(rules, "heavy_rain_disruption", -8, "Heavy recent rain")
    elif current_rain > 10:
        _add_rule(rules, "strong_rain_penalty", -6, "Strong rain")
    if rainfall_48h >= 50:
        _add_rule(rules, "major_rain_shock", -12, "Major rain disruption")
    if (
        environment.recent_precipitation_sum_12h is not None
        and environment.recent_precipitation_sum_12h >= 3.0
        and environment.wind_speed_knots * 1.852 <= 15
        and rainfall_24h < 25
    ):
        _add_rule(rules, "weather_recovery_window", 3, "Settling after recent weather")

    if environment.wave_height_m is not None:
        if 0.3 <= environment.wave_height_m <= 1.0:
            _add_rule(rules, "strong_wave_rock", 4, "Some wave energy")
        if environment.wave_height_m < 0.3:
            _add_rule(rules, "calm_sea_beach", 3, "Calm sea")
        if environment.wave_height_m > 1.0:
            wind_kph = environment.wind_speed_knots * 1.852
            if wind_kph >= 18:
                _add_rule(rules, "big_wave_beach", -5, "Larger surf and wind chop")
            else:
                _add_rule(rules, "passing_swell_high", -2, "Larger swell passing offshore")
    if environment.wave_height_delta_24h is not None and environment.wave_height_delta_24h <= -0.08:
        _add_rule(rules, "pelagic_settling_window", 2, "Settling sea")

    water_temp = _water_temperature_context(environment, environment.fish_profile)
    rules.extend(water_temp["rules"])

    weather_shock_score, shock_rules = _weather_shock_rules(environment)
    rules.extend(shock_rules)

    total_delta = sum(rule["score_delta"] for rule in rules)
    return {
        "family": environment.rule_family,
        "score_delta": round(total_delta, 2),
        "weather_shock_score": weather_shock_score,
        "rules": rules,
        "reason_tags": [rule["id"] for rule in rules],
    }


def _compress_extreme_score(score: float) -> float:
    if score <= 90:
        return score
    return min(100.0, 90.0 + ((score - 90.0) * 0.35))


def _compress_roaming_score(score: float) -> float:
    if score <= 70:
        return score
    return min(90.0, 70.0 + ((score - 70.0) * 0.34))


def _calibrate_public_preview_score(score: float) -> float:
    """Keep searched-coordinate previews below curated-spot certainty."""
    score = float(score)
    if score <= 35:
        return max(0.0, score * 0.92)
    if score <= 50:
        return 32.2 + ((score - 35.0) * 0.95)
    if score <= 65:
        return 46.45 + ((score - 50.0) * 1.02)
    if score <= 78:
        return 61.75 + ((score - 65.0) * 1.05)
    return min(86.5, 75.4 + ((score - 78.0) * 0.55))


def _reason_buckets(tags: set[str]) -> dict[str, int]:
    movement = {
        "rising_tide_window",
        "falling_tide_window",
        "early_flood_bonus",
        "large_tide_range",
        "strong_local_tide_flow",
        "pelagic_settling_window",
        "inferred_edge_flow",
    }
    concentration = {
        "large_tide_range",
        "strong_local_tide_flow",
        "calm_sea_beach",
        "strong_wave_rock",
        "cloud_cover_bonus",
        "weather_recovery_window",
        "water_temp_optimal",
        "water_temp_stable",
        "light_rain_cover",
        "useful_wind_push",
        "side_shore_ripple",
        "inferred_edge_flow",
    }
    timing = {
        "sunrise_window",
        "sunset_window",
        "dawn_window",
        "dusk_window",
        "major_moon_phase_bonus",
        "dark_moon_night_bonus",
        "full_moon_night_bonus",
    }
    negative = {
        "slack_tide_penalty",
        "plain_day_penalty",
        "strong_wind_penalty",
        "gust_penalty",
        "big_wave_beach",
        "ocean_influenced_estuary_swell_penalty",
        "open_bay_swell_cap",
        "rough_open_bay_cap",
        "water_temp_cold",
        "water_temp_cool",
        "water_temp_hot",
        "water_temp_cooling_fast",
        "water_temp_warming_fast",
        "low_confidence_current",
        "harsh_midday_penalty",
        "small_tide_range",
        "dead_water_2h",
        "weak_tide_movement_3h",
        "weak_tide_rate",
        "sharp_pressure_shift_flag",
        "recent_weather_shock",
        "heavy_rain_disruption",
        "strong_rain_penalty",
        "major_rain_shock",
        "offshore_push_away",
        "wind_presentation_penalty",
    }
    return {
        "movement": len(tags & movement),
        "concentration": len(tags & concentration),
        "timing": len(tags & timing),
        "negative": len(tags & negative),
    }


def _stack_adjustments(tags: set[str]) -> tuple[float, float]:
    buckets = _reason_buckets(tags)
    positive = 0.0
    negative = 0.0

    if buckets["movement"] >= 2 and buckets["timing"] >= 1:
        positive += 4.0
    if buckets["movement"] >= 2 and buckets["concentration"] >= 2:
        positive += 3.0
    if buckets["timing"] >= 2 and buckets["concentration"] >= 1:
        positive += 1.5
    if buckets["movement"] >= 3 and buckets["concentration"] >= 2 and buckets["timing"] >= 2:
        positive += 1.5

    if buckets["negative"] >= 2:
        negative += 5.0 + ((buckets["negative"] - 2) * 2.0)
    if {"slack_tide_penalty", "plain_day_penalty"} <= tags:
        negative += 3.0
    if "harsh_midday_penalty" in tags and buckets["movement"] == 0:
        negative += 4.0
    if "strong_wind_penalty" in tags and ({"gust_penalty", "big_wave_beach"} & tags):
        negative += 4.0
    rain_disruption = {"heavy_rain_disruption", "strong_rain_penalty", "major_rain_shock"} & tags
    if rain_disruption and ({"cold_water", "water_temp_cold", "strong_wind_penalty"} & tags):
        negative += 4.0
    if "recent_weather_shock" in tags and ({"dead_water_2h", "weak_tide_movement_3h", "weak_tide_rate"} & tags):
        negative += 5.0
    if {"ocean_influenced_estuary_swell_penalty", "big_wave_beach"} <= tags:
        negative += 4.0

    return positive, negative


def _is_resident_dominant_type(dominant_type: str) -> bool:
    return dominant_type in {"bay_estuary_edge", "jetty"}


def _resident_mode_score(dominant_type: str, dominant_scores: Mapping[str, Any], tags: set[str]) -> int:
    base_by_type = {
        "beach": 26,
        "rocks": 34,
        "jetty": 38,
        "bay_estuary_edge": 42,
    }
    score = float(base_by_type.get(dominant_type, 30))
    score += (float(dominant_scores["resident_opportunity"]) - 50.0) * 0.45

    if {"sunrise_window", "sunset_window", "dawn_window", "dusk_window"} & tags:
        score += 6
    if {"rising_tide_window", "falling_tide_window", "early_flood_bonus"} & tags:
        score += 6
    if {"moderate_wind_bonus", "cloud_cover_bonus", "stable_pressure_bonus", "pressure_rising", "pressure_falling"} & tags:
        score += 5
    if dominant_type in {"bay_estuary_edge", "jetty"} and {"calm_sea_beach", "large_tide_range"} & tags:
        score += 3

    if {"slack_tide_penalty", "harsh_midday_penalty"} & tags:
        score -= 4
    if {"strong_wind_penalty", "gust_penalty", "heavy_rain_disruption", "strong_rain_penalty", "major_rain_shock", "big_wave_beach"} & tags:
        score -= 7

    if dominant_type == "beach":
        score = min(score, 62)
    elif dominant_type == "rocks":
        score = min(score, 68)
    elif dominant_type == "jetty":
        score = min(score, 72)
    elif dominant_type == "bay_estuary_edge":
        score = min(score, 74)

    return min(88, _clamp(_compress_extreme_score(score)))


def _roaming_mode_score(dominant_type: str, dominant_scores: Mapping[str, Any], tags: set[str]) -> int:
    buckets = _reason_buckets(tags)
    pelagic_bias = dominant_type in {"beach", "rocks"}
    resident_dominance = _is_resident_dominant_type(dominant_type)

    base_by_type = {
        "beach": 34,
        "rocks": 36,
        "jetty": 22,
        "bay_estuary_edge": 24,
    }
    score = float(base_by_type.get(dominant_type, 26))
    score += (float(dominant_scores["roaming_opportunity"]) - 50.0) * 0.32

    score += buckets["movement"] * 7
    score += buckets["concentration"] * 5
    score += buckets["timing"] * 6
    score -= buckets["negative"] * 5

    if not pelagic_bias:
        score = min(score, 46)
    if resident_dominance and buckets["concentration"] == 0:
        score = min(score, 38)
    if buckets["movement"] == 0:
        score = min(score, 46)
    if buckets["concentration"] == 0:
        score = min(score, 52)
    if buckets["timing"] == 0:
        score = min(score, 60)
    if resident_dominance and buckets["movement"] < 2:
        score = min(score, 58)

    strong_combo = buckets["movement"] >= 2 and buckets["concentration"] >= 1 and buckets["timing"] >= 1
    if score >= 74 and buckets["movement"] < 2:
        score = min(score, 68)
    if score >= 78 and not strong_combo:
        score = min(score, 70)
    if score >= 82 and not (buckets["movement"] >= 3 and buckets["concentration"] >= 2 and buckets["timing"] >= 1):
        score = min(score, 76)

    return min(90, _clamp(_compress_roaming_score(score)))


def _false_high_score_guards(
    *,
    activity: float,
    presence: float,
    trip_quality: float,
    resident: float,
    roaming: float,
    tags: set[str],
) -> tuple[float, float, float, float, float, list[str]]:
    guard_tags: list[str] = []
    timing_tags = {
        "sunrise_window",
        "sunset_window",
        "dawn_window",
        "dusk_window",
        "major_moon_phase_bonus",
        "dark_moon_night_bonus",
        "full_moon_night_bonus",
    }
    movement_positive = {
        "rising_tide_window",
        "falling_tide_window",
        "early_flood_bonus",
        "rising_tide_proxy",
        "falling_tide_proxy",
        "large_tide_range",
    }
    weak_movement = {"dead_water_2h", "weak_tide_movement_3h", "weak_tide_rate", "small_tide_range"} & tags
    strong_timing = len(tags & timing_tags) >= 2 or (
        "major_moon_phase_bonus" in tags and bool(tags & {"sunrise_window", "sunset_window", "dawn_window", "dusk_window"})
    )

    if strong_timing and "dead_water_2h" in tags:
        activity = min(activity, 65)
        presence = min(presence, 63)
        trip_quality = min(trip_quality, 65)
        roaming = min(roaming, 65)
        guard_tags.append("timing_capped_by_dead_water")

    if strong_timing and "recent_weather_shock" in tags and weak_movement:
        activity = min(activity, 60)
        presence = min(presence, 58)
        trip_quality = min(trip_quality, 58)
        resident = min(resident, 62)
        roaming = min(roaming, 58)
        guard_tags.append("timing_capped_by_local_instability")

    if activity >= 68 and trip_quality <= 52:
        activity = min(activity, trip_quality + 14)
        guard_tags.append("activity_capped_by_trip_quality")

    if not (tags & movement_positive) and (weak_movement or "slack_tide_penalty" in tags):
        presence = min(presence, max(0, activity - 6))
        if "plain_day_penalty" in tags or "harsh_midday_penalty" in tags:
            guard_tags.append("presence_capped_by_weak_movement")

    return activity, presence, trip_quality, resident, roaming, guard_tags


def _local_system_priority_guards(
    *,
    activity: float,
    presence: float,
    trip_quality: float,
    resident: float,
    roaming: float,
    tags: set[str],
    dominant_type: str,
    environment_context: Mapping[str, Any],
) -> tuple[float, float, float, float, float, list[str]]:
    guard_tags: list[str] = []
    normalized = environment_context.get("normalized", {})
    inputs = environment_context.get("inputs_used", {})
    flow_strength = float(normalized.get("water_flow_strength", normalized.get("movement_bonus", 0.5)))
    wind_fit = float(normalized.get("wind_system_fit", 0.5))
    weather_shock = float(normalized.get("weather_shock", 0.0))
    current_confidence = str(inputs.get("tide_current_confidence") or "low")
    waterbody_class = str(inputs.get("waterbody_class") or "")
    temp_signal = str(inputs.get("water_temperature_signal") or "unknown")
    temp_trend = str(inputs.get("water_temperature_trend") or "unknown")
    trend_break = bool(
        tags
        & {
            "trend_breaking_cold_change",
            "severe_multi_day_cold_break",
            "rapid_temperature_drop",
            "multi_day_pressure_break",
            "strong_wind_shift",
            "recent_heavy_rain_shock",
            "multi_day_rain_disruption",
        }
    )
    estuary_like = dominant_type in {"bay_estuary_edge", "jetty"}
    open_like = dominant_type in {"beach", "rocks"}

    if estuary_like and "recent_weather_shock" in tags and trend_break:
        if flow_strength < 0.68 or wind_fit < 0.50 or weather_shock >= 4.0:
            activity = min(activity, 60)
            presence = min(presence, 60)
            trip_quality = min(trip_quality, 58)
            resident = min(resident, 64)
            roaming = min(roaming, 56)
            guard_tags.append("estuary_system_trend_cap")
        elif not (tags & {"weather_recovery_window", "weather_trend_recovering", "partial_weather_recovery"}):
            activity = min(activity, 66)
            presence = min(presence, 66)
            trip_quality = min(trip_quality, 64)
            guard_tags.append("estuary_trend_needs_recovery")

    if estuary_like and flow_strength < 0.46 and {"sunrise_window", "sunset_window", "major_moon_phase_bonus"} & tags:
        activity = min(activity, 58)
        presence = min(presence, 56)
        trip_quality = min(trip_quality, 58)
        guard_tags.append("estuary_timing_capped_by_flow")

    if current_confidence == "low" and waterbody_class in {"river_mouth", "tidal_river"} and activity >= 68:
        activity = min(activity, 66)
        presence = min(presence, 66)
        trip_quality = min(trip_quality, 64)
        guard_tags.append("river_current_confidence_cap")

    if temp_signal == "cold" and temp_trend in {"cooling_fast", "unknown"} and activity >= 62:
        activity = min(activity, 60)
        presence = min(presence, 58)
        roaming = min(roaming, 58)
        guard_tags.append("cold_water_fish_signal_cap")

    if open_like and "recent_weather_shock" in tags and trend_break and (flow_strength < 0.55 or wind_fit < 0.42):
        activity = min(activity, 62)
        presence = min(presence, 60)
        trip_quality = min(trip_quality, 58)
        guard_tags.append("open_coast_system_trend_cap")

    return activity, presence, trip_quality, resident, roaming, guard_tags


def _ocean_influenced_estuary_pressure(
    *,
    dominant_type: str,
    environment_context: Mapping[str, Any],
) -> dict[str, Any]:
    if dominant_type not in {"bay_estuary_edge", "jetty"}:
        return {"severity": 0.0, "tags": []}

    normalized = environment_context.get("normalized", {})
    inputs = environment_context.get("inputs_used", {})
    water_body_exposure = float(normalized.get("water_body_exposure", 0.0) or 0.0)
    inner_bay_shelter = float(normalized.get("inner_bay_shelter", 1.0) or 1.0)
    exposed_penalty = float(normalized.get("exposed_penalty", 0.0) or 0.0)
    wave_height = float(inputs.get("wave_height_m") or inputs.get("swell_height_m") or 0.0)
    swell_height = float(inputs.get("swell_height_m") or 0.0)
    swell_direction = inputs.get("swell_direction_deg")
    open_water_bearing = environment_context.get("open_water_bearing_deg")
    wind_speed_knots = float(inputs.get("wind_speed_knots") or 0.0)
    effective_wave = max(wave_height, swell_height * 1.08)

    ocean_influenced = water_body_exposure >= 0.42 and inner_bay_shelter <= 0.62
    if not ocean_influenced or effective_wave < 1.35:
        return {"severity": 0.0, "tags": []}

    # Directional gate: if the swell is coming from a direction that does not
    # align with the open-water bearing of this coordinate, the offshore swell
    # is unlikely to actually pressure the bay's inner angles. Only apply the
    # gate when both directions are known; otherwise preserve the existing
    # conservative behavior.
    if swell_direction is not None and open_water_bearing is not None:
        from_open_water = _angular_distance_deg(float(swell_direction), float(open_water_bearing))
        if from_open_water > 70.0:
            return {"severity": 0.0, "tags": []}

    severity = 1.0
    tags = ["ocean_influenced_estuary_swell_penalty"]
    if effective_wave >= 2.2 or exposed_penalty >= 0.18:
        severity = 2.0
        tags.append("open_bay_swell_cap")
    if effective_wave >= 3.2:
        severity = 3.0
        tags.append("rough_open_bay_cap")

    # Light-wind softening: when local wind is light AND wave is moderate,
    # the swell is passing offshore rather than driving chop in the bay. This
    # is the typical "calm day with offshore swell" Tasmanian estuary case.
    # Reduce severity by one tier (but never below 0).
    wind_kph = wind_speed_knots * 1.852
    if wind_kph < 12 and effective_wave < 2.2:
        severity = 0.0
        return {"severity": 0.0, "tags": []}

    return {
        "severity": severity,
        "effective_wave_m": round(effective_wave, 2),
        "tags": tags,
    }


def _sheltered_estuary_support_lift(
    *,
    dominant_type: str,
    environment_context: Mapping[str, Any],
    tags: set[str],
) -> tuple[float, list[str]]:
    """Small UX calibration for sheltered estuaries when the local system is genuinely working."""
    if environment_context.get("region_slug") != "sheltered_estuary":
        return 0.0, []
    if dominant_type not in {"bay_estuary_edge", "jetty"}:
        return 0.0, []

    normalized = environment_context.get("normalized", {})
    flow_strength = float(normalized.get("water_flow_strength", 0.5) or 0.5)
    wind_fit = float(normalized.get("wind_system_fit", 0.5) or 0.5)
    weather_shock = float(normalized.get("weather_shock", 0.0) or 0.0)
    structure_flow = float(normalized.get("structure_flow_interaction", 0.0) or 0.0)
    ocean_pressure = _ocean_influenced_estuary_pressure(
        dominant_type=dominant_type,
        environment_context=environment_context,
    )

    blocking_tags = {
        "recent_weather_shock",
        "dead_water_2h",
        "weak_tide_movement_3h",
        "weak_tide_rate",
        "offshore_push_away",
        "wind_presentation_penalty",
        "strong_wind_penalty",
        "gust_penalty",
        "heavy_rain_disruption",
        "strong_rain_penalty",
        "major_rain_shock",
        "sharp_pressure_shift_flag",
        "rapid_temperature_drop",
        "trend_breaking_cold_change",
        "severe_multi_day_cold_break",
        "recent_warm_trend_interrupted",
        "rapid_pressure_change_24h",
        "rapid_pressure_change_6h",
        "multi_day_pressure_break",
        "strong_wind_shift",
        "recent_heavy_rain_shock",
        "multi_day_rain_disruption",
        "low_confidence_current",
        "water_temp_cold",
        "water_temp_cooling_fast",
    }
    if tags & blocking_tags or weather_shock >= 1.5 or float(ocean_pressure.get("severity", 0.0) or 0.0) > 0:
        return 0.0, []
    if flow_strength < 0.62 or wind_fit < 0.46:
        return 0.0, []

    moving_water_tags = {"rising_tide_window", "falling_tide_window", "early_flood_bonus", "strong_local_tide_flow"}
    timing_tags = {"sunrise_window", "sunset_window", "dawn_window", "dusk_window"}
    edge_tags = {"inferred_edge_flow", "modest_inferred_edge_flow"}
    if not ((tags & moving_water_tags) or structure_flow >= 0.32):
        return 0.0, []

    lift = 3.0
    if flow_strength >= 0.72 and ((tags & timing_tags) or (tags & edge_tags) or structure_flow >= 0.38):
        lift = 5.5
    return lift, ["sheltered_estuary_supportive_flow"]


def _local_adjustment_breakdown(
    *,
    score_modes: Mapping[str, Any],
    environment_context: Mapping[str, Any],
) -> dict[str, Any]:
    raw_time = environment_context.get("raw_time_signal", {})
    raw_score = int(raw_time.get("score", 50))
    adjusted_score = int(score_modes["activity_score"])
    normalized = environment_context.get("normalized", {})
    inputs = environment_context.get("inputs_used", {})
    tags = set(environment_context.get("generic_rules", {}).get("reason_tags", []))
    drivers: list[dict[str, str]] = []

    def add_driver(kind: str, driver_id: str, label: str) -> None:
        drivers.append({"type": kind, "id": driver_id, "label": label})

    flow_strength = float(normalized.get("water_flow_strength", 0.5))
    wind_fit = float(normalized.get("wind_system_fit", 0.5))
    weather_shock = float(normalized.get("weather_shock", 0.0))
    structure_category = str(inputs.get("structure_flow_category") or "unknown")
    wind_category = str(inputs.get("wind_to_shore_category") or "unknown")

    if flow_strength >= 0.68 or "strong_local_tide_flow" in tags:
        add_driver("positive", "moving_water", "Local water movement supports the time signal")
    elif flow_strength < 0.46 or {"dead_water_2h", "weak_tide_movement_3h", "weak_tide_rate"} & tags:
        add_driver("negative", "weak_water_movement", "Weak local water movement reduced the time signal")

    if wind_category == "onshore_or_push_to_edge":
        add_driver("positive", "supportive_wind_direction", "Wind direction may support this shoreline")
    elif wind_category == "offshore_or_push_away":
        add_driver("negative", "unsupported_wind_direction", "Wind direction may not support this shoreline")
    elif wind_fit < 0.35:
        add_driver("negative", "wind_presentation_risk", "Wind strength may hurt presentation")

    if weather_shock >= 3.0 or "recent_weather_shock" in tags:
        add_driver("negative", "recent_weather_instability", "Recent weather instability reduced local confidence")
    elif {"stable_pressure_bonus", "weather_recovery_window", "weather_trend_recovering", "partial_weather_recovery"} & tags:
        add_driver("positive", "stable_or_recovering_weather", "Stable or recovering weather supported the window")

    if structure_category == "complex_edge_with_moving_water":
        add_driver("positive", "edge_flow_interaction", "Inferred edges and moving water supported the local setup")
    elif structure_category == "modest_edge_flow":
        add_driver("positive", "modest_edge_flow", "Some inferred edge flow supported the local setup")
    elif structure_category == "edge_waiting_for_flow":
        add_driver("negative", "edge_waiting_for_flow", "Inferred edges did not have enough moving water")

    return {
        "raw_time_signal_score": raw_score,
        "raw_time_signal_label": raw_time.get("label", "neutral_time_signal"),
        "raw_time_reason_tags": raw_time.get("reason_tags", []),
        "local_adjusted_score": adjusted_score,
        "adjustment_delta": adjusted_score - raw_score,
        "drivers": drivers[:5],
        "local_inputs": {
            "water_flow_strength": round(flow_strength, 2),
            "wind_system_fit": round(wind_fit, 2),
            "weather_shock": round(weather_shock, 2),
            "wind_to_shore_category": wind_category,
            "structure_flow_category": structure_category,
        },
    }


# Safety / Comfort / Fish split: parallel views on top of the engine's
# existing activity / presence / trip_quality scores. These are NEW fields
# that don't replace the legacy ones; the engine's main score and the
# 102+ regression assertions stay untouched. The point is to give the
# frontend three independent dimensions so a "great fish day in dangerous
# weather" doesn't get hidden behind a single muddled trip_quality number.
SAFETY_FLAG_LOW = "low"
SAFETY_FLAG_MODERATE = "moderate"
SAFETY_FLAG_ELEVATED = "elevated"
SAFETY_FLAG_HAZARDOUS = "hazardous"
EXPOSED_TYPES_FOR_SAFETY = frozenset({"beach", "rocks"})


def _fish_outlook_score(activity_score: float, presence_score: float) -> int:
    """Pure fish-opportunity view: activity + presence, no trip / safety mix.

    Activity weighs slightly more because it captures rule alignment, while
    presence is a softer signal on whether fish are likely concentrated.
    """
    fish = (0.55 * float(activity_score)) + (0.45 * float(presence_score))
    return _clamp(fish)


def _comfort_score(
    *,
    inputs_used: Mapping[str, Any],
    normalized: Mapping[str, Any],
) -> tuple[int, list[str]]:
    """Body-comfort view: temperature, wind chill, rain, gusts, wave drag.

    Returns a 0-100 score plus the list of factor tags that pushed it down.
    A clean autumn morning at 14C with light wind starts near 80; cold
    wet windy conditions land in the teens.
    """
    factors: list[str] = []
    score = 78.0

    temperature_c = inputs_used.get("temperature_c")
    wind_speed_knots = float(inputs_used.get("wind_speed_knots") or 0.0)
    wind_gust_knots = inputs_used.get("wind_gust_knots")
    rain_mm = float(inputs_used.get("rain_mm") or 0.0)
    recent_precip = float(inputs_used.get("recent_precipitation_sum_12h") or 0.0)
    wave_height_m = float(inputs_used.get("wave_height_m") or 0.0)
    swell_height_m = float(inputs_used.get("swell_height_m") or 0.0)
    effective_sea_m = max(wave_height_m, swell_height_m * 0.85)
    cloud_cover_pct = inputs_used.get("cloud_cover_pct")

    if temperature_c is not None:
        temp = float(temperature_c)
        if temp < 4:
            score -= 28
            factors.append("very_cold_air")
        elif temp < 8:
            score -= 18
            factors.append("cold_air")
        elif temp < 12:
            score -= 8
            factors.append("cool_air")
        elif 16 <= temp <= 24:
            score += 4
        elif temp > 28:
            score -= 6
            factors.append("hot_air")

        gust_spread = max(0.0, float(wind_gust_knots or wind_speed_knots) - wind_speed_knots)
        wet_drag = 2.0 if rain_mm >= 0.4 else 0.0
        if recent_precip >= 2.0:
            wet_drag += 1.0
        wind_chill_proxy = (
            temp
            - max(0.0, wind_speed_knots - 3.2) * 1.02
            - gust_spread * 0.22
            - wet_drag
        )
        if wind_chill_proxy <= 0:
            score -= 14
            factors.append("biting_wind_chill")
        elif wind_chill_proxy <= 4:
            score -= 8
            factors.append("notable_wind_chill")
        elif wind_chill_proxy <= 7:
            score -= 3
            factors.append("mild_wind_chill")

    if rain_mm >= 2.0:
        score -= 14
        factors.append("steady_rain")
    elif rain_mm >= 0.4:
        score -= 6
        factors.append("light_rain")
    elif recent_precip >= 3.0:
        score -= 3
        factors.append("recent_wet_air")

    gust_kn = float(wind_gust_knots) if wind_gust_knots is not None else wind_speed_knots
    if gust_kn >= 30:
        score -= 18
        factors.append("strong_gusts")
    elif gust_kn >= 22:
        score -= 10
        factors.append("brisk_gusts")
    elif wind_speed_knots >= 18:
        score -= 6
        factors.append("brisk_wind")

    if effective_sea_m >= 2.5:
        score -= 12
        factors.append("rough_seas")
    elif effective_sea_m >= 1.5:
        score -= 5
        factors.append("notable_seas")
    elif swell_height_m >= 1.2 and wave_height_m < 1.0:
        score -= 3
        factors.append("long_period_swell")

    if cloud_cover_pct is not None:
        cloud = float(cloud_cover_pct)
        if cloud >= 95 and rain_mm >= 0.4:
            score -= 2
            factors.append("overcast_with_rain")

    return _clamp(score), factors


def _safety_flag(
    *,
    inputs_used: Mapping[str, Any],
    dominant_type: str,
    tags: set[str],
) -> tuple[str, list[str], int]:
    """Independent safety lens. Returns (flag, factors, raw_risk_points).

    Safety is intentionally a 4-tier enum (not a 0-100 number) because users
    rarely want to debate "how safe is 62". The boundaries map to:
        low        : no major broad-condition risk detected
        moderate   : worth being aware of the conditions
        elevated   : real risk; experienced anglers only / pick spots carefully
        hazardous  : do not fish exposed water; safety > fish today
    """
    factors: list[str] = []
    risk_points = 0

    wave_height_m = float(inputs_used.get("wave_height_m") or inputs_used.get("swell_height_m") or 0.0)
    swell_height_m = float(inputs_used.get("swell_height_m") or 0.0)
    effective_wave = max(wave_height_m, swell_height_m * 1.08)
    wind_speed_knots = float(inputs_used.get("wind_speed_knots") or 0.0)
    wind_gust_knots_raw = inputs_used.get("wind_gust_knots")
    wind_gust_knots = float(wind_gust_knots_raw) if wind_gust_knots_raw is not None else wind_speed_knots
    temperature_c = inputs_used.get("temperature_c")
    rain_mm = float(inputs_used.get("rain_mm") or 0.0)
    rainfall_24h = float(inputs_used.get("rainfall_24h") or 0.0)
    wave_height_delta_24h = inputs_used.get("wave_height_delta_24h")

    if effective_wave >= 3.5:
        risk_points += 4
        factors.append("rough_seas_above_3m")
    elif effective_wave >= 2.5:
        risk_points += 3
        factors.append("rough_seas_above_2m5")
    elif effective_wave >= 1.8:
        risk_points += 2
        factors.append("notable_wave_activity")
    elif effective_wave >= 1.2:
        risk_points += 1
        factors.append("moderate_wave_activity")

    if wind_speed_knots >= 25:
        risk_points += 3
        factors.append("strong_wind")
    elif wind_speed_knots >= 18:
        risk_points += 2
        factors.append("brisk_wind")

    if wind_gust_knots >= 35:
        risk_points += 3
        factors.append("severe_gusts")
    elif wind_gust_knots >= 25:
        risk_points += 2
        factors.append("strong_gusts")

    if dominant_type in EXPOSED_TYPES_FOR_SAFETY and effective_wave >= 1.5:
        risk_points += 2
        factors.append("exposed_with_wave")

    if (
        temperature_c is not None
        and float(temperature_c) <= 8
        and wind_speed_knots >= 10
        and (rain_mm >= 0.5 or rainfall_24h >= 5)
    ):
        risk_points += 2
        factors.append("cold_wet_windy")

    try:
        if wave_height_delta_24h is not None and float(wave_height_delta_24h) >= 0.6:
            risk_points += 1
            factors.append("rapid_wave_change")
    except (TypeError, ValueError):
        pass

    # Severe weather shock tag should bump safety even when individual numbers
    # are below the per-axis thresholds (e.g. fast pressure drop + gusts).
    if "severe_multi_day_cold_break" in tags or "trend_breaking_cold_change" in tags:
        risk_points += 1
        factors.append("severe_weather_break")

    if risk_points >= 6:
        flag = SAFETY_FLAG_HAZARDOUS
    elif risk_points >= 4:
        flag = SAFETY_FLAG_ELEVATED
    elif risk_points >= 2:
        flag = SAFETY_FLAG_MODERATE
    else:
        flag = SAFETY_FLAG_LOW

    return flag, factors, risk_points


def _trip_reality_score(comfort_score: int, safety_flag: str) -> int:
    """User-facing trip reality: comfort first, capped by broad safety risk.

    This intentionally excludes bite timing, tide strength, and fish presence.
    Those belong in fish_outlook/activity; a calm, dry, low-risk day should not
    receive a poor trip score just because the fish window is weak.
    """
    score = float(comfort_score)
    if safety_flag == SAFETY_FLAG_HAZARDOUS:
        score = min(score, 35)
    elif safety_flag == SAFETY_FLAG_ELEVATED:
        score = min(score, 55)
    elif safety_flag == SAFETY_FLAG_MODERATE:
        score = min(score, 70)
    return _clamp(score)


def _coastal_score_modes(
    *,
    cards: Mapping[str, dict[str, Any]],
    dominant_type: str,
    environment_context: Mapping[str, Any],
) -> dict[str, Any]:
    """Build public score layers without local spot rules."""
    rule_context = environment_context["generic_rules"]
    tags = set(rule_context["reason_tags"])
    dominant_card = cards[dominant_type]
    dominant_scores = dominant_card["scores"]
    positive_stack, negative_stack = _stack_adjustments(tags)

    habitat_factor = {
        "beach": 0.76,
        "rocks": 0.82,
        "jetty": 0.80,
        "bay_estuary_edge": 0.74,
    }.get(dominant_type, 0.9)

    activity = (50.0 + float(rule_context["score_delta"])) * habitat_factor
    activity += (dominant_scores["roaming_opportunity"] - 50) * 0.08
    activity += (dominant_scores["resident_opportunity"] - 50) * 0.05
    activity += (dominant_scores["trip_quality"] - 50) * 0.04

    if "harsh_midday_penalty" in tags:
        activity -= 4
    if "weather_recovery_window" in tags or "pelagic_settling_window" in tags:
        activity += 2
    if dominant_type in {"bay_estuary_edge", "jetty"} and "moderate_rain_edge_opportunity" in tags:
        activity += 2
    if "inferred_edge_flow" in tags:
        activity += 2 if dominant_type in {"rocks", "jetty", "bay_estuary_edge"} else 1
    normalized = environment_context.get("normalized", {})
    local_system_supportive = (
        float(normalized.get("water_flow_strength", normalized.get("movement_bonus", 0.5))) >= 0.58
        and float(normalized.get("wind_system_fit", 0.5)) >= 0.46
        and "recent_weather_shock" not in tags
    )
    if "major_moon_phase_bonus" in tags and (
        "sunrise_window" in tags or "sunset_window" in tags or "dawn_window" in tags or "dusk_window" in tags
    ):
        activity += 3 if local_system_supportive else 0
    sheltered_lift, score_mode_tags = _sheltered_estuary_support_lift(
        dominant_type=dominant_type,
        environment_context=environment_context,
        tags=tags,
    )
    ocean_estuary_pressure = _ocean_influenced_estuary_pressure(
        dominant_type=dominant_type,
        environment_context=environment_context,
    )
    ocean_pressure_tags = list(ocean_estuary_pressure.get("tags", []))
    ocean_pressure_severity = float(ocean_estuary_pressure.get("severity", 0.0) or 0.0)
    activity += sheltered_lift
    if ocean_pressure_severity >= 3.0:
        activity -= 12
    elif ocean_pressure_severity >= 2.0:
        activity -= 8
    elif ocean_pressure_severity >= 1.0:
        activity -= 5
    activity += positive_stack - negative_stack

    activity = _compress_extreme_score(_clamp(activity))

    resident = _resident_mode_score(dominant_type, dominant_scores, tags)
    roaming = _roaming_mode_score(dominant_type, dominant_scores, tags)
    presence = activity * 0.82
    if {"rising_tide_window", "falling_tide_window", "early_flood_bonus", "large_tide_range"} & tags:
        presence += 5
    if {"sunrise_window", "sunset_window", "dawn_window", "dusk_window"} & tags:
        presence += 4
    if {"cloud_cover_bonus", "stable_pressure_bonus", "pressure_rising", "pressure_falling"} & tags:
        presence += 2
    if "harsh_midday_penalty" in tags:
        presence -= 4
    if {"strong_wind_penalty", "gust_penalty", "heavy_rain_disruption", "strong_rain_penalty", "major_rain_shock", "big_wave_beach", "slack_tide_penalty"} & tags:
        presence -= 4
    if dominant_type in {"bay_estuary_edge", "jetty"} and "moderate_rain_edge_opportunity" in tags:
        presence += 3
    if "inferred_edge_flow" in tags:
        presence += 3 if dominant_type in {"rocks", "jetty", "bay_estuary_edge"} else 1
    elif "modest_inferred_edge_flow" in tags and dominant_type in {"rocks", "jetty", "bay_estuary_edge"}:
        presence += 1
    presence += sheltered_lift * 0.8
    if ocean_pressure_severity >= 3.0:
        presence -= 12
    elif ocean_pressure_severity >= 2.0:
        presence -= 8
    elif ocean_pressure_severity >= 1.0:
        presence -= 5
    presence += (resident - 50) * 0.10 + (roaming - 50) * 0.12
    presence += (positive_stack * 0.55) - (negative_stack * 0.75)
    presence = _compress_extreme_score(min(_clamp(presence), _clamp(activity + 8)))

    trip_quality = (activity * 0.62) + (presence * 0.18) + (resident * 0.08) + (roaming * 0.12)
    trip_quality += (positive_stack * 0.45) - (negative_stack * 1.10)
    if {"strong_wind_penalty", "gust_penalty", "heavy_rain_disruption", "strong_rain_penalty", "major_rain_shock", "big_wave_beach"} & tags:
        trip_quality -= 8
    if "offshore_push_away" in tags:
        presence -= 3
        roaming -= 4
    if "wind_presentation_penalty" in tags:
        trip_quality -= 5
    if "useful_wind_push" in tags:
        roaming += 3
        presence += 2
    elif "side_shore_ripple" in tags:
        roaming += 2
    if "inferred_edge_flow" in tags:
        resident += 2 if dominant_type in {"jetty", "bay_estuary_edge"} else 1
        roaming += 2 if dominant_type in {"rocks", "jetty", "bay_estuary_edge"} else 1
    elif "modest_inferred_edge_flow" in tags and dominant_type in {"rocks", "jetty", "bay_estuary_edge"}:
        resident += 1
        roaming += 1
    resident += sheltered_lift * 0.45
    roaming += sheltered_lift * 0.55
    if ocean_pressure_severity >= 2.0:
        roaming -= 4
    elif ocean_pressure_severity >= 1.0:
        roaming -= 2
    if dominant_type not in {"bay_estuary_edge", "jetty"} and "moderate_rain_edge_opportunity" in tags:
        trip_quality -= 2
    if "harsh_midday_penalty" in tags:
        trip_quality -= 5
    if {"weather_recovery_window", "pelagic_settling_window"} & tags:
        trip_quality += 4
    trip_quality += sheltered_lift * 0.35
    if ocean_pressure_severity >= 3.0:
        trip_quality -= 18
    elif ocean_pressure_severity >= 2.0:
        trip_quality -= 12
    elif ocean_pressure_severity >= 1.0:
        trip_quality -= 7
    inputs = environment_context["inputs_used"]
    temperature_c = inputs.get("temperature_c")
    wind_speed_knots = float(inputs.get("wind_speed_knots") or 0.0)
    wind_gust_knots = inputs.get("wind_gust_knots")
    rain_mm = float(inputs.get("rain_mm") or 0.0)
    recent_precipitation = float(inputs.get("recent_precipitation_sum_12h") or 0.0)
    wave_height_m = float(inputs.get("wave_height_m") or 0.0)
    swell_height_m = float(inputs.get("swell_height_m") or 0.0)
    is_daylight = inputs.get("is_daylight")
    exposure = float(environment_context.get("normalized", {}).get("directional_exposure", 0.0))
    weather_stress = float(environment_context.get("normalized", {}).get("weather_stress", 0.0))
    exposed_penalty = float(environment_context.get("normalized", {}).get("exposed_penalty", 0.0))
    exposed_type = dominant_type in {"beach", "rocks"}
    swell_trip_weight = 1.0 if exposed_type else 0.55 if dominant_type in {"bay_estuary_edge", "jetty"} else 0.75
    trip_sea_height = max(wave_height_m, swell_height_m * swell_trip_weight)

    if temperature_c is not None:
        temp = float(temperature_c)
        if temp <= 7 and wind_speed_knots >= 6.5:
            trip_quality -= 10
        elif temp <= 9 and wind_speed_knots >= 5.5:
            trip_quality -= 7
        elif temp <= 11 and wind_speed_knots >= 7.5:
            trip_quality -= 5

        gust_spread = max(0.0, float(wind_gust_knots or wind_speed_knots) - wind_speed_knots)
        wet_drag = 2.0 if rain_mm >= 0.4 else 0.0
        if recent_precipitation >= 2.0:
            wet_drag += 1.0
        wind_chill_proxy = temp - max(0.0, wind_speed_knots - 3.2) * 1.02 - gust_spread * 0.22 - wet_drag
        if exposed_type and exposure >= 0.45 and wind_chill_proxy <= 2:
            trip_quality -= 10
        elif exposed_type and exposure >= 0.45 and wind_chill_proxy <= 4:
            trip_quality -= 7
        elif wind_chill_proxy <= 5 and wind_speed_knots >= 5.5:
            trip_quality -= 4
        if exposed_type and is_daylight is False and temp <= 8:
            trip_quality -= 4

    if wind_gust_knots is not None and exposed_type and float(wind_gust_knots) >= 19:
        trip_quality -= 5
    if exposed_type and trip_sea_height >= 1.0:
        trip_quality -= 5
    elif exposed_type and trip_sea_height >= 0.6 and wind_gust_knots is not None and float(wind_gust_knots) >= 12:
        trip_quality -= 4
    if exposed_type and swell_height_m >= 2.0:
        trip_quality -= 8
    elif exposed_type and swell_height_m >= 1.2:
        trip_quality -= 4
    elif not exposed_type and swell_height_m >= 2.0:
        trip_quality -= 3
    if rain_mm >= 0.4 and temperature_c is not None and float(temperature_c) <= 10:
        trip_quality -= 4
    trip_quality -= 5.0 * weather_stress
    if exposed_type:
        trip_quality -= 7.0 * exposed_penalty
    if roaming < 40 and resident >= 60:
        trip_quality = min(trip_quality, activity + 2)

    if ocean_pressure_severity >= 3.0:
        activity = min(activity, 46)
        presence = min(presence, 42)
        trip_quality = min(trip_quality, 34)
    elif ocean_pressure_severity >= 2.0:
        activity = min(activity, 56)
        presence = min(presence, 54)
        trip_quality = min(trip_quality, 46)
    elif ocean_pressure_severity >= 1.0:
        activity = min(activity, 64)
        presence = min(presence, 62)
        trip_quality = min(trip_quality, 56)

    trip_quality = _compress_extreme_score(min(_clamp(trip_quality), _clamp(activity + 5)))
    activity = _calibrate_public_preview_score(activity)
    presence = _calibrate_public_preview_score(presence)
    trip_quality = _calibrate_public_preview_score(trip_quality)
    resident = _calibrate_public_preview_score(resident)
    roaming = _calibrate_public_preview_score(roaming)
    activity, presence, trip_quality, resident, roaming, guard_tags = _false_high_score_guards(
        activity=activity,
        presence=presence,
        trip_quality=trip_quality,
        resident=resident,
        roaming=roaming,
        tags=tags,
    )
    activity, presence, trip_quality, resident, roaming, system_guard_tags = _local_system_priority_guards(
        activity=activity,
        presence=presence,
        trip_quality=trip_quality,
        resident=resident,
        roaming=roaming,
        tags=tags,
        dominant_type=dominant_type,
        environment_context=environment_context,
    )
    guard_tags.extend(system_guard_tags)

    final_activity = _clamp(activity)
    final_presence = _clamp(presence)
    final_trip_quality = _clamp(trip_quality)
    inputs_used_context = environment_context.get("inputs_used", {}) or {}
    fish_outlook = _fish_outlook_score(final_activity, final_presence)
    comfort_score, comfort_factors = _comfort_score(
        inputs_used=inputs_used_context,
        normalized=normalized,
    )
    safety_flag, safety_factors, safety_risk_points = _safety_flag(
        inputs_used=inputs_used_context,
        dominant_type=dominant_type,
        tags=tags,
    )
    trip_reality = _trip_reality_score(comfort_score, safety_flag)

    return {
        "activity_score": final_activity,
        "presence_score": final_presence,
        "trip_quality_score": trip_reality,
        "fish_window_trip_score": final_trip_quality,
        "score_guard_tags": guard_tags,
        "score_mode_tags": score_mode_tags + ocean_pressure_tags,
        "fish_outlook_score": fish_outlook,
        "comfort_score": comfort_score,
        "comfort_factors": comfort_factors,
        "safety_flag": safety_flag,
        "safety_factors": safety_factors,
        "safety_risk_points": safety_risk_points,
    }


def _water_type_rule_delta_from_context(context: Mapping[str, Any], type_key: str) -> tuple[float, list[dict[str, Any]]]:
    rules: list[dict[str, Any]] = []
    inputs = context["inputs_used"]
    wave_height_m = float(inputs.get("wave_height_m") or inputs.get("swell_height_m") or 0.0)
    if type_key == "rocks" and 0.3 <= wave_height_m <= 1.0:
        _add_rule(rules, "strong_wave_rock", 4, "Some white water on rocks")
    if type_key == "beach" and wave_height_m < 0.3:
        _add_rule(rules, "calm_sea_beach", 3, "Calm beach conditions")
    if type_key == "beach" and wave_height_m > 1.0:
        _add_rule(rules, "big_wave_beach", -5, "Larger surf on beach")
    return sum(rule["score_delta"] for rule in rules), rules


def _environment_context(
    environment: EnvironmentInputs,
    signals: GlobalSignals,
    region_config: RegionConfig,
) -> dict[str, Any]:
    wind_factor = _clamp_unit((environment.wind_speed_knots - 6.0) / 18.0) * region_config.exposure_bias
    effective_swell_height = environment.swell_height_m if environment.swell_height_m is not None else environment.wave_height_m
    swell_factor = (
        0.0
        if effective_swell_height is None
        else _clamp_unit((effective_swell_height - 0.35) / 1.8) * region_config.exposure_bias
    )
    wind_factor = _clamp_unit(wind_factor)
    swell_factor = _clamp_unit(swell_factor)
    pressure_penalty = _clamp_unit(abs(environment.pressure_hpa - 1015.0) / 18.0)
    pressure_bonus = 1.0 - pressure_penalty
    wind_alignment = _directional_alignment(signals.open_water_bearing_deg, environment.wind_direction_deg)
    swell_alignment = _directional_alignment(signals.open_water_bearing_deg, environment.swell_direction_deg)
    wind_onshore = None
    wind_offshore = None
    wind_alongshore = None
    if signals.open_water_bearing_deg is not None and environment.wind_direction_deg is not None:
        delta_rad = math.radians(_angular_distance_signed(environment.wind_direction_deg, signals.open_water_bearing_deg))
        wind_onshore = max(environment.wind_speed_knots * math.cos(delta_rad), 0.0)
        wind_offshore = max(-environment.wind_speed_knots * math.cos(delta_rad), 0.0)
        wind_alongshore = abs(environment.wind_speed_knots * math.sin(delta_rad))

    tide_movement = {
        "low": 0.42,
        "rising": 0.80,
        "mid": 0.58,
        "high": 0.50,
        "falling": 0.66,
    }[environment.tide_phase]
    tide_movement_factor = 1.0
    if environment.tide_height_change_next_2h is not None and environment.tide_height_change_next_2h < 0.05:
        tide_movement_factor = 0.25
    elif environment.tide_height_change_next_3h is not None and environment.tide_height_change_next_3h < 0.08:
        tide_movement_factor = 0.45
    elif environment.tide_movement_rate_m_per_hour is not None and environment.tide_movement_rate_m_per_hour < 0.03:
        tide_movement_factor = 0.55
    tide_movement *= tide_movement_factor
    if environment.current_strength_proxy is not None:
        tide_movement = _clamp_unit((0.55 * tide_movement) + (0.45 * environment.current_strength_proxy))
    if environment.tide_current_confidence == "low" and environment.waterbody_class in {"river_mouth", "tidal_river"}:
        tide_movement = min(tide_movement, 0.68)
    structure_flow = _structure_flow_context(signals, tide_movement)
    wind_to_shore = _wind_to_shore_context(
        environment=environment,
        signals=signals,
        wind_onshore_knots=wind_onshore,
        wind_offshore_knots=wind_offshore,
        wind_alongshore_knots=wind_alongshore,
    )
    rule_context = _generic_coastal_rules(environment)
    raw_time_signal = _raw_time_signal_context(environment)
    local_geometry_rules = [*structure_flow["rules"], *wind_to_shore["rules"]]
    if local_geometry_rules:
        merged_rules = [*rule_context["rules"], *local_geometry_rules]
        rule_context = {
            **rule_context,
            "score_delta": round(sum(rule["score_delta"] for rule in merged_rules), 2),
            "rules": merged_rules,
            "reason_tags": [rule["id"] for rule in merged_rules],
        }
    time_movement = _clamp_unit(0.60 + (rule_context["score_delta"] / 40.0))
    wind_system_fit = float(wind_to_shore["score"])

    movement_bonus = _clamp_unit((0.72 * tide_movement) + (0.28 * time_movement))
    directional_exposure = _clamp_unit((0.55 * wind_alignment) + (0.45 * swell_alignment))
    water_body_exposure = _clamp_unit((0.65 * signals.exposure) + (0.35 * signals.outer_water_fraction))
    inner_bay_shelter = _clamp_unit((0.60 * signals.shelter) + (0.40 * signals.inner_water_fraction))
    exposure_gate = _clamp_unit((0.45 * directional_exposure) + (0.55 * water_body_exposure))
    weather_stress = _clamp_unit((0.58 * wind_factor) + (0.42 * swell_factor))
    exposed_penalty = _clamp_unit(weather_stress * exposure_gate)
    shelter_bonus = _clamp_unit((1.0 - (weather_stress * 0.58)) * inner_bay_shelter * region_config.shelter_bias)

    return {
        "region_slug": region_config.slug,
        "open_water_bearing_deg": signals.open_water_bearing_deg,
        "inputs_used": {
            "temperature_c": environment.temperature_c,
            "wind_speed_knots": environment.wind_speed_knots,
            "wind_direction_deg": environment.wind_direction_deg,
            "wind_gust_knots": environment.wind_gust_knots,
            "recent_wind_max_12h": environment.recent_wind_max_12h,
            "swell_height_m": environment.swell_height_m,
            "swell_direction_deg": environment.swell_direction_deg,
            "wave_height_m": environment.wave_height_m,
            "wave_height_delta_24h": environment.wave_height_delta_24h,
            "wave_data_source": environment.wave_data_source,
            "sea_surface_temperature_c": environment.sea_surface_temperature_c,
            "sea_surface_temperature_delta_24h": environment.sea_surface_temperature_delta_24h,
            "sea_surface_temperature_delta_72h": environment.sea_surface_temperature_delta_72h,
            "pressure_hpa": environment.pressure_hpa,
            "pressure_delta_3h": environment.pressure_delta_3h,
            "pressure_delta_6h": environment.pressure_delta_6h,
            "pressure_delta_24h": environment.pressure_delta_24h,
            "pressure_delta_48h": environment.pressure_delta_48h,
            "pressure_delta_72h": environment.pressure_delta_72h,
            "temperature_delta_24h": environment.temperature_delta_24h,
            "temperature_delta_48h": environment.temperature_delta_48h,
            "temperature_delta_72h": environment.temperature_delta_72h,
            "temperature_drop_from_recent_72h_peak": environment.temperature_drop_from_recent_72h_peak,
            "wind_direction_change_12h": environment.wind_direction_change_12h,
            "max_gust_24h": environment.max_gust_24h,
            "max_gust_72h": environment.max_gust_72h,
            "precipitation_mm": environment.precipitation_mm,
            "rain_mm": environment.rain_mm,
            "recent_precipitation_sum_12h": environment.recent_precipitation_sum_12h,
            "rainfall_24h": environment.rainfall_24h,
            "rainfall_48h": environment.rainfall_48h,
            "rainfall_72h": environment.rainfall_72h,
            "cloud_cover_pct": environment.cloud_cover_pct,
            "tide_phase": environment.tide_phase,
            "tide_stage": environment.tide_stage,
            "hours_to_high_tide": environment.hours_to_high_tide,
            "hours_to_low_tide": environment.hours_to_low_tide,
            "hours_since_low_tide": environment.hours_since_low_tide,
            "hours_since_high_tide": environment.hours_since_high_tide,
            "tide_range_m": environment.tide_range_m,
            "tide_height_m": environment.tide_height_m,
            "tide_height_change_next_2h": environment.tide_height_change_next_2h,
            "tide_height_change_next_3h": environment.tide_height_change_next_3h,
            "tide_height_change_prev_2h": environment.tide_height_change_prev_2h,
            "tide_movement_rate_m_per_hour": environment.tide_movement_rate_m_per_hour,
            "tide_source": environment.tide_source,
            "tide_current_confidence": environment.tide_current_confidence,
            "current_strength_proxy": environment.current_strength_proxy,
            "current_source_note": environment.current_source_note,
            "time_window": environment.time_window,
            "hour_of_day": environment.hour_of_day,
            "hours_from_sunrise": environment.hours_from_sunrise,
            "hours_from_sunset": environment.hours_from_sunset,
            "hours_from_solar_noon": environment.hours_from_solar_noon,
            "is_daylight": environment.is_daylight,
            "moon_phase_fraction": environment.moon_phase_fraction,
            "moon_phase_name": environment.moon_phase_name,
            "moon_illumination_pct": environment.moon_illumination_pct,
            "waterbody_class": environment.waterbody_class,
            "fish_profile": environment.fish_profile,
            "water_temperature_signal": environment.water_temperature_signal,
            "water_temperature_trend": environment.water_temperature_trend,
            "temperature_confidence": environment.temperature_confidence,
            "wind_onshore_knots": None if wind_onshore is None else round(wind_onshore, 2),
            "wind_offshore_knots": None if wind_offshore is None else round(wind_offshore, 2),
            "wind_alongshore_knots": None if wind_alongshore is None else round(wind_alongshore, 2),
            "wind_to_shore_category": wind_to_shore["category"],
            "structure_flow_category": structure_flow["category"],
        },
        "normalized": {
            "wind_factor": round(wind_factor, 2),
            "wind_alignment": round(wind_alignment, 2),
            "swell_factor": round(swell_factor, 2),
            "swell_alignment": round(swell_alignment, 2),
            "pressure_bonus": round(pressure_bonus, 2),
            "movement_bonus": round(movement_bonus, 2),
            "water_flow_strength": round(tide_movement, 2),
            "tide_movement_factor": round(tide_movement_factor, 2),
            "structure_edge_signal": round(structure_flow["structure_edge_signal"], 2),
            "structure_flow_interaction": round(structure_flow["interaction"], 2),
            "wind_system_fit": round(wind_system_fit, 2),
            "time_activity": round(time_movement, 2),
            "directional_exposure": round(directional_exposure, 2),
            "water_body_exposure": round(water_body_exposure, 2),
            "inner_bay_shelter": round(inner_bay_shelter, 2),
            "weather_stress": round(weather_stress, 2),
            "exposed_penalty": round(exposed_penalty, 2),
            "shelter_bonus": round(shelter_bonus, 2),
            "weather_shock": rule_context.get("weather_shock_score", 0.0),
            "raw_time_signal_score": raw_time_signal["score"],
        },
        "raw_time_signal": raw_time_signal,
        "generic_rules": rule_context,
    }


def _tide_phase_strengths(signals: GlobalSignals, region_config: RegionConfig) -> dict[str, dict[str, float]]:
    channel_hint = _clamp_unit((signals.coastline_complexity * 0.6) + (signals.shelter * 0.4))
    open_hint = _clamp_unit((signals.exposure * 0.65) + (signals.coastal_edge_signal * 0.35))
    movement_scale = region_config.tide_movement_bias
    return {
        "beach": {
            "low": 0.34 * movement_scale,
            "rising": 0.88 * movement_scale,
            "mid": 0.62 * movement_scale,
            "high": 0.44 * movement_scale,
            "falling": 0.70 * movement_scale,
        },
        "rocks": {
            "low": 0.42 * movement_scale,
            "rising": 0.74 * movement_scale,
            "mid": 0.60 * movement_scale,
            "high": 0.82 * movement_scale,
            "falling": 0.66 * movement_scale,
        },
        "jetty": {
            "low": (0.54 + 0.10 * channel_hint) * movement_scale,
            "rising": (0.74 + 0.10 * channel_hint) * movement_scale,
            "mid": 0.62 * movement_scale,
            "high": (0.60 + 0.08 * channel_hint) * movement_scale,
            "falling": (0.72 + 0.10 * channel_hint) * movement_scale,
        },
        "bay_estuary_edge": {
            "low": (0.58 + 0.10 * channel_hint) * movement_scale,
            "rising": (0.78 + 0.12 * channel_hint) * movement_scale,
            "mid": 0.60 * movement_scale,
            "high": (0.46 + 0.06 * open_hint) * movement_scale,
            "falling": (0.84 + 0.12 * channel_hint) * movement_scale,
        },
    }


def _apply_tide_adjustment(
    *,
    resident: float,
    roaming: float,
    trip: float,
    tide_phase: str,
    tide_lookup: Mapping[str, Mapping[str, float]],
    type_key: str,
) -> tuple[float, float, float]:
    tide_value = _clamp_unit(tide_lookup[type_key][tide_phase])
    centered = tide_value - 0.60
    return (
        resident + (12.0 * centered),
        roaming + (20.0 * centered),
        trip + (8.0 * centered),
    )


def _apply_environment(
    *,
    resident: float,
    roaming: float,
    trip: float,
    exposure_weight: float,
    shelter_weight: float,
    movement_weight: float,
    pressure_weight: float,
    context: Mapping[str, Any],
) -> tuple[float, float, float]:
    normalized = context["normalized"]
    exposed_penalty = normalized["exposed_penalty"]
    shelter_bonus = normalized["shelter_bonus"]
    movement_bonus = normalized["movement_bonus"]
    pressure_bonus = normalized["pressure_bonus"]
    generic_rule_delta = float(context.get("generic_rules", {}).get("score_delta", 0.0))

    trip_adjustment = (-28.0 * exposure_weight * exposed_penalty) + (8.0 * shelter_weight * shelter_bonus)
    roaming_adjustment = (
        (22.0 * movement_weight * movement_bonus)
        + (0.75 * movement_weight * generic_rule_delta)
        - (16.0 * exposure_weight * exposed_penalty)
    )
    resident_adjustment = (
        (8.0 * shelter_weight * shelter_bonus)
        + (5.5 * pressure_weight * pressure_bonus)
        + (0.30 * movement_weight * generic_rule_delta)
    )
    trip_adjustment += 0.25 * movement_weight * generic_rule_delta

    return (
        resident + resident_adjustment,
        roaming + roaming_adjustment,
        trip + trip_adjustment,
    )


def _score_nearby_water_types(
    signals: GlobalSignals,
    type_signals: TypeSignals,
    environment_context: Mapping[str, Any],
    region_config: RegionConfig,
) -> dict[str, dict]:
    tide_lookup = _tide_phase_strengths(signals, region_config)
    tide_phase = environment_context["inputs_used"]["tide_phase"]

    beach_resident, beach_roaming, beach_trip = _apply_tide_adjustment(
        resident=20 + (20 * type_signals.beach) + (10 * signals.coastline_complexity),
        roaming=30 + (45 * type_signals.beach),
        trip=20 + (20 * signals.accessibility) + (20 * signals.exposure) - (10 * signals.coastline_complexity),
        tide_phase=tide_phase,
        tide_lookup=tide_lookup,
        type_key="beach",
    )
    beach_resident, beach_roaming, beach_trip = _apply_environment(
        resident=beach_resident,
        roaming=beach_roaming,
        trip=beach_trip,
        exposure_weight=0.95,
        shelter_weight=0.10,
        movement_weight=0.95,
        pressure_weight=0.35,
        context=environment_context,
    )
    beach_type_delta, _beach_type_rules = _water_type_rule_delta_from_context(environment_context, "beach")
    beach_resident += beach_type_delta * 0.20
    beach_roaming += beach_type_delta * 0.65
    beach_trip += beach_type_delta * 0.45
    rocks_resident, rocks_roaming, rocks_trip = _apply_tide_adjustment(
        resident=25 + (35 * type_signals.rocks) + (15 * signals.coastline_complexity),
        roaming=20 + (30 * type_signals.rocks) + (15 * signals.exposure),
        trip=18 + (22 * signals.accessibility) + (10 * signals.coastline_complexity) - (12 * signals.exposure),
        tide_phase=tide_phase,
        tide_lookup=tide_lookup,
        type_key="rocks",
    )
    rocks_resident, rocks_roaming, rocks_trip = _apply_environment(
        resident=rocks_resident,
        roaming=rocks_roaming,
        trip=rocks_trip,
        exposure_weight=1.0,
        shelter_weight=0.05,
        movement_weight=0.70,
        pressure_weight=0.45,
        context=environment_context,
    )
    rocks_type_delta, _rocks_type_rules = _water_type_rule_delta_from_context(environment_context, "rocks")
    rocks_resident += rocks_type_delta * 0.25
    rocks_roaming += rocks_type_delta * 0.60
    rocks_trip += rocks_type_delta * 0.35
    jetty_resident, jetty_roaming, jetty_trip = _apply_tide_adjustment(
        resident=18 + (30 * type_signals.jetty) + (12 * signals.shelter),
        roaming=20 + (28 * type_signals.jetty) + (10 * signals.coastline_complexity),
        trip=24 + (24 * signals.accessibility) + (16 * signals.shelter),
        tide_phase=tide_phase,
        tide_lookup=tide_lookup,
        type_key="jetty",
    )
    jetty_resident, jetty_roaming, jetty_trip = _apply_environment(
        resident=jetty_resident,
        roaming=jetty_roaming,
        trip=jetty_trip,
        exposure_weight=0.45,
        shelter_weight=0.65,
        movement_weight=0.55,
        pressure_weight=0.40,
        context=environment_context,
    )
    jetty_type_delta, _jetty_type_rules = _water_type_rule_delta_from_context(environment_context, "jetty")
    jetty_resident += jetty_type_delta * 0.25
    jetty_roaming += jetty_type_delta * 0.55
    jetty_trip += jetty_type_delta * 0.30
    bay_resident, bay_roaming, bay_trip = _apply_tide_adjustment(
        resident=24 + (32 * type_signals.bay_estuary_edge) + (10 * signals.shelter),
        roaming=18 + (24 * type_signals.bay_estuary_edge) + (10 * signals.coastline_complexity),
        trip=28 + (24 * signals.accessibility) + (18 * signals.shelter),
        tide_phase=tide_phase,
        tide_lookup=tide_lookup,
        type_key="bay_estuary_edge",
    )
    bay_resident, bay_roaming, bay_trip = _apply_environment(
        resident=bay_resident,
        roaming=bay_roaming,
        trip=bay_trip,
        exposure_weight=0.30,
        shelter_weight=0.90,
        movement_weight=0.60,
        pressure_weight=0.45,
        context=environment_context,
    )
    bay_type_delta, _bay_type_rules = _water_type_rule_delta_from_context(environment_context, "bay_estuary_edge")
    bay_resident += bay_type_delta * 0.25
    bay_roaming += bay_type_delta * 0.55
    bay_trip += bay_type_delta * 0.30

    return {
        "beach": _build_water_type_card(
            name="Beach",
            resident=beach_resident,
            roaming=beach_roaming,
            trip=beach_trip,
            inference_strength=type_signals.beach,
            reasons=[
                "Open-water exposure suggests beach-style movement is plausible nearby.",
                "This is a broad shoreline signal, not a confirmed surf beach.",
                "Environmental inputs can move beach-style scores more sharply than sheltered types.",
                "Rising tide currently boosts beach-style movement more than slack high or low water.",
            ],
        ),
        "rocks": _build_water_type_card(
            name="Rocks",
            resident=rocks_resident,
            roaming=rocks_roaming,
            trip=rocks_trip,
            inference_strength=type_signals.rocks,
            reasons=[
                "Exposed shoreline plus coastline breaks can support rock-style opportunity.",
                "Exposure can improve activity but can also reduce comfort and safety.",
                "Rock-style opportunity currently holds better around mid to higher water than very low tide.",
            ],
        ),
        "jetty": _build_water_type_card(
            name="Jetty",
            resident=jetty_resident,
            roaming=jetty_roaming,
            trip=jetty_trip,
            inference_strength=type_signals.jetty,
            reasons=[
                "Sheltered edge water and coastline structure can support man-made access points nearby.",
                "This does not confirm an actual jetty or wharf at the searched point.",
                "Jetty-style opportunity currently responds best to moving water rather than slack tide.",
            ],
        ),
        "bay_estuary_edge": _build_water_type_card(
            name="Bay or estuary edge",
            resident=bay_resident,
            roaming=bay_roaming,
            trip=bay_trip,
            inference_strength=type_signals.bay_estuary_edge,
            reasons=[
                "Sheltered water and coastline complexity suggest bay or estuary-edge conditions nearby.",
                "This is the broadest inshore interpretation and stays intentionally cautious.",
                "Bay or estuary-edge opportunity currently improves most when tide movement is active.",
            ],
        ),
    }


def _base_response(lat: float, lon: float) -> dict:
    return {
        "contract_version": CONTRACT_VERSION,
        "input": {"latitude": lat, "longitude": lon},
    }


def _invalid_input_response(lat: float, lon: float) -> dict:
    response = _base_response(lat, lon)
    response.update(
        {
            "status": "invalid_input",
            "support": {
                "supported": False,
                "reason_code": INVALID_REASON_CODE,
                "message": "Latitude must be between -90 and 90, and longitude between -180 and 180.",
                "nearest_supported_water_km": None,
                "confidence": HIGH_CONFIDENCE,
            },
            "overall_recommendation": None,
            "nearby_water_types": {},
            "meta": {
                "mode": PREVIEW_MODE,
                "preview_confidence": HIGH_CONFIDENCE,
                "curated_spot_equivalent": False,
                "support_profile": {
                    "support_mode": SUPPORT_MODE_INVALID,
                    "distance_band_km": None,
                },
            },
        }
    )
    return response


def _unsupported_response(
    lat: float,
    lon: float,
    reason_code: str = UNSUPPORTED_REASON_CODE,
    message: str = "This forecast currently supports coastal and tidal fishing areas only.",
    nearest_supported_water_km: float | None = None,
) -> dict:
    response = _base_response(lat, lon)
    response.update(
        {
            "status": "unsupported",
            "support": {
                "supported": False,
                "reason_code": reason_code,
                "message": message,
                "nearest_supported_water_km": None if nearest_supported_water_km is None else round(nearest_supported_water_km, 1),
                "confidence": HIGH_CONFIDENCE,
            },
            "overall_recommendation": None,
            "nearby_water_types": {},
            "meta": {
                "mode": PREVIEW_MODE,
                "preview_confidence": PREVIEW_CONFIDENCE,
                "curated_spot_equivalent": False,
                "support_profile": {
                    "support_mode": SUPPORT_MODE_UNSUPPORTED,
                    "distance_band_km": None if nearest_supported_water_km is None else round(nearest_supported_water_km, 1),
                },
            },
        }
    )
    return response


def _is_extended_tidal_candidate(type_signals: TypeSignals) -> bool:
    sheltered_structured = max(type_signals.jetty, type_signals.bay_estuary_edge)
    sheltered_bay = type_signals.bay_estuary_edge
    return (sheltered_bay >= 0.45 and type_signals.beach <= 0.35) or (
        sheltered_structured >= 0.4 and type_signals.jetty >= 0.4 and type_signals.beach <= 0.3
    )


def _support_mode(on_water: bool, is_direct_support: bool, is_extended_support: bool) -> str:
    if on_water:
        return SUPPORT_MODE_ON_WATER
    if is_direct_support:
        return SUPPORT_MODE_NEAR_WATER
    if is_extended_support:
        return SUPPORT_MODE_TIDAL_CORRIDOR
    return SUPPORT_MODE_UNSUPPORTED


# Region-aware tiebreaker order for dominant water-type selection. When two
# water types score within DOMINANT_TIEBREAKER_TOLERANCE of each other on
# overall_recommendation, we prefer the type that better matches the searched
# region. This avoids dict-iteration order silently picking "beach" whenever
# beach / jetty / bay overall scores are essentially tied for a sheltered
# search like Southport or Sandy Bay.
DOMINANT_TIEBREAKER_TOLERANCE = 6
_REGION_DOMINANT_PREFERENCE = {
    "open_coast": ("beach", "rocks", "jetty", "bay_estuary_edge"),
    "surf_coast": ("beach", "rocks", "jetty", "bay_estuary_edge"),
    "sheltered_estuary": ("bay_estuary_edge", "jetty", "rocks", "beach"),
    "harbour_access": ("jetty", "bay_estuary_edge", "rocks", "beach"),
    "bay_coast": ("bay_estuary_edge", "jetty", "rocks", "beach"),
    "generic_coastal": ("bay_estuary_edge", "jetty", "rocks", "beach"),
}


def _pick_dominant_type(
    nearby_water_types: Mapping[str, Mapping[str, Any]],
    region_config: RegionConfig,
) -> str:
    preference = _REGION_DOMINANT_PREFERENCE.get(
        region_config.slug,
        _REGION_DOMINANT_PREFERENCE["generic_coastal"],
    )

    def overall(card: Mapping[str, Any]) -> int:
        scores = card.get("scores") or {}
        return int(scores.get("overall_recommendation") or 0)

    best_type, best_card = max(
        nearby_water_types.items(),
        key=lambda item: overall(item[1]),
    )
    best_score = overall(best_card)

    # Within tolerance, pick the highest-ranked region-preferred type that
    # also scores within tolerance of the leader. Strict winners (gap >
    # tolerance) keep their position regardless of region.
    in_tolerance = [
        type_key
        for type_key, card in nearby_water_types.items()
        if best_score - overall(card) <= DOMINANT_TIEBREAKER_TOLERANCE
    ]
    if len(in_tolerance) <= 1:
        return best_type

    pref_index = {type_key: idx for idx, type_key in enumerate(preference)}
    in_tolerance.sort(key=lambda type_key: pref_index.get(type_key, len(preference)))
    return in_tolerance[0]


def build_preview(
    lat: float,
    lon: float,
    environment: Mapping[str, Any] | None = None,
    region: str | None = None,
) -> dict:
    """Build a generic low-confidence preview for searched coordinates."""
    if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
        return _invalid_input_response(lat, lon)

    nearest_water_km = _find_nearest_water_km(lat, lon)
    on_water = nearest_water_km == 0.0
    if nearest_water_km is None:
        return _unsupported_response(lat, lon)

    nearest_supported_water_km = nearest_water_km or 0.0
    global_signals = _compute_global_signals(lat, lon, nearest_supported_water_km, on_water)
    waterbody_classification = _classify_waterbody(
        global_signals,
        nearest_water_km=nearest_supported_water_km,
        on_water=on_water,
        manual_region=region,
    )
    effective_region = region or "generic_coastal"
    region_config = get_region_config(effective_region)
    type_signals = _apply_region_bias(_infer_type_signals(global_signals), region_config)
    is_direct_support = nearest_supported_water_km <= DIRECT_NEARBY_WATER_KM
    is_extended_support = (
        not is_direct_support
        and nearest_supported_water_km <= EXTENDED_TIDAL_PREVIEW_KM
        and _is_extended_tidal_candidate(type_signals)
    )
    if not (is_direct_support or is_extended_support):
        return _unsupported_response(
            lat,
            lon,
            reason_code=DISTANCE_UNSUPPORTED_REASON_CODE,
            message="This preview currently supports searched points that are on coastal or tidal water, or very close to it.",
            nearest_supported_water_km=nearest_supported_water_km,
        )
    normalized_environment = _enrich_environment(
        _normalize_environment(environment),
        classification=waterbody_classification,
        effective_region_slug=region_config.slug,
    )
    environment_context = _environment_context(normalized_environment, global_signals, region_config)
    nearby_water_types = _score_nearby_water_types(global_signals, type_signals, environment_context, region_config)

    dominant_type = _pick_dominant_type(nearby_water_types, region_config)
    score_modes = _coastal_score_modes(
        cards=nearby_water_types,
        dominant_type=dominant_type,
        environment_context=environment_context,
    )
    overall_score = score_modes["activity_score"]
    score_breakdown = _local_adjustment_breakdown(
        score_modes=score_modes,
        environment_context=environment_context,
    )
    reason_tags = (
        environment_context["generic_rules"]["reason_tags"]
        + score_modes.get("score_guard_tags", [])
        + score_modes.get("score_mode_tags", [])
    )

    overall_label = (
        "Promising nearby options"
        if overall_score >= 65
        else "Usable nearby options"
        if overall_score >= 50
        else "Patchy nearby options"
    )
    support_message = (
        "Coordinate sits on supported coastal or tidal water."
        if on_water
        else "Coordinate is inland but close enough to supported coastal or tidal water for a nearby preview."
        if is_direct_support
        else "Coordinate is inland, but nearby sheltered tidal water still supports a cautious preview."
    )
    support_mode = _support_mode(on_water, is_direct_support, is_extended_support)

    response = _base_response(lat, lon)
    response.update(
        {
        "status": "ok",
        "support": {
            "supported": True,
            "reason_code": SUPPORTED_REASON_CODE if is_direct_support else EXTENDED_SUPPORTED_REASON_CODE,
            "message": support_message,
            "nearest_supported_water_km": round(nearest_supported_water_km, 1),
            "confidence": PREVIEW_CONFIDENCE,
        },
        "overall_recommendation": {
            "label": overall_label,
            "score": _clamp(overall_score),
            "activity_score": score_modes["activity_score"],
            "presence_score": score_modes["presence_score"],
            "trip_quality_score": score_modes["trip_quality_score"],
            "fish_outlook_score": score_modes["fish_outlook_score"],
            "comfort_score": score_modes["comfort_score"],
            "comfort_factors": score_modes["comfort_factors"],
            "safety_flag": score_modes["safety_flag"],
            "safety_factors": score_modes["safety_factors"],
            "confidence": PREVIEW_CONFIDENCE,
            "dominant_inferred_type": dominant_type,
            "model_rule_family": environment_context["generic_rules"]["family"],
            "reason_tags": reason_tags,
            "score_breakdown": score_breakdown,
            "reason_summary": [
                "Nearby water types are inferred from broad coastline shape around the searched coordinate.",
                "Time, tide, wind, swell, and pressure use generic coastal rules.",
                "Scores are preview-level guidance and should rank below curated local hot spots.",
            ],
        },
        "nearby_water_types": nearby_water_types,
        "meta": {
            "mode": PREVIEW_MODE,
            "preview_confidence": PREVIEW_CONFIDENCE,
            "curated_spot_equivalent": False,
            "region": {
                "slug": region_config.slug,
                "display_name": region_config.display_name,
                "manual_region_override": region,
            },
            "waterbody_classification": {
                "waterbody_class": waterbody_classification.waterbody_class,
                "classification_confidence": waterbody_classification.confidence,
                "classification_reasons": list(waterbody_classification.reasons),
                "manual_region_override": region,
                "recommended_region": waterbody_classification.recommended_region,
                "effective_region": region_config.slug,
            },
            "support_profile": {
                "support_mode": support_mode,
                "distance_band_km": round(nearest_supported_water_km, 1),
                "direct_nearby_limit_km": DIRECT_NEARBY_WATER_KM,
                "extended_tidal_limit_km": EXTENDED_TIDAL_PREVIEW_KM,
            },
            "search_confidence_score": round(global_signals.search_confidence_score, 2),
            "water_type_order": list(WATER_TYPE_KEYS),
            "coastline_metrics": {
                "inner_water_fraction": round(global_signals.inner_water_fraction, 2),
                "mid_water_fraction": round(global_signals.mid_water_fraction, 2),
                "outer_water_fraction": round(global_signals.outer_water_fraction, 2),
                "coastline_complexity": round(global_signals.coastline_complexity, 2),
                "open_water_bearing_deg": None
                if global_signals.open_water_bearing_deg is None
                else round(global_signals.open_water_bearing_deg, 1),
            },
            "inference_signals": {
                "coastal_edge_signal": round(global_signals.coastal_edge_signal, 2),
                "exposure": round(global_signals.exposure, 2),
                "shelter": round(global_signals.shelter, 2),
                "accessibility": round(global_signals.accessibility, 2),
                "type_strengths": {
                    "beach": round(type_signals.beach, 2),
                    "rocks": round(type_signals.rocks, 2),
                    "jetty": round(type_signals.jetty, 2),
                    "bay_estuary_edge": round(type_signals.bay_estuary_edge, 2),
                },
            },
            "environment": environment_context,
        },
        }
    )
    return response
