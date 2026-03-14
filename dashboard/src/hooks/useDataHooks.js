import { useCallback } from "react";
import { usePolling } from "./usePolling";
import {
  fetchSymbols,
  fetchDates,
  fetchPriceHistory,
  fetchSignals,
  fetchTrades,
  fetchPortfolio,
  fetchLogs,
} from "../api";

export function useSymbols() {
  const fetchFn = useCallback(() => fetchSymbols(), []);
  return usePolling(fetchFn);
}

export function useDates() {
  const fetchFn = useCallback(() => fetchDates(), []);
  return usePolling(fetchFn);
}

export function usePriceHistory(symbol) {
  const fetchFn = useCallback(() => fetchPriceHistory(symbol), [symbol]);
  return usePolling(fetchFn);
}

export function useSignals(date) {
  const fetchFn = useCallback(() => fetchSignals(date), [date]);
  return usePolling(fetchFn);
}

export function useTrades(date) {
  const fetchFn = useCallback(() => fetchTrades(date), [date]);
  return usePolling(fetchFn);
}

export function usePortfolio(date) {
  const fetchFn = useCallback(() => fetchPortfolio(date), [date]);
  return usePolling(fetchFn);
}

export function useLogs(date, severity) {
  const fetchFn = useCallback(() => fetchLogs(date, severity), [date, severity]);
  return usePolling(fetchFn);
}
