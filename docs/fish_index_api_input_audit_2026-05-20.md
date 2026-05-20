# Fish Index API Input Audit - 2026-05-20

This note records the external API fields that feed the fish index path.

Fish index is not a raw API field. It is calculated as:

```text
fish_outlook_score = 0.55 * activity_score + 0.45 * presence_score
```

`activity_score` and `presence_score` are produced from the environment inputs below plus the local coastal geometry model. Nearby structures are not allowed to increase the score.

## Corrections Made

- The Open-Meteo marine fetch now includes one extra day after the forecast range when live data is fetched. This gives the tide-event inference enough sea-level data to classify highs/lows near the end of the selected day.
- `tide_height_m` is now preserved in the scoring input record. The current score uses tide phase, stage, range, height change, and movement rate, but keeping the actual tide height visible makes audits reliable.
- Hourly and frontend condition payloads now prefer the environment values produced from API data instead of relying only on normalized preview metadata.

## API Inputs Required By Fish Index

| Algorithm input | API field or derivation | Unit | Check |
| --- | --- | --- | --- |
| `temperature_c` | Open-Meteo weather `hourly.temperature_2m` | C | Direct value, required for weather shock and comfort pressure around the fish score. |
| `wind_speed_knots` | Open-Meteo weather `hourly.wind_speed_10m`, requested with `wind_speed_unit=kn` | knots | Direct value, used for wind fit, weather stress, and trip drag. |
| `wind_direction_deg` | Open-Meteo weather `hourly.wind_direction_10m` | degrees | Direct value, used against open-water bearing. |
| `wind_gust_knots` | Open-Meteo weather `hourly.wind_gusts_10m`, requested with `wind_speed_unit=kn` | knots | Direct value, used for gust penalties and safety/comfort. |
| `pressure_hpa` | Open-Meteo weather `hourly.surface_pressure` | hPa | Direct value, used for pressure stability. |
| `pressure_delta_3h/6h/24h/48h/72h` | Derived from `hourly.surface_pressure` lookback values | hPa | Derived values, used for weather shock and stability tags. |
| `temperature_delta_24h/48h/72h` | Derived from `hourly.temperature_2m` lookback values | C | Derived values, used for weather shock. |
| `temperature_drop_from_recent_72h_peak` | Derived from recent `hourly.temperature_2m` values | C | Derived value, used for sharp-cold-change penalty. |
| `wind_direction_change_12h` | Derived from recent `hourly.wind_direction_10m` values | degrees | Derived value, used for trend notes and instability. |
| `max_gust_24h/72h` | Derived from recent `hourly.wind_gusts_10m` values | knots | Derived value, used for recent gust instability. |
| `rain_mm` | Open-Meteo weather `hourly.rain` | mm | Direct value, used for current rain effect. |
| `precipitation_mm` | Open-Meteo weather `hourly.precipitation` | mm | Direct value, used as all-precipitation fallback and recent wetness. |
| `recent_precipitation_sum_12h` | Derived from recent `hourly.precipitation` values | mm | Derived value, used for weather recovery and comfort drag. |
| `rainfall_24h/48h/72h` | Derived from recent `hourly.rain`, falling back to `hourly.precipitation` when rain is zero | mm | Derived value, used for rain disruption. |
| `cloud_cover_pct` | Open-Meteo weather `hourly.cloud_cover` | percent | Direct value, used for light/cover bonus. |
| `wave_height_m` | Open-Meteo marine `hourly.wave_height` | m | Direct value when available. In protected estuaries only, a bounded wind-based estimate is used if both wave and swell are missing. |
| `swell_height_m` | Open-Meteo marine `hourly.swell_wave_height` | m | Direct value, used for exposed water stress. |
| `swell_direction_deg` | Open-Meteo marine `hourly.swell_wave_direction` | degrees | Direct value, used against open-water bearing. |
| `wave_height_delta_24h` | Derived from recent `hourly.wave_height` values | m | Derived value, used for settling or rapidly changing sea state. |
| `sea_surface_temperature_c` | Open-Meteo marine `hourly.sea_surface_temperature` | C | Direct value, used for cold/optimal water temperature tags. |
| `tide_height_m` | Open-Meteo marine `hourly.sea_level_height_msl` | m | Direct value now retained in the scoring input record. |
| `tide_phase` | Derived from `hourly.sea_level_height_msl` high/low events | phase | Used directly in movement and water-type scoring. |
| `tide_stage` | Derived from surrounding high/low events | flood/ebb/slack | Used directly for flood/ebb/slack scoring. |
| `tide_range_m` | Derived from surrounding high/low event heights | m | Used for large/small tide movement. |
| `tide_height_change_next_2h/3h` | Derived from inferred tide event heights | m | Used for dead-water and strong-flow scoring. |
| `tide_movement_rate_m_per_hour` | Derived from surrounding high/low event heights and time gap | m/h | Used for weak/strong tide movement. |
| `sunrise/sunset` | Open-Meteo weather `daily.sunrise` and `daily.sunset` | local time | Used to derive dawn/dusk/daylight timing. |
| `moon_phase_name` and `moon_illumination_pct` | Internal astronomical calculation | phase/percent | Used for major moon phase tags. |

## Sandy Bay Live Audit

Audit coordinate: Sandy Bay, Tasmania (`-42.8991036, 147.3389916`)

Forecast date: `2026-05-20`

Audited representative scoring window: `2026-05-20T06:00:00+10:00`

| Input | API value | Algorithm value | Result |
| --- | ---: | ---: | --- |
| `temperature_c` | `7.5` | `7.5` | OK |
| `wind_speed_knots` | `5.1` | `5.1` | OK |
| `wind_direction_deg` | `308` | `308.0` | OK |
| `wind_gust_knots` | `14.8` | `14.8` | OK |
| `pressure_hpa` | `1011.5` | `1011.5` | OK |
| `rain_mm` | `0.0` | `0.0` | OK |
| `precipitation_mm` | `0.0` | `0.0` | OK |
| `cloud_cover_pct` | `69` | `69.0` | OK |
| `wave_height_m` | `0.14` | `0.14` | OK |
| `swell_height_m` | `0.12` | `0.12` | OK |
| `swell_direction_deg` | `193` | `193.0` | OK |
| `sea_surface_temperature_c` | `13.9` | `13.9` | OK |
| `tide_height_m` | `-0.57` | `-0.57` | OK |
| `tide_phase` | derived | `rising` | OK |
| `tide_stage` | derived | `flood` | OK |
| `tide_movement_rate_m_per_hour` | derived | `0.114` | OK |
| `tide_range_m` | derived | `0.91` | OK |

Open-Meteo units returned in the audit:

```json
{
  "weather": {
    "temperature_2m": "C",
    "surface_pressure": "hPa",
    "wind_speed_10m": "kn",
    "wind_direction_10m": "degrees",
    "wind_gusts_10m": "kn",
    "precipitation": "mm",
    "rain": "mm",
    "cloud_cover": "percent"
  },
  "marine": {
    "wave_height": "m",
    "wave_period": "s",
    "swell_wave_height": "m",
    "swell_wave_direction": "degrees",
    "sea_surface_temperature": "C",
    "sea_level_height_msl": "m"
  }
}
```

