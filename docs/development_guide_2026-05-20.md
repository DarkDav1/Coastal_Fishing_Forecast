# Coastal Fishing Forecast Development Guide

Last updated: 2026-05-20  
Repository: `/Users/chenweic/dev/Fishing_Forcast/workspace-cocky/coastal-fishing-forecast`  
Audience: backend scoring work, frontend integration, algorithm tuning, and AI handoff  

## 1. Product Scope

This repository is the public generic coastal product. It is not the private high-confidence Derwent engine.

The product currently supports:

- Shore-based coastal fishing.
- Bays and sheltered inner-water locations.
- Estuaries, river mouths, and tidal river corridors.
- Harbours, public fishing access areas, jetties, rock edges, surf beaches, bay edges, and estuary edges.
- Low-cost forecasts for searched places, GPS points, and map-clicked coordinates.

The product does not currently support:

- Inland freshwater rivers.
- Inland lakes or reservoirs.
- Private Derwent-specific spot rules.
- Manual on-site observations such as birds, baitfish, surface bust-ups, water clarity, or local angler reports.
- Direct fish-score boosts from nearby access pins, jetties, parking, boat ramps, or public map structures.

Core rules:

- A searched coordinate is not a curated hotspot. Scores must stay conservative unless the evidence is strong.
- Fish potential and trip reality must be shown separately.
- Access and structure data helps the user find where to fish. It must not raise the fish score.
- Tide height is not current. Sea-level movement is only a low-cost proxy for current.
- Water temperature is a first-class scoring input, not a small side adjustment.
- High scores require several independent signals to align.

## 2. Local Setup

### 2.1 Python environment

```bash
cd /Users/chenweic/dev/Fishing_Forcast/workspace-cocky/coastal-fishing-forecast
python3 -m venv .venv
./.venv/bin/python -m pip install -e .
```

Use the repository-local `.venv`. System Python can fail on managed-environment restrictions.

### 2.2 API server

```bash
cd apps/web
npm run api
```

The API server listens on:

```text
http://127.0.0.1:8787
```

The Node API server wraps the Python CLI commands from the repository root. The `.venv` must exist before this server can work.

### 2.3 Frontend dev server

```bash
cd apps/web
npm run dev
```

Vite normally starts on:

```text
http://127.0.0.1:5173/
```

If the port is already in use, Vite uses another nearby port. In current local runs, the app is often available at:

```text
http://127.0.0.1:5176/
```

Startup order:

1. Start `npm run api`.
2. Start `npm run dev`.
3. Open the Vite URL in the in-app browser.
4. Search for places such as `Sandy Bay Tasmania`, `Port Huon Tasmania`, or `Binalong Bay Tasmania`.

## 3. Required Verification Commands

### 3.1 Full Python test suite

```bash
./.venv/bin/python -m unittest discover -s tests -v
```

Current baseline: 236 tests passing.

### 3.2 Frontend production build

```bash
cd apps/web
npm run build
```

### 3.3 Python syntax check

```bash
./.venv/bin/python -m py_compile \
  coastal_fishing_forecast/preview.py \
  coastal_fishing_forecast/forecast.py \
  coastal_fishing_forecast/api.py
```

### 3.4 Engine verification command

```bash
./.venv/bin/coastal-verify
```

### 3.5 Direct coordinate preview

```bash
./.venv/bin/coastal-preview -42.8991036 147.3389916
```

### 3.6 Frontend-shaped API response

```bash
./.venv/bin/coastal-api-forecast -42.8991036 147.3389916 \
  --start-date 2026-05-20 \
  --end-date 2026-05-20 \
  --region sheltered_estuary \
  --windows morning,day,dusk \
  --condition-source forecast \
  --tide-source openmeteo_model
```

## 4. Repository Map

