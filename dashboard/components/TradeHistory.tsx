"use client";

import type { TradeRecord } from "@/lib/types";

interface Props {
  trades: TradeRecord[];
}

function formatDateTime(ts: string): string {
  try {
    return new Date(ts).toLocaleString("ko-KR", {
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return ts;
  }
}

export default function TradeHistory({ trades }: Props) {
  const recent = [...trades].reverse().slice(0, 20);

  return (
    <div
      className="rounded-2xl border p-5"
      style={{ background: "var(--card)", borderColor: "var(--border)" }}
    >
      <div className="text-sm font-semibold mb-4">체결 내역</div>

      {recent.length === 0 ? (
        <div className="text-text-muted text-sm py-6 text-center">체결 내역이 없습니다.</div>
      ) : (
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {recent.map((t, i) => {
            const isBuy = t.side === "buy";
            return (
              <div
                key={i}
                className="flex items-center justify-between py-2 border-b last:border-b-0"
                style={{ borderColor: "var(--border)" }}
              >
                <div className="flex items-center gap-3">
                  <span
                    className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                      isBuy
                        ? "bg-green-400/10 text-green-400"
                        : "bg-red-400/10 text-red-400"
                    }`}
                  >
                    {isBuy ? "매수" : "매도"}
                  </span>
                  <div>
                    <div className="text-sm font-medium">{t.symbol}</div>
                    <div className="text-xs text-text-muted">{formatDateTime(t.ts)}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-bold tabular">
                    ${t.price.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                  </div>
                  <div className="text-xs text-text-muted">{t.qty}주</div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
