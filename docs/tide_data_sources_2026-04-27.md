# Tide Data Sources (2026-04-27)

## Current engine support

The engine can now resolve tide phase from:

- inline tide events via `--tide-events-json`
- local JSON/CSV tide event files via `--tide-events-file`
- Open-Meteo model sea-level curve via `--tide-source openmeteo_model`
- TidesAtlas via `--tide-source tidesatlas`
- coarse fallback approximation when no real tide events are configured

## Open-Meteo model tide proxy

Open-Meteo Marine exposes `sea_level_height_msl`, a model sea-level variable that includes tide effects. The engine can now request that field and infer high/low tide events from the hourly curve.

Command example:

```bash
./.venv/bin/coastal-api-forecast -41.2530 148.3060 \
  --start-date 2026-04-20 \
  --end-date 2026-04-20 \
  --region open_coast \
  --windows morning,dusk \
  --condition-source archive \
  --tide-source openmeteo_model
```

Important confidence rule:

- `model_estimated` means tide phase is inferred from model sea-level data.
- This does not represent a verified local tide station.
- It is better than the coarse astronomical fallback, but should remain lower confidence than TidesAtlas or supplied official tide events.
- The frontend should label it as model tide, not station tide.

## TidesAtlas

TidesAtlas is the first directly integrated API source.

Configuration:

```bash
export TIDESATLAS_API_KEY="your-key"
```

Command example:

```bash
./.venv/bin/coastal-forecast -41.2530 148.3060 \
  --start-date 2026-04-20 \
  --end-date 2026-04-26 \
  --region open_coast \
  --windows morning,dusk \
  --condition-source archive \
  --tide-source tidesatlas
```

Implementation notes:

- endpoint: `https://tidesatlas.com/api/v1/tides`
- auth: `X-API-Key`
- coordinate mode: `lat` / `lon`
- returned event field: `extremes`
- normalized engine fields: `time`, `type`, `height_m`
- maximum request span is handled in 14-day chunks

If `--tide-source auto` is used, the engine uses the low-cost Open-Meteo model tide proxy when available. TidesAtlas is only used when explicitly selected with `--tide-source tidesatlas`, to avoid accidental quota usage.

Live verification:

```bash
TIDESATLAS_API_KEY="your-key" ./.venv/bin/coastal-verify --include-live-tides --verbose
```

Expected success signal:

```text
PASS live:tidesatlas
```

If the key is missing or invalid, live verification fails. This is intentional so estimated tide phases are not mistaken for real tide data.

Important confidence rule:

- `live_verified` means TidesAtlas returned real tide events from a nearby station.
- `live_verified_remote_station` means TidesAtlas returned real tide events, but the selected station is distant from the searched coordinate.
- Remote-station tide data is better than pure approximation, but it should not be presented as high-confidence local tide timing.

GPS default rule:

- when a user provides GPS coordinates, use those coordinates for real tide lookup
- allow the tide provider to return the nearest available station or port
- include the returned station distance when available
- downgrade confidence when the nearest station is distant
- do not let the frontend silently choose a station without backend verification

## BoM registered data

The Bureau of Meteorology documents registered user data services and lists the Australian Tide Prediction Bundle `IDBZ0019`.

Practical setup path:

1. Apply for or configure BoM Registered User Services.
2. Confirm access to Australian Tide Prediction Bundle `IDBZ0019`.
3. Confirm delivery method, likely registered-user file delivery rather than a simple public REST endpoint.
4. Store account credentials outside the repo.
5. Build a small importer that converts delivered tide predictions into the engine's common event format:

```json
[
  {"time": "2026-04-20T05:00:00+10:00", "type": "low", "height_m": 0.2},
  {"time": "2026-04-20T11:00:00+10:00", "type": "high", "height_m": 1.1}
]
```

Important constraint:

- BoM is the authority for Australian tide predictions, but this is not currently a simple no-key JSON API path.
- Licensing, attribution, disclaimer text, and redistribution terms must be handled before product release.

## AusTides / AHO

AusTides `AHP114` is the official electronic product equivalent to the Australian National Tide Tables.

Practical setup path:

1. Acquire AusTides or the relevant licensed tide product.
2. Confirm whether export or batch extraction is allowed under the licence.
3. Export predictions for required ports/stations.
4. Normalize those predictions into the same `time/type/height_m` engine format.
5. Keep station metadata and datum notes with the imported events.

Important constraint:

- AusTides is authoritative, but it is a product/licensing path, not a public app API.
- It should be treated as a production data source candidate after licensing is clear.

## Engine recommendation

Use Open-Meteo model tide for low-cost development and replay.

Use TidesAtlas for API-backed real tide station checks when quota is acceptable.

Keep BoM/AusTides as the preferred production authority path for Australia, but only after:

- account/licence is confirmed
- redistribution/attribution requirements are documented
- delivered files or exports are mapped into the common tide-event format