```text
coastal_fishing_forecast/
  preview.py              Core single-coordinate scoring, support checks, waterbody classification, fish and trip scores.
  forecast.py             Hourly, windowed, and multi-day forecast orchestration.
  api.py                  Frontend response assembly.
  search_forecast.py      Place search plus forecast composition.
  conditions.py           Open-Meteo weather and marine fetching and normalization.
  tides.py                Tide events, tide phase, and model tide handling.
  tidesatlas.py           Optional TidesAtlas integration.
  structures.py           Access and structure map reference layer.
  planner.py              Action-plan wording.
  score_factors_llm.py    Score-factor payloads and rule-based fallback.
  feedback.py             User outcome feedback recording.
  feedback_analysis.py    Feedback replay and bias summaries.

apps/web/
  server/api-server.mjs   Node API server that calls Python CLI tools.
  src/App.tsx             Main page, score presentation, charts, and weather visuals.
  src/api.ts              Frontend API client.
  src/types.ts            Frontend response types.
  src/styles.css          UI styles.

tests/
  test_preview.py         Core engine and algorithm regression tests.
  test_forecast.py        Multi-day forecast, tide, and weather data paths.
  test_cache_and_api.py   Frontend API shape and cache behavior.
  test_safety_comfort_split.py  Fish, comfort, safety, and trip-score split.
  test_combo_release.py   Strong-signal alignment and high-score release.
  test_structures.py      Access and structure map layer.
  test_feedback*.py       User feedback and calibration analysis.
```

## 5. End-to-End Forecast Flow

When a user searches for a place:

1. The frontend calls `/api/search-forecast`.
2. The Node server calls `coastal-search-forecast`.
3. The Python search layer resolves the place name into candidate coordinates.
4. The backend chooses the candidate that best matches coastal or tidal-water relevance.
5. `build_range_forecast` loads weather, marine, tide, solar, moon, and geometry inputs.
6. Each representative hour calls `build_preview`.
7. `build_preview` checks support status, classifies the waterbody, normalizes environmental input, and scores the point.
8. `build_frontend_forecast_response` converts raw scoring output into page-ready data.
9. The React app renders the hero score, map, curves, day overview, score factors, and weather visual cards.

Simplified flow:

```text
Search text
  -> place candidates
  -> selected coordinate
  -> weather / marine / tide / solar / moon / geometry
  -> waterbody classification
  -> hourly preview scoring
  -> daily forecast response
  -> React UI
```

## 6. External Data Sources

### 6.1 Open-Meteo weather

Used for:

- Air temperature.
- Wind speed.
- Wind direction.
- Wind gust.
- Surface pressure.
- Rain.
- Precipitation.
- Cloud cover.
- Sunrise and sunset.

Requirements:

- Wind speed must be requested in knots.
- Timezone must be `Australia/Hobart` for Tasmania examples.
- Forecast mode needs lookback context for weather shock and trend detection.

### 6.2 Open-Meteo marine

Used for:

- Wave height.
- Wave period.
- Swell wave height.
- Swell wave direction.
- Sea surface temperature.
- Sea-level height above mean sea level.

Requirements:

- Use `cell_selection=sea` where possible.
- Live forecasts should request one extra day beyond the selected date range so tide-event inference has enough sea-level data near the day boundary.
- `sea_level_height_msl` is a model sea-level curve. It is useful, but it is not a verified local tide station and not a direct current prediction.

### 6.3 TidesAtlas

Optional environment variable:

```bash
export TIDESATLAS_API_KEY="..."
```

Used for:

- Real tide events.
- Better tide verification.
- Lower uncertainty than Open-Meteo sea-level-only tide inference.

The app still works without this key. Without it, tide and current confidence is lower.

### 6.4 Mapbox

Optional environment variable:

```bash
export MAPBOX_ACCESS_TOKEN="..."
```

Used for:

- Place search.

Without this key, the app can use Nominatim.

### 6.5 GitHub Models

Optional environment variable:

```bash
export GITHUB_TOKEN="..."
```

Used for:

- Score-factor wording.
- Planner wording.

Rules:

- The model is never allowed to change scores.
- The model is never allowed to remove tide-source warnings.
- The model is never allowed to claim unverified structures, private places, or exact local knowledge.
- If the model fails, the app falls back to deterministic rule-based copy.

## 7. API Input Audit

The fish index is not returned by an external API. It is calculated internally:

```text
fish_outlook_score = 0.55 * activity_score + 0.45 * presence_score
```

Core inputs:

