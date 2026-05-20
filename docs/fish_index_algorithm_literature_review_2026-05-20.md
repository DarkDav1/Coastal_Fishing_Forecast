# Fish Index Algorithm Literature Review - 2026-05-20

This note evaluates the current public coastal fish-index logic against public agency guidance and peer-reviewed fisheries literature.

## Executive View

The current algorithm is directionally reasonable as a generic coastal/estuary forecast:

- It correctly treats moving water as more important than static high/low tide.
- It correctly rewards dawn/dusk and penalizes harsh midday.
- It separates fish opportunity from comfort and safety, which avoids hiding a good fish window behind unpleasant weather.
- It is appropriately cautious for searched coordinates rather than curated fishing spots.

The main weakness is that it uses tide-height change as a proxy for current. That is usable as a fallback, but NOAA explicitly warns that high/low tide timing and slack/maximum current timing are location-specific and cannot be inferred reliably from a generic rule of thumb. For bays and estuaries, the next improvement should be a current-aware tide module.

## Source Summary

| Factor | Evidence | Algorithm assessment |
| --- | --- | --- |
| Tide/current movement | NOAA says fish may concentrate during ebb or flood currents, and strong tidal currents can concentrate bait and smaller fish. NOAA also says tide height and current timing are not interchangeable at all locations. | Correct to reward moving water and penalize slack. Needs improvement because the model should distinguish vertical tide height from horizontal current speed. |
| Run-in / flood tide | Victorian Fisheries Authority notes run-in tide can be effective in lower estuary reaches and for Australian salmon/mullet. | Correct to reward early flood and rising tide, especially for sheltered estuary and bay edges. |
| Run-out / ebb tide | VFA flathead guidance says channel edges, drop-offs, weed beds and sandbank edges on a run-out tide can be productive. A tidal-flat study found higher fish number/biomass on ebb in that system. | Correct to keep ebb/falling tide as positive, but species and habitat should change the weight. |
| First and last light | VFA marks first/last light as prime estuary fishing time. Studies on gobies and rock sole found dawn/dusk feeding or activity peaks. | Strongly reasonable. Current +10 dawn/dusk bonus is defensible. |
| Habitat | VFA emphasizes jetties, rock walls, reefs, drop-offs, channel edges, weed beds, mudflats, and deep holes. USGS found stationary habitat and water-quality features interact in estuaries. | Habitat should matter, but nearby inferred structures must not inflate score. Use actual waterbody/habitat classification, not nearby map structures. |
| Temperature | A 2020 review reports temperature affects metabolism, feeding, digestion, and activity; effects vary by species and optimum range. | Directionally correct, but current fixed thresholds should become seasonal/species-aware. |
| Barometric pressure | One feeding study on yellow perch found no significant effect of barometric pressure on food intake. | Current pressure should stay a small weather-trend/support signal, not a major fish trigger. Direct pressure bonuses should be conservative. |
| Moon phase | Evidence is mixed. A tidal-flat study found moon/tide effects in one tropical system, while its references include studies that did not find moon effects in Queensland nocturnal assemblages. | Current low-weight moon bonus is acceptable, but it should not drive high scores by itself. |
| Wind/waves | Wind drives surface/current variability in estuaries and affects presentation, comfort, and safety. | Correct to use wind/wave heavily for trip and safety. For fish index, wind/wave should mainly act through exposure, water movement, turbidity, and presentation rather than broad blanket penalties. |

## Current Algorithm Fit

### What is solid

1. Moving-water logic is valid.

The algorithm rewards flood/ebb and penalizes slack. This matches NOAA and state-fisheries guidance. The Sandy Bay example where 05:00 low/slack is modest but 06:00 early flood is better is conceptually correct.

2. Dawn/dusk timing is valid.

The current sunrise/sunset weighting is supported by both angling guidance and fish-activity studies. This is one of the stronger components.

3. Separating fish index from comfort/safety is correct.

Fish may be active even when conditions are cold or unpleasant. Keeping fish opportunity separate from trip comfort is a better product model than a single blended score.

4. Conservative public-preview calibration is appropriate.

A searched coordinate is not a verified fishing spot. The algorithm should avoid 80+ scores unless multiple independent signals align.

### What is weak

1. Tide height is being overused as current.

The model infers flood/ebb/slack from sea-level shape. That is better than having no tide signal, but it is not the same as measured or predicted current speed. In some bays, current peaks can lag high/low water or occur near high/low water depending on local hydraulics.

2. Species differences are not explicit enough.

Flathead, bream, salmon, estuary perch, mulloway, and rock-edge species do not share one universal tide preference. The model has water-type modes, but not species or target-family profiles.

3. Estuary water quality is under-modeled.

