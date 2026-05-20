import { execFile, spawn } from "node:child_process";
import { createServer } from "node:http";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, "../../..");
const coastalSearchForecast = path.join(repoRoot, ".venv/bin/coastal-search-forecast");
const coastalPlaceSearch = path.join(repoRoot, ".venv/bin/coastal-place-search");
const coastalApiForecast = path.join(repoRoot, ".venv/bin/coastal-api-forecast");
const coastalFeedback = path.join(repoRoot, ".venv/bin/coastal-feedback");
const coastalScoreFactors = path.join(repoRoot, ".venv/bin/coastal-score-factors");
const API_PORT = Number(process.env.COASTAL_WEB_API_PORT ?? process.env.PORT ?? 8787);
const FEEDBACK_MAX_BODY_BYTES = 32 * 1024;
const SCORE_FACTORS_MAX_BODY_BYTES = 512 * 1024;
const API_CACHE_TTL_MS = 15 * 60 * 1000;
const API_CACHE_MAX_ENTRIES = 80;
const apiCache = new Map();
const pendingRequests = new Map();

function sendJson(response, statusCode, payload) {
  response.writeHead(statusCode, {
    "Content-Type": "application/json; charset=utf-8",
    "Access-Control-Allow-Origin": "*"
  });
  response.end(JSON.stringify(payload));
}

function sendHtml(response, statusCode, html) {
  response.writeHead(statusCode, {
    "Content-Type": "text/html; charset=utf-8",
    "Cache-Control": "no-store",
    "Access-Control-Allow-Origin": "*"
  });
  response.end(html);
}

function single(value, fallback = "") {
  if (Array.isArray(value)) return value[0] ?? fallback;
  return value ?? fallback;
}

function cacheKey(url) {
  return `${url.pathname}?${url.searchParams.toString()}`;
}

function getCachedPayload(url) {
  const key = cacheKey(url);
  const cached = apiCache.get(key);
  if (!cached) return null;
  if (Date.now() - cached.createdAt > API_CACHE_TTL_MS) {
    apiCache.delete(key);
    return null;
  }
  apiCache.delete(key);
  apiCache.set(key, cached);
  return cached.payload;
}

function setCachedPayload(url, payload) {
  const key = cacheKey(url);
  apiCache.set(key, { createdAt: Date.now(), payload });
  while (apiCache.size > API_CACHE_MAX_ENTRIES) {
    const oldestKey = apiCache.keys().next().value;
    apiCache.delete(oldestKey);
  }
}

async function cached(url, loader) {
  const cachedPayload = getCachedPayload(url);
  if (cachedPayload !== null) {
    return cachedPayload;
  }
  const key = cacheKey(url);
  if (pendingRequests.has(key)) {
    return pendingRequests.get(key);
  }
  const pending = loader()
    .then((payload) => {
      setCachedPayload(url, payload);
      return payload;
    })
    .finally(() => {
      pendingRequests.delete(key);
    });
  pendingRequests.set(key, pending);
  return pending;
}

function sanitizeCoordinate(value, fallback) {
  const number = Number(value);
  if (!Number.isFinite(number)) return fallback;
  return number;
}

async function runWindyEmbedProxy(url) {
  const lat = sanitizeCoordinate(url.searchParams.get("lat"), -42.8991).toFixed(4);
  const lon = sanitizeCoordinate(url.searchParams.get("lon"), 147.3390).toFixed(4);
  const windyUrl = new URL("https://embed.windy.com/embed2.html");
  const params = {
    lat,
    lon,
    detailLat: lat,
    detailLon: lon,
    width: "760",
    height: "620",
    zoom: "10",
    level: "surface",
    overlay: "wind",
    product: "ecmwf",
    menu: "",
    message: "true",
    marker: "true",
    calendar: "now",
    pressure: "",
    type: "map",
    location: "coordinates",
    detail: "true",
    metricWind: "kt",
    metricTemp: "°C",
    radarRange: "-1",
  };
  for (const [key, value] of Object.entries(params)) {
    windyUrl.searchParams.set(key, value);
  }
  const upstream = await fetch(windyUrl, {
    headers: {
      "User-Agent": "Mozilla/5.0 CoastalFishingForecast/1.0",
      "Accept": "text/html,application/xhtml+xml",
    },
  });
  if (!upstream.ok) {
    throw new Error(`Windy embed request failed with ${upstream.status}`);
  }
  const html = await upstream.text();
  return html
    .replace("<head>", '<head><base href="https://embed.windy.com/">')
    .replaceAll('src="/', 'src="https://embed.windy.com/')
    .replaceAll('href="/', 'href="https://embed.windy.com/');
}

