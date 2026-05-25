# Australia Official Fishing Guide List

Checked on 2026-05-22.

This document is the guide-source list, not the raw point dataset list.

Generated coordinate outputs:

- `docs/generated/official_fishing_guide_locations_2026-05-22.json`
- `docs/generated/official_fishing_guide_locations_2026-05-22.csv`
- `docs/generated/nsw_sydney_harbour_go_fishing_spots_2026-05-22.json`
- `docs/generated/nsw_sydney_harbour_go_fishing_spots_2026-05-22.csv`
- `docs/generated/nsw_official_fad_and_reef_spots_2026-05-22.json`
- `docs/generated/nsw_official_fad_and_reef_spots_2026-05-22.csv`
- `docs/generated/nsw_offshore_artificial_reef_spots_2026-05-22.json`
- `docs/generated/nsw_offshore_artificial_reef_spots_2026-05-22.csv`
- `docs/generated/vic_go_fishing_spots_2026-05-22.json`
- `docs/generated/vic_go_fishing_spots_2026-05-22.csv`
- `docs/generated/vic_recreational_reef_spots_2026-05-22.json`
- `docs/generated/vic_recreational_reef_spots_2026-05-22.csv`
- `docs/generated/qld_official_fad_spots_2026-05-22.json`
- `docs/generated/qld_official_fad_spots_2026-05-22.csv`
- `docs/generated/qld_moreton_bay_artificial_reef_spots_2026-05-22.json`
- `docs/generated/qld_moreton_bay_artificial_reef_spots_2026-05-22.csv`
- `docs/generated/nt_official_offshore_spots_2026-05-22.json`
- `docs/generated/nt_official_offshore_spots_2026-05-22.csv`
- `docs/generated/nt_land_based_spots_2026-05-22.json`
- `docs/generated/nt_land_based_spots_2026-05-22.csv`
- `docs/generated/wa_artificial_reef_spots_2026-05-22.json`
- `docs/generated/wa_artificial_reef_spots_2026-05-22.csv`
- `docs/generated/wa_official_fad_spots_2026-05-22.json`
- `docs/generated/wa_official_fad_spots_2026-05-22.csv`
- `docs/generated/tas_hot_fishing_spots_2026-05-22.json`
- `docs/generated/tas_hot_fishing_spots_2026-05-22.csv`
- `docs/generated/sa_restored_reef_spots_2026-05-22.json`
- `docs/generated/sa_restored_reef_spots_2026-05-22.csv`
- `docs/generated/nt_sa_supplemental_fishing_spots_2026-05-22.json`
- `docs/generated/nt_sa_supplemental_fishing_spots_2026-05-22.csv`
- `docs/generated/au_relaxed_supplemental_fishing_spots_2026-05-24.json`
- `docs/generated/au_relaxed_supplemental_fishing_spots_2026-05-24.csv`
- `docs/generated/official_fishing_spots_combined_2026-05-22.json`
- `docs/generated/official_fishing_spots_combined_2026-05-22.csv`

The `official_fishing_guide_locations` outputs are first-pass guide-area map
pins. The `nsw_sydney_harbour_go_fishing_spots` outputs are the first
spot-level extraction from a NSW Go Fishing guide map. The `vic_go_fishing`
outputs are spot-level VFA guide locations, while `vic_recreational_reef_spots`
adds VFA recreational reef coordinates. The QLD, NT, WA FAD, and reef outputs
are official coordinate-bearing references, so they should be shown as
boat/offshore map references unless shore access is explicit. The
`qld_moreton_bay_artificial_reef_spots` outputs are official artificial reef map
coordinates from Queensland Government PDF maps. The `tas_hot_fishing_spots`
outputs are spot-level named places from the official Fishing Tasmania Hot
Fishing Spots guide pages. The NSW offshore reef and SA restored reef outputs
are coordinate-bearing official map references, not shore-access guides.
`nt_sa_supplemental_fishing_spots` is the relaxed-scope layer: government
parks/fishing pages, government-supported AFANT context, marine parks, local
tourism, and public fishing guides. Keep it visibly separate from strict
official coordinate tables. `au_relaxed_supplemental_fishing_spots` applies the
same relaxed standard nationally using state tourism, TEQ/Queensland, Visit NSW,
Visit Victoria, Tourism WA, and public/local fishing references.

