# Australia Official Fishing Spot Source List

Checked on 2026-05-22 for the generic coastal fishing forecast product.

This list follows the Tasmania map-layer pattern:

- Official fishing spots, fishing platforms, artificial reefs, and fish aggregating devices can become fishing-location candidates only when the source clearly says they are for recreational fishing.
- Boat ramps and launch sites are public-access reference points only. They must stay `map_eligible=true`, `planner_eligible=false`, and must not lift the fish score.
- Closure maps, marine park zones, habitat layers, rules pages, and species-range maps are context layers. They should not create a recommended fishing spot by themselves.
- Inland freshwater lists are recorded here for future expansion, but v1 remains coastal saltwater and estuary only.

## Import Priority

| Priority | Jurisdiction | Source | What it gives us | First product use |
| --- | --- | --- | --- | --- |
| 1 | TAS | Fishing Tasmania Hot Fishing Spots | Official named coastal, estuary, wharf, beach, jetty, bay, and shoreline fishing places | Direct spot candidates, using the Tasmania guide pattern |
| 1 | NSW | NSW DPI / DPIRD Interactive Map for Recreational Fishers | Recreational fishing havens, artificial reefs, FADs, accessible fishing platforms, closures, marine park zones | Best next NSW fishing-location layer because it contains explicit recreational fishing features |
| 1 | QLD | Queensland FAD list and Moreton Bay artificial reef maps | Coordinate-bearing offshore fishing structures and artificial reefs | Boat/offshore fishing candidates; not shore access |
| 1 | NT | NT Government artificial reef, FAD, parks/fishing pages, plus government-supported AFANT context | Coordinate-bearing artificial reefs/FADs plus named public land-based fishing references | Boat/offshore, shore, and relaxed-scope candidates, with strong safety warnings |
| 2 | VIC | VFA recreational fishing reefs | Completed recreational reef projects, including shore, boat, kayak, estuary, and offshore reefs | Added coordinate-bearing reef references from linked pages |
| 2 | WA | DPIRD FAD and artificial reef map layers plus Recreational Fishing Location Guide | Official FADs, artificial reefs, and WA bioregion guide context | FAD/reef map references now extracted; PDF guide still needs table extraction |
| 3 | SA | PIRSA SA Fishing app, SA marine park/fishing reports, tourism/council guides, and Windara Reef references | Official rules app plus relaxed-scope public fishing references | Context and supplemental map candidates; no clean PIRSA spot API found yet |
| 3 | National relaxed-scope | Visit NSW, Queensland/TEQ, Visit Victoria, Tourism WA, tourism/council/public fishing pages | Named coastal, estuary, jetty, beach, harbour and river-mouth public fishing references | Supplemental map candidates with lower source confidence |
| 4 | ACT | ACT recreational fishing map/page | Inland public waters and trout/open/prohibited water rules | Out of v1 coastal scope |

## Source Classes

| Class | Meaning | Can affect fish score? | Can appear on map? |
| --- | --- | --- | --- |
| `official_fishing_spot` | Explicit government fishing spot, platform, or fishing area | No direct score boost | Yes |
| `artificial_reef` | Artificial reef built or listed for recreational fishing | No direct score boost | Yes, mostly boat/offshore mode |
| `fad` | Fish aggregating device | No direct score boost | Yes, boat/offshore mode only |
| `recreational_fishing_haven` | Area reserved or managed for recreational fishing | No direct score boost | Yes, as an area/context layer |
| `boat_ramp` | Launch/access point | No | Yes, map-only |
| `rule_context` | Closures, marine parks, rules, species ranges, habitat | No | Yes, as warning/context only |
| `supplemental_public_fishing_access_candidate` | Relaxed-scope public fishing reference from tourism, local council, government-supported guide, or public fishing guide | No direct score boost | Yes, with a lower source-confidence label |

## National Relaxed-Scope Pass

