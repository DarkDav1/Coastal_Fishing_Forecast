# Frontend API Contract (2026-04-27)

This contract is for a standalone generic forecast frontend.

It is separate from the raw engine payload. The goal is to give the UI page-ready data while still preserving the raw forecast for debugging.

## Command

```bash
./.venv/bin/coastal-api-forecast -41.2530 148.3060 \
  --start-date 2026-04-20 \
  --end-date 2026-04-21 \
  --region open_coast \
  --windows morning,dusk \
  --condition-source archive
```

## Response shape

Top-level fields:

- `api_contract_version`
- `forecast_contract_version`
- `input`
- `location`
- `data_sources`
- `tide_verification`
- `confidence`
- `hero`
- `plan`
- `explanation`
- `summary`
- `daily_forecast`
- `modules`
- `raw_forecast`

Future map and structure layers should be returned separately from the core forecast unless they are summarized into a forecast explanation. The planned structure-layer contract is:

- `docs/structure_facility_layer_plan_2026-04-28.md`

## Hero

The hero block is designed for the top of the page:

```json
{
  "score": 53,
  "label": "Usable nearby options",
  "headline": "Beach is the strongest nearby option.",
  "best_window": {}
}
```

Frontend use:

- large score / label
- one-line recommendation
- best time window callout
- confidence/source warning from `data_sources`

## Fishing Plan

The `plan` block turns the structured forecast into an action checklist. It does not change engine scores, best window, support status, confidence label, or tide verification.

```json
{
  "contract_version": "2026-04-28.fishing_plan.v1",
  "source": "rule_based",
  "planner_provider": "rule_based",
  "recommendation": {
    "label": "maybe",
    "score": 54,
    "summary": "There are usable nearby options, but keep a backup plan."
  },
  "primary_action": {
    "time_window": "morning",
    "water_type": "beach",
    "behavior_group": "Beach roaming fish",
    "score": 54,
    "text": "try the beach signal during morning first."
  },
  "backup_action": {
    "water_type": "Estuary edge",
    "score": 56,
    "text": "Backup option: consider Estuary edge if the first choice looks poor on arrival."
  },
  "avoid": [],
  "risks": [],
  "confidence_note": "Medium confidence with caution: tide phase uses model sea-level data, not a verified local tide station.",
  "data_source_note": "Tide data came from Open-Meteo model sea-level data, not a local station."
}
```

Planner providers:

- `rule_based`: default deterministic fallback
- `github_models`: uses GitHub Models for wording only, with rule-based fallback
- `llm`: generic alias that currently attempts the same model-backed path, then falls back

Frontend use:

- Map tab: show `recommendation`, `primary_action`, and confidence note
- Conditions tab: show `risks`, `avoid`, and data-source note
- Fish tab: use `primary_action.behavior_group`; do not infer species probabilities

## Location

The engine does not resolve place names.

Response:

```json
{
  "display_name": "-41.2530, 148.3060",
  "source": "coordinate_input",
  "coordinates": {"latitude": -41.253, "longitude": 148.306}
}
```

Future place-name search or reverse geocoding should live in a separate resolver outside the engine. The resolver can pass coordinates into this API.

The current resolver contract is documented in:

- `docs/place_search_contract_2026-04-28.md`

The combined search-to-forecast command is:

```bash
./.venv/bin/coastal-search-forecast "Binalong Bay Tasmania" --provider nominatim --start-date 2026-04-20 --end-date 2026-04-20
```

## Confidence

The confidence block is for product display:

```json
{
  "score": 73,
  "label": "medium",
  "factors": [
    "Searched-coordinate forecast, not a curated hotspot.",
    "Coordinate is near supported coastal or tidal water.",
    "Weather and marine conditions are loaded from an external provider.",
    "Tide phase is based on real high/low tide events."
  ]
}
```

Rules:

- searched-coordinate previews are capped below high confidence
- real tide events improve confidence
- estimated tide lowers confidence
- on-water support is stronger than near-water support

## Tide Verification

The tide verification block prevents estimated tides from being mistaken for real tide data:

```json
{
  "status": "provided_events",
  "source": "tide_events",
  "message": "Real tide events were supplied to the engine."
}
```

Possible statuses:

- `live_verified`
- `live_verified_remote_station`
- `provided_events`
- `model_estimated`
- `estimated`

When the status is `live_verified_remote_station`, the frontend should show a caution that the tide station is not local to the searched coordinate.

When the status is `model_estimated`, the frontend should show that tide phase comes from model sea-level data, not a verified local tide station.

For GPS-based forecasts, the backend should use the user's coordinates to select the nearest available real tide / hydrology station when a real tide provider is enabled. The frontend should not choose stations directly. It should display the backend's tide status, source, and station distance when returned.

