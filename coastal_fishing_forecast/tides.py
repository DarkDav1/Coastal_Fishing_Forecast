"""Tide phase helpers for time-window forecasts.

The engine can use real high/low tide events when a caller supplies them.
When no events are available, it falls back to a coarse astronomical phase
estimate so replay paths do not silently pin every window to the same tide.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone, tzinfo
import json
from pathlib import Path
from typing import Any, Iterable, Mapping


TIDE_PHASES = {"low", "rising", "high", "falling", "mid"}
SEMIDIURNAL_HALF_CYCLE = timedelta(hours=6, minutes=12, seconds=30)
EVENT_WINDOW = timedelta(minutes=45)
REFERENCE_HIGH_WATER_UTC = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)


@dataclass(frozen=True)
class TideEvent:
    time: datetime
    event_type: str
    height_m: float | None = None


@dataclass(frozen=True)
class TideContext:
    phase: str
    stage: str
    hours_to_high_tide: float | None = None
    hours_to_low_tide: float | None = None
    hours_since_high_tide: float | None = None
    hours_since_low_tide: float | None = None
    tide_range_m: float | None = None
    tide_height_change_next_2h: float | None = None
    tide_height_change_next_3h: float | None = None
    tide_height_change_prev_2h: float | None = None
    tide_movement_rate_m_per_hour: float | None = None


def _parse_datetime(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def parse_tide_events(raw_events: Iterable[Mapping[str, Any]] | None) -> list[TideEvent]:
    if raw_events is None:
        return []

    events: list[TideEvent] = []
    for raw_event in raw_events:
        event_type = str(raw_event.get("type", "")).strip().lower()
        if event_type not in {"high", "low"}:
            continue
        height = raw_event.get("height_m")
        events.append(
            TideEvent(
                time=_parse_datetime(str(raw_event["time"])),
                event_type=event_type,
                height_m=None if height is None else float(height),
            )
        )
    return sorted(events, key=lambda event: event.time)


def load_tide_events_file(path: str | Path) -> list[TideEvent]:
    file_path = Path(path)
    suffix = file_path.suffix.lower()
    if suffix == ".json":
        raw = json.loads(file_path.read_text(encoding="utf-8"))
        if isinstance(raw, Mapping):
            raw_events = raw.get("events", [])
        else:
            raw_events = raw
        return parse_tide_events(raw_events)
    if suffix == ".csv":
        with file_path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        normalized_rows = []
        for row in rows:
            normalized_rows.append(
                {
                    "time": row.get("time") or row.get("datetime") or row.get("date_time"),
                    "type": row.get("type") or row.get("event_type") or row.get("event"),
                    "height_m": row.get("height_m") or row.get("height") or None,
                }
            )
        return parse_tide_events(normalized_rows)
    raise ValueError("tide event file must be .json or .csv")


def infer_tide_events_from_sea_level(
    times: Iterable[str],
    sea_level_heights_m: Iterable[Any],
    *,
    default_timezone: tzinfo = timezone.utc,
) -> list[TideEvent]:
    """Infer high/low tide events from an hourly sea-level model curve.

    This is useful for model sources such as Open-Meteo Marine. It is not a
    replacement for local tide-table stations, so callers should expose the
    source clearly in confidence messaging.
    """
    points: list[tuple[datetime, float]] = []
    for raw_time, raw_height in zip(times, sea_level_heights_m, strict=False):
        if raw_height is None:
            continue
        try:
            parsed_time = _parse_datetime(str(raw_time))
            if parsed_time.tzinfo is timezone.utc and "+" not in str(raw_time) and not str(raw_time).endswith("Z"):
                parsed_time = parsed_time.replace(tzinfo=default_timezone)
            points.append((parsed_time, float(raw_height)))
        except (TypeError, ValueError):
            continue

    events: list[TideEvent] = []
    for index in range(1, len(points) - 1):
        previous_height = points[index - 1][1]
        current_time, current_height = points[index]
        next_height = points[index + 1][1]
        if current_height >= previous_height and current_height > next_height:
            events.append(TideEvent(time=current_time, event_type="high", height_m=current_height))
        elif current_height <= previous_height and current_height < next_height:
            events.append(TideEvent(time=current_time, event_type="low", height_m=current_height))
    return events


def infer_tide_phase_from_events(target_time: datetime, events: Iterable[TideEvent]) -> str | None:
    event_list = sorted(events, key=lambda event: event.time)
    if not event_list:
        return None

    target = target_time if target_time.tzinfo is not None else target_time.replace(tzinfo=timezone.utc)
    previous_events = [event for event in event_list if event.time <= target]
    next_events = [event for event in event_list if event.time >= target]
    previous_event = previous_events[-1] if previous_events else None
    next_event = next_events[0] if next_events else None

    nearest = min(
        (event for event in (previous_event, next_event) if event is not None),
        key=lambda event: abs(event.time - target),
        default=None,
    )
    if nearest is not None and abs(nearest.time - target) <= EVENT_WINDOW:
        return nearest.event_type

    if previous_event is None or next_event is None:
        return None
    if previous_event.event_type == "low" and next_event.event_type == "high":
        return "rising"
    if previous_event.event_type == "high" and next_event.event_type == "low":
        return "falling"
    return "mid"


def _hours_between(first: datetime, second: datetime) -> float:
    return round((second - first).total_seconds() / 3600.0, 3)


def _interpolated_tide_height(target: datetime, events: list[TideEvent]) -> float | None:
    if not events:
        return None

    previous_event = None
    next_event = None
    for event in events:
        if event.height_m is None:
            continue
        if event.time <= target:
            previous_event = event
        elif event.time > target:
            next_event = event
            break

    if previous_event is not None and previous_event.time == target:
        return previous_event.height_m
    if previous_event is None or next_event is None:
        return None

    total_seconds = (next_event.time - previous_event.time).total_seconds()
    if total_seconds <= 0:
        return None
    elapsed_seconds = (target - previous_event.time).total_seconds()
    ratio = max(0.0, min(1.0, elapsed_seconds / total_seconds))
    return previous_event.height_m + ((next_event.height_m - previous_event.height_m) * ratio)


def _tide_height_change(
    target: datetime,
    events: list[TideEvent],
    *,
    offset_hours: float,
) -> float | None:
    current_height = _interpolated_tide_height(target, events)
    comparison_height = _interpolated_tide_height(target + timedelta(hours=offset_hours), events)
    if current_height is None or comparison_height is None:
        return None
    return round(abs(comparison_height - current_height), 3)


def resolve_tide_context(
    target_time: datetime,
    lon: float,
    tide_events: Iterable[TideEvent] | None = None,
) -> TideContext:
    """Return phase plus generic coastal tide movement features.

    These features are generic: they describe whether water is flooding,
    ebbing, near slack, and how close the window is to the next high/low.
    """
    phase, _source = resolve_tide_phase(target_time, lon, tide_events)
    event_list = sorted(tide_events or [], key=lambda event: event.time)
    if not event_list:
        stage = "flood" if phase == "rising" else "ebb" if phase == "falling" else "slack"
        return TideContext(phase=phase, stage=stage)

    target = target_time if target_time.tzinfo is not None else target_time.replace(tzinfo=timezone.utc)
    previous_event = None
    next_event = None
    for event in event_list:
        if event.time <= target:
            previous_event = event
        elif event.time > target:
            next_event = event
            break

    previous_high = next((event for event in reversed(event_list) if event.time <= target and event.event_type == "high"), None)
    previous_low = next((event for event in reversed(event_list) if event.time <= target and event.event_type == "low"), None)
    next_high = next((event for event in event_list if event.time >= target and event.event_type == "high"), None)
    next_low = next((event for event in event_list if event.time >= target and event.event_type == "low"), None)

    if previous_event is None and next_event is not None:
        stage = "flood" if next_event.event_type == "high" else "ebb"
    elif previous_event is not None and next_event is None:
        stage = "ebb" if previous_event.event_type == "high" else "flood"
    elif previous_event is not None and next_event is not None:
        if abs(previous_event.time - target) <= EVENT_WINDOW or abs(next_event.time - target) <= EVENT_WINDOW:
            stage = "slack"
        elif previous_event.event_type == "low" and next_event.event_type == "high":
            stage = "flood"
        elif previous_event.event_type == "high" and next_event.event_type == "low":
            stage = "ebb"
        else:
            stage = "slack"
    else:
        stage = "unknown"

    tide_range = None
    if previous_event is not None and next_event is not None:
        if previous_event.height_m is not None and next_event.height_m is not None:
            tide_range = round(abs(next_event.height_m - previous_event.height_m), 3)

    change_next_2h = _tide_height_change(target, event_list, offset_hours=2.0)
    change_next_3h = _tide_height_change(target, event_list, offset_hours=3.0)
    change_prev_2h = _tide_height_change(target, event_list, offset_hours=-2.0)
    movement_rate = None
    if previous_event is not None and next_event is not None:
        if previous_event.height_m is not None and next_event.height_m is not None:
            hours_between_events = abs(_hours_between(previous_event.time, next_event.time))
            if hours_between_events > 0:
                movement_rate = round(abs(next_event.height_m - previous_event.height_m) / hours_between_events, 3)

    return TideContext(
        phase=phase,
        stage=stage,
        hours_to_high_tide=None if next_high is None else _hours_between(target, next_high.time),
        hours_to_low_tide=None if next_low is None else _hours_between(target, next_low.time),
        hours_since_high_tide=None if previous_high is None else _hours_between(previous_high.time, target),
        hours_since_low_tide=None if previous_low is None else _hours_between(previous_low.time, target),
        tide_range_m=tide_range,
        tide_height_change_next_2h=change_next_2h,
        tide_height_change_next_3h=change_next_3h,
        tide_height_change_prev_2h=change_prev_2h,
        tide_movement_rate_m_per_hour=movement_rate,
    )


def estimate_tide_phase(target_time: datetime, lon: float) -> str:
    """Return a coarse no-key tide phase estimate.

    Longitude shifts the reference event so east/west coasts do not all share
    identical synthetic phase. This is not a replacement for a port tide table.
    """
    target = target_time if target_time.tzinfo is not None else target_time.replace(tzinfo=timezone.utc)
    longitude_offset = timedelta(hours=lon / 15.0)
    shifted_reference = REFERENCE_HIGH_WATER_UTC - longitude_offset
    elapsed = target.astimezone(timezone.utc) - shifted_reference
    half_cycles = elapsed.total_seconds() / SEMIDIURNAL_HALF_CYCLE.total_seconds()
    nearest_half_cycle = round(half_cycles)
    distance_to_event = abs(half_cycles - nearest_half_cycle) * SEMIDIURNAL_HALF_CYCLE

    event_is_high = nearest_half_cycle % 2 == 0
    if distance_to_event <= EVENT_WINDOW:
        return "high" if event_is_high else "low"

    lower_cycle = int(half_cycles // 1)
    last_event_high = lower_cycle % 2 == 0
    return "falling" if last_event_high else "rising"


def resolve_tide_phase(
    target_time: datetime,
    lon: float,
    tide_events: Iterable[TideEvent] | None = None,
) -> tuple[str, str]:
    event_phase = infer_tide_phase_from_events(target_time, tide_events or [])
    if event_phase in TIDE_PHASES:
        return event_phase, "tide_events"
    return estimate_tide_phase(target_time, lon), "astronomical_approximation"
