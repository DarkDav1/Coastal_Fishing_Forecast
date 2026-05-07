# Frontend Reference: Windy.app Fishing Spot (2026-04-28)

Reference page studied:

- https://windy.app/fishing/spot/381583/Hobart

This note is for product and frontend planning only. Do not copy site text, media, layout, or proprietary scoring. Use it as a reference for page structure and forecast presentation.

## What The Site Does

Windy.app presents a fishing forecast as a spot page.

Main visible sections:

- spot title and coordinates
- day selector
- sunrise and sunset
- biting score percentage
- best time summary
- hourly biting scores
- current conditions
- solunar activity report
- air condition explanation
- moon phase explanation
- about spot photo gallery
- nearby spots
- nearest meteostation
- archive / reviews / top spots

Compared with Tides4Fishing, Windy.app is more compact and more spot-oriented. It leads with a score and hourly forecast rather than a long educational tide page.

## High-Value Ideas For Our Frontend

### 1. Hero Score With Best Time Copy

Windy.app uses a clear percentage score and a plain sentence about the best fishing times.

Our equivalent:

- overall recommendation score
- best window label
- short sentence: "Best nearby option: beach in the morning"
- confidence badge beside the score

We should avoid implying exact local certainty for searched coordinates.

### 2. Hourly / Window Score Strip

Windy.app shows scores across the day at intervals.

Our first version can show:

- morning
- day
- dusk

Later:

- 2-hour or 3-hour timeline
- score, tide phase, wind, swell per time block

This is a strong frontend direction because it lets users compare when to go.

### 3. Current Conditions Card

Windy.app puts current temperature, feels-like, wind, pressure, humidity, sea temperature, UV, cloud cover, visibility, moonrise, and moon phase in one compact block.

Our first version should use:

- wind
- swell
- tide
- pressure
- confidence / data source

Later:

- water temperature
- UV
- visibility
- humidity
- moonrise / moonset

### 4. Solunar Explanation As Secondary Copy

Windy.app includes a generated report explaining current activity and best days.

For our product:

- keep solunar optional
- do not let it dominate tide / wind / swell / water-type support
- use it as a secondary signal when added

### 5. Nearby Spots

Windy.app lists nearby spots with distance and current weather snippets.

For our product:

- near-term: nearby search candidates or alternative coastal places
- later: curated supported spots with higher confidence
- do not invent local spot quality from generic coordinate search

### 6. Nearest Meteostation

Windy.app shows closest weather station information.

For our frontend:

- show nearest tide station when TidesAtlas or official station data is used
- show station distance
- show caution when remote
- for Open-Meteo model tide, show "model tide" instead of station

## What We Should Not Copy

- Single "biting score" as the only product answer.
- Spot photo gallery as a first milestone.
- User reviews or local community features.
- A claim that generic searched coordinates are exact spots.
- Species certainty without real species model support.

## Proposed UI Influence

Use Windy.app's compact spot-page pattern for our first result page:

1. location header
2. overall score and confidence
3. best window summary
4. window score strip
5. condition chips
6. water-type cards
7. explanation and risks
8. nearby alternatives or unsupported state

This is better for our first frontend than a long tide-table style page.

## Backend Gaps This Reference Exposes

Useful future backend additions:

- more granular hourly or 3-hour scoring
- sunrise and sunset in API output
- moonrise and moonset
- moon phase
- current-condition snapshot
- water temperature
- UV index
- visibility
- nearest weather station metadata
- nearest tide station metadata

## Difference From Our Product

Windy.app is spot-first. Our v1 is searched-coordinate preview first.

Our differentiator should remain:

- clear supported / unsupported decision
- lower confidence for generic searched coordinates
- nearby water-type opportunity cards
- explicit data-source confidence, especially for tide data
