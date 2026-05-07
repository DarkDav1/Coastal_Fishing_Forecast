# Global Engine Master Handoff (2026-04-29)

## Purpose

This document is for the **generic coastal engine session**.

It captures:

1. the full current scoring architecture in the Derwent engine
2. the detailed tuning and compression logic now in use
3. the API shape and response model
4. the data acquisition pipeline and operational commands
5. what is transferable to the global engine and what is local-only

This is not a short product note.
It is the working engineering handoff for continuing the global engine track.

---

## 1. Project split

### Derwent local engine

Current local engine path:

- `/Users/chenweic/dev/Fishing_Forcast/workspace-cocky/fishing-forecast`

Role:

- high-confidence local system
- personal-use Derwent and nearby spots
- local spot splitting
- local species and structure tuning

### Global coastal engine

Current generic project path:

- `/Users/chenweic/dev/Fishing_Forcast/workspace-cocky/coastal-fishing-forecast`

Role:

- public-facing coastal / estuary product track
- generic search / nearby preview
- future regional expansion

### Core rule for the global session

Do **not** turn the global engine into a copy of the Derwent engine.

Use the Derwent engine as a source of:

- transferable score concepts
- transferable environmental logic
- tuning patterns
- response shape

Do **not** blindly copy:

- spot names
- local bridge assumptions
- local species mix
- local thresholds that only make sense because of local calibration

---

## 2. Current Derwent engine scope

The local engine currently models **22 spots**.

### Spot layers

- `area`: 19
- `micro_spot`: 3

### Spot types

- `shoreline`: 19
- `jetty`: 2
- `reef`: 1

### Most-used families

- `winter_sea_trout_shore`: 6
- `reef_trevally_edge`: 5
- `sheltered_bay_flatfish`: 2
- `mullet_shallow_structure`: 2
- `lower_estuary_transition`: 2
- `bridge_current_break`: 2
- `squid_jetty_weed_edge`: 2

### Most-used tags

- `mixed_structure`
- `current_break`
- `open_shore`
- `pelagic_edge`
- `runout_ambush`
- `sea_trout_support`
- `sheltered_bay`
- `trevally_support`
- `squid_support`
- `sandy_flat`
- `dropoff_edge`
- `bridge_structure`
- `reef`
- `rock_ledge`
- `bottom_fish_zone`

### Species support currently present

- `australian_salmon`
- `flathead`
- `sea_trout`
- `trevally`
- `bream`
- `garfish`
- `mullet`
- `cod`
- `trout`
- `morwong`
- `squid`
- `flounder`
- `whiting`
- `barracouta`
- `bottom_fish`
- `small_inshore`
- `atlantic_salmon`
- `pike`
- `jack_mackerel`
- `longfin_pike`
- `warehou`

For the global engine, this list is useful as a **taxonomy example**, not as a final public-product species set.

---

## 3. Current score outputs

The current local engine produces these main outputs per hourly row:

- `bite_score`
- `resident_opportunity_score`
- `roaming_opportunity_score`
- `nearshore_presence_score`
- `trip_quality_score`
- `big_fish_near_shore`
- `reason_tags`

These are then rolled up to daily API outputs.

### What they mean

#### `bite_score`

Main fish-activity score.
This is still the backbone signal.

#### `resident_opportunity_score`

Probability that the place is worth treating as a **resident-fish** location:

- bottom fish
- bream
- flathead
- cod
- flounder

This is intentionally separated from roaming / schooling opportunities.

#### `roaming_opportunity_score`

Probability that **roaming fish** or **schooling opportunity** is present:

- pelagic edge movement
- trevally edge movement
- Australian salmon type arrival
- sea-trout runout movement

This score is heavily capped unless movement, concentration, and timing evidence line up.

#### `nearshore_presence_score`

Proxy for whether worthwhile fish activity is actually near enough to accessible shoreline structure.

#### `trip_quality_score`

Human-value score:

- worth going or not
- includes fishability
- includes comfort / exposure / cold / gust / roughness

This is the score most suitable for recommendation layers.

#### `big_fish_near_shore`

Simple classification:

- `low`
- `medium`
- `high`

This is not a biomass estimate.
It is a coarse confidence read built from score + structure + timing + predator support.

---

## 4. Raw score architecture

The local engine builds scores in this order:

1. derive feature row
2. evaluate global rules
3. apply spot-specific and habitat adjustments
4. apply family / species / structure rules
5. apply current / chlorophyll / weather memory logic
6. apply anti-overconfidence caps
7. derive resident / roaming / presence / trip layers

This order matters.
For the global engine, the biggest reusable pattern is:

**environment -> local type -> movement evidence -> caps -> human-value layer**

---

## 5. Feature layer: what the scoring logic consumes

Current feature builder:

- `/Users/chenweic/dev/Fishing_Forcast/workspace-cocky/fishing-forecast/fishing_forecast/features.py`

Current location metadata:

- `/Users/chenweic/dev/Fishing_Forcast/workspace-cocky/fishing-forecast/config/locations.yaml`
- `/Users/chenweic/dev/Fishing_Forcast/workspace-cocky/fishing-forecast/fishing_forecast/locations.py`

### 5.1 Base environmental fields

The current system uses these broad groups:

- time / timestamp
- sunrise / sunset offsets
- moonrise / moonset offsets
- moon phase name
- tide stage
- hours to high tide / low tide
- hours since low tide
- air temperature
- sea surface temperature
- pressure
- pressure change
- cloud cover
- rain
- precipitation
- wind speed
- wind direction
- gusts
- wave height
- wave period
- tidal range

### 5.2 Memory windows

Short-term environmental memory currently includes:

- `recent_wind_max_12h`
- `recent_gust_max_12h`
- `recent_rain_sum_12h`
- `recent_precip_sum_12h`
- `recent_severe_weather_12h`

This supports:

- severe weather penalty
- weather recovery window
- weather recovery tail

### 5.3 Rolling rain windows

Current rolling accumulation windows:

- `rain_sum_1d`
- `rain_sum_3d`
- `rain_sum_7d`
- `rain_sum_14d`
- matching precipitation windows

Main current uses:

- bream runoff pulse
- sea-trout runoff pulse
- dirty-runoff penalties

### 5.4 Wind relative to coastline

Current feature layer decomposes wind into:

- `onshore_wind_10m`
- `offshore_wind_10m`
- `alongshore_wind_10m`

This uses `coast_facing_deg` in the location config.

This is one of the most transferable pieces to the global engine.

### 5.5 Advanced trend features

Temperature / sea-state trend features currently available:

- `sst_delta_6h`
- `sst_delta_24h`
- `wave_height_delta_6h`
- `wave_height_delta_24h`

Main current uses:

- pelagic warming trend
- pelagic cooling penalty
- settling window after rough weather

### 5.6 Chlorophyll

Chlorophyll features currently available:

- `chlorophyll_a`
- `chl_mean_3d`
- `chl_mean_7d`
- `chl_delta_3d`

Current use:

- regional productivity background
- pelagic productive-water logic
- chlorophyll uptick / fade

Important caveat:

For the current Derwent use case, chlorophyll is a **broad regional context** feature, not a spot-precise truth source.

### 5.7 Surface current

Current features available:

- `current_u`
- `current_v`
- `current_speed`
- `current_direction_to`
- `current_speed_delta_6h`
- `current_speed_delta_24h`
- `current_onshore`
- `current_offshore`
- `current_alongshore`

Current use:

- current-break logic
- bridge alignment
- reef alignment
- pelagic flow and uptick logic

This is the most important advanced-data input for distinguishing roaming opportunity.

---

## 6. Base rule evaluation logic

The scoring backbone lives here:

- `/Users/chenweic/dev/Fishing_Forcast/workspace-cocky/fishing-forecast/fishing_forecast/scoring.py`

### 6.1 General scoring helpers

#### `compress_extreme_score`

- scores `<= 90` unchanged
- above 90: only 35% of excess is kept

Purpose:

- prevent too many perfect or near-perfect activity scores

#### `compress_roaming_score`

