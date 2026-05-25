export type StructureFacility = {
  id: string;
  type: string;
  label: string;
  access: string;
  source: string;
  status: string;
  attributes?: Record<string, unknown>;
  planner_eligible?: boolean;
  map_eligible?: boolean;
  role?: "public_fishing_access" | "public_access_only" | "hidden" | string;
  distance_km?: number;
  coordinates?: {
    latitude: number;
    longitude: number;
  };
  pin_forecast?: {
    score?: number | null;
    label?: string | null;
    dominant_water_type?: string | null;
    waterbody_class?: string | null;
    classification_confidence?: number | null;
    fish_profile?: string | null;
  };
};

export type PlaceCandidate = {
  id: string;
  display_name: string;
  short_name?: string;
  latitude: number;
  longitude: number;
  country?: string;
  region?: string;
  source?: string;
  types?: string[];
};

export type PlaceSearchResponse = {
  query: string;
  provider: string;
  results: PlaceCandidate[];
};

export type PlanAction = {
  text: string;
  time_window?: string | null;
  representative_time?: string | null;
  water_type?: string | null;
  behavior_group?: string | null;
  score?: number | null;
  confirmed_structure?: string[];
};

export type ForecastResponse = {
  status: "ok" | "unsupported_or_no_result";
  query: string;
  selected_place: null | {
    display_name: string;
    latitude: number;
    longitude: number;
    forecast_support?: {
      supported: boolean;
      message: string;
    nearest_supported_water_km?: number;
    };
  };
  candidates?: PlaceCandidate[];
  forecast: null | {
    hero: {
      score: number | null;
      label: string;
      fish_outlook_score?: number | null;
      comfort_score?: number | null;
      trip_quality_score?: number | null;
      safety_flag?: string | null;
      waterbody_class?: string | null;
      classification_confidence?: number | null;
      fish_profile?: string | null;
      headline: string;
      best_window: null | WindowCard;
    };
    classification?: null | {
      waterbody_class?: string | null;
      classification_confidence?: number | null;
      classification_reasons?: string[];
      manual_region_override?: string | null;
      effective_region?: string | null;
      fish_profile?: string | null;
    };
    confidence: {
      score: number;
      label: string;
      factors: string[];
    };
    tide_verification: {
      status: string;
      source: string;
      message: string;
      station_distance_km?: number;
    };
    daily_forecast: Array<{
      date: string;
      day_score?: number | null;
      fish_day_score?: number | null;
      best_window_score?: number | null;
      average_window_score?: number | null;
      hourly_peak_score?: number | null;
      hourly_mean_score?: number | null;
      daily_score_note?: string | null;
      best_window: WindowCard | null;
      windows: WindowCard[];
    }>;
    hourly_activity?: HourlyActivityPoint[];
    structure_facilities: StructureFacility[];
    structure_data?: {
      source?: string;
      sources?: Array<{ source: string; status: string; count?: number }>;
    };
  };
  plan: {
    source: string;
    recommendation: {
      label: "go" | "maybe" | "skip";
      score: number | null;
      summary: string;
    };
    primary_action: PlanAction;
    backup_action?: PlanAction | null;
    avoid: string[];
    risks: string[];
    confidence_note: string;
    data_source_note: string;
  };
};

export type HourlyActivityPoint = {
  date: string;
  hour: number;
  time: string;
  score: number | null;
  activity_score?: number | null;
  presence_score?: number | null;
  trip_quality_score?: number | null;
  fish_outlook_score?: number | null;
  comfort_score?: number | null;
  safety_flag?: string | null;
  big_fish_near_shore?: string | null;
  label?: string | null;
  dominant_inferred_type?: string | null;
  time_window?: string | null;
  tide_phase?: string | null;
  tide_source?: string | null;
  tide_stage?: string | null;
  tide_range_m?: number | null;
  tide_height_m?: number | null;
  tide_movement_rate_m_per_hour?: number | null;
  tide_current_confidence?: string | null;
  current_strength_proxy?: number | null;
  current_source_note?: string | null;
  wind_speed_knots?: number | null;
  wind_direction_deg?: number | null;
  wind_gust_knots?: number | null;
  wave_height_m?: number | null;
  swell_height_m?: number | null;
  rain_mm?: number | null;
  precipitation_mm?: number | null;
  temperature_c?: number | null;
  pressure_hpa?: number | null;
  sea_surface_temperature_c?: number | null;
  sea_surface_temperature_delta_24h?: number | null;
  water_temperature_signal?: string | null;
  water_temperature_trend?: string | null;
  temperature_confidence?: string | null;
  waterbody_class?: string | null;
  fish_profile?: string | null;
};

