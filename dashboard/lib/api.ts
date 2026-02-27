import type { BotStatus, HistoryData, StrategyInfo, TradingConfig, StrategyCatalog } from "./types";

// 개발: Next.js(:3000) → Python(:8080) CORS 허용
// 프로덕션: 동일 오리진 (Python이 Next.js 빌드 파일 서빙)
export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ||
  (typeof window !== "undefined" && window.location.port === "3000"
    ? "http://localhost:8080"
    : "");

function authHeaders(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("botApiToken");
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.error ?? `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

// ── GET 엔드포인트 ───────────────────────────────────────────────
export const fetchStatus = (): Promise<BotStatus> => apiFetch("/status");
export const fetchHistory = (): Promise<HistoryData> => apiFetch("/history");
export const fetchStrategyInfo = (): Promise<StrategyInfo> => apiFetch("/strategy");
export const fetchConfig = (): Promise<TradingConfig> => apiFetch("/config");
export const fetchStrategyCatalog = (): Promise<StrategyCatalog> => apiFetch("/strategies");

// ── POST 제어 명령 ───────────────────────────────────────────────
export const pauseBot = () => apiFetch("/pause", { method: "POST" });
export const resumeBot = () => apiFetch("/resume", { method: "POST" });
export const stopBot = () => apiFetch("/stop", { method: "POST" });

// ── 전략 변경 ────────────────────────────────────────────────────
export const swapStrategy = (name: string, params?: Record<string, number>) =>
  apiFetch<StrategyInfo & { ok: boolean }>("/strategy", {
    method: "POST",
    body: JSON.stringify({ name, params }),
  });

export const updateStrategyParams = (params: Record<string, number>) =>
  apiFetch<StrategyInfo & { ok: boolean }>("/strategy/params", {
    method: "POST",
    body: JSON.stringify(params),
  });

// ── 봇 설정 변경 ─────────────────────────────────────────────────
export const updateConfig = (cfg: Partial<TradingConfig>) =>
  apiFetch<TradingConfig & { ok: boolean }>("/config", {
    method: "POST",
    body: JSON.stringify(cfg),
  });
