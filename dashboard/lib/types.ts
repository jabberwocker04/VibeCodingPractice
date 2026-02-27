// Python LiveBotStatus 데이터클래스와 1:1 매핑

export interface BotStatus {
  running: boolean;
  paused: boolean;
  symbol: string;
  company_name: string;
  strategy: string;
  interval: string;
  trades: number;
  cash: number;
  position_qty: number;
  last_price: number;
  equity: number;
  pnl: number;
  pnl_pct: number;
  last_signal: "buy" | "sell" | "hold";
  last_tick_at: string;
  loop_count: number;
  started_at_utc: string;
  last_error: string;
}

export interface PricePoint {
  ts: string;
  price: number;
  equity: number;
  pnl: number;
  signal: "buy" | "sell" | "hold";
}

export interface TradeRecord {
  ts: string;
  side: "buy" | "sell";
  price: number;
  qty: number;
  symbol: string;
}

export interface HistoryData {
  prices: PricePoint[];
  trades: TradeRecord[];
}

export interface StrategyInfo {
  name: string;
  params: Record<string, number>;
}

export interface TradingConfig {
  quantity: number;
  max_position_qty: number;
  tick_seconds: number;
  interval: string;
  history_period: string;
}

export interface StrategyCatalog {
  names: string[];
  descriptions: Record<string, string>;
  defaults: Record<string, Record<string, number>>;
}