- scores `<= 70` unchanged
- above 70: only 34% of excess is kept
- hard cap at 90

Purpose:

- roaming score must be much harder to push high than general bite score

### 6.2 Global rule deltas currently used in `bite_score`

Base activity score starts from:

- `base_score` from `config/scoring_rules.yaml`

Then a global map applies fixed deltas.

Current main global deltas:

- `sunrise_window`: `+10`
- `sunset_window`: `+10`
- `moonrise_overlap`: `+6`
- `moonset_overlap`: `+4`
- `major_moon_phase_bonus`: `+4`
- `dark_moon_night_bonus`: `+3`
- `full_moon_night_bonus`: `+3`
- `rising_tide_window`: `+12`
- `early_flood_bonus`: `+8`
- `falling_tide_window`: `+5`
- `slack_tide_penalty`: `-6`
- `moderate_wind_bonus`: `+4`
- `strong_wind_penalty`: `-10`
- `cloud_cover_bonus`: `+4`
- `heavy_rain_penalty`: `-10`
- `stable_pressure_bonus`: `+3`
- `sharp_pressure_shift_flag`: `-2`
- `harsh_midday_penalty`: `-8`
- `large_tide_range`: `+5`
- `small_tide_range`: `-3`
- `strong_wave_rock`: `+4`
- `calm_sea_beach`: `+3`
- `big_wave_beach`: `-5`
- `golden_window_rocks`: `+12`
- `golden_window_beach`: `+10`
- `island_mid_tide`: `+6`

These are the current top-level fixed rule weights.

---

## 7. Spot and habitat tuning

### 7.1 Spot-specific rule hooks

Current local engine still uses some spot hooks:

- `sandy_bay_flats`
- `sandy_bay_dropoff`
- `taroona`
- `tasman_bridge_lookout`
- `kangaroo_bluff_edge`
- `tranmere_shore`
- `tranmere_reef_edge`
- `howrah_edge`

These are local and should mostly **not** be ported directly into the global engine.

### 7.2 Habitat multipliers

Current local engine also uses local productivity multipliers.

Examples:

- bridges / reef: around `1.0`
- reef edge: around `0.95`
- generic shore: around `0.82–0.84`
- sandy flat: around `0.75`

Transferable lesson:

- a global engine should have **water-type priors**
- but they should be tied to inferred type, not local spot slug

---

## 8. Species and family logic currently active

This is the most important section for the global session.

The local engine is no longer one generic fish score.
It has distinct family-level logic.

### 8.1 Flathead logic

Tags:

- `flathead_sandy_ambush`
- `flathead_edge_window`

Current interpretation:

- sandy flat + active tide + manageable wind
- low-light edge support

Transferable:

- yes, for generic beach / bay-flat / dropoff logic

### 8.2 Mullet logic

Tags:

- `mullet_channel_edge`
- `mullet_low_light_cruise`

Current interpretation:

- active tide around structure or channel edges
- low-light cruising on edge or current-adjacent water

Transferable:

- yes, as a generic shallow-structure and bait-holding signal

### 8.3 Squid logic

Tags:

- `squid_night_window`
- `squid_incoming_tide`
- `squid_sheltered_weed_edge`
- `squid_exposed_surge_penalty`

Current interpretation:

- jetty + night + rising tide + shelter
- penalty if too exposed or too much surge

Transferable:

- yes, but only where jetties / weed edge / calm-water assumptions make sense

### 8.4 Sea-trout logic

Tags:

- `sea_trout_runout_edge`
- `sea_trout_big_tide_bias`
- `sea_trout_runoff_pulse`
- `sea_trout_dirty_runoff`
- `winter_sea_trout_season`
- `winter_sea_trout_offseason`

Current interpretation:

- productive ebb / runout / low-light / winter shoulder season
- moderate runoff helps, too much runoff hurts

Transferable:

- partly
- only for regions where sea-run trout style estuary movement is relevant

### 8.5 Bream logic

Tags:

- `bream_sheltered_margin`
- `bream_low_light_edge`
- `bream_runoff_pulse`
- `bream_dirty_runoff`

Current interpretation:

