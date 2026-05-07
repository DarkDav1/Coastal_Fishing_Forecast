# Product Scope And Engine Split (2026-04-22)

## Decision

The project is now split into two tracks.

## Track 1: Derwent local engine

This remains the local high-confidence system.

Use it for:

- personal use
- Derwent hot spots
- local tuning
- local spot splitting
- local species logic

Do not stretch this project into a generic public app engine.

## Track 2: Generic coastal product engine

This is the new public-product track.

Use it for:

- app / web product architecture
- regional coastal expansion
- search / nearby preview
- generic shoreline-type forecasts

## Why the split is necessary

If the Derwent project is used directly as a public generic engine, the product will overstate confidence.

The reason is simple:

- current spot logic is local
- current species mix is local
- current calibration is local
- current explanations are local

That is acceptable for a personal Derwent tool.
It is not acceptable as the main engine story for a public app.

## Scope of the generic engine

The generic engine should be framed as a **coastal saltwater and estuary product**, not a general fishing product.

### In scope

- beaches
- rock ledges
- jetties / wharves
- sheltered bays
- estuary margins
- channel edges
- lower-estuary transition water

### Out of scope for v1

- inland rivers
- inland lakes
- non-tidal freshwater systems

## Core product behavior

The generic engine should support two user modes.

### Mode A: Curated spots

Used where the backend has explicit spot knowledge.

### Mode B: Search / nearby preview

Used when the user selects a coordinate.

This mode must:

- infer broad water type
- use nearby weather / marine / tide inputs
- return lower-confidence output than curated spots

## Required backend layers for the generic engine

### 1. Supported-water check

Before scoring, determine whether the coordinate belongs to supported coastal or tidal water.

If not:

- reject the forecast
- return a clear unsupported message

### 2. Water-type inference

Before scoring, infer broad local type:

- beach
- rocks
- jetty
- bay edge
- estuary edge
- channel edge

### 3. Region configuration

Separate generic rules from region-specific assumptions.

Examples of future regions:

- Southeast Tasmania estuary
- Southeast Tasmania open coast
- East coast surf / rock

### 4. Confidence handling

The product should distinguish:

- curated high-confidence outputs
- searched medium-confidence outputs
- unsupported outputs

## Recommended scoring outputs

The public product track should keep using:

- `resident_opportunity`
- `roaming_opportunity`
- `trip_quality`
- `overall_recommendation`

But it should not expose them as if every region has the same certainty.

## Practical rule

Do not ship inland freshwater support in the generic engine until there is a separate freshwater model.
