# Engine Sample Provenance (2026-04-24)

This file explains where the current regression samples came from.

These samples are not a forecast-truth dataset.

They are engine regression inputs used to keep behavior stable while the preview logic changes.

## Sample source types

### `public_reference`

These are manually chosen, widely recognizable public coastal or inland reference locations.

Purpose:

- cover obvious open coast, bay, harbour, and inland cases
- keep the engine tied to understandable generic geography

Examples:

- `bondi_open_coast`
- `newcastle_harbour`
- `geelong_bay_edge`
- `alice_springs_inland`

### `boundary_probe`

These are manually chosen boundary coordinates near supported water.

Purpose:

- test whether the engine is too permissive or too strict near the support boundary
- lock in reject vs support behavior for searched inland-near-coast points

Examples:

- `gold_coast_inland_boundary`
- `surfers_inland_farther`
- `brisbane_river_inner_far`

### `scanned_candidate`

These are coordinates selected after local probing around a candidate corridor or inner estuary area.

Purpose:

- find points that actually exercise a special engine branch such as `tidal_corridor_preview`
- avoid inventing labels that the live heuristic does not support

Examples:

- `georges_river_inner_corridor`

## Working rule

A sample only stays in the fixed regression set if it helps test one of these:

- supported vs unsupported behavior
- a generic archetype such as open coast, bay edge, harbour access, or tidal corridor
- a region preset shift
- an environment or tide interaction

If the live engine clearly shows that a sample was labeled with the wrong archetype, the sample label should be corrected before the algorithm is distorted to fit it.