- sheltered bay margins
- active tide
- low light
- moderate runoff pulse good
- dirty runoff bad

Transferable:

- yes, to estuary / sheltered-bay product regions

### 8.6 Trevally / reef-edge roaming logic

Tags:

- `reef_trevally_current_edge`
- `reef_current_flow_window`
- `reef_current_alignment`
- `reef_current_exposed`

Current interpretation:

- active water on reef edge
- alongshore current alignment helps
- onshore exposure hurts

Transferable:

- yes, as generic rock-edge roaming logic

### 8.7 Pelagic family logic

Tags:

- `pelagic_active_edge`
- `pelagic_settling_window`
- `pelagic_current_flow`
- `pelagic_current_uptick`
- `pelagic_current_alignment`
- `pelagic_productive_water`
- `pelagic_chl_uptick`
- `pelagic_warming_trend`
- `pelagic_cooling_penalty`
- `pelagic_chl_fade`
- `pelagic_dead_current`

Current interpretation:

- roaming arrivals should depend on edge + movement + timing + productivity background
- dead current should kill fake optimism

Transferable:

- yes, this is one of the strongest global-engine foundations

---

## 9. `resident_opportunity_score` logic

This logic is currently one of the cleanest reusable pieces.

### 9.1 Resident score priors

Resident score starts at:

- `18`

Then gains habitat prior from:

- `bream_support`
- `sheltered_bay`
- `sandy_flat`
- `dropoff_edge`
- `bridge_structure`
- `current_break`
- reef / ledge / bottom-fish tags
- `sheltered_bay_flatfish`
- `bridge_current_break`
- resident-supporting species

Habitat prior is capped at:

- `+32`

### 9.2 Resident score positives

Main bonuses:

- sunrise / sunset / moon overlaps
- rising / falling tide / early flood
- moderate wind / cloud / stable pressure
- current-break activity
- bream margin tags
- flathead ambush tags
- bottom-fish structural tags
- sheltered clean-water tag
- mullet support tags

### 9.3 Resident score negatives

Main penalties:

- slack tide / midday
- strong wind / gust / rain / hard onshore
- severe weather
- current slack
- dirty runoff
- small-fish bias

### 9.4 Resident archetype caps

Resident score is then controlled by water type:

- pelagic-biased place with no resident species: max `48`
- pelagic-biased place with weak resident support: max `58`
- reef resident bias with weak resident support: max `64`
- sheltered flat with resident support: max `74`
- sheltered flat without clear support: max `66`
- bridge mixed bias with strong resident support: max `78`
- bridge mixed without it: max `70`
- micro-spot hard cap: `78`

Additional local caps:

- bridge without active current window: max `72`
- sheltered flat without relevant resident tags: max `62`

Final resident score:

- compressed by `compress_extreme_score`
- hard-capped at `88`

### 9.5 Main transferable lesson

Resident opportunity should be **type-led and support-led**, not just boosted because a place is famous or structurally interesting.

---

## 10. `roaming_opportunity_score` logic

This is the most important part for the global coastal app.

### 10.1 Roaming score priors

Starts at:

- `10`

Habitat prior gains from:

- `pelagic_edge`
- `lower_estuary_transition`
- `current_break`
- `bridge_current_break`
- `reef_trevally_edge`
- `runout_ambush`
- `open_shore`
- roaming species support

Habitat prior cap:

- `+32`

### 10.2 Three evidence buckets

Roaming logic is built around:

1. `movement_trigger_count`
2. `concentration_trigger_count`
3. `timing_trigger_count`

This is the key structure the global engine should preserve.

#### Movement triggers

- current-break active tide
- bridge current window
- reef current flow
- pelagic current flow
- current uptick
- alignment tags

#### Concentration triggers

- big tide bait bottleneck
- current-break crossflow
- pelagic edge window
- runout ambush
- productive water / chlorophyll uptick

#### Timing triggers

- sunrise / sunset
- moonrise / moonset
- recovery window / settling window
- warming trend

### 10.3 Roaming score negatives

Main negatives:

- slack or dead current
- exposed current direction
- cooling penalty
- chlorophyll fade
- severe weather