| Input | Source | Use |
| --- | --- | --- |
| `temperature_c` | Open-Meteo weather | Weather shock, comfort, cold or warm pressure around the fish score. |
| `wind_speed_knots` | Open-Meteo weather | Wind fit, trip reality, and exposed-water penalties. |
| `wind_direction_deg` | Open-Meteo weather | Compared with open-water bearing. |
| `wind_gust_knots` | Open-Meteo weather | Safety and comfort. |
| `pressure_hpa` | Open-Meteo weather | Stability and weather shock. |
| `rain_mm` / `precipitation_mm` | Open-Meteo weather | Current rain and recent disturbance. |
| `cloud_cover_pct` | Open-Meteo weather | Light cover. |
| `wave_height_m` | Open-Meteo marine | Sea state, risk, and trip reality. |
| `swell_height_m` | Open-Meteo marine | Exposed-coast risk and trip reality. |
| `swell_direction_deg` | Open-Meteo marine | Compared with open-water bearing. |
| `sea_surface_temperature_c` | Open-Meteo marine | Water temperature layer. |
| `sea_level_height_msl` | Open-Meteo marine | Tide height and tide-event inference. |
| `sunrise` / `sunset` | Open-Meteo daily | Dawn, dusk, and daylight timing. |
| Moon phase | Internal astronomy calculation | Weak supporting signal. |
| Coastline sampling | `global_land_mask` and local sampling | Waterbody type and exposure. |

Derived inputs:

- `tide_phase`
- `tide_stage`
- `tide_range_m`
- `tide_height_m`
- `tide_movement_rate_m_per_hour`
- `tide_current_confidence`
- `current_strength_proxy`
- `water_temperature_signal`
- `water_temperature_trend`
- `temperature_confidence`
- `weather_shock_score`
- `open_water_bearing_deg`
- `wind_to_shore_relationship`
- `swell_to_shore_relationship`

## 8. Waterbody Classification

Output fields:

- `waterbody_class`
- `classification_confidence`
- `classification_reasons`
- `manual_region_override`
- `effective_region`

Supported classes:

| Class | Meaning |
| --- | --- |
| `open_coast` | Open coastline. |
| `surf_coast` | Surf-exposed coastline. |
| `bay_coast` | Bay shoreline. |
| `sheltered_estuary` | Sheltered estuary or inner bay. |
| `river_mouth` | River mouth. |
| `tidal_river` | Tidal river corridor. |
| `harbour_access` | Harbour or access-heavy water. |
| `unsupported` | Not supported by the product. |

Classification should mainly use geographic sampling, not the place name:

- Inner water fraction.
- Mid water fraction.
- Outer water fraction.
- Coastline complexity.
- Open-water bearing.
- Exposure.
- Shelter.
- Nearest-water distance.
- Narrow tidal corridor evidence.

Place names, OSM types, and Nominatim categories are weak evidence only.

Acceptance examples:

- Sandy Bay should not be classified as open coast.
- Port Huon should land near `river_mouth` or `sheltered_estuary`.
- Binalong Bay should land near `open_coast` or `surf_coast`.

## 9. Water Temperature Layer

Primary input:

```text
sea_surface_temperature_c
```

Output fields:

- `water_temperature_signal`
- `water_temperature_trend`
- `temperature_confidence`
- `sea_surface_temperature_delta_24h`
- `sea_surface_temperature_delta_72h`

Rules:

- If water temperature is missing, lower confidence. Do not guess.
- Cold water should prevent an unrealistically high score even if tide timing is good.
- Stable in-range water can improve presence.
- Rapid cooling or unusual warming should appear in the challenge factors.
- Different fish profiles should use different temperature thresholds.

Current internal profiles:

- `generic_estuary`
- `flathead`
- `bream_estuary`
- `salmon_pelagic`
- `mulloway`
- `rocks_reef`

The default profile is selected from `waterbody_class`. If the user has not selected a target fish, keep the generic profile conservative.

## 10. Tide and Current

Tide-data priority:

1. Tide events supplied by the caller.
2. TidesAtlas.
3. Open-Meteo marine `sea_level_height_msl`.
4. Coarse astronomical approximation.

Important fields:

- `tide_phase`
- `tide_stage`
- `tide_range_m`
- `tide_height_m`
- `tide_movement_rate_m_per_hour`
- `tide_current_confidence`
- `current_strength_proxy`
- `current_source_note`
- `hours_to_high_tide`
- `hours_to_low_tide`
- `hours_since_low_tide`

Product rules:

- Low tide itself is not automatically good.
- Low-tide slack should not score high.
- The period after low tide, when water starts moving, can score better.
- Early flood, stable ebb, and good light can become strong only when they align with other signals.
- Open-Meteo sea-level curves usually mean lower current confidence.
- Low-confidence current must not push a score to 70+ by itself.

## 11. Scoring Layers

### 11.1 Activity score

Meaning:

```text
Are fish more likely to feed during this time window?
```

Main inputs:

- Dawn, dusk, and daylight.
- Tide stage.
- Tide movement.
- Weather shock.
- Rain and cloud cover.
- Pressure trend.
- Water temperature.
- Fish profile.

Common positive factors:

- First light or last light.
- Water starting to move.
- Stable in-range water temperature.
- Light cover or light rain.
- Several independent signals aligning.

Common negative factors:

- Slack water.
- Strong weather shock.
- Rapid cooling.
- Cold water.
- Harsh daylight when other signals are weak.

### 11.2 Presence score

Meaning:

```text
Are fish more likely to be near this waterbody or shoreline?
```

Main inputs:

- Waterbody class.
- Real waterbody geometry.
- Bay, estuary, channel, harbour, or open-coast context.
- Water temperature stability.
- Wave, swell, and exposure.
- Recent rain and estuary disturbance.

Forbidden scoring inputs:

- Number of nearby access pins.
- Distance to a public jetty.
- Parking, boat ramps, or map access features.
- OSM structure data as a direct fish-score boost.

### 11.3 Fish potential

Frontend label:

```text
Fish potential
```

Calculation:

```text
fish_outlook_score = 0.55 * activity_score + 0.45 * presence_score
```

Meaning:

```text
Fish signal before comfort and safety.
```

### 11.4 Comfort score

Meaning:

```text
How comfortable are the weather and conditions for a person fishing from shore?
```

Main inputs:

- Air temperature.
- Wind speed.
- Gusts.
- Rain.
- Precipitation.
- Wave height.
- Swell height.

### 11.5 Safety flag

Possible values:

- `low`
- `moderate`
- `elevated`
- `hazardous`

Main inputs:

- Gusts.
- Wave height.
- Swell height.
- Exposed waterbody class.
- Wind and swell relationship to the coast.
- Cold, wet, and windy combinations.

### 11.6 Trip reality

Frontend label:

```text
Trip reality
```

Backend field:

```text
trip_quality_score
```

Current definition:

```text
trip_quality_score = comfort_score, then capped by safety_flag
```

Safety caps:

| Safety flag | Trip reality cap |
| --- | ---: |
| `low` | no cap |
| `moderate` | 70 |
| `elevated` | 55 |
| `hazardous` | 35 |

Rules:

- Trip reality must not be lowered by weak fish activity, weak tide movement, or poor bite timing.
- If weather is comfortable, wind and swell are manageable, and broad safety risk is low, trip reality should be high.
- The old mixed fish/time/tide trip score is kept internally as `fish_window_trip_score` for debugging and selection context.

### 11.7 Overall score

The large hero score is a product-level summary. It is not pure fish potential.

Rules:

- If fish potential is low, the overall score must not pretend the fish signal is strong.
- If trip reality is high, the UI can say the day is comfortable for a short try, but not that fish are likely.
- If safety is `elevated` or `hazardous`, the trip recommendation must be suppressed even when fish potential is high.
- 80+ should appear only when tide movement, timing, water temperature, wind, swell, and weather stability strongly align.

## 12. High-Score Release and False-High Guards

High scores require multiple aligned signals:

- Suitable waterbody type.
- Suitable light window.
- Clear moving water.
- Stable or suitable water temperature.
- Wind and swell not excessive for the class.
- No major weather shock.
- Tide/current confidence not too low.

Common caps:

- Dead water.
- Weather shock.
- Cold water.
- Rapid cooling.
- Large swell on exposed coast.
- Hazardous safety.
- Unsupported or low-confidence coordinate.
- Low current confidence in river mouths or tidal rivers.

Target distribution:

- Most ordinary days: 40 to 65.
- Usable windows: 60 to 70.
- 70+: clear evidence required.
- 80+: strong alignment only.

## 13. Structure and Map Layer

The structure layer is map context and planning help. It is not fish-score evidence.

It can display:

- Public fishing access.
- Official fishing spots.
- Public jetties.
- Boat ramps.
- Beach access.
- Rocky shoreline.

It must not:

- Raise fish score because many access pins are nearby.
- Claim more fish because a nearby jetty exists.
- Treat a private pier as public fishing access.
- Treat a boat ramp as a shore-fishing recommendation by default.

Real waterbody attributes can affect scoring:

- Channel edge.
- Mudflat.
- Sandflat.
- Weed or seagrass.
- Reef or rock edge.
- Estuary mouth.
- Open beach exposure.

## 14. Frontend Display Contract

Main frontend type file:

```text
apps/web/src/types.ts
```

