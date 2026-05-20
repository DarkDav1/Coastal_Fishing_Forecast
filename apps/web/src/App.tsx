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
    fishPotential: "Fish potential",
    tripReality: "Trip reality",
    waterbodyClass: "Water type",
    waterTemp: "Water temp",
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
    historyForecast: "Recent history + forecast",
    dragDates: "Drag sideways to review each day’s average score",
    dateStripPeakLabel: "avg",
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
    windTideWaves: "Wind, Tide, Waves & Swell",
    windMap: "Wind map",
    windSpeed: "Wind speed",
    windyNote: "Live wind layer from Windy. Curves below use the same hourly data as the score.",
    tideHeight: "Tide height",
    tideMovement: "Tide movement",
    tideMovementProxyNote: "This curve shows model-estimated tide movement, not local tide-table height.",
    waveHeight: "Wave height",
    swellHeight: "Swell height",
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
    forecastButton: "查看鱼情",
    checkingButton: "分析中...",
    selectedPlace: "已选地点",
    waitingPlace: "等待预测",
    todayScore: "今日建议",
    fishPotential: "鱼情潜力",
    tripReality: "出行现实",
    waterbodyClass: "水域类型",
    waterTemp: "水温",
    searchResultWaiting: "搜索后会显示今日判断。",
    strongestNearby: "是今天附近更值得看的水域类型。",
    primaryMap: "主要地图",
    selectedMap: "已选地图",
    publicAccessTitle: "附近可到达的公共钓点",
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
    fishActivity24h: "全天鱼情曲线",
    historyForecast: "近期走势 + 预测",
    dragDates: "横向拖动查看每天的平均表现",
    dateStripPeakLabel: "平均",
    today: "今天",
    score: "评分",
    scoreLayers: "评分拆分",
    activity: "开口活跃",
    presence: "靠岸信号",
    trip: "出行条件",
    biteTiming: "开口时间",
    fishNearby: "鱼是否靠近",
    whyWindow: "全天情况",
    bestTime: "最佳时间",
    tide: "潮汐",
    comfort: "舒适度",
    pressure: "气压",
    firstMove: "今日建议",
    scoreFactors: "为什么是这个分",
    scoreFactorsGenerating: "正在生成说明…",
    scoreFactorsPositive: "加分项",
    scoreFactorsNegative: "扣分项",
    backup: "备选方案",
    weatherVisual: "风浪可视化",
    windTideWaves: "风、潮汐、浪与涌浪",
    windMap: "风场地图",
    windSpeed: "风速",
    windyNote: "风场来自 Windy；下方曲线使用同一组逐小时天气数据。",
    tideHeight: "潮高",
    tideMovement: "潮汐变化",
    tideMovementProxyNote: "这条曲线看的是潮水流动强弱，不是潮汐表里的潮位高度。",
    waveHeight: "浪高",
    swellHeight: "涌浪高度",
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

const WATERBODY_CLASS_LABELS_EN: Record<string, string> = {
  open_coast: "open coast",
  surf_coast: "surf coast",
  bay_coast: "bay coast",
  sheltered_estuary: "sheltered estuary",
  river_mouth: "river mouth",
  tidal_river: "tidal river",
  harbour_access: "harbour / access water",
  unsupported: "unsupported water"
};