### 10.4 Resident-dominance suppression

Roaming score is capped when the fish signal looks too resident:

- flathead
- bottom fish
- bream margin
- sheltered flat bias

This is crucial.

### 10.5 Roaming hard caps

Current caps include:

- no pelagic bias + no roaming species: max `40`
- sheltered flat + no roaming species: max `34`
- sheltered flat + resident dominance: max `28`
- no movement trigger: max `46`
- no concentration trigger: max `52`
- no timing trigger: max `60`
- resident dominance + no concentration trigger: max `38`
- bridge bias + movement trigger count < 2: max `58`
- micro spot + movement trigger count < 2: max `58`

Further high-end controls:

- if score >= `74` and no arrival evidence: max `68`
- if score >= `80` and no arrival + concentration evidence: max `72`
- bridge >= `78` without alignment / flow uptick: max `70`
- reef edge >= `78` without alignment / crossflow: max `72`
- score >= `78` without strong combo: max `70`
- score >= `82` without stronger combo: max `76`
- score >= `86` without full movement+concentration+timing confirmation: max `80`

Final roaming score:

- compressed by `compress_roaming_score`
- hard-capped at `90`

### 10.6 Main transferable lesson

Roaming score must behave like **event evidence**, not like a generic “good place” score.

---

## 11. Anti-overconfidence controls in `bite_score`

The local engine now has several explicit “do not overhype” controls.

### 11.1 Stack controls

- `bridge_stack_control`
- `pelagic_tail_control`
- `bridge_pelagic_peak_control`
- `bridge_dead_current`
- `pelagic_dead_current`
- `stack_density_control`

Purpose:

- prevent too many 90+ scores
- prevent bridge + pelagic + tide stacks from pretending to be guaranteed frenzy
- prevent dead-current windows from staying inflated

### 11.2 Schooling-evidence controls

Tags:

- `schooling_evidence_missing`
- `schooling_evidence_weak`
- `schooling_confirmation_missing`
- `resident_fish_not_frenzy`
- `resident_bottom_fish_cap`
- `bridge_resident_bait_cap`
- `schooling_arrival_unconfirmed`
- `micro_spot_resident_cap`

Purpose:

- having resident fish is not the same as having a roaming fish event
- bait-holding is not the same as a true frenzy

This logic is extremely important for the global engine.

It is one of the key places where the local engine stopped over-scoring bridges and mixed-structure spots.

---

## 12. `big_fish_near_shore` logic

Current derivation uses:

- counts of high-condition tags
- predator-support tags
- score thresholds
- micro-spot and small-fish suppression

Current bands:

- `high`
- `medium`
- `low`

This is a coarse supporting label, not a primary score.

For the global engine, it can be kept as a UI helper, but it should not drive recommendations on its own.

---

## 13. `nearshore_presence_score` logic

This score is derived from:

- `bite_score * 0.82`

Then adjusted by:

### Presence positives

- active current-break / bridge / runout windows
- current flow and alignment tags
- big tide bottleneck
- runoff pulse
- pelagic active / settling / warming tags
- productive-water context
- flathead and mullet edge tags
- squid sheltered-weed-edge
- pelagic edge / bridge structure / sea-trout runout
- large active tide range
- `big_fish_near_shore`

### Presence negatives

- hard onshore
- dirty runoff
- current slack
- exposed current direction
- squid surge exposure
- pelagic cooling
- chlorophyll fade
- severe exposed weather

Final presence score:

- capped relative to bite score (`score + 8`)
- compressed with `compress_extreme_score`
- usually held below `97` if the raw bite score is not extreme

### Transferable lesson

Presence is the bridge between “activity exists” and “that activity is actually within reach”.

This is highly useful for a public product.

---

## 14. `trip_quality_score` logic

This is the current human-value layer.

### 14.1 Base formula

Current base blend:

- `bite_score * 0.62`
- `nearshore_presence_score * 0.18`
- `resident_score * 0.08`
- `roaming_score * 0.12`

### 14.2 Positive trip modifiers

