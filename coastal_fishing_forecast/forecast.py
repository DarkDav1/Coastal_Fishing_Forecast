"""Date-range forecast and replay path for searched coordinates."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
import math
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from coastal_fishing_forecast.conditions import fetch_open_meteo_conditions
from coastal_fishing_forecast.preview import WATER_TYPE_KEYS, build_preview
from coastal_fishing_forecast.tides import (
    TideEvent,
    infer_tide_events_from_sea_level,
    load_tide_events_file,
    parse_tide_events,
    resolve_tide_context,
    resolve_tide_phase,
)
from coastal_fishing_forecast.tidesatlas import fetch_tidesatlas_events


FORECAST_CONTRACT_VERSION = "2026-04-27.timeseries.v1"
DEFAULT_TIMEZONE = ZoneInfo("Australia/Hobart")
WEATHER_TREND_LOOKBACK_DAYS = 3
TIDE_INFERENCE_LOOKAHEAD_DAYS = 1
PROTECTED_WAVE_ESTIMATE_REGIONS = {"sheltered_estuary", "bay_coast", "harbour_access", "river_mouth", "tidal_river"}


@dataclass(frozen=True)
class TimeWindow:
    key: str
    start_hour: int
    end_hour: int
    representative_hour: int


TIME_WINDOWS: dict[str, TimeWindow] = {
    "morning": TimeWindow("morning", 5, 10, 7),
    "day": TimeWindow("day", 11, 15, 13),
    "dusk": TimeWindow("dusk", 16, 20, 18),
}


def _hourly_time_window(hour: int) -> str:
    if 3 <= hour < 5:
        return "pre_dawn"
    if 5 <= hour <= 9:
        return "dawn"
    if 10 <= hour <= 15:
        return "day"
    if 16 <= hour <= 20:
        return "dusk"
    return "night"


def _parse_date(value: str | date) -> date:
    return value if isinstance(value, date) else date.fromisoformat(value)


def _parse_hour(value: str) -> int:
    return int(value[11:13])


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=DEFAULT_TIMEZONE)
    return parsed


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _circular_mean(values: list[float]) -> float | None:
    if not values:
        return None
    x_total = sum(math.cos(math.radians(value)) for value in values)
    y_total = sum(math.sin(math.radians(value)) for value in values)
    return (math.degrees(math.atan2(y_total, x_total)) + 360.0) % 360.0


def _window_numeric_values(hourly: Mapping[str, list[Any]], key: str, indices: list[int]) -> list[float]:
    values: list[float] = []
    series = hourly.get(key, [])
    for idx in indices:
        if idx >= len(series):
            continue
        value = series[idx]
        if value is None:
            continue
        try:
            values.append(float(value))
        except (TypeError, ValueError):
            continue
    return values


def _values_for_window(hourly: Mapping[str, list[Any]], key: str, day: date, window: TimeWindow) -> list[Any]:
    values: list[Any] = []
    day_prefix = day.isoformat()
    for idx, timestamp in enumerate(hourly["time"]):
        if not str(timestamp).startswith(day_prefix):
            continue
        hour = _parse_hour(str(timestamp))
        if window.start_hour <= hour <= window.end_hour:
            values.append((idx, timestamp))
    return values


def _daily_value(daily: Mapping[str, list[Any]], day: date, key: str) -> Any:
    dates = daily.get("time", [])
    values = daily.get(key, [])
    day_string = day.isoformat()
    for idx, value in enumerate(dates):
        if str(value) == day_string and idx < len(values):
            return values[idx]
    return None


def _solar_context(day: date, representative_time: datetime, weather_daily: Mapping[str, list[Any]]) -> dict[str, Any]:
    sunrise_raw = _daily_value(weather_daily, day, "sunrise")
    sunset_raw = _daily_value(weather_daily, day, "sunset")
    if sunrise_raw is None or sunset_raw is None:
        sunrise = datetime.combine(day, time(6, 15), tzinfo=DEFAULT_TIMEZONE)
        sunset = datetime.combine(day, time(18, 0), tzinfo=DEFAULT_TIMEZONE)
    else:
        sunrise = _parse_datetime(str(sunrise_raw))
        sunset = _parse_datetime(str(sunset_raw))

    solar_noon = sunrise + ((sunset - sunrise) / 2)
    return {
        "sunrise": sunrise.isoformat(),
        "sunset": sunset.isoformat(),
        "hours_from_sunrise": round((representative_time - sunrise).total_seconds() / 3600.0, 3),
        "hours_from_sunset": round((representative_time - sunset).total_seconds() / 3600.0, 3),
        "hours_from_solar_noon": round((representative_time - solar_noon).total_seconds() / 3600.0, 3),
        "is_daylight": sunrise <= representative_time <= sunset,
    }


def _pressure_delta_3h(
    weather_hourly: Mapping[str, list[Any]],
    representative_time: datetime,
    current_pressure: float,
) -> float | None:
    times = weather_hourly.get("time", [])
    pressures = weather_hourly.get("surface_pressure", [])
    best_delta: float | None = None
    best_age: float | None = None
    for idx, raw_time in enumerate(times):
        if idx >= len(pressures):
            continue
        pressure = _safe_float(pressures[idx])
        if pressure is None:
            continue
        candidate_time = _parse_datetime(str(raw_time))
        age_hours = (representative_time - candidate_time).total_seconds() / 3600.0
        if age_hours < 2.5:
            continue
        if best_age is None or age_hours < best_age:
            best_age = age_hours
            best_delta = current_pressure - pressure
    return None if best_delta is None else round(best_delta, 2)


def _series_delta(
    hourly: Mapping[str, list[Any]],
    key: str,
    representative_time: datetime,
    current_value: float | None,
    *,
    min_age_hours: float,
) -> float | None:
    if current_value is None:
        return None
    times = hourly.get("time", [])
    values = hourly.get(key, [])
    best_value: float | None = None
    best_age: float | None = None
    for idx, raw_time in enumerate(times):
        if idx >= len(values):
            continue
        value = _safe_float(values[idx])
        if value is None:
            continue
        candidate_time = _parse_datetime(str(raw_time))
        age_hours = (representative_time - candidate_time).total_seconds() / 3600.0
        if age_hours < min_age_hours:
            continue
        if best_age is None or age_hours < best_age:
            best_age = age_hours
            best_value = value
    return None if best_value is None else round(current_value - best_value, 3)


def _direction_delta(
    hourly: Mapping[str, list[Any]],
    key: str,
    representative_time: datetime,
    current_direction: float | None,
    *,
    min_age_hours: float,
) -> float | None:
    if current_direction is None:
        return None
    times = hourly.get("time", [])
    values = hourly.get(key, [])
    best_direction: float | None = None
    best_age: float | None = None
    for idx, raw_time in enumerate(times):
        if idx >= len(values):
            continue
        value = _safe_float(values[idx])
        if value is None:
            continue
        candidate_time = _parse_datetime(str(raw_time))
        age_hours = (representative_time - candidate_time).total_seconds() / 3600.0
        if age_hours < min_age_hours:
            continue
        if best_age is None or age_hours < best_age:
            best_age = age_hours
            best_direction = value
    if best_direction is None:
        return None
    difference = abs(current_direction - best_direction) % 360.0
    return round(min(difference, 360.0 - difference), 1)


def _recent_numeric_values(hourly: Mapping[str, list[Any]], key: str, representative_time: datetime, max_hours: float) -> list[float]:
    values: list[float] = []
    times = hourly.get("time", [])
    series = hourly.get(key, [])
    for idx, raw_time in enumerate(times):
        if idx >= len(series):
            continue
        value = _safe_float(series[idx])
        if value is None:
            continue
        candidate_time = _parse_datetime(str(raw_time))
        age_hours = (representative_time - candidate_time).total_seconds() / 3600.0
        if 0 <= age_hours <= max_hours:
            values.append(value)
    return values


def _recent_numeric_values_between(
    hourly: Mapping[str, list[Any]],
    key: str,
    representative_time: datetime,
    min_hours: float,
    max_hours: float,
) -> list[float]:
    values: list[float] = []
    times = hourly.get("time", [])
    series = hourly.get(key, [])
    for idx, raw_time in enumerate(times):
        if idx >= len(series):
            continue
        value = _safe_float(series[idx])
        if value is None:
            continue
        candidate_time = _parse_datetime(str(raw_time))
        age_hours = (representative_time - candidate_time).total_seconds() / 3600.0
        if min_hours <= age_hours <= max_hours:
            values.append(value)
    return values


def _moon_phase_info(day: date) -> dict[str, Any]:
    known_new_moon = date(2000, 1, 6)
    synodic_month = 29.53058867
    days = (day - known_new_moon).days
    fraction = (days % synodic_month) / synodic_month
    illumination = 0.5 * (1 - math.cos(2 * math.pi * fraction))
    if fraction < 0.03 or fraction >= 0.97:
        name = "new_moon"
    elif fraction < 0.22:
        name = "waxing_crescent"
    elif fraction < 0.28:
        name = "first_quarter"
    elif fraction < 0.47:
        name = "waxing_gibbous"
    elif fraction < 0.53:
        name = "full_moon"
    elif fraction < 0.72:
        name = "waning_gibbous"
    elif fraction < 0.78:
        name = "last_quarter"
    else:
        name = "waning_crescent"
    return {
        "moon_phase_fraction": round(fraction, 4),
        "moon_phase_name": name,
        "moon_illumination_pct": round(illumination * 100, 1),
    }


def _allows_protected_estuary_wave_estimate(region: str | None) -> bool:
    return (region or "").lower() in PROTECTED_WAVE_ESTIMATE_REGIONS


def _condition_fetch_end_date(end: date, condition_source: str) -> date:
    lookahead = date.fromordinal(end.toordinal() + TIDE_INFERENCE_LOOKAHEAD_DAYS)
    today = datetime.now(DEFAULT_TIMEZONE).date()
    if condition_source in {"auto", "archive"} and end < today <= lookahead:
        return end
    return lookahead


def _window_environment(
    *,
    day: date,
    window: TimeWindow,
    weather_hourly: Mapping[str, list[Any]],
    weather_daily: Mapping[str, list[Any]],
    marine_hourly: Mapping[str, list[Any]],
    lon: float,
    tide_events: list[TideEvent],
    tide_event_source_label: str | None = None,
    region: str | None = None,
) -> dict[str, Any]:
    weather_rows = _values_for_window(weather_hourly, "weather", day, window)
    marine_rows = _values_for_window(marine_hourly, "marine", day, window)
    weather_indices = [row[0] for row in weather_rows]
    marine_indices = [row[0] for row in marine_rows]

    representative_time = datetime.combine(day, time(window.representative_hour, 0), tzinfo=DEFAULT_TIMEZONE)
    if weather_rows:
        representative_time = _parse_datetime(str(weather_rows[min(len(weather_rows) // 2, len(weather_rows) - 1)][1]))
    tide_phase, tide_source = resolve_tide_phase(representative_time, lon, tide_events)
    tide_context = resolve_tide_context(representative_time, lon, tide_events)
    display_tide_source = tide_event_source_label or tide_source

    if window.key == "morning":
        engine_time_window = "dawn"
    elif window.key.startswith("hour_"):
        engine_time_window = _hourly_time_window(window.representative_hour)
    else:
        engine_time_window = window.key
    pressure_hpa = round(_mean(_window_numeric_values(weather_hourly, "surface_pressure", weather_indices)) or 1015.0, 1)
    wave_height = _mean(_window_numeric_values(marine_hourly, "wave_height", marine_indices))
    swell_height = _mean(_window_numeric_values(marine_hourly, "swell_wave_height", marine_indices))
    rain_values = _window_numeric_values(weather_hourly, "rain", weather_indices)
    precipitation_values = _window_numeric_values(weather_hourly, "precipitation", weather_indices)
    temperature_values = _window_numeric_values(weather_hourly, "temperature_2m", weather_indices)
    temperature_c = None if not temperature_values else round(_mean(temperature_values) or 0.0, 1)
    wind_direction = _circular_mean(_window_numeric_values(weather_hourly, "wind_direction_10m", weather_indices))
    swell_direction = _circular_mean(_window_numeric_values(marine_hourly, "swell_wave_direction", marine_indices))
    recent_gusts_24h = _recent_numeric_values(weather_hourly, "wind_gusts_10m", representative_time, 24)
    recent_gusts_72h = _recent_numeric_values(weather_hourly, "wind_gusts_10m", representative_time, 72)
    rainfall_24h = round(sum(_recent_numeric_values(weather_hourly, "rain", representative_time, 24)), 2)
    rainfall_48h = round(sum(_recent_numeric_values(weather_hourly, "rain", representative_time, 48)), 2)
    rainfall_72h = round(sum(_recent_numeric_values(weather_hourly, "rain", representative_time, 72)), 2)
    if rainfall_24h == 0:
        rainfall_24h = round(sum(_recent_numeric_values(weather_hourly, "precipitation", representative_time, 24)), 2)
    if rainfall_48h == 0:
        rainfall_48h = round(sum(_recent_numeric_values(weather_hourly, "precipitation", representative_time, 48)), 2)
    if rainfall_72h == 0:
        rainfall_72h = round(sum(_recent_numeric_values(weather_hourly, "precipitation", representative_time, 72)), 2)
    previous_72h_temperatures = _recent_numeric_values_between(
        weather_hourly,
        "temperature_2m",
        representative_time,
        6,
        72,
    )
    mean_wind_speed = round(_mean(_window_numeric_values(weather_hourly, "wind_speed_10m", weather_indices)) or 12.0, 1)
    sea_level_values = _window_numeric_values(marine_hourly, "sea_level_height_msl", marine_indices)
    sea_temp_values = _window_numeric_values(marine_hourly, "sea_surface_temperature", marine_indices)
    sea_surface_temperature = None if not sea_temp_values else round(_mean(sea_temp_values) or 0.0, 1)
    wave_data_source = "openmeteo_marine"
    if wave_height is None and swell_height is None and sea_level_values and _allows_protected_estuary_wave_estimate(region):
        wave_data_source = "protected_estuary_estimate"
        protected_estuary_wave = round(max(0.08, min(0.35, 0.06 + (mean_wind_speed * 0.025))), 2)
        wave_height = protected_estuary_wave
        swell_height = protected_estuary_wave
    elif wave_height is None and swell_height is None:
        wave_data_source = "unavailable"

    environment = {
        "temperature_c": temperature_c,
        "wind_speed_knots": mean_wind_speed,
        "wind_direction_deg": None,
        "wind_gust_knots": None
        if not _window_numeric_values(weather_hourly, "wind_gusts_10m", weather_indices)
        else round(_mean(_window_numeric_values(weather_hourly, "wind_gusts_10m", weather_indices)) or 0.0, 1),
        "recent_wind_max_12h": None
        if not _recent_numeric_values(weather_hourly, "wind_speed_10m", representative_time, 12)
        else round(max(_recent_numeric_values(weather_hourly, "wind_speed_10m", representative_time, 12)), 1),
        "swell_height_m": None if swell_height is None else round(swell_height, 2),
        "swell_direction_deg": None,
        "wave_height_m": None if wave_height is None else round(wave_height, 2),
        "wave_height_delta_24h": _series_delta(marine_hourly, "wave_height", representative_time, wave_height, min_age_hours=24),
        "wave_data_source": wave_data_source,
        "sea_surface_temperature_c": sea_surface_temperature,
        "sea_surface_temperature_delta_24h": _series_delta(
            marine_hourly,
            "sea_surface_temperature",
            representative_time,
            sea_surface_temperature,
            min_age_hours=24,
        ),
        "sea_surface_temperature_delta_72h": _series_delta(
            marine_hourly,
            "sea_surface_temperature",
            representative_time,
            sea_surface_temperature,
            min_age_hours=72,
        ),
        "pressure_hpa": pressure_hpa,
        "pressure_delta_3h": _pressure_delta_3h(weather_hourly, representative_time, pressure_hpa),
        "pressure_delta_6h": _series_delta(weather_hourly, "surface_pressure", representative_time, pressure_hpa, min_age_hours=6),
        "pressure_delta_24h": _series_delta(weather_hourly, "surface_pressure", representative_time, pressure_hpa, min_age_hours=24),
        "pressure_delta_48h": _series_delta(weather_hourly, "surface_pressure", representative_time, pressure_hpa, min_age_hours=48),
        "pressure_delta_72h": _series_delta(weather_hourly, "surface_pressure", representative_time, pressure_hpa, min_age_hours=72),
        "temperature_delta_24h": _series_delta(weather_hourly, "temperature_2m", representative_time, temperature_c, min_age_hours=24),
        "temperature_delta_48h": _series_delta(weather_hourly, "temperature_2m", representative_time, temperature_c, min_age_hours=48),
        "temperature_delta_72h": _series_delta(weather_hourly, "temperature_2m", representative_time, temperature_c, min_age_hours=72),
        "temperature_drop_from_recent_72h_peak": None
        if temperature_c is None or not previous_72h_temperatures
        else round(temperature_c - max(previous_72h_temperatures), 2),
        "wind_direction_change_12h": _direction_delta(
            weather_hourly,
            "wind_direction_10m",
            representative_time,
            wind_direction,
            min_age_hours=12,
        ),
        "max_gust_24h": None if not recent_gusts_24h else round(max(recent_gusts_24h), 1),
        "max_gust_72h": None if not recent_gusts_72h else round(max(recent_gusts_72h), 1),
        "rainfall_24h": rainfall_24h,
        "rainfall_48h": rainfall_48h,
        "rainfall_72h": rainfall_72h,
        "precipitation_mm": round(_mean(precipitation_values) or 0.0, 2),
        "rain_mm": round(_mean(rain_values) or 0.0, 2),
        "recent_precipitation_sum_12h": round(
            sum(_recent_numeric_values(weather_hourly, "precipitation", representative_time, 12)),
            2,
        ),
        "cloud_cover_pct": round(_mean(_window_numeric_values(weather_hourly, "cloud_cover", weather_indices)) or 0.0, 1),
        "tide_phase": tide_phase,
        "tide_stage": tide_context.stage,
        "hours_to_high_tide": tide_context.hours_to_high_tide,
        "hours_to_low_tide": tide_context.hours_to_low_tide,
        "hours_since_low_tide": tide_context.hours_since_low_tide,
        "hours_since_high_tide": tide_context.hours_since_high_tide,
        "tide_range_m": tide_context.tide_range_m,
        "tide_height_m": None
        if not _window_numeric_values(marine_hourly, "sea_level_height_msl", marine_indices)
        else round(_mean(_window_numeric_values(marine_hourly, "sea_level_height_msl", marine_indices)) or 0.0, 3),
        "tide_height_change_next_2h": tide_context.tide_height_change_next_2h,
        "tide_height_change_next_3h": tide_context.tide_height_change_next_3h,
        "tide_height_change_prev_2h": tide_context.tide_height_change_prev_2h,
        "tide_movement_rate_m_per_hour": tide_context.tide_movement_rate_m_per_hour,
        "tide_source": display_tide_source,
        "time_window": engine_time_window,
        "hour_of_day": representative_time.hour + (representative_time.minute / 60.0),
        "rule_family": "generic_coastal_v1",
    }
    environment.update(_solar_context(day, representative_time, weather_daily))
    environment.update(_moon_phase_info(day))

    if wind_direction is not None:
        environment["wind_direction_deg"] = round(wind_direction)
    if swell_direction is not None:
        environment["swell_direction_deg"] = round(swell_direction)

    return {
        "environment": environment,
        "tide_source": display_tide_source,
        "representative_time": representative_time.isoformat(),
    }


def _date_range(start_date: date, end_date: date) -> list[date]:
    days = (end_date - start_date).days
    if days < 0:
        raise ValueError("end_date must be on or after start_date")
    return [date.fromordinal(start_date.toordinal() + offset) for offset in range(days + 1)]


def _open_meteo_model_tide_events(conditions: Mapping[str, Any]) -> list[TideEvent]:
    marine_hourly = conditions.get("marine_hourly", {})
    if "sea_level_height_msl" not in marine_hourly:
        return []
    return infer_tide_events_from_sea_level(
        marine_hourly.get("time", []),
        marine_hourly.get("sea_level_height_msl", []),
        default_timezone=DEFAULT_TIMEZONE,
    )


def _summarize_windows(windows: list[dict[str, Any]]) -> dict[str, Any]:
    supported = [window for window in windows if window["preview"]["status"] == "ok"]
    if not supported:
        return {"best_windows": [], "average_score": None}

    def summary_score(window: dict[str, Any]) -> float:
        recommendation = window["preview"]["overall_recommendation"]
        activity = recommendation.get("activity_score")
        presence = recommendation.get("presence_score")
        trip_quality = recommendation.get("trip_quality_score")
        if activity is None or presence is None or trip_quality is None:
            return float(recommendation["score"])
        return (float(activity) * 0.40) + (float(presence) * 0.35) + (float(trip_quality) * 0.25)

    return {
        "average_score": round(
            sum(summary_score(window) for window in supported) / len(supported),
            1,
        ),
        "best_windows": [
            {
                "date": window["date"],
                "time_window": window["time_window"],
                "score": window["preview"]["overall_recommendation"]["score"],
                "activity_score": window["preview"]["overall_recommendation"].get("activity_score"),
                "presence_score": window["preview"]["overall_recommendation"].get("presence_score"),
                "trip_quality_score": window["preview"]["overall_recommendation"].get("trip_quality_score"),
                "label": window["preview"]["overall_recommendation"]["label"],
                "dominant_inferred_type": window["preview"]["overall_recommendation"]["dominant_inferred_type"],
            }
            for window in sorted(supported, key=summary_score, reverse=True)[:5]
        ],
    }


def _build_hourly_activity(
    *,
    lat: float,
    lon: float,
    days: list[date],
    region: str | None,
    condition_region: str | None = None,
    weather_hourly: Mapping[str, list[Any]],
    weather_daily: Mapping[str, list[Any]],
    marine_hourly: Mapping[str, list[Any]],
    tide_events: list[TideEvent],
    tide_event_source_label: str | None,
) -> list[dict[str, Any]]:
    hourly_activity: list[dict[str, Any]] = []
    for day in days:
        for hour in range(24):
            window = TimeWindow(f"hour_{hour:02d}", hour, hour, hour)
            window_context = _window_environment(
                day=day,
                window=window,
                weather_hourly=weather_hourly,
                weather_daily=weather_daily,
                marine_hourly=marine_hourly,
                lon=lon,
                tide_events=tide_events,
                tide_event_source_label=tide_event_source_label,
                region=condition_region or region,
            )
            preview = build_preview(lat, lon, environment=window_context["environment"], region=region)
            recommendation = preview.get("overall_recommendation") or {}
            environment = window_context["environment"]
            inputs_used = preview.get("meta", {}).get("environment", {}).get("inputs_used", {})

            def environment_or_input(key: str) -> Any:
                value = environment.get(key)
                return value if value is not None else inputs_used.get(key)

            hourly_activity.append(
                {
                    "date": day.isoformat(),
                    "hour": hour,
                    "time": datetime.combine(day, time(hour, 0), tzinfo=DEFAULT_TIMEZONE).isoformat(),
                    "score": recommendation.get("score"),
                    "activity_score": recommendation.get("activity_score"),
                    "presence_score": recommendation.get("presence_score"),
                    "trip_quality_score": recommendation.get("trip_quality_score"),
                    "fish_outlook_score": recommendation.get("fish_outlook_score"),
                    "comfort_score": recommendation.get("comfort_score"),
                    "safety_flag": recommendation.get("safety_flag"),
                    "label": recommendation.get("label"),
                    "dominant_inferred_type": recommendation.get("dominant_inferred_type"),
                    "time_window": window_context["environment"]["time_window"],
                    "tide_phase": window_context["environment"]["tide_phase"],
                    "tide_source": window_context["tide_source"],
                    "tide_stage": environment_or_input("tide_stage"),
                    "tide_range_m": environment_or_input("tide_range_m"),
                    "tide_height_m": environment_or_input("tide_height_m"),
                    "tide_movement_rate_m_per_hour": environment_or_input("tide_movement_rate_m_per_hour"),
                    "tide_current_confidence": environment_or_input("tide_current_confidence"),
                    "current_strength_proxy": environment_or_input("current_strength_proxy"),
                    "current_source_note": environment_or_input("current_source_note"),
                    "wind_speed_knots": environment.get("wind_speed_knots"),
                    "wind_direction_deg": environment.get("wind_direction_deg"),
                    "wind_gust_knots": environment_or_input("wind_gust_knots"),
                    "wave_height_m": environment_or_input("wave_height_m"),
                    "swell_height_m": environment.get("swell_height_m"),
                    "sea_surface_temperature_c": environment_or_input("sea_surface_temperature_c"),
                    "sea_surface_temperature_delta_24h": environment_or_input("sea_surface_temperature_delta_24h"),
                    "water_temperature_signal": environment_or_input("water_temperature_signal"),
                    "water_temperature_trend": environment_or_input("water_temperature_trend"),
                    "temperature_confidence": environment_or_input("temperature_confidence"),
                    "rain_mm": environment_or_input("rain_mm"),
                    "precipitation_mm": environment_or_input("precipitation_mm"),
                    "temperature_c": environment_or_input("temperature_c"),
                    "pressure_hpa": environment.get("pressure_hpa"),
                    "waterbody_class": environment_or_input("waterbody_class"),
                    "fish_profile": environment_or_input("fish_profile"),
                    "rule_tags": recommendation.get("reason_tags", []),
                }
            )
    return hourly_activity


def _best_hour_for_window(hourly_activity: list[Mapping[str, Any]], day: date, window: TimeWindow) -> int:
    day_string = day.isoformat()
    candidates = [
        point
        for point in hourly_activity
        if point.get("date") == day_string
        and window.start_hour <= int(point.get("hour", -1)) <= window.end_hour
        and point.get("score") is not None
    ]
    if not candidates:
        return window.representative_hour
    best = max(candidates, key=lambda point: int(point["score"]))
    return int(best["hour"])


def build_range_forecast(
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
    cache_enabled: bool = True,
    cache_dir: str | Path | None = None,
) -> dict[str, Any]:
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    condition_fetch_start = date.fromordinal(start.toordinal() - WEATHER_TREND_LOOKBACK_DAYS)
    condition_fetch_end = _condition_fetch_end_date(end, condition_source)
    selected_windows = tuple(TIME_WINDOWS[key] for key in windows)
    parsed_tide_events = load_tide_events_file(tide_events_file) if tide_events_file else parse_tide_events(tide_events)
    tide_source_used = "tide_events_file" if tide_events_file else "tide_events" if parsed_tide_events else "astronomical_approximation"
    tide_provider_meta: dict[str, Any] | None = None
    use_open_meteo_tide = tide_source in {"auto", "openmeteo_model"}
    needs_conditions_for_tide = use_open_meteo_tide and not parsed_tide_events

    conditions = condition_data or fetch_open_meteo_conditions(
        lat=lat,
        lon=lon,
        start_date=condition_fetch_start,
        end_date=condition_fetch_end,
        source=condition_source,
        cache_enabled=cache_enabled,
        cache_dir=cache_dir,
    )

    if not parsed_tide_events and tide_source in {"tidesatlas"}:
        try:
            parsed_tide_events, tide_provider_meta = fetch_tidesatlas_events(
                lat=lat,
                lon=lon,
                start_date=start,
                end_date=end,
                api_key=tidesatlas_api_key,
                cache_enabled=cache_enabled,
                cache_dir=cache_dir,
            )
            tide_source_used = "tidesatlas" if parsed_tide_events else "astronomical_approximation"
        except ValueError:
            if tide_source == "tidesatlas":
                raise
        except Exception:
            if tide_source == "tidesatlas":
                raise

    if not parsed_tide_events and needs_conditions_for_tide:
        parsed_tide_events = _open_meteo_model_tide_events(conditions)
        if parsed_tide_events:
            tide_source_used = "openmeteo_model"
            tide_provider_meta = {
                "provider": "open_meteo",
                "model": "sea_level_height_msl",
                "station_distance_km": None,
                "confidence_note": "Model sea-level tide proxy, not a local tide station.",
            }

    if tide_source == "approximation" and not tide_events_file and not tide_events:
        parsed_tide_events = []
        tide_source_used = "astronomical_approximation"

    window_tide_source_label = "openmeteo_model" if tide_source_used == "openmeteo_model" else None
    forecast_days = _date_range(start, end)
    condition_region = region
    if condition_region is None:
        try:
            classification_probe = build_preview(lat, lon)
            condition_region = (
                classification_probe.get("meta", {})
                .get("waterbody_classification", {})
                .get("recommended_region")
            )
        except (KeyError, TypeError, ValueError):
            condition_region = None
    hourly_activity = _build_hourly_activity(
        lat=lat,
        lon=lon,
        days=forecast_days,
        region=region,
        condition_region=condition_region,
        weather_hourly=conditions["weather_hourly"],
        weather_daily=conditions.get("weather_daily", {}),
        marine_hourly=conditions["marine_hourly"],
        tide_events=parsed_tide_events,
        tide_event_source_label=window_tide_source_label,
    )

    forecast_windows: list[dict[str, Any]] = []
    for day in forecast_days:
        for window in selected_windows:
            best_window_hour = _best_hour_for_window(hourly_activity, day, window)
            scoring_window = TimeWindow(window.key, best_window_hour, best_window_hour, best_window_hour)
            window_context = _window_environment(
                day=day,
                window=scoring_window,
                weather_hourly=conditions["weather_hourly"],
                weather_daily=conditions.get("weather_daily", {}),
                marine_hourly=conditions["marine_hourly"],
                lon=lon,
                tide_events=parsed_tide_events,
                tide_event_source_label=window_tide_source_label,
                region=condition_region or region,
            )
            preview = build_preview(lat, lon, environment=window_context["environment"], region=region)
            score_cards = preview.get("nearby_water_types", {})
            forecast_windows.append(
                {
                    "date": day.isoformat(),
                    "time_window": window.key,
                    "engine_time_window": window_context["environment"]["time_window"],
                    "representative_time": window_context["representative_time"],
                    "environment": window_context["environment"],
                    "tide_source": window_context["tide_source"],
                    "preview": preview,
                    "water_type_scores": {
                        key: score_cards[key]["scores"]["overall_recommendation"]
                        for key in WATER_TYPE_KEYS
                        if key in score_cards
                    },
                }
            )

    return {
        "contract_version": FORECAST_CONTRACT_VERSION,
        "input": {
            "latitude": lat,
            "longitude": lon,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "region": region or "auto",
            "condition_region": condition_region or "generic_coastal",
            "windows": [window.key for window in selected_windows],
        },
        "data_sources": {
            "conditions": conditions.get("provider", "provided"),
            "weather_source": conditions.get("weather_source", "provided"),
            "cache_enabled": cache_enabled,
            "condition_fetch_start": condition_fetch_start.isoformat() if condition_data is None else start.isoformat(),
            "condition_fetch_end": condition_fetch_end.isoformat() if condition_data is None else end.isoformat(),
            "weather_trend_lookback_days": 0 if condition_data is not None else WEATHER_TREND_LOOKBACK_DAYS,
            "tide_inference_lookahead_days": 0 if condition_data is not None else (condition_fetch_end - end).days,
            "tide": tide_source_used,
            "tide_provider": tide_provider_meta,
        },
        "summary": _summarize_windows(forecast_windows),
        "windows": forecast_windows,
        "hourly_activity": hourly_activity,
    }