export type WindowCard = {
  date: string;
  time_window: string;
  representative_time: string;
  status: string;
  score: number;
  activity_score?: number | null;
  presence_score?: number | null;
  trip_quality_score?: number | null;
  fish_outlook_score?: number | null;
  comfort_score?: number | null;
  comfort_factors?: string[];
  safety_flag?: string | null;
  safety_factors?: string[];
  big_fish_near_shore?: string | null;
  label: string;
  reason_tags?: string[];
  positive_reason_tags?: string[];
  negative_reason_tags?: string[];
  dominant_water_type: string;
  waterbody_class?: string | null;
  classification_confidence?: number | null;
  classification_reasons?: string[];
  manual_region_override?: string | null;
  fish_profile?: string | null;
  water_type_scores: Array<{ key: string; label: string; score: number }>;
  expanded_water_types: Array<{ key: string; label: string; score: number; parent: string }>;
  behavior_groups: Array<{ key: string; label: string; score: number; reason: string }>;
  conditions: {
    wind: {
      speed_knots: number;
      direction_deg: number;
      gust_knots?: number | null;
      recent_max_12h?: number | null;
      onshore_knots?: number | null;
      offshore_knots?: number | null;
      alongshore_knots?: number | null;
    };
    swell: {
      height_m: number | null;
      direction_deg: number | null;
      wave_height_m?: number | null;
      wave_height_delta_24h?: number | null;
      source?: string | null;
    };
    pressure_hpa: number;
    pressure_delta_3h?: number | null;
    air?: {
      temperature_c?: number | null;
      rain_mm?: number | null;
      precipitation_mm?: number | null;
      recent_precipitation_sum_12h?: number | null;
      cloud_cover_pct?: number | null;
    };
    weather_trend?: {
      shock_score?: number | null;
      change_notes?: string[];
      risk_level?: string | null;
    };
    marine?: {
      sea_surface_temperature_c?: number | null;
      sea_surface_temperature_delta_24h?: number | null;
      sea_surface_temperature_delta_72h?: number | null;
      water_temperature_signal?: string | null;
      water_temperature_trend?: string | null;
      temperature_confidence?: string | null;
    };
    tide: {
      phase: string;
      source: string;
      stage?: string | null;
      range_m?: number | null;
      height_m?: number | null;
      movement_rate_m_per_hour?: number | null;
      current_confidence?: string | null;
      current_strength_proxy?: number | null;
      current_source_note?: string | null;
      hours_to_high_tide?: number | null;
      hours_to_low_tide?: number | null;
      hours_since_low_tide?: number | null;
    };
    solar?: {
      hour_of_day?: number | null;
      hours_from_sunrise?: number | null;
      hours_from_sunset?: number | null;
      hours_from_solar_noon?: number | null;
      is_daylight?: boolean | null;
    };
    moon?: {
      phase_name?: string | null;
      illumination_pct?: number | null;
    };
    formula?: {
      normalized?: Record<string, number | null | undefined>;
      rules?: Array<{ id: string; label: string; score_delta: number }>;
      score_delta?: number | null;
      family?: string | null;
    };
    classification?: {
      waterbody_class?: string | null;
      classification_confidence?: number | null;
      classification_reasons?: string[];
      manual_region_override?: string | null;
      effective_region?: string | null;
    };
    fish_profile?: string | null;
  };
};