### 14.1 Hero

The hero should show:

- Main score.
- Recommendation label.
- `Fish potential`.
- `Trip reality`.
- Water type.
- Short plan summary.

The user should understand these cases:

- Fish may be present, but today is not comfortable or safe.
- Conditions are pleasant, but fish signal is ordinary.
- Tide timing is good, but water temperature or weather shock is holding the score down.

### 14.2 Day overview

Recommended cards:

- Fish outlook.
- Water movement.
- Water temperature.
- Weather comfort.
- Waves and safety.

Water temperature must be visible as its own explanatory card. It should not be hidden inside comfort.

### 14.3 Score factors

Left column:

```text
What's helping
```

Only show real positive factors.

Right column:

```text
What's challenging
```

Only show real negative factors.

Rules:

- Do not write conclusion-only text such as "the day is not a high-score day."
- Explain why the score is where it is.
- Do not use semicolons in score-factor text.
- Do not turn missing data into a confident statement.
- If no obvious challenge appears, check weak current, cold water, weather shock, harsh light, low tide/current confidence, wind, wave, and swell before saying there are no negatives.

### 14.4 Weather visual

Current modules:

- Wind map.
- Wind speed.
- Tide height.
- Wave height.
- Swell height.

Requirements:

- Prefer the Windy iframe when it loads.
- If the iframe is blocked, show the fallback without breaking the curves below it.
- Curves must use the same hourly data as the score.
- The y-axis must sit cleanly inside the chart shell without overlapping the plot.
- The final x-axis label `23` must not be clipped.
- Wind, tide, wave, and swell units must be clear.

## 15. Frontend API Fields

Top-level fields:

- `status`
- `query`
- `selected_place`
- `forecast`
- `plan`

`forecast.hero` fields:

- `score`
- `label`
- `fish_outlook_score`
- `comfort_score`
- `trip_quality_score`
- `safety_flag`
- `waterbody_class`
- `classification_confidence`
- `fish_profile`
- `headline`
- `best_window`

Important `WindowCard` fields:

- `score`
- `activity_score`
- `presence_score`
- `fish_outlook_score`
- `comfort_score`
- `trip_quality_score`
- `safety_flag`
- `waterbody_class`
- `classification_confidence`
- `classification_reasons`
- `fish_profile`
- `conditions.wind`
- `conditions.swell`
- `conditions.marine`
- `conditions.tide`
- `conditions.solar`
- `conditions.moon`

Important `HourlyActivityPoint` fields:

- `score`
- `activity_score`
- `presence_score`
- `fish_outlook_score`
- `comfort_score`
- `trip_quality_score`
- `safety_flag`
- `tide_phase`
- `tide_stage`
- `tide_height_m`
- `tide_movement_rate_m_per_hour`
- `tide_current_confidence`
- `current_strength_proxy`
- `wind_speed_knots`
- `wave_height_m`
- `swell_height_m`
- `sea_surface_temperature_c`
- `water_temperature_signal`
- `water_temperature_trend`
- `temperature_confidence`
- `waterbody_class`
- `fish_profile`

## 16. Development Workflows

### 16.1 Changing scores

1. Decide whether the change belongs to fish potential, trip reality, comfort, safety, or overall score.
2. Find the related scoring function in `preview.py`.
3. Add or update tests, usually in `test_preview.py` or `test_safety_comfort_split.py`.
4. Run the targeted test.
5. Run the full test suite.
6. Open the frontend and inspect the visible rendered score.

Minimum verification:

```bash
./.venv/bin/python -m unittest tests.test_safety_comfort_split -v
./.venv/bin/python -m unittest tests.test_preview -v
./.venv/bin/python -m unittest discover -s tests -v
```

### 16.2 Adding API fields

1. Preserve the raw input or derived value in `preview.py` or `forecast.py`.
2. Pass the value through `api.py`.
3. Add the type in `apps/web/src/types.ts`.
4. Use the field in `App.tsx`.
5. Add field-presence coverage in `test_cache_and_api.py`.
6. Build the frontend.

Minimum verification:

```bash
./.venv/bin/python -m unittest tests.test_cache_and_api -v
cd apps/web && npm run build
```

### 16.3 Changing UI

1. Confirm the API field exists.
2. Update `App.tsx` and `styles.css`.
3. Run `npm run build`.
4. Inspect both desktop and mobile widths in the browser.
5. Check browser console errors.

Acceptance checks:

- Sandy Bay renders.
- Port Huon renders.
- Date switching keeps weather visual working.
- Score factors match the visible score.
- Charts are not clipped or overlapping.

### 16.4 Changing data sources

1. Do not trust third-party field units without checking them.
2. Add new fields to the audit docs or test fixtures.
3. Check both live fetch and cached fetch.
4. Missing data must lower confidence, not trigger fake estimates.
5. If a provider is paid or quota-limited, preserve a low-cost fallback.

## 17. Golden Cases

Large tuning changes should be checked against these cases:

| Case | Purpose |
| --- | --- |
| Sandy Bay | Inner bay or bay coast. It should not be treated as open coast. |
| Port Huon | River mouth or sheltered estuary. Freshwater disturbance, water temperature, and current confidence matter more than open-coast wave height. |
| Binalong Bay | Open coast or surf coast. Swell, wind, and safety should matter strongly. |
| Harbour access | Access should help mapping but should not raise fish score. |
| Slack tide | Low-tide or high-tide slack should not score high. |
| Early flood | The period after low tide when water begins to move can score better. |
| Strong aligned day | 70+ or 80+ is allowed when several signals align. |
| Cold-water day | Cold water must prevent false highs. |
| Warm-stable day | Stable in-range water can improve presence. |
| Bad weather | Fish potential may remain high, but trip reality and recommendation must be limited by safety. |

Record for each golden case:

- Coordinates.
- Waterbody class.
- Classification confidence.
- API inputs.
- Tide stage.
- Current confidence.
- Water temperature signal.
- Fish potential.
- Trip reality.
- Safety flag.
- Score factors.
- Visible UI result.

## 18. Feedback and Calibration

Outcome feedback should include:

- Place.
- Coordinates.
- Date and time.
- Target fish.
- Method.
- Catch or no catch.
- Count and rough size class.
- Water clarity.
- Perceived water temperature.
- Notes.
- Prediction score and key prediction fields at the time.

Do not rush into machine learning.

Correct calibration flow:

1. Collect feedback.
2. Replay and aggregate outcomes.
3. Find overpredicted and underpredicted examples.
4. Tune rules manually.
5. Add regression cases.
6. Consider model-based tuning only after enough feedback exists.

## 19. Known Limitations

- Tide current still mostly uses sea-level curve proxy data. It is not real horizontal current speed.
- Water-temperature profiles are V1 and need more observed outcome data.
- Estuary freshwater, salinity, and turbidity are still proxies. Real river flow and water-quality data would improve Port Huon-style locations.
- Habitat data is still coarse. Channel edge, weed bed, reef edge, and depth-break layers need better sources.
- The Windy iframe can be blocked by browser or third-party restrictions. A fallback must remain.
- Searched coordinates are inherently lower confidence than curated hotspots.

## 20. Near-Term Development Priorities

1. Improve current-aware tide scoring with real current data or station lag calibration.
2. Improve estuary water-quality proxy with recent rain, river flow, and disturbance recovery.
3. Expand target-family profiles for flathead, bream, salmon, mulloway, and rocks or reef fishing.
4. Build a golden-case dashboard for Sandy Bay, Port Huon, Binalong Bay, and other fixed samples.
5. Expand feedback replay by waterbody class, safety flag, and temperature signal.
6. Continue improving visible explanations so the user sees the actual reason for score loss.

## 21. Related Documents

- `docs/current_engine_algorithm_full_2026-05-07.md`
- `docs/fish_index_algorithm_literature_review_2026-05-20.md`
- `docs/fish_index_api_input_audit_2026-05-20.md`
- `docs/frontend_api_contract_2026-04-27.md`
- `docs/tide_data_sources_2026-04-27.md`
- `docs/engine_verification_path_2026-04-27.md`
- `docs/structure_facility_layer_plan_2026-04-28.md`
- `docs/feedback_schema_v1_2026-05-07.md`

## 22. Handoff Checklist

Before handing the work to another session, confirm:

- Full Python test suite passes.
- Frontend build passes.
- Sandy Bay page opens.
- Port Huon page opens.
- Fish potential and trip reality are shown separately.
- Access and structure data does not affect fish score.
- Water temperature appears in day overview and score factors.
- Low-confidence tide/current cannot create a high score by itself.
- Wave and swell both affect trip reality and safety.
- Score factors put positive reasons on the left and negative reasons on the right.
- Copy does not make overconfident claims from unverified data.

