import unittest
from pathlib import Path
from unittest.mock import patch

from coastal_fishing_forecast.forecast import build_range_forecast
from coastal_fishing_forecast.tides import (
    infer_tide_events_from_sea_level,
    load_tide_events_file,
    parse_tide_events,
    resolve_tide_phase,
)
from coastal_fishing_forecast.tidesatlas import normalize_tidesatlas_response


def _fixture_conditions() -> dict:
    times = []
    pressure = []
    wind_speed = []
    wind_direction = []
    precipitation = []
    wave_height = []
    swell_height = []
    swell_direction = []
    sea_level = []
    sea_level_pattern = [1.0, 0.5, 0.0, -0.5, -1.0, -0.5, 0.0, 0.5]

    for day in ("2026-04-20", "2026-04-21"):
        for hour in range(24):
            times.append(f"{day}T{hour:02d}:00")
            pressure.append(1024.0 + (hour / 24.0))
            wind_speed.append(6.0 + (hour / 12.0))
            wind_direction.append(330)
            precipitation.append(0.0)
            wave_height.append(1.0)
            swell_height.append(0.8)
            swell_direction.append(100)
            sea_level.append(sea_level_pattern[hour % len(sea_level_pattern)])

    return {
        "provider": "fixture",
        "weather_source": "fixture",
        "weather_hourly": {
            "time": times,
            "surface_pressure": pressure,
            "wind_speed_10m": wind_speed,
            "wind_direction_10m": wind_direction,
            "precipitation": precipitation,
            "cloud_cover": [45.0 for _ in times],
        },
        "weather_daily": {
            "time": ["2026-04-20", "2026-04-21"],
            "sunrise": ["2026-04-20T06:35", "2026-04-21T06:36"],
            "sunset": ["2026-04-20T17:27", "2026-04-21T17:26"],
        },
        "marine_hourly": {
            "time": times,
            "wave_height": wave_height,
            "swell_wave_height": swell_height,
            "swell_wave_direction": swell_direction,
            "sea_level_height_msl": sea_level,
        },
    }


def _fixture_conditions_varying_hourly_waves() -> dict:
    base = _fixture_conditions()
    times = base["marine_hourly"]["time"]
    wave_height = [round(0.5 + index * 0.01, 2) for index in range(len(times))]
    swell_height = [round(0.4 + index * 0.005, 2) for index in range(len(times))]
    marine = dict(base["marine_hourly"])
    marine["wave_height"] = wave_height
    marine["swell_wave_height"] = swell_height
    return {**base, "marine_hourly": marine}


def _fixture_conditions_with_weather_lookback() -> dict:
    times = []
    pressure = []
    wind_speed = []
    wind_direction = []
    wind_gusts = []
    temperature = []
    precipitation = []
    wave_height = []
    swell_height = []
    swell_direction = []
    sea_level = []
    sea_level_pattern = [1.0, 0.5, 0.0, -0.5, -1.0, -0.5, 0.0, 0.5]

    for day_index, day in enumerate(("2026-04-17", "2026-04-18", "2026-04-19", "2026-04-20")):
        for hour in range(24):
            times.append(f"{day}T{hour:02d}:00")
            warm_previous_days = day_index < 3
            afternoon = 12 <= hour <= 16
            temperature.append(23.0 if warm_previous_days and afternoon else 16.0 if afternoon else 12.0)
            pressure.append(1020.0 if warm_previous_days else 1008.0)
            wind_speed.append(6.0)
            wind_direction.append(330)
            wind_gusts.append(12.0)
            precipitation.append(0.0)
            wave_height.append(0.4)
            swell_height.append(0.4)
            swell_direction.append(100)
            sea_level.append(sea_level_pattern[hour % len(sea_level_pattern)])

    return {
        "provider": "fixture",
        "weather_source": "fixture",
        "weather_hourly": {
            "time": times,
            "temperature_2m": temperature,
            "surface_pressure": pressure,
            "wind_speed_10m": wind_speed,
            "wind_direction_10m": wind_direction,
            "wind_gusts_10m": wind_gusts,
            "precipitation": precipitation,
            "rain": precipitation,
            "cloud_cover": [45.0 for _ in times],
        },
        "weather_daily": {
            "time": ["2026-04-17", "2026-04-18", "2026-04-19", "2026-04-20"],
            "sunrise": ["2026-04-17T06:32", "2026-04-18T06:33", "2026-04-19T06:34", "2026-04-20T06:35"],
            "sunset": ["2026-04-17T17:30", "2026-04-18T17:29", "2026-04-19T17:28", "2026-04-20T17:27"],
        },
        "marine_hourly": {
            "time": times,
            "wave_height": wave_height,
            "swell_wave_height": swell_height,
            "swell_wave_direction": swell_direction,
            "sea_level_height_msl": sea_level,
        },
    }