The target source type is the Tasmania model:

- official or government-backed fishing guides
- "where to fish" pages
- regional fishing maps
- downloadable fishing-location guides
- app-backed official guide content

Do not treat boat ramp datasets as fishing guides. Boat ramps stay map-only access references.

## Closest Matches To Tasmania

| Rank | Jurisdiction | Guide source | Similarity to Tasmania Hot Fishing Spots | Import value |
| --- | --- | --- | --- | --- |
| 1 | Tasmania | Fishing Tasmania Hot Fishing Spots / Fishing Information Maps | Baseline source. 11 regional guides with where-to-fish, target species, gear advice, and maps. | Already the best pattern for regional guide extraction. |
| 1 | NSW | NSW DPI Fishing information: Local fishing guides + Go Fishing guides | Very close. It has local district guides plus named "Go Fishing" guides for bays, rivers, harbours, wharves, parks, dams, and coastal areas. | Best next state for extracting official guide-based fishing locations. |
| 2 | Victoria | VFA Fishing locations + coastal fishing spot pages | Close. Official VFA pages group coastal spots such as Port Phillip Bay, Western Port, Hopkins River, and artificial reefs. | Good for guide page extraction; fewer obvious downloadable regional maps than NSW/TAS. |
| 2 | WA | DPIRD Recreational Fishing Location Guide | Close in intent. It is an official location guide for identifying fishing locations and block numbers by WA bioregion. | Strong source, but likely needs PDF extraction. |
| 3 | NT | Land Based Fishing Guide - Darwin and Beyond | Close in content, but published by AFANT with NT Government grant support rather than as a direct NT.gov guide. | Useful candidate after licence/access review. |
| 4 | QLD | Qld Fishing 2.0 app + official recreational fishing pages | Official guide/app, but not a clear public "hot fishing spots" guide page. It points users to FADs, artificial reefs, boat facilities, stocked impoundments, rules, and species. | Use app/source discovery and official FAD/reef lists, not a guide-page scrape yet. |
| 5 | SA | PIRSA SA Fishing app | Official guide app, but mainly rules, closure maps, species info, catch reporting, and "commonly found near here" species. | Context/app source first; not a clean fishing-spot guide list yet. |
| 6 | ACT | ACT recreational fishing page/map | Official fishing rules/map, but inland freshwater only. | Out of v1 coastal scope. |

## Tasmania Baseline

| Source | Owner | What it contains | Count / scope | Product use |
| --- | --- | --- | --- | --- |
| Hot Fishing Spots | Fishing Tasmania / NRE Tasmania | Regional "where fish are biting" guides, maps, gear advice, species notes | 11 regional guides | Baseline for guide-to-map extraction |
| Recreational Sea Fishing Guide | Fishing Tasmania / NRE Tasmania | Rules, species, area restrictions, contacts, app handoff | 2025-26 sea fishing guide | Rule/context source |
| Fishing Tas app | Fishing Tasmania / NRE Tasmania | Current sea fishing information on phone/tablet | App source | User-facing rule/context reference |

Tasmania regional guide names:

1. Bruny D'Entrecasteaux Region
2. Derwent River
3. East Coast Region
4. Tasman Peninsula Region
5. St Helens Region
6. North East Coast and Flinders Island
7. Tamar River
8. Devonport and Port Sorell Region
9. North West Coast
10. King Island
11. Macquarie Harbour

Links:

- https://fishing.tas.gov.au/recreational-fishing/fishing-tips/hot-fishing-spots
- https://fishing.tas.gov.au/recreational-fishing/fishing-guides/recreational-sea-fishing-guide

## New South Wales

