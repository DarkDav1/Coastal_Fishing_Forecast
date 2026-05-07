# New Session Bootstrap (2026-04-22)

## Project

- Project path:
  - `/Users/chenweic/dev/Fishing_Forcast/workspace-cocky/coastal-fishing-forecast`

## What this project is

This project is the **generic public-product track**.

It is not the Derwent personal-use engine.

The Derwent engine remains separate here:

- `/Users/chenweic/dev/Fishing_Forcast/workspace-cocky/fishing-forecast`

## Product goal

Build a generic **coastal saltwater and estuary fishing forecast** backend that can support:

- app / web product
- curated coastal hot spots
- searched places
- GPS-based nearby preview

## Product boundary

### In scope for v1

- beaches
- rock ledges
- jetties / wharves
- sheltered bays
- estuary margins
- channel edges
- lower-estuary transition water

### Explicitly out of scope for v1

- inland rivers
- inland lakes
- reservoirs
- non-tidal freshwater systems

If a searched place is inland, the backend should reject the forecast clearly instead of returning made-up scores.

## Product modes

### Mode 1: Curated hot spots

Higher-confidence, backend-maintained spots.

### Mode 2: Search / nearby preview

Lower-confidence forecast built from:

- searched place
- map tap
- GPS location

This mode must not pretend to know local structure as well as curated spots.

## Core scoring outputs

The target output model is:

- `resident_opportunity`
- `roaming_opportunity`
- `trip_quality`
- `overall_recommendation`

These outputs should be generic, explainable, and usable for product UI.

## What should not be copied from the Derwent engine blindly

Do not directly port:

- Derwent spot-specific assumptions
- Derwent species assumptions
- Derwent bridge logic
- Derwent local calibration
- Derwent micro-spot tuning

The generic product should reuse only the transferable ideas:

- resident vs roaming separation
- trip quality as human reality cost
- positive / negative reasons
- weather, marine, tide, current, and dynamic-condition logic

## Immediate architecture direction

The generic engine should be built around these layers.

### 1. Supported-water check

Decide whether a coordinate belongs to supported coastal or tidal water.

### 2. Water-type inference

Infer broad nearby type:

- beach
- rocks
- jetty
- bay edge
- estuary edge
- channel edge

### 3. Generic scoring

Score inferred nearby types using generic logic.

### 4. Confidence handling

Return different confidence for:

- curated spot
- searched preview
- unsupported inland request

## First development target

The first useful milestone is not "full scoring."

It is:

### Milestone A

Create the search / nearby intake path with:

- coordinate input
- inland rejection
- water-type inference shell
- placeholder response structure

This gives the public-product project a real backend direction without pretending the whole engine already exists.

## Recommended first build order

1. Create project package skeleton.
2. Add coastal-support check for arbitrary coordinates.
3. Add water-type inference stub and response format.
4. Define a preview endpoint contract.
5. Add UI-ready output shape for:
   - overall
   - beach nearby
   - rocks nearby
   - jetty nearby
   - bay / estuary edge nearby
6. Only after that, start refining real scoring logic.

## Done criteria for the first milestone

The first milestone is done when:

1. the project can accept coordinates
2. inland coordinates are rejected clearly
3. supported coastal coordinates return a structured preview payload
4. the payload separates nearby type cards
5. the shape is usable by web or app without depending on Derwent spot logic

## Files to read first

1. `/Users/chenweic/dev/Fishing_Forcast/workspace-cocky/coastal-fishing-forecast/README.md`
2. `/Users/chenweic/dev/Fishing_Forcast/workspace-cocky/coastal-fishing-forecast/docs/product_scope_and_engine_split_2026-04-22.md`
3. `/Users/chenweic/dev/Fishing_Forcast/workspace-cocky/coastal-fishing-forecast/docs/web_handoff_generic_app_2026-04-22.md`

## Working rule

Do not turn this project into a hidden copy of the Derwent engine.

This project exists to build the public-facing generic coastal product track.
