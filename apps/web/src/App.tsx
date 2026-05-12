import { FormEvent, PointerEvent, useEffect, useRef, useState } from "react";
import { forecastPlace, searchForecast, searchPlaces } from "./api";
import type { ForecastResponse, HourlyActivityPoint, PlaceCandidate, StructureFacility, WindowCard } from "./types";

const DEMO_QUERY = "Sandy Bay Tasmania";
const MAP_ZOOM = 14;
const MAP_MIN_ZOOM = 12;
const MAP_MAX_ZOOM = 19;
const MAP_TILE_SIZE = 256;
const MAP_DEFAULT_WIDTH = 980;
const MAP_DEFAULT_HEIGHT = 760;
const MAX_VISIBLE_STRUCTURE_KM = 5;

type Lang = "en" | "zh";
type Theme = "day" | "night";

const UI_TEXT = {
  en: {
    languageToggle: "中文",
    themeToggleDay: "Day",
    themeToggleNight: "Night",
    switchToEnglish: "Switch to English",
    switchToChinese: "Switch to Chinese",
    switchToDay: "Switch to day mode",
    switchToNight: "Switch to night mode",
    brand: "Coastal Fishing Forecast",
    eyebrow: "Generic coastal forecast engine",
    heroTitle: "Plan the next cast from live coastal signals.",
    heroCopy: "Search a coastal place, check today’s fish activity, and plan the first move.",
    searchPlaceholder: "Search a coastal place",
    forecastButton: "Forecast",
    checkingButton: "Checking...",
    selectedPlace: "Selected place",
    waitingPlace: "Waiting for forecast",
    todayScore: "Today’s call",
    searchResultWaiting: "Search result will appear here.",
    strongestNearby: "is the strongest nearby option today.",
    primaryMap: "Primary map",
    selectedMap: "Selected map",
    publicAccessTitle: "Public fishing access near this search",
    unsupportedMapTitle: "Selected location is outside the forecast area",
    officialAccess: "official or mapped fishing access",
    supportedSignals: "supported coastal signals at this coordinate",
    mapControls: "Map controls",
    dragMap: "Drag map · tap a point",
    fishingAccess: "Fishing access",
    mapLeads: "Map leads",
    mapIntro: "Official fishing map entries and confirmed public fishing access within 5 km.",
    noAccess: "No public fishing access found nearby",
    noAccessMeta: "nothing confirmed within 5 km",
    noAccessNote: "Use the forecast by water style first, then verify access locally.",
    unsupported: "Unsupported",
    unsupportedAdvice: "Move the search to coastal or tidal water.",
    fishActivity24h: "24-hour fish activity",
    historyForecast: "30-day history + forecast",
    dragDates: "Drag sideways to review each day’s peak window score",
    dateStripPeakLabel: "peak",
    today: "Today",
    score: "score",
    scoreLayers: "Forecast score layers",
    activity: "Activity",
    presence: "Presence",
    trip: "Trip",
    biteTiming: "bite timing",
    fishNearby: "fish nearby",
    whyWindow: "Day overview",
    bestTime: "Best time",
    tide: "Tide",
    comfort: "Comfort",
    pressure: "Pressure",
    firstMove: "Today’s move",
    scoreFactors: "Score factors",
    scoreFactorsGenerating: "Generating explanation…",
    scoreFactorsPositive: "What's helping",
    scoreFactorsNegative: "What's challenging",
    backup: "Backup",
    weatherVisual: "Weather visual",
    windTideWaves: "Wind, Tide & Waves",
    windMap: "Wind map",
    windyNote: "Live wind layer from Windy. Curves below use the same hourly data as the score.",
    tideHeight: "Tide height",
    tideMovement: "Tide movement",
    tideMovementProxyNote: "This curve shows model-estimated tide movement, not local tide-table height.",
    waveHeight: "Wave height",
    waveUnavailableNote:
      "Open-Meteo returned no usable hourly ``wave_height`` / ``swell_wave_height`` for this day in the API response (or the running forecast server is an older build that does not fill those fields). Tide and wind above still reflect the forecast.",
    publicPlanNote: "Public fishing access for planning the first move.",
    exactPlace: "Choose the exact place",
    noPlaceFound: "No matching place found.",
    reset: "Reset",
    searchPoint: "Search point",
    closeMarker: "Close marker details",
    mapLegend: "Map legend",
    noMapCenter: "No map center available.",
    selectedCoordinate: "Selected coordinate",
    dateSelector: "Forecast date selector",
    fishCurveLabel: "Daily fish activity curve",
    windyTitle: "Windy wind map"
  },
  zh: {
    languageToggle: "EN",
    themeToggleDay: "日间",
    themeToggleNight: "夜间",
    switchToEnglish: "切换到英文",
    switchToChinese: "切换到中文",
    switchToDay: "切换到日间模式",
    switchToNight: "切换到夜间模式",
    brand: "Coastal Fishing Forecast",
    eyebrow: "通用海岸鱼情预测引擎",
    heroTitle: "用海岸信号判断是否出钓。",
    heroCopy: "搜索海岸钓点，查看今日鱼情，并决定是否值得出发。",
    searchPlaceholder: "搜索海岸地点",
    forecastButton: "预测",
    checkingButton: "检查中...",
    selectedPlace: "已选地点",
    waitingPlace: "等待预测",
    todayScore: "今日建议",
    searchResultWaiting: "搜索结果会显示在这里。",
    strongestNearby: "是今天附近最强的水域类型。",
    primaryMap: "主要地图",
    selectedMap: "已选地图",
    publicAccessTitle: "本次搜索附近的公共钓点入口",
    unsupportedMapTitle: "所选位置不在当前预测范围内",
    officialAccess: "官方或地图标注钓点入口",
    supportedSignals: "个受支持的海岸信号",
    mapControls: "地图控制",
    dragMap: "拖动地图 · 点击点位",
    fishingAccess: "钓点入口",
    mapLeads: "地图线索",
    mapIntro: "仅显示 5 公里内的官方钓点和确认公共入口。",
    noAccess: "附近没有确认公共钓点入口",
    noAccessMeta: "5 公里内暂无确认点位",
    noAccessNote: "先按水域类型看鱼情，再现场确认入口。",
    unsupported: "暂不支持",
    unsupportedAdvice: "请把搜索点移到海岸或潮汐水域。",
    fishActivity24h: "24 小时鱼情活跃度",
    historyForecast: "30 天历史 + 预测",
    dragDates: "横向拖动查看每日最佳窗口评分",
    dateStripPeakLabel: "最高",
    today: "今天",
    score: "评分",
    scoreLayers: "评分拆分",
    activity: "活跃度",
    presence: "近岸存在感",
    trip: "出钓条件",
    biteTiming: "开口时间",
    fishNearby: "鱼是否靠近",
    whyWindow: "全天情况",
    bestTime: "最佳时间",
    tide: "潮汐",
    comfort: "舒适度",
    pressure: "气压",
    firstMove: "今日建议",
    scoreFactors: "分数原因",
    scoreFactorsGenerating: "正在生成说明…",
    scoreFactorsPositive: "有利因素",
    scoreFactorsNegative: "不利因素",
    backup: "备选方案",
    weatherVisual: "天气可视化",
    windTideWaves: "风、潮汐与浪况",
    windMap: "风场地图",
    windyNote: "风场来自 Windy；下方曲线使用与评分相同的逐小时数据。",
    tideHeight: "潮高",
    tideMovement: "潮汐变化",
    tideMovementProxyNote: "这条曲线显示的是模型估计的潮汐运动，不是本地潮汐表潮高。",
    waveHeight: "浪高",
    waveUnavailableNote:
      "Open-Meteo 当日逐小时未返回可用的 ``wave_height`` / ``swell_wave_height``（或当前运行的预报服务仍是旧版本、未写入这些字段）。上方潮汐与风场仍来自预报。",
    publicPlanNote: "可作为规划第一步的公共钓点入口。",
    exactPlace: "选择准确地点",
    noPlaceFound: "没有找到匹配地点。",
    reset: "重置",
    searchPoint: "搜索点",
    closeMarker: "关闭点位详情",
    mapLegend: "地图图例",
    noMapCenter: "没有可用地图中心。",
    selectedCoordinate: "已选坐标",
    dateSelector: "预测日期选择器",
    fishCurveLabel: "全天鱼情曲线",
    windyTitle: "Windy 风场地图"
  }
} as const;

function copy(lang: Lang) {
  return UI_TEXT[lang];
}

function scoreTone(label: string) {
  if (label === "go") return "go";
  if (label === "skip") return "skip";
  return "maybe";
}

function recommendationLabel(score?: number | null) {
  if (score == null) return "maybe";
  if (score >= 65) return "go";
  if (score < 40) return "skip";
  return "maybe";
}

function recommendationDisplay(label: string, lang: Lang = "en") {
  if (lang === "zh") {
    if (label === "go") return "值得去";
    if (label === "skip") return "建议等";
    return "可短试";
  }
  if (label === "go") return "Go";
  if (label === "skip") return "Wait";
  return "Maybe";
}

function candidateMeta(candidate: PlaceCandidate) {
  const region = [candidate.region, candidate.country].filter(Boolean).join(", ");
  const types = candidate.types?.slice(0, 2).join(" / ");
  const coords = `${candidate.latitude.toFixed(4)}, ${candidate.longitude.toFixed(4)}`;
  return [region, types, coords].filter(Boolean).join(" · ");
}

const SOURCE_LABELS: Record<string, string> = {
  list_wildfisheries: "Tasmania Fishing Map",
  list_mast: "Tasmania MAST",
  openmeteo_model: "Open-Meteo model",
  osm_overpass: "OpenStreetMap",
  tidesatlas: "TidesAtlas"
};

const STRUCTURE_TYPE_LABELS: Record<string, string> = {
  beach_access: "Beach access",
  boat_ramp: "Boat ramp",
  fishing_platform: "Fishing platform",
  official_fishing_spot: "Official fishing spot",
  pier: "Pier",
  public_jetty: "Public jetty",
  public_pier: "Public pier",
  public_wharf: "Public wharf",
  rocky_shoreline: "Rocky shoreline"
};

const WATER_TYPE_LABELS_ZH: Record<string, string> = {
  bay_estuary_edge: "湾区 / 河口边缘",
  beach: "沙滩",
  rocks: "礁石",
  jetty: "码头",
  morning: "早晨",
  dusk: "黄昏",
  pre_dawn: "黎明前",
  day: "白天",
  night: "夜间",
  rising: "涨潮",
  falling: "落潮",
  flood: "涨潮",
  ebb: "落潮",
  slack: "平潮",
  high: "高潮",
  low: "低潮"
};

const STRUCTURE_TYPE_LABELS_ZH: Record<string, string> = {
  beach_access: "沙滩入口",
  boat_ramp: "船坡 / 下水点",
  fishing_platform: "钓鱼平台",
  official_fishing_spot: "官方钓点",
  pier: "栈桥",
  public_jetty: "公共码头",
  public_pier: "公共栈桥",
  public_wharf: "公共码头",
  rocky_shoreline: "礁石岸线"
};

function formatSource(source?: string | null, lang: Lang = "en") {
  if (!source) return lang === "zh" ? "预测数据" : "Forecast data";
  if (lang === "zh" && source === "osm_overpass") return "OpenStreetMap";
  return SOURCE_LABELS[source] ?? displayWaterType(source, lang);
}

function formatStructureType(type?: string | null, lang: Lang = "en") {
  if (!type) return lang === "zh" ? "地图结构" : "Mapped structure";
  if (lang === "zh") return STRUCTURE_TYPE_LABELS_ZH[type] ?? displayWaterType(type, lang);
  return STRUCTURE_TYPE_LABELS[type] ?? displayWaterType(type);
}

function formatAccess(access?: string | null, lang: Lang = "en") {
  if (lang === "zh") {
    if (access === "public") return "公共入口";
    if (access === "private") return "私人入口";
    if (access === "unknown") return "入口未知";
    return displayWaterType(access, lang);
  }
  if (access === "public") return "Public access";
  if (access === "private") return "Private access";
  if (access === "unknown") return "Access unknown";
  return displayWaterType(access);
}

function markerKind(structure: StructureFacility) {
  if (structure.planner_eligible) return "public";
  return "hidden";
}