| Source | Owner | What it contains | Count / scope | Product use |
| --- | --- | --- | --- | --- |
| Fishing information - Local fishing guides | NSW DPI / DPIRD | District recreational fishing guides and restrictions | 25 local guides listed on the index | High-value regional guide extraction |
| Fishing information - Go Fishing Guides | NSW DPI / DPIRD | Named guide pages/PDFs for bays, rivers, harbours, wharves, parks, dams, and coastal towns | 26 Go Fishing guides listed on the index | Highest-value NSW source for named fishing places |
| Recreational Fishing Havens | NSW DPI / DPIRD | Coastal areas largely free of commercial fishing for better recreational fishing | 30 havens stated on NSW guide index; separate data catalogue currently describes 32 areas | Area/context layer |
| FishSmart app | NSW DPI / DPIRD | Rules, closures, maps, and fishing information | App source | User-facing rule/context reference |

NSW guide families to extract first:

- Sydney Harbour's Wharves, Piers and Parks
- Botany Bay
- Jervis Bay
- Lake Macquarie
- St Georges Basin
- Tuross Head
- Middle and North Harbour Parks and Reserves
- Parramatta and Lane Cove Rivers' Wharves and Parks
- Coffs Coast
- Hawkesbury River
- Bermagui
- Great Lakes
- Ulladulla
- Port Macquarie
- Batemans Bay

Links:

- https://www.dpi.nsw.gov.au/fishing/recreational/resources/info
- https://www.dpi.nsw.gov.au/fishing/recreational/resources/info/fishing-locations/go-fishing-sydney-harbours-wharves%2C-piers-and-parks
- https://www.dpi.nsw.gov.au/fishing/recreational/resources/info/fishing-locations/go-fishing-botany-bay

## Queensland

| Source | Owner | What it contains | Count / scope | Product use |
| --- | --- | --- | --- | --- |
| Qld Fishing 2.0 app | Queensland Government | Catch rules, FADs, boat facilities, stocked impoundments, artificial reefs, permits, species | App source | Official guide/app context |
| Recreational fishing guide | Queensland Government | Printed/general recreational fishing guide | Single guide, app recommended for latest rules | Rule/context source |
| Fish aggregating device pages | Queensland Government | FAD locations and status | Coordinate tables/pages | Boat/offshore map layer, not shore guide |
| Artificial reef dataset/pages | Queensland Government / Queensland Open Data | Recreational artificial reef sites | Data source | Boat/offshore map layer, not shore guide |

Current assessment:

- Queensland has official guide/app material, but I did not find a Tasmania-style public "hot fishing spots by region" guide page.
- For imports, use official FAD and artificial reef lists first, and keep looking for any public app API or guide dataset.

Links:

- https://www.qld.gov.au/recreation/activities/boating-fishing/rec-fishing/rules/guide
- https://www.qld.gov.au/environment/coasts-waterways/fishing
- https://www.qld.gov.au/recreation/activities/boating-fishing/rec-fishing/app/use
- https://www.qld.gov.au/recreation/activities/boating-fishing/rec-fishing/fish-aggregating-devices/find-a-fish-aggregating-device
- https://www.data.qld.gov.au/dataset/artificial-reef-sites-queensland

## Victoria

| Source | Owner | What it contains | Count / scope | Product use |
| --- | --- | --- | --- | --- |
| Fishing locations | Victorian Fisheries Authority | Inland and coastal fishing location profile links | Coastal categories include Port Phillip Bay, Western Port, Hopkins River, artificial reefs | Good guide-page extraction source |
| Fishing tips and tricks | Victorian Fisheries Authority | Species and general how-to guides | Multiple guide pages | Species/context source |
| Recreational fishing guide | Victorian Fisheries Authority | Statewide rules and guidance | Annual PDF guide | Rule/context source |
| GoFishVic app | Victorian Fisheries Authority | Official app reference | App source | User-facing rule/context reference |

Victoria coastal guide targets:

- Port Phillip Bay
- Western Port
- Hopkins River
- Artificial reefs
- VFA recreational fishing reefs pages

Links:

- https://vfa.vic.gov.au/recreational-fishing/fishing-locations
- https://vfa.vic.gov.au/recreational-fishing/fishing-locations/fishing-guides
- https://vfa.vic.gov.au/recreational-fishing/recreational-fishing-guide/7786-VFA-2025-Rec-Fishing-Guide-2026-FA-3.0-Digital-1.pdf

