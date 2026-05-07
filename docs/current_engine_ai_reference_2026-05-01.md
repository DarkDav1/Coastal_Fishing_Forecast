# Current Generic Coastal Engine AI Reference

Updated: 2026-05-01  
Project: `/Users/chenweic/dev/Fishing_Forcast/workspace-cocky/coastal-fishing-forecast`  
Scope: generic coastal saltwater and tidal/estuary forecast engine only.

This document is for another AI or engineer taking over the current engine. It explains what the engine does, how the score is built, what external data it uses, which rules are deliberately conservative, and where future tuning should happen.

## 1. Hard Boundary

This repo is the generic public coastal product track.

Do not mix this with the personal Derwent engine:

- Generic coastal repo: `/Users/chenweic/dev/Fishing_Forcast/workspace-cocky/coastal-fishing-forecast`
- Personal Derwent repo: `/Users/chenweic/dev/Fishing_Forcast/workspace-cocky/fishing-forecast`

The current generic engine borrows the shape of the older Derwent rule system, but it intentionally removes named Derwent spots, Derwent-only species logic, and curated local certainty.

The generic engine should remain:

- coastal saltwater
- tidal/estuary water
- searched-coordinate preview
- lower confidence than curated hot spots
- explicit about unsupported inland/lake locations

It should not silently become:

- a freshwater trout engine
- an inland river/lake engine
- a Derwent-specific spot recommender
- a guaranteed catch predictor

## 2. Current Engine Entrypoints

There are four main product paths.

### 2.1 Raw Coordinate Preview

File: `coastal_fishing_forecast/preview.py`  
Function: `build_preview(lat, lon, environment=None, region=None)`

This is the core scoring engine. It accepts a latitude and longitude, optionally an environment block, and returns a low-confidence searched-coordinate forecast.

It does four things:

- validates coordinates
- rejects unsupported inland/non-tidal locations
- infers broad nearby water type from coastline geometry
- scores beach, rocks, jetty-style edge, and bay/estuary edge

### 2.2 Date-Range Forecast

File: `coastal_fishing_forecast/forecast.py`  
Function: `build_range_forecast(...)`

This wraps `build_preview` across dates and windows.

It loads or accepts:

- hourly weather
- hourly marine data
- tide events or tide phase estimates
- sunrise/sunset
- moon phase approximation

It then scores:

- configured windows, currently `morning`, `day`, and `dusk`
- each hour of the forecast range for the 24-hour activity curve
- best hour inside each selected window

### 2.3 Frontend/API Response

File: `coastal_fishing_forecast/api.py`  
Function: `build_frontend_forecast_response(...)`

This converts raw engine output into a frontend-friendly payload:

- hero score
- daily forecast cards
- best window card
- hourly activity strip
- weather/marine/tide condition strip
- confidence block
- explanation block
- action plan
- optional public structure map data
- read-only social pulse context

### 2.4 Search-To-Forecast

File: `coastal_fishing_forecast/search_forecast.py`  
Function: `build_search_forecast_response(query, ...)`

This is the normal user flow:

1. User searches a place name.
2. Place provider returns candidate coordinates.
3. Each candidate is checked with `build_preview`.
4. The best supported coastal/tidal candidate is selected.
5. The selected coordinate is passed into the frontend forecast path.

The search step does not score fishing. It only resolves and ranks coordinates.

## 3. Output Contract Summary

The core preview output has:

- `status`: `ok`, `unsupported`, or `invalid_input`
- `support`: whether the coordinate is supported and why
- `overall_recommendation`: main forecast score and score layers
- `nearby_water_types`: inferred broad water-type cards
- `meta`: diagnostics, geometry signals, confidence, environment inputs, rule tags

The important score layers are:

- `activity_score`: fish activity signal
- `presence_score`: probability-like nearshore presence signal, still not a true probability
- `trip_quality_score`: human trip value, penalized hard by uncomfortable or unsafe weather
- `resident_opportunity_score`: holding/resident fish opportunity
- `roaming_opportunity_score`: moving/pelagic/roaming opportunity
- `big_fish_near_shore`: coarse `low`/`medium` label

The frontend-visible score is not always a direct raw activity score. The app's visible "today weighted score" is a weighted mix of activity, presence, and trip quality. Tune visible behavior against that final visible score, not just one internal field.

## 4. High-Level Data Flow

```text
Place search or coordinate input
        |
        v
Candidate coordinate
        |
        v
Land/ocean support check with global-land-mask
        |
        +--> unsupported if too far inland / non-tidal
        |
        v
Coastline ring sampling around coordinate
        |
        v
Broad water-type inference
        |
        v
Weather + marine + tide + sun + moon environment
        |
        v
Generic rule deltas
        |
        v
Water-type score cards
        |
        v
Activity / presence / trip / resident / roaming layers
        |
        v
Public-preview calibration and confidence labels
        |
        v
Frontend payload + action plan + optional map/social context
```