| Source | Official owner | Contains | Data shape | Product classification | Import note |
| --- | --- | --- | --- | --- | --- |
| Visit NSW coastal fishing articles and regional pages | Destination NSW / Visit NSW | Public fishing references around Eurobodalla, Central Coast, Coffs Harbour, Jervis Bay and Bermagui | Web pages | `supplemental_public_fishing_access_candidate` | Added 12 NSW relaxed-scope rows. |
| Queensland / TEQ tourism and drive guides | Tourism and Events Queensland / Queensland tourism | Public fishing references such as Urangan Pier, Gold Coast creeks, Pumicestone Passage, 1770, Tannum Sands and North Queensland jetties | Web/PDF tourism guides | `supplemental_public_fishing_access_candidate` | Added 18 QLD relaxed-scope rows. |
| Visit Victoria fishing and coastal attraction pages | Visit Victoria | Pier, surf, bay and inlet references such as Rosebud, Apollo Bay, Lakes Entrance, Cape Conran, Inverloch and Mallacoota | Web pages | `supplemental_public_fishing_access_candidate` | Added 12 VIC relaxed-scope rows. |
| Tourism Western Australia attraction and destination pages | Tourism WA | Jetty, beach, harbour and river-mouth references across WA | Web pages | `supplemental_public_fishing_access_candidate` | Added 15 WA relaxed-scope rows. |

## Tasmania

| Source | Official owner | Contains | Data shape | Product classification | Import note |
| --- | --- | --- | --- | --- | --- |
| Hot Fishing Spots / Fishing Information Maps | Fishing Tasmania / NRE Tasmania | 11 official regional guide pages with named places such as wharves, jetties, beaches, bays, estuary edges, points, rivers, and shorelines | Web guide pages plus downloadable maps | `official_fishing_spot` | Added 131 named spot candidates with coordinates. Keep `score_impact=none`; verify local closures and access before planning use. |

Official links:

- https://fishing.tas.gov.au/recreational-fishing/fishing-tips/hot-fishing-spots/fishing-information-maps

## New South Wales

| Source | Official owner | Contains | Data shape | Product classification | Import note |
| --- | --- | --- | --- | --- | --- |
| Interactive Map for Recreational Fishers | NSW DPI / DPIRD | Closures, recreational fishing havens, artificial reefs, FADs, trout waters, marine protected areas, accessible fishing platforms | Web map / FishSmart app layer | Mixed: `official_fishing_spot`, `artificial_reef`, `fad`, `rule_context` | Highest-value NSW source. Need inspect map services and split feature layers by type. |
| Recreational Fishing Havens | Data.NSW / DPIRD | 32 areas set aside along the NSW coast for recreational fishing | ArcGIS REST, WMS, metadata | `recreational_fishing_haven` | Use as area layer, not exact point. Good confidence because the dataset is explicitly recreational fishing. |
| Fish Aggregating Devices | NSW DPIRD | Seasonal FAD coordinates, distance from access point, depth | HTML coordinate table and Google map | `fad` | Boat/offshore only. Needs seasonal status handling. |
| Estuarine artificial reefs | NSW DPIRD | Estuarine reef locations, coordinates, reef balls, depth | HTML coordinate table | `artificial_reef` | Boat/estuary reef candidates. Not shore access. |
| Offshore artificial reef pages | NSW DPIRD | Sydney, Southern Sydney JD, Wollongong, Terrigal, Port Macquarie, Merimbula and other reef pages with coordinates/species/depth | Individual HTML/PDF pages | `artificial_reef` | Added 10 coordinates from the main public offshore reef pages. |
| Go Fishing regional guides | NSW DPI / DPIRD | Regional fishing maps, local guidance, restrictions | PDFs | `official_fishing_spot` or `rule_context` after review | Manual extraction first; useful for shore and estuary guide copy. |
| NSW Boat Ramps | Transport for NSW | Boat ramps | GeoJSON | `boat_ramp` | Already implemented as map-only access. |

Official links:

