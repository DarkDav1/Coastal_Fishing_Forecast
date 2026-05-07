# External Key Setup (2026-04-28)

This project can run without paid keys by using:

- Nominatim for low-volume place search
- Open-Meteo for weather and marine data
- astronomical tide approximation when no real tide provider is configured

For stronger product testing, configure these optional keys.

## Mapbox Place Search

Used by:

- `coastal-place-search --provider mapbox`
- `coastal-search-forecast --provider mapbox`

Environment variable:

```bash
export MAPBOX_ACCESS_TOKEN="your-mapbox-token"
```

Smoke test:

```bash
./.venv/bin/coastal-place-search "Binalong Bay Tasmania" --provider mapbox --country au --proximity -41.3,148.3
```

If configured correctly, the response should include `provider: mapbox` and one or more candidate coordinates.

Development fallback:

```bash
./.venv/bin/coastal-place-search "Binalong Bay Tasmania" --provider nominatim --country au
```

Use Nominatim only for low-volume development tests.

## TidesAtlas Real Tide Events

Used by:

- `coastal-forecast --tide-source tidesatlas`
- `coastal-api-forecast --tide-source tidesatlas`
- `coastal-search-forecast --tide-source tidesatlas`
- `coastal-verify --include-live-tides`

Environment variable:

```bash
export TIDESATLAS_API_KEY="your-tidesatlas-key"
```

Smoke test:

```bash
./.venv/bin/coastal-verify --include-live-tides --verbose
```

Expected success signal:

```text
PASS live:tidesatlas
```

Forecast test:

```bash
./.venv/bin/coastal-search-forecast "Binalong Bay Tasmania" \
  --provider nominatim \
  --start-date 2026-04-28 \
  --end-date 2026-04-30 \
  --region open_coast \
  --windows morning,dusk \
  --tide-source tidesatlas
```

If configured correctly, `data_sources.tide` should be `tidesatlas`, and the frontend `tide_verification.status` should be `live_verified`.

If the response says `live_verified_remote_station`, the key works, but the selected tide station is distant. Treat that tide phase as lower confidence until a closer tide source is available.

## GitHub Models Planner

Used by:

- `coastal-api-forecast --planner-provider github_models`
- `coastal-search-forecast --planner-provider github_models`

Environment variables:

```bash
export GITHUB_TOKEN="your-github-token"
export GITHUB_MODELS_MODEL="openai/gpt-4o-mini"
```

Optional endpoint override:

```bash
export GITHUB_MODELS_ENDPOINT="https://models.github.ai/inference/chat/completions"
```

Smoke test:

```bash
./.venv/bin/coastal-api-forecast -41.2530 148.3060 \
  --start-date 2026-04-20 \
  --end-date 2026-04-20 \
  --region open_coast \
  --windows morning \
  --condition-source archive \
  --tide-source openmeteo_model \
  --planner-provider github_models
```

If configured correctly, `plan.source` should be `github_models`.

If the key is missing, rate-limited, times out, or returns invalid JSON, the response remains usable and `plan.source` becomes `rule_based_fallback`.

## Local Shell Persistence

For zsh, add keys to:

```bash
~/.zshrc
```

Example:

```bash
export MAPBOX_ACCESS_TOKEN="your-mapbox-token"
export TIDESATLAS_API_KEY="your-tidesatlas-key"
export GITHUB_TOKEN="your-github-token"
export GITHUB_MODELS_MODEL="openai/gpt-4o-mini"
```

Then reload:

```bash
source ~/.zshrc
```

## Safety

Do not commit API keys to the repository.

Keep keys in:

- shell environment variables
- local `.env` files ignored by git
- deployment secret managers
