# Coastal Fishing Forecast

Generic saltwater and estuary fishing forecast engine.

## Why this project exists

This project is intentionally separate from the existing Derwent-specific engine.

The Derwent project remains the high-confidence local system used for:

- curated local hot spots
- detailed spot splitting
- Derwent species logic
- personal-use local tuning

This project is the generic product track for a public app or web app.

It is meant to support:

- coastal saltwater spots
- estuary shore fishing
- jetties, rocks, beaches, bay edges, channel edges
- searched places and GPS-based previews

It is **not** meant to cover inland rivers or inland lakes in the first version.

## Product scope

### Supported in v1

- coastal saltwater
- estuary / tidal water
- surf beaches
- rock ledges
- jetties and wharves
- bay edges
- channel / transition water

### Explicitly not supported in v1

- inland rivers
- inland lakes
- reservoirs
- freshwater trout-only systems away from tidal influence

## Product lines

The generic app should support two product lines.

### 1. Curated hot spots

These are known spots maintained by the backend for supported regions.

### 2. Search / nearby preview

The user searches a place, taps a map, or uses GPS.
The backend infers local water type and returns a lower-confidence forecast.

## Core scoring model

The generic engine should work around four outputs:

- `resident_opportunity`
- `roaming_opportunity`
- `trip_quality`
- `overall_recommendation`

## Design rules

1. Do not pretend every searched coordinate is understood like a curated local spot.
2. Separate region logic from generic logic.
3. Use water-type inference before scoring.
4. Reject unsupported inland locations clearly instead of returning fake scores.
5. Keep confidence visible in product behavior, even if the UI language stays simple.

## Initial roadmap

1. Define supported coastal product scope.
2. Build inland / non-coastal rejection logic.
3. Build water-type inference:
   - beach
   - rocks
   - jetty
   - bay edge
   - estuary edge
   - channel edge
4. Add region config layer.
5. Add generic preview endpoint for searched coordinates.
6. Add curated region packs later.

## Relationship to the Derwent project

The Derwent project remains the working local engine:

- `/Users/chenweic/dev/Fishing_Forcast/workspace-cocky/fishing-forecast`

This new project is the generic product track:

- `/Users/chenweic/dev/Fishing_Forcast/workspace-cocky/coastal-fishing-forecast`

## First working preview path

The first backend milestone now exists as a small search-preview path for raw coordinates.

It currently does four things:

1. accepts latitude and longitude
2. rejects inland or unsupported coordinates clearly
3. infers broad nearby water types from coastline shape
4. returns a structured low-confidence preview payload for app or web

This path is intentionally cautious.

It is meant for searched coordinates, not curated local hot spots.

## Preview output shape

Supported coordinates return:

- `overall_recommendation`
- `nearby_water_types.beach`
- `nearby_water_types.rocks`
- `nearby_water_types.jetty`
- `nearby_water_types.bay_estuary_edge`

Each nearby type card includes:

- `resident_opportunity`
- `roaming_opportunity`
- `trip_quality`
- `overall_recommendation`

## Local setup

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -e .
```

## Run a preview

```bash
./.venv/bin/coastal-preview -33.8915 151.2767
```

Or:

```bash
./.venv/bin/python -m coastal_fishing_forecast -42.8821 147.3390
```

## Run a date-range forecast or replay

```bash
./.venv/bin/coastal-forecast -41.2530 148.3060 \
  --start-date 2026-04-20 \
  --end-date 2026-04-26 \
  --region open_coast \
  --windows morning,dusk \
  --condition-source archive
```

The range path loads weather and marine conditions, estimates or accepts tide phase per window, then returns a structured list of preview windows plus a summary.

Run the low-cost search-to-forecast regression replay:

```bash
./.venv/bin/coastal-regression-replay \
  --start-date 2026-04-20 \
  --end-date 2026-04-20 \
  --cache-dir .cache/coastal_fishing_forecast \
  --fail-on-error
```

This replay uses Nominatim place search, cached Open-Meteo archive conditions, and tide approximation. It does not use TidesAtlas quota.

The replay covers supported coastal examples and explicit rejection examples. Current cases include open beaches, estuary towns, bay edges, harbour water, surf beaches, headlands, breakwall-style access, inland towns, and inland lakes.

## Frontend planning

The current end-to-end development guide is documented in:

- `docs/development_guide_2026-05-20.md`

The first standalone frontend plan is documented in:

- `docs/frontend_product_plan_2026-04-28.md`

The frontend should first prove the search-to-forecast flow, including supported coastal places and unsupported inland/lake cases, before adding curated hot spots or heavy map features.

The frontend API includes a `plan` block for action-oriented recommendations. By default this is rule-based. For GitHub Models wording tests, pass:

```bash
./.venv/bin/coastal-api-forecast -41.2530 148.3060 \
  --start-date 2026-04-20 \
  --end-date 2026-04-20 \
  --region open_coast \
  --windows morning \
  --condition-source archive \
  --tide-source openmeteo_model \
  --planner-provider github_models
