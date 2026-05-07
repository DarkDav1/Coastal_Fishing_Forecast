# Place Search Contract (2026-04-28)

Place search is intentionally separate from the forecast engine.

The resolver turns a human query into candidate coordinates. The forecast engine still only accepts coordinates.

## Command

Free low-volume development test:

```bash
./.venv/bin/coastal-place-search "St Helens Tasmania" \
  --provider nominatim \
  --country au \
  --limit 5
```

Mapbox production-style search:

```bash
export MAPBOX_ACCESS_TOKEN="your-token"

./.venv/bin/coastal-place-search "Bay of Fires" \
  --provider mapbox \
  --country au \
  --proximity -41.3,148.3 \
  --limit 5
```

## Response shape

```json
{
  "query": "Bay of Fires",
  "provider": "nominatim",
  "results": [
    {
      "id": "nominatim:relation:456",
      "display_name": "St Helens, Break O'Day, Tasmania, 7216, Australia",
      "short_name": "St Helens",
      "latitude": -41.3236306,
      "longitude": 148.2493858,
      "country": "Australia",
      "region": "Tasmania",
      "source": "nominatim",
      "confidence": null,
      "types": ["boundary", "administrative"],
      "bbox": [-41.35, -41.29, 148.22, 148.28]
    }
  ]
}
```

## Frontend Flow

1. User types a place query.
2. Frontend calls the place search endpoint.
3. Frontend shows candidate places.
4. User selects one result.
5. Frontend sends that result's latitude and longitude to the forecast API.
6. Forecast API decides whether the coordinate is supported.

## Combined Search Forecast

For a one-shot backend product flow:

```bash
./.venv/bin/coastal-search-forecast "Binalong Bay Tasmania" \
  --provider nominatim \
  --start-date 2026-04-20 \
  --end-date 2026-04-20 \
  --region open_coast \
  --windows morning \
  --condition-source archive
```

This command:

- searches candidate places
- ranks coastal-looking candidates above administrative results
- runs a support check for each candidate
- boosts candidates closer to supported coastal/tidal water
- selects the first supported candidate
- returns the frontend forecast response for that coordinate

The response includes:

- `selected_place`
- `candidates`
- `forecast`
- `status`

## Low-Cost Regression Replay

For repeatable searched-place checks without using TidesAtlas quota:

```bash
./.venv/bin/coastal-regression-replay \
  --start-date 2026-04-20 \
  --end-date 2026-04-20 \
  --cache-dir .cache/coastal_fishing_forecast \
  --fail-on-error
```

The replay currently covers 11 cases through the same combined search-to-forecast path:

- supported examples: Binalong Bay, St Helens, Coles Bay, Fremantle, Sydney Harbour, Torquay Surf Beach, Noosa Heads, and Port Macquarie Breakwall
- rejection examples: Alice Springs, Lake Eildon, and Dubbo

Each result includes the selected place summary, expected outcome, forecast summary when available, and failure reasons when a case does not match expectation.

## Boundaries

The place resolver does:

- query autocomplete
- candidate location ranking
- coordinate lookup
- country and proximity filtering
- search-result caching

The forecast engine does:

- coastal/tidal support decision
- weather, marine, tide, and score calculation
- confidence and recommendation output

The resolver does not decide whether a place is fishable.

The combined search-forecast flow does a lightweight support check, but final fishing quality still comes from the forecast response.

## Configuration

Nominatim:

- no key required
- suitable for low-volume development tests
- must be cached
- do not use the public service as a high-volume production backend

Mapbox token:

```bash
MAPBOX_ACCESS_TOKEN="your-token"
```

Cache controls:

```bash
--no-cache
--cache-dir .cache/coastal_fishing_forecast
```

If Mapbox is selected and no token is configured, search fails clearly. It does not return fake local fixtures.