- https://www.dpi.nsw.gov.au/fishing/recreational/plan-your-next-fishing-trip-interactive-map-for-recreational-fishers
- https://data.nsw.gov.au/data/dataset/recreational-fishing-havens
- https://www.dpi.nsw.gov.au/fishing/recreational/resources/fish-aggregating-devices
- https://www.dpi.nsw.gov.au/fishing/recreational/resources/artificial-reef/estuarine-artificial-reefs
- https://www.dpi.nsw.gov.au/fishing/recreational/resources/artificial-reef/sydney-offshore-artificial-reef
- https://www.dpi.nsw.gov.au/fishing/recreational/resources/artificial-reef/southern-sydney
- https://www.dpi.nsw.gov.au/fishing/recreational/resources/artificial-reef/wollongong-offshore-artificial-reef
- https://www.dpi.nsw.gov.au/fishing/recreational/resources/artificial-reef/terrigal-offshore-artificial-reef
- https://www.dpi.nsw.gov.au/fishing/recreational/resources/artificial-reef/port-macquarie-recreational-fishing-reef
- https://www.dpi.nsw.gov.au/fishing/recreational/resources/artificial-reef/merimbula-offshore-artificial-reef

## Queensland

| Source | Official owner | Contains | Data shape | Product classification | Import note |
| --- | --- | --- | --- | --- | --- |
| Qld Fishing 2.0 app / recreational fishing page | Queensland Government | FADs, boat facilities, stocked impoundments, artificial reefs, rules | App and web pages | Mixed | Good official product index, but app data may need web/API discovery. |
| Find a fish aggregating device | Queensland Government | Surface and subsurface FAD names, coordinates, distance, depth, deployed status text | HTML coordinate table and map | `fad` | High priority for boat/offshore mode. Page says to check status before trips. |
| Artificial reef sites - Queensland | Queensland Open Data | Artificial reef sites designed specifically for recreational fishing | SHP/TAB/FGDB/KMZ/GPKG | `artificial_reef` | Best machine-readable QLD reef source. |
| Moreton Bay artificial reefs | Queensland Parks / DETSI | Eight Moreton Bay artificial reefs and map coordinates | Web page and linked PDF maps | `artificial_reef` | Added 78 official map coordinates as boat/offshore references. |
| Recreational boating facilities | Queensland Open Data | Boat ramps and boating facilities | API/open data | `boat_ramp` | Already implemented as map-only access. |
| Stocked Impoundment Permit Scheme locations | Queensland Government | Stocked dams and weirs with target species | HTML list | Future freshwater only | Out of v1 coastal scope. Keep for later inland module. |

Official links:

- https://www.qld.gov.au/environment/coasts-waterways/fishing
- https://www.qld.gov.au/recreation/activities/boating-fishing/rec-fishing/app/use
- https://www.qld.gov.au/recreation/activities/boating-fishing/rec-fishing/fish-aggregating-devices/find-a-fish-aggregating-device
- https://www.data.qld.gov.au/dataset/artificial-reef-sites-queensland
- https://parks.qld.gov.au/parks/moreton-bay/zoning/trial_artificial_reef_program
- https://www.data.qld.gov.au/dataset/recreational-boating-facilities-queensland
- https://www.qld.gov.au/recreation/activities/boating-fishing/rec-fishing/dams/stocked-impoundment-permits/locations

## Victoria