## 5. Location Support Logic

The support logic is intentionally conservative.

Files:

- `coastal_fishing_forecast/preview.py`
- dependency: `global-land-mask`

Key constants:

- `DIRECT_NEARBY_WATER_KM = 5.0`
- `EXTENDED_TIDAL_PREVIEW_KM = 8.0`
- `SEARCH_DISTANCES_KM = (0.5, 1.5, 3.0, 5.0, 8.0, 12.0, 20.0)`
- `ANALYSIS_RINGS_KM = (3.0, 8.0, 15.0)`
- bearings sampled every 30 degrees

The engine first checks if the point is ocean water. If not, it searches rings around the coordinate to find nearby water. This creates three possible supported modes:

- `on_water`: coordinate itself is ocean/coastal water
- `near_water`: coordinate is inland but within 5 km of supported water
- `tidal_corridor`: coordinate is 5-8 km from water, but nearby geometry looks sheltered/tidal enough to allow a cautious preview

Unsupported modes:

- `invalid_input`: invalid latitude/longitude
- `inland_or_non_tidal`: no water found in search rings
- `too_far_from_supported_water`: water exists but too far away or not a plausible tidal corridor

Important: inland and lake locations should be rejected clearly instead of returning fake low scores.

## 6. Coastline Geometry Signals

The engine does not know exact beaches, rocks, jetties, or estuary edges at the searched coordinate. It infers broad local water type from coastline shape.

The ring sampler computes:

- `inner_water_fraction`: water fraction at 3 km
- `mid_water_fraction`: water fraction at 8 km
- `outer_water_fraction`: water fraction at 15 km
- `coastline_complexity`: how often land/water state changes around the rings
- `open_water_bearing_deg`: coarse direction of open water
- `coastal_edge_signal`: high when the 8 km ring looks like a coast/edge
- `exposure`: roughly outer water fraction
- `shelter`: inverse of exposure
- `accessibility`: closer water means higher accessibility
- `search_confidence_score`: starts low and rises when the point is on/near water

These are broad approximations. They are not a GIS-grade shoreline normal, not bathymetry, and not a confirmed access map.

## 7. Water-Type Inference

File: `preview.py`  
Function: `_infer_type_signals`

The four base water types are:

- `beach`
- `rocks`
- `jetty`
- `bay_estuary_edge`

Current inference formulas:

```text
beach =
  0.50 * exposure
+ 0.30 * coastal_edge_signal
+ 0.20 * accessibility

rocks =
  0.40 * exposure
+ 0.35 * coastline_complexity
+ 0.25 * accessibility

jetty =
  0.35 * coastal_edge_signal
+ 0.30 * coastline_complexity
+ 0.20 * shelter
+ 0.15 * accessibility

bay_estuary_edge =
  0.45 * shelter
+ 0.35 * coastline_complexity
+ 0.20 * accessibility
```

These produce strengths in the 0-1 range.

Important behavior:

- Beach favors open exposure and obvious coast edge.
- Rocks favor exposure plus broken/complex coastline.
- Jetty is only a structure-style inference unless confirmed by map data.
- Bay/estuary edge favors sheltered but complex water.

The planner must not claim a real jetty or wharf from this inference alone.

## 8. Region Bias Layer

File: `coastal_fishing_forecast/regions.py`

The region config gently biases generic signals without creating named-spot logic.

Current regions:

- `generic_coastal`
- `open_coast`
- `sheltered_estuary`
- `surf_coast`
- `harbour_access`
- `bay_coast`

Each region can bias:

- beach strength
- rocks strength
- jetty strength
- bay/estuary strength
- tide movement effect
- shelter effect
- exposure effect

Use this layer for broad public-product behavior. Do not add local named spots here.

## 9. Environment Inputs

File: `preview.py`  
Dataclass: `EnvironmentInputs`

The scoring engine can consume:

- air temperature
- wind speed, direction, gusts
- recent maximum wind
- swell height and direction
- wave height
- 24-hour wave-height change
- sea surface temperature
- pressure
- 3-hour pressure delta
- precipitation/rain
- recent 12-hour precipitation
- cloud cover
- tide phase
- tide stage
- time to/from high/low tide
- tide range
- time window
- hour of day
- sunrise/sunset offsets
- solar noon offset
- daylight flag
- moon phase fraction
- moon phase name
- moon illumination

Defaults are intentionally neutral:

- wind: 12 knots
- swell: 1.0 m
- pressure: 1015 hPa
- tide phase: `mid`
- time window: `day`

If direction is missing, directional alignment defaults to neutral `0.5`, not fake onshore/offshore certainty.

## 10. Weather and Marine Data

File: `coastal_fishing_forecast/conditions.py`

Open-Meteo is the current no-key provider for weather and marine conditions.

Weather endpoint:

- forecast: `https://api.open-meteo.com/v1/forecast`
- archive: `https://archive-api.open-meteo.com/v1/archive`

Weather variables requested:

- `temperature_2m`
- `surface_pressure`
- `wind_speed_10m`
- `wind_direction_10m`
- `wind_gusts_10m`
- `precipitation`
- `rain`
- `cloud_cover`
- daily `sunrise`
- daily `sunset`

Marine endpoint:

- `https://marine-api.open-meteo.com/v1/marine`

Marine variables requested:

- `wave_height`
- `wave_period`
- `swell_wave_height`
- `swell_wave_direction`
- `sea_surface_temperature`
- `sea_level_height_msl`

The marine request uses `cell_selection=sea`, because this product needs marine grid cells rather than nearby land cells.

Open-Meteo official notes relevant to this engine:

- Weather forecast API accepts coordinates and returns JSON hourly forecast data.
- The weather docs define `surface_pressure`, 10 m wind speed/direction, and gusts.
- The marine API includes wave height, swell height/direction, sea surface temperature, and sea level height.
- Open-Meteo warns that model tide/current accuracy at coastal areas is limited and not suitable for navigation.

Sources:

- Open-Meteo Weather Forecast API: https://open-meteo.com/en/docs
- Open-Meteo Marine Weather API: https://open-meteo.com/en/docs/marine-weather-api

## 11. Tide Data Logic

Files:

- `coastal_fishing_forecast/tides.py`
- `coastal_fishing_forecast/tidesatlas.py`
- `coastal_fishing_forecast/forecast.py`

The engine can resolve tide in five ways:

1. Supplied inline tide events.
2. Tide events from JSON/CSV file.
3. TidesAtlas real tide events.
4. Open-Meteo `sea_level_height_msl` model-derived high/low events.
5. Coarse astronomical fallback.

### 11.1 Tide Event Format

Internally, tide events become:

```text
TideEvent(
  time=datetime,
  event_type="high" or "low",
  height_m=float | None
)
```

JSON and CSV importers normalize:

- time
- event type
- optional height in metres

### 11.2 Phase From Real Events

If high/low events exist:

- within 45 minutes of high: `high`
- within 45 minutes of low: `low`
- after low and before high: `rising`
- after high and before low: `falling`
- otherwise: `mid`

The engine also derives:

- `stage`: `flood`, `ebb`, `slack`, or `unknown`
- `hours_to_high_tide`
- `hours_to_low_tide`
- `hours_since_high_tide`
- `hours_since_low_tide`
- `tide_range_m` when adjacent event heights are known

### 11.3 Open-Meteo Tide Proxy

When `tide_source` is `auto` or `openmeteo_model`, and no real tide events are supplied, the engine tries to infer high/low events from the Open-Meteo marine `sea_level_height_msl` curve.

This is useful for low-cost development and public preview, but it is not a local station tide table.

The API response labels this as:

- `tide_verification.status = model_estimated`
- `tide_verification.source = openmeteo_model`

### 11.4 TidesAtlas

TidesAtlas is used only when explicitly selected with `tide_source="tidesatlas"` or CLI `--tide-source tidesatlas`.

Endpoint:

- `https://tidesatlas.com/api/v1/tides`

Auth:

- environment variable: `TIDESATLAS_API_KEY`
- or explicit API key argument

The adapter requests:

- `lat`
- `lon`
- `date`
- `days`
- `format=json`

The adapter normalizes `extremes` into high/low events and records returned port metadata. If the selected port/station is more than 50 km from the searched coordinate, the frontend confidence block reports `live_verified_remote_station`.

Source:

- TidesAtlas API docs: https://tidesatlas.com/en/api/docs

### 11.5 Astronomical Fallback

If no real or model tide events are available, the engine estimates a semidiurnal tide phase from:

- a fixed reference high water: `2026-01-01T00:00Z`
- half-cycle length: 6 h 12 m 30 s
- longitude offset

This exists so replay paths do not pin every forecast to the same tide. It must always be presented as low-confidence tide information.

## 12. Solar and Moon Logic

File: `forecast.py`

Solar context comes from Open-Meteo daily sunrise/sunset when available. If missing, it falls back to:

- sunrise: 06:15 local
- sunset: 18:00 local

The engine derives:

- `hours_from_sunrise`
- `hours_from_sunset`
- `hours_from_solar_noon`
- `is_daylight`

Moon phase is approximated internally:

- known reference new moon: 2000-01-06
- synodic month: 29.53058867 days
- fraction in lunar cycle
- illumination estimate from a cosine curve
- coarse phase names such as `new_moon`, `full_moon`, `first_quarter`, etc.

Current moon logic is light-touch:

- new/full moon adds a small major phase bonus
- new moon at night adds a dark-night bonus
- full moon at night adds a bright-night bonus
- moon phase stacks more strongly when it overlaps dawn/dusk or other good signals

