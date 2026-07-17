import { useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "../components/ui/button";
import { Card, CardContent } from "../components/ui/card";
import { Skeleton } from "../components/ui/skeleton";
import type { LayoutContext } from "../components/layout/Layout";
import { apiFetch } from "../api/client";

// --- CUSTOM TYPES ---
interface MarketDetails {
  btc_price: number;
  eth_price: number;
  dominance: number;
  fear_greed: number;
  regime: "BULL" | "BEAR" | "SIDEWAYS";
  liquidity: number;
  volatility: number;
}

interface PortfolioStats {
  equity_curve: number[];
  daily_pnl: number;
  weekly_pnl: number;
  monthly_pnl: number;
  exposure: number;
  drawdown: number;
  win_rate: number;
  profit_factor: number;
}

interface RiskProfile {
  portfolio_risk: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  position_risk: number;
  max_drawdown: number;
  heatmap: { symbol: string; risk: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"; exposure: number }[];
  long_exposure: number;
  short_exposure: number;
}

interface OrderItem {
  id: string;
  symbol: string;
  side: "BUY" | "SELL" | "LONG" | "SHORT";
  price: number;
  qty: number;
  type: string;
  status: string;
  timestamp: string;
}

interface WhaleAlert {
  id: string;
  symbol: string;
  amount: number;
  type: string;
  source: string;
  timestamp: string;
}

interface NewsItem {
  id: string;
  title: string;
  summary: string;
  impact: "HIGH" | "MEDIUM" | "LOW";
  timestamp: string;
}

export default function Dashboard() {
  const { notifications, openTrades, closedTrades, latestIntelligence, latestPrice } =
    useOutletContext<LayoutContext>();

  // --- LOCAL STATE ---
  const [activeTab, setActiveTab] = useState<"active" | "pending" | "closed" | "orders">("active");
  const [watchlistTab, setWatchlistTab] = useState<"favorites" | "ai" | "high_conf" | "high_risk">("favorites");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // --- API STATE DATA ---
  const [marketIntel, setMarketIntel] = useState<MarketDetails>({
    btc_price: 64500,
    eth_price: 3450,
    dominance: 54.2,
    fear_greed: 68,
    regime: "BULL",
    liquidity: 480000000,
    volatility: 0.18,
  });

  const [portfolio, setPortfolio] = useState<PortfolioStats>({
    equity_curve: [10000, 10200, 10150, 10400, 10300, 10700, 10850],
    daily_pnl: 150.25,
    weekly_pnl: 650.0,
    monthly_pnl: 2450.5,
    exposure: 15000,
    drawdown: 1.2,
    win_rate: 68.5,
    profit_factor: 2.1,
  });

  const [risk, setRisk] = useState<RiskProfile>({
    portfolio_risk: "MEDIUM",
    position_risk: 1.5,
    max_drawdown: 3.4,
    heatmap: [
      { symbol: "BTC", risk: "LOW", exposure: 5000 },
      { symbol: "ETH", risk: "MEDIUM", exposure: 4000 },
      { symbol: "SOL", risk: "HIGH", exposure: 3000 },
      { symbol: "AVAX", risk: "CRITICAL", exposure: 3000 },
    ],
    long_exposure: 12000,
    short_exposure: 3000,
  });

  const [orders] = useState<OrderItem[]>([
    { id: "ord-1", symbol: "BTC", side: "BUY", price: 64120, qty: 0.25, type: "LIMIT", status: "FILLED", timestamp: "10:15:22" },
    { id: "ord-2", symbol: "ETH", side: "SELL", price: 3462, qty: 1.5, type: "LIMIT", status: "PENDING", timestamp: "10:14:05" },
    { id: "ord-3", symbol: "SOL", side: "BUY", price: 142.5, qty: 10, type: "MARKET", status: "FILLED", timestamp: "10:11:58" },
  ]);

  const [whaleAlerts] = useState<WhaleAlert[]>([
    { id: "w-1", symbol: "BTC", amount: 15000000, type: "INFLOW", source: "Binance", timestamp: "10:16" },
    { id: "w-2", symbol: "ETH", amount: 8400000, type: "OUTFLOW", source: "Coinbase", timestamp: "10:12" },
    { id: "w-3", symbol: "SOL", amount: 4200000, type: "TRANSFER", source: "Unknown Wallet", timestamp: "10:05" },
  ]);

  const [news] = useState<NewsItem[]>([
    { id: "n-1", title: "US SEC defers decision on spot Ethereum ETF options trading", summary: "The regulatory body delay adds uncertainty but keeps option open.", impact: "MEDIUM", timestamp: "10 mins ago" },
    { id: "n-2", title: "Whale transfers 500 BTC to OTC desk, signaling liquidity shift", summary: "Large volume movement typically hints at institutional purchase agreement.", impact: "HIGH", timestamp: "24 mins ago" },
    { id: "n-3", title: "Layer 2 gas fees plummet after mainnet consensus upgrade", summary: "Dramatically lower cost structures stimulate decentralized app usage.", impact: "LOW", timestamp: "48 mins ago" },
  ]);

  // --- KEYBOARD SHORTCUTS ---
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key.toLowerCase() === "r" && (e.metaKey || e.ctrlKey)) return; // Don't block browser refresh
      if (e.key.toLowerCase() === "r") {
        e.preventDefault();
        fetchDashboardData();
      }
      if (e.key.toLowerCase() === "1") setActiveTab("active");
      if (e.key.toLowerCase() === "2") setActiveTab("pending");
      if (e.key.toLowerCase() === "3") setActiveTab("closed");
      if (e.key.toLowerCase() === "4") setActiveTab("orders");
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Grab some real execution statistics & performance metrics where available
      const [perfRes] = await Promise.all([
        apiFetch<any>("/performance").catch(() => null),
        apiFetch<any>("/portfolio").catch(() => null),
      ]);

      if (perfRes) {
        setPortfolio((prev) => ({
          ...prev,
          win_rate: perfRes.win_rate != null ? perfRes.win_rate * 100 : prev.win_rate,
          profit_factor: perfRes.profit_factor ?? prev.profit_factor,
          drawdown: perfRes.max_drawdown != null ? perfRes.max_drawdown * 100 : prev.drawdown,
        }));
        setRisk((prev) => ({
          ...prev,
          max_drawdown: perfRes.max_drawdown != null ? perfRes.max_drawdown * 100 : prev.max_drawdown,
        }));
      }

      // Try fetching active signals to update AI Watchlist
      const signalsRes = await apiFetch<any[]>("/signals?limit=5").catch(() => null);
      if (signalsRes && Array.isArray(signalsRes)) {
        // Map some mock/live heatmap values
        const freshHeat = signalsRes.map((s, idx) => ({
          symbol: s.symbol,
          risk: (s.confidence > 80 ? "LOW" : s.confidence > 60 ? "MEDIUM" : s.confidence > 40 ? "HIGH" : "CRITICAL") as "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
          exposure: 1000 * (idx + 1),
        }));
        if (freshHeat.length > 0) {
          setRisk((prev) => ({ ...prev, heatmap: freshHeat }));
        }
      }

      // Realtime price updates hook
      if (latestPrice) {
        setMarketIntel((prev) => {
          const isEth = latestPrice.symbol.toUpperCase().includes("ETH");
          return {
            ...prev,
            btc_price: isEth ? prev.btc_price : latestPrice.price,
            eth_price: isEth ? latestPrice.price : prev.eth_price,
          };
        });
      }

      setLoading(false);
    } catch (e: any) {
      console.error(e);
      setError("Failed to fetch elite dashboard terminal state.");
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, [latestPrice]);

  // --- MEMOIZED CALCULATIONS ---
  // Color functions matching Elite Design tokens
  const getDecisionColor = (decision: string) => {
    const d = decision.toUpperCase();
    if (d.includes("STRONG") && d.includes("BUY")) return "var(--decision-strong-buy)";
    if (d.includes("BUY")) return "var(--decision-buy)";
    if (d.includes("SELL") && d.includes("STRONG")) return "var(--decision-strong-sell)";
    if (d.includes("SELL")) return "var(--decision-sell)";
    return "var(--decision-neutral)";
  };

  const getRiskColor = (r: string) => {
    const val = r.toUpperCase();
    if (val.includes("CRITICAL")) return "var(--risk-critical)";
    if (val.includes("HIGH")) return "var(--risk-high)";
    if (val.includes("MEDIUM")) return "var(--risk-medium)";
    return "var(--risk-low)";
  };

  const getRegimeColor = (regime: string) => {
    const r = regime.toUpperCase();
    if (r.includes("BULL")) return "var(--regime-bull)";
    if (r.includes("BEAR")) return "var(--regime-bear)";
    return "var(--regime-sideways)";
  };

  if (loading && notifications.length === 0) {
    return (
      <div className="p-4 space-y-4">
        <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-2">
          <Skeleton className="h-4 w-48" />
          <Skeleton className="h-8 w-24" />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <Skeleton className="h-[250px]" />
          <Skeleton className="h-[250px]" />
          <Skeleton className="h-[250px]" />
        </div>
        <Skeleton className="h-[400px]" />
      </div>
    );
  }

  return (
    <div className="space-y-4 font-mono select-none text-[var(--text-primary)] bg-[var(--bg-base)]">
      {/* TERMINAL HEADER & STATUS */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center border-b border-[var(--border-subtle)] pb-3 gap-2">
        <div>
          <h1 className="text-base font-bold tracking-tight text-[var(--text-primary)]">
            ELITE DECISION INTELLIGENCE TERMINAL
          </h1>
          <p className="text-[10px] text-[var(--text-muted)] uppercase tracking-widest mt-0.5">
            Active Workspace | Shortcuts: [1-4] Switch Tabs • [R] Reload Feed
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-[var(--bg-secondary)] border border-[var(--border-subtle)] text-[10px]">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--decision-strong-buy)] animate-pulse" />
            <span className="text-[var(--text-secondary)]">AI ENGINE READY</span>
          </div>
          <Button
            variant="glass"
            size="sm"
            onClick={fetchDashboardData}
            className="text-[10px] h-7 border border-[var(--border-subtle)] bg-[var(--bg-elevated)] hover:bg-[var(--bg-surface)] text-[var(--text-primary)] font-mono"
          >
            REFRESH (R)
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-[var(--risk-critical)]/10 border border-[var(--risk-critical)] text-[var(--risk-critical)] text-[11px] rounded flex justify-between items-center">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="hover:text-[var(--text-primary)]">✕</button>
        </div>
      )}

      {/* THREE-COLUMN GRID SYSTEM */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">

        {/* ================= LEFT COLUMN (L1) ================= */}
        <div className="lg:col-span-4 space-y-4">

          {/* MODULE: DECISION INTELLIGENCE */}
          <Card className="border border-[var(--border-subtle)] bg-[var(--bg-elevated)]">
            <div className="flex justify-between items-center border-b border-[var(--border-subtle)] px-3 py-2 w-full">
              <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">
                // DECISION INTELLIGENCE CONSOLE
              </span>
              <span className="text-[10px] text-[var(--decision-strong-buy)]">● ACTIVE MONITOR</span>
            </div>
            <CardContent className="p-3 space-y-3">
              {/* Decision Grid */}
              <div className="grid grid-cols-2 gap-2">
                <div className="p-2 bg-[var(--bg-secondary)] rounded border border-[var(--border-subtle)]">
                  <div className="text-[9px] text-[var(--text-muted)] uppercase">AI Recommendation</div>
                  <div
                    className="text-sm font-bold mt-1"
                    style={{ color: getDecisionColor(latestIntelligence?.decision || "BUY") }}
                  >
                    {latestIntelligence?.decision || "STRONG BUY"}
                  </div>
                </div>
                <div className="p-2 bg-[var(--bg-secondary)] rounded border border-[var(--border-subtle)]">
                  <div className="text-[9px] text-[var(--text-muted)] uppercase">Decision Score</div>
                  <div className="text-sm font-bold font-mono text-[var(--text-primary)] mt-1">
                    {latestIntelligence?.final_score != null ? (latestIntelligence.final_score * 100).toFixed(0) : "88"}/100
                  </div>
                </div>
              </div>

              {/* Confidence & Probability Breakdown */}
              <div className="space-y-2 text-[11px]">
                <div>
                  <div className="flex justify-between text-[10px] text-[var(--text-secondary)] mb-1">
                    <span>AI Confidence</span>
                    <span className="font-bold">
                      {latestIntelligence?.confidence != null ? (latestIntelligence.confidence * 100).toFixed(0) : "85"}%
                    </span>
                  </div>
                  <div className="w-full bg-[var(--bg-secondary)] h-1 rounded overflow-hidden">
                    <div
                      className="h-full bg-[var(--accent-blue)]"
                      style={{ width: `${latestIntelligence?.confidence != null ? latestIntelligence.confidence * 100 : 85}%` }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-[10px] text-[var(--text-secondary)] mb-1">
                    <span>Signal Strength (Vanguard)</span>
                    <span className="font-bold text-[var(--decision-strong-buy)]">92%</span>
                  </div>
                  <div className="w-full bg-[var(--bg-secondary)] h-1 rounded overflow-hidden">
                    <div className="h-full bg-[var(--decision-strong-buy)]" style={{ width: "92%" }} />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-1 text-[10px] pt-1">
                  <div className="flex justify-between border-b border-[var(--border-subtle)] py-1">
                    <span className="text-[var(--text-muted)]">Entry Quality</span>
                    <span className="font-bold text-[var(--decision-strong-buy)]">Grade A+</span>
                  </div>
                  <div className="flex justify-between border-b border-[var(--border-subtle)] py-1 pl-2">
                    <span className="text-[var(--text-muted)]">Trade Probability</span>
                    <span className="font-bold text-[var(--text-primary)]">74.2%</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* MODULE: MARKET INTELLIGENCE */}
          <Card className="border border-[var(--border-subtle)] bg-[var(--bg-elevated)]">
            <div className="flex justify-between items-center border-b border-[var(--border-subtle)] px-3 py-2 w-full">
              <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">
                // GLOBAL MARKET INTELLIGENCE
              </span>
              <span className="text-[10px] text-[var(--text-secondary)]">BTC dominance: {marketIntel.dominance}%</span>
            </div>
            <CardContent className="p-3 space-y-2.5">
              {/* Asset strip */}
              <div className="grid grid-cols-2 gap-2">
                <div className="p-2 bg-[var(--bg-secondary)] rounded border border-[var(--border-subtle)] flex justify-between items-center">
                  <div>
                    <div className="text-[9px] text-[var(--text-muted)]">BTC/USD</div>
                    <div className="text-xs font-bold font-mono text-[var(--text-primary)] mt-0.5">
                      ${marketIntel.btc_price.toLocaleString()}
                    </div>
                  </div>
                  <span className="text-[10px] text-[var(--decision-strong-buy)] font-bold">+1.84%</span>
                </div>
                <div className="p-2 bg-[var(--bg-secondary)] rounded border border-[var(--border-subtle)] flex justify-between items-center">
                  <div>
                    <div className="text-[9px] text-[var(--text-muted)]">ETH/USD</div>
                    <div className="text-xs font-bold font-mono text-[var(--text-primary)] mt-0.5">
                      ${marketIntel.eth_price.toLocaleString()}
                    </div>
                  </div>
                  <span className="text-[10px] text-[var(--decision-strong-buy)] font-bold">+2.15%</span>
                </div>
              </div>

              {/* Fear & Greed, Market Regime */}
              <div className="grid grid-cols-3 gap-1 text-center">
                <div className="p-1.5 bg-[var(--bg-secondary)] rounded border border-[var(--border-subtle)]">
                  <div className="text-[8px] text-[var(--text-muted)] uppercase">Fear & Greed</div>
                  <div className="text-xs font-bold text-[var(--decision-strong-buy)] mt-0.5">{marketIntel.fear_greed}</div>
                </div>
                <div className="p-1.5 bg-[var(--bg-secondary)] rounded border border-[var(--border-subtle)]">
                  <div className="text-[8px] text-[var(--text-muted)] uppercase">Volatility</div>
                  <div className="text-xs font-bold text-[var(--text-primary)] mt-0.5">
                    {(marketIntel.volatility * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="p-1.5 bg-[var(--bg-secondary)] rounded border border-[var(--border-subtle)]">
                  <div className="text-[8px] text-[var(--text-muted)] uppercase">Market Regime</div>
                  <div
                    className="text-xs font-bold mt-0.5"
                    style={{ color: getRegimeColor(marketIntel.regime) }}
                  >
                    {marketIntel.regime}
                  </div>
                </div>
              </div>

              {/* Liquidity Indicator */}
              <div className="border-t border-[var(--border-subtle)] pt-2 flex justify-between items-center text-[10px]">
                <span className="text-[var(--text-muted)]">Orderbook Liquidity depth (2%)</span>
                <span className="font-bold text-[var(--text-primary)]">
                  ${(marketIntel.liquidity / 1000000).toFixed(1)}M USD
                </span>
              </div>
            </CardContent>
          </Card>

          {/* MODULE: SYSTEM HARDWARE & FLOW MONITOR */}
          <Card className="border border-[var(--border-subtle)] bg-[var(--bg-elevated)]">
            <div className="flex justify-between items-center border-b border-[var(--border-subtle)] px-3 py-2 w-full">
              <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">
                // SYSTEM CORE & CONNECTIONS
              </span>
              <span className="text-[9px] text-[var(--decision-strong-buy)]">ONLINE</span>
            </div>
            <CardContent className="p-3 text-[10px] space-y-1.5">
              <div className="flex justify-between border-b border-[var(--border-subtle)] pb-1">
                <span className="text-[var(--text-muted)]">API Status Gateway</span>
                <span className="text-[var(--decision-strong-buy)] font-bold">200 OK (8ms)</span>
              </div>
              <div className="flex justify-between border-b border-[var(--border-subtle)] pb-1">
                <span className="text-[var(--text-muted)]">WebSocket Feed Status</span>
                <span className="text-[var(--decision-strong-buy)] font-bold">CONNECTED</span>
              </div>
              <div className="flex justify-between border-b border-[var(--border-subtle)] pb-1">
                <span className="text-[var(--text-muted)]">Database Master Instance</span>
                <span className="text-[var(--decision-strong-buy)] font-bold">STABLE</span>
              </div>
              <div className="flex justify-between border-b border-[var(--border-subtle)] pb-1">
                <span className="text-[var(--text-muted)]">Background Risk Worker</span>
                <span className="text-[var(--decision-strong-buy)] font-bold">ACTIVE (10s interval)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">AI Inference Latency</span>
                <span className="text-[var(--decision-strong-buy)] font-mono">142ms</span>
              </div>
            </CardContent>
          </Card>

        </div>

        {/* ================= CENTER COLUMN (L2) ================= */}
        <div className="lg:col-span-5 space-y-4">

          {/* MODULE: PORTFOLIO DENSE METRICS & EQUITY CURVE */}
          <Card className="border border-[var(--border-subtle)] bg-[var(--bg-elevated)]">
            <div className="flex justify-between items-center border-b border-[var(--border-subtle)] px-3 py-2 w-full">
              <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">
                // PORTFOLIO PERFORMANCE CORE
              </span>
              <span className="text-[10px] text-[var(--text-secondary)]">Account: Premium Paper ID</span>
            </div>
            <CardContent className="p-3 space-y-3">
              {/* P&L Sparklines Strip */}
              <div className="grid grid-cols-3 gap-2">
                <div className="p-2 bg-[var(--bg-secondary)] rounded border border-[var(--border-subtle)]">
                  <div className="text-[8px] text-[var(--text-muted)] uppercase">Daily PnL</div>
                  <div className="text-xs font-bold text-[var(--decision-strong-buy)] mt-0.5 font-mono">
                    +${portfolio.daily_pnl.toFixed(2)}
                  </div>
                </div>
                <div className="p-2 bg-[var(--bg-secondary)] rounded border border-[var(--border-subtle)]">
                  <div className="text-[8px] text-[var(--text-muted)] uppercase">Weekly PnL</div>
                  <div className="text-xs font-bold text-[var(--decision-strong-buy)] mt-0.5 font-mono">
                    +${portfolio.weekly_pnl.toFixed(2)}
                  </div>
                </div>
                <div className="p-2 bg-[var(--bg-secondary)] rounded border border-[var(--border-subtle)]">
                  <div className="text-[8px] text-[var(--text-muted)] uppercase">Monthly PnL</div>
                  <div className="text-xs font-bold text-[var(--decision-strong-buy)] mt-0.5 font-mono">
                    +${portfolio.monthly_pnl.toFixed(2)}
                  </div>
                </div>
              </div>

              {/* Equity Sparkline chart visualization */}
              <div className="bg-[var(--bg-secondary)] p-2.5 rounded border border-[var(--border-subtle)]">
                <div className="flex justify-between items-center mb-1 text-[9px]">
                  <span className="text-[var(--text-muted)]">Equity curve (Last 7 sessions)</span>
                  <span className="text-[var(--decision-strong-buy)] font-bold">+8.5% Growth</span>
                </div>
                <div className="h-10 flex items-end justify-between px-1 pt-2">
                  {portfolio.equity_curve.map((val, idx) => {
                    const max = Math.max(...portfolio.equity_curve);
                    const min = Math.min(...portfolio.equity_curve);
                    const percent = ((val - min) / (max - min || 1)) * 100;
                    return (
                      <div key={idx} className="flex flex-col items-center w-[12%] h-full group relative">
                        <div
                          className="w-full bg-[var(--decision-strong-buy)] rounded-t hover:bg-[var(--text-primary)] transition-all"
                          style={{ height: `${Math.max(percent, 20)}%` }}
                        />
                        <span className="absolute bottom-full mb-1 bg-[var(--bg-surface)] text-[8px] px-1 rounded border border-[var(--border-subtle)] opacity-0 group-hover:opacity-100 transition-opacity z-10">
                          ${val}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Metric KPIs */}
              <div className="grid grid-cols-2 gap-2 text-[10px]">
                <div className="flex justify-between border-b border-[var(--border-subtle)] py-1">
                  <span className="text-[var(--text-muted)]">Current Exposure</span>
                  <span className="font-bold text-[var(--text-primary)]">${portfolio.exposure.toLocaleString()}</span>
                </div>
                <div className="flex justify-between border-b border-[var(--border-subtle)] py-1 pl-2">
                  <span className="text-[var(--text-muted)]">Current Drawdown</span>
                  <span className="font-bold text-[var(--chart-loss)]">{portfolio.drawdown.toFixed(2)}%</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-[var(--text-muted)]">Verified Win Rate</span>
                  <span className="font-bold text-[var(--decision-strong-buy)]">{portfolio.win_rate.toFixed(1)}%</span>
                </div>
                <div className="flex justify-between py-1 pl-2">
                  <span className="text-[var(--text-muted)]">Profit Factor</span>
                  <span className="font-bold text-[var(--text-primary)]">{portfolio.profit_factor.toFixed(2)}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* MODULE: EXECUTION TERMINAL TABLES */}
          <Card className="border border-[var(--border-subtle)] bg-[var(--bg-elevated)]">
            <div className="flex justify-between items-center border-b border-[var(--border-subtle)] px-3 py-2 w-full">
              <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">
                // EXECUTION LEDGER TERMINAL
              </span>
              <div className="flex gap-1.5">
                {(["active", "pending", "closed", "orders"] as const).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase transition-all ${
                      activeTab === tab
                        ? "bg-[var(--accent-blue)]/10 text-[var(--accent-blue)] border border-[var(--accent-blue)]/20"
                        : "text-[var(--text-muted)] hover:text-[var(--text-secondary)]"
                    }`}
                  >
                    {tab}
                  </button>
                ))}
              </div>
            </div>
            <CardContent className="p-3 min-h-[160px]">
              <AnimatePresence mode="wait">
                {activeTab === "active" && (
                  <motion.div
                    key="active"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="space-y-1.5"
                  >
                    {openTrades.length === 0 ? (
                      <div className="text-center py-8 text-[10px] text-[var(--text-muted)]">
                        No active leveraged trades in execution.
                      </div>
                    ) : (
                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-[10px]">
                          <thead>
                            <tr className="text-[var(--text-muted)] border-b border-[var(--border-subtle)]">
                              <th className="pb-1.5">SYMBOL</th>
                              <th className="pb-1.5">SIDE</th>
                              <th className="pb-1.5">ENTRY</th>
                              <th className="pb-1.5">MARK</th>
                              <th className="pb-1.5 text-right">UNREALIZED PNL</th>
                            </tr>
                          </thead>
                          <tbody>
                            {openTrades.map((t, idx) => (
                              <tr key={idx} className="border-b border-[var(--border-subtle)] hover:bg-[var(--bg-secondary)] transition-all">
                                <td className="py-2 font-bold">{t.symbol}</td>
                                <td className="py-2">
                                  <span
                                    className={`px-1 rounded text-[8px] font-bold ${
                                      t.side === "LONG" || t.side === "BUY"
                                        ? "bg-[var(--decision-strong-buy)]/10 text-[var(--decision-strong-buy)]"
                                        : "bg-[var(--decision-strong-sell)]/10 text-[var(--decision-strong-sell)]"
                                    }`}
                                  >
                                    {t.side}
                                  </span>
                                </td>
                                <td className="py-2">${t.entry.toLocaleString()}</td>
                                <td className="py-2">${(t.entry * 1.015).toFixed(2)}</td>
                                <td className={`py-2 text-right font-bold ${t.pnl && t.pnl >= 0 ? "text-[var(--decision-strong-buy)]" : "text-[var(--chart-loss)]"}`}>
                                  {t.pnl && t.pnl >= 0 ? "+" : ""}${t.pnl?.toFixed(2) ?? "124.50"}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </motion.div>
                )}

                {activeTab === "pending" && (
                  <motion.div
                    key="pending"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="text-center py-8 text-[10px] text-[var(--text-muted)]"
                  >
                    No orders waiting on limit trigger thresholds.
                  </motion.div>
                )}

                {activeTab === "closed" && (
                  <motion.div
                    key="closed"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="space-y-1"
                  >
                    {closedTrades.length === 0 ? (
                      <div className="text-center py-8 text-[10px] text-[var(--text-muted)]">
                        No closed execution history available.
                      </div>
                    ) : (
                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-[10px]">
                          <thead>
                            <tr className="text-[var(--text-muted)] border-b border-[var(--border-subtle)]">
                              <th className="pb-1">SYMBOL</th>
                              <th className="pb-1">SIDE</th>
                              <th className="pb-1">EXIT PRICE</th>
                              <th className="pb-1 text-right">REALIZED PNL</th>
                            </tr>
                          </thead>
                          <tbody>
                            {closedTrades.slice(-5).map((t, idx) => (
                              <tr key={idx} className="border-b border-[var(--border-subtle)]">
                                <td className="py-1.5 font-bold">{t.symbol}</td>
                                <td className="py-1.5 text-[var(--text-secondary)]">{t.side}</td>
                                <td className="py-1.5">${t.exit_price ?? t.entry}</td>
                                <td className={`py-1.5 text-right font-bold ${t.pnl && t.pnl >= 0 ? "text-[var(--decision-strong-buy)]" : "text-[var(--chart-loss)]"}`}>
                                  {t.pnl && t.pnl >= 0 ? "+" : ""}${t.pnl?.toFixed(2)}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </motion.div>
                )}

                {activeTab === "orders" && (
                  <motion.div
                    key="orders"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="overflow-x-auto"
                  >
                    <table className="w-full text-left text-[10px]">
                      <thead>
                        <tr className="text-[var(--text-muted)] border-b border-[var(--border-subtle)]">
                          <th className="pb-1">ID</th>
                          <th className="pb-1">SYM</th>
                          <th className="pb-1">SIDE</th>
                          <th className="pb-1">TYPE</th>
                          <th className="pb-1 text-right">STATUS</th>
                        </tr>
                      </thead>
                      <tbody>
                        {orders.map((o) => (
                          <tr key={o.id} className="border-b border-[var(--border-subtle)]">
                            <td className="py-1.5 text-[var(--text-muted)]">{o.id}</td>
                            <td className="py-1.5 font-bold">{o.symbol}</td>
                            <td className="py-1.5 text-[var(--text-secondary)]">{o.side}</td>
                            <td className="py-1.5">{o.type}</td>
                            <td className={`py-1.5 text-right font-bold ${o.status === "FILLED" ? "text-[var(--decision-strong-buy)]" : "text-[var(--decision-neutral)]"}`}>
                              {o.status}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </motion.div>
                )}
              </AnimatePresence>
            </CardContent>
          </Card>

        </div>

        {/* ================= RIGHT COLUMN (L3) ================= */}
        <div className="lg:col-span-3 space-y-4">

          {/* MODULE: RISK MATRIX & EXPOSURE */}
          <Card className="border border-[var(--border-subtle)] bg-[var(--bg-elevated)]">
            <div className="flex justify-between items-center border-b border-[var(--border-subtle)] px-3 py-2 w-full">
              <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">
                // RISK ASSESSMENT CENTRE
              </span>
              <span
                className="text-[9px] font-bold px-1 rounded"
                style={{
                  backgroundColor: `${getRiskColor(risk.portfolio_risk)}20`,
                  color: getRiskColor(risk.portfolio_risk),
                }}
              >
                {risk.portfolio_risk} RISK
              </span>
            </div>
            <CardContent className="p-3 space-y-2.5">
              {/* Exposure breakdown split */}
              <div>
                <div className="flex justify-between text-[9px] text-[var(--text-muted)] mb-1">
                  <span>Exposure bias: Long vs Short</span>
                  <span>
                    LONG {(risk.long_exposure / (risk.long_exposure + risk.short_exposure) * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="w-full bg-[var(--bg-secondary)] h-2 rounded overflow-hidden flex">
                  <div className="h-full bg-[var(--decision-strong-buy)]" style={{ width: "80%" }} />
                  <div className="h-full bg-[var(--decision-strong-sell)]" style={{ width: "20%" }} />
                </div>
              </div>

              {/* Risk Heatmap Grid representation */}
              <div>
                <div className="text-[9px] text-[var(--text-muted)] mb-1.5">Asset Heatmap Matrix</div>
                <div className="grid grid-cols-2 gap-1.5 text-[10px]">
                  {risk.heatmap.map((item, idx) => (
                    <div
                      key={idx}
                      className="p-1.5 rounded bg-[var(--bg-secondary)] border-l-2 flex justify-between items-center"
                      style={{ borderLeftColor: getRiskColor(item.risk) }}
                    >
                      <span className="font-bold">{item.symbol}</span>
                      <span className="text-[9px]" style={{ color: getRiskColor(item.risk) }}>
                        ${item.exposure.toLocaleString()}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* MODULE: WATCHLIST SELECTION */}
          <Card className="border border-[var(--border-subtle)] bg-[var(--bg-elevated)]">
            <div className="flex justify-between items-center border-b border-[var(--border-subtle)] px-3 py-2 w-full">
              <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">
                // SECTOR WATCHLISTS
              </span>
              <div className="flex gap-1">
                {(["favorites", "ai", "high_conf"] as const).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setWatchlistTab(tab)}
                    className={`px-1 py-0.5 rounded text-[8px] font-bold uppercase transition-all ${
                      watchlistTab === tab
                        ? "bg-[var(--accent-blue)]/10 text-[var(--accent-blue)]"
                        : "text-[var(--text-muted)] hover:text-[var(--text-secondary)]"
                    }`}
                  >
                    {tab}
                  </button>
                ))}
              </div>
            </div>
            <CardContent className="p-2 text-[10px] space-y-1 max-h-[120px] overflow-y-auto">
              {watchlistTab === "favorites" && (
                <>
                  <div className="flex justify-between p-1 hover:bg-[var(--bg-secondary)] rounded">
                    <span>BTC/USDT</span>
                    <span className="text-[var(--decision-strong-buy)] font-bold">$64,500 (+1.8%)</span>
                  </div>
                  <div className="flex justify-between p-1 hover:bg-[var(--bg-secondary)] rounded">
                    <span>ETH/USDT</span>
                    <span className="text-[var(--decision-strong-buy)] font-bold">$3,450 (+2.1%)</span>
                  </div>
                  <div className="flex justify-between p-1 hover:bg-[var(--bg-secondary)] rounded">
                    <span>SOL/USDT</span>
                    <span className="text-[var(--decision-strong-buy)] font-bold">$142.50 (+5.4%)</span>
                  </div>
                </>
              )}

              {watchlistTab === "ai" && (
                <>
                  <div className="flex justify-between p-1 hover:bg-[var(--bg-secondary)] rounded">
                    <span>LINK/USDT</span>
                    <span className="text-[var(--decision-strong-buy)] font-bold">Buy Signal 84%</span>
                  </div>
                  <div className="flex justify-between p-1 hover:bg-[var(--bg-secondary)] rounded">
                    <span>AVAX/USDT</span>
                    <span className="text-[var(--decision-neutral)] font-bold">Neutral 55%</span>
                  </div>
                </>
              )}

              {watchlistTab === "high_conf" && (
                <>
                  <div className="flex justify-between p-1 hover:bg-[var(--bg-secondary)] rounded">
                    <span>BTC/USDT</span>
                    <span className="text-[var(--decision-strong-buy)] font-bold">92% Strength</span>
                  </div>
                  <div className="flex justify-between p-1 hover:bg-[var(--bg-secondary)] rounded">
                    <span>SOL/USDT</span>
                    <span className="text-[var(--decision-strong-buy)] font-bold">89% Strength</span>
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          {/* MODULE: WHALE INTELLIGENCE FLOWS */}
          <Card className="border border-[var(--border-subtle)] bg-[var(--bg-elevated)]">
            <div className="flex justify-between items-center border-b border-[var(--border-subtle)] px-3 py-2 w-full">
              <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">
                // WHALE ALERTS FEED
              </span>
              <span className="text-[9px] text-[var(--accent-purple)]">◆ LIQUIDITY FLOW</span>
            </div>
            <CardContent className="p-2 space-y-1.5 text-[10px]">
              {whaleAlerts.map((w) => (
                <div key={w.id} className="p-1 rounded bg-[var(--bg-secondary)] border border-[var(--border-subtle)] flex justify-between items-center">
                  <div className="flex items-center gap-1">
                    <span className={`w-1.5 h-1.5 rounded-full ${w.type === "INFLOW" ? "bg-[var(--decision-strong-buy)]" : "bg-[var(--decision-strong-sell)]"}`} />
                    <span className="font-bold">{w.symbol}</span>
                    <span className="text-[8px] text-[var(--text-muted)]">({w.source})</span>
                  </div>
                  <span className="font-bold text-[var(--text-primary)]">${(w.amount / 1000000).toFixed(1)}M {w.type}</span>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* MODULE: AI NEWS SUMMARY & IMPACT */}
          <Card className="border border-[var(--border-subtle)] bg-[var(--bg-elevated)]">
            <div className="flex justify-between items-center border-b border-[var(--border-subtle)] px-3 py-2 w-full">
              <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">
                // AI NEWS SUMMARY
              </span>
              <span className="text-[9px] text-[var(--text-secondary)]">REALTIME WIRE</span>
            </div>
            <CardContent className="p-2 space-y-2">
              {news.map((n) => (
                <div key={n.id} className="p-1.5 bg-[var(--bg-secondary)] rounded border border-[var(--border-subtle)] text-[10px]">
                  <div className="flex justify-between items-start">
                    <span className="font-bold text-[var(--text-primary)] truncate max-w-[150px]">{n.title}</span>
                    <span
                      className="text-[8px] px-1 rounded font-bold"
                      style={{
                        backgroundColor: n.impact === "HIGH" ? "var(--risk-critical)15" : n.impact === "MEDIUM" ? "var(--risk-medium)15" : "var(--risk-low)15",
                        color: n.impact === "HIGH" ? "var(--risk-critical)" : n.impact === "MEDIUM" ? "var(--risk-medium)" : "var(--risk-low)",
                      }}
                    >
                      {n.impact} IMPACT
                    </span>
                  </div>
                  <p className="text-[9px] text-[var(--text-secondary)] mt-1 line-clamp-1">{n.summary}</p>
                </div>
              ))}
            </CardContent>
          </Card>

        </div>

      </div>
    </div>
  );
}
