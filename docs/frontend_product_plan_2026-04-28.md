# Frontend Product Plan (2026-04-28)

This plan is for a standalone generic coastal fishing forecast frontend.

It should not reuse Derwent-specific assumptions. The first frontend should prove the searched-place forecast path before adding curated hot spots, accounts, saved spots, or heavy map features.

## First Product Goal

Build a working search-to-forecast experience:

1. user searches a coastal or inland place
2. app resolves candidate coordinates
3. backend decides whether the location is supported
4. app shows either a forecast preview or a clear unsupported state

The first frontend should treat searched-place forecasts as lower-confidence previews, not as curated local spot forecasts.

## First Demo Locations

The first frontend demo should be tested against these cases:

- Binalong Bay Tasmania: supported open beach-style preview
- St Helens Tasmania: supported estuary-town preview
- Sydney Harbour Australia: supported harbour-water preview
- Alice Springs Northern Territory: unsupported inland rejection
- Lake Eildon Victoria: unsupported inland-lake rejection

These are aligned with the backend low-cost regression replay.

## Main User Flow

### Search Flow

1. User lands on the search page.
2. User enters a place name.
3. App calls the place-search endpoint.
4. App renders candidate places.
5. User chooses a candidate, or the app uses the top supported candidate in simple demo mode.
6. App calls the forecast endpoint.
7. App renders forecast, unsupported state, or error state.

For the first demo, the app may use the combined search-to-forecast endpoint to reduce UI complexity. The split candidate flow should remain the target product shape.

### GPS Flow

GPS can be a second path after search works.

1. User taps current location.
2. App sends coordinates directly to the frontend forecast endpoint.
3. Backend attempts to use the nearest available tide / hydrology station when a real tide source is enabled.
4. App renders forecast or unsupported state.

Default tide-station behavior:

- use the user's GPS coordinate as the tide lookup coordinate
- prefer the nearest available tide station from the configured real tide provider
- include station distance in the response when available
- show normal tide confidence only when the station is local enough
- show a caution banner when the nearest station is distant
- fall back to tide approximation when no real station source is configured

The frontend should not choose tide stations itself. It should show the backend-selected station status and distance.

### Map Tap Flow

Map tap should not be first unless a frontend session already has map infrastructure ready.

1. User taps map.
2. App sends coordinates directly to the forecast endpoint.
3. App shows low-confidence searched-coordinate preview.

### Structure Map Layer

Boat ramps, piers, jetties, and water access points should be a separate map layer.

Initial frontend behavior:

- show mapped boat ramps
- show mapped pier / jetty features
- show mapped water access points
- expose source and confidence when tapped

The frontend should not treat these markers as curated fishing spots. They are structure/access signals only.

The detailed structure-layer contract is documented in:

- `docs/structure_facility_layer_plan_2026-04-28.md`

## Page Structure

### Search Page

Primary job: get the user to a supported forecast or a clear unsupported message.

Core sections:

- search input
- recent demo searches during development
- candidate result list
- loading and empty states
- short product scope note: coastal and tidal fishing only

### Forecast Page

Primary job: explain whether it is worth going and where nearby looks best.

Core sections:

- location header
- recommendation hero
- fishing plan card
- confidence banner
- best-window card
- water-type opportunity cards
- condition panel
- daily forecast list
- nearby structure/access summary when available
- explanation panel
- raw/debug drawer for development only

### Unsupported Page

Primary job: reject unsupported places without making the product feel broken.

Required message:

> This forecast currently supports coastal and tidal fishing areas only.

Optional secondary action:

- search a nearby coast
- choose another place

## Component Plan

### `SearchBox`

Inputs:

- query string
- optional country filter

States:

- idle
- typing
- loading
- results
- no results
- error

### `CandidateList`

Shows:

- display name
- region/country
- source
- candidate type when available

Behavior:

- selecting a candidate should trigger coordinate forecast later
- demo mode can skip this and use combined search-to-forecast

### `ForecastHero`

Uses:

- `forecast.hero.score`
- `forecast.hero.label`
- `forecast.hero.headline`
- `forecast.hero.best_window`

Display:

- large recommendation score
- plain-language label
- best time window
- short forecast headline

### `FishingPlanCard`

Uses:

- `forecast.plan.recommendation`
- `forecast.plan.primary_action`
- `forecast.plan.backup_action`
- `forecast.plan.avoid`
- `forecast.plan.risks`
- `forecast.plan.confidence_note`
- `forecast.plan.data_source_note`

Display:

- Go / Maybe / Skip recommendation
- first action to try
- backup option
- what to avoid
- confidence and data-source note

Rules:

- do not display unsupported plans as fishing advice
- do not hide model tide or remote-station warnings
- do not turn behavior groups into species predictions

### `ConfidenceBanner`

Uses:

- `forecast.confidence.label`
- `forecast.confidence.score`
- `forecast.confidence.factors`
- `forecast.tide_verification.status`

Important display rules:

- show estimated tide warning when status is `estimated`
- show remote-station warning when status is `live_verified_remote_station`
- show station distance when `forecast.tide_verification.station_distance_km` is present
- show searched-coordinate preview wording unless the future backend marks a curated spot

### `WaterTypeCards`

Uses:

- `forecast.daily_forecast[*].windows[*].water_type_scores`
- `forecast.daily_forecast[*].windows[*].expanded_water_types`

Initial cards:

- beach
- rocks
- jetty / wharf
- bay / estuary edge

These cards should avoid claiming exact mapped features. Use wording like "nearby signal" or "best nearby option".

### `ConditionsPanel`

Uses:

- wind speed and direction
- swell height and direction
- tide phase and source
- pressure

First display:

- wind chip
- swell chip
- tide chip
- pressure chip

The tide chip should show whether tide data came from a nearby real station, a distant real station, supplied tide events, or approximation.

### `ExplanationPanel`

Uses:

- `forecast.explanation.why_this_window`
- `forecast.explanation.risks`
- `forecast.explanation.alternatives`

Display:

- why this time
- risks
- backup options

### `UnsupportedState`

Uses:

- top-level `status`
- selected candidate support if available

Display:

- clear unsupported message
- no score
- no fake water-type cards

## API Mapping

### Recommended Demo Endpoint

Use the combined flow first:

```text
GET /api/search-forecast?query=Binalong%20Bay%20Tasmania&start_date=2026-04-20&end_date=2026-04-20
```

Backend command equivalent:

```bash
./.venv/bin/coastal-search-forecast "Binalong Bay Tasmania" \
  --provider nominatim \
  --start-date 2026-04-20 \
  --end-date 2026-04-20 \
  --region open_coast \
  --windows morning,dusk \
  --condition-source archive
```

Expected response handling:

- `status == "ok"` and `forecast != null`: render forecast page
- `status == "unsupported_or_no_result"`: render unsupported page
- network or server error: render retry/error state

### Later Split Endpoints

Place search:

```text
GET /api/places?query=St%20Helens%20Tasmania&provider=nominatim&country=au
```

Coordinate forecast:

```text
GET /api/forecast?lat=-41.252011&lon=148.304772&start_date=2026-04-20&end_date=2026-04-20
```

The split flow is better for real UX because users can choose between candidate locations.

GPS forecast with real tide lookup enabled:

```text
GET /api/forecast?lat=-41.252011&lon=148.304772&start_date=2026-04-20&end_date=2026-04-20&tide_source=auto
```

Expected tide response handling:

- `live_verified`: show real tide data
- `live_verified_remote_station`: show real tide data with a station-distance caution
- `provided_events`: show real supplied tide events
- `estimated`: show approximation warning

## Frontend State Model

Top-level states:

- `idle`: no search yet
- `searching`: place or combined forecast request in progress
- `forecast_ready`: supported forecast returned
- `unsupported`: backend rejected location or no supported candidate
- `error`: request failed or response could not be parsed

Forecast confidence states:

- `medium`: normal searched-coordinate preview
- `low`: estimated tide, distant tide station, or near-water support
- `high`: not expected for searched-coordinate previews in v1

## Visual Direction

The frontend should feel like a weather and marine forecast product, not like a generic dashboard.

Recommended first visual system:

- coastal chart-inspired layout
- large forecast score
- tide/wind/swell chips near the top
- water-type cards as the main decision surface
- subdued caution styling for confidence and tide-source warnings

Avoid:

- pretending searched places are exact fishing spots
- species-specific certainty
- inland fishing language
- dark-mode-only design
- map-first product before the forecast path works

## First Build Milestone

The first frontend milestone is complete when:

1. Binalong Bay renders a supported forecast.
2. St Helens renders a supported forecast.
3. Sydney Harbour renders a supported forecast.
4. Alice Springs renders the unsupported state.
5. Lake Eildon renders the unsupported state.
6. Estimated tide is visibly marked as lower confidence.
7. Distant real tide stations are visibly marked as lower confidence when returned.
8. The page shows water-type cards and condition chips.
9. The app can be tested from one local command.

## Backend Requirements For Frontend Session

The frontend session needs a small HTTP wrapper around the existing Python commands or package functions.

Minimum routes:

- `/api/search-forecast`
- `/api/places`
- `/api/forecast`
- `/api/health`

The wrapper should not add fishing logic. It should only translate HTTP inputs to existing backend calls and return JSON.

Tide-station behavior belongs in the backend wrapper or engine adapter, not in the frontend. The frontend should only display `tide_verification.status`, `station_distance_km`, source label, and confidence factors returned by the backend.

## Open Questions

- Whether the first frontend should be built as a static React app with a Python API server, or as a full-stack web app with API routes.
- Whether demo mode should call the combined endpoint only, or expose candidate selection immediately.
- Whether the first map should be omitted, read-only, or selectable.
- Whether TidesAtlas should stay disabled in frontend demos until quota is safer.
- What station-distance threshold should be used for "nearby" versus "remote" station display outside the current backend default.