Rainfall is used, but salinity, freshwater inflow, turbidity, and dissolved oxygen are missing. For river-influenced places like Port Huon, this can be a bigger driver than open-coast wave height.

4. Pressure should be downgraded.

Pressure trend can be a proxy for weather systems, but current fish-specific evidence is weak. It should help explain stability/shock, not create a high fish score.

5. Habitat needs to be sharper but safely separated from nearby structures.

The algorithm should not score nearby jetties or mapped access points. But it should eventually use confirmed habitat layers such as mudflat, weed bed, reef, channel edge, depth break, and estuary mouth condition where available.

## Recommended Improvements

### Priority 1 - Current-aware tide scoring

Add a tide-current confidence layer:

- High confidence: real current prediction or verified local tide/current station.
- Medium confidence: local tide station with known lag calibration.
- Low confidence: Open-Meteo sea-level curve only.

Then score moving water by current strength, not just tide phase. If only sea-level data exists, keep the current score capped.

### Priority 2 - Species / target-family profiles

Add optional scoring profiles:

- generic estuary
- bream / estuary perch
- flathead
- salmon / pelagic
- mulloway
- rocks / reef species

Each profile should have different tide, light, temperature, and habitat weights. The generic score can remain the default.

### Priority 3 - Estuary water-quality proxy

For river/estuary locations, add:

- recent river rainfall by catchment
- river-flow or level data where available
- turbidity proxy after rainfall
- salinity/freshwater influence proxy
- oxygen-risk proxy for closed or poorly flushed estuaries

This matters more for Port Huon-style locations than for open beaches.

### Priority 4 - Reduce direct pressure influence

Keep pressure trend in weather-shock logic, but reduce standalone pressure bonuses. A stable or changing pressure should not override weak tide movement, harsh light, poor water quality, or bad wind/wave setup.

### Priority 5 - Habitat layer without nearby-structure scoring

Keep map leads/access separate from score. For scoring, only use habitat if it describes the actual searched water or a confirmed waterbody segment:

- depth/channel edge
- mudflat/sandflat
- weed/seagrass
- reef/rocky edge
- estuary mouth / river channel
- open beach exposure

### Priority 6 - Calibration from outcomes

The algorithm is currently a physics/ecology heuristic. To improve beyond this, collect trip logs:

- searched place
- date/time
- target species
- method
- catch/no catch
- number/size class
- water clarity
- notes on baitfish/birds

Then tune weights by outcome instead of intuition.

## Bottom Line

The current model is credible as a generic coastal/estuary heuristic, but it should not be presented as a precise fish predictor. Its strongest parts are moving-water logic, dawn/dusk timing, wave/wind safety separation, and conservative public scoring. Its weakest part is tide-current inference. The next serious algorithm upgrade should be current-aware scoring plus species/habitat profiles.

## Sources

- NOAA National Ocean Service, tide/current importance for fishing: https://oceanservice.noaa.gov/education/tutorial_tides/tides09_monitor.html
- NOAA Tides & Currents FAQ, tide height vs tidal current timing: https://www.tidesandcurrents.noaa.gov/faq.html
- NOAA National Ocean Service, tides and currents overview: https://oceanservice.noaa.gov/navigation/tidesandcurrents/
- Victorian Fisheries Authority, Hopkins River estuary fishing guidance: https://vfa.vic.gov.au/recreational-fishing/fishing-locations/hopkins-river
- Victorian Fisheries Authority, flathead habitat and run-out tide guidance: https://vfa.vic.gov.au/recreational-fishing/fishing-locations/fishing-guides/flathead
- USGS / Marine and Coastal Fisheries, estuarine habitat and water-quality drivers: https://pubs.usgs.gov/publication/70226475
- Paiva et al. 2011, moon and tide effects on fish capture in a tropical tidal flat: https://www.cambridge.org/core/journals/journal-of-the-marine-biological-association-of-the-united-kingdom/article/abs/moon-and-tide-effects-on-fish-capture-in-a-tropical-tidal-flat/FBA783C53D6E35DA7B05B9C76D820101
- Antholz et al. 1991, brackish fjord feeding activity and dawn/dusk rhythms: https://link.springer.com/article/10.1007/BF02365521
- Sogard and Olla 2006, rock sole activity, temperature, dawn/dusk: https://www.sciencedirect.com/science/article/abs/pii/S0022098105002327
- Volkoff and Ronnestad 2020, effects of temperature on fish feeding and digestion: https://www.tandfonline.com/doi/full/10.1080/23328940.2020.1765950
- VanderWeyst 2014, barometric pressure and yellow perch feeding: https://pines.bemidjistate.edu/j-earth-life-sci/50/