function markerLabel(structure: StructureFacility) {
  const kind = markerKind(structure);
  if (kind === "public") return "🎣";
  return "";
}

function shouldShowStructure(structure: StructureFacility) {
  return mapEligible(structure) && isWithinVisibleStructureRadius(structure);
}

function mapEligible(structure: StructureFacility) {
  if (structure.access !== "public") return false;
  return Boolean(structure.planner_eligible);
}

function isWithinVisibleStructureRadius(structure: StructureFacility) {
  return typeof structure.distance_km === "number" && structure.distance_km <= MAX_VISIBLE_STRUCTURE_KM;
}

function longitudeToWorldX(longitude: number, zoom: number) {
  return ((longitude + 180) / 360) * MAP_TILE_SIZE * 2 ** zoom;
}

function latitudeToWorldY(latitude: number, zoom: number) {
  const safeLatitude = Math.max(Math.min(latitude, 85.05112878), -85.05112878);
  const radians = (safeLatitude * Math.PI) / 180;
  return (
    ((1 - Math.log(Math.tan(radians) + 1 / Math.cos(radians)) / Math.PI) / 2) *
    MAP_TILE_SIZE *
    2 ** zoom
  );
}

function worldToCoordinates(x: number, y: number, zoom: number) {
  const scale = MAP_TILE_SIZE * 2 ** zoom;
  const longitude = (x / scale) * 360 - 180;
  const n = Math.PI - (2 * Math.PI * y) / scale;
  const latitude = (180 / Math.PI) * Math.atan(Math.sinh(n));
  return { latitude, longitude };
}

function mapViewport(
  center: { latitude: number; longitude: number },
  zoom = MAP_ZOOM,
  dimensions = { width: MAP_DEFAULT_WIDTH, height: MAP_DEFAULT_HEIGHT }
) {
  const centerX = longitudeToWorldX(center.longitude, zoom);
  const centerY = latitudeToWorldY(center.latitude, zoom);
  return {
    zoom,
    left: centerX - dimensions.width / 2,
    top: centerY - dimensions.height / 2,
    width: dimensions.width,
    height: dimensions.height
  };
}

function pointOnMap(
  coordinates: { latitude: number; longitude: number },
  viewport: ReturnType<typeof mapViewport>
) {
  const x = longitudeToWorldX(coordinates.longitude, viewport.zoom) - viewport.left;
  const y = latitudeToWorldY(coordinates.latitude, viewport.zoom) - viewport.top;
  return {
    left: (x / viewport.width) * 100,
    top: (y / viewport.height) * 100,
    visible: x >= -30 && x <= viewport.width + 30 && y >= -30 && y <= viewport.height + 30
  };
}

function mapTiles(viewport: ReturnType<typeof mapViewport>) {
  const maxTile = 2 ** viewport.zoom;
  const minX = Math.floor(viewport.left / MAP_TILE_SIZE);
  const maxX = Math.floor((viewport.left + viewport.width) / MAP_TILE_SIZE);
  const minY = Math.floor(viewport.top / MAP_TILE_SIZE);
  const maxY = Math.floor((viewport.top + viewport.height) / MAP_TILE_SIZE);
  const tiles = [];
  for (let x = minX; x <= maxX; x += 1) {
    for (let y = minY; y <= maxY; y += 1) {
      if (y < 0 || y >= maxTile) continue;
      const wrappedX = ((x % maxTile) + maxTile) % maxTile;
      tiles.push({
        key: `${viewport.zoom}-${x}-${y}`,
        src: `https://tile.openstreetmap.org/${viewport.zoom}/${wrappedX}/${y}.png`,
        left: ((x * MAP_TILE_SIZE - viewport.left) / viewport.width) * 100,
        top: ((y * MAP_TILE_SIZE - viewport.top) / viewport.height) * 100,
        width: (MAP_TILE_SIZE / viewport.width) * 100,
        height: (MAP_TILE_SIZE / viewport.height) * 100
      });
    }
  }
  return tiles;
}

function waterTypeAdvantage(key: string, label: string, lang: Lang = "en") {
  if (lang === "zh") {
    if (key.includes("bay") || key.includes("estuary")) {
      return "优势：有遮蔽的边缘在外侧水域一般时更容易保持稳定。";
    }
    if (key.includes("jetty") || label.toLowerCase().includes("jetty")) {
      return "优势：结构物容易集中水流、阴影和饵鱼移动。";
    }
    if (key.includes("beach")) return "优势：沙滩沟槽和边线在潮汐、浪况配合时更有机会。";
    if (key.includes("rock")) return "优势：硬边和浪花能提供掩护与伏击路线。";
    return "优势：这是当前窗口附近较强的水域信号之一。";
  }
  if (key.includes("bay") || key.includes("estuary")) {
    return "Advantage: sheltered edges usually hold more stable water when open areas are marginal.";
  }
  if (key.includes("jetty") || label.toLowerCase().includes("jetty")) {
    return "Advantage: structure can concentrate current lines, shade, and bait movement.";
  }
  if (key.includes("beach")) {
    return "Advantage: beach gutters and edges can suit roaming fish when tide and swell line up.";
  }
  if (key.includes("rock")) {
    return "Advantage: hard edges can create wash, cover, and ambush lanes.";
  }
  return "Advantage: this is one of the stronger nearby habitat signals for the selected window.";
}

function waterTypeShortAdvantage(key: string, label: string, lang: Lang = "en") {
  if (lang === "zh") {
    if (key.includes("bay") || key.includes("estuary")) return "有遮蔽水域";
    if (key.includes("jetty") || label.toLowerCase().includes("jetty")) return "水流和阴影";
    if (key.includes("beach")) return "沟槽和边线";
    if (key.includes("rock")) return "浪花和掩护";
    return "附近较强类型";
  }
  if (key.includes("bay") || key.includes("estuary")) return "Sheltered water";
  if (key.includes("jetty") || label.toLowerCase().includes("jetty")) return "Current and shade";
  if (key.includes("beach")) return "Gutters and edges";
  if (key.includes("rock")) return "Wash and cover";
  return "Stronger nearby style";
}