| Source | Official owner | Contains | Data shape | Product classification | Import note |
| --- | --- | --- | --- | --- | --- |
| Recreational Fishing Reefs | Victorian Fisheries Authority | Completed recreational reefs: Corio Bay rocky reefs, Port Phillip Bay shellfish reefs, boat-based reefs, shore-based reefs, kingfish reef, kayaker's reef, Gippsland estuarine reefs, Torquay offshore reef | Hub page with linked project pages | `artificial_reef` / `official_fishing_spot` depending on reef type | Added 36 coordinates from Corio Bay, boat-based reefs, Kingfish Reef, Kayaker's Reef, and Torquay. |
| Torquay reef / FAD pages | Victorian Fisheries Authority | Torquay reef boundary coordinates and seasonal FAD context | Web pages/PDFs | `artificial_reef`, `fad` | Torquay reef boundary is added; seasonal FAD status still needs a current source before active display. |
| Recreational Fish Habitat | Data Vic / DEECA, commissioned by VFA | Key habitat locations for recreational marine species in major bays and inlets | DWG/DXF/GDB/SHP/MIF/TAB | `rule_context` / habitat context | Not a public access list and not a recommendation by itself. Useful later for confidence/context. |
| Boating Vic facilities | Victorian Government | Boat ramps and boating facilities | API | `boat_ramp` | Already implemented as map-only access. |

Official links:

- https://vfa.vic.gov.au/recreational-fishing/fishing-locations/recreational-fishing-reefs
- https://vfa.vic.gov.au/about/media-releases/torquay-reef-welcomes-fish-attracting-devices
- https://vfa.vic.gov.au/about/news/fad-tastic-summer-ahead-for-southwest-fishers
- https://discover.data.vic.gov.au/dataset/recreational-fish-habitat
- https://www.boating.vic.gov.au/

## Western Australia

| Source | Official owner | Contains | Data shape | Product classification | Import note |
| --- | --- | --- | --- | --- | --- |
| Recreational Fishing Location Guide | DPIRD WA | Official fishing locations, sites, maps, depths, and block numbers by bioregion | PDF publication | `official_fishing_spot` after extraction | Best WA candidate. Needs PDF table/map extraction and coordinate/block interpretation before import. |
| Fish aggregating devices | DPIRD WA | Public FAD map with coordinates and current deployment status | ArcGIS web map / feature layer | `fad` | Added 49 FAD records; filter by deployment status before active recommendations. |
| Artificial reefs | DPIRD WA | Public artificial reef page and map layer | Web page and ArcGIS feature layer | `artificial_reef` | Added 10 reef records, including Dampier from the public reef layer. |
| WA recreational fishing rules map | DPIRD WA | Location-based rules, common species, marine protected areas, bioregions | Web map/search | `rule_context` | Good context layer; not enough by itself to create a spot. |
| Recreational Fishing Regions (DPIRD-096) | WA data catalogue / DPIRD | WA recreational fishing regions | ArcGIS/WFS/WMS | `rule_context` | Region boundary layer, not spot list. |
| Public Boat Ramps DOT-033 | WA Department of Transport | Boat ramps | ArcGIS layers | `boat_ramp` | Already implemented as map-only access. |

Official links:

- https://library.dpird.wa.gov.au/fr_fop/58/
- https://www.dpird.wa.gov.au/individuals/recreational-fishing/recreational-fishing-guides/
- https://www.dpird.wa.gov.au/individuals/recreational-fishing/recreational-fishing-initiatives/fish-aggregating-devices/
- https://www.dpird.wa.gov.au/individuals/recreational-fishing/recreational-fishing-initiatives/artificial-reefs/
- https://rules.fish.wa.gov.au/
- https://catalogue.data.wa.gov.au/dataset/recreational-fishing-regions-dpird-096
- https://catalogue.data.wa.gov.au/dataset/boat-ramps

## South Australia