The engine does not currently calculate true moonrise/moonset or lunar transit. It should not claim full solunar precision.

External reference context:

- Solunar-style fishing logic traditionally combines sun, moon, and tide as movement cues, but this engine only uses a simplified moon-phase layer, not a proprietary solunar table.
- Tides4Fishing-style products show that fishing users expect tide, weather, moon, pressure, and swell together; this engine uses that as product framing, not as copied proprietary scoring.

## 13. Generic Rule Delta Layer

File: `preview.py`  
Function: `_generic_derwent_rules`

This layer creates rule tags and a summed `score_delta`.

It is called "Derwent-style" because it borrows the successful rule categories from the personal engine, but it removes named local spot rules.

### 13.1 Positive Time Rules

- within 1.5 h of sunrise: `sunrise_window`, +10
- dawn fallback: `dawn_window`, +8
- within 1.5 h of sunset: `sunset_window`, +10
- dusk fallback: `dusk_window`, +8

### 13.2 Moon Rules

- new moon or full moon: `major_moon_phase_bonus`, +4
- new moon at night: `dark_moon_night_bonus`, +3
- full moon at night: `full_moon_night_bonus`, +3

### 13.3 Midday Penalties

- within 2 h of solar noon during daylight: `harsh_midday_penalty`, -8
- plain day fallback: `plain_day_penalty`, -4

### 13.4 Tide Rules

- flood tide approaching high within 2 h: `rising_tide_window`, +12
- early flood after low within 2 h: `early_flood_bonus`, +8
- ebb tide approaching low within 2 h: `falling_tide_window`, +5
- slack water: `slack_tide_penalty`, -6
- rising proxy when only phase is known: `rising_tide_proxy`, +7
- falling proxy when only phase is known: `falling_tide_proxy`, +4
- tide range over 0.6 m: `large_tide_range`, +5
- tide range under 0.3 m: `small_tide_range`, -3

### 13.5 Wind Rules

The rule code converts knots to km/h for these thresholds.

- 5-12 km/h: `moderate_wind_bonus`, +4
- 12-20 km/h: `light_wind_ok`, +1
- over 20 km/h: `strong_wind_penalty`, -10
- gusts over 40 km/h: `gust_penalty`, -5

### 13.6 Pressure Rules

Using 3-hour pressure delta:

- stable within 1.5 hPa: `stable_pressure_bonus`, +3
- rising by at least 1.5 hPa: `pressure_rising`, +4
- falling by at least 1.5 hPa: `pressure_falling`, +5
- absolute shift at least 4 hPa: `sharp_pressure_shift_flag`, -2

This treats pressure change as a movement/weather-change signal. The sharp-shift flag keeps extreme changes from becoming pure upside.

### 13.7 Rain, Cloud, Wave, Temperature

- cloud cover 30-80%: `cloud_cover_bonus`, +4
- rain/precipitation over 2 mm: `heavy_rain_penalty`, -10
- recent rain with light wind: `weather_recovery_window`, +3
- wave height 0.3-1.0 m: `strong_wave_rock`, +4
- wave height under 0.3 m: `calm_sea_beach`, +3
- wave height over 1.0 m: `big_wave_beach`, -5
- wave height falling over 24 h: `pelagic_settling_window`, +2
- sea surface temperature under 10 C: `water_temp_cold`, -5
- sea surface temperature 15-22 C: `water_temp_optimal`, +3

## 14. Normalized Environment Context

File: `preview.py`  
Function: `_environment_context`

The engine converts raw inputs into normalized factors:

- `wind_factor`
- `swell_factor`
- `pressure_bonus`
- `wind_alignment`
- `swell_alignment`
- `movement_bonus`
- `time_activity`
- `directional_exposure`
- `water_body_exposure`
- `inner_bay_shelter`
- `weather_stress`
- `exposed_penalty`
- `shelter_bonus`

Important formulas:

```text
wind_factor =
  clamp((wind_speed_knots - 6) / 18) * exposure_bias

swell_factor =
  clamp((swell_height_m - 0.35) / 1.8) * exposure_bias

pressure_penalty =
  clamp(abs(pressure_hpa - 1015) / 18)

pressure_bonus =
  1 - pressure_penalty

tide_movement =
  low     -> 0.42
  rising  -> 0.80
  mid     -> 0.58
  high    -> 0.50
  falling -> 0.66

time_movement =
  clamp(0.60 + score_delta / 40)

movement_bonus =
  0.55 * tide_movement
+ 0.45 * time_movement

directional_exposure =
  0.55 * wind_alignment
+ 0.45 * swell_alignment

weather_stress =
  0.58 * wind_factor
+ 0.42 * swell_factor

exposed_penalty =
  weather_stress * exposure_gate

shelter_bonus =
  (1 - weather_stress * 0.58)
* inner_bay_shelter
* shelter_bias
```

This is where weather and tide start influencing the score beyond simple rule tags.

