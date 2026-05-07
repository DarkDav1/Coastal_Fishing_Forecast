# Structure Facility Layer Plan (2026-04-28)

This plan covers boat ramps, piers, jetties, wharves, and water access points.

The goal is to provide a map and scoring support layer for coastal and tidal fishing previews. This should not become a separate inland boating or lake forecast product.

## Product Goal

Show nearby access and structure features around a searched coordinate:

- boat ramp / slipway
- pier / jetty / wharf
- water access point
- later: official boat ramp datasets where available

These features should improve structure awareness and map display. They should not automatically turn a searched coordinate into a curated fishing spot.

## Data Source Strategy

### Phase 1: OpenStreetMap / Overpass

Use OSM as the first free source.

Relevant tags:

- boat ramp: `leisure=slipway`
- pier / jetty / wharf: `man_made=pier`
- legacy jetty: `man_made=jetty`
- water access point: `waterway=access_point`

Notes:

- `man_made=jetty` is discouraged in OSM, but old data may still exist.
- `waterway=access_point` is broader and lower confidence than a real boat ramp or pier.
- OSM completeness varies by region.

### Phase 2: Government Open Data

Use official datasets to improve confidence where available.

Examples:

- WA public boat ramps
- Queensland / Brisbane boat ramp locations
- NSW Transport boat ramps
- local council boat ramp datasets

These should be imported into a normalized internal structure, not queried directly from the frontend.

## Overpass Query Shape

For a frontend map viewport:

```overpass
[out:json][timeout:25];
(
  node["leisure"="slipway"]({{bbox}});
  way["leisure"="slipway"]({{bbox}});
  relation["leisure"="slipway"]({{bbox}});

  node["man_made"="pier"]({{bbox}});
  way["man_made"="pier"]({{bbox}});
  relation["man_made"="pier"]({{bbox}});

  node["man_made"="jetty"]({{bbox}});
  way["man_made"="jetty"]({{bbox}});
  relation["man_made"="jetty"]({{bbox}});

  node["waterway"="access_point"]({{bbox}});
  way["waterway"="access_point"]({{bbox}});
  relation["waterway"="access_point"]({{bbox}});
);
out center tags;
```

The production app should call our backend, not Overpass directly from the browser.

## Proposed Backend Endpoint

```text
GET /api/structures?bbox=south,west,north,east
```

Optional parameters:

- `types=boat_ramp,pier,access_point`
- `source=osm`
- `limit=500`

Coordinate-nearby endpoint:

```text
GET /api/structures/nearby?lat=-41.253&lon=148.306&radius_km=5
```

## Response Shape

```json
{
  "contract_version": "2026-04-28.structure_facilities.v1",
  "input": {
    "bbox": [-41.30, 148.20, -41.20, 148.35],
    "source": "osm"
  },
  "features": [
    {
      "id": "osm:way:123",
      "type": "pier",
      "label": "Pier / jetty",
      "name": "Example Jetty",
      "source": "osm",
      "source_tags": {
        "man_made": "pier"
      },
      "confidence": "medium",
      "geometry": {
        "type": "Point",
        "coordinates": [148.306, -41.253]
      },
      "distance_km": 0.4,
      "engine_use": {
        "supports_jetty_signal": true,
        "supports_access_signal": true,
        "curated_spot_equivalent": false
      }
    }
  ],
  "summary": {
    "total": 1,
    "by_type": {
      "pier": 1
    }
  }
}
```

## Normalized Types

Use these internal feature types:

- `boat_ramp`
- `pier`
- `access_point`
- `breakwater`
- `unknown_structure`

Mapping:

- `leisure=slipway` -> `boat_ramp`
- `man_made=pier` -> `pier`
- `man_made=jetty` -> `pier`
- `waterway=access_point` -> `access_point`

## Confidence Rules

Initial confidence:

- government boat ramp dataset: `high`
- OSM `leisure=slipway`: `medium`
- OSM `man_made=pier`: `medium`
- OSM `man_made=jetty`: `low` to `medium`
- OSM `waterway=access_point`: `low`

Confidence should be separate from fishing quality.

## Frontend Map Behavior

First map layer:

- boat ramp marker
- pier / jetty marker or line
- access point marker

Marker copy should be cautious:

- "Mapped boat ramp"
- "Mapped pier / jetty"
- "Mapped water access"

Avoid:

- "good fishing spot"
- "confirmed fishing platform"
- species-specific claims

## Engine Integration

The structure layer can influence:

- `jetty` inferred strength
- `structure_fish` behavior group
- explanation alternatives
- confidence that a structure-like option exists nearby

It should not influence:

- inland support decision by itself
- beach / rocks certainty unless feature tags justify it
- curated hotspot confidence
- species-specific predictions

Suggested first engine use:

- within 0.5 km: strong boost to jetty/structure signal
- 0.5-2 km: moderate nearby-structure signal
- 2-5 km: weak alternative signal
- over 5 km: no score effect, map display only

## Caching And Quotas

Overpass should be cached server-side.

Recommended cache keys:

- rounded bbox tile
- normalized query type set
- source

Recommended TTL:

- 7 to 30 days for OSM structure features
- longer for imported government datasets

Do not query public Overpass on every map pan in production.

## First Build Milestone

Done means:

1. backend can fetch OSM structures for a bbox
2. backend normalizes feature types
3. backend returns source tags and confidence
4. frontend can render markers from the response
5. searched-coordinate forecast can include nearby structure summary
6. no inland lake or river forecasting is added

## Open Questions

- Whether to implement Overpass fetch directly now or start with a static imported OSM fixture.
- Whether map geometries should be full lines/polygons or point-centroids in v1.
- Which official Australian boat ramp dataset should be imported first.
- Whether structure features should be returned inside forecast payloads or requested as a separate map layer.