```

Configure `GITHUB_TOKEN` first. If the model is unavailable, the API falls back to the rule-based plan.

To use TidesAtlas for real tide events, set an API key:

```bash
export TIDESATLAS_API_KEY="your-key"

./.venv/bin/coastal-forecast -41.2530 148.3060 \
  --start-date 2026-04-20 \
  --end-date 2026-04-26 \
  --region open_coast \
  --windows morning,dusk \
  --condition-source archive \
  --tide-source tidesatlas
```

You can also pass the key directly with `--tidesatlas-api-key`.

If real tide events are available from a tide table, pass them in:

```bash
./.venv/bin/coastal-forecast -41.2530 148.3060 \
  --start-date 2026-04-20 \
  --end-date 2026-04-20 \
  --region open_coast \
  --windows morning \
  --tide-events-json '[{"time":"2026-04-20T05:00:00+10:00","type":"low"},{"time":"2026-04-20T11:00:00+10:00","type":"high"}]'
```

Or use a JSON/CSV file:

```bash
./.venv/bin/coastal-forecast -41.2530 148.3060 \
  --start-date 2026-04-20 \
  --end-date 2026-04-20 \
  --region open_coast \
  --windows morning \
  --tide-events-file tests/fixtures_tide_events_bay_of_fires_2026-04-20.json
```

Tide files should contain `time`, `type`, and optional `height_m`. Supported event types are `high` and `low`.

For low-cost model tide without spending TidesAtlas quota:

```bash
./.venv/bin/coastal-api-forecast -41.2530 148.3060 \
  --start-date 2026-04-20 \
  --end-date 2026-04-20 \
  --region open_coast \
  --windows morning,dusk \
  --condition-source archive \
  --tide-source openmeteo_model
```

This uses Open-Meteo model sea-level data and marks the tide as model-estimated, not verified against a local tide station.

Without real tide events or model tide data, the engine uses a coarse astronomical approximation and marks that source in the output.

## Run a frontend-oriented API response

```bash
./.venv/bin/coastal-api-forecast -41.2530 148.3060 \
  --start-date 2026-04-20 \
  --end-date 2026-04-21 \
  --region open_coast \
  --windows morning,dusk \
  --condition-source archive
```

This returns page-ready sections:

- `hero`
- `location`
- `confidence`
- `tide_verification`
- `daily_forecast`
- `conditions`
- `expanded_water_types`
- `behavior_groups`
- `modules`
- `raw_forecast`

External weather, marine, and tide API responses are cached by default. Use `--no-cache` to bypass cache and `--cache-dir` to choose a cache directory.

## Run place search

Place search is separate from the forecast engine. It resolves a user query into candidate coordinates.

Free low-volume development test:

```bash
./.venv/bin/coastal-place-search "St Helens Tasmania" \
  --provider nominatim \
  --country au
```

Mapbox production-style search:

```bash
export MAPBOX_ACCESS_TOKEN="your-token"

./.venv/bin/coastal-place-search "Bay of Fires" \
  --provider mapbox \
  --country au \
  --proximity -41.3,148.3
```

The selected result's latitude and longitude should then be passed to `coastal-api-forecast`.

Or run the full search-to-forecast flow:

```bash
./.venv/bin/coastal-search-forecast "Binalong Bay Tasmania" \
  --provider nominatim \
  --start-date 2026-04-20 \
  --end-date 2026-04-20 \
  --region open_coast \
  --windows morning \
  --condition-source archive
```

External key setup is documented in:

- `docs/external_keys_setup_2026-04-28.md`

## Verification

Use this as the main local verification path:

```bash
./.venv/bin/coastal-verify
```

It runs:

- the full regression test suite
- a coastal on-water smoke check
- a near-water smoke check
- a tidal-corridor smoke check
- an unsupported inland/boundary smoke check
- an invalid-coordinate smoke check
- the date-range forecast and tide-phase regression tests
- the frontend-oriented API response contract
- the JSON cache helper

For more detail:

```bash
./.venv/bin/coastal-verify --verbose
```

To verify real TidesAtlas tide access:

```bash
TIDESATLAS_API_KEY="your-key" ./.venv/bin/coastal-verify --include-live-tides --verbose
```

The raw test suite can also be run directly:

```bash
./.venv/bin/python -m unittest discover -s tests -v
```
