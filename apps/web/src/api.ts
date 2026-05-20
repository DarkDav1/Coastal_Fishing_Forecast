import type { ForecastResponse, PlaceCandidate, PlaceSearchResponse } from "./types";

function isoDateOffset(days: number) {
  const date = new Date();
  date.setDate(date.getDate() + days);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function forecastDefaults() {
  return {
    start_date: isoDateOffset(-7),
    end_date: isoDateOffset(5),
    planner_provider: "rule_based"
  };
}

async function readApiError(response: Response) {
  const body = await response.text();
  if (body) {
    try {
      const parsed = JSON.parse(body) as { message?: string; error?: string };
      return parsed.message ?? parsed.error ?? body;
    } catch {
      return body;
    }
  }
  if (response.status >= 500) {
    return "Local forecast API is not reachable. Start the web API server and try again.";
  }
  return `Request failed with ${response.status}`;
}

export async function searchForecast(query: string): Promise<ForecastResponse> {
  const params = new URLSearchParams({
    query,
    ...forecastDefaults()
  });
  const response = await fetch(`/api/search-forecast?${params.toString()}`);
  if (!response.ok) {
    throw new Error(await readApiError(response));
  }
  return response.json();
}

export async function searchPlaces(query: string): Promise<PlaceSearchResponse> {
  const params = new URLSearchParams({ query });
  const response = await fetch(`/api/place-search?${params.toString()}`);
  if (!response.ok) {
    throw new Error(await readApiError(response));
  }
  return response.json();
}

export async function forecastPlace(candidate: PlaceCandidate): Promise<ForecastResponse> {
  const params = new URLSearchParams({
    lat: String(candidate.latitude),
    lon: String(candidate.longitude),
    display_name: candidate.display_name,
    id: candidate.id,
    ...forecastDefaults()
  });
  const response = await fetch(`/api/coordinate-forecast?${params.toString()}`);
  if (!response.ok) {
    throw new Error(await readApiError(response));
  }
  return response.json();
}
