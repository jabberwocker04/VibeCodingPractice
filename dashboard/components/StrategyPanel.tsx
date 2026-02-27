"use client";

import { useState, useCallback } from "react";
import { swapStrategy, updateStrategyParams } from "@/lib/api";
import { useStrategyCatalog } from "@/lib/hooks";
import type { BotStatus, StrategyInfo } from "@/lib/types";

interface Props {
  status: BotStatus | undefined;
  strategyInfo: StrategyInfo | undefined;
  onRefresh: () => void;
}

type Msg = { text: string; ok: boolean } | null;

const PARAM_LABELS: Record<string, string> = {
  short_window: "단기 윈도우",
  long_window: "장기 윈도우",
  period: "기간",
  oversold: "과매도 기준",
  overbought: "과매수 기준",
  fast_period: "빠른 EMA 기간",
  slow_period: "느린 EMA 기간",
  signal_period: "시그널 기간",
  std_dev: "표준편차 배수",
};

export default function StrategyPanel({ status, strategyInfo, onRefresh }: Props) {
  const { data: catalog } = useStrategyCatalog();
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<Msg>(null);

  // Selected strategy name
  const [selectedName, setSelectedName] = useState<string>(() => strategyInfo?.name ?? "sma");

  // Editable params — initialise from current strategyInfo or catalog defaults
  const [params, setParams] = useState<Record<string, number>>(() => {
    if (strategyInfo?.params) return { ...strategyInfo.params };
    return {};
  });

  const defaultParams: Record<string, number> =
    (catalog?.defaults[selectedName] as Record<string, number>) ?? {};

  const displayParams: Record<string, number> =
    Object.keys(params).length > 0 && strategyInfo?.name === selectedName
      ? params
      : defaultParams;

  const handleSelectStrategy = (name: string) => {
    setSelectedName(name);
    const defaults = (catalog?.defaults[name] as Record<string, number>) ?? {};
    setParams({ ...defaults });
  };

  const setParam = (key: string, val: string) => {
    const n = parseFloat(val);
    if (isNaN(n)) return;
    setParams((prev) => ({ ...prev, [key]: n }));
  };

  const act = useCallback(
    async (fn: () => Promise<unknown>, label: string) => {
      if (loading) return;
      setLoading(true);
      setMsg(null);
      try {
        await fn();
        setMsg({ text: `${label} 완료`, ok: true });
        onRefresh();
      } catch (e: unknown) {
        setMsg({
          text: `실패: ${e instanceof Error ? e.message : String(e)}`,
          ok: false,
        });
      } finally {
        setLoading(false);
      }
    },
    [loading, onRefresh]
  );

  const handleSwap = () => {
    act(() => swapStrategy(selectedName, displayParams), "전략 교체");
  };

  const handleParamsOnly = () => {
    act(() => updateStrategyParams(displayParams), "파라미터 수정");
  };

  const isRunning = status?.running ?? false;
  const isSameStrategy = selectedName === (strategyInfo?.name ?? selectedName);
  const strategyNames = catalog?.names ?? ["sma", "rsi", "macd", "bollinger"];
  const descriptions = catalog?.descriptions ?? {};

  return (
    <div
      className="rounded-2xl border p-5"
      style={{ background: "var(--card)", borderColor: "var(--border)" }}
    >
      <div className="text-sm font-semibold mb-4">전략 설정</div>

      {/* Strategy selector */}
      <div className="mb-4">
        <label className="block text-xs text-gray-400 mb-1">전략 선택</label>
        <select
          value={selectedName}
          onChange={(e) => handleSelectStrategy(e.target.value)}
          className="w-full rounded-xl px-3 py-2 text-sm bg-[var(--card2)] border border-[var(--border)] text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          {strategyNames.map((name) => (
            <option key={name} value={name}>
              {name.toUpperCase()} — {descriptions[name] ?? name}
            </option>
          ))}
        </select>
      </div>

      {/* Param inputs */}
      {Object.keys(displayParams).length > 0 && (
        <div className="grid grid-cols-2 gap-3 mb-4">
          {Object.entries(displayParams).map(([key, val]) => (
            <div key={key}>
              <label className="block text-xs text-gray-400 mb-1">
                {PARAM_LABELS[key] ?? key}
              </label>
              <input
                type="number"
                step="any"
                value={params[key] ?? val}
                onChange={(e) => setParam(key, e.target.value)}
                className="w-full rounded-xl px-3 py-2 text-sm bg-[var(--card2)] border border-[var(--border)] text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
          ))}
        </div>
      )}

      {/* Action buttons */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={handleSwap}
          disabled={!isRunning || loading}
          className="px-4 py-2 rounded-xl text-sm font-semibold bg-blue-600 text-white disabled:opacity-40 hover:opacity-85 transition-opacity"
        >
          {loading ? "처리 중…" : "전략 교체"}
        </button>
        <button
          onClick={handleParamsOnly}
          disabled={!isRunning || loading || !isSameStrategy}
          title={!isSameStrategy ? "파라미터 수정은 현재 전략과 동일할 때만 가능" : undefined}
          className="px-4 py-2 rounded-xl text-sm font-semibold bg-[var(--card2)] border border-[var(--border)] text-white disabled:opacity-40 hover:opacity-85 transition-opacity"
        >
          파라미터만 수정
        </button>
      </div>

      {/* Active strategy info */}
      {strategyInfo && (
        <div className="mt-3 text-xs text-gray-500">
          현재 활성:{" "}
          <span className="text-gray-300">{strategyInfo.name.toUpperCase()}</span>{" "}
          — 파라미터:{" "}
          <span className="text-gray-300">
            {Object.entries(strategyInfo.params)
              .map(([k, v]) => `${k}=${v}`)
              .join(", ")}
          </span>
        </div>
      )}

      {/* Message */}
      {msg && (
        <div
          className={`mt-3 text-xs font-medium ${msg.ok ? "text-green-400" : "text-red-400"}`}
        >
          {msg.ok ? "✓ " : "⚠ "}
          {msg.text}
        </div>
      )}
    </div>
  );
}