## Western Australia

| Source | Owner | What it contains | Count / scope | Product use |
| --- | --- | --- | --- | --- |
| Recreational Fishing Location Guide | DPIRD WA | Fishing locations, sites, maps, depths, and block numbers by bioregion | One official PDF publication | Strong WA equivalent to a location guide; needs PDF extraction |
| Recreational fishing guides page | DPIRD WA | Recreational fishing guide collection | Guide index | Rule/context source |
| Rules map | DPIRD WA | Rules, species, marine protected areas, bioregions | Web map | Rule/context source |

Current assessment:

- WA's location guide is the closest WA source to the Tasmania guide concept.
- It is probably not a clean point list; extract location names, region/block, and map references first.

Links:

- https://library.dpird.wa.gov.au/fr_fop/58/
- https://www.dpird.wa.gov.au/individuals/recreational-fishing/recreational-fishing-guides/
- https://rules.fish.wa.gov.au/

## South Australia

| Source | Owner | What it contains | Count / scope | Product use |
| --- | --- | --- | --- | --- |
| SA Fishing app | PIRSA | Official recreational fishing app, species, rules, closure maps, reporting, fish commonly found near location | App source | Rule/context and possible future app-source discovery |
| Recreational fishing page | PIRSA | Rules, fisheries management, SA Fishing app entry | Web guide hub | Rule/context source |

Current assessment:

- SA has an official app and guide hub, but I did not find a public Tasmania-style fishing-spot guide list.
- Do not import "species commonly found near here" as a fishing spot list.

Links:

- https://pir.sa.gov.au/sa-fishing-app
- https://www.pir.sa.gov.au/recreational_fishing/safishingapp
- https://pir.sa.gov.au/rec-fishing

## Northern Territory

| Source | Owner | What it contains | Count / scope | Product use |
| --- | --- | --- | --- | --- |
| NT Fishing and Boating Mate app | NT Government | Fishing and boating rules, tides, wind, safe boating, app map/reporting | App source | Official app/context source |
| Land Based Fishing Guide - Darwin and Beyond | AFANT, supported by NT Government Recreational Fishing Grant | Land-based locations around Darwin, Palmerston, Dundee, Katherine, with baits, tides, seasons, tips | 64-page guidebook | Closest NT guide, but not directly a government publication |
| NT artificial reefs / FAD pages | NT Government | Fishing areas, reef/FAD rules and positions | Web pages | Boat/offshore map layer and rule context |

Current assessment:

- The land-based guide is the closest NT match to Tasmania's "where to fish" guides, but confirm rights before importing.
- For official-only import, start with NT Government artificial reef/FAD pages and app context.

Links:

- https://newsroom.nt.gov.au/article?id=d4d5c0c51cf85336de71aee82b553b05
- https://afant.com.au/lbfg-darwin/
- https://daf.nt.gov.au/news/2025/guide-to-land-based-fishing-now-available
- https://nt.gov.au/marine/recreational-fishing/when-and-where-to-fish/rules-for-fishing-in-specific-areas

## Australian Capital Territory

| Source | Owner | What it contains | Count / scope | Product use |
| --- | --- | --- | --- | --- |
| Recreational fishing in the ACT | ACT Government | ACT public fishing waters, rules, map, open/trout/prohibited waters | Inland freshwater only | Out of coastal v1 scope |

Link:

- https://www.act.gov.au/environment/animals-and-plants/animals/wildlife-management/fish/recreational-fishing-in-the-act

## Practical Next Import Order

1. NSW guide index: extract NSW local guides and Go Fishing guide URLs, then parse coastal guide pages/PDFs for named locations.
2. Tasmania baseline: keep current 11-region guide model as the extraction template.
3. Victoria fishing locations: crawl coastal profile pages and artificial reef pages.
4. WA DPIRD location guide: extract PDF tables/maps into region-level candidate locations.
5. NT land-based guide: confirm permissions; if acceptable, treat as guide-derived locations, not pure government data.
6. Queensland and South Australia: keep as official app/context sources until a public "where to fish" guide list or app data endpoint is found.

