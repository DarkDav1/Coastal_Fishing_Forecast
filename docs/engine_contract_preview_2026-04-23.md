# Engine Contract: Coordinate Preview (2026-04-23)

This document is for backend and session handoff only.

## Purpose

The engine accepts a searched coordinate and returns one of three outcomes:

1. `ok`
2. `unsupported`
3. `invalid_input`

This contract is engine-only.

It does not define:

- HTTP routes
- frontend rendering
- map search behavior
- curated hotspot behavior

## Engine entry point

- Python function: `coastal_fishing_forecast.build_preview(lat, lon, environment=None, region=None)`
- CLI: `coastal-preview <lat> <lon>`

Optional CLI flag:

- `--environment-json '{"wind_speed_knots": 18, "wind_direction_deg": 110, "swell_height_m": 1.8, "swell_direction_deg": 110, "pressure_hpa": 1012, "tide_phase": "rising", "time_window": "dawn"}'`
- `--region open_coast`

## Stable top-level fields

Every response includes:

- `contract_version`
- `status`
- `input`
- `support`
- `overall_recommendation`
- `nearby_water_types`
- `meta`

Important support-state details now also appear in:

- `meta.support_profile.support_mode`
- `meta.support_profile.distance_band_km`
- `meta.support_profile.direct_nearby_limit_km`
- `meta.support_profile.extended_tidal_limit_km`

## Status meanings

### `ok`

The coordinate is on supported coastal/tidal water, or close enough to supported water for a low-confidence nearby preview.

### `unsupported`

The coordinate is not within the current supported coastal/tidal scope.

### `invalid_input`

The coordinate values are outside valid latitude/longitude bounds.

## Reason codes

### Support reason codes

- `coastal_or_tidal_preview`
- `tidal_corridor_preview`
- `inland_or_non_tidal`
- `too_far_from_supported_water`
- `invalid_coordinate`

These are engine reason codes, not final product wording.

Current support boundary is intentionally tighter than before:

- direct nearby preview is intended for points on water or very close to supported water
- farther inland searched points are rejected unless they still look like a sheltered tidal corridor case within the tighter extended preview band

Support modes currently used in `meta.support_profile.support_mode`:

- `on_water`
- `near_water`
- `tidal_corridor`
- `unsupported`
- `invalid_input`

## Confidence rules

- `ok` responses are currently low-confidence preview outputs
- `unsupported` and `invalid_input` use high-confidence rejection
- searched coordinate output must remain lower-confidence than curated hotspots

## Nearby water type keys

Current stable order:

1. `beach`
2. `rocks`
3. `jetty`
4. `bay_estuary_edge`

These are broad inferred nearby types only.

They do not confirm exact local structure.

## Score fields inside each nearby type

- `resident_opportunity`
- `roaming_opportunity`
- `trip_quality`
- `overall_recommendation`

All current scores are coarse preview values on a 0 to 100 scale.

## Optional environment inputs

The engine can now accept an optional environment object with these broad fields:

- `wind_speed_knots`
- `wind_direction_deg`
- `swell_height_m`
- `swell_direction_deg`
- `pressure_hpa`
- `tide_phase`
- `time_window`

If omitted, the engine uses neutral defaults.

These values currently act as broad scoring modifiers only.

They do not change support detection or nearby water-type inference.

Direction fields are optional.

If omitted, the engine uses a neutral directional assumption instead of pretending it knows the forcing angle.

Normalized environment values are returned in:

- `meta.environment.inputs_used`
- `meta.environment.normalized`

Tide phase is now applied differently across nearby types.

Examples:

- beach-like output currently benefits more from rising tide than slack high tide
- bay or estuary-edge output currently benefits more from active falling or rising water than slack high tide

## Optional region preset

The engine can now accept an optional generic `region` preset.

Current presets:

- `generic_coastal`
- `open_coast`
- `sheltered_estuary`
- `surf_coast`
- `harbour_access`
- `bay_coast`

These presets are generic biases only.

They do not introduce local spot knowledge.

The chosen preset is returned in:

- `meta.region.slug`
- `meta.region.display_name`

## Known limits in current engine

- It uses broad coastline geometry only
- It now ingests broad wind, wind direction, swell, swell direction, pressure, tide-phase, and time-window inputs as score modifiers
- Coastline orientation is estimated from coarse nearby water geometry, not true shoreline mapping
- Region presets are still broad generic biases, not validated local calibration
- It does not confirm real jetties, rocks, or named structures
- Open exposed coast can still lean beach-first even where rocky access exists nearby
- Support boundaries are still geometric heuristics, not a true tidal-water polygon check
- It should not be treated as curated-spot confidence

## Integration guidance for the next session

- Treat this as a raw engine contract
- Do not remap or rename fields casually
- Prefer wrapping it at the API layer rather than changing the engine response shape
- If new fields are added later, keep backward-compatible defaults where possible