## Daily cards

`daily_forecast` is the main mobile and desktop card feed.

Each day includes:

- `date`
- `best_window`
- `windows`

Each window includes:

- `date`
- `time_window`
- `representative_time`
- `status`
- `score`
- `label`
- `dominant_water_type`
- `water_type_scores`
- `expanded_water_types`
- `behavior_groups`
- `conditions`

## Expanded Water Types

The raw engine still uses the stable broad buckets:

- `beach`
- `rocks`
- `jetty`
- `bay_estuary_edge`

The frontend API derives more product-friendly water types:

- `surf_beach`
- `open_rocks`
- `jetty_wharf`
- `bay_edge`
- `estuary_edge`
- `channel_edge`

These are marked as derived. They are useful for UI copy and cards, but should not yet be treated as confirmed mapped features.

## Behavior Groups

Behavior groups give the frontend a fish-behavior layer without over-claiming species certainty:

- `beach_roaming_fish`
- `estuary_resident_fish`
- `structure_fish`
- `rock_edge_fish`

These are generic opportunity groups, not exact species predictions.

## Explanation

The explanation block is designed for user-facing reasoning:

```json
{
  "why_this_window": [
    "morning has the strongest overall score in this forecast range.",
    "beach is the leading broad water-type signal.",
    "Beach roaming fish is the strongest fish-behavior group."
  ],
  "risks": [
    "Tide phase is estimated, so tide-sensitive guidance has lower confidence."
  ],
  "alternatives": [
    {"label": "Estuary edge", "score": 56, "reason": "Secondary inferred water type to consider nearby."}
  ]
}
```

Frontend use:

- explain why a window is recommended
- show broad risks without over-claiming certainty
- present backup water-type options

## Conditions

Each window contains compact weather, marine, and tide data:

```json
{
  "wind": {"speed_knots": 8.0, "direction_deg": 330},
  "swell": {"height_m": 0.5, "direction_deg": 46},
  "pressure_hpa": 1018.7,
  "tide": {"phase": "rising", "source": "openmeteo_model"}
}
```

Frontend use:

- wind chip
- swell chip
- tide chip
- pressure chip
- warning badge if tide source is `astronomical_approximation`
- model tide badge if tide source is `openmeteo_model`
- station-distance badge if `tide_verification.station_distance_km` is present

## Module flags

`modules` tells the frontend what surfaces can be rendered:

```json
{
  "recommendation": true,
  "daily_cards": true,
  "window_cards": true,
  "weather": true,
  "marine": true,
  "tide": true,
  "map": false,
  "plan": true,
  "expanded_water_types": true,
  "behavior_groups": true,
  "confidence": true,
  "explanation": true
}
```

The map flag is currently false because this engine does not yet return geometry, contours, or tile overlays.

When structure facilities are added, `modules.map` can become true for a frontend that supports marker layers. Structure markers should remain source/confidence annotated and should not imply curated fishing certainty.

## Cache

External weather, marine, and TidesAtlas API responses are cached by default.

CLI controls:

```bash
--no-cache
--cache-dir .cache/coastal_fishing_forecast
```

Environment override:

```bash
COASTAL_FORECAST_CACHE_DIR=/path/to/cache
```

Archive weather data is cached without a time expiry. Forecast data is cached with a short expiry.

## UI Content References

The frontend should combine:

- a compact recommendation summary
- daily cards
- time-window cards
- wind, swell, tide, pressure chips
- optional maps later
- clear data-source labels

Reference patterns:

- Surfline spot pages emphasize tide, swell, surf, wind, colored rating, and daily summaries.
- BoM MetEye marine guidance emphasizes wind, waves, swells, rainfall, weather, temperature, and map/time playback.
- PredictWind emphasizes a dashboard/table approach across wind, wave, rain, ocean data, tide/current, maps, graphs, and alerts.

Useful references:

- https://support.surfline.com/hc/en-us/articles/13749782983579-Understanding-the-Spot-Forecast-Page-on-the-Surfline-Website
- https://support.surfline.com/hc/en-us/articles/5291001325595-Understanding-the-Live-and-Forecast-tabs-on-the-Surfline-iOS-App
- https://www.bom.gov.au/marine/knowledge-centre/meteye.shtml
- https://www.predictwind.com/apps/predictwind-app

## Product Rules

- Do not present searched-coordinate output as a curated local hotspot.
- Show lower confidence when the tide source is estimated.
- Prefer "best window" and "best water type" over false exactness.
- Treat expanded water types and behavior groups as derived guidance, not confirmed spot features.
- Keep raw forecast available behind a debug panel, not as primary UI copy.
