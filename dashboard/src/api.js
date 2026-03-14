const BASE_URL = "http://localhost:8000";

async function apiFetch(path) {
  const response = await fetch(`${BASE_URL}${path}`);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText} (${path})`);
  }
  return response.json();
}

export async function fetchHealth() {
  return apiFetch("/api/health");
}

export async function fetchSymbols() {
  return apiFetch("/api/symbols");
}

export async function fetchDates() {
  return apiFetch("/api/dates");
}

export async function fetchPriceHistory(symbol) {
  return apiFetch(`/api/price-history/${symbol}`);
}

export async function fetchSignals(date) {
  return apiFetch(date ? `/api/signals/${date}` : "/api/signals");
}

export async function fetchTrades(date) {
  return apiFetch(date ? `/api/trades/${date}` : "/api/trades");
}

export async function fetchPortfolio(date) {
  return apiFetch(date ? `/api/portfolio/${date}` : "/api/portfolio");
}

export async function fetchLogs(date, severity) {
  let path = date ? `/api/logs/${date}` : "/api/logs";
  if (severity) {
    path += `?severity=${encodeURIComponent(severity)}`;
  }
  return apiFetch(path);
}