- weather recovery
- sheltered water cleanup
- pelagic settling window
- useful onshore / alongshore window
- squid night
- sea-trout runout
- flathead sandy ambush
- mullet channel edge

### 14.3 Negative trip modifiers

- severe weather
- hard onshore
- big surf beach
- gust penalty
- severe sheltered penalty
- small fish bias
- micro spot caution
- midday penalty
- `big_fish_near_shore = low`

### 14.4 Winter / cold / exposure penalties

This is a major differentiator of the current engine.

Current penalties include:

- `cold_windy_trip_penalty`
- `winter_wind_chill_penalty`
- `gust_spread_trip_penalty`
- `cold_exposed_window_penalty`
- `wet_cold_trip_penalty`
- `exposed_gust_trip_penalty`
- `rough_exposed_trip_penalty`
- `night_cold_exposure_penalty`
- `stacked_trip_cap`

These use:

- low air temperature
- wind speed
- gust spread
- wetness
- rain and recent precip
- exposure tags
- pre-dawn / night timing
- rough water

### 14.5 Trip cap behavior

Trip score is capped relative to bite score:

- `trip_cap = score + 5`

Then reduced further by:

- wind chill proxy
- cold exposed windows
- gusts
- rough exposed water
- stacked-signal control

Final trip score:

- compressed with `compress_extreme_score`
- capped below `96` when raw activity score is not extreme

### 14.6 Transferable lesson

Trip quality is where the global app can differentiate itself most clearly.

A public app can tolerate some uncertainty in fish behavior.
It cannot tolerate obviously unrealistic “great trip” calls in cold, windy, exposed conditions.

---

## 15. Recommendation logic

### 15.1 Daily recommendation level in database seed

Defined in:

- `/Users/chenweic/dev/Fishing_Forcast/workspace-cocky/fishing-forecast/apps/api/app/seed.py`

Current blended formula:

- `worthwhile_avg * 0.55`
- `max(resident_avg, roaming_avg) * 0.25`
- `activity_avg * 0.2`

Extra bump:

- if `peak_score >= 88`
- and `worthwhile_avg >= 75`
- and `max(resident_avg, roaming_avg) >= 62`
- then blended gets `+2`

Current bands:

- `GO`: `>= 80`
- `PROBE`: `>= 66`
- `CAUTION`: `>= 52`
- else `PASS`

### 15.2 Preview endpoint recommendation level

For search preview, `main.py` currently uses a simpler local function:

- `GO`: `>= 75`
- `PROBE`: `>= 55`
- `CAUTION`: `>= 35`
- else `PASS`

This is currently a lower-confidence anchor-blend preview, not a true generic preview model.

For the global engine, this should be redesigned rather than copied blindly.

---

## 16. Current API shape

API app path:

- `/Users/chenweic/dev/Fishing_Forcast/workspace-cocky/fishing-forecast/apps/api/app`

### 16.1 Main endpoints

- `GET /api/v1/meta`
- `GET /api/v1/spots`
- `GET /api/v1/spots/{slug}`
- `GET /api/v1/spots/{slug}/hourly`
- `GET /api/v1/forecast/summary`
- `GET /api/v1/forecast/week`
- `GET /api/v1/conditions/summary`
- `GET /api/v1/analysis/today`
- `POST /api/v1/locations/preview`
- `POST /api/v1/admin/refresh`

### 16.2 Daily spot payload

Includes:

- slug
- name
- areaKey
- lat / lng
- layer
- recommendationLevel
- activityAvgIndex
- residentAvgIndex
- roamingAvgIndex
- presenceAvgIndex
- worthwhileAvgIndex
- peakHourLocal
- peakScore
- topReason
- positiveReasons
- negativeReasons

### 16.3 Hourly payload

Includes:

- timestamp
- biteScore
- residentOpportunityScore
- roamingOpportunityScore
- nearshorePresenceScore
- worthwhileScore
- bigFishNearShore
- reasonTags
- positiveReasons
- negativeReasons
- temperature2m
- pressureMsl
- windSpeed10m
- windGusts10m
- cloudCover
- waveHeight
- wavePeriod
- seaSurfaceTemperature
- currentSpeed
- currentDirectionTo
- tideStage