const WATERBODY_CLASS_LABELS_ZH: Record<string, string> = {
  open_coast: "外海岸",
  surf_coast: "冲浪海岸",
  bay_coast: "内湾岸线",
  sheltered_estuary: "遮蔽河口 / 内湾",
  river_mouth: "河口",
  tidal_river: "潮汐河道",
  harbour_access: "港湾 / 入口水域",
  unsupported: "暂不支持水域"
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

function displayWaterbodyClass(value?: string | null, lang: Lang = "en") {
  if (!value) return lang === "zh" ? "自动判断中" : "classifying";
  const normalized = value.toLowerCase();
  if (lang === "zh") return WATERBODY_CLASS_LABELS_ZH[normalized] ?? value.replaceAll("_", " ");
  return WATERBODY_CLASS_LABELS_EN[normalized] ?? value.replaceAll("_", " ");
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
  const tripQuality = tripRealityScore(window);
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
  const tripQuality = tripRealityScore(window);
  if ((score != null && score < 40) || (tripQuality != null && tripQuality <= 10)) {
    if (lang === "zh") return "更好的备选：选择更有遮蔽的位置，或把这次出钓留到下一个稳定日。";
    return "Better backup: choose a more sheltered location, or save the trip for the next stable day.";
  }
  if (lang === "zh" && fallback) return "备选：如果第一个位置人多、关闭或没有动静，换到地图标注的礁石岸线。";
  return fallback ?? "";
}

function average(values: Array<number | null | undefined>) {
  const valid = numericValues(values);
  if (!valid.length) return null;
  return Math.round(valid.reduce((sum, value) => sum + value, 0) / valid.length);
}

function averageFloat(values: Array<number | null | undefined>) {
  const valid = numericValues(values);
  if (!valid.length) return null;
  return valid.reduce((sum, value) => sum + value, 0) / valid.length;
}

function numericValues(values: Array<number | null | undefined>) {
  return values.filter((value): value is number => typeof value === "number" && Number.isFinite(value));
}

function maxOrNull(values: Array<number | null | undefined>) {
  const valid = numericValues(values);
  return valid.length ? Math.max(...valid) : null;
}

function mostCommonString(values: Array<string | null | undefined>) {
  const counts = new Map<string, number>();
  for (const value of values) {
    if (!value) continue;
    counts.set(value, (counts.get(value) ?? 0) + 1);
  }
  return [...counts.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] ?? null;
}

function strongestSafetyFlag(values: Array<string | null | undefined>) {
  const rank: Record<string, number> = { none: 0, low: 0, moderate: 1, elevated: 2, hazardous: 3 };
  let strongest: string | null = null;
  for (const value of values) {
    if (!value) continue;
    if (strongest == null || (rank[value] ?? 0) > (rank[strongest] ?? 0)) strongest = value;
  }
  return strongest;
}

function applySafetyRealityCap(score: number | null, safetyFlag?: string | null) {
  if (score == null) return null;
  if (safetyFlag === "hazardous") return Math.min(score, 35);
  if (safetyFlag === "elevated") return Math.min(score, 55);
  if (safetyFlag === "moderate") return Math.min(score, 70);
  return score;
}

function tripRealityScore(
  value?: {
    comfort_score?: number | null;
    safety_flag?: string | null;
    trip_quality_score?: number | null;
    score?: number | null;
  } | null
) {
  if (!value) return null;
  const base = numberOrNull(value.comfort_score) ?? numberOrNull(value.trip_quality_score) ?? numberOrNull(value.score);
  return applySafetyRealityCap(base, value.safety_flag);
}

function todayForecastDay(forecast: ForecastResponse["forecast"] | undefined) {
  const today = todayIsoDate();
  return forecast?.daily_forecast.find((day) => day.date === today) ?? forecast?.daily_forecast[0] ?? null;
}

function dailyScoreSummary(day?: { best_window: WindowCard | null; windows: WindowCard[] } | null) {
  const windows = day?.windows ?? [];
  const activity = average(windows.map((window) => window.activity_score ?? window.score));
  const presence = average(windows.map((window) => window.presence_score ?? window.score));
  const safetyFlag = strongestSafetyFlag(windows.map((window) => window.safety_flag));
  const rawTripQuality = average(windows.map(tripRealityScore));
  const tripQuality = applySafetyRealityCap(rawTripQuality, safetyFlag);
  const fishIndex = average(
    windows.map((window) => window.fish_outlook_score ?? (window.activity_score != null && window.presence_score != null
      ? Math.round(window.activity_score * 0.55 + window.presence_score * 0.45)
      : window.score))
  );
  const weighted =
    fishIndex == null || tripQuality == null
      ? selectedWindowScore(day?.best_window ?? null)
      : Math.round(fishIndex * 0.62 + tripQuality * 0.38);
  return { activity, presence, tripQuality, fishIndex, weighted, safetyFlag };
}

function dayScore(day?: { best_window: WindowCard | null; windows: WindowCard[] } | null) {
  return dailyScoreSummary(day).weighted;
}

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
  const score = dayScore(day);
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

function cleanScoreFactorText(line: string) {
  return line
    .replace(/[；;]/g, ".")
    .replace(/\s*\.\s*\./g, ".")
    .replace(/\.(?=\S)/g, ". ")
    .replace(/\s+/g, " ")
    .trim();
}

function polishChineseCopy(line: string, lang: Lang) {
  const cleaned = cleanScoreFactorText(line);
  if (lang !== "zh") return cleaned;

  const replacements: Array<[RegExp, string]> = [
    [/潮差还可以[，,]\s*涨落潮的节奏比较看得出来。?/g, "潮差具备一定幅度，涨落潮节奏较明确。"],
    [/涨落潮的节奏比较看得出来/g, "涨落潮节奏较明确"],
    [/比较看得出来/g, "较明确"],
    [/水体在中等程度上流动/g, "潮水具备一定流动性"],
    [/不是完全死水/g, "水体并非完全停滞"],
    [/水动不起来/g, "水流推动不足"],
    [/鱼口容易散/g, "鱼口稳定性较低"],
    [/天气还行/g, "天气稳定"],
    [/体感还可以/g, "体感条件较好"],
    [/还可以/g, "具备一定条件"],
    [/还行/g, "基本可控"],
    [/好处理/g, "较平稳"],
    [/不算稳/g, "稳定性一般"],
    [/打折/g, "受到削弱"],
    [/拖低/g, "降低"],
    [/刚经历过一段偏暖天气，现在明显转冷/g, "近期由偏暖转为明显降温"],
    [/近期暖段/g, "近期偏暖阶段"],
    [/存在感/g, "影响"],
  ];

  return replacements.reduce((current, [pattern, replacement]) => current.replace(pattern, replacement), cleaned);
}

function translateWeatherChangeNote(note: string, lang: Lang) {
  const cleaned = note.trim().replace(/[.。]+$/, "");
  if (lang !== "zh") return cleaned;
  const translations: Record<string, string> = {
    "Air temperature has dropped sharply from the recent warm period": "近期由偏暖转为明显降温",
    "Air temperature has fallen noticeably over the last day": "过去一天明显降温",
    "Pressure has moved quickly over the last day": "过去一天气压变化较快",
    "Pressure is changing quickly in the current window": "当前时段气压变化较快，稳定性下降",
    "Wind direction has shifted strongly in the last half day": "过去半天风向变化明显",
    "Heavy recent rain may have disrupted inshore water conditions": "近期雨量偏大，近岸水色和盐度可能受影响",
    "Recent multi-day rain may still be affecting the water": "近期连续降雨可能仍在影响近岸水况",
    "Recent strong gusts may have unsettled exposed water": "近期阵风偏强，外露水域稳定性较差",
    "The sea state has changed quickly compared with the previous day": "海况变化较快，单个窗口的参考价值有限",
  };
  return translations[cleaned] ?? cleaned;
}

function dayConditionStats(day?: { windows: WindowCard[] } | null) {
  const windows = day?.windows ?? [];
  const windAvg = averageFloat(windows.map((window) => window.conditions.wind.speed_knots));
  const gustMax = Math.max(0, ...windows.map((window) => window.conditions.wind.gust_knots ?? window.conditions.wind.recent_max_12h ?? 0));
  const waveAvg = averageFloat(windows.map(windowWaveHeight));
  const waveMax = maxOrNull(windows.map(windowWaveHeight));
  const swellMax = maxOrNull(windows.map(windowSwellHeight));
  const rainTotal = windows.reduce((sum, window) => sum + (window.conditions.air?.rain_mm ?? window.conditions.air?.precipitation_mm ?? 0), 0);
  const temperatureAvg = averageFloat(windows.map((window) => window.conditions.air?.temperature_c));
  const waterTempAvg = averageFloat(windows.map((window) => window.conditions.marine?.sea_surface_temperature_c));
  const pressureAvg = averageFloat(windows.map((window) => window.conditions.pressure_hpa));
  const shockMax = Math.max(0, ...windows.map((window) => window.conditions.weather_trend?.shock_score ?? 0));
  const tideMovementMax = Math.max(0, ...windows.map((window) => Math.abs(window.conditions.tide.movement_rate_m_per_hour ?? 0)));
  const tideRangeAvg = averageFloat(windows.map((window) => window.conditions.tide.range_m));
  const tidePhases = Array.from(new Set(windows.map((window) => window.conditions.tide.phase).filter(Boolean)));
  const hasEstimatedWave = windows.some((window) => window.conditions.swell.source === "protected_estuary_estimate");
  const hasMissingWave = windows.some((window) => window.conditions.swell.wave_height_m == null);
  const windowScores = windows.map((window) => window.score).filter((score) => Number.isFinite(score));
  const minWindowScore = windowScores.length ? Math.min(...windowScores) : null;
  const slackWindows = windows.filter((window) => window.conditions.tide.stage === "slack").length;
  const waterTempSignal = mostCommonString(windows.map((window) => window.conditions.marine?.water_temperature_signal));
  const waterTempTrend = mostCommonString(windows.map((window) => window.conditions.marine?.water_temperature_trend));
  const temperatureConfidence = mostCommonString(windows.map((window) => window.conditions.marine?.temperature_confidence));
  const waterbodyClass = mostCommonString(windows.map((window) => window.waterbody_class ?? window.conditions.classification?.waterbody_class));
  const fishProfile = mostCommonString(windows.map((window) => window.fish_profile ?? window.conditions.fish_profile));
  const negativeRules = windows.flatMap((window) =>
    (window.conditions.formula?.rules ?? [])
      .filter((rule) => rule.score_delta < 0)
      .map((rule) => ({ id: rule.id, label: rule.label, score_delta: rule.score_delta }))
  );
  return {
    gustMax,
    hasEstimatedWave,
    hasMissingWave,
    minWindowScore: Number.isFinite(minWindowScore) ? minWindowScore : null,
    negativeRules,
    pressureAvg,
    rainTotal,
    shockMax,
    slackWindows,
    swellMax,
    temperatureAvg,
    tideMovementMax,
    tidePhases,
    tideRangeAvg,
    waveAvg,
    waveMax,
    waterbodyClass,
    waterTempAvg,
    waterTempSignal,
    waterTempTrend,
    temperatureConfidence,
    fishProfile,
    windAvg
  };
}

function fishIndexMeaning(summary: ReturnType<typeof dailyScoreSummary>, lang: Lang = "en") {
  const fish = summary.fishIndex;
  if (fish == null) return lang === "zh" ? "鱼情指数还不足以判断全天强弱。" : "Not enough fish-signal data to read the day yet.";
  if (lang === "zh") {
    if (fish >= 70) return "鱼情指数综合开口活跃度和靠岸可能性；今天整体信号较强。";
    if (fish >= 55) return "鱼情指数综合开口活跃度和靠岸可能性；今天存在机会，但稳定性一般。";
    if (fish >= 40) return "鱼情指数综合开口活跃度和靠岸可能性；今天整体一般，主要依赖短窗口。";
    return "鱼情指数综合开口活跃度和靠岸可能性；今天信号偏弱。";
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

type ScoreRule = { id: string; label: string; score_delta: number };

function negativeRuleReason(rule: ScoreRule, lang: Lang = "en") {
  const id = rule.id.toLowerCase();
  if (lang === "zh") {
    if (id.includes("harsh_midday")) return "白天强光会降低鱼口稳定性，机会更依赖清晨或傍晚窗口。";
    if (id.includes("recent_weather_shock")) return "近期天气变化较大，近岸鱼情稳定性不足。";
    if (id.includes("slack_tide")) return "部分时段接近缓水，水流推动不足。";
    if (id.includes("weak_tide") || id.includes("dead_water")) return "潮水推动偏弱，诱鱼和换水信号不足。";
    if (id.includes("gust")) return "阵风偏强，抛投和站稳都会受影响。";
    if (id.includes("strong_wind")) return "风力偏强，控线难度和体感压力上升。";
    if (id.includes("rain")) return "降雨会影响近岸水色、水质和稳定性。";
    if (id.includes("cold")) return "气温或水温偏冷，鱼类活跃度可能下降。";
    if (id.includes("big_wave") || id.includes("wave")) return "浪况偏大，近岸操作难度和安全压力上升。";
    return `${rule.label} 会降低这个时段的表现。`;
  }
  if (id.includes("harsh_midday")) return "Bright daylight pulls down the weaker window, so the bite depends more on short morning or evening timing.";
  if (id.includes("recent_weather_shock")) return "Recent weather shock is still weighing on near-shore stability.";
  if (id.includes("slack_tide")) return "Some windows sit near slack water, reducing movement support.";
  if (id.includes("weak_tide") || id.includes("dead_water")) return "Weak tide movement gives less water exchange to spark activity.";
  if (id.includes("gust")) return "Sharp gusts reduce casting comfort and footing confidence.";
  if (id.includes("strong_wind")) return "Stronger wind works against line control and comfort.";
  if (id.includes("rain")) return "Rain disruption can reduce near-shore water quality and stability.";
  if (id.includes("cold")) return "Cold air or water reduces the activity signal.";
  if (id.includes("big_wave") || id.includes("wave")) return "Larger waves cut into comfort and safety margin near shore.";
  return `${rule.label} pulls down this window.`;
}

function negativeRuleReasons(rules: ScoreRule[], lang: Lang = "en") {
  const sorted = [...rules].sort((a, b) => a.score_delta - b.score_delta);
  const reasons: string[] = [];
  for (const rule of sorted) {
    const reason = negativeRuleReason(rule, lang);
    if (!reasons.includes(reason)) reasons.push(reason);
    if (reasons.length >= 3) break;
  }
  return reasons;
}

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

  negative.push(...negativeRuleReasons(stats.negativeRules, lang));
  if (stats.minWindowScore != null && stats.minWindowScore < 45) {
    negative.push(
      lang === "zh"
        ? "当天机会主要集中在少数短窗口，其他时段整体表现较弱。"
        : "Opportunity is concentrated in short windows. Weaker periods drag down the day."
    );
  }

  if (stats.tideMovementMax >= 0.18) {
    positive.push(
      lang === "zh"
        ? "潮水交换较明显，有利于近岸水流和食物移动。"
        : "Tide movement is clearly felt—water exchanges well near shore."
    );
  } else if (stats.tideMovementMax >= 0.08) {
    positive.push(
      lang === "zh"
        ? "潮水具备一定流动性，水体并非完全停滞。"
        : "There is moderate tidal flow—enough water movement to notice."
    );
  } else {
    negative.push(
      lang === "zh"
        ? "潮水整体偏弱，水流推动不足，鱼口更容易分散。"
        : "Tide flow is weak, so less water movement to spark activity."
    );
  }

  if (stats.tideRangeAvg != null && stats.tideRangeAvg >= 0.65) {
    positive.push(
      lang === "zh"
        ? "潮差具备一定幅度，涨落潮节奏较明确。"
        : "Tidal range is reasonably wide, so highs and lows matter more."
    );
  }
  if (stats.slackWindows > 0) {
    negative.push(
      lang === "zh"
        ? "部分时段接近缓水，水流推动不足。"
        : "Some windows sit near slack water, which reduces water movement support."
    );
  }

  if (stats.waterTempAvg == null || stats.temperatureConfidence === "low") {
    negative.push(
      lang === "zh"
        ? "水温或水温趋势数据不足，鱼情判断会更保守。"
        : "Water temperature or its trend is incomplete, so the fish read is more cautious."
    );
  } else if (stats.waterTempSignal === "cold") {
    negative.push(
      lang === "zh"
        ? "水温明显偏冷，不能只因为潮水不错就给高鱼情。"
        : "Cold water drags down fish activity even if the tide window looks useful."
    );
  } else if (stats.waterTempSignal === "cool") {
    negative.push(
      lang === "zh"
        ? "水温偏凉，鱼情更依赖短时间强水流。"
        : "Cool water means the fish signal depends more on short movement windows."
    );
  } else if (stats.waterTempSignal === "hot") {
    negative.push(
      lang === "zh"
        ? "水温偏热，浅水鱼情稳定性会下降。"
        : "Hot water can reduce shallow-water stability."
    );
  } else if (stats.waterTempSignal === "optimal" && stats.waterTempTrend === "stable") {
    positive.push(
      lang === "zh"
        ? "水温处在目标鱼可接受区间，而且近期变化稳定。"
        : "Water temperature is in range for the target profile and recently stable."
    );
  }

  if (stats.waterTempTrend === "cooling_fast") {
    negative.push(
      lang === "zh"
        ? "水温快速下降，鱼情稳定性受到压制。"
        : "A fast water-temperature drop suppresses fish stability."
    );
  } else if (stats.waterTempTrend === "warming_fast") {
    negative.push(
      lang === "zh"
        ? "水温快速升高，浅水鱼情需要保守判断。"
        : "A fast water-temperature rise makes the shallow-water read less stable."
    );
  }

  const cold = stats.temperatureAvg != null && stats.temperatureAvg < 9;
  const windy = stats.windAvg != null && stats.windAvg > 16;
  const gusty = stats.gustMax > 24;
  const rainy = stats.rainTotal >= 2;
  const volatile = stats.shockMax >= 2;
  if (cold) {
    negative.push(lang === "zh" ? "气温偏低，体感偏冷。" : "Cool air temperatures make it feel chilly.");
  }
  if (windy) {
    negative.push(lang === "zh" ? "风力偏大，控线、抛投和站位难度上升。" : "Steady wind is on the stronger side for casting and footing.");
  }
  if (gusty) {
    negative.push(lang === "zh" ? "阵风偏强，抛投和站稳需要更加谨慎。" : "Gusts are sharp enough to affect casting and balance.");
  }
  if (rainy) {
    negative.push(lang === "zh" ? "当天降雨较明显，近岸水况可能受影响。" : "Meaningful rain across the day’s windows.");
  }
  if (volatile) {
    negative.push(lang === "zh" ? "近期天气变化偏大，鱼情稳定性下降。" : "Recent weather has been unstable.");
  }

  if (!cold && !windy && !gusty && !rainy && !volatile) {
    positive.push(
      lang === "zh"
        ? "天气整体较温和，未见明显低温、大风、大雨或突变。"
        : "Weather is relatively mild—no extreme cold, heavy rain, or wild swings."
    );
  }

  if (stats.hasMissingWave) {
    negative.push(
      lang === "zh"
        ? "缺少可靠浪况数据，海面情况需现场确认。"
        : "Real wave data is missing, so sea-state confidence is lower."
    );
  } else if (stats.hasEstimatedWave) {
    negative.push(
      lang === "zh"
        ? "浪高来自内湾估算，外露位置仍需谨慎判断。"
        : "Wave height is a protected-estuary estimate, not a direct marine-model wave value."
    );
  }

  if (stats.waveMax == null) {
    negative.push(
      lang === "zh"
        ? "浪况数据不足，海面情况需现场确认。"
        : "Wave data is unavailable, so sea-state confidence is lower."
    );
  } else if (stats.waveMax >= 2) {
    negative.push(
      lang === "zh"
        ? "浪况偏大，近岸操作难度和安全压力上升。"
        : "Seas are fairly rough—comfort and safety margin drop near shore."
    );
  } else if (stats.waveMax >= 1.2) {
    negative.push(
      lang === "zh"
        ? "浪况中等偏高，遮蔽位置更适合执行。"
        : "Waves run moderately high—sheltered spots are easier."
    );
  } else {
    positive.push(
      lang === "zh"
        ? "浪况不大，海面整体较平稳。"
        : "Waves stay modest—the sea state is unlikely to be the main blocker."
    );
  }

  if (stats.swellMax != null && stats.swellMax >= 2) {
    negative.push(
      lang === "zh"
        ? "涌浪偏大，即使本地浪高不高，外露水域的出行品质也会下降。"
        : "Swell is large enough to lower trip quality on exposed water even if local wave height looks modest."
    );
  } else if (stats.swellMax != null && stats.swellMax >= 1.2) {
    negative.push(
      lang === "zh"
        ? "涌浪有存在感，外露海岸和礁石位置需要降低执行预期。"
        : "Swell is noticeable, so exposed beaches and rocks need lower execution expectations."
    );
  } else if (stats.swellMax != null && !stats.hasMissingWave) {
    positive.push(
      lang === "zh"
        ? "涌浪不大，对今天行程品质的压力有限。"
        : "Swell stays modest, so it adds little trip-quality pressure."
    );
  }

  const trendNotes = firstWeatherChangeNotes(day, 3);
  if (trendNotes.length > 0) {
    const notes = trendNotes.map((note) => translateWeatherChangeNote(cleanScoreFactorText(note), lang));
    const line =
      lang === "zh"
        ? `预报趋势：${notes.join("。")}。`
        : `Forecast trend: ${notes.join(". ")}.`;
    if (volatile || stats.shockMax >= 1.5 || factorLooksChallenging(line)) {
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

function factorLooksChallenging(line: string) {
  const text = line.toLowerCase();
  if (text.includes("no extreme") || text.includes("没有极端")) return false;
  if (
    text.includes("水体并非完全停滞") ||
    text.includes("天气整体较温和") ||
    text.includes("没有明显低温")
  ) {
    return false;
  }
  return [
    "not a strong",
    "only ",
    "limited",
    "short try",
    "committed session",
    "drops to",
    "uneven",
    "weak",
    "slack",
    "reduces",
    "lower",
    "missing",
    "estimate",
    "not a direct",
    "dropped",
    "fallen",
    "shifted",
    "unstable",
    "rough",
    "gust",
    "rain",
    "cold",
    "偏低",
    "只有",
    "不算",
    "不是",
    "短试",
    "低到",
    "不均匀",
    "偏弱",
    "缓水",
    "打折",
    "缺失",
    "估算",
    "突变",
    "下降",
    "波动",
    "偏大",
  ].some((marker) => text.includes(marker));
}

function factorIsScoreTautology(line: string) {
  const text = line.toLowerCase();
  return [
    "all-day score is",
    "fish index is only",
    "trip quality is only",
    "全天综合分只有",
    "鱼情指数只有",
    "行程质量只有",
  ].some((marker) => text.includes(marker));
}

function factorLooksHelpful(line: string) {
  const text = line.toLowerCase();
  return [
    "clearly felt",
    "moderate tidal",
    "reasonably wide",
    "mild",
    "no extreme",
    "modest",
    "unlikely to be the main blocker",
    "活跃",
    "一定流动",
    "水体并非完全停滞",
    "潮差",
    "温和",
    "没有极端",
    "浪不大",
    "较平稳",
  ].some((marker) => text.includes(marker));
}

function normalizeScoreFactors(blocks: ScoreFactorsBlocks, lang: Lang = "en"): ScoreFactorsBlocks {
  const positive: string[] = [];
  const negative: string[] = [];
  const addUnique = (target: string[], line: string) => {
    const trimmed = polishChineseCopy(line, lang);
    if (trimmed && !target.includes(trimmed)) target.push(trimmed);
  };

  for (const line of blocks.positive) {
    const polished = polishChineseCopy(line, lang);
    if (factorIsScoreTautology(polished)) continue;
    if (factorLooksChallenging(polished)) {
      addUnique(negative, polished);
    } else {
      addUnique(positive, polished);
    }
  }
  for (const line of blocks.negative) {
    const polished = polishChineseCopy(line, lang);
    if (factorIsScoreTautology(polished)) continue;
    if (!factorLooksChallenging(polished) && factorLooksHelpful(polished)) {
      addUnique(positive, polished);
    } else {
      addUnique(negative, polished);
    }
  }
  return { positive, negative, summary: blocks.summary ? polishChineseCopy(blocks.summary, lang) : undefined };
}

function mergeScoreFactors(
  model: ScoreFactorsBlocks | null,
  fallback: ScoreFactorsBlocks | null,
  lang: Lang = "en"
): ScoreFactorsBlocks | null {
  if (!model) return fallback ? normalizeScoreFactors(fallback, lang) : null;
  if (!fallback) return normalizeScoreFactors(model, lang);
  const merge = (primary: string[], secondary: string[]) =>
    Array.from(new Set([...primary, ...secondary].map((s) => s.trim()).filter(Boolean)));
  return normalizeScoreFactors({
    positive: merge(model.positive, fallback.positive),
    negative: merge(model.negative, fallback.negative),
    summary: model.summary ?? fallback.summary
  }, lang);
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
  const wave = windowWaveHeight(window);
  const swell = numberOrNull(condition.swell.height_m);
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
              : tags.has("big_wave") || tags.has("rough") || (wave != null && wave >= 2)
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
      wave == null
        ? "🌊 浪况：数据不足，现场确认"
        : wave >= 3
        ? "🌊 浪况：浪很大，避开外露水域"
        : wave >= 2
          ? "🌊 浪况：浪偏大，选择有遮蔽处"
          : wave >= 1.2
            ? "🌊 浪况：中等偏大"
            : "🌊 浪况：不大";
    const safetyProblems = [
      (swell != null && swell >= 2) || (wave != null && wave >= 2.5) ? "外露礁石和沙滩需要谨慎" : null,
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
            : tags.has("big_wave") || tags.has("rough") || (wave != null && wave >= 2)
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
    wave == null
      ? "🌊 Waves: data missing, check locally"
      : wave >= 3
      ? "🌊 Waves: very large, avoid exposure"
      : wave >= 2
        ? "🌊 Waves: large, choose shelter"
        : wave >= 1.2
          ? "🌊 Waves: moderate to large"
          : "🌊 Waves: not large";
  const safetyProblems = [
    (swell != null && swell >= 2) || (wave != null && wave >= 2.5) ? "exposed rocks and beaches need caution" : null,
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
  const seaHeight = Math.max(windowWaveHeight(window) ?? 0, (windowSwellHeight(window) ?? 0) * 0.85);
  const hasSeaData = windowWaveHeight(window) != null || windowSwellHeight(window) != null;
  if (lang === "zh") {
    if (!hasSeaData) return "浪况数据不足";
    if (seaHeight <= 0.3) return "水面平静";
    if (seaHeight <= 0.8) return "可钓";
    return "水况偏粗";
  }
  if (!hasSeaData) return "wave data missing";
  if (seaHeight <= 0.3) return "calm";
  if (seaHeight <= 0.8) return "fishable";
  return "rougher";
}

function waterTemperatureNote(stats: ReturnType<typeof dayConditionStats>, lang: Lang = "en") {
  const signal = stats.waterTempSignal;
  const trend = stats.waterTempTrend;
  if (stats.waterTempAvg == null || !signal || signal === "unknown") {
    return lang === "zh" ? "水温数据不足，鱼情置信度会降低。" : "Water temperature is incomplete, so fish confidence is lower.";
  }
  if (lang === "zh") {
    if (signal === "cold") return "水温明显偏冷，会压低鱼类活跃度。";
    if (signal === "cool") return "水温偏凉，机会更依赖强水流和好时段。";
    if (signal === "hot") return "水温偏热，浅水鱼情可能受压。";
    if (trend === "cooling_fast") return "水温快速下降，鱼情稳定性下降。";
    if (trend === "warming_fast") return "水温升得较快，需要更保守看待。";
    if (signal === "optimal" && trend === "stable") return "水温处在合适区间且变化稳定。";
    return "水温处于可参考范围。";
  }
  if (signal === "cold") return "Water is cold for the target profile and drags down activity.";
  if (signal === "cool") return "Water is cool, so the day needs stronger movement and timing.";
  if (signal === "hot") return "Water is hot enough to pressure shallow fish activity.";
  if (trend === "cooling_fast") return "Water temperature is dropping quickly, reducing stability.";
  if (trend === "warming_fast") return "Water temperature is rising quickly, so confidence is more cautious.";
  if (signal === "optimal" && trend === "stable") return "Water temperature is in range and stable.";
  return "Water temperature is usable but not a standalone reason to score high.";
}

function DayOverviewPanel({ day, lang }: { day: { best_window: WindowCard | null; windows: WindowCard[] } | null | undefined; lang: Lang }) {
  if (!day?.windows.length) return null;
  const text = copy(lang);
  const summary = dailyScoreSummary(day);
  const stats = dayConditionStats(day);
  const tideLabel =
    stats.tidePhases.length > 1
      ? (lang === "zh" ? "潮相变化" : "mixed tide")
      : displayWaterType(stats.tidePhases[0], lang);
  const tideNote =
    stats.tideMovementMax >= 0.18
      ? (lang === "zh" ? "全天水流较明显" : "clear water movement during the day")
      : stats.tideMovementMax >= 0.08
        ? (lang === "zh" ? "水流中等，需结合全天条件判断" : "moderate movement; do not rely on time alone")
        : (lang === "zh" ? "水流偏弱，鱼口稳定性较低" : "weaker movement can make fish activity patchy");
  const weatherProblems = [
    stats.windAvg != null && stats.windAvg > 16 ? (lang === "zh" ? "平均风偏强" : "windy") : null,
    stats.gustMax > 24 ? (lang === "zh" ? "阵风偏强" : "strong gusts") : null,
    stats.rainTotal >= 2 ? (lang === "zh" ? "有雨" : "rain") : null,
    stats.temperatureAvg != null && stats.temperatureAvg < 9 ? (lang === "zh" ? "偏冷" : "cold") : null,
    stats.shockMax >= 2 ? (lang === "zh" ? "近期天气变化" : "recent weather change") : null
  ].filter(Boolean);
  const marineProblems = [
    stats.swellMax != null && stats.swellMax >= 2 ? (lang === "zh" ? "涌浪偏大" : "larger swell") : null,
    stats.waveMax == null ? (lang === "zh" ? "本地浪高数据不足" : "local wave data missing") : null,
    stats.waveMax != null && stats.waveMax >= 2 ? (lang === "zh" ? "外露水域浪偏大" : "rougher exposed water") : null,
    stats.gustMax >= 30 ? (lang === "zh" ? "强阵风影响站稳和抛投" : "gusts can affect footing and casting") : null
  ].filter(Boolean);
  const marineValue = [
    stats.waveMax == null
      ? (lang === "zh" ? "本地浪高不足" : "local wave missing")
      : `${stats.waveMax.toFixed(2)} m ${lang === "zh" ? "最高浪高" : "max waves"}`,
    stats.swellMax != null ? `${stats.swellMax.toFixed(2)} m ${lang === "zh" ? "涌浪" : "swell"}` : null,
  ].filter(Boolean).join(" · ");
  const rows = [
    {
      icon: "🎣",
      label: lang === "zh" ? "鱼情整体" : "Fish outlook",
      value: `${summary.fishIndex ?? "--"} ${lang === "zh" ? "鱼情" : "fish index"}`,
      note: fishIndexMeaning(summary, lang)
    },
    {
      icon: "🌊",
      label: lang === "zh" ? "水流/潮水" : "Water movement",
      value: tideLabel,
      note: tideNote
    },
    {
      icon: "🌡️",
      label: text.waterTemp,
      value:
        stats.waterTempAvg == null
          ? (lang === "zh" ? "数据不足" : "data missing")
          : `${stats.waterTempAvg.toFixed(1)}°C`,
      note: waterTemperatureNote(stats, lang)
    },
    {
      icon: "🍃",
      label: lang === "zh" ? "天气体感" : "Weather comfort",
      value: `${stats.windAvg?.toFixed(1) ?? "--"} kt${stats.temperatureAvg != null ? ` · ${stats.temperatureAvg.toFixed(0)}°C` : ""}`,
      note: weatherProblems.length
        ? (lang === "zh" ? weatherProblems.slice(0, 2).join("、") : weatherProblems.slice(0, 2).join(" and "))
        : (lang === "zh" ? "体感条件较好" : "comfortable overall")
    },
    {
      icon: "⚠️",
      label: lang === "zh" ? "浪况/安全" : "Waves + safety",
      value: marineValue,
      note: marineProblems.length
        ? (lang === "zh" ? marineProblems[0] : marineProblems[0])
        : (lang === "zh" ? "未见明显安全压力" : "no obvious broad risk")
    }
  ];
  const shortRules = [
    summary.weighted == null
      ? (lang === "zh" ? "等待评分" : "Waiting for score")
      : summary.weighted >= 55
        ? (lang === "zh" ? "全天可钓" : "Fishable day")
        : summary.weighted >= 40
          ? (lang === "zh" ? "整体一般" : "Mixed day")
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
        : (lang === "zh" ? "天气稳定" : "Manageable weather"),
    stats.waterTempSignal === "cold" || stats.waterTempTrend === "cooling_fast"
      ? (lang === "zh" ? "水温拖后腿" : "Water temp drag")
      : stats.waterTempSignal === "optimal" && stats.waterTempTrend === "stable"
        ? (lang === "zh" ? "水温稳定" : "Stable water temp")
        : `${text.waterbodyClass}: ${displayWaterbodyClass(stats.waterbodyClass, lang)}`,
    stats.swellMax != null && stats.swellMax >= 2
      ? (lang === "zh" ? "涌浪偏大" : "Large swell")
      : stats.waveMax == null
        ? (lang === "zh" ? "浪况待确认" : "Wave data missing")
      : stats.waveMax >= 2
        ? (lang === "zh" ? "避开外露水域" : "Avoid exposed water")
        : (lang === "zh" ? "浪不大" : "Waves not large")
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

  const scoreFactorsDisplay = mergeScoreFactors(scoreFactorsLlm, scoreFactorsFallback, lang);

  return (
    <section className="plan-card">
      <div className="plan-head">
        <span className={`recommendation ${tone}`}>{recommendationDisplay(selectedLabel, lang)}</span>
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
                  <p className="score-factor-empty">
                    {lang === "zh"
                      ? "没有明显硬伤，但仍要按当天整体分数控制预期。"
                      : "No severe safety blocker, but still manage expectations around the score and window."}
                  </p>
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
const CURVE_LEFT = 112;
const CURVE_RIGHT = 918;
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

function curveTooltipLeftPercent(x: number) {
  return Math.max(12, Math.min(88, (x / CURVE_VIEWBOX_WIDTH) * 100));
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
  return numberOrNull(window.conditions.swell.wave_height_m);
}

function windowSwellHeight(window: WindowCard) {
  return numberOrNull(window.conditions.swell.height_m);
}

function hourlyRain(point: HourlyActivityPoint) {
  return point.rain_mm ?? point.precipitation_mm ?? 0;
}

function hourlyWindSpeed(point: HourlyActivityPoint) {
  return point.wind_speed_knots ?? null;
}

function hourlyWave(point: HourlyActivityPoint) {
  return point.wave_height_m ?? null;
}

function hourlySwell(point: HourlyActivityPoint) {
  return point.swell_height_m ?? null;
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
      tripQualityScore: tripRealityScore(point),
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
      tripQualityScore: tripRealityScore(window),
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
              <b>{dayScore(day) ?? "--"}</b>
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
        <div className="curve-tooltip" style={{ left: `${curveTooltipLeftPercent(activePoint.x)}%` }}>
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

type WeatherAxis = {
  min: number;
  max: number;
  ticks: number[];
  decimals: number;
};

function cleanAxisValue(value: number) {
  return Math.abs(value) < 0.000001 ? 0 : Number(value.toFixed(6));
}

function niceAxisStep(rawStep: number) {
  if (!Number.isFinite(rawStep) || rawStep <= 0) return 1;
  const magnitude = 10 ** Math.floor(Math.log10(rawStep));
  const normalized = rawStep / magnitude;
  if (normalized <= 1) return magnitude;
  if (normalized <= 2) return 2 * magnitude;
  if (normalized <= 2.5) return 2.5 * magnitude;
  if (normalized <= 5) return 5 * magnitude;
  return 10 * magnitude;
}

function axisDecimalsForStep(step: number, unit: string) {
  if (unit === "mm") return step < 1 ? 1 : 0;
  if (unit === "m" || unit === "m/h") return step < 1 ? 2 : 1;
  return 0;
}

function formatAxisTick(value: number, decimals: number) {
  const fixed = cleanAxisValue(value).toFixed(decimals);
  if (!fixed.includes(".")) return fixed;
  return fixed.replace(/(\.\d*?[1-9])0+$/, "$1").replace(/\.0+$/, "");
}

function buildWeatherAxis(points: WeatherSeriesPoint[], unit: string, allowNegative = false): WeatherAxis {
  const values = points.map((point) => point.value).filter((value) => Number.isFinite(value));
  const rawMin = Math.min(...values);
  const rawMax = Math.max(...values);
  const dataSpan = Math.max(0.01, rawMax - rawMin);
  let min = 0;
  let max = Math.max(rawMax * 1.15, unit === "m/h" ? 0.05 : unit === "m" ? 0.1 : 1);

  if (allowNegative && rawMin < 0) {
    const padding = Math.max(dataSpan * 0.08, 0.02);
    min = rawMin - padding;
    max = rawMax + padding;
  }

  if (max <= min) {
    max = min + Math.max(Math.abs(rawMax) * 0.2, 0.1);
  }

  const step = niceAxisStep((max - min) / 3);
  const axisMin = allowNegative && min < 0 ? Math.floor(min / step) * step : 0;
  let axisMax = Math.ceil(max / step) * step;
  if (axisMax <= axisMin) axisMax = axisMin + step;

  const ticks: number[] = [];
  for (let tick = axisMin; tick <= axisMax + step / 2; tick += step) {
    ticks.push(cleanAxisValue(tick));
  }

  return {
    min: cleanAxisValue(axisMin),
    max: cleanAxisValue(axisMax),
    ticks,
    decimals: axisDecimalsForStep(step, unit)
  };
}

function weatherValueRatio(value: number, axis: WeatherAxis) {
  const span = axis.max - axis.min || 1;
  return Math.max(0, Math.min(1, (value - axis.min) / span));
}

function weatherValueY(value: number, axis: WeatherAxis) {
  return CURVE_BOTTOM - weatherValueRatio(value, axis) * CURVE_HEIGHT;
}

function weatherCurvePath(points: WeatherSeriesPoint[], axis: WeatherAxis) {
  if (!points.length) return "";
  const plotted = points.map((point) => {
    const x = CURVE_LEFT + (point.hour / 23) * CURVE_WIDTH;
    const y = weatherValueY(point.value, axis);
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
  note,
  allowNegative = false
}: {
  label: string;
  unit: string;
  points: WeatherSeriesPoint[];
  selectedHour: number;
  onSelectHour: (hour: number) => void;
  note?: string;
  allowNegative?: boolean;
}) {
  if (!points.length) return null;
  const selected = points.reduce((closest, point) => (
    Math.abs(point.hour - selectedHour) < Math.abs(closest.hour - selectedHour) ? point : closest
  ), points[0]);
  const axis = buildWeatherAxis(points, unit, allowNegative);
  const linePath = weatherCurvePath(points, axis);
  const selectedPoint = {
    x: CURVE_LEFT + (selected.hour / 23) * CURVE_WIDTH,
    y: weatherValueY(selected.value, axis)
  };
  const fillPath = `${linePath} L ${CURVE_RIGHT} ${CURVE_BOTTOM} L ${CURVE_LEFT} ${CURVE_BOTTOM} Z`;
  const decimals = unit === "mm" ? 1 : unit === "m" || unit === "m/h" ? 2 : 0;
  const selectedValueLabel = `${formatCurveTime(selected.hour)} · ${selected.value.toFixed(decimals)} ${unit}`;
  const yAxisTicks = axis.ticks.map((tick) => ({
    label: formatAxisTick(tick, axis.decimals),
    top: `${(weatherValueY(tick, axis) / CURVE_VIEWBOX_HEIGHT) * 100}%`
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
      <div className="curve-chart weather-curve-chart">
        <svg
          viewBox={`0 0 ${CURVE_VIEWBOX_WIDTH} ${CURVE_VIEWBOX_HEIGHT}`}
          preserveAspectRatio="none"
          aria-label={`${label} hourly curve`}
          onClick={updateWeatherHour}
          onPointerMove={updateWeatherHour}
        >
          <rect className="curve-plot-bg" x={CURVE_LEFT} y={CURVE_TOP} width={CURVE_WIDTH} height={CURVE_HEIGHT} rx="20" />
          {axis.ticks.map((tick) => {
            const y = weatherValueY(tick, axis);
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
        <div className="curve-tooltip" style={{ left: `${curveTooltipLeftPercent(selectedPoint.x)}%` }}>
          {selectedValueLabel}
        </div>
        <div className="curve-labels y-labels" aria-hidden="true">
          {yAxisTicks.map((tick) => (
            <span key={tick.label} style={{ top: tick.top }}>{tick.label}</span>
          ))}
        </div>
        <div className="curve-labels x-labels" aria-hidden="true">
          {CURVE_X_TICKS.map((tick) => {
            const x = CURVE_LEFT + (tick / 23) * CURVE_WIDTH;
            return <span key={tick} style={{ left: `${(x / CURVE_VIEWBOX_WIDTH) * 100}%` }}>{String(tick).padStart(2, "0")}</span>;
          })}
        </div>
      </div>
      {note ? <p className="weather-curve-note">{note}</p> : null}
    </div>
  );
}

function windyEmbedUrl(center: ForecastResponse["selected_place"]) {
  if (!center) return null;
  const lat = center.latitude.toFixed(4);
  const lon = center.longitude.toFixed(4);
  return `/api/windy-embed?lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(lon)}`;
}

function WindFieldMap({
  points,
  center,
  selectedHour,
  lang
}: {
  points: HourlyActivityPoint[];
  center: ForecastResponse["selected_place"];
  selectedHour: number;
  lang: Lang;
}) {
  const text = copy(lang);
  const windyUrl = windyEmbedUrl(center);
  if (!points.length) return null;
  const current = points.reduce(
    (closest, point) => (Math.abs(point.hour - selectedHour) < Math.abs(closest.hour - selectedHour) ? point : closest),
    points[0]
  );
  return (
    <div className="weather-map-panel">
      <div className="weather-curve-head">
        <span>{text.windMap}</span>
        <b>{formatCurveTime(current.hour)} · {compassLabel(current.wind_direction_deg)} · {(current.wind_gust_knots ?? current.wind_speed_knots ?? 0).toFixed(0)} kt</b>
      </div>
      {windyUrl ? (
        <iframe
          allowFullScreen
          className="wind-map-frame"
          loading="eager"
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
    .map((point) => ({ hour: point.hour, value: numberOrNull(hourlyWave(point)), label: point.time_window ?? "" }))
    .filter((point): point is WeatherSeriesPoint => point.value != null);
  const windSpeedPoints = hourly
    .map((point) => ({ hour: point.hour, value: numberOrNull(hourlyWindSpeed(point)), label: compassLabel(point.wind_direction_deg) }))
    .filter((point): point is WeatherSeriesPoint => point.value != null);
  const swellPoints = hourly
    .map((point) => ({ hour: point.hour, value: numberOrNull(hourlySwell(point)), label: point.time_window ?? "" }))
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
          lang={lang}
          points={hourly}
          selectedHour={activeHour}
        />
        <WeatherCurve label={text.windSpeed} unit="kt" points={windSpeedPoints} selectedHour={activeHour} onSelectHour={setActiveHour} />
        <WeatherCurve
          label={tideLabel}
          unit={tideUnit}
          points={tidePoints}
          selectedHour={activeHour}
          onSelectHour={setActiveHour}
          note={tideNote}
          allowNegative={hasVerifiedTideHeight}
        />
        <WeatherCurve label={text.waveHeight} unit="m" points={wavePoints} selectedHour={activeHour} onSelectHour={setActiveHour} />
        <WeatherCurve label={text.swellHeight} unit="m" points={swellPoints} selectedHour={activeHour} onSelectHour={setActiveHour} />
      </div>
    </section>
  );
}

function HeroScoreCard({ data, forecast, lang }: { data: ForecastResponse | null; forecast: ForecastResponse["forecast"] | undefined; lang: Lang }) {
  const text = copy(lang);
  const todayDay = todayForecastDay(forecast);
  const bestWindow = todayDay?.best_window ?? forecast?.hero.best_window ?? null;
  const summary = dailyScoreSummary(todayDay);
  const score = dayScore(todayDay) ?? selectedWindowScore(bestWindow) ?? forecast?.hero.score ?? null;
  const label = recommendationLabel(score);
  const tone = scoreTone(label);
  const fishPotential = summary.fishIndex ?? bestWindow?.fish_outlook_score ?? forecast?.hero.fish_outlook_score ?? null;
  const tripReality = summary.tripQuality ?? tripRealityScore(bestWindow) ?? forecast?.hero.comfort_score ?? forecast?.hero.trip_quality_score ?? null;
  const waterbodyClass =
    bestWindow?.waterbody_class ??
    forecast?.classification?.waterbody_class ??
    forecast?.hero.waterbody_class ??
    null;
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
      <div className="hero-score-split" aria-label={lang === "zh" ? "鱼情和出行拆分" : "Fish and trip split"}>
        <div>
          <span>{text.fishPotential}</span>
          <strong>{fishPotential ?? "--"}</strong>
          <small>
            {lang === "zh"
              ? "只看鱼可能是否更活跃。"
              : "Fish signal only, before comfort and safety."}
          </small>
        </div>
        <div>
          <span>{text.tripReality}</span>
          <strong>{tripReality ?? "--"}</strong>
          <small>
            {summary.safetyFlag === "hazardous"
              ? (lang === "zh" ? "安全压力高，出行建议会被压低。" : "Safety risk is high, so trip advice is capped.")
              : summary.safetyFlag === "elevated"
                ? (lang === "zh" ? "安全余量一般，需要更保守。" : "Safety margin is reduced, so be more conservative.")
                : (lang === "zh" ? "全天出行条件均值，安全风险会封顶。" : "Day-average trip ease, capped by safety.")}
          </small>
        </div>
      </div>
      <small>
        {text.waterbodyClass}: {displayWaterbodyClass(waterbodyClass, lang)}
      </small>
      <small>{bestWindow ? `${displayWaterType(bestWindow.dominant_water_type, lang)} ${text.strongestNearby}` : forecast?.hero.headline ?? text.searchResultWaiting}</small>
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
