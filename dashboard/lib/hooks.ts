import useSWR from "swr";
import { fetchStatus, fetchHistory, fetchStrategyCatalog } from "./api";
import type { BotStatus, HistoryData, StrategyCatalog } from "./types";

const POLL_MS = 3000;

export function useBotStatus() {
  return useSWR<BotStatus>("status", fetchStatus, {
    refreshInterval: POLL_MS,
    revalidateOnFocus: false,
    dedupingInterval: 1000,
  });
}

export function useHistory() {
  return useSWR<HistoryData>("history", fetchHistory, {
    refreshInterval: POLL_MS,
    revalidateOnFocus: false,
    dedupingInterval: 1000,
  });
}

export function useStrategyCatalog() {
  return useSWR<StrategyCatalog>("strategies", fetchStrategyCatalog, {
    revalidateOnFocus: false,
    revalidateOnReconnect: false,
  });
}