function isoDateOffset(days) {
  const date = new Date();
  date.setDate(date.getDate() + days);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

async function runSearchForecast(url) {
  const query = single(url.searchParams.get("query"), "Sandy Bay Tasmania").trim();
  const startDate = single(url.searchParams.get("start_date"), isoDateOffset(-7));
  const endDate = single(url.searchParams.get("end_date"), isoDateOffset(5));
  const region = url.searchParams.get("region");
  const plannerProvider = single(url.searchParams.get("planner_provider"), "rule_based");
  const args = [
    query,
    "--provider",
    "nominatim",
    "--start-date",
    startDate,
    "--end-date",
    endDate,
    "--windows",
    "morning,day,dusk",
    "--condition-source",
    "forecast",
    "--tide-source",
    "openmeteo_model",
    "--planner-provider",
    plannerProvider,
    "--structure-source",
    "auto",
    "--structure-radius-m",
    "2000",
    "--cache-dir",
    ".cache/coastal_fishing_forecast"
  ];
  if (region) args.push("--region", region);

  const { stdout } = await execFileAsync(coastalSearchForecast, args, {
    cwd: repoRoot,
    maxBuffer: 20 * 1024 * 1024,
    timeout: 60000
  });
  return JSON.parse(stdout);
}

async function runPlaceSearch(url) {
  const query = single(url.searchParams.get("query"), "").trim();
  const args = [
    query,
    "--provider",
    "nominatim",
    "--country",
    "",
    "--limit",
    "8",
    "--cache-dir",
    ".cache/coastal_fishing_forecast"
  ];
  const { stdout } = await execFileAsync(coastalPlaceSearch, args, {
    cwd: repoRoot,
    maxBuffer: 4 * 1024 * 1024,
    timeout: 30000
  });
  return JSON.parse(stdout);
}

function readRequestBody(request, maxBytes) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let total = 0;
    request.on("data", (chunk) => {
      total += chunk.length;
      if (total > maxBytes) {
        reject(new Error("payload_too_large"));
        request.destroy();
        return;
      }
      chunks.push(chunk);
    });
    request.on("end", () => resolve(Buffer.concat(chunks).toString("utf-8")));
    request.on("error", reject);
  });
}

function recordScoreFactorsViaCli(body) {
  return new Promise((resolve, reject) => {
    const child = spawn(coastalScoreFactors, [], {
      cwd: repoRoot,
      timeout: 35000,
    });
    const out = [];
    const err = [];
    child.stdout.on("data", (c) => out.push(c));
    child.stderr.on("data", (c) => err.push(c));
    child.on("error", reject);
    child.on("close", (code) => {
      const stdout = Buffer.concat(out).toString("utf-8").trim();
      const stderr = Buffer.concat(err).toString("utf-8").trim();
      if (!stdout) {
        reject(new Error(`score-factors CLI returned no output (exit ${code}); stderr=${stderr}`));
        return;
      }
      try {
        resolve({ code, json: JSON.parse(stdout) });
      } catch (parseError) {
        reject(parseError);
      }
    });
    child.stdin.write(body);
    child.stdin.end();
  });
}

function recordFeedbackViaCli(body) {
  return new Promise((resolve, reject) => {
    const child = spawn(coastalFeedback, [], {
      cwd: repoRoot,
      timeout: 10000,
    });
    const out = [];
    const err = [];
    child.stdout.on("data", (c) => out.push(c));
    child.stderr.on("data", (c) => err.push(c));
    child.on("error", reject);
    child.on("close", (code) => {
      const stdout = Buffer.concat(out).toString("utf-8").trim();
      const stderr = Buffer.concat(err).toString("utf-8").trim();
      if (!stdout) {
        reject(new Error(`feedback CLI returned no output (exit ${code}); stderr=${stderr}`));
        return;
      }
      try {
        resolve({ code, json: JSON.parse(stdout) });
      } catch (parseError) {
        reject(parseError);
      }
    });
    child.stdin.write(body);
    child.stdin.end();
  });
}

