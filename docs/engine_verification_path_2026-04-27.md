# Engine Verification Path (2026-04-27)

This project now has one main repo-local verification command:

```bash
./.venv/bin/coastal-verify
```

## What it checks

The command verifies the current generic preview engine through two layers.

### 1. Regression suite

Runs the full `tests` suite.

This checks:

- stable output contract
- invalid coordinate handling
- inland / unsupported rejection
- supported coastal and tidal preview behavior
- broad nearby water-type inference
- environmental modifier behavior
- generic region preset behavior
- fixed regression sample stability
- date-range forecast/replay behavior
- tide-event phase handling
- JSON/CSV tide-event file loading
- TidesAtlas response normalization
- JSON cache helper behavior
- frontend-oriented API response behavior
- place-search response normalization and cache behavior
- Nominatim response normalization for free provider testing
- combined search-to-forecast candidate selection behavior
- low-cost search-to-forecast regression replay behavior

### 2. Engine smoke checks

Runs direct representative coordinate checks for:

- coastal on-water preview
- nearby coastal preview
- tidal-corridor preview
- unsupported boundary rejection
- invalid-coordinate rejection

These smoke checks make it quick to confirm that the main app-facing path still works after engine changes.

## Useful commands

Run the normal verification path:

```bash
./.venv/bin/coastal-verify
```

Run with more detail:

```bash
./.venv/bin/coastal-verify --verbose
```

Run live TidesAtlas verification after configuring a real API key:

```bash
TIDESATLAS_API_KEY="your-key" ./.venv/bin/coastal-verify --include-live-tides --verbose
```

This check must not be treated as passing unless it reports `PASS live:tidesatlas`.

Run only smoke checks:

```bash
./.venv/bin/coastal-verify --skip-unittest
```

Run the raw test suite:

```bash
./.venv/bin/python -m unittest discover -s tests -v
```

Run a representative date-range replay:

```bash
./.venv/bin/coastal-forecast -41.2530 148.3060 --start-date 2026-04-20 --end-date 2026-04-26 --region open_coast --windows morning,dusk --condition-source archive
```

Run the low-cost searched-place replay without spending TidesAtlas quota:

```bash
./.venv/bin/coastal-regression-replay --start-date 2026-04-20 --end-date 2026-04-20 --cache-dir .cache/coastal_fishing_forecast --fail-on-error
```

This uses Nominatim, cached weather/marine archive data, and tide approximation. It includes supported coastal examples plus inland and inland-lake rejection examples.

Run a replay with tide events from file:

```bash
./.venv/bin/coastal-forecast -41.2530 148.3060 --start-date 2026-04-20 --end-date 2026-04-20 --region open_coast --windows morning --condition-source archive --tide-events-file tests/fixtures_tide_events_bay_of_fires_2026-04-20.json
```

Run with TidesAtlas when an API key is configured:

```bash
TIDESATLAS_API_KEY="your-key" ./.venv/bin/coastal-forecast -41.2530 148.3060 --start-date 2026-04-20 --end-date 2026-04-26 --region open_coast --windows morning,dusk --condition-source archive --tide-source tidesatlas
```

Run the frontend-oriented API response:

```bash
./.venv/bin/coastal-api-forecast -41.2530 148.3060 --start-date 2026-04-20 --end-date 2026-04-21 --region open_coast --windows morning,dusk --condition-source archive
```

## Finishing rule

Before handing engine changes to another session, run:

```bash
./.venv/bin/coastal-verify
```

If it fails, fix the engine or the regression expectation before treating the work as complete.
