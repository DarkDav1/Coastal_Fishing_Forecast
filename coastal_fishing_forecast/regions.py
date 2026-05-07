"""Generic region configuration for the coastal preview engine."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RegionConfig:
    slug: str
    display_name: str
    beach_bias: float = 1.0
    rocks_bias: float = 1.0
    jetty_bias: float = 1.0
    bay_estuary_bias: float = 1.0
    tide_movement_bias: float = 1.0
    shelter_bias: float = 1.0
    exposure_bias: float = 1.0


DEFAULT_REGION = RegionConfig(
    slug="generic_coastal",
    display_name="Generic Coastal",
)

REGION_CONFIGS = {
    DEFAULT_REGION.slug: DEFAULT_REGION,
    "open_coast": RegionConfig(
        slug="open_coast",
        display_name="Generic Open Coast",
        beach_bias=1.08,
        rocks_bias=1.06,
        jetty_bias=0.94,
        bay_estuary_bias=0.90,
        tide_movement_bias=1.05,
        shelter_bias=0.92,
        exposure_bias=1.08,
    ),
    "sheltered_estuary": RegionConfig(
        slug="sheltered_estuary",
        display_name="Generic Sheltered Estuary",
        beach_bias=0.90,
        rocks_bias=0.92,
        jetty_bias=1.06,
        bay_estuary_bias=1.10,
        tide_movement_bias=1.08,
        shelter_bias=1.10,
        exposure_bias=0.92,
    ),
    "surf_coast": RegionConfig(
        slug="surf_coast",
        display_name="Generic Surf Coast",
        beach_bias=1.12,
        rocks_bias=1.02,
        jetty_bias=0.96,
        bay_estuary_bias=0.86,
        tide_movement_bias=1.07,
        shelter_bias=0.90,
        exposure_bias=1.10,
    ),
    "harbour_access": RegionConfig(
        slug="harbour_access",
        display_name="Generic Harbour Access",
        beach_bias=0.94,
        rocks_bias=0.96,
        jetty_bias=1.12,
        bay_estuary_bias=1.04,
        tide_movement_bias=1.02,
        shelter_bias=1.08,
        exposure_bias=0.95,
    ),
    "bay_coast": RegionConfig(
        slug="bay_coast",
        display_name="Generic Bay Coast",
        beach_bias=0.96,
        rocks_bias=0.92,
        jetty_bias=1.04,
        bay_estuary_bias=1.12,
        tide_movement_bias=1.03,
        shelter_bias=1.12,
        exposure_bias=0.90,
    ),
}


def get_region_config(region: str | None) -> RegionConfig:
    if not region:
        return DEFAULT_REGION
    return REGION_CONFIGS.get(region, DEFAULT_REGION)
