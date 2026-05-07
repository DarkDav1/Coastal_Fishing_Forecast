# Frontend Reference: Tides4Fishing (2026-04-28)

Reference page studied:

- https://tides4fishing.com/nc/grande-terre/gilles

This note is for product and frontend planning only. Do not copy site text, artwork, layout, or proprietary data. Use it as a reference for information architecture and fishing-weather content grouping.

## What The Site Does Well

Tides4Fishing is organized as a long-form fishing conditions page, not just a tide table.

Main sections:

- location and date navigation
- weather
- water temperature
- swell
- high and low tides
- tidal coefficient
- monthly tide table
- moonrise and moonset
- solunar activity
- moon phase
- nearby fishing sites / locations

The page treats fishing conditions as a bundle of signals: weather, pressure, wind, swell, tide, moon, and solunar timing.

## High-Value Ideas For Our Frontend

### 1. Date Strip At The Top

The site has a horizontal date selector for the current forecast window.

Our version should use:

- today plus next several days
- score badge per day
- selected date state
- no heavy calendar in v1

### 2. Forecast Sections As Anchors

The site groups content into clear anchors: Weather, Tides, Solunar, Sites.

Our first app can use:

- Summary
- Conditions
- Tide
- Water types
- Explanation
- Nearby / unsupported

This keeps mobile navigation simple.

### 3. Tide State As Plain Language

The site explains current water state as rising/falling and time until the next high/low tide.

Our frontend should eventually show:

- current tide phase
- next high/low when real or model events are available
- "rising now" / "falling now"
- tide source confidence

This needs backend support for next tide event, not only phase.

### 4. Tidal Coefficient / Tide Strength

The site uses a coefficient to communicate spring/neap strength and likely water movement.

Our equivalent should not claim the same coefficient unless we have the right source. Instead use:

- tide range estimate
- movement strength
- high / medium / low movement

This can be derived from event heights when real tide events or model sea-level data are available.

### 5. Pressure Trend Card

The site highlights pressure trend as a fishing signal.

Our engine already has pressure as an input, but not a true trend. A frontend card should wait until backend returns:

- current pressure
- pressure trend
- trend label

### 6. Swell Education

The site explains significant wave height and maximum wave risk.

Our frontend should keep the first version simpler:

- swell height
- swell direction
- exposed-water caution

Later:

- wave period
- surf risk copy
- exposed rocks warning

### 7. Solunar As Optional Module

The site includes major and minor periods based on lunar transit and moonrise/moonset.

For us this should be optional and clearly lower priority than tide, wind, swell, and support/reject logic.

Possible later module:

- major periods
- minor periods
- moon phase
- moon illumination

Do not let solunar dominate the recommendation in v1.

## What We Should Not Copy

- Long educational copy blocks in the core result page.
- Overloaded one-page layout for first mobile version.
- Any proprietary tide coefficient method or exact activity label system.
- Claims that generic searched coordinates are exact fishing spots.

## Proposed First UI Influence

For our frontend, borrow the content hierarchy but make it more decision-oriented:

1. Should I go?
2. Best window today.
3. Where nearby looks best: beach, rocks, jetty, bay / estuary edge.
4. Why: tide, wind, swell, pressure.
5. Confidence and data source.
6. Backup windows / alternatives.

## Backend Gaps This Reference Exposes

Useful future backend additions:

- next high/low tide event in API output
- tide movement strength derived from tide range
- pressure trend instead of only pressure value
- wave period in condition strip
- moon phase and illumination
- optional solunar periods
- compact daily timeline for tide + sun + best fishing windows

## Immediate Recommendation

Do not build a Tides4Fishing clone.

Use it as validation that fishing users expect weather, tide, moon, and swell in one place. Our product difference should be the location-support decision and nearby water-type scoring, which Tides4Fishing does not appear to make explicit for searched coordinates.
