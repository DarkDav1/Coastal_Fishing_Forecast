# Australia Public Fishing And Boat Ramp Sources

This note records the public data sources checked for the generic coastal product. The product should only use these sources for map reference and trip planning. Access points, ramps, jetties, parking, and public fishing pins must not increase the fish score.

## Official Fishing Rule And Guide Sources

| State / territory | Official source to use | Product use |
| --- | --- | --- |
| NSW | NSW DPI FishSmart app and saltwater recreational fishing guide | Rules, local guides, closures, public fishing map references |
| QLD | Queensland Government recreational fishing rules and Qld Fishing 2.0 app | Rules, species limits, closures, responsible fishing notes |
| VIC | Victorian Fisheries Authority recreational fishing guide and Vic Fishing app | Rules, marine parks, safety warnings, guide copy |
| TAS | Fishing Tasmania / NRE Tasmania recreational fishing pages | Rules, recreational sea fishing information |
| WA | DPIRD recreational fishing pages and recreational fishing guide | Rules, licensing context, location-guide references |
| SA | PIRSA SA Fishing app | Rules, species limits, closures, app reference |
| NT | NT Government recreational fishing booklet and NT Fishing & Boating Mate app | Rules, access caveats, crocodile and Aboriginal land access warnings |
| ACT | ACT Government recreational fishing page | Inland-only rules, ACT reporting and NSW boundary caveats |

## Public Boat Ramp / Public Access Data Sources

| Priority | Jurisdiction | Source | Notes |
| --- | --- | --- | --- |
| Implemented | Tasmania | LIST WildFisheries sea fishing spots and LIST / MAST boat ramp layer | `structure_source=auto` queries these for Tasmanian coordinates. MAST ramps are map-only. |
| Implemented | NSW | Transport for NSW Maritime NSW Boat Ramps GeoJSON | Direct official import. Fee-required ramps are hidden when the source marks `FEE_PAYABLE`. |
| Implemented | QLD | Queensland Open Data recreational boating facilities | Direct official import. Only `Boat Ramp` / `Canoe Ramp` records are shown; jetties and pontoons are not imported as fishing structure. |
| Implemented | VIC | Boating Vic facilities API | Direct official import from the public Boating Vic facilities endpoint. Closed, hidden, or deleted ramps are skipped. |
| Implemented | WA | WA Department of Transport Public Boat Ramps DOT-033 public ArcGIS layers | Direct official import from sealed, unsealed, and paddle-craft ramp layers. |
| Implemented | SA | Location SA / DIT boat ramp layer | Direct official import from the Location SA topographic boat ramp layer. Closed/private comments are skipped. |
| Implemented | NT | NT Government public boat ramps Google My Maps KML | Direct import from the public NT Government ramp map linked on nt.gov.au. Closed warnings are skipped. |
| Implemented fallback | Australia-wide | OpenStreetMap Overpass | Used after the state/territory official source. Only explicit public/free access is shown. Private, customer-only, and fee-required ramps are hidden. |
| Not yet implemented | ACT | ACT Government boat ramp asset table | A public table exists, but the checked API rows did not expose usable coordinates. Keep OSM/manual inputs only until a coordinate-bearing source is confirmed. |

## Source Links Checked

- NSW DPI FishSmart app: https://www.dpi.nsw.gov.au/fishing/recreational/resources/fishsmart-app
- NSW DPI saltwater recreational fishing guide: https://www.dpi.nsw.gov.au/fishing/recreational/fishing-rules-and-regs/saltwater-recreational-fishing-guide
- Transport for NSW Maritime NSW Boat Ramps dataset: https://developer.transport.nsw.gov.au/data/dataset/maritime-nsw-boat-ramps
- Queensland recreational fishing rules: https://www.qld.gov.au/recreation/activities/boating-fishing/rec-fishing/rules
- Qld Fishing 2.0 app: https://www.qld.gov.au/recreation/activities/boating-fishing/rec-fishing/app
- Queensland recreational boating facilities dataset: https://www.data.qld.gov.au/dataset/recreational-boating-facilities-queensland
- Victorian Fisheries Authority recreational fishing guide PDF: https://vfa.vic.gov.au/recreational-fishing/recreational-fishing-guide/7786-VFA-2025-Rec-Fishing-Guide-2026-FA-3.0-Digital-1.pdf
- Boating Vic public facilities app/API: https://www.boating.vic.gov.au/
- Fishing Tasmania recreational fishing: https://fishing.tas.gov.au/recreational-fishing
- WA DPIRD recreational fishing: https://www.dpird.wa.gov.au/individuals/recreational-fishing/
- WA Public Boat Ramps DOT-033: https://catalogue.data.wa.gov.au/dataset/boat-ramps
- PIRSA SA Fishing app: https://pir.sa.gov.au/fishing-and-aquaculture/recreational-fishing/sa-fishing-app
- SA DIT boat ramp locations: https://dit.sa.gov.au/boating-facilities/boat-ramp-locations
- Location SA Boating Facilities metadata: https://www.location.sa.gov.au/lms/Reports/ReportMetadata.aspx?p_no=963
- NT Government recreational fishing rules: https://nt.gov.au/marine/recreational-fishing/rules/about-recreational-fishing
- NT Government public boat ramps: https://nt.gov.au/marine/for-all-harbour-and-boat-users/ramps-wharves-and-moorings/find-a-boat-ramp
- ACT recreational fishing: https://www.act.gov.au/environment/animals-and-plants/animals/wildlife-management/fish/recreational-fishing-in-the-act

## Inclusion Rules For Boat Ramps

- Show only public and free ramps when the source exposes access/fee fields.
- Hide `access=private`, `access=no`, `access=customers`, and `fee=yes`.
- Treat boat ramps as `public_access_only`: they can appear on the map but must not create fish-score, fish-potential, or “best fishing spot” uplift.
- Prefer official government layers over OSM when both are available.
- Deduplicate official and OSM items by nearby coordinate and facility group.
- Label uncertain OSM ramps conservatively. If public access is not explicit, do not show the item.

## Implementation Notes

- Current frontend map markers now support map-only public boat ramps separately from fishing access points.
- Boat ramp pins are intended for “where can I launch / access the water” only.
- Implemented official-source importers normalize into the existing `StructureFacility` shape with `type="boat_ramp"`, `access="public"`, `planner_eligible=false`, `map_eligible=true`, and `role="public_access_only"`.
- Automatic source selection uses an approximate Australian state/territory bounding box. This is a routing hint for official public-access data, not a fish-score input.
