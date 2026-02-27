"use client";

import type { BotStatus } from "@/lib/types";

function fmt(v: number | undefined, digits = 2): string {
  if (v == null) return "—";
  return v.toLocaleString("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

interface CardProps {
  label: string;
  value: React.ReactNode;
  sub?: React.ReactNode;
}

function Card({ label, value, sub }: CardProps) {
  return (
    <div
      className="rounded-2xl p-5 border flex flex-col gap-2"
      style={{ background: "var(--card)", borderColor: "var(--border)" }}
    >
      <div className="text-xs text-text-muted tracking-wide uppercase">{label}</div>
      <div className="text-2xl font-bold tabular leading-none">{value}</div>
      {sub && <div className="text-xs text-text-muted">{sub}</div>}
    </div>
  );
}

interface Props {
  status: BotStatus | undefined;
}

export default function StatCards({ status }: Props) {
  const pnl = status?.pnl ?? 0;
  const pnlPct = status?.pnl_pct ?? 0;
  const isUp = pnl >= 0;
  const pnlColor = isUp ? "text-green-400" : "text-red-400";
  const sign = isUp ? "+" : "";

  const signalMap: Record<string, { label: string; cls: string }> = {
    buy:  { label: "매수 ▲", cls: "text-green-400" },
    sell: { label: "매도 ▼", cls: "text-red-400" },
    hold: { label: "대기", cls: "text-text-muted" },
  };
  const sig = signalMap[status?.last_signal ?? "hold"] ?? signalMap.hold;

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
      {/* 평가금액 */}
      <Card
        label="평가금액"
        value={<span className="tabular">${fmt(status?.equity)}</span>}
        sub={`시작 이후 ${sign}${pnlPct.toFixed(2)}%`}
      />

      {/* 총 수익 */}
      <Card
        label="총 손익"
        value={
          <span className={`tabular ${pnlColor}`}>
            {sign}${fmt(Math.abs(pnl))}
          </span>
        }
        sub={
          <span className={pnlColor}>
            {sign}{pnlPct.toFixed(2)}%
          </span>
        }
      />

      {/* 현금 */}
      <Card
        label="현금 잔고"
        value={<span className="tabular">${fmt(status?.cash)}</span>}
        sub="주문가능금액"
      />

      {/* 가격 */}
      <Card
        label="현재가"
        value={<span className="tabular">${fmt(status?.last_price)}</span>}
        sub={status?.symbol ?? "—"}
      />

      {/* 포지션 */}
      <Card
        label="보유 수량"
        value={<span className="tabular">{status?.position_qty ?? 0}주</span>}
        sub={`거래 ${status?.trades ?? 0}회`}
      />

      {/* 신호 */}
      <Card
        label="마지막 신호"
        value={<span className={sig.cls}>{sig.label}</span>}
        sub={`틱 ${status?.loop_count ?? 0}회`}
      />
    </div>
  );
}