### 16.4 Forecast summary payload

Includes:

- activityAverage
- residentAverage
- roamingAverage
- presenceAverage
- worthwhileAverage
- best spot info
- recommendation level counts
- top reasons
- top positive reasons
- top negative reasons

### 16.5 Preview endpoint current behavior

The current `POST /api/v1/locations/preview` is **not a true generic coastal search engine**.

Current behavior:

- finds nearest existing anchored local spots
- blends their daily and hourly outputs by inverse distance
- returns a lower-confidence preview payload

This is useful as a product-shape prototype.
It is **not** the final architecture for the global engine.

### 16.6 Reason splitting behavior

Positive vs negative reasons are not separately stored in DB.

They are derived at API layer using markers such as:

- `penalty`
- `caution`
- `dirty`
- `dead`
- `exposed`
- `cap`
- `trimmed`
- `slack`
- `offseason`
- `weak`
- `hard`

This is simple but useful and should be preserved unless a better typed-reason model is introduced.

---

## 17. Data acquisition pipeline

### 17.1 Current source modules

Source modules:

- `/Users/chenweic/dev/Fishing_Forcast/workspace-cocky/fishing-forecast/fishing_forecast/sources/open_meteo.py`
- `/Users/chenweic/dev/Fishing_Forcast/workspace-cocky/fishing-forecast/fishing_forecast/sources/open_meteo_marine.py`
- `/Users/chenweic/dev/Fishing_Forcast/workspace-cocky/fishing-forecast/fishing_forecast/sources/bom_tides.py`
- `/Users/chenweic/dev/Fishing_Forcast/workspace-cocky/fishing-forecast/fishing_forecast/sources/tide_fetcher.py`
- `/Users/chenweic/dev/Fishing_Forcast/workspace-cocky/fishing-forecast/fishing_forecast/sources/copernicus_chlorophyll.py`
- `/Users/chenweic/dev/Fishing_Forcast/workspace-cocky/fishing-forecast/fishing_forecast/sources/copernicus_currents.py`

### 17.2 Current fetch scripts

Core operational scripts:

- `scripts/fetch_open_meteo.py`
- `scripts/fetch_bom_tides.py`
- `scripts/fetch_copernicus_chlorophyll.py`
- `scripts/fetch_copernicus_currents.py`
- `scripts/build_features.py`
- `python -m fishing_forecast.scoring`

### 17.3 Current raw / processed outputs

Typical outputs:

- weather CSV
- marine CSV
- tide CSV
- `data/processed/features_hourly.csv`
- `data/processed/scores_hourly.csv`
- Copernicus chlorophyll processed CSV
- Copernicus current processed CSV

### 17.4 Information acquisition rule for the global engine

For the global engine, the acquisition layer should be abstracted into:

1. weather inputs
2. marine inputs
3. tide inputs
4. ocean-background inputs
5. coastal-support / water-type inference inputs

The current Derwent scripts are a workable operational reference, not the final public-product architecture.

---

## 18. How to run the current Derwent pipeline

Project path:

- `/Users/chenweic/dev/Fishing_Forcast/workspace-cocky/fishing-forecast`

Typical sequence:

1. fetch weather
2. fetch marine
3. fetch tides
4. fetch Copernicus chlorophyll
5. fetch Copernicus currents
6. build features
7. score rows
8. seed API DB
9. start API

Typical commands:

```bash
cd /Users/chenweic/dev/Fishing_Forcast/workspace-cocky/fishing-forecast
./.venv/bin/python scripts/fetch_open_meteo.py
./.venv/bin/python scripts/fetch_bom_tides.py
./.venv/bin/python scripts/fetch_copernicus_chlorophyll.py
./.venv/bin/python scripts/fetch_copernicus_currents.py
./.venv/bin/python scripts/build_features.py
./.venv/bin/python -m fishing_forecast.scoring
./.venv/bin/python -c "from apps.api.app.seed import init_and_seed; init_and_seed(force=True)"
PYTHONPATH=/Users/chenweic/dev/Fishing_Forcast/workspace-cocky/fishing-forecast ./.venv/bin/uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8012
```

