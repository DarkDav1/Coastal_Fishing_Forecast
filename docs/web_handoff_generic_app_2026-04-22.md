# Web Handoff: Generic Coastal App Track (2026-04-22)

## What changed

There is now a separate project track for the public-facing product.

### Local Derwent engine

Still lives here:

- `/Users/chenweic/dev/Fishing_Forcast/workspace-cocky/fishing-forecast`

Purpose:

- personal Derwent use
- local hot spots
- high-confidence local tuning

### Generic coastal product engine

Now lives here:

- `/Users/chenweic/dev/Fishing_Forcast/workspace-cocky/coastal-fishing-forecast`

Purpose:

- public app / web product
- generic coastal and estuary coverage
- searched-place preview

## Product direction for web

The web app should be planned around two front-end flows.

## 1. Curated hot spots

This is the easier and more trustworthy product line.

User experience:

- browse known spots
- compare scores
- read positive and negative reasons
- see best hours

This should remain the most trusted mode.

## 2. Search / nearby preview

This is the broader product line.

User experience:

- search a place
- tap the map
- use current GPS
- receive a preview forecast for that location

Important:

This should be presented as a preview mode, not the same confidence level as curated spots.

## Expected backend behavior for search / nearby

When the user searches a place, the backend should:

1. check whether the coordinate is in supported coastal or tidal water
2. reject unsupported inland places
3. infer nearby water types
4. score those water types
5. return a combined summary

## What the frontend should eventually show

For a searched area, the product should not return only one blunt score.

It should ideally show:

- overall nearby score
- nearby beach score
- nearby rocks score
- nearby jetty score
- nearby bay / estuary edge score

This is the main product differentiation direction.

Example:

- rocks nearby: stronger resident fish, lower comfort in wind
- jetty nearby: more bait concentration, moderate roaming chance
- beach nearby: tide and light-window dependent

## Supported scope

The generic app should be framed as:

- coastal fishing
- estuary fishing
- saltwater shore fishing

It should not be framed as:

- all fishing
- inland river forecasting
- lake forecasting

## Unsupported case

If the searched place is inland, the UI should show a clear unsupported message.

Suggested product wording:

- This forecast currently supports coastal and tidal fishing areas only.

## Frontend delivery recommendation

### Phase 1

Build the shell for the two modes:

- curated spots
- search / nearby

### Phase 2

For search / nearby:

- allow search
- allow GPS
- allow map selection
- show unsupported inland state

### Phase 3

When the backend preview path is ready:

- render nearby type cards
- show overall score plus beach / rocks / jetty / bay-edge suggestions

## Immediate takeaway for web work

Do not design the web app as "Derwent hot spots with a search box".

Design it as:

1. curated hot spots
2. generic nearby preview

Those are different user experiences and should stay separate in the product structure.
