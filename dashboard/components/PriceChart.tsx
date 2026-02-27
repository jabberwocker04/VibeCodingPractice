"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  ZAxis,
} from "recharts";
import type { PricePoint } from "@/lib/types";

interface Props {
  prices: PricePoint[];
  symbol?: string;
  lastPrice?: number;
}

function formatTime(ts: string): string {
  try {
    return new Date(ts).toLocaleTimeString("ko-KR", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return ts;
  }
}

function formatPrice(v: number): string {
  return "$" + v.toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 2 });
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function CustomTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload as PricePoint;
  if (!d) return null;

  const sigMap: Record<string, string> = { buy: "매수 ▲", sell: "매도 ▼", hold: "" };
  const sigColor: Record<string, string> = { buy: "#22C55E", sell: "#EF4444", hold: "#8B8FA8" };

  return (
    <div
      className="text-xs rounded-xl p-3 shadow-xl border"
      style={{ background: "var(--card)", borderColor: "var(--border)" }}
    >
      <div className="text-text-muted mb-1">{formatTime(d.ts)}</div>
      <div className="font-bold">{formatPrice(d.price)}</div>
      {d.signal !== "hold" && (
        <div style={{ color: sigColor[d.signal] }}>{sigMap[d.signal]}</div>
      )}
    </div>
  );
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function SignalDot(props: any) {
  const { cx, cy, payload } = props as { cx: number; cy: number; payload: PricePoint };
  if (payload.signal === "buy") {
    return <circle cx={cx} cy={cy} r={5} fill="#22C55E" stroke="#0A0B10" strokeWidth={1.5} />;
  }
  if (payload.signal === "sell") {
    return <circle cx={cx} cy={cy} r={5} fill="#EF4444" stroke="#0A0B10" strokeWidth={1.5} />;
  }
  return null;
}

export default function PriceChart({ prices, symbol, lastPrice }: Props) {
  const data = prices.map((p) => ({ ...p, label: formatTime(p.ts) }));

  const minP = Math.min(...prices.map((p) => p.price)) * 0.9995;
  const maxP = Math.max(...prices.map((p) => p.price)) * 1.0005;

  return (
    <div
      className="rounded-2xl border p-5"
      style={{ background: "var(--card)", borderColor: "var(--border)" }}
    >
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="text-sm font-semibold">
            {symbol ? `${symbol} 가격 차트` : "가격 차트"}
          </div>
          <div className="text-xs text-text-muted mt-0.5">
            <span className="inline-flex items-center gap-1.5 mr-3">
              <span className="w-2.5 h-2.5 rounded-full bg-green-400" />매수
            </span>
            <span className="inline-flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-red-400" />매도
            </span>
          </div>
        </div>
        {lastPrice != null && (
          <div className="text-right">
            <div className="text-xl font-bold tabular">{formatPrice(lastPrice)}</div>
          </div>
        )}
      </div>

      {/* 차트 */}
      {prices.length < 2 ? (
        <div className="h-52 flex items-center justify-center text-text-muted text-sm">
          데이터 수집 중…
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1A1C26" vertical={false} />
            <XAxis
              dataKey="label"
              tick={{ fill: "#5A5E78", fontSize: 10 }}
              tickLine={false}
              axisLine={false}
              interval="preserveStartEnd"
            />
            <YAxis
              domain={[minP, maxP]}
              tick={{ fill: "#5A5E78", fontSize: 10 }}
              tickLine={false}
              axisLine={false}
              tickFormatter={formatPrice}
              width={72}
            />
            <Tooltip content={<CustomTooltip />} />
            <Line
              type="monotone"
              dataKey="price"
              stroke="#3B82F6"
              strokeWidth={2}
              dot={<SignalDot />}
              activeDot={{ r: 4, fill: "#3B82F6" }}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