async function runCoordinateForecast(url) {
  const lat = single(url.searchParams.get("lat"));
  const lon = single(url.searchParams.get("lon"));
  const displayName = single(url.searchParams.get("display_name"), `${lat}, ${lon}`);
  const placeId = single(url.searchParams.get("id"), `selected:${lat},${lon}`);
  const startDate = single(url.searchParams.get("start_date"), isoDateOffset(-7));
  const endDate = single(url.searchParams.get("end_date"), isoDateOffset(5));
  const region = url.searchParams.get("region");
  const plannerProvider = single(url.searchParams.get("planner_provider"), "rule_based");
  const args = [
    lat,
    lon,
    "--start-date",
    startDate,
    "--end-date",
    endDate,
    "--windows",
    "morning,day,dusk",
    "--condition-source",
    "forecast",
    "--tide-source",
    "openmeteo_model",
    "--planner-provider",
    plannerProvider,
    "--structure-source",
    "auto",
    "--structure-radius-m",
    "2000",
    "--cache-dir",
    ".cache/coastal_fishing_forecast"
  ];
  if (region) args.push("--region", region);
  const { stdout } = await execFileAsync(coastalApiForecast, args, {
    cwd: repoRoot,
    maxBuffer: 20 * 1024 * 1024,
    timeout: 60000
  });
  const forecast = JSON.parse(stdout);
  const selectedPlace = {
    id: placeId,
    display_name: displayName,
    latitude: Number(lat),
    longitude: Number(lon),
    source: "selected_place"
  };
  return {
    contract_version: "2026-04-28.coordinate_forecast.v1",
    query: displayName,
    provider: "selected_coordinate",
    selected_place: selectedPlace,
    candidates: [selectedPlace],
    forecast,
    plan: forecast.plan,
    status: forecast.hero?.best_window ? "ok" : "unsupported_or_no_result"
  };
}

const server = createServer(async (request, response) => {
  try {
    const url = new URL(request.url ?? "/", `http://127.0.0.1:${API_PORT}`);
    if (request.method === "OPTIONS") {
      response.writeHead(204, {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type"
      });
      response.end();
      return;
    }
    if (url.pathname === "/api/health") {
      sendJson(response, 200, { ok: true, service: "coastal-web-api" });
      return;
    }
    if (url.pathname === "/api/windy-embed") {
      const html = await runWindyEmbedProxy(url);
      sendHtml(response, 200, html);
      return;
    }
    if (url.pathname === "/api/search-forecast") {
      const payload = await cached(url, () => runSearchForecast(url));
      sendJson(response, 200, payload);
      return;
    }
    if (url.pathname === "/api/place-search") {
      const payload = await cached(url, () => runPlaceSearch(url));
      sendJson(response, 200, payload);
      return;
    }
    if (url.pathname === "/api/coordinate-forecast") {
      const payload = await cached(url, () => runCoordinateForecast(url));
      sendJson(response, 200, payload);
      return;
    }
    if (url.pathname === "/api/feedback") {
      if (request.method !== "POST") {
        sendJson(response, 405, { error: "method_not_allowed", allow: "POST" });
        return;
      }
      let body;
      try {
        body = await readRequestBody(request, FEEDBACK_MAX_BODY_BYTES);
      } catch (bodyError) {
        const message = bodyError instanceof Error ? bodyError.message : String(bodyError);
        if (message === "payload_too_large") {
          sendJson(response, 413, { error: "payload_too_large" });
        } else {
          sendJson(response, 400, { error: "request_body_error", message });
        }
        return;
      }
      if (!body) {
        sendJson(response, 400, { error: "empty_body" });
        return;
      }
      try {
        const result = await recordFeedbackViaCli(body);
        if (result.json && result.json.error) {
          sendJson(response, 400, result.json);
        } else {
          sendJson(response, 201, result.json);
        }
      } catch (feedbackError) {
        sendJson(response, 500, {
          error: "feedback_io_error",
          message: feedbackError instanceof Error ? feedbackError.message : String(feedbackError),
        });
      }
      return;
    }
    if (url.pathname === "/api/score-factors") {
      if (request.method !== "POST") {
        sendJson(response, 405, { error: "method_not_allowed", allow: "POST" });
        return;
      }
      let body;
      try {
        body = await readRequestBody(request, SCORE_FACTORS_MAX_BODY_BYTES);
      } catch (bodyError) {
        const message = bodyError instanceof Error ? bodyError.message : String(bodyError);
        if (message === "payload_too_large") {
          sendJson(response, 413, { error: "payload_too_large" });
        } else {
          sendJson(response, 400, { error: "request_body_error", message });
        }
        return;
      }
      if (!body) {
        sendJson(response, 400, { error: "empty_body" });
        return;
      }
      try {
        const result = await recordScoreFactorsViaCli(body);
        sendJson(response, 200, result.json);
      } catch (sfError) {
        sendJson(response, 500, {
          error: "score_factors_io_error",
          message: sfError instanceof Error ? sfError.message : String(sfError),
        });
      }
      return;
    }
    sendJson(response, 404, { error: "not_found" });
  } catch (error) {
    sendJson(response, 500, {
      error: "api_error",
      message: error instanceof Error ? error.message : String(error)
    });
  }
});

server.listen(API_PORT, "127.0.0.1", () => {
  console.log(`Coastal web API listening on http://127.0.0.1:${API_PORT}`);
});