function displayWaterType(value?: string | null, lang: Lang = "en") {
  if (!value) return "Nearby water";
  const normalized = value.toLowerCase();
  if (lang === "zh") return WATER_TYPE_LABELS_ZH[normalized] ?? value.replaceAll("_", " ");
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function scoreMeaning(score?: number | null, lang: Lang = "en") {
  if (lang === "zh") {
    if (score == null) return "等待预测评分。";
    if (score >= 70) return "适合认真规划一次出钓";
    if (score >= 55) return "可以去，但计划要简单";
    if (score >= 40) return "只适合顺路短试";
    return "建议等更强的日子";
  }
  if (score == null) return "Waiting for a forecast score.";
  if (score >= 70) return "Good day to plan a proper session";
  if (score >= 55) return "Worth going with a simple plan";
  if (score >= 40) return "Only worth a short try nearby";
  return "Better to wait for a stronger day";
}

function selectedWindowScore(window: WindowCard | null) {
  return window?.score ?? window?.trip_quality_score ?? null;
}

function selectedWindowSummary(window: WindowCard | null, lang: Lang = "en") {
  const score = selectedWindowScore(window);
  if (lang === "zh") {
    if (!window || score == null) return "选择日期查看当天窗口。";
    if (score >= 70) return "这一天有较强的附近窗口。";
    if (score >= 55) return "这一天可以钓，但需要清晰计划。";
    if (score >= 40) return "这一天偏勉强，适合短试。";
    return "这一天不适合专门出钓。";
  }
  if (!window || score == null) return "Select a date to review that day's fishing window.";
  if (score >= 70) return "This date has one of the stronger nearby windows.";
  if (score >= 55) return "This date is fishable, but still needs a clear plan.";
  if (score >= 40) return "This date looks marginal; keep it short and opportunistic.";
  return "This date is weak for a dedicated trip.";
}

function formatActionTime(value?: string | null, fallback?: string) {
  if (!value) return fallback ?? "";
  const isoMatch = value.match(/T(\d{2}):(\d{2})/);
  if (isoMatch) return `${isoMatch[1]}:${isoMatch[2]}`;
  const timeMatch = value.match(/^(\d{1,2}):(\d{2})/);
  if (timeMatch) return `${timeMatch[1].padStart(2, "0")}:${timeMatch[2]}`;
  return fallback ?? value;
}

function selectedPrimaryAction(window: WindowCard | null, structures: StructureFacility[], lang: Lang = "en") {
  if (!window) return "";
  const score = selectedWindowScore(window);
  const tripQuality = window.trip_quality_score ?? null;
  if ((score != null && score < 40) || (tripQuality != null && tripQuality <= 10)) {
    if (lang === "zh") return "今天跳过这个点。条件太弱，不适合专门出钓；等更稳定的窗口，或换附近更合适的位置。";
    return "Skip this spot today. Conditions are too weak for a dedicated trip; wait for a calmer window or check another nearby place.";
  }
  const time = formatActionTime(window.representative_time, `${String(curveHour(window.time_window)).padStart(2, "0")}:00`);
  const waterType = displayWaterType(window.dominant_water_type, lang);
  const hasPublicStructure = structures.some((structure) => structure.planner_eligible && isWithinVisibleStructureRadius(structure));
  if (lang === "zh") {
    const start = hasPublicStructure
      ? `从公共入口开始，时间约 ${time}`
      : `从最强的${waterType}水域开始，时间约 ${time}`;
    return `${start}。给它 60-90 分钟；如果水面一直很安静，就换点。`;
  }
  const start = hasPublicStructure
    ? `Start from public access around ${time}`
    : `Start around the strongest ${waterType.toLowerCase()} water around ${time}`;
  return `${start}. Give it 60-90 minutes, then switch if the water looks quiet.`;
}

function selectedBackupAction(window: WindowCard | null, fallback?: string, lang: Lang = "en") {
  const score = selectedWindowScore(window);
  const tripQuality = window?.trip_quality_score ?? null;
  if ((score != null && score < 40) || (tripQuality != null && tripQuality <= 10)) {
    if (lang === "zh") return "更好的备选：选择更有遮蔽的位置，或把这次出钓留到下一个稳定日。";
    return "Better backup: choose a more sheltered location, or save the trip for the next stable day.";
  }
  if (lang === "zh" && fallback) return "备选：如果第一个位置人多、关闭或没有动静，换到地图标注的礁石岸线。";
  return fallback ?? "";
}

function average(values: Array<number | null | undefined>) {
  const valid = values.filter((value): value is number => typeof value === "number");
  if (!valid.length) return null;
  return Math.round(valid.reduce((sum, value) => sum + value, 0) / valid.length);
}

function averageFloat(values: Array<number | null | undefined>) {
  const valid = values.filter((value): value is number => typeof value === "number");
  if (!valid.length) return null;
  return valid.reduce((sum, value) => sum + value, 0) / valid.length;
}

function todayForecastDay(forecast: ForecastResponse["forecast"] | undefined) {
  const today = todayIsoDate();
  return forecast?.daily_forecast.find((day) => day.date === today) ?? forecast?.daily_forecast[0] ?? null;
}

function dailyScoreSummary(day?: { best_window: WindowCard | null; windows: WindowCard[] } | null) {
  const windows = day?.windows ?? [];
  const activity = average(windows.map((window) => window.activity_score ?? window.score));
  const presence = average(windows.map((window) => window.presence_score ?? window.score));
  const tripQuality = average(windows.map((window) => window.trip_quality_score ?? window.score));
  const fishIndex = average([activity, presence]);
  const weighted =
    activity == null || presence == null || tripQuality == null
      ? selectedWindowScore(day?.best_window ?? null)
      : Math.round(activity * 0.4 + presence * 0.35 + tripQuality * 0.25);
  return { activity, presence, tripQuality, fishIndex, weighted };
}

function dayScore(day?: { best_window: WindowCard | null; windows: WindowCard[] } | null) {
  return dailyScoreSummary(day).weighted;
}

/** Highest window `score` for the date strip (better perceived “best moment that day”). */
function dayMaxWindowScore(day?: { best_window: WindowCard | null; windows: WindowCard[] } | null): number | null {
  const windows = day?.windows ?? [];
  const scores = windows
    .map((w) => w.score)
    .filter((s): s is number => typeof s === "number" && Number.isFinite(s));
  if (scores.length) return Math.round(Math.max(...scores));
  const fallback = selectedWindowScore(day?.best_window ?? null);
  return fallback != null ? Math.round(fallback) : null;
}

function daySummaryText(day?: { best_window: WindowCard | null; windows: WindowCard[] } | null, lang: Lang = "en") {
  const summary = dailyScoreSummary(day);
  const score = summary.weighted;
  if (lang === "zh") {
    if (score == null) return "选择日期查看全天情况。";
    if (score >= 70) return "这一天整体条件较强，适合认真规划。";
    if (score >= 55) return "这一天整体可钓，但计划要清晰。";
    if (score >= 40) return "这一天整体偏一般，只适合短试或顺路查看。";
    return "这一天整体偏弱，不适合专门出钓。";
  }
  if (score == null) return "Select a date to review the whole-day outlook.";
  if (score >= 70) return "This date has strong overall conditions for a proper session.";
  if (score >= 55) return "This date is fishable overall, but still needs a clear plan.";
  if (score >= 40) return "This date is mixed overall; keep it short or opportunistic.";
  return "This date is weak overall for a dedicated trip.";
}

function firstWeatherChangeNotes(day?: { windows: WindowCard[] } | null, limit = 2): string[] {
  const windows = day?.windows ?? [];
  const out: string[] = [];
  const seen = new Set<string>();
  for (const window of windows) {
    const notes = window.conditions?.weather_trend?.change_notes;
    if (!Array.isArray(notes)) continue;
    for (const note of notes) {
      if (typeof note === "string" && note.trim() && !seen.has(note)) {
        seen.add(note);
        out.push(note.trim());
        if (out.length >= limit) return out;
      }
    }
  }
  return out;
}

function dayConditionStats(day?: { windows: WindowCard[] } | null) {
  const windows = day?.windows ?? [];
  const windAvg = averageFloat(windows.map((window) => window.conditions.wind.speed_knots));
  const gustMax = Math.max(0, ...windows.map((window) => window.conditions.wind.gust_knots ?? window.conditions.wind.recent_max_12h ?? 0));
  const waveAvg = averageFloat(windows.map((window) => window.conditions.swell.wave_height_m ?? window.conditions.swell.height_m));
  const waveMax = Math.max(0, ...windows.map((window) => window.conditions.swell.wave_height_m ?? window.conditions.swell.height_m));
  const swellMax = Math.max(0, ...windows.map((window) => window.conditions.swell.height_m));
  const rainTotal = windows.reduce((sum, window) => sum + (window.conditions.air?.rain_mm ?? window.conditions.air?.precipitation_mm ?? 0), 0);
  const temperatureAvg = averageFloat(windows.map((window) => window.conditions.air?.temperature_c));
  const pressureAvg = averageFloat(windows.map((window) => window.conditions.pressure_hpa));
  const shockMax = Math.max(0, ...windows.map((window) => window.conditions.weather_trend?.shock_score ?? 0));
  const tideMovementMax = Math.max(0, ...windows.map((window) => Math.abs(window.conditions.tide.movement_rate_m_per_hour ?? 0)));
  const tideRangeAvg = averageFloat(windows.map((window) => window.conditions.tide.range_m));
  const tidePhases = Array.from(new Set(windows.map((window) => window.conditions.tide.phase).filter(Boolean)));
  return { gustMax, pressureAvg, rainTotal, shockMax, swellMax, temperatureAvg, tideMovementMax, tidePhases, tideRangeAvg, waveAvg, waveMax, windAvg };
}

function fishIndexMeaning(summary: ReturnType<typeof dailyScoreSummary>, lang: Lang = "en") {
  const fish = summary.fishIndex;
  if (fish == null) return lang === "zh" ? "鱼情指数还不足以判断全天强弱。" : "Not enough fish-signal data to read the day yet.";
  if (lang === "zh") {
    if (fish >= 70) return "鱼情指数代表当天鱼活跃度和靠岸信号，当前整体偏强。";
    if (fish >= 55) return "鱼情指数代表当天鱼活跃度和靠岸信号，当前有机会但不算稳定强。";
    if (fish >= 40) return "鱼情指数代表当天鱼活跃度和靠岸信号，当前偏一般，只适合看短窗口。";
    return "鱼情指数代表当天鱼活跃度和靠岸信号，当前偏弱。";
  }
  if (fish >= 70) return "Fish index reflects bite activity and near-shore presence; today's fish signal is strong.";
  if (fish >= 55) return "Fish index reflects bite activity and near-shore presence; today has usable fish signal.";
  if (fish >= 40) return "Fish index reflects bite activity and near-shore presence; today is mixed and short-window focused.";
  return "Fish index reflects bite activity and near-shore presence; today's fish signal is weak.";
}

type ScoreFactorsBlocks = {
  positive: string[];
  negative: string[];
  summary?: string;
};

/** Rule-based fallback: split tide / weather / sea into helpful vs challenging bullets. */
function dayScoreFactorsBullets(
  day?: { best_window: WindowCard | null; windows: WindowCard[] } | null,
  lang: Lang = "en"
): ScoreFactorsBlocks | null {
  const summary = dailyScoreSummary(day);
  if (summary.weighted == null) return null;

  const stats = dayConditionStats(day);
  const positive: string[] = [];
  const negative: string[] = [];

  if (stats.tideMovementMax >= 0.18) {
    positive.push(
      lang === "zh"
        ? "潮水交换较活跃，近岸水体更新更明显。"
        : "Tide movement is clearly felt—water exchanges well near shore."
    );
  } else if (stats.tideMovementMax >= 0.08) {
    positive.push(
      lang === "zh"
        ? "有一定潮水流速，水体在中等程度上流动。"
        : "There is moderate tidal flow—enough water movement to notice."
    );
  } else {
    negative.push(
      lang === "zh"
        ? "潮水整体偏弱，水流带动力不足。"
        : "Tide flow is weak, so less water movement to spark activity."
    );
  }

  if (stats.tideRangeAvg != null && stats.tideRangeAvg >= 0.65) {
    positive.push(
      lang === "zh"
        ? "潮差相对可观，潮水进退更有存在感。"
        : "Tidal range is reasonably wide, so highs and lows matter more."
    );
  }

  const cold = stats.temperatureAvg != null && stats.temperatureAvg < 9;
  const windy = stats.windAvg != null && stats.windAvg > 16;
  const gusty = stats.gustMax > 24;
  const rainy = stats.rainTotal >= 2;
  const volatile = stats.shockMax >= 2;
  if (cold) {
    negative.push(lang === "zh" ? "平均气温偏低，体感偏冷。" : "Cool air temperatures make it feel chilly.");
  }
  if (windy) {
    negative.push(lang === "zh" ? "平均风力偏大，对线组和站位要求更高。" : "Steady wind is on the stronger side for casting and footing.");
  }
  if (gusty) {
    negative.push(lang === "zh" ? "阵风偏强，抛投与站稳都要留心。" : "Gusts are sharp enough to affect casting and balance.");
  }
  if (rainy) {
    negative.push(lang === "zh" ? "窗口期内累计降雨明显。" : "Meaningful rain across the day’s windows.");
  }
  if (volatile) {
    negative.push(lang === "zh" ? "近期天气序列波动较大。" : "Recent weather has been unstable.");
  }

  if (!cold && !windy && !gusty && !rainy && !volatile) {
    positive.push(
      lang === "zh"
        ? "天气整体相对温和，没有极端低温、大风大雨或剧烈突变。"
        : "Weather is relatively mild—no extreme cold, heavy rain, or wild swings."
    );
  }

  if (stats.waveMax >= 2) {
    negative.push(
      lang === "zh"
        ? "浪高偏大，近岸折腾度与安全余量下降。"
        : "Seas are fairly rough—comfort and safety margin drop near shore."
    );
  } else if (stats.waveMax >= 1.2) {
    negative.push(
      lang === "zh"
        ? "海浪中等偏高，有遮蔽的位置会更舒服。"
        : "Waves run moderately high—sheltered spots are easier."
    );
  } else {
    positive.push(
      lang === "zh"
        ? "浪高不大，海面整体相对温顺。"
        : "Waves stay modest—the sea state is unlikely to be the main blocker."
    );
  }

  const phases = stats.tidePhases.filter((p): p is string => typeof p === "string" && Boolean(p));
  if (phases.length > 0) {
    positive.push(
      lang === "zh"
        ? `各时段潮相包括：${phases.join("、")}。`
        : `Tide phases across windows include: ${phases.join(", ")}.`
    );
  }

  const trendNotes = firstWeatherChangeNotes(day, 3);
  if (trendNotes.length > 0) {
    const line =
      lang === "zh"
        ? `预报序列提示：${trendNotes.join("；")}。`
        : `Forecast trend notes: ${trendNotes.join("; ")}.`;
    if (volatile || stats.shockMax >= 1.5) {
      negative.push(line);
    } else {
      positive.push(line);
    }
  }

  const dedupe = (items: string[]) => Array.from(new Set(items.map((s) => s.trim()).filter(Boolean)));

  return {
    positive: dedupe(positive),
    negative: dedupe(negative),
  };
}

function plainWindowLabel(value?: string | null, lang: Lang = "en") {
  const label = displayWaterType(value, lang);
  if (lang === "zh") return label;
  if (label === "Dusk") return "late afternoon";
  if (label === "Morning") return "morning";
  if (label === "Pre Dawn") return "early morning";
  if (label === "Day") return "daytime";
  return label.toLowerCase();
}

function friendlyScoreReason(window: WindowCard | null, summary: ReturnType<typeof dailyScoreSummary>, lang: Lang = "en") {
  if (!window) return [];
  const condition = window.conditions;
  const score = summary.weighted ?? selectedWindowScore(window);
  const wind = condition.wind.speed_knots;
  const gust = condition.wind.gust_knots ?? condition.wind.recent_max_12h ?? null;
  const wave = condition.swell.wave_height_m ?? condition.swell.height_m;
  const swell = condition.swell.height_m;
  const rain = condition.air?.rain_mm ?? condition.air?.precipitation_mm ?? 0;
  const temperature = condition.air?.temperature_c ?? null;
  const shock = condition.weather_trend?.shock_score ?? 0;
  const tags = new Set([...(window.negative_reason_tags ?? []), ...(condition.weather_trend?.change_notes ?? [])]);
  if (lang === "zh") {
    const fishReason =
      score == null
        ? "🎣 鱼情：等待预测"
        : score >= 70
          ? `🎣 鱼情：${plainWindowLabel(window.time_window, lang)}窗口较强`
          : score >= 55
            ? "🎣 鱼情：尚可，计划要聚焦"
            : score >= 40
              ? "🎣 鱼情：偏零散，只适合短试"
              : tags.has("big_wave") || tags.has("rough") || wave >= 2
                ? "🎣 鱼情：水况不稳，表现偏弱"
                : tags.has("weather_shock") || tags.has("trend_break") || shock >= 2
                  ? "🎣 鱼情：天气变化后偏弱"
                  : "🎣 鱼情：偏弱，建议等或换点";
    const weatherProblems = [
      wind > 16 ? "风偏强" : null,
      gust != null && gust > 24 ? "阵风偏强" : null,
      rain >= 2 ? "有雨" : null,
      temperature != null && temperature < 9 ? "气温偏冷" : null,
      shock >= 2 ? "近期天气变化" : null
    ].filter(Boolean);
    const weatherReason = weatherProblems.length
      ? `🍃 天气：体感一般，${weatherProblems.slice(0, 2).join("、")}`
      : "🍃 天气：体感舒适";
    const waveReason =
      wave >= 3
        ? "🌊 浪况：浪很大，避开外露水域"
        : wave >= 2
          ? "🌊 浪况：浪偏大，选择有遮蔽处"
          : wave >= 1.2
            ? "🌊 浪况：中等偏大"
            : "🌊 浪况：不大";
    const safetyProblems = [
      swell >= 2 || wave >= 2.5 ? "外露礁石和沙滩需要谨慎" : null,
      gust != null && gust >= 30 ? "强阵风会影响抛投和站稳" : null,
      wind >= 25 ? "强风会增加暴露风险" : null,
      rain >= 8 ? "大雨会影响视线和脚下安全" : null
    ].filter(Boolean);
    const safetyReason = safetyProblems.length ? `⚠️ 安全：${safetyProblems[0]}` : "⚠️ 安全：未发现明显风险";
    return [fishReason, weatherReason, waveReason, safetyReason];
  }

  const fishReason =
    score == null
      ? "🎣 Fish: waiting for forecast"
      : score >= 70
        ? `🎣 Fish: strong ${plainWindowLabel(window.time_window, lang)} window`
        : score >= 55
          ? "🎣 Fish: fair, keep the plan focused"
          : score >= 40
            ? "🎣 Fish: patchy, short look only"
            : tags.has("big_wave") || tags.has("rough") || wave >= 2
              ? "🎣 Fish: poor, unsettled water"
              : tags.has("weather_shock") || tags.has("trend_break") || shock >= 2
                ? "🎣 Fish: poor after weather change"
                : "🎣 Fish: poor, wait or change spot";
  const weatherProblems = [
    wind > 16 ? "strong wind" : null,
    gust != null && gust > 24 ? "strong gusts" : null,
    rain >= 2 ? "rain" : null,
    temperature != null && temperature < 9 ? "cold air" : null,
    shock >= 2 ? "recent weather change" : null
  ].filter(Boolean);
  const weatherReason = weatherProblems.length
    ? `🍃 Weather: uncomfortable, ${weatherProblems.slice(0, 2).join(" and ")}`
    : "🍃 Weather: comfortable";
  const waveReason =
    wave >= 3
      ? "🌊 Waves: very large, avoid exposure"
      : wave >= 2
        ? "🌊 Waves: large, choose shelter"
        : wave >= 1.2
          ? "🌊 Waves: moderate to large"
          : "🌊 Waves: not large";
  const safetyProblems = [
    swell >= 2 || wave >= 2.5 ? "exposed rocks and beaches need caution" : null,
    gust != null && gust >= 30 ? "strong gusts can make casting and footing risky" : null,
    wind >= 25 ? "strong wind increases exposure risk" : null,
    rain >= 8 ? "heavy rain can affect visibility and footing" : null
  ].filter(Boolean);
  const safetyReason = safetyProblems.length
    ? `⚠️ Safety: ${safetyProblems[0]}`
    : "⚠️ Safety: no obvious risk";
  return [fishReason, weatherReason, waveReason, safetyReason];
}

function lightLevelText(window: WindowCard, lang: Lang = "en") {
  const condition = window.conditions;
  if (lang === "zh") {
    if (condition.solar?.is_daylight === false) return "弱光";
    if (window.time_window === "morning" || window.time_window === "dusk") return "光线变化";
    return "白天";
  }
  if (condition.solar?.is_daylight === false) return "low light";
  if (window.time_window === "morning" || window.time_window === "dusk") return "change of light";
  return "daylight";
}

function windComfortText(window: WindowCard, lang: Lang = "en") {
  const wind = window.conditions.wind.speed_knots;
  if (lang === "zh") {
    if (wind <= 8) return "风小且舒服";
    if (wind <= 14) return "可接受";
    return "外露区域会更难操作";
  }
  if (wind <= 8) return "light and comfortable";
  if (wind <= 14) return "manageable";
  return "exposed areas may be harder";
}

function seaComfortText(window: WindowCard, lang: Lang = "en") {
  const swell = window.conditions.swell.height_m;
  if (lang === "zh") {
    if (swell <= 0.3) return "水面平静";
    if (swell <= 0.8) return "可钓";
    return "水况偏粗";
  }
  if (swell <= 0.3) return "calm";
  if (swell <= 0.8) return "fishable";
  return "rougher";
}

function DayOverviewPanel({ day, lang }: { day: { best_window: WindowCard | null; windows: WindowCard[] } | null | undefined; lang: Lang }) {
  if (!day?.windows.length) return null;
  const text = copy(lang);
  const summary = dailyScoreSummary(day);
  const stats = dayConditionStats(day);
  const tideLabel =
    stats.tidePhases.length > 1
      ? (lang === "zh" ? "多阶段潮汐" : "mixed tide")
      : displayWaterType(stats.tidePhases[0], lang);
  const tideNote =
    stats.tideMovementMax >= 0.18
      ? (lang === "zh" ? "全天有较明显水流" : "clear water movement during the day")
      : stats.tideMovementMax >= 0.08
        ? (lang === "zh" ? "水流中等，别只看时间" : "moderate movement; do not rely on time alone")
        : (lang === "zh" ? "水流偏弱，鱼情容易分散" : "weaker movement can make fish activity patchy");
  const weatherProblems = [
    stats.windAvg != null && stats.windAvg > 16 ? (lang === "zh" ? "平均风偏强" : "windy") : null,
    stats.gustMax > 24 ? (lang === "zh" ? "阵风偏强" : "strong gusts") : null,
    stats.rainTotal >= 2 ? (lang === "zh" ? "有雨" : "rain") : null,
    stats.temperatureAvg != null && stats.temperatureAvg < 9 ? (lang === "zh" ? "偏冷" : "cold") : null,
    stats.shockMax >= 2 ? (lang === "zh" ? "近期天气变化" : "recent weather change") : null
  ].filter(Boolean);
  const marineProblems = [
    stats.waveMax >= 2 ? (lang === "zh" ? "外露水域浪偏大" : "rougher exposed water") : null,
    stats.swellMax >= 2 ? (lang === "zh" ? "涌浪偏大" : "larger swell") : null,
    stats.gustMax >= 30 ? (lang === "zh" ? "强阵风影响站稳和抛投" : "gusts can affect footing and casting") : null
  ].filter(Boolean);
  const rows = [
    {
      icon: "🎣",
      label: lang === "zh" ? "鱼情整体" : "Fish outlook",
      value: `${summary.fishIndex ?? "--"} ${lang === "zh" ? "鱼情指数" : "fish index"}`,
      note: fishIndexMeaning(summary, lang)
    },
    {
      icon: "🌊",
      label: lang === "zh" ? "水流/潮汐" : "Water movement",
      value: tideLabel,
      note: tideNote
    },
    {
      icon: "🍃",
      label: lang === "zh" ? "天气体感" : "Weather comfort",
      value: `${stats.windAvg?.toFixed(1) ?? "--"} kt${stats.temperatureAvg != null ? ` · ${stats.temperatureAvg.toFixed(0)}°C` : ""}`,
      note: weatherProblems.length
        ? (lang === "zh" ? weatherProblems.slice(0, 2).join("、") : weatherProblems.slice(0, 2).join(" and "))
        : (lang === "zh" ? "整体舒适" : "comfortable overall")
    },
    {
      icon: "⚠️",
      label: lang === "zh" ? "浪况/安全" : "Waves + safety",
      value: `${stats.waveMax.toFixed(2)} m ${lang === "zh" ? "最高浪" : "max waves"}`,
      note: marineProblems.length
        ? (lang === "zh" ? marineProblems[0] : marineProblems[0])
        : (lang === "zh" ? "未见明显大风险" : "no obvious broad risk")
    }
  ];
  const shortRules = [
    summary.weighted == null
      ? (lang === "zh" ? "等待评分" : "Waiting for score")
      : summary.weighted >= 55
        ? (lang === "zh" ? "全天可钓" : "Fishable day")
        : summary.weighted >= 40
          ? (lang === "zh" ? "全天一般" : "Mixed day")
          : (lang === "zh" ? "全天偏弱" : "Weak day"),
    stats.tideMovementMax >= 0.18
      ? (lang === "zh" ? "水流明显" : "Clear tide movement")
      : stats.tideMovementMax >= 0.08
        ? (lang === "zh" ? "水流中等" : "Moderate tide movement")
        : (lang === "zh" ? "水流偏弱" : "Weak tide movement"),
    stats.windAvg != null && stats.windAvg > 16
      ? (lang === "zh" ? "风偏强" : "Windy overall")
      : stats.temperatureAvg != null && stats.temperatureAvg < 9
        ? (lang === "zh" ? "体感偏冷" : "Cold air")
        : (lang === "zh" ? "天气可控" : "Manageable weather"),
    stats.waveMax >= 2
      ? (lang === "zh" ? "避开外露水域" : "Avoid exposed water")
      : (lang === "zh" ? "浪况不大" : "Waves not large")
  ];
  return (
    <div className="formula-panel">
      <div className="formula-head">
        <span>{text.whyWindow}</span>
      </div>
      <div className="formula-grid">
        {rows.map((row) => (
          <div key={row.label}>
            <span><i>{row.icon}</i>{row.label}</span>
            <b>{row.value}</b>
            <small>{row.note}</small>
          </div>
        ))}
      </div>
      <div className="rule-strip" aria-label={lang === "zh" ? "全天主要信号" : "Main day signals"}>
        {shortRules.map((rule) => <span key={rule}>{rule}</span>)}
      </div>
    </div>
  );
}

function potentialSpots(structures: StructureFacility[], window: WindowCard | null, lang: Lang = "en") {
  const fallbackScore = selectedWindowScore(window) ?? window?.score ?? null;
  const scoreForType = (type: string) => {
    if (type === "beach_access") return window?.water_type_scores.find((item) => item.key === "beach")?.score ?? fallbackScore;
    if (type === "rocky_shoreline") return window?.water_type_scores.find((item) => item.key === "rocks")?.score ?? fallbackScore;
    if (type === "public_jetty" || type === "fishing_platform") {
      return window?.water_type_scores.find((item) => item.key.includes("jetty"))?.score ?? fallbackScore;
    }
    return fallbackScore;
  };
  const fishingAccess = structures
    .filter((item) => item.planner_eligible && item.access === "public" && isWithinVisibleStructureRadius(item))
    .slice(0, 3)
    .map((item) => ({
      title: item.label,
      meta: `${formatStructureType(item.type, lang)} · ${item.distance_km ?? "?"} km`,
      scoreLabel: scoreForType(item.type) == null ? "--" : String(scoreForType(item.type)),
      tone: "strong",
      note: lang === "zh"
        ? (item.source === "list_wildfisheries" ? "本次搜索附近的官方钓点。" : "本次搜索附近的公共钓点入口。")
        : (item.source === "list_wildfisheries" ? "Official fishing map entry near this search." : "Public fishing access near this search."),
      advantage: item.source === "list_wildfisheries"
        ? (lang === "zh" ? "为什么有帮助：官方点位能提供真实可规划的位置。" : "Why it helps: official spot data gives a real place to plan around.")
        : (lang === "zh" ? "为什么有帮助：清楚入口靠近边线和水流变化。" : "Why it helps: clear access near edge and current changes.")
    }));

  return fishingAccess.slice(0, 5);
}

function publicFishingStructures(structures: StructureFacility[]) {
  return structures.filter(
    (structure) => structure.planner_eligible && structure.access === "public" && isWithinVisibleStructureRadius(structure)
  );
}

function mapReferenceStructures(structures: StructureFacility[]) {
  return structures.filter(shouldShowStructure);
}

function StructureMap({
  structures,
  window,
  center,
  lang,
  unsupported
}: {
  structures: StructureFacility[];
  window: WindowCard | null;
  center: ForecastResponse["selected_place"];
  lang: Lang;
  unsupported?: ForecastResponse | null;
}) {
  const text = copy(lang);
  const mapRef = useRef<HTMLDivElement | null>(null);
  const dragRef = useRef<null | {
    pointerId: number;
    startX: number;
    startY: number;
    centerX: number;
    centerY: number;
  }>(null);
  const [viewCenter, setViewCenter] = useState(center ? { latitude: center.latitude, longitude: center.longitude } : null);
  const [viewZoom, setViewZoom] = useState(MAP_ZOOM);
  const [activeStructure, setActiveStructure] = useState<StructureFacility | null>(null);
  const [mapDimensions, setMapDimensions] = useState({ width: MAP_DEFAULT_WIDTH, height: MAP_DEFAULT_HEIGHT });

  useEffect(() => {
    setViewCenter(center ? { latitude: center.latitude, longitude: center.longitude } : null);
    setViewZoom(MAP_ZOOM);
    setActiveStructure(null);
  }, [center?.latitude, center?.longitude]);

  useEffect(() => {
    const element = mapRef.current;
    if (!element) return;
    const updateDimensions = () => {
      const width = Math.max(320, Math.round(element.clientWidth));
      const height = Math.max(320, Math.round(element.clientHeight));
      setMapDimensions((current) => (current.width === width && current.height === height ? current : { width, height }));
    };
    updateDimensions();
    const observer = new ResizeObserver(updateDimensions);
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  const eligible = publicFishingStructures(structures);
  const viewport = viewCenter ? mapViewport(viewCenter, viewZoom, mapDimensions) : null;
  const tiles = viewport ? mapTiles(viewport) : [];
  const searchPosition = center && viewport ? pointOnMap(center, viewport) : null;
  const visible = viewport
    ? mapReferenceStructures(structures)
        .filter((structure) => structure.coordinates)
        .map((structure) => ({ structure, position: pointOnMap(structure.coordinates!, viewport) }))
        .filter((item) => item.position.visible)
        .slice(0, 36)
    : [];
  const activePosition =
    activeStructure?.coordinates && viewport ? pointOnMap(activeStructure.coordinates, viewport) : null;
  const spots = potentialSpots(structures, window, lang);
  const isUnsupported = Boolean(unsupported);

  function beginDrag(event: PointerEvent<HTMLDivElement>) {
    if (!viewCenter) return;
    if ((event.target as HTMLElement).closest("button,a")) return;
    event.currentTarget.setPointerCapture(event.pointerId);
    dragRef.current = {
      pointerId: event.pointerId,
      startX: event.clientX,
      startY: event.clientY,
      centerX: longitudeToWorldX(viewCenter.longitude, viewZoom),
      centerY: latitudeToWorldY(viewCenter.latitude, viewZoom)
    };
  }

  function updateDrag(event: PointerEvent<HTMLDivElement>) {
    const drag = dragRef.current;
    if (!drag || drag.pointerId !== event.pointerId) return;
    const nextX = drag.centerX - (event.clientX - drag.startX);
    const nextY = drag.centerY - (event.clientY - drag.startY);
    setViewCenter(worldToCoordinates(nextX, nextY, viewZoom));
  }

  function endDrag(event: PointerEvent<HTMLDivElement>) {
    if (dragRef.current?.pointerId === event.pointerId) {
      dragRef.current = null;
    }
  }

  function resetMap() {
    if (!center) return;
    setViewCenter({ latitude: center.latitude, longitude: center.longitude });
    setViewZoom(MAP_ZOOM);
    setActiveStructure(null);
  }

  function zoomMap(direction: 1 | -1) {
    setViewZoom((current) => Math.min(MAP_MAX_ZOOM, Math.max(MAP_MIN_ZOOM, current + direction)));
  }

  return (
    <section className="map-card map-feature">
      <div className="map-feature-head">
        <div>
          <div className="section-label">{isUnsupported ? text.selectedMap : text.primaryMap}</div>
          <h2>{isUnsupported ? text.unsupportedMapTitle : text.publicAccessTitle}</h2>
        </div>
        {isUnsupported ? (
          <div className="structure-summary unsupported-summary">
            <strong>0</strong>
            <span>{text.supportedSignals}</span>
          </div>
        ) : (
          <div className="structure-summary">
            <strong>{eligible.length}</strong>
            <span>{text.officialAccess}</span>
          </div>
        )}
      </div>
      <div className="map-content">
        <div
          className="map-stage"
          ref={mapRef}
          aria-label={lang === "zh" ? "附近公共钓点地图预览" : "Nearby public structure map preview"}
          onPointerCancel={endDrag}
          onPointerDown={beginDrag}
          onPointerLeave={endDrag}
          onPointerMove={updateDrag}
          onPointerUp={endDrag}
        >
          {viewport ? (
            <>
              <div className="tile-pane" aria-hidden="true">
                {tiles.map((tile) => (
                  <img
                    alt=""
                    draggable="false"
                    key={tile.key}
                    src={tile.src}
                    style={{
                      height: `${tile.height}%`,
                      left: `${tile.left}%`,
                      top: `${tile.top}%`,
                      width: `${tile.width}%`
                    }}
                  />
                ))}
              </div>
              <div className="map-shade" />
              <div className="north-mark">N</div>
              {searchPosition ? (
                <div
                  className="search-pin"
                  aria-label={text.searchPoint}
                  style={{ left: `${searchPosition.left}%`, top: `${searchPosition.top}%` }}
                  title={text.searchPoint}
                />
              ) : null}
              <div className="map-controls" aria-label={text.mapControls}>
                <button onClick={() => zoomMap(1)} type="button">+</button>
                <button onClick={() => zoomMap(-1)} type="button">−</button>
                <button onClick={resetMap} type="button">{text.reset}</button>
              </div>
              <div className="map-help">{text.dragMap}</div>
            </>
          ) : (
            <div className="map-empty">{text.noMapCenter}</div>
          )}
          {visible.map(({ structure, position }) => {
            const kind = markerKind(structure);
            return (
              <button
                aria-label={`Show ${structure.label}`}
                className={`marker ${kind}${activeStructure?.id === structure.id ? " active" : ""}`}
                key={structure.id}
                onClick={(event) => {
                  event.stopPropagation();
                  setActiveStructure(structure);
                }}
                style={{ left: `${position.left}%`, top: `${position.top}%` }}
                title={`${structure.label} · ${formatAccess(structure.access, lang)}`}
                type="button"
              >
                <span>{markerLabel(structure)}</span>
              </button>
            );
          })}
          {activeStructure && activePosition?.visible ? (
            <div
              className="map-popup"
              style={{ left: `${activePosition.left}%`, top: `${activePosition.top}%` }}
            >
              <button aria-label={text.closeMarker} onClick={() => setActiveStructure(null)} type="button">×</button>
              <b>{activeStructure.label}</b>
              <small>
                {formatStructureType(activeStructure.type, lang)} · {formatAccess(activeStructure.access, lang)}
              </small>
              <p>
                {text.publicPlanNote}
              </p>
              <small>
                {activeStructure.distance_km ?? "?"} km · {formatSource(activeStructure.source, lang)}
              </small>
            </div>
          ) : null}
          {!isUnsupported ? (
            <div className="map-legend" aria-label={text.mapLegend}>
              <span><i className="legend-public" />{text.fishingAccess}</span>
            </div>
          ) : null}
          <a
            className="map-attribution"
            href="https://www.openstreetmap.org/copyright"
            rel="noreferrer"
            target="_blank"
          >
            © OpenStreetMap contributors
          </a>
        </div>
        {isUnsupported ? (
          <aside className="potential-card unsupported-map-note">
            <div className="section-label">{text.unsupported}</div>
            <h3>{text.unsupportedAdvice}</h3>
            <p>{unsupported?.plan.primary_action.text}</p>
            <small>
              {text.selectedCoordinate}: {center?.latitude.toFixed(4)}, {center?.longitude.toFixed(4)}
            </small>
          </aside>
        ) : (
          <aside className="potential-card">
            <div className="section-label">{text.mapLeads}</div>
            <p className="spot-intro">{text.mapIntro}</p>
            <div className="spot-list">
              {spots.length ? spots.map((spot) => (
                <div className={`spot-row ${spot.tone}`} key={`${spot.title}-${spot.meta}`}>
                  <div className="spot-row-head">
                    <div>
                      <b>{spot.title}</b>
                      <small>{spot.meta}</small>
                    </div>
                    <strong>{spot.scoreLabel}</strong>
                  </div>
                  <p>{spot.note}</p>
                  <em>{spot.advantage}</em>
                </div>
              )) : (
                <div className="spot-row caution">
                  <div className="spot-row-head">
                    <div>
                      <b>{text.noAccess}</b>
                      <small>{text.noAccessMeta}</small>
                    </div>
                  </div>
                  <p>{text.noAccessNote}</p>
                </div>
              )}
            </div>
          </aside>
        )}
      </div>
    </section>
  );
}

function FishingPlanCard({
  data,
  lang,
  selectedDate,
  onSelectDate
}: {
  data: ForecastResponse;
  lang: Lang;
  selectedDate: string | null;
  onSelectDate: (date: string) => void;
}) {
  const text = copy(lang);
  const dailyForecast = data.forecast?.daily_forecast ?? [];
  const selectedDay = dailyForecast.find((day) => day.date === selectedDate) ?? dailyForecast[0];
  const windows = selectedDay?.windows ?? [];
  const hourlyActivity = data.forecast?.hourly_activity ?? [];
  const selectedScore = dayScore(selectedDay);
  const selectedLabel = recommendationLabel(selectedScore);
  const tone = scoreTone(selectedLabel);
  const scoreFactorsFallback = dayScoreFactorsBullets(selectedDay, lang);
  const [scoreFactorsLlm, setScoreFactorsLlm] = useState<ScoreFactorsBlocks | null>(null);
  const [scoreFactorsLlmLoading, setScoreFactorsLlmLoading] = useState(false);

  useEffect(() => {
    if (!selectedDay?.windows?.length) {
      setScoreFactorsLlm(null);
      setScoreFactorsLlmLoading(false);
      return;
    }
    const controller = new AbortController();
    setScoreFactorsLlmLoading(true);
    setScoreFactorsLlm(null);
    fetch("/api/score-factors", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        lang,
        date: selectedDay.date ?? "",
        windows: selectedDay.windows,
      }),
      signal: controller.signal,
    })
      .then((res) => res.json())
      .then(
        (payload: {
          positive_factors?: string[];
          negative_factors?: string[];
          summary?: string;
        }) => {
          if (controller.signal.aborted) return;
          const pos = Array.isArray(payload.positive_factors)
            ? payload.positive_factors.filter((s): s is string => typeof s === "string").map((s) => s.trim()).filter(Boolean)
            : [];
          const neg = Array.isArray(payload.negative_factors)
            ? payload.negative_factors.filter((s): s is string => typeof s === "string").map((s) => s.trim()).filter(Boolean)
            : [];
          if (!pos.length && !neg.length) {
            setScoreFactorsLlm(null);
            return;
          }
          const sum =
            typeof payload.summary === "string" && payload.summary.trim().length > 0 ? payload.summary.trim() : undefined;
          setScoreFactorsLlm({ positive: pos, negative: neg, summary: sum });
        }
      )
      .catch(() => {
        if (!controller.signal.aborted) setScoreFactorsLlm(null);
      })
      .finally(() => {
        if (!controller.signal.aborted) setScoreFactorsLlmLoading(false);
      });
    return () => controller.abort();
  }, [selectedDay, lang]);

  const scoreFactorsDisplay = scoreFactorsLlm ?? scoreFactorsFallback;

  return (
    <section className="plan-card">
      <div className="plan-head">
        <span className={`recommendation ${tone}`}>{recommendationDisplay(selectedLabel, lang)}</span>
        <span className="score">{selectedScore ?? "--"}</span>
      </div>
      <h2>{daySummaryText(selectedDay, lang)}</h2>
      <FishingCurve
        days={dailyForecast}
        lang={lang}
        onSelectDate={onSelectDate}
        selectedDate={selectedDay?.date ?? null}
        windows={windows}
        hourlyActivity={hourlyActivity.filter((point) => !selectedDay?.date || point.date === selectedDay.date)}
      />
      <DayOverviewPanel day={selectedDay} lang={lang} />
      <div className="action-block primary score-factor-copy">
        <span>{text.scoreFactors}</span>
        {scoreFactorsLlmLoading ? (
          <p className="score-factor-loading">{text.scoreFactorsGenerating}</p>
        ) : scoreFactorsDisplay ? (
          <>
            <div className="score-factor-lists">
              <div className="score-factor-col score-factor-positive">
                <h4>{text.scoreFactorsPositive}</h4>
                {scoreFactorsDisplay.positive.length ? (
                  <ul>
                    {scoreFactorsDisplay.positive.map((line) => (
                      <li key={line}>{line}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="score-factor-empty">{lang === "zh" ? "（无明显加分项）" : "(No standout positives.)"}</p>
                )}
              </div>
              <div className="score-factor-col score-factor-negative">
                <h4>{text.scoreFactorsNegative}</h4>
                {scoreFactorsDisplay.negative.length ? (
                  <ul>
                    {scoreFactorsDisplay.negative.map((line) => (
                      <li key={line}>{line}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="score-factor-empty">{lang === "zh" ? "（无明显扣分项）" : "(No major negatives.)"}</p>
                )}
              </div>
            </div>
            {scoreFactorsDisplay.summary ? (
              <p className="score-factor-summary">{scoreFactorsDisplay.summary}</p>
            ) : null}
          </>
        ) : (
          <p>{lang === "zh" ? "当前数据不足。" : "Not enough data yet."}</p>
        )}
      </div>
    </section>
  );
}

function curveHour(windowKey: string) {
  if (windowKey === "dawn" || windowKey === "morning") return 7;
  if (windowKey === "pre_dawn") return 5;
  if (windowKey === "day") return 13;
  if (windowKey === "dusk") return 18;
  return 12;
}

function representativeHour(window: WindowCard | null) {
  if (!window) return null;
  const time = formatActionTime(window.representative_time);
  const hour = Number(time.slice(0, 2));
  return Number.isFinite(hour) ? hour : curveHour(window.time_window);
}

type CurveAnchor = {
  hour: number;
  score: number;
  activityScore?: number | null;
  presenceScore?: number | null;
  tripQualityScore?: number | null;
  bigFishNearShore?: string | null;
  label: string;
  tidePhase?: string | null;
  timeWindow?: string | null;
};

const CURVE_VIEWBOX_WIDTH = 1000;
const CURVE_VIEWBOX_HEIGHT = 220;
const CURVE_LEFT = 62;
const CURVE_RIGHT = 986;
const CURVE_TOP = 26;
const CURVE_BOTTOM = 158;
const CURVE_WIDTH = CURVE_RIGHT - CURVE_LEFT;
const CURVE_HEIGHT = CURVE_BOTTOM - CURVE_TOP;
const CURVE_Y_TICKS = [80, 50, 20];
const CURVE_X_TICKS = [0, 6, 12, 18, 23];

function formatCurveTime(hour: number) {
  const totalMinutes = Math.max(0, Math.min(23 * 60 + 59, Math.round(hour * 60)));
  const wholeHour = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  return `${String(wholeHour).padStart(2, "0")}:${String(minutes).padStart(2, "0")}`;
}

function formatCurveLabel(item: CurveAnchor, lang: Lang = "en") {
  const label = displayWaterType(item.timeWindow ?? item.label, lang);
  return lang === "zh" ? label : label.replace("Pre Dawn", "Pre-dawn");
}

function formatBigFishHint(value?: string | null, lang: Lang = "en") {
  if (lang === "zh") {
    if (value === "high") return "大鱼机会较高";
    if (value === "medium") return "有一些大鱼机会";
    if (value === "low") return "降低期待";
    return "舒适度";
  }
  if (value === "high") return "bigger fish chance";
  if (value === "medium") return "some bigger fish chance";
  if (value === "low") return "keep expectations modest";
  return "comfort";
}

function compassLabel(degrees?: number | null) {
  if (typeof degrees !== "number") return "--";
  const labels = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
  return labels[Math.round((((degrees % 360) + 360) % 360) / 45) % labels.length];
}

function windowRain(window: WindowCard) {
  return window.conditions.air?.rain_mm ?? window.conditions.air?.precipitation_mm ?? 0;
}

function windowWaveHeight(window: WindowCard) {
  return window.conditions.swell.wave_height_m ?? window.conditions.swell.height_m;
}

function hourlyRain(point: HourlyActivityPoint) {
  return point.rain_mm ?? point.precipitation_mm ?? 0;
}

/** Accept numeric strings from JSON edge paths so wave curves do not disappear. */
function coerceFiniteNumber(value: unknown): number | null {
  if (value === null || value === undefined) return null;
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string") {
    const trimmed = value.trim();
    if (!trimmed) return null;
    const n = Number(trimmed);
    return Number.isFinite(n) ? n : null;
  }
  return null;
}

function hourlyWave(point: HourlyActivityPoint): number | null {
  return coerceFiniteNumber(point.wave_height_m) ?? coerceFiniteNumber(point.swell_height_m);
}

function hourlyTideHeight(point: HourlyActivityPoint) {
  if (typeof point.tide_height_m === "number") return point.tide_height_m;
  return null;
}

function hourlyTideMovement(point: HourlyActivityPoint) {
  if (typeof point.tide_movement_rate_m_per_hour === "number") return Math.abs(point.tide_movement_rate_m_per_hour);
  return null;
}

function numberOrNull(value: number | null | undefined) {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function formatDateChip(value: string, lang: Lang = "en") {
  const date = new Date(`${value}T12:00:00`);
  return date.toLocaleDateString(lang === "zh" ? "zh-CN" : "en-AU", { weekday: "short", day: "2-digit" });
}

function todayIsoDate() {
  const date = new Date();
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function pickInitialDate(days: Array<{ date: string }>, fallback: string | null) {
  const today = todayIsoDate();
  return days.some((day) => day.date === today) ? today : fallback ?? days[0]?.date ?? null;
}

function interpolateOptionalScore(previous?: number | null, next?: number | null, ratio = 0) {
  if (typeof previous === "number" && typeof next === "number") {
    return Math.round(previous + (next - previous) * ratio);
  }
  return ratio < 0.5 ? previous ?? next ?? null : next ?? previous ?? null;
}

function interpolateCurve(anchors: CurveAnchor[], hour: number): CurveAnchor {
  const sorted = [...anchors].sort((a, b) => a.hour - b.hour);
  const clampedHour = Math.max(sorted[0].hour, Math.min(sorted[sorted.length - 1].hour, hour));
  const nextIndex = sorted.findIndex((item) => item.hour >= clampedHour);
  if (nextIndex <= 0) return { ...sorted[0], hour: clampedHour, score: sorted[0].score };
  const previous = sorted[nextIndex - 1];
  const next = sorted[nextIndex];
  const span = Math.max(1, next.hour - previous.hour);
  const ratio = (clampedHour - previous.hour) / span;
  const score = Math.round(previous.score + (next.score - previous.score) * ratio);
  const nearest = ratio < 0.5 ? previous : next;
  return {
    hour: clampedHour,
    score,
    activityScore: score,
    presenceScore: interpolateOptionalScore(previous.presenceScore, next.presenceScore, ratio),
    tripQualityScore: interpolateOptionalScore(previous.tripQualityScore, next.tripQualityScore, ratio),
    bigFishNearShore: nearest.bigFishNearShore,
    label: nearest.label,
    tidePhase: nearest.tidePhase,
    timeWindow: nearest.timeWindow
  };
}

function curvePoint<T extends { hour: number; score: number }>(item: T) {
  const x = CURVE_LEFT + (item.hour / 23) * CURVE_WIDTH;
  const y = CURVE_BOTTOM - (Math.max(0, Math.min(100, item.score)) / 100) * CURVE_HEIGHT;
  return { ...item, x, y };
}

function smoothCurvePath(points: Array<{ x: number; y: number }>) {
  if (!points.length) return "";
  if (points.length === 1) return `M ${points[0].x.toFixed(2)} ${points[0].y.toFixed(2)}`;
  let path = `M ${points[0].x.toFixed(2)} ${points[0].y.toFixed(2)}`;
  for (let index = 0; index < points.length - 1; index += 1) {
    const previous = points[index - 1] ?? points[index];
    const current = points[index];
    const next = points[index + 1];
    const afterNext = points[index + 2] ?? next;
    const controlOneX = current.x + (next.x - previous.x) / 6;
    const controlOneY = current.y + (next.y - previous.y) / 6;
    const controlTwoX = next.x - (afterNext.x - current.x) / 6;
    const controlTwoY = next.y - (afterNext.y - current.y) / 6;
    path += ` C ${controlOneX.toFixed(2)} ${controlOneY.toFixed(2)}, ${controlTwoX.toFixed(2)} ${controlTwoY.toFixed(2)}, ${next.x.toFixed(2)} ${next.y.toFixed(2)}`;
  }
  return path;
}

function FishingCurve({
  days,
  lang,
  onSelectDate,
  selectedDate,
  windows,
  hourlyActivity
}: {
  days: Array<{ date: string; best_window: WindowCard | null; windows: WindowCard[] }>;
  lang: Lang;
  onSelectDate: (date: string) => void;
  selectedDate: string | null;
  windows: WindowCard[];
  hourlyActivity: HourlyActivityPoint[];
}) {
  const text = copy(lang);
  const [active, setActive] = useState<CurveAnchor | null>(null);
  const dateStripRef = useRef<HTMLDivElement | null>(null);
  const dateDragRef = useRef<null | {
    pointerId: number;
    startX: number;
    startY: number;
    scrollLeft: number;
    moved: boolean;
  }>(null);
  const [isDraggingDates, setIsDraggingDates] = useState(false);
  const scored = hourlyActivity
    .filter((point) => typeof (point.activity_score ?? point.score) === "number")
    .map((point): CurveAnchor => ({
      hour: point.hour,
      score: (point.activity_score ?? point.score) as number,
      activityScore: point.activity_score ?? point.score,
      presenceScore: point.presence_score,
      tripQualityScore: point.trip_quality_score,
      bigFishNearShore: point.big_fish_near_shore,
      label: point.time_window ?? point.label ?? `${point.hour}:00`,
      tidePhase: point.tide_phase,
      timeWindow: point.time_window
    }));
  if (!scored.length && !windows.length) return null;
  const fallbackScored = windows
    .filter((window) => typeof window.score === "number")
    .map((window): CurveAnchor => ({
      hour: curveHour(window.time_window),
      score: window.activity_score ?? window.score,
      activityScore: window.activity_score ?? window.score,
      presenceScore: window.presence_score,
      tripQualityScore: window.trip_quality_score,
      bigFishNearShore: window.big_fish_near_shore,
      label: window.time_window,
      timeWindow: window.time_window
    }));
  const curveData = scored.length ? scored : fallbackScored;
  const best = curveData.length
    ? curveData.reduce((winner, item) => (item.score > winner.score ? item : winner), curveData[0])
    : null;
  useEffect(() => {
    if (best) setActive(best);
  }, [best?.hour, best?.score, best?.label]);
  useEffect(() => {
    const strip = dateStripRef.current;
    if (!strip || !selectedDate) return;
    const activeButton = strip.querySelector<HTMLButtonElement>(`button[data-date="${selectedDate}"]`);
    if (!activeButton) return;
    window.requestAnimationFrame(() => {
      strip.scrollLeft = activeButton.offsetLeft - strip.clientWidth / 2 + activeButton.clientWidth / 2;
    });
  }, [selectedDate, days.length]);
  if (!curveData.length || !best) return null;
  const activePointData = active ?? best;

  const anchors = curveData.length >= 12
    ? curveData
    : [
        {
          hour: 0,
          score: Math.max(20, curveData[0].score - 12),
          activityScore: Math.max(20, curveData[0].score - 12),
          presenceScore: curveData[0].presenceScore,
          tripQualityScore: curveData[0].tripQualityScore,
          bigFishNearShore: curveData[0].bigFishNearShore,
          label: "night",
          timeWindow: "night"
        },
        ...curveData,
        {
          hour: 23,
          score: Math.max(20, curveData[curveData.length - 1].score - 10),
          activityScore: Math.max(20, curveData[curveData.length - 1].score - 10),
          presenceScore: curveData[curveData.length - 1].presenceScore,
          tripQualityScore: curveData[curveData.length - 1].tripQualityScore,
          bigFishNearShore: curveData[curveData.length - 1].bigFishNearShore,
          label: "late",
          timeWindow: "night"
        }
      ];
  const plotted = anchors.map(curvePoint);
  const activePoint = curvePoint(activePointData);
  const linePath = smoothCurvePath(plotted);
  const fillPath = `${linePath} L ${CURVE_RIGHT} ${CURVE_BOTTOM} L ${CURVE_LEFT} ${CURVE_BOTTOM} Z`;
  function updateFromPointer(event: PointerEvent<SVGSVGElement>) {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = Math.max(0, Math.min(rect.width, event.clientX - rect.left));
    const chartX = (x / rect.width) * CURVE_VIEWBOX_WIDTH;
    const hour = ((Math.max(CURVE_LEFT, Math.min(CURVE_RIGHT, chartX)) - CURVE_LEFT) / CURVE_WIDTH) * 23;
    setActive(interpolateCurve(anchors, hour));
  }

  function beginDateDrag(event: PointerEvent<HTMLDivElement>) {
    const strip = dateStripRef.current;
    if (!strip) return;
    dateDragRef.current = {
      pointerId: event.pointerId,
      startX: event.clientX,
      startY: event.clientY,
      scrollLeft: strip.scrollLeft,
      moved: false
    };
    if (event.target instanceof Element && event.target.closest("button")) return;
    event.currentTarget.setPointerCapture(event.pointerId);
  }

  function updateDateDrag(event: PointerEvent<HTMLDivElement>) {
    const drag = dateDragRef.current;
    const strip = dateStripRef.current;
    if (!drag || !strip || drag.pointerId !== event.pointerId) return;
    const deltaX = event.clientX - drag.startX;
    const deltaY = event.clientY - drag.startY;
    if (Math.abs(deltaX) > 8 && Math.abs(deltaX) > Math.abs(deltaY)) {
      drag.moved = true;
      setIsDraggingDates(true);
      strip.scrollLeft = drag.scrollLeft - deltaX;
      event.preventDefault();
    }
  }

  function endDateDrag(event: PointerEvent<HTMLDivElement>) {
    const drag = dateDragRef.current;
    if (!drag || drag.pointerId !== event.pointerId) return;
    dateDragRef.current = null;
    setIsDraggingDates(false);
  }

  function selectDate(date: string) {
    onSelectDate(date);
  }

  return (
    <div className="fishing-curve">
      <div className="curve-head">
        <div>
          <span>{text.fishActivity24h}</span>
          <b>
            {formatCurveLabel(activePointData, lang)} · {formatCurveTime(activePointData.hour)} ·{" "}
            {lang === "zh" ? `活跃度 ${activePointData.score}` : `activity ${activePointData.score}`}
          </b>
        </div>
        <strong>{activePointData.score}</strong>
      </div>
      {days.length > 1 ? (
        <div className="date-strip-wrap">
          <div className="date-strip-head">
            <span>{text.historyForecast}</span>
            <small>{text.dragDates}</small>
          </div>
          <div
            className={`date-strip${isDraggingDates ? " dragging" : ""}`}
            aria-label={text.dateSelector}
            onPointerCancel={endDateDrag}
            onPointerDown={beginDateDrag}
            onPointerLeave={endDateDrag}
            onPointerMove={updateDateDrag}
            onPointerUp={endDateDrag}
            ref={dateStripRef}
          >
          {days.map((day) => (
            <button
              className={day.date === selectedDate ? "active" : ""}
              data-date={day.date}
              key={day.date}
              onClick={() => selectDate(day.date)}
              type="button"
            >
              {day.date === todayIsoDate() ? <em>{text.today}</em> : <span>{formatDateChip(day.date, lang)}</span>}
              <b>{dayMaxWindowScore(day) ?? "--"}</b>
              <small>{text.dateStripPeakLabel}</small>
            </button>
          ))}
          </div>
        </div>
      ) : null}
      <div className="curve-chart">
        <svg
          viewBox={`0 0 ${CURVE_VIEWBOX_WIDTH} ${CURVE_VIEWBOX_HEIGHT}`}
          preserveAspectRatio="none"
          aria-label={text.fishCurveLabel}
          onClick={updateFromPointer}
          onPointerMove={updateFromPointer}
        >
          <rect className="curve-plot-bg" x={CURVE_LEFT} y={CURVE_TOP} width={CURVE_WIDTH} height={CURVE_HEIGHT} rx="20" />
          {CURVE_Y_TICKS.map((tick) => {
            const y = CURVE_BOTTOM - (tick / 100) * CURVE_HEIGHT;
            return (
              <g key={tick}>
                <line className="curve-grid-line" x1={CURVE_LEFT} x2={CURVE_RIGHT} y1={y} y2={y} />
              </g>
            );
          })}
          {CURVE_X_TICKS.map((tick) => {
            const x = CURVE_LEFT + (tick / 23) * CURVE_WIDTH;
            return (
              <g key={tick}>
                <line className="curve-grid-line vertical" x1={x} x2={x} y1={CURVE_TOP} y2={CURVE_BOTTOM} />
              </g>
            );
          })}
          <path className="curve-fill" d={fillPath} />
          <path className="curve-line" d={linePath} />
          <line className="curve-cursor" x1={activePoint.x} x2={activePoint.x} y1={CURVE_TOP} y2={CURVE_BOTTOM} />
        </svg>
        <div className="curve-tooltip" style={{ left: `${(activePoint.x / CURVE_VIEWBOX_WIDTH) * 100}%` }}>
          {formatCurveTime(activePointData.hour)} · {activePointData.score}
        </div>
        <div className="curve-labels y-labels" aria-hidden="true">
          {CURVE_Y_TICKS.map((tick) => {
            const y = CURVE_BOTTOM - (tick / 100) * CURVE_HEIGHT;
            return <span key={tick} style={{ top: `${(y / CURVE_VIEWBOX_HEIGHT) * 100}%` }}>{tick}</span>;
          })}
        </div>
        <div className="curve-labels x-labels" aria-hidden="true">
          {CURVE_X_TICKS.map((tick) => {
            const x = CURVE_LEFT + (tick / 23) * CURVE_WIDTH;
            return <span key={tick} style={{ left: `${(x / CURVE_VIEWBOX_WIDTH) * 100}%` }}>{String(tick).padStart(2, "0")}</span>;
          })}
        </div>
      </div>
      <div className="score-mode-strip" aria-label={text.scoreLayers}>
        <div>
          <span>🎣 {text.activity}</span>
          <b>{activePointData.activityScore ?? activePointData.score}</b>
          <small>{text.biteTiming}</small>
        </div>
        <div>
          <span>🐟 {text.presence}</span>
          <b>{activePointData.presenceScore ?? "--"}</b>
          <small>{text.fishNearby}</small>
        </div>
        <div>
          <span>🌤 {text.trip}</span>
          <b>{activePointData.tripQualityScore ?? "--"}</b>
          <small>{formatBigFishHint(activePointData.bigFishNearShore, lang)}</small>
        </div>
      </div>
      <p>
        {best.score < 40
          ? (lang === "zh" ? "全天曲线整体偏弱。不要只因为某个小时略好就专门出发。" : "The whole-day curve is weak. Do not plan around one slightly better hour.")
          : (lang === "zh" ? "用曲线判断当天强弱节奏，但最终按全天天气、水流和浪况决定是否出发。" : "Use the curve to understand the day’s rhythm, then decide from the whole-day weather, water movement, and waves.")}
      </p>
    </div>
  );
}

type ForecastDay = NonNullable<ForecastResponse["forecast"]>["daily_forecast"][number];

type WeatherSeriesPoint = {
  hour: number;
  value: number;
  label: string;
};

function weatherCurvePath(points: WeatherSeriesPoint[], maxValue: number) {
  if (!points.length) return "";
  const plotted = points.map((point) => {
    const x = CURVE_LEFT + (point.hour / 23) * CURVE_WIDTH;
    const y = CURVE_BOTTOM - (Math.max(0, Math.min(maxValue, point.value)) / maxValue) * CURVE_HEIGHT;
    return { x, y };
  });
  return smoothCurvePath(plotted);
}

function WeatherCurve({
  label,
  unit,
  points,
  selectedHour,
  onSelectHour,
  note
}: {
  label: string;
  unit: string;
  points: WeatherSeriesPoint[];
  selectedHour: number;
  onSelectHour: (hour: number) => void;
  note?: string;
}) {
  if (!points.length) return null;
  const selected = points.reduce((closest, point) => (
    Math.abs(point.hour - selectedHour) < Math.abs(closest.hour - selectedHour) ? point : closest
  ), points[0]);
  const maxDataValue = Math.max(1, ...points.map((point) => point.value));
  const maxValue = maxDataValue;
  const linePath = weatherCurvePath(points, maxValue);
  const selectedPoint = curvePoint({ hour: selected.hour, score: (selected.value / maxValue) * 100 });
  const fillPath = `${linePath} L ${CURVE_RIGHT} ${CURVE_BOTTOM} L ${CURVE_LEFT} ${CURVE_BOTTOM} Z`;
  const decimals = unit === "mm" ? 1 : unit === "m" || unit === "m/h" ? 2 : 0;
  const selectedValueLabel = `${formatCurveTime(selected.hour)} · ${selected.value.toFixed(decimals)} ${unit}`;
  const yAxisTicks = CURVE_Y_TICKS.map((tick) => ({
    label: ((tick / 100) * maxValue).toFixed(decimals),
    top: `${((CURVE_BOTTOM - (tick / 100) * CURVE_HEIGHT) / CURVE_VIEWBOX_HEIGHT) * 100}%`
  }));
  function updateWeatherHour(event: PointerEvent<SVGSVGElement>) {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = Math.max(0, Math.min(rect.width, event.clientX - rect.left));
    const chartX = (x / rect.width) * CURVE_VIEWBOX_WIDTH;
    const hour = ((Math.max(CURVE_LEFT, Math.min(CURVE_RIGHT, chartX)) - CURVE_LEFT) / CURVE_WIDTH) * 23;
    onSelectHour(hour);
  }
  return (
    <div className="weather-curve-panel">
      <div className="weather-curve-head">
        <span>{label}</span>
        <b>{selectedValueLabel}</b>
      </div>
      <div className="weather-chart-shell">
        <div className="weather-y-axis" aria-hidden="true">
          {yAxisTicks.map((tick) => (
            <span key={tick.label} style={{ top: tick.top }}>{tick.label}</span>
          ))}
        </div>
        <div className="curve-chart">
          <svg
            viewBox={`0 0 ${CURVE_VIEWBOX_WIDTH} ${CURVE_VIEWBOX_HEIGHT}`}
            preserveAspectRatio="none"
            aria-label={`${label} hourly curve`}
            onClick={updateWeatherHour}
            onPointerMove={updateWeatherHour}
          >
            <rect className="curve-plot-bg" x={CURVE_LEFT} y={CURVE_TOP} width={CURVE_WIDTH} height={CURVE_HEIGHT} rx="20" />
            {CURVE_Y_TICKS.map((tick) => {
              const y = CURVE_BOTTOM - (tick / 100) * CURVE_HEIGHT;
              return <line className="curve-grid-line" key={tick} x1={CURVE_LEFT} x2={CURVE_RIGHT} y1={y} y2={y} />;
            })}
            {CURVE_X_TICKS.map((tick) => {
              const x = CURVE_LEFT + (tick / 23) * CURVE_WIDTH;
              return <line className="curve-grid-line vertical" key={tick} x1={x} x2={x} y1={CURVE_TOP} y2={CURVE_BOTTOM} />;
            })}
            <path className="curve-fill" d={fillPath} />
            <path className="curve-line" d={linePath} />
            <line className="curve-cursor" x1={selectedPoint.x} x2={selectedPoint.x} y1={CURVE_TOP} y2={CURVE_BOTTOM} />
          </svg>
          <div className="curve-tooltip" style={{ left: `${(selectedPoint.x / CURVE_VIEWBOX_WIDTH) * 100}%` }}>
            {selectedValueLabel}
          </div>
          <div className="curve-labels x-labels" aria-hidden="true">
            {CURVE_X_TICKS.map((tick) => {
              const x = CURVE_LEFT + (tick / 23) * CURVE_WIDTH;
              return <span key={tick} style={{ left: `${(x / CURVE_VIEWBOX_WIDTH) * 100}%` }}>{String(tick).padStart(2, "0")}</span>;
            })}
          </div>
        </div>
      </div>
      {note ? <p className="weather-curve-note">{note}</p> : null}
    </div>
  );
}

function windyCalendarParam(date: string | null | undefined, hour: number) {
  if (!date) return "now";
  const [year, month, day] = date.split("-").map((part) => Number(part));
  if (!year || !month || !day) return "now";
  const target = new Date(year, month - 1, day, Math.round(hour), 0, 0, 0);
  const leadHours = Math.round((target.getTime() - Date.now()) / 3_600_000);
  if (leadHours < 2) return "now";
  return String(Math.min(240, leadHours));
}

function WindFieldMap({
  points,
  center,
  selectedHour,
  selectedDate,
  forecastHour,
  lang
}: {
  points: HourlyActivityPoint[];
  center: ForecastResponse["selected_place"];
  selectedHour: number;
  selectedDate: string | null | undefined;
  forecastHour: number;
  lang: Lang;
}) {
  const text = copy(lang);
  if (!points.length) return null;
  const current = points.reduce(
    (closest, point) => (Math.abs(point.hour - selectedHour) < Math.abs(closest.hour - selectedHour) ? point : closest),
    points[0]
  );
  const calendar = windyCalendarParam(selectedDate, forecastHour);
  const windyUrl = center
    ? `https://embed.windy.com/embed2.html?lat=${center.latitude.toFixed(4)}&lon=${center.longitude.toFixed(4)}&detailLat=${center.latitude.toFixed(4)}&detailLon=${center.longitude.toFixed(4)}&width=760&height=620&zoom=10&level=surface&overlay=wind&product=ecmwf&menu=&message=true&marker=true&calendar=${calendar}&pressure=&type=map&location=coordinates&detail=true&metricWind=kt&metricTemp=%C2%B0C&radarRange=-1`
    : null;
  return (
    <div className="weather-map-panel">
      <div className="weather-curve-head">
        <span>{text.windMap}</span>
        <b>{formatCurveTime(current.hour)} · {compassLabel(current.wind_direction_deg)} · {(current.wind_gust_knots ?? current.wind_speed_knots ?? 0).toFixed(0)} kt</b>
      </div>
      {windyUrl ? (
        <iframe
          allowFullScreen
          key={windyUrl}
          loading="lazy"
          referrerPolicy="no-referrer-when-downgrade"
          src={windyUrl}
          title={text.windyTitle}
        />
      ) : null}
      <small>{text.windyNote}</small>
    </div>
  );
}

function WeatherVisualPanel({
  day,
  hourlyActivity,
  center,
  lang
}: {
  day: ForecastDay | null;
  hourlyActivity: HourlyActivityPoint[];
  center: ForecastResponse["selected_place"];
  lang: Lang;
}) {
  const text = copy(lang);
  const windows = day?.windows ?? [];
  const hourly = (day ? hourlyActivity.filter((point) => point.date === day.date) : []).sort((a, b) => a.hour - b.hour);
  const selected = day?.best_window ?? windows[0] ?? null;
  const defaultHour = representativeHour(selected) ?? hourly[0]?.hour ?? 0;
  const [activeHour, setActiveHour] = useState(defaultHour);
  useEffect(() => {
    setActiveHour(defaultHour);
  }, [day?.date, defaultHour]);
  if (!windows.length && !hourly.length) return null;
  const wavePoints = hourly
    .map((point) => ({ hour: point.hour, value: hourlyWave(point), label: point.time_window ?? "" }))
    .filter((point): point is WeatherSeriesPoint => point.value != null);
  const tideHeightPoints = hourly
    .map((point) => ({ hour: point.hour, value: numberOrNull(hourlyTideHeight(point)), label: point.tide_phase ?? "" }))
    .filter((point): point is WeatherSeriesPoint => point.value != null);
  const tideMovementPoints = hourly
    .map((point) => ({ hour: point.hour, value: numberOrNull(hourlyTideMovement(point)), label: point.tide_phase ?? "" }))
    .filter((point): point is WeatherSeriesPoint => point.value != null);
  const hasVerifiedTideHeight = tideHeightPoints.length >= Math.max(2, Math.floor(hourly.length * 0.5));
  const tidePoints = hasVerifiedTideHeight ? tideHeightPoints : tideMovementPoints;
  const tideLabel = hasVerifiedTideHeight ? text.tideHeight : text.tideMovement;
  const tideUnit = hasVerifiedTideHeight ? "m" : "m/h";
  const tideNote = hasVerifiedTideHeight ? undefined : text.tideMovementProxyNote;
  return (
    <section className="weather-visual-card">
      <div className="section-label">{text.weatherVisual}</div>
      <h3>{text.windTideWaves}</h3>
      <div className="weather-visual-grid">
        <WindFieldMap
          center={center}
          forecastHour={defaultHour}
          lang={lang}
          points={hourly}
          selectedDate={day?.date}
          selectedHour={activeHour}
        />
        <WeatherCurve
          label={tideLabel}
          unit={tideUnit}
          points={tidePoints}
          selectedHour={activeHour}
          onSelectHour={setActiveHour}
          note={tideNote}
        />
        {wavePoints.length > 0 ? (
          <WeatherCurve label={text.waveHeight} unit="m" points={wavePoints} selectedHour={activeHour} onSelectHour={setActiveHour} />
        ) : hourly.length > 0 ? (
          <div className="weather-curve-panel weather-wave-unavailable">
            <div className="weather-curve-head">
              <span>{text.waveHeight}</span>
              <b>—</b>
            </div>
            <p className="weather-wave-unavailable-note">{text.waveUnavailableNote}</p>
          </div>
        ) : null}
      </div>
    </section>
  );
}

function HeroScoreCard({ data, forecast, lang }: { data: ForecastResponse | null; forecast: ForecastResponse["forecast"] | undefined; lang: Lang }) {
  const text = copy(lang);
  const todayDay = todayForecastDay(forecast);
  const bestWindow = todayDay?.best_window ?? forecast?.hero.best_window ?? null;
  const summary = dailyScoreSummary(todayDay);
  const score = summary.weighted ?? selectedWindowScore(bestWindow) ?? forecast?.hero.score ?? null;
  const reasons = friendlyScoreReason(bestWindow, summary, lang);
  const label = recommendationLabel(score);
  const tone = scoreTone(label);
  return (
    <div className="hero-score">
      <span>{text.selectedPlace}</span>
      <b>{data?.selected_place?.display_name ?? text.waitingPlace}</b>
      <div className={`decision-badge ${tone}`}>{recommendationDisplay(label, lang)}</div>
      <div className="score-readout">
        <strong>{score ?? "--"}</strong>
        <div>
          <span>{text.todayScore}</span>
          <p>{scoreMeaning(score, lang)}</p>
        </div>
      </div>
      <small>{bestWindow ? `${displayWaterType(bestWindow.dominant_water_type, lang)} ${text.strongestNearby}` : forecast?.hero.headline ?? text.searchResultWaiting}</small>
      {reasons.length ? (
        <ul className="score-reasons">
          {reasons.map((reason) => (
            <li key={reason}>{reason}</li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

function UnsupportedState({ data, lang }: { data: ForecastResponse; lang: Lang }) {
  const text = copy(lang);
  return (
    <section className="unsupported">
      <span>{text.unsupported}</span>
      <h2>{lang === "zh" ? "当前预测仅支持海岸和潮汐钓鱼区域。" : "This forecast currently supports coastal and tidal fishing areas only."}</h2>
      <p>{data.plan.primary_action.text}</p>
    </section>
  );
}

export default function App() {
  const [query, setQuery] = useState(DEMO_QUERY);
  const [data, setData] = useState<ForecastResponse | null>(null);
  const [candidates, setCandidates] = useState<PlaceCandidate[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [lang, setLang] = useState<Lang>("en");
  const [theme, setTheme] = useState<Theme>("day");
  const text = copy(lang);

  async function runSearch(nextQuery = query) {
    setLoading(true);
    setError(null);
    setCandidates([]);
    try {
      const result = await searchForecast(nextQuery);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function runCandidateSearch(nextQuery = query) {
    const normalized = nextQuery.trim();
    if (!normalized) return;
    setLoading(true);
    setError(null);
    setCandidates([]);
    try {
      const result = await searchPlaces(normalized);
      if (result.results.length > 1) {
        setCandidates(result.results);
        return;
      }
      if (result.results.length === 1) {
        await chooseCandidate(result.results[0]);
        return;
      }
      setError(text.noPlaceFound);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function chooseCandidate(candidate: PlaceCandidate) {
    setLoading(true);
    setError(null);
    try {
      const result = await forecastPlace(candidate);
      setData(result);
      setQuery(candidate.short_name ?? candidate.display_name);
      setCandidates([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void runSearch(DEMO_QUERY);
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  useEffect(() => {
    const days = data?.forecast?.daily_forecast ?? [];
    if (!days.length) {
      setSelectedDate(null);
      return;
    }
    setSelectedDate((current) => {
      if (current && days.some((day) => day.date === current)) return current;
      return pickInitialDate(days, data?.forecast?.hero.best_window?.date ?? null);
    });
  }, [data?.query, data?.forecast?.daily_forecast.length]);

  function submit(event: FormEvent) {
    event.preventDefault();
    void runCandidateSearch();
  }

  const forecast = data?.forecast;
  const selectedDay = forecast?.daily_forecast.find((day) => day.date === selectedDate) ?? todayForecastDay(forecast);
  const bestWindow = selectedDay?.best_window ?? forecast?.hero.best_window ?? null;
  const structures = forecast?.structure_facilities ?? [];

  return (
    <main className={`lang-${lang} theme-${theme}`}>
      <header className="hero">
        <nav>
          <span className="brand-mark" aria-hidden="true">
            <svg viewBox="0 0 48 48" focusable="false">
              <path className="logo-coast" d="M11.8 19.3c2.8-4.9 8.1-8 14.6-8 3.2 0 6.2.8 8.7 2.5" />
              <path className="logo-fish-tail" d="M31.7 24.7 39.2 18.7v12z" />
              <path className="logo-fish-body" d="M8.7 24.7c5.4-6.8 16.1-6.8 23 0-6.9 6.8-17.6 6.8-23 0Z" />
              <circle className="logo-fish-eye" cx="16.4" cy="23" r="1.55" />
              <path className="logo-wave" d="M8.8 33.2c4.9 0 4.9-2.9 9.8-2.9s4.9 2.9 9.8 2.9 4.9-2.9 9.8-2.9" />
              <circle className="logo-sun" cx="36.6" cy="12.6" r="2.8" />
            </svg>
          </span>
          <span>{text.brand}</span>
          <div className="nav-actions">
            <button
              aria-label={theme === "night" ? text.switchToDay : text.switchToNight}
              className="theme-toggle"
              onClick={() => setTheme((current) => (current === "day" ? "night" : "day"))}
              type="button"
            >
              {theme === "night" ? text.themeToggleDay : text.themeToggleNight}
            </button>
            <button
              aria-label={lang === "zh" ? text.switchToEnglish : text.switchToChinese}
              className="language-toggle"
              onClick={() => setLang((current) => (current === "en" ? "zh" : "en"))}
              type="button"
            >
              {text.languageToggle}
            </button>
          </div>
        </nav>
        <div className="hero-grid">
          <div>
            <p className="eyebrow">{text.eyebrow}</p>
            <h1>{text.heroTitle}</h1>
            <p className="hero-copy">
              {text.heroCopy}
            </p>
            <form className="search-form" onSubmit={submit}>
              <input
                aria-label={text.searchPlaceholder}
                onChange={(event) => setQuery(event.target.value)}
                placeholder={text.searchPlaceholder}
                value={query}
              />
              <button disabled={loading}>{loading ? text.checkingButton : text.forecastButton}</button>
            </form>
            {candidates.length ? (
              <div className="candidate-menu">
                <span>{text.exactPlace}</span>
                {candidates.map((candidate) => (
                  <button key={candidate.id} onClick={() => void chooseCandidate(candidate)} type="button">
                    <b>{candidate.display_name}</b>
                    <small>{candidateMeta(candidate)}</small>
                  </button>
                ))}
              </div>
            ) : null}
            {error ? <p className="error">{error}</p> : null}
          </div>
          <HeroScoreCard data={data} forecast={forecast} lang={lang} />
        </div>
      </header>

      {data?.status === "unsupported_or_no_result" ? (
        <>
          <UnsupportedState data={data} lang={lang} />
          <StructureMap center={data.selected_place} lang={lang} structures={[]} unsupported={data} window={null} />
        </>
      ) : null}

      {data?.status === "ok" && forecast ? (
        <>
          <StructureMap center={data.selected_place} lang={lang} structures={structures} window={bestWindow} />
          <div className="dashboard">
            <div className="left-column">
              <FishingPlanCard data={data} lang={lang} onSelectDate={setSelectedDate} selectedDate={selectedDate} />
            </div>
            <div className="right-column">
              <WeatherVisualPanel
                center={data.selected_place}
                day={selectedDay ?? null}
                hourlyActivity={forecast.hourly_activity ?? []}
                lang={lang}
              />
            </div>
          </div>
        </>
      ) : null}
    </main>
  );
}