| Source | Official owner | Contains | Data shape | Product classification | Import note |
| --- | --- | --- | --- | --- | --- |
| SA Fishing app | PIRSA | Rules, closure maps, aquatic reserves, species found near current location, catch reporting | App and web description | `rule_context` | Official but no clean public point dataset found in this pass. Do not import "species found here" as fishing spots. |
| Marine parks / recreational fishing reports | SA Environment / Marine Parks | Fishing opportunities, Windara Reef, reservoir opening and facility projects | PDFs/web reports | `rule_context`, possible future project leads | Good policy context, not a clean coordinate-bearing list. |
| Windara Reef coordinate reference | South Australian Government / DIT and DEW | Restored shellfish reef near Ardrossan with government coordinate reference and marine-park/fishing context | Web page / notice | `rule_context` / `artificial_reef` map reference | Added as a map/context point only; check current marine park rules before any trip advice. |
| Marine Parks fishing page | South Australian Marine Parks | Iconic public fishing experiences such as Waitpinga, Locks Well, Browns Beach, Second Valley Jetty and Stenhouse Bay Jetty | Web page | `supplemental_public_fishing_access_candidate` | Added selected named public fishing references as relaxed-scope rows. |
| Elliston fishing information | Elliston official tourism | Local named fishing places around Elliston including Waterloo Bay, Boords Beach, Elliston Jetty, Anxious Bay and Sheringa Beach | Web page | `supplemental_public_fishing_access_candidate` | Added selected local guide references as relaxed-scope rows. |
| Fleurieu Coast local fishing spots | Visit Fleurieu Coast / District Council of Yankalilla | Local fishing spot guide for Fleurieu coast locations | PDF guide | `supplemental_public_fishing_access_candidate` | Added selected jetty/coastal references as relaxed-scope rows. |
| SA tourism and WE ARE.SA fishing references | South Australian tourism / Government of South Australia | Public fishing and jetty references across SA | Web pages | `supplemental_public_fishing_access_candidate` | Added selected public jetties, beaches and river-mouth spots as relaxed-scope rows. |
| Location SA / DIT boat ramp layer | SA Government | Boat ramps | ArcGIS/map layer | `boat_ramp` | Already implemented as map-only access. |

Official links:

- https://pir.sa.gov.au/sa-fishing-app
- https://www.pir.sa.gov.au/recreational_fishing/safishingapp
- https://dit.sa.gov.au/news/feed?a=408138
- https://www.environment.sa.gov.au/goodliving/posts/2019/05/windara-reef
- https://www.marineparks.sa.gov.au/enjoy/fishing
- https://elliston.com.au/attractions/fishing-information/
- https://www.visitfleurieucoast.com.au/webdata/resources/files/A35%20Local%20Fishing%20Spots.pdf
- https://www.weare.sa.gov.au/news/2023/q4/top-fishing-spots-in-south-australia
- https://dit.sa.gov.au/boating-facilities/boat-ramp-locations
- https://www.location.sa.gov.au/lms/Reports/ReportMetadata.aspx?p_no=963

## Northern Territory

| Source | Official owner | Contains | Data shape | Product classification | Import note |
| --- | --- | --- | --- | --- | --- |
| Artificial reefs in the NT | NT Government | Engineered reef complexes, Fenton Patches, Darwin Harbour, Lee Point and other artificial reefs with coordinates/depth/species on many entries | HTML tables/details | `artificial_reef` | High priority for NT boat/offshore mode. Must show crocodile, remoteness, and reef-fish protection warnings. |
| NT fish aggregating devices | NT Government | FAD coordinates and safety notes | HTML coordinate list | `fad` | High priority, but seasonal/current status must be checked. |
| Land Based Fishing Guide - Darwin and Beyond | AFANT with NT Recreational Fishing Grants support, announced by NT DAF | Land-based fishing opportunities around Darwin, Palmerston, Dundee, Katherine | Guidebook, not directly available as open data in this pass | `official_fishing_spot` only after manual review | Useful lead, but not a government dataset. Confirm licence/access before import. |
| Stokes Hill Wharf | Darwin Waterfront / NT Government | Dedicated fishing platform and artificial reefs in front of the platform | Web page | `official_fishing_spot` | Added as a land-based candidate with access and crocodile review required. |
| NT parks fishing references | NT Government | Parks/reserves where fishing is allowed with named access points such as Rapid Creek fishing platform and Lee Point Rocks | Web page | `official_fishing_spot` / `rule_context` | Added named land-based candidates where the official page explicitly lists fishing locations. |
| Mandorah Marine Facilities | Infrastructure NT | Mandorah Jetty retained for ferry services and recreational fishers, with future fishing-platform improvements | Project page | `official_fishing_spot` | Added as a land-based candidate; check construction impacts before user-facing planning. |
| AFANT Land Based Fishing Guide - Darwin & Beyond | AFANT, supported by NT Government Recreational Fishing Grant | Public guide context for Darwin, Palmerston, Dundee and Katherine land-based fishing | Guidebook public page | `supplemental_public_fishing_access_candidate` | Added selected public land-based candidates as relaxed-scope rows; full guidebook requires permission/source text. |
| NT public boat ramps | NT Government | Public boat ramps | KML/My Maps | `boat_ramp` | Already implemented as map-only access. |