class ForecastTests(unittest.TestCase):
    fixtures_dir = Path(__file__).resolve().parent

    def test_range_forecast_returns_windows_and_summary(self) -> None:
        result = build_range_forecast(
            -41.2530,
            148.3060,
            start_date="2026-04-20",
            end_date="2026-04-21",
            region="open_coast",
            windows=("morning", "dusk"),
            condition_data=_fixture_conditions(),
        )

        self.assertEqual(result["contract_version"], "2026-04-27.timeseries.v1")
        self.assertEqual(len(result["windows"]), 4)
        self.assertEqual(result["windows"][0]["time_window"], "morning")
        self.assertEqual(result["windows"][0]["engine_time_window"], "dawn")
        self.assertIn(result["windows"][0]["environment"]["tide_phase"], {"low", "rising", "high", "falling", "mid"})
        self.assertIn("best_windows", result["summary"])
        self.assertGreater(len(result["summary"]["best_windows"]), 0)
        self.assertEqual(len(result["hourly_activity"]), 48)
        self.assertEqual(result["hourly_activity"][0]["hour"], 0)
        self.assertIn(result["hourly_activity"][0]["time_window"], {"pre_dawn", "dawn", "day", "dusk", "night"})
        self.assertIsInstance(result["hourly_activity"][13]["score"], int)
        self.assertEqual(result["windows"][0]["environment"]["rule_family"], "derwent_generalized_v1")
        self.assertIn("rule_tags", result["hourly_activity"][13])

    def test_hourly_scores_use_derwent_style_light_windows_not_plain_midday(self) -> None:
        result = build_range_forecast(
            -41.2530,
            148.3060,
            start_date="2026-04-20",
            end_date="2026-04-20",
            region="open_coast",
            windows=("morning", "day", "dusk"),
            condition_data=_fixture_conditions(),
            tide_events=[
                {"time": "2026-04-20T00:00:00+10:00", "type": "low", "height_m": 0.1},
                {"time": "2026-04-20T06:00:00+10:00", "type": "high", "height_m": 0.8},
                {"time": "2026-04-20T12:00:00+10:00", "type": "low", "height_m": 0.1},
                {"time": "2026-04-20T18:00:00+10:00", "type": "high", "height_m": 0.8},
            ],
        )

        hourly = {point["hour"]: point for point in result["hourly_activity"]}
        self.assertGreater(hourly[6]["score"], hourly[12]["score"])
        self.assertGreater(hourly[17]["score"], hourly[12]["score"])
        self.assertIn("sunrise_window", hourly[6]["rule_tags"])
        self.assertIn("harsh_midday_penalty", hourly[12]["rule_tags"])

    def test_real_tide_events_override_approximation(self) -> None:
        tide_events = [
            {"time": "2026-04-20T05:00:00+10:00", "type": "low", "height_m": 0.2},
            {"time": "2026-04-20T11:00:00+10:00", "type": "high", "height_m": 1.1},
        ]
        result = build_range_forecast(
            -41.2530,
            148.3060,
            start_date="2026-04-20",
            end_date="2026-04-20",
            region="open_coast",
            windows=("morning",),
            condition_data=_fixture_conditions(),
            tide_events=tide_events,
        )

        self.assertEqual(result["data_sources"]["tide"], "tide_events")
        self.assertEqual(result["windows"][0]["tide_source"], "tide_events")
        self.assertEqual(result["windows"][0]["environment"]["tide_phase"], "rising")

    def test_open_meteo_model_tide_source_uses_sea_level_curve(self) -> None:
        result = build_range_forecast(
            -41.2530,
            148.3060,
            start_date="2026-04-20",
            end_date="2026-04-20",
            region="open_coast",
            windows=("morning",),
            condition_data=_fixture_conditions(),
            tide_source="openmeteo_model",
        )

        self.assertEqual(result["data_sources"]["tide"], "openmeteo_model")
        self.assertEqual(result["data_sources"]["tide_provider"]["provider"], "open_meteo")
        self.assertEqual(result["windows"][0]["tide_source"], "openmeteo_model")
        self.assertIn(result["windows"][0]["environment"]["tide_phase"], {"low", "rising", "high", "falling", "mid"})

    def test_tide_phase_from_events_marks_near_high_or_low(self) -> None:
        events = parse_tide_events(
            [
                {"time": "2026-04-20T05:00:00+00:00", "type": "low"},
                {"time": "2026-04-20T11:00:00+00:00", "type": "high"},
            ]
        )
        phase, source = resolve_tide_phase(events[0].time, 148.3060, events)
        self.assertEqual(phase, "low")
        self.assertEqual(source, "tide_events")

    def test_tide_events_can_be_inferred_from_model_sea_level(self) -> None:
        events = infer_tide_events_from_sea_level(
            [
                "2026-04-20T00:00:00+10:00",
                "2026-04-20T01:00:00+10:00",
                "2026-04-20T02:00:00+10:00",
                "2026-04-20T03:00:00+10:00",
                "2026-04-20T04:00:00+10:00",
            ],
            [0.0, 0.8, 1.0, 0.7, 0.1],
        )

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_type, "high")
        self.assertEqual(events[0].height_m, 1.0)

    def test_tide_events_json_file_can_drive_forecast(self) -> None:
        fixture = self.fixtures_dir / "fixtures_tide_events_bay_of_fires_2026-04-20.json"
        result = build_range_forecast(
            -41.2530,
            148.3060,
            start_date="2026-04-20",
            end_date="2026-04-20",
            region="open_coast",
            windows=("morning",),
            condition_data=_fixture_conditions(),
            tide_events_file=str(fixture),
        )

        self.assertEqual(result["data_sources"]["tide"], "tide_events_file")
        self.assertEqual(result["windows"][0]["tide_source"], "tide_events")
        self.assertEqual(result["windows"][0]["environment"]["tide_phase"], "rising")

    def test_tide_events_csv_file_loads(self) -> None:
        fixture = self.fixtures_dir / "fixtures_tide_events_bay_of_fires_2026-04-20.csv"
        events = load_tide_events_file(fixture)

        self.assertEqual(len(events), 3)
        self.assertEqual(events[0].event_type, "low")
        self.assertEqual(events[1].event_type, "high")

    def test_tidesatlas_response_normalizes_to_tide_events(self) -> None:
        events = normalize_tidesatlas_response(
            {
                "extremes": [
                    {"datetime": "2026-04-20T05:00:00+10:00", "height_m": 0.2, "type": "low"},
                    {"datetime": "2026-04-20T11:00:00+10:00", "height_m": 1.1, "type": "high"},
                ]
            }
        )

        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].event_type, "low")
        self.assertEqual(events[0].height_m, 0.2)

    def test_tidesatlas_source_can_drive_forecast(self) -> None:
        events = parse_tide_events(
            [
                {"time": "2026-04-20T05:00:00+10:00", "type": "low", "height_m": 0.2},
                {"time": "2026-04-20T11:00:00+10:00", "type": "high", "height_m": 1.1},
            ]
        )

        with patch(
            "coastal_fishing_forecast.forecast.fetch_tidesatlas_events",
            return_value=(events, {"provider": "tidesatlas", "port": {"name": "Demo"}, "port_distance_km": 2.5}),
        ):
            result = build_range_forecast(
                -41.2530,
                148.3060,
                start_date="2026-04-20",
                end_date="2026-04-20",
                region="open_coast",
                windows=("morning",),
                condition_data=_fixture_conditions(),
                tide_source="tidesatlas",
                tidesatlas_api_key="test-key",
            )

        self.assertEqual(result["data_sources"]["tide"], "tidesatlas")
        self.assertEqual(result["data_sources"]["tide_provider"]["provider"], "tidesatlas")
        self.assertEqual(result["windows"][0]["tide_source"], "tide_events")
        self.assertEqual(result["windows"][0]["environment"]["tide_phase"], "rising")

    def test_weather_shock_uses_multi_day_trend_context_when_available(self) -> None:
        result = build_range_forecast(
            -41.2530,
            148.3060,
            start_date="2026-04-20",
            end_date="2026-04-20",
            region="open_coast",
            windows=("day",),
            condition_data=_fixture_conditions_with_weather_lookback(),
        )

        afternoon = {point["hour"]: point for point in result["hourly_activity"]}
        self.assertIn("trend_breaking_cold_change", afternoon[13]["rule_tags"])
        self.assertIn("recent_weather_shock", afternoon[13]["rule_tags"])
        window_env = result["windows"][0]["environment"]
        self.assertLessEqual(window_env["temperature_drop_from_recent_72h_peak"], -5.0)

    def test_hourly_activity_wave_height_tracks_marine_hourly_series(self) -> None:
        result = build_range_forecast(
            -41.2530,
            148.3060,
            start_date="2026-04-20",
            end_date="2026-04-20",
            region="open_coast",
            windows=("morning",),
            condition_data=_fixture_conditions_varying_hourly_waves(),
        )
        day_points = [point for point in result["hourly_activity"] if point["date"] == "2026-04-20"]
        waves = [point["wave_height_m"] for point in day_points]
        self.assertGreater(len(set(waves)), 8)
        self.assertAlmostEqual(day_points[0]["wave_height_m"], 0.5)
        self.assertAlmostEqual(day_points[16]["wave_height_m"], round(0.5 + 16 * 0.01, 2))


if __name__ == "__main__":
    unittest.main()
