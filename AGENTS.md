# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

Coastal Fishing Forecast — a Python engine + React/TypeScript web frontend for on-shore fishing forecasts. Two services:

| Service | Description | Port |
|---------|-------------|------|
| **Python engine** | Forecast CLI tools in `coastal_fishing_forecast/` | N/A (CLI) |
| **API server** | Node.js HTTP server in `apps/web/server/api-server.mjs` | 8787 |
| **Vite dev server** | React frontend in `apps/web/` | 5173 |

### Prerequisites

- `python3.12-venv` system package is required (`sudo apt-get install -y python3.12-venv`)
- Node.js 22+ (pre-installed)

### Running services

1. **Python venv** must be set up first: `python3 -m venv .venv && ./.venv/bin/pip install -e .`
2. **API server** (`apps/web`): `npm run api` — wraps the Python CLI tools behind HTTP endpoints; requires `.venv` to be set up at repo root
3. **Vite dev server** (`apps/web`): `npm run dev` — proxies `/api` to `http://127.0.0.1:8787`
4. Start the API server before the Vite dev server for the app to work end-to-end.

### Key commands

- **Tests**: `./.venv/bin/python -m unittest discover -s tests -v` (~220 tests, ~4s)
- **CLI preview**: `./.venv/bin/coastal-preview LAT LON` (e.g. `-42.88 147.33`)
- **Verification**: `./.venv/bin/coastal-verify`
- **Web build**: `cd apps/web && npm run build`

### Gotchas

- The API server (`api-server.mjs`) hardcodes paths to `.venv/bin/coastal-*` from the repo root. The Python venv **must** be at `/workspace/.venv/`.
- The first `search-forecast` API call can take ~25s because it fetches live weather/tide data from Open-Meteo + Nominatim. Subsequent calls are cached (~5min TTL).
- Optional API keys (`TIDESATLAS_API_KEY`, `MAPBOX_ACCESS_TOKEN`, `GITHUB_TOKEN`) enhance functionality but the app works without them using free data sources.
- **`POST /api/score-factors`** (Score factors): JSON body `{ lang, date, windows }`. Calls GitHub Models when **`GITHUB_TOKEN`** is set. Response `{ positive_factors: string[], negative_factors: string[], summary?: string, provider }`. Empty lists + `provider: fallback` → UI uses rule-based bullets in `dayScoreFactorsBullets()` in `App.tsx`.
- **Wave height curve**: `hourly_activity` fills `wave_height_m` and `swell_height_m` **only** from Open-Meteo marine hourly (`wave_height`, `swell_wave_height`), matching each timestep in **Australia/Hobart**. There is **no** fallback to preview engine defaults (which can include a nominal swell fill) and **no** synthetic curve from scored windows—if both series are missing in the JSON, the UI shows an explicit unavailable note (usually means the API server needs `pip install -e .` + restart, or Open-Meteo returned nulls for that grid/day).
