"use client";

import { useCallback, useEffect, useState } from "react";
import { useBotStatus, useHistory } from "@/lib/hooks";
import { fetchStrategyInfo } from "@/lib/api";
import type { StrategyInfo } from "@/lib/types";

import StatusHeader from "@/components/StatusHeader";
import StatCards from "@/components/StatCards";
import PriceChart from "@/components/PriceChart";
import TradeHistory from "@/components/TradeHistory";
import ControlPanel from "@/components/ControlPanel";
import StrategyPanel from "@/components/StrategyPanel";
import ConfigPanel from "@/components/ConfigPanel";

export default function DashboardPage() {
  const { data: status, isLoading: statusLoading, mutate: mutateStatus } = useBotStatus();
  const { data: history, mutate: mutateHistory } = useHistory();
  const [strategyInfo, setStrategyInfo] = useState<StrategyInfo | undefined>(undefined);

  const refreshAll = useCallback(() => {
    mutateStatus();
    mutateHistory();
    fetchStrategyInfo()
      .then((s) => setStrategyInfo(s))
      .catch(() => {});
  }, [mutateStatus, mutateHistory]);

  // Load strategy info on mount and after status loads
  useEffect(() => {
    fetchStrategyInfo()
      .then((s) => setStrategyInfo(s))
      .catch(() => {});
  }, [status?.running]);

  return (
    <div
      className="min-h-screen"
      style={{ background: "var(--bg)", color: "var(--fg)" }}
    >
      {/* Sticky header */}
      <StatusHeader status={status} isLoading={statusLoading} />

      {/* Main content */}
      <main className="max-w-screen-xl mx-auto px-4 pb-10 pt-6 space-y-5">
        {/* Stat cards row */}
        <StatCards status={status} />

        {/* 2-column layout */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
          {/* Left: chart + trade history (2/3 width) */}
          <div className="xl:col-span-2 space-y-5">
            <PriceChart
              prices={history?.prices ?? []}
              symbol={status?.symbol}
              lastPrice={status?.last_price}
            />
            <TradeHistory trades={history?.trades ?? []} />
          </div>

          {/* Right: control panels (1/3 width) */}
          <div className="space-y-5">
            <ControlPanel status={status} onRefresh={refreshAll} />
            <StrategyPanel
              status={status}
              strategyInfo={strategyInfo}
              onRefresh={refreshAll}
            />
            <ConfigPanel status={status} onRefresh={refreshAll} />
          </div>
        </div>
      </main>
    </div>
  );
}