## Count Summary

These are guide-source counts, not total fishing spots:

| Jurisdiction | Count found now | Meaning |
| --- | ---: | --- |
| TAS | 11 guides / 131 named spots | Regional hot fishing spot guides and extracted named places |
| NSW | 25 + 26 / 123 extracted spots | 25 local fishing guides plus 26 Go Fishing guides on the official index, with FADs, reefs, and relaxed tourism references extracted |
| VIC | 4 coastal location categories / 79 extracted spots | Port Phillip Bay, Western Port, Hopkins River, artificial reefs, and relaxed tourism references |
| WA | 1 guide / 74 extracted FAD, reef, and relaxed references | Statewide recreational fishing location guide plus official FAD/reef map layers and Tourism WA references |
| QLD | 1 app/guide hub / 147 extracted FAD, reef, and relaxed references | Official app/guide context plus FAD, artificial reef, and TEQ/Queensland tourism references |
| SA | 1 app/guide hub / 39 extracted references | Official app/guide context, Windara Reef, and relaxed-scope public fishing/tourism references |
| NT | 1 close guide candidate / 43 extracted spots | AFANT land-based guide with NT Government support, plus official FAD, reef, parks, and land-based references |
| ACT | 1 inland page/map | Out of coastal v1 scope |

Immediate answer: the closest Tasmania-style guide sources are NSW, Victoria, WA, and the NT land-based guide candidate. NSW is clearly the best next target because it has many official named guide pages and PDFs.

## Generated Spot-Level Counts

| Output | Count | Notes |
| --- | ---: | --- |
| TAS Hot Fishing Spots | 131 | Spot-level named places from Fishing Tasmania's 11 official regional guides |
| NSW Sydney Harbour Go Fishing spots | 70 | Spot-level land-based wharf, pier, park, reserve, beach, and shoreline candidates |
| NSW offshore artificial reef spots | 10 | Official offshore reef coordinates from Sydney, Southern Sydney, Wollongong, Terrigal, Port Macquarie, and Merimbula |
| VIC Go Fishing spots | 31 | 10 Western Port Bay, 13 South West, and 8 Port Phillip Bay locations; freshwater-only lakes are marked `future_freshwater` |
| VIC recreational reef spots | 36 | VFA reef coordinates: Corio Bay, Port Phillip boat-based reefs, Kingfish Reef, Kayaker's Reef, and Torquay Offshore Reef |
| QLD official FAD spots | 51 | Official FAD coordinates; boat/offshore only |
| QLD Moreton Bay artificial reef spots | 78 | Official artificial reef map coordinates from 8 Moreton Bay reef sites; boat/offshore only |
| NT official offshore spots | 22 | Official FAD and artificial reef coordinates; boat/offshore only |
| NT land-based spots | 4 | Government or government-managed pages naming public land-based fishing locations |
| NSW official FAD and estuarine reef spots | 31 | 22 official FAD / bait marker coordinates and 9 estuarine artificial reef coordinates |
| WA artificial reef spots | 10 | WA artificial reef coordinates, including Dampier from the DPIRD public reef map layer |
| WA official FAD spots | 49 | DPIRD public FAD map layer; includes deployment status for active, not deployed, and broken-free devices |
| SA restored reef spots | 1 | Windara Reef government coordinate reference; map/context only until current rules are checked |
| NT/SA supplemental fishing spots | 55 | Relaxed-scope layer: 17 NT and 38 SA public fishing references from government parks pages, government-supported guides, marine parks, local tourism, and public fishing guides |
| AU relaxed supplemental fishing spots | 57 | Final relaxed-scope national pass: 12 NSW, 18 QLD, 12 VIC, and 15 WA public fishing references |
| Combined official spot feed | 636 | NSW + TAS + VIC + QLD + NT + WA + SA spot-level outputs with no missing coordinates; includes strict official and relaxed-scope supplemental layers |
