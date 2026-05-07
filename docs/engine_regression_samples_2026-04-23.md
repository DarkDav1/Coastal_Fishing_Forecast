# Engine Regression Samples (2026-04-23)

This file records the current representative coordinate set used for engine regression.

Source fixture:

- `tests/fixtures_regression_samples.py`

## Current sample groups

### Open coast

- `bondi_open_coast`
- `manly_open_coast`
- `port_arthur_open`

### Surf coast

- `cronulla_beach`

### Rocky open edge

- `bare_island_rock_edge`

### Sheltered / harbour edge

- `sydney_harbour_edge`
- `fremantle_harbour`
- `newcastle_harbour`
- `devonport_edge`
- `port_hacking_edge`
- `port_river_mid`
- `botany_bay_inner`
- `darwin_harbour_inner`
- `pittwater_inner`

### Tidal edge

- `hobart_tidal`
- `georges_river_inner_near`

### Bay edge

- `geelong_bay_edge`
- `st_kilda_bay`

### Large bay mixed

- `moreton_bay_inner`

### Channel mixed

- `bruny_channelish`

### Boundary case

- `gold_coast_inland_boundary`

### Tidal corridor

- `georges_river_inner_corridor`

### Boundary reject

- `surfers_inland_farther`
- `adelaide_inner_far`
- `brisbane_river_inner_far`
- `swan_inner_far`

### Unsupported inland

- `alice_springs_inland`
- `wagga_inland`
- `launceston_inner_reject`

## Current purpose

These samples are not a truth dataset for forecast quality.

They are a regression set for engine behavior:

- status remains stable
- generic archetype signals remain plausible
- region presets move signals in the intended direction
- inland rejection stays explicit

## Next expansion targets

- more sheltered estuary margins
- more open rock platforms
- more harbour-wall and jetty-like cases
- more coastal boundary inland points
- more southern exposed coast examples