## 15. Tide Effect by Water Type

File: `preview.py`  
Function: `_tide_phase_strengths`

Tide phase is not equal for all water types.

Current tendencies:

- beach: strongest on rising tide, then falling, weaker at low/high
- rocks: high and rising are strong
- jetty: rising/falling are useful, channel hint can help
- bay/estuary edge: falling and rising are strongest, high is weaker unless open-hint supports it

The tide value is centered at 0.60:

```text
centered = tide_value - 0.60

resident += 12 * centered
roaming  += 20 * centered
trip     +=  8 * centered
```

This means moving water affects roaming more than resident or trip quality.

## 16. Water-Type Score Cards

File: `preview.py`  
Function: `_score_nearby_water_types`

Each water type gets three raw scores:

- resident
- roaming
- trip

Then each is adjusted by tide, environment, and water-type-specific rules.

### 16.1 Beach Base

```text
resident = 20 + 20 * beach_strength + 10 * coastline_complexity
roaming  = 30 + 45 * beach_strength
trip     = 20 + 20 * accessibility + 20 * exposure - 10 * coastline_complexity
```

Beach is highly exposed and movement-sensitive:

- high exposure penalty weight
- high movement weight
- low shelter weight

### 16.2 Rocks Base

```text
resident = 25 + 35 * rocks_strength + 15 * coastline_complexity
roaming  = 20 + 30 * rocks_strength + 15 * exposure
trip     = 18 + 22 * accessibility + 10 * coastline_complexity - 12 * exposure
```

Rocks can score for fish when exposed but trip quality is punished by exposure.

### 16.3 Jetty-Style Base

```text
resident = 18 + 30 * jetty_strength + 12 * shelter
roaming  = 20 + 28 * jetty_strength + 10 * coastline_complexity
trip     = 24 + 24 * accessibility + 16 * shelter
```

This is not confirmed infrastructure unless map data says so.

### 16.4 Bay / Estuary Edge Base

```text
resident = 24 + 32 * bay_strength + 10 * shelter
roaming  = 18 + 24 * bay_strength + 10 * coastline_complexity
trip     = 28 + 24 * accessibility + 18 * shelter
```

Bay/estuary edge is intentionally the broadest and most cautious inshore interpretation.

## 17. Environment Adjustment by Water Type

File: `preview.py`  
Function: `_apply_environment`

Every water type passes different weights into the same environment adjustment.

General adjustment:

```text
trip_adjustment =
  -28 * exposure_weight * exposed_penalty
+  8 * shelter_weight  * shelter_bonus
+  0.25 * movement_weight * generic_rule_delta

roaming_adjustment =
   22 * movement_weight * movement_bonus
+ 0.75 * movement_weight * generic_rule_delta
-  16 * exposure_weight * exposed_penalty

resident_adjustment =
   8 * shelter_weight * shelter_bonus
+ 5.5 * pressure_weight * pressure_bonus
+ 0.30 * movement_weight * generic_rule_delta
```

Type weights:

```text
beach:
  exposure 0.95, shelter 0.10, movement 0.95, pressure 0.35

rocks:
  exposure 1.00, shelter 0.05, movement 0.70, pressure 0.45

jetty:
  exposure 0.45, shelter 0.65, movement 0.55, pressure 0.40

bay_estuary_edge:
  exposure 0.30, shelter 0.90, movement 0.60, pressure 0.45
```

This is why bad weather hits exposed beaches/rocks harder than sheltered estuary edges.

## 18. Public Preview Calibration

File: `preview.py`  
Function: `_calibrate_public_preview_score`

The engine deliberately calibrates searched-coordinate scores below curated hot-spot certainty.

Current calibration:

```text
raw <= 35:
  raw * 0.92

35 < raw <= 50:
  32.2 + (raw - 35) * 0.95

50 < raw <= 65:
  46.45 + (raw - 50) * 1.02

65 < raw <= 78:
  61.75 + (raw - 65) * 1.05

raw > 78:
  min(86.5, 75.4 + (raw - 78) * 0.55)
```

Purpose:

- keep ordinary preview days lower
- allow genuinely aligned strong stacks into the 70s/80s
- avoid many 90+ public-preview scores
- make low-scoring situations feel clearly low instead of compressed into the middle

Do not remove this without replacing it with an explicit calibration strategy.

## 19. Stack Logic

File: `preview.py`  
Functions: `_reason_buckets`, `_stack_adjustments`

Rule tags are grouped into:

- movement
- concentration
- timing
- negative

Positive stack examples:

- movement + timing
- movement + concentration
- timing + concentration
- strong all-category alignment

Negative stack examples:

- two or more negative tags
- slack tide + plain day
- harsh midday without movement
- strong wind plus gusts or larger surf
- heavy rain plus cold/strong wind

This is the recent spread-improvement layer: good days can lift higher when multiple independent positives align, while bad days can fall lower when multiple independent negatives stack.

