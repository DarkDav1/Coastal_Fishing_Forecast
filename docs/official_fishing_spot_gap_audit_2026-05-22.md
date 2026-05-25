# Official Fishing Spot Gap Audit

Checked on 2026-05-22 after the NSW/VIC/QLD/NT/WA/TAS spot-level generation.

## What Was Added In The Gap Pass

| Jurisdiction | Added | Count | Status |
| --- | --- | ---: | --- |
| NSW | Official FAD coordinates | 22 | Added as boat/offshore map references |
| NSW | Estuarine artificial reef coordinates | 9 | Added as estuary/boat reef references |
| NSW | Offshore artificial reef coordinates | 10 | Added as boat/offshore map references |
| NSW | Sydney Harbour guide spot `scope` field | 70 updated rows | Fixed empty scope in the combined feed |
| WA | Official artificial reef coordinates | 10 | Added as boat/offshore map references |
| TAS | Fishing Tasmania Hot Fishing Spots named places | 131 | Added as official shore/coastal/estuary guide spot candidates |
| QLD | Moreton Bay artificial reef map coordinates | 78 | Added as boat/offshore map references |
| VIC | Port Phillip Bay Go Fishing named spots | 8 | Added to the VFA Go Fishing spot list |
| VIC | VFA recreational reef coordinates | 36 | Added as reef references; Merv's Reef is marked shore-reachable |
| WA | DPIRD public FAD map layer | 49 | Added with current deployment status retained |
| NT | Official/government land-based fishing references | 4 | Added as shore/land-based candidates with crocodile and access review required |
| SA | Windara Reef coordinate reference | 1 | Added as a map/context reef reference, not a direct shore-access recommendation |
| NT | Relaxed-scope public fishing references | 17 | Added from NT.gov parks/fishing sites, AFANT government-supported context, and public tourism/fishing references |
| SA | Relaxed-scope public fishing references | 38 | Added from Marine Parks, local tourism, state tourism, and public fishing guide pages |
| NSW | Relaxed-scope public fishing references | 12 | Added from Visit NSW coastal fishing articles and regional pages |
| QLD | Relaxed-scope public fishing references | 18 | Added from Queensland/TEQ tourism and drive-guide references |
| VIC | Relaxed-scope public fishing references | 12 | Added from Visit Victoria fishing and coastal attraction pages |
| WA | Relaxed-scope public fishing references | 15 | Added from Tourism Western Australia attraction and destination pages |

The combined official spot feed now contains 636 rows with no missing coordinates.

## Still Missing Or Deferred

| Jurisdiction | Gap | Reason | Next action |
| --- | --- | --- | --- |
| TAS | Fishing Tasmania PDF map symbols still need second-pass review | The 131 named places from the official pages are added, but map-only symbols and exact access points may add more detail | Review the downloadable regional maps for extra symbols not named in page text |
| NSW | Other Go Fishing guides beyond Sydney Harbour are not yet spot-level | We only extracted Sydney Harbour in this pass | Continue with Botany Bay, Jervis Bay, Lake Macquarie, St Georges Basin, Hawkesbury, Coffs Coast, Port Macquarie, Batemans Bay |
| NSW | Some offshore reef planning PDFs may contain more sub-patch detail | Main public offshore reef page coordinates are now added for Sydney, Southern Sydney, Wollongong, Terrigal, Port Macquarie, and Merimbula | Only add extra PDF sub-patches when they are current and not duplicating public page coordinates |
| QLD | Artificial reef open-data package is not fully resolved | Moreton Bay reef map coordinates are now added, but the broader QSpatial download still needs direct machine-readable extraction | Resolve QSpatial download for any non-Moreton-Bay reef metadata |
| VIC | Some VFA reef pages are still image-only or descriptive | Corio Bay, boat-based reefs, Kingfish Reef, Kayaker's Reef, and Torquay coordinates are done; East Gippsland and some shore/shellfish reef pages need map-image or report extraction | Extract East Gippsland reef map image coordinates only if a reliable coordinate source is found |
| WA | DPIRD Recreational Fishing Location Guide is not spot-level | The public library page exists, but the direct PDF download returned 403 in this environment | Use browser/manual download or another official mirror, then parse PDF |
| WA | FAD map/list is extracted, but statuses vary | The public map layer includes devices that are in position, currently not deployed, broken free, or unknown | Filter by `deployment_status` before showing active FAD recommendations |
| SA | No PIRSA Tasmania-style fishing spot guide found | Relaxed-scope SA spots are added from Marine Parks, tourism and local guide sources, but PIRSA still does not expose a public fishing-spot coordinate list | Keep these rows as supplemental until access, closures, and current rules are checked |
| NT | Full AFANT guidebook not extracted | The public AFANT page confirms the government-supported guide exists, but the full book is not a public machine-readable coordinate list | Keep current AFANT-derived rows as supplemental context; import the full guide only if permission/source text becomes available |
| ACT | Inland freshwater only | Out of coastal v1 scope | Defer to future freshwater product |

## Inclusion Rules Confirmed

- Shore/land-based official guide spots can be shown as `public_fishing_access_candidate`.
- Relaxed-scope rows are `supplemental_public_fishing_access_candidate`, not strict official coordinate rows.
- FADs and artificial reefs are map references only unless the app has a boat/offshore planning mode.
- All added points keep `score_impact="none"`.
- Boat ramps remain map-only and are not part of this fishing spot feed.
