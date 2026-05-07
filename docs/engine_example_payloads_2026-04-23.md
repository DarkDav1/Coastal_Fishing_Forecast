# Engine Example Payloads (2026-04-23)

These are representative engine outputs for handoff and API wrapping.

## 1. Coastal land near supported water

Input:

- `lat=-33.8915`
- `lon=151.2767`

Expected shape highlights:

- `status = ok`
- `support.reason_code = coastal_or_tidal_preview`
- `support.nearest_supported_water_km > 0`
- all four nearby water type cards present
- `overall_recommendation.confidence = low`

## 2. Inland unsupported point

Input:

- `lat=-23.6980`
- `lon=133.8807`

Expected shape highlights:

- `status = unsupported`
- `support.supported = false`
- `support.reason_code = inland_or_non_tidal`
- `overall_recommendation = null`
- `nearby_water_types = {}`

## 3. Invalid input

Input:

- `lat=95`
- `lon=151`

Expected shape highlights:

- `status = invalid_input`
- `support.reason_code = invalid_coordinate`
- `support.supported = false`
- `overall_recommendation = null`
- `nearby_water_types = {}`

## 4. Tidal-water supported point

Input:

- `lat=-42.8821`
- `lon=147.3390`

Expected shape highlights:

- `status = ok`
- `support.nearest_supported_water_km = 0.0`
- `meta.curated_spot_equivalent = false`
- `overall_recommendation.dominant_inferred_type` is one of the nearby type keys

## Integration note

The next session should treat these as contract examples, not score targets.

The exact numeric values may shift as the engine improves.

The field presence, status meanings, and reason-code behavior should remain stable unless the contract version changes.