## 20. Score Mode Layer

File: `preview.py`  
Function: `_derwent_style_score_modes`

This layer exposes the same score categories as the personal engine while staying generic.

### 20.1 Activity Score

Activity starts from:

```text
activity = (50 + generic_rule_delta) * habitat_factor
```

Habitat factors:

```text
beach:           0.76
rocks:           0.82
jetty:           0.80
bay_estuary_edge:0.74
```

Then activity receives small effects from:

- dominant roaming opportunity
- dominant resident opportunity
- dominant trip quality
- harsh midday penalty
- weather recovery / settling sea bonus
- moon phase overlapping dawn/dusk
- positive/negative stack adjustment

### 20.2 Resident Opportunity

Resident opportunity uses a type prior:

```text
beach: 26
rocks: 34
jetty: 38
bay_estuary_edge: 42
```

It is boosted by:

- dawn/dusk/sunrise/sunset
- moving tide
- moderate wind, cloud, stable/rising/falling pressure
- sheltered/structure-like types with calm sea or larger tide range

It is penalized by:

- slack tide
- harsh midday
- strong wind
- gusts
- heavy rain
- large surf

It is capped by type:

```text
beach max 62
rocks max 68
jetty max 72
bay_estuary_edge max 74
```

### 20.3 Roaming Opportunity

Roaming is intentionally hard to push high.

Type priors:

```text
beach: 34
rocks: 36
jetty: 22
bay_estuary_edge: 24
```

It needs evidence of:

- movement
- concentration
- timing

Caps:

- non-beach/non-rock types cap low unless evidence is strong
- no movement caps at 46
- no concentration caps at 52
- no timing caps at 60
- resident-dominant types with weak movement cap at 58
- high scores require strong combo evidence

This prevents sheltered resident conditions from pretending to be pelagic arrival events.

### 20.4 Presence Score

Presence starts from:

```text
presence = activity * 0.82
```

It is adjusted by:

- moving tide / large tide range
- sunrise/sunset/dawn/dusk
- cloud/pressure support
- harsh midday
- wind/gust/rain/surf/slack negatives
- resident and roaming scores
- stack adjustments

It is capped relative to activity:

```text
presence <= activity + 8
```

### 20.5 Trip Quality

Trip quality blends:

```text
trip_quality =
  activity * 0.62
+ presence * 0.18
+ resident * 0.08
+ roaming * 0.12
```

Then it is penalized for human fishing comfort/safety:

- strong wind
- gusts
- rain
- large surf
- harsh midday
- cold air plus wind
- cold exposed nighttime
- exposed wave/gust combinations
- weather stress
- exposed penalty

It receives small boosts from:

- weather recovery
- settling sea
- positive stack

It is capped relative to activity:

```text
trip_quality <= activity + 5
```

This means the engine can say "fish might be active, but the trip is poor" when weather is harsh.

### 20.6 Big Fish Near Shore

This is currently only `low` or `medium`.

It becomes `medium` only when:

- activity is high enough, and
- dawn/sunset/moon/tide signals align enough

It is not a species predictor.

## 21. Confidence Logic

File: `api.py`  
Function: `_confidence`

Confidence is separate from score. It answers: "How much should the app trust this forecast shape?"

It considers:

- searched coordinate, not curated hotspot
- support mode: on water, near water, tidal corridor
- external weather/marine availability
- tide verification source

Tide confidence tiers:

- `live_verified`: TidesAtlas near enough
- `provided_events`: user supplied real tide events
- `live_verified_remote_station`: real tide events but distant station
- `model_estimated`: Open-Meteo sea-level model proxy
- `estimated`: coarse astronomical approximation

The final confidence score is capped at 82 and usually labeled `medium` or `low`.

## 22. Place Search Logic

File: `coastal_fishing_forecast/places.py`

Supported providers:

- `mapbox`
- `nominatim`

Mapbox:

- current code uses v5 endpoint: `https://api.mapbox.com/geocoding/v5/mapbox.places`
- requires `MAPBOX_ACCESS_TOKEN`
- supports country filter, proximity, limit, language

Nominatim:

- endpoint: `https://nominatim.openstreetmap.org/search`
- no API key
- sends a custom user agent
- supports country filter, language, limit

Candidate ranking is intentionally lightweight:

- coastal type hints add score
- administrative/boundary types are penalized
- bounding box adds a small hint
- Mapbox confidence/relevance can add score

Then `search_forecast.py` calls `build_preview` on each ranked candidate. The final selected candidate is the first supported one after support-aware scoring.

Sources:

- Mapbox Geocoding API: https://docs.mapbox.com/api/search/geocoding/
- Nominatim Search API: https://nominatim.org/release-docs/latest/api/Search/

## 23. Structure / Public Access Layer

File: `coastal_fishing_forecast/structures.py`

This layer is not the core score engine. It supports map display and safer action planning.

Sources currently supported:

