# Feedback Schema v1

**Locked: 2026-05-07.** Bumping the schema is a breaking-style change.
Never mutate the meaning of an existing field; only ever **add new
optional fields**. If a real breaking change is needed, introduce v2
and read both versions in `read_feedback`.

---

## Purpose

Phase A of the empirical calibration loop (P1 #6). Captures user-reported
trip outcomes alongside the engine's predicted scores so Phase B can
analyze offline and Phase C can defensibly tune calibration constants.

## Storage

- Format: **JSON Lines** (`.jsonl`), one record per line.
- Default path: `data/feedback.jsonl` (override via env
  `COASTAL_FORECAST_FEEDBACK_PATH`).
- Append-only. The CLI `coastal-feedback` is the only sanctioned
  writer. Manual edits are not supported.

## Wire format (POST `/api/feedback`)

Required fields:

| Field          | Type   | Constraint                                              |
|----------------|--------|---------------------------------------------------------|
| `trip_date`    | string | `YYYY-MM-DD`                                            |
| `trip_window`  | string | one of `pre_dawn / dawn / morning / day / dusk / night` |
| `lat`          | number | `-90..90`                                               |
| `lon`          | number | `-180..180`                                             |
| `predicted`    | object | must contain `predicted.score` (int)                    |
| `outcome`      | string | one of `skunked / ok / decent / great`                  |

Optional fields:

| Field            | Type    | Constraint                                |
|------------------|---------|-------------------------------------------|
| `region`         | string  | one of the engine's region presets        |
| `outcome_notes`  | string  | ≤ 120 characters                          |
| `report_id`      | string  | client-supplied UUID (server fills if missing) |

### `predicted` block

The frontend should send back the predicted scores **verbatim** from the
forecast response so calibration analysis isn't affected by future
algorithm changes. Recommended shape (all optional except `score`):

```json
{
  "score": 65,
  "fish_outlook_score": 67,
  "comfort_score": 70,
  "safety_flag": "low",
  "safety_factors": ["..."],
  "comfort_factors": ["..."],
  "dominant_water_type": "bay_estuary_edge",
  "key_reason_tags": ["sunrise_window", "rising_tide_window"],
  "combo_release": "rare_alignment_window"
}
```

`predicted.safety_flag`, when present, is validated against the engine's
4-tier enum (`low / moderate / elevated / hazardous`).

## Stored row format

The server enriches each row with metadata before writing:

```json
{
  "schema_version": "v1",
  "report_id": "0b1864ccad7d420d9f7438efca9380dd",
  "submitted_at": "2026-05-07T13:45:52.527192+00:00",
  "trip_date": "2026-05-08",
  "trip_window": "morning",
  "lat": -42.8915,
  "lon": 147.3320,
  "region": "sheltered_estuary",
  "predicted": { ... },
  "outcome": "decent",
  "outcome_notes": "Two flathead near the marina edge"
}
```

## Frontend integration (Phase A delivery requires this)

The day-overview window card should add a small 4-tier picker after the
trip is over (or at any time the user opens it):

```
How did it go?  [😐 skunked] [🐟 ok] [🐟🐟 decent] [🎯 great]
```

When clicked, POST `/api/feedback` with the body above. The frontend can
fire-and-forget; the server returns 201 + the stored record on success
or 400 + `{error, message}` on validation failure.

## Phase B (implemented)

`coastal-analyze-feedback` CLI (module:
`coastal_fishing_forecast.feedback_analysis`) reads the jsonl and emits a
markdown report on stdout covering:

- sample size, date span, schema version
- Phase C readiness gate (>= 50 rows, >= 3 regions, >= 14 days span)
- outcome distribution
- predicted-vs-actual signed deviation (mean / median / mean_abs)
  using fixed targets: skunked=20, ok=45, decent=65, great=85
- score-bucket sanity (do high predictions match great outcomes?)
- breakdowns by `region`, `predicted.dominant_water_type`,
  `predicted.safety_flag`, `predicted.combo_release`
- reason-tag enrichment in `great` and `skunked` buckets

The script is read-only; it never modifies any algorithm constants.

Usage:

    coastal-analyze-feedback                     # uses default path
    coastal-analyze-feedback --path X.jsonl
    coastal-analyze-feedback > calibration_report.md

## Phase C (NOT yet implemented)

Tune `_calibrate_public_preview_score` thresholds and
`_stack_adjustments` constants based on empirical data. Requires the
Phase C gate to pass: >= 50 reports, 3+ regions, 2+ weeks span. Each
constant change should use a hold-out split (80 / 20) to validate.

## Migration policy

- Add new optional fields → backward compatible, no version bump.
- Remove or rename fields → bump to v2, keep v1 readable forever.
- Existing rows must remain interpretable indefinitely. Calibration
  analysis should always start with `schema_version` to know which
  fields to trust.
