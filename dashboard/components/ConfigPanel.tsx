"use client";

import { useState, useEffect, useCallback } from "react";
import { fetchConfig, updateConfig } from "@/lib/api";
import type { BotStatus, TradingConfig } from "@/lib/types";

interface Props {
  status: BotStatus | undefined;
  onRefresh: () => void;
}

type Msg = { text: string; ok: boolean } | null;

export default function ConfigPanel({ status, onRefresh }: Props) {
  const [config, setConfig] = useState<TradingConfig>({
    quantity: 1,
    max_position_qty: 5,
    tick_seconds: 3,
    interval: "1m",
    history_period: "1d",
  });
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<Msg>(null);

  // Load current config on mount
  useEffect(() => {
    fetchConfig()
      .then((c) => setConfig(c))
      .catch(() => {});
  }, []);

  const set = (key: keyof TradingConfig, val: string) => {
    const n = parseFloat(val);
    if (isNaN(n)) return;
    setConfig((prev) => ({ ...prev, [key]: n }));
  };

  const handleSave = useCallback(async () => {
    if (loading) return;
    setLoading(true);
    setMsg(null);
    try {
      await updateConfig(config);
      setMsg({ text: "설정 저장 완료", ok: true });
      onRefresh();
    } catch (e: unknown) {
      setMsg({ text: `실패: ${e instanceof Error ? e.message : String(e)}`, ok: false });
    } finally {
      setLoading(false);
    }
  }, [config, loading, onRefresh]);

  const isRunning = status?.running ?? false;

  const fields: { key: keyof TradingConfig; label: string; step: number; min: number }[] = [
    { key: "quantity", label: "주문 수량 (주)", step: 1, min: 1 },
    { key: "max_position_qty", label: "최대 보유 수량", step: 1, min: 1 },
    { key: "tick_seconds", label: "틱 간격 (초)", step: 0.5, min: 0.5 },
  ];

  return (
    <div
      className="rounded-2xl border p-5"
      style={{ background: "var(--card)", borderColor: "var(--border)" }}
    >
      <div className="text-sm font-semibold mb-4">거래 설정</div>

      <div className="grid grid-cols-1 gap-3 mb-4">
        {fields.map(({ key, label, step, min }) => (
          <div key={key}>
            <label className="block text-xs text-gray-400 mb-1">{label}</label>
            <input
              type="number"
              step={step}
              min={min}
              value={config[key]}
              onChange={(e) => set(key, e.target.value)}
              className="w-full rounded-xl px-3 py-2 text-sm bg-[var(--card2)] border border-[var(--border)] text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
        ))}
      </div>

      <button
        onClick={handleSave}
        disabled={!isRunning || loading}
        className="w-full px-4 py-2 rounded-xl text-sm font-semibold bg-blue-600 text-white disabled:opacity-40 hover:opacity-85 transition-opacity"
      >
        {loading ? "저장 중…" : "설정 저장"}
      </button>

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