- OpenStreetMap Overpass
- Tasmania LIST MAST boat ramps
- Tasmania LIST WildFisheries sea fishing spots

### 23.1 Overpass

Endpoint:

- `https://overpass-api.de/api/interpreter`

Queried tags:

- `man_made=pier`
- `man_made=jetty`
- `leisure=slipway`
- `leisure=fishing`
- `sport=fishing`
- generic `fishing` tag

Only public or clearly public-access features are planner-eligible.

Source:

- Overpass API: https://wiki.openstreetmap.org/wiki/Overpass_API

### 23.2 Tasmania LIST MAST

Endpoint in code:

- `https://services.thelist.tas.gov.au/arcgis/rest/services/Public/TopographyAndRelief/MapServer/33/query`

Used for marine facilities such as boat ramps, jetties, wharves, piers, and slipways.

### 23.3 Tasmania LIST WildFisheries

Endpoint in code:

- `https://services.thelist.tas.gov.au/arcgis/rest/services/Public/WildFisheries/MapServer/0/query`

Used for official sea fishing spots and public fishing access features.

LISTmap source:

- https://nre.tas.gov.au/land-tasmania/the-list/listmap

Important: LISTmap itself warns that displayed information can be indicative and should not be treated as legal boundary truth. The engine should treat these records as public-product access hints, not legal advice.

### 23.4 Planner Eligibility

Planner-eligible types:

- `beach_access`
- `fishing_platform`
- `official_fishing_spot`
- `public_jetty`
- `rocky_shoreline`

Map-only type:

- `boat_ramp`

Boat ramps are useful map context but should not be described as fishing jetties.

## 24. Action Planner

File: `coastal_fishing_forecast/planner.py`

The planner turns forecast output into user action text.

It must not change:

- score
- best window
- support status

The rule-based planner:

- labels the recommendation as go/maybe/skip
- gives a primary action
- gives a backup option
- lists risks and avoid notes
- explains confidence and tide source
- guards terrain claims

The optional LLM planner path:

- provider name: `github_models` or `llm`
- only receives whitelisted forecast fields
- can rewrite text only
- cannot alter score, best window, support, or safety cautions
- falls back to rule-based planner on errors

The terrain guard is important. If no confirmed public structure exists, generated text must not claim a real jetty, pier, wharf, marina, breakwall, etc.

## 25. Social Pulse Context

File: `coastal_fishing_forecast/social_pulse.py`

This is a read-only context layer added from the previous social-intel work.

It reads:

- sibling path: `../fishing-forecast/data/social_intel/social_signals.csv`

It does not crawl Facebook or Xiaohongshu in this repo.

It does not change score.

The API explicitly returns:

```text
role: context_only
score_adjustment_allowed: false
```

Social pulse logic:

- find nearest area anchor
- read recent rows within a default 45-day window
- weight by recency
- weight by area relevance
- weight by evidence confidence
- downweight boat-only signals for shore product context
- return platform counts, species counts, matched areas, pulse score, and pulse level

Current pulse levels:

```text
score >= 65 -> high
score >= 35 -> medium
score >= 12 -> low
else        -> none
```

Reason for context-only status:

- old experiments showed direct social covariates made forecast performance worse
- social data is noisy and uneven by platform/location
- it is better as annotation, routing, validation, or later calibration context

## 26. Cache Layer

File: `coastal_fishing_forecast/cache.py`

Cache location:

- default: `.cache/coastal_fishing_forecast`
- override env: `COASTAL_FORECAST_CACHE_DIR`

Cache keys are SHA-256 hashes of namespace + sorted params.

Typical TTL behavior:

- Open-Meteo archive: no TTL
- Open-Meteo forecast: 1 hour
- place search: 1 day
- OSM/LIST structure lookups: 7 days
- TidesAtlas: cached with no TTL by URL

This is important because verification/replay should avoid repeated external calls and avoid accidental TidesAtlas quota usage.

## 27. External References and Why They Matter

### Open-Meteo Weather Forecast API

URL: https://open-meteo.com/en/docs

Used for:

- hourly weather
- pressure
- wind
- gusts
- rain/precipitation
- cloud cover
- sunrise/sunset

The docs describe the `/v1/forecast` endpoint and define the hourly weather variables used by this engine.

### Open-Meteo Marine Weather API

URL: https://open-meteo.com/en/docs/marine-weather-api

Used for:

- wave height
- swell height/direction
- sea surface temperature
- model sea-level height

Important caution: Open-Meteo notes that tide/current model accuracy near coastal areas is limited and is not suitable for navigation. This is why the engine labels Open-Meteo tide as `model_estimated`.

### TidesAtlas

URL: https://tidesatlas.com/en/api/docs

Used for:

- real high/low tide events when explicitly selected

The engine treats real tide events as higher confidence than model tide, but still checks station distance.

### OpenStreetMap Overpass API

