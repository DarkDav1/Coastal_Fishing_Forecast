# Engine Handoff Notes (2026-04-23)

## What is ready

The engine now has a first usable coordinate-preview path with:

- structured coordinate intake
- structured invalid-input handling
- inland / unsupported rejection
- low-confidence nearby coastal preview output
- stable nearby type ordering
- optional environment-aware score modifiers
- simple directional wind/swell handling against estimated open-water bearing
- water-type-specific tide handling
- optional generic region presets
- a fixed regression sample fixture set
- explicit support-profile state in engine output
- contract documentation for downstream wrapping
- a repeatable `coastal-verify` command for local engine validation
- a first `coastal-forecast` date-range forecast/replay path
- automatic tide-phase handling, with support for supplied real tide events
- JSON/CSV tide-event file loading for tide-table handoff
- TidesAtlas API support for real tide-event lookup when configured
- JSON cache support for weather, marine, and tide API responses
- frontend-oriented API response via `coastal-api-forecast`
- coordinate-based location display, confidence scoring, tide verification, derived water types, and behavior groups in the API facade
- separate Mapbox-backed `coastal-place-search` resolver for query-to-coordinate lookup
- Nominatim provider for free low-volume place-search testing
- `coastal-search-forecast` combined flow from place query to frontend forecast response
- low-cost `coastal-regression-replay` path that avoids TidesAtlas quota

## What the engine currently decides

Given `lat` and `lon`, it decides:

1. is the input valid
2. is the location within supported coastal/tidal scope
3. what nearby broad water types look plausible
4. what coarse preview scores to return
5. how broad environment inputs should nudge those scores
6. whether wind/swell direction broadly lines up with the estimated open-water side
7. which generic regional bias preset to apply
8. whether current output still matches the fixed regression sample set
9. whether a searched point is too far inland to justify even a cautious nearby preview
10. whether support came from on-water, near-water, or tidal-corridor handling
11. how date-range weather, marine, and tide windows should feed preview scoring

## What the next session should assume

- this is a generic coastal/tidal preview engine only
- this is not Derwent logic
- this should remain lower-confidence than curated hotspot output
- `bay_estuary_edge` is still a deliberately broad bucket

## What the next session should not assume

- no true spot recognition exists yet
- no full marine/tide/weather model exists yet
- current environment handling is still broad modifier logic, not localized condition modeling
- directional forcing is estimated against coarse open-water bearing, not true shoreline normals
- region presets are broad generic biases only, not region-specific calibration
- support/reject boundaries are still heuristic and should later move toward better water-body checks
- no frontend-ready wording layer exists yet
- automatic tide phase is only an approximation unless real tide events are supplied
- TidesAtlas requires `TIDESATLAS_API_KEY` or `--tidesatlas-api-key`
- frontend should consume the API facade first and keep `raw_forecast` for debug/detail views

## Recommended next engine tasks

1. add broader regression coordinates across obvious coastal and inland cases
2. refine how environment modifiers interact with each nearby type
3. refine directional exposure and tide logic with more real coastal samples
4. expand region config from broad presets into better generic regional archetypes
5. run `./.venv/bin/coastal-verify` before and after engine changes
6. connect a stronger tide-table provider for automatic real tide events
7. keep updating the fixed regression sample set as new archetypes are added
8. use `./.venv/bin/coastal-regression-replay --start-date 2026-04-20 --end-date 2026-04-20 --cache-dir .cache/coastal_fishing_forecast --fail-on-error` for searched-place regression checks without TidesAtlas spend

## Safe integration rule

If another session builds an API wrapper now, it should treat the current engine output as the source-of-truth payload and add translation at the boundary, not inside the engine core.
