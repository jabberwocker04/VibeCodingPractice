"use client";

import { useState, useCallback } from "react";
import { pauseBot, resumeBot, stopBot } from "@/lib/api";
import type { BotStatus } from "@/lib/types";

interface Props {
  status: BotStatus | undefined;
  onRefresh: () => void;
}

type Msg = { text: string; ok: boolean } | null;

export default function ControlPanel({ status, onRefresh }: Props) {
  const [msg, setMsg] = useState<Msg>(null);
  const [loading, setLoading] = useState(false);

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
        setMsg({ text: `실패: ${e instanceof Error ? e.message : String(e)}`, ok: false });
      } finally {
        setLoading(false);
      }
    },
    [loading, onRefresh]
  );

  const handleStop = () => {
    if (!confirm("봇을 완전히 중지합니까?\n서버 프로세스도 종료됩니다.")) return;
    act(stopBot, "중지");
  };

  const isRunning = status?.running ?? false;
  const isPaused = status?.paused ?? false;

  return (
    <div
      className="rounded-2xl border p-5"
      style={{ background: "var(--card)", borderColor: "var(--border)" }}
    >
      <div className="text-sm font-semibold mb-4">봇 제어</div>

      <div className="flex flex-wrap gap-2">
        {/* 일시정지 / 재개 */}
        {isPaused ? (
          <button
            onClick={() => act(resumeBot, "재개")}
            disabled={!isRunning || loading}
            className="px-4 py-2 rounded-xl text-sm font-semibold bg-green-500 text-white disabled:opacity-40 hover:opacity-85 transition-opacity"
          >
            ▶ 재개
          </button>
        ) : (
          <button
            onClick={() => act(pauseBot, "일시정지")}
            disabled={!isRunning || loading}
            className="px-4 py-2 rounded-xl text-sm font-semibold bg-yellow-500 text-black disabled:opacity-40 hover:opacity-85 transition-opacity"
          >
            ⏸ 일시정지
          </button>
        )}

        {/* 중지 */}
        <button
          onClick={handleStop}
          disabled={!isRunning || loading}
          className="px-4 py-2 rounded-xl text-sm font-semibold bg-red-500 text-white disabled:opacity-40 hover:opacity-85 transition-opacity"
        >
          ■ 중지
        </button>
      </div>

      {/* 메시지 */}
      {msg && (
        <div
          className={`mt-3 text-xs font-medium ${msg.ok ? "text-green-400" : "text-red-400"}`}
        >
          {msg.ok ? "✓ " : "⚠ "}{msg.text}
        </div>
      )}
    </div>
  );
}
