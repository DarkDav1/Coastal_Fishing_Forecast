"""LLM-backed narrative for the web «score factors» panel (tide / weather / sea)."""

from __future__ import annotations

import json
import math
import sys
from typing import Any, Mapping

from urllib.error import URLError

from coastal_fishing_forecast.github_models import GitHubModelsError, generate_github_models_score_factors_text


def _num(x: Any) -> float | None:
    if isinstance(x, bool):
        return None
    if isinstance(x, (int, float)):
        if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
            return None
        return float(x)
    return None


def _average_float(values: list[float | None]) -> float | None:
    valid = [v for v in values if isinstance(v, (int, float)) and not (isinstance(v, float) and math.isnan(v))]
    if not valid:
        return None
    return float(sum(valid)) / len(valid)


def aggregate_windows_stats(windows: list[Mapping[str, Any]]) -> dict[str, Any]:
    """Mirror apps/web `dayConditionStats` aggregation from window cards."""

    wind_avgs: list[float | None] = []
    gusts: list[float] = [0.0]
    wave_avgs: list[float | None] = []
    waves_max: list[float] = [0.0]
    swells_max: list[float] = [0.0]
    rain_tot = 0.0
    temps: list[float | None] = []
    pressures: list[float | None] = []
    shocks: list[float] = [0.0]
    tide_move_max: list[float] = [0.0]
    tide_ranges: list[float | None] = []
    tide_phases: set[str] = set()

    for window in windows:
        cond = window.get("conditions") if isinstance(window.get("conditions"), Mapping) else {}
        wind = cond.get("wind") if isinstance(cond.get("wind"), Mapping) else {}
        swell = cond.get("swell") if isinstance(cond.get("swell"), Mapping) else {}
        air = cond.get("air") if isinstance(cond.get("air"), Mapping) else {}
        wtrend = cond.get("weather_trend") if isinstance(cond.get("weather_trend"), Mapping) else {}
        tide = cond.get("tide") if isinstance(cond.get("tide"), Mapping) else {}

        wind_avgs.append(_num(wind.get("speed_knots")))
        g = _num(wind.get("gust_knots"))
        r12 = _num(wind.get("recent_max_12h"))
        gusts.append(max(g or 0.0, r12 or 0.0))

        wh = _num(swell.get("wave_height_m"))
        hm = _num(swell.get("height_m"))
        wave_avgs.append(wh if wh is not None else hm)
        waves_max.append(max(wh or 0.0, hm or 0.0))
        swells_max.append(hm or 0.0)

        rain_tot += float(air.get("rain_mm") or air.get("precipitation_mm") or 0.0)
        temps.append(_num(air.get("temperature_c")))
        pressures.append(_num(cond.get("pressure_hpa")))

        shock = _num(wtrend.get("shock_score"))
        shocks.append(float(shock or 0.0))

        tr = _num(tide.get("movement_rate_m_per_hour"))
        tide_move_max.append(abs(tr or 0.0))
        tide_ranges.append(_num(tide.get("range_m")))
        ph = tide.get("phase")
        if isinstance(ph, str) and ph:
            tide_phases.add(ph)

    out: dict[str, Any] = {
        "wind_speed_avg_knots": round(x, 2) if (x := _average_float(wind_avgs)) is not None else None,
        "wind_gust_max_knots": round(max(gusts), 2),
        "wave_height_avg_m": round(x, 2) if (x := _average_float(wave_avgs)) is not None else None,
        "wave_height_max_m": round(max(waves_max), 2),
        "swell_height_max_m": round(max(swells_max), 2),
        "rain_total_mm_window_sum": round(rain_tot, 2),
        "air_temperature_avg_c": round(x, 2) if (x := _average_float(temps)) is not None else None,
        "pressure_avg_hpa": round(x, 2) if (x := _average_float(pressures)) is not None else None,
        "weather_shock_max": round(max(shocks), 2),
        "tide_movement_rate_abs_max_m_per_h": round(max(tide_move_max), 4),
        "tide_range_avg_m": round(x, 3) if (x := _average_float(tide_ranges)) is not None else None,
        "tide_phases_observed": sorted(tide_phases),
    }
    return out


def _collect_change_notes(windows: list[Mapping[str, Any]], limit: int = 8) -> list[str]:
    notes: list[str] = []
    seen: set[str] = set()
    for window in windows:
        cond = window.get("conditions") if isinstance(window.get("conditions"), Mapping) else {}
        wtrend = cond.get("weather_trend") if isinstance(cond.get("weather_trend"), Mapping) else {}
        raw = wtrend.get("change_notes")
        if not isinstance(raw, list):
            continue
        for item in raw:
            if isinstance(item, str) and item.strip() and item not in seen:
                seen.add(item)
                notes.append(item.strip())
                if len(notes) >= limit:
                    return notes
    return notes


def build_score_factors_payload(
    *,
    lang: str,
    date_iso: str,
    windows: list[Mapping[str, Any]],
) -> dict[str, Any]:
    aggregates = aggregate_windows_stats(windows)
    notes = _collect_change_notes(windows)
    slots = [
        {"time_window": w.get("time_window"), "representative_time": w.get("representative_time")}
        for w in windows[:12]
        if isinstance(w, Mapping)
    ]
    return {
        "lang": lang if lang in {"en", "zh"} else "en",
        "date": date_iso,
        "aggregates": aggregates,
        "weather_change_notes": notes,
        "windows_summary": slots,
    }


def explain_score_factors(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Returns paragraph + provider; on failure returns empty paragraph for client fallback."""

    try:
        result = generate_github_models_score_factors_text(payload)
        return {"paragraph": result["paragraph"], "provider": "github_models"}
    except (GitHubModelsError, OSError, TimeoutError, ValueError, URLError):
        return {"paragraph": "", "provider": "fallback"}


def main() -> None:
    """Stdin JSON -> stdout JSON. Always exits 0 so the Node gateway can forward errors in-body."""

    raw = sys.stdin.read()
    if not raw.strip():
        print(json.dumps({"paragraph": "", "provider": "fallback", "error": "empty_stdin"}))
        return
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(json.dumps({"paragraph": "", "provider": "fallback", "error": "invalid_json", "message": str(exc)}))
        return

    windows = data.get("windows")
    if not isinstance(windows, list):
        print(json.dumps({"paragraph": "", "provider": "fallback", "error": "missing_windows"}))
        return

    lang = data.get("lang") if isinstance(data.get("lang"), str) else "en"
    date_iso = data.get("date") if isinstance(data.get("date"), str) else ""

    payload = build_score_factors_payload(lang=lang, date_iso=date_iso, windows=windows)
    out = explain_score_factors(payload)
    print(json.dumps(out))
