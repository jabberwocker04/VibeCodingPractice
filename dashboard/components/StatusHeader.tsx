"use client";

import type { BotStatus } from "@/lib/types";

interface Props {
  status: BotStatus | undefined;
  isLoading: boolean;
}

function StatusDot({ running, paused }: { running: boolean; paused: boolean }) {
  if (!running)
    return (
      <span className="flex items-center gap-2 text-sm font-semibold text-red-400">
        <span className="w-2 h-2 rounded-full bg-red-400" />
        중지됨
      </span>
    );
  if (paused)
    return (
      <span className="flex items-center gap-2 text-sm font-semibold text-yellow-400">
        <span className="w-2 h-2 rounded-full bg-yellow-400" />
        일시정지
      </span>
    );
  return (
    <span className="flex items-center gap-2 text-sm font-semibold text-green-400">
      <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse-dot" />
      매매 중
    </span>
  );
}

export default function StatusHeader({ status, isLoading }: Props) {
  const name = status?.company_name || status?.symbol || "자동매매봇";
  const sym = status?.symbol ?? "—";
  const strat = status?.strategy ?? "—";
  const interval = status?.interval ?? "—";

  return (
    <header
      className="sticky top-0 z-50 flex items-center justify-between px-6 py-4 border-b"
      style={{ background: "var(--bg)", borderColor: "var(--border)" }}
    >
      {/* 왼쪽: 로고 + 이름 */}
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-blue-500 flex items-center justify-center text-white text-lg font-black select-none">
          N
        </div>
        <div>
          <div className="text-base font-bold leading-tight">{name}</div>
          <div className="text-xs text-text-muted">
            {sym} &middot; {strat} &middot; {interval}
          </div>
        </div>
      </div>

      {/* 오른쪽: 상태 뱃지 */}
      <div
        className="flex items-center gap-3 px-4 py-2 rounded-2xl text-sm"
        style={{ background: "var(--card2)" }}
      >
        {isLoading && !status ? (
          <span className="flex items-center gap-2 text-text-muted text-sm">
            <span className="w-3 h-3 rounded-full border-2 border-text-muted border-t-transparent animate-spin" />
            연결 중
          </span>
        ) : (
          <StatusDot running={status?.running ?? false} paused={status?.paused ?? false} />
        )}
      </div>
    </header>
  );
}