URL: https://wiki.openstreetmap.org/wiki/Overpass_API

Used for:

- public jetties/pier/slipway/fishing access map context

The Overpass API is read-only and returns selected OSM elements by query. This matches the engine's need to fetch nearby map features without editing OSM.

### Mapbox Geocoding

URL: https://docs.mapbox.com/api/search/geocoding/

Used optionally for:

- place text to coordinate lookup

The current code uses the v5 endpoint, while Mapbox docs now emphasize v6. If upgrading, update code and tests deliberately.

### Nominatim Search

URL: https://nominatim.org/release-docs/latest/api/Search/

Used by default for:

- place text to coordinate lookup without a Mapbox key

Nominatim returns best matches, not all possible OSM objects in an area. For object-type searching, the Nominatim docs point users toward Overpass.

### Tasmania LISTmap / LIST ArcGIS Services

URL: https://nre.tas.gov.au/land-tasmania/the-list/listmap

Used for:

- official sea fishing spot catalogue
- marine/access facility layers

The current code calls ArcGIS REST endpoints directly.

## 28. What The Score Means

The score is a decision index, not a catch probability.

Interpretation:

- 0-35: poor or unsupported/weak conditions
- 35-50: weak to patchy
- 50-65: usable but not special
- 65-75: worthwhile if the location looks right on arrival
- 75-86: strong public-preview alignment
- 86+: currently rare/capped for searched coordinates

A high score means several broad signals align:

- supported coastal/tidal location
- plausible water type nearby
- moving tide
- dawn/dusk or strong timing
- manageable wind/swell
- pressure/cloud/water context not hostile
- trip quality not crushed by weather

A low score can come from:

- unsupported location
- slack tide
- plain midday
- strong wind/gusts
- heavy rain
- large exposed surf
- cold wind-chill style trip penalty
- lack of movement/concentration/timing evidence

## 29. Tuning Guidance

Tune in this order:

1. Verify support/rejection first. Bad support logic creates fake forecasts.
2. Verify visible weighted score, not only raw engine score.
3. Tune negative stacks before lowering all scores globally.
4. Tune positive stacks before raising all scores globally.
5. Keep the 80+ path possible only for strong aligned combinations.
6. Keep social pulse out of direct scoring until there is validation data.
7. Keep map structures separate from inferred water type.

Safe tuning locations:

- public score shape: `_calibrate_public_preview_score`
- good/bad signal spread: `_stack_adjustments`
- generic rule deltas: `_generic_derwent_rules`
- tide phase strength by type: `_tide_phase_strengths`
- weather impact by type: `_apply_environment` call weights
- region broad behavior: `regions.py`

Risky tuning locations:

- support distance thresholds
- land/ocean sampling
- place candidate selection
- terrain/structure claim guards
- planner safety rules

Do not tune by only checking one example location. Use a set of open coast, bay, estuary, harbour, surf, inland town, and inland lake examples.

## 30. Verification Commands

Recommended full verification:

```bash
./.venv/bin/coastal-verify
```

Direct preview:

```bash
./.venv/bin/coastal-preview -41.2530 148.3060
```

Date range:

```bash
./.venv/bin/coastal-forecast -41.2530 148.3060 \
  --start-date 2026-04-20 \
  --end-date 2026-04-26 \
  --region open_coast \
  --windows morning,dusk \
  --condition-source archive
```

Frontend/API payload:

```bash
./.venv/bin/coastal-api-forecast -41.2530 148.3060 \
  --start-date 2026-04-20 \
  --end-date 2026-04-21 \
  --region open_coast \
  --windows morning,dusk \
  --condition-source archive
```

Search-to-forecast:

```bash
./.venv/bin/coastal-search-forecast "St Helens Tasmania" \
  --start-date 2026-05-01 \
  --end-date 2026-05-03
```

Unit tests:

```bash
./.venv/bin/python -m unittest discover -s tests -v
```

## 31. Current Known Limitations

The engine does not yet have:

- true bathymetry
- local current model beyond tide phase/stage
- true moonrise/moonset or lunar transit
- species-specific public scoring
- validated catch-rate labels
- high-confidence curated hot spots in this generic repo
- real-time social crawling in this repo
- browser-visible social pulse UI
- legal-grade access verification

The most important modeling gap is validation data. Rules are coherent and product-safe, but they are still a heuristic decision index until calibrated against real catch/effort outcomes or trusted human review data.

## 32. Current Design Philosophy

This engine should be useful without pretending to know more than it knows.

Core principles:

- reject unsupported places instead of guessing
- separate score from confidence
- separate inferred water type from confirmed map structure
- separate fish activity from trip quality
- reward independent positive stacks
- punish independent negative stacks
- keep searched-coordinate previews below curated hotspot confidence
- make tide source quality visible
- keep social data contextual until validated

If another AI changes the engine, it should preserve those principles unless explicitly asked to redesign the product.