Official links:

- https://nt.gov.au/marine/recreational-fishing/when-and-where-to-fish/rules-for-fishing-in-specific-areas
- https://nt.gov.au/marine/recreational-fishing/when-and-where-to-fish/artificial-reefs/rules-for-using-a-fishing-aggregating-device
- https://www.waterfront.nt.gov.au/stokes-hill-wharf
- https://nt.gov.au/parks/safety-rules/boating-and-fishing-in-parks
- https://infrastructure.nt.gov.au/project/mandorah-marine-facilities
- https://daf.nt.gov.au/news/2025/guide-to-land-based-fishing-now-available
- https://afant.com.au/lbfg-darwin/
- https://www.waterfront.nt.gov.au/stokes-hill-wharf
- https://nt.gov.au/marine/for-all-harbour-and-boat-users/ramps-wharves-and-moorings/find-a-boat-ramp

## Australian Capital Territory

| Source | Official owner | Contains | Data shape | Product classification | Import note |
| --- | --- | --- | --- | --- | --- |
| Recreational fishing in the ACT | ACT Government | Open waters, trout waters, prohibited waters, ACT recreational fishing map | Web page/map | Future freshwater only | Out of current coastal/estuary v1 scope. Keep only as future inland module reference. |

Official link:

- https://www.act.gov.au/environment/animals-and-plants/animals/wildlife-management/fish/recreational-fishing-in-the-act

## First Import Backlog

1. NSW: inspect the DPI/DPIRD interactive map services and import layers for accessible fishing platforms, artificial reefs, FADs, and recreational fishing havens separately.
2. QLD: import the public FAD coordinate table and the official Artificial reef sites dataset.
3. NT: confirm whether the AFANT land-based guide can be imported, then separate public shore spots from general guide context.
4. VIC: inspect image-only East Gippsland and shellfish reef pages for reliable coordinate sources before adding more.
5. WA: extract the DPIRD Recreational Fishing Location Guide into a structured list, then decide which entries are coastal/estuary and which are only region/block labels.
6. SA: keep only boat ramps and rule context for now. Continue searching for a coordinate-bearing official fishing spot or reef list before importer work.

## Normalized Output Target

Every imported item should normalize toward:

```json
{
  "id": "source_namespace:source_id",
  "type": "official_fishing_spot | artificial_reef | fad | recreational_fishing_haven | boat_ramp",
  "label": "Official name",
  "access": "public | unknown",
  "status": "confirmed",
  "source": "source_namespace",
  "coordinates": {
    "latitude": -0.0,
    "longitude": 0.0
  },
  "planner_eligible": false,
  "map_eligible": true,
  "role": "public_fishing_access | public_access_only | rule_context",
  "mode": "shore | estuary | boat | offshore | kayak | unknown",
  "attributes": {
    "official_url": "https://...",
    "depth_m": null,
    "species_note": null,
    "seasonal_status": null,
    "safety_note": null
  }
}
```

Important: `planner_eligible` must remain false by default for FADs, artificial reefs, and boat ramps until the product has a separate boat/offshore planning mode. For shore-based official platforms and official fishing spots, enable `planner_eligible` only when public access and fishing use are both explicit.