### Verification checklist

After refresh:

1. `features_hourly.csv` exists
2. `scores_hourly.csv` exists
3. hourly rows contain resident / roaming / worthwhile
4. API returns daily spots
5. API returns hourly rows with positive and negative reasons

---

## 19. What the global engine should reuse directly

These are the strongest transferable assets:

### Reuse directly

- resident vs roaming split
- presence layer
- trip quality as human-value layer
- positive / negative reason split
- wind relative to coast
- current relative to coast
- weather memory and recovery windows
- trend features:
  - SST
  - wave change
  - current change
  - chlorophyll trend
- anti-overconfidence caps
- “resident fish is not frenzy” logic

### Reuse with modification

- species families
- runoff logic
- reef / edge / bridge roaming logic
- productivity background
- big-fish helper label
- preview endpoint contract

### Do not copy blindly

- Derwent spot slugs
- exact local habitat multipliers
- exact local spot caps
- local bridge assumptions
- local sea-trout seasonality
- any rule that only exists because of a specific local place

---

## 20. What the global engine still needs

The global engine does **not** need “more local spots”.
It needs missing generic layers.

### P0

Supported-water check:

- accept coastal / tidal coordinates
- reject inland coordinates clearly

### P1

Water-type inference:

- beach
- rocks
- jetty
- bay edge
- estuary edge
- channel edge

### P2

Generic preview response:

- overall
- nearby beach
- nearby rocks
- nearby jetty
- nearby bay / estuary edge

### P3

Region config layer:

- supported region set
- species mix by region
- resident / roaming prior changes by region

### P4

True generic scoring path:

- no dependence on Derwent anchor spots
- no fake local confidence

---

## 21. Immediate guidance for the global session

If starting from scratch in the global engine project:

1. read this document
2. keep the four output scores
3. keep the reason model
4. keep the cap philosophy
5. do not start by building a full fish model
6. first build:
   - coordinate intake
   - inland rejection
   - water-type inference shell
   - preview response shape

The first real milestone is not “perfect prediction”.
It is:

**a believable coastal preview engine that knows when not to pretend.**

---

## 22. File index

### Derwent local engine source of truth

- scoring:
  - `/Users/chenweic/dev/Fishing_Forcast/workspace-cocky/fishing-forecast/fishing_forecast/scoring.py`
- features:
  - `/Users/chenweic/dev/Fishing_Forcast/workspace-cocky/fishing-forecast/fishing_forecast/features.py`
- spot metadata:
  - `/Users/chenweic/dev/Fishing_Forcast/workspace-cocky/fishing-forecast/config/locations.yaml`
  - `/Users/chenweic/dev/Fishing_Forcast/workspace-cocky/fishing-forecast/fishing_forecast/locations.py`
- API:
  - `/Users/chenweic/dev/Fishing_Forcast/workspace-cocky/fishing-forecast/apps/api/app/main.py`
  - `/Users/chenweic/dev/Fishing_Forcast/workspace-cocky/fishing-forecast/apps/api/app/schemas.py`
  - `/Users/chenweic/dev/Fishing_Forcast/workspace-cocky/fishing-forecast/apps/api/app/seed.py`
- worthwhile fallback:
  - `/Users/chenweic/dev/Fishing_Forcast/workspace-cocky/fishing-forecast/fishing_forecast/score_modes.py`

### Global project files

- `/Users/chenweic/dev/Fishing_Forcast/workspace-cocky/coastal-fishing-forecast/README.md`
- `/Users/chenweic/dev/Fishing_Forcast/workspace-cocky/coastal-fishing-forecast/docs/product_scope_and_engine_split_2026-04-22.md`
- `/Users/chenweic/dev/Fishing_Forcast/workspace-cocky/coastal-fishing-forecast/docs/web_handoff_generic_app_2026-04-22.md`
- `/Users/chenweic/dev/Fishing_Forcast/workspace-cocky/coastal-fishing-forecast/docs/new_session_bootstrap_2026-04-22.md`
