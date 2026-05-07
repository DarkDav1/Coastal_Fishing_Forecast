# Engine Todo Checklist (2026-04-23)

Scope: engine only.  
Not in scope for this session:

- frontend implementation
- search UI
- map interactions
- product copy polish

## Phase 1: Stabilize preview contract

- [x] Define a stable engine response contract for searched coordinates
- [x] Add explicit reason codes for `ok`, `unsupported`, and invalid input cases
- [x] Keep nearby water type order stable for downstream consumers
- [x] Add contract version field for handoff safety
- [x] Add example payloads for the next session

## Phase 2: Strengthen support decision

- [x] Return structured invalid-input responses instead of throwing raw errors
- [x] Keep inland / non-tidal rejection explicit
- [x] Add more coastal boundary regression samples
- [ ] Split future unsupported reasons more finely if needed

## Phase 3: Strengthen nearby water-type inference

- [x] Separate inference signals from final score formulas more clearly
- [x] Add test fixtures for beach-like, rock-like, sheltered-edge, and harbour-like coordinates
- [ ] Review whether `bay_estuary_edge` should later split into bay edge and estuary edge

## Phase 4: Prepare next-session handoff

- [x] Write engine contract notes for API/session handoff
- [x] Document current engine boundaries and known limits
- [x] Add documented example payload shapes for the next session

## Phase 5: Next engine work after this session

- [x] Introduce first environmental inputs: wind, tide phase, swell, pressure, time window
- [x] Separate geographic inference from condition scoring
- [x] Add first directional wind/swell handling against estimated open-water bearing
- [x] Add first generic region config layer without Derwent-specific tuning
- [x] Add first fixed regression sample set for supported coastal and estuary archetypes
- [x] Expand generic region presets to cover surf coast, harbour access, and bay coast patterns
- [x] Add a repeatable `coastal-verify` command for engine validation
- [x] Add second-wave harbour, tidal-edge, large-bay, and boundary-reject regression samples
- [x] Add first date-range forecast/replay path for searched coordinates
- [x] Add automatic tide-phase handling with real tide-event override support
- [x] Add JSON/CSV tide-event file loading for real tide-table handoff
- [x] Add TidesAtlas API adapter for real tide-event lookup
- [x] Document BoM registered data / AusTides production-source path
- [x] Add JSON cache layer for external weather, marine, and tide responses
- [x] Add frontend-oriented forecast API response facade
- [x] Keep location display coordinate-based until a real place resolver exists
- [x] Add derived water-type split for frontend product cards
- [x] Add generic fish-behavior groups
- [x] Add frontend confidence scoring and tide-verification status
- [x] Add separate Mapbox-backed place search resolver outside the forecast engine
- [x] Add Nominatim free-test provider for place search
- [x] Add combined search-to-forecast backend product flow
- [x] Improve candidate selection using support status and distance-to-water signals
- [x] Add frontend explanation block for reasons, risks, and alternatives
- [x] Add rule-based Fishing Plan layer for action-oriented frontend recommendations
- [x] Add GitHub Models planner provider with safe rule-based fallback
- [x] Document external key setup for Mapbox and TidesAtlas
- [x] Add low-cost search-to-forecast regression replay that avoids TidesAtlas quota
- [x] Build a richer low-cost regression replay set for supported and rejected searched places
- [x] Plan structure facility layer for boat ramps, piers, jetties, and access points
- [ ] Add backend structure facility fetch/normalization path
- [ ] Keep expanding fixed regression coordinates across more countries and coastline archetypes
- [ ] Expand tide behavior using more coastal and estuary validation cases
- [x] Tighten searched-coordinate rejection for farther inland boundary cases
- [ ] Replace heuristic support boundary with better supported-water geometry later
