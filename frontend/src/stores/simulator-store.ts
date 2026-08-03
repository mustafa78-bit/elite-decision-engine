import { create } from "zustand";
import type {
  SimulatorConfig,
  SimulatorState,
  SimulatorStatus,
  MissionReport,
  SimulatedCandle,
  SimulatedDecision,
  SimulatedTrade,
  TimelineEvent,
  SimSpeed,
  AIDecisionMode,
} from "../api/simulator";

interface SimulatorStoreState {
  config: SimulatorConfig;
  state: SimulatorState | null;
  status: SimulatorStatus | null;
  report: MissionReport | null;
  candles: SimulatedCandle[];
  currentCandle: SimulatedCandle | null;
  decisions: SimulatedDecision[];
  trades: SimulatedTrade[];
  timeline: TimelineEvent[];
  selectedCandleIndex: number;
  showAIDecisionPanel: boolean;
  showManualTradingPanel: boolean;
  showExplanationPanel: boolean;
  showMissionTimeline: boolean;
  showWhaleOverlay: boolean;
  showNewsOverlay: boolean;
  showTrainingMode: boolean;
  showReport: boolean;
  showScenarios: boolean;
  showSessions: boolean;
  showFounderMode: boolean;
  loading: boolean;
  error: string | null;

  setConfig: (config: Partial<SimulatorConfig>) => void;
  setState: (state: SimulatorState | null) => void;
  setStatus: (status: SimulatorStatus | null) => void;
  setReport: (report: MissionReport | null) => void;
  addCandle: (candle: SimulatedCandle) => void;
  setCurrentCandle: (candle: SimulatedCandle | null) => void;
  addDecision: (decision: SimulatedDecision) => void;
  addTrade: (trade: SimulatedTrade) => void;
  updateTrade: (tradeId: string, updates: Partial<SimulatedTrade>) => void;
  addTimelineEvent: (event: TimelineEvent) => void;
  clearTimeline: () => void;
  setSelectedCandleIndex: (idx: number) => void;
  setShowAIDecisionPanel: (v: boolean) => void;
  setShowManualTradingPanel: (v: boolean) => void;
  setShowExplanationPanel: (v: boolean) => void;
  setShowMissionTimeline: (v: boolean) => void;
  setShowWhaleOverlay: (v: boolean) => void;
  setShowNewsOverlay: (v: boolean) => void;
  setShowTrainingMode: (v: boolean) => void;
  setShowReport: (v: boolean) => void;
  setShowScenarios: (v: boolean) => void;
  setShowSessions: (v: boolean) => void;
  setShowFounderMode: (v: boolean) => void;
  setLoading: (v: boolean) => void;
  setError: (err: string | null) => void;
  reset: () => void;
}

const DEFAULT_CONFIG: SimulatorConfig = {
  symbol: "BTC",
  timeframe: "1h",
  initial_capital: 10000,
  ai_mode: "FULL_AI" as AIDecisionMode,
  speed: "1x" as SimSpeed,
  slippage_bps: 5,
  fee_rate: 0.001,
  leverage: 1.0,
  risk_per_trade: 0.02,
  founder_mode: false,
  whale_simulation: false,
  news_replay: false,
};

export const useSimulatorStore = create<SimulatorStoreState>((set) => ({
  config: { ...DEFAULT_CONFIG },
  state: null,
  status: null,
  report: null,
  candles: [],
  currentCandle: null,
  decisions: [],
  trades: [],
  timeline: [],
  selectedCandleIndex: 0,
  showAIDecisionPanel: true,
  showManualTradingPanel: false,
  showExplanationPanel: true,
  showMissionTimeline: true,
  showWhaleOverlay: false,
  showNewsOverlay: false,
  showTrainingMode: false,
  showReport: false,
  showScenarios: false,
  showSessions: false,
  showFounderMode: false,
  loading: false,
  error: null,

  setConfig: (partial) => set((s) => ({ config: { ...s.config, ...partial } })),
  setState: (state) => set({
    state,
    trades: state?.trades ?? [],
    decisions: state?.decisions ?? [],
    timeline: state?.timeline ?? [],
    currentCandle: state?.current_timestamp
      ? { timestamp: state.current_timestamp, open: 0, high: 0, low: 0, close: state.current_price ?? 0, volume: 0 }
      : null,
  }),
  setStatus: (status) => set({ status }),
  setReport: (report) => set({ report }),

  addCandle: (candle) => set((s) => ({
    candles: [...s.candles.slice(-1000), candle],
    currentCandle: candle,
  })),

  setCurrentCandle: (candle) => set({ currentCandle: candle }),

  addDecision: (decision) => set((s) => ({
    decisions: [...s.decisions.slice(-500), decision],
  })),

  addTrade: (trade) => set((s) => ({
    trades: [...s.trades, trade],
  })),

  updateTrade: (tradeId, updates) => set((s) => ({
    trades: s.trades.map((t) => (t.id === tradeId ? { ...t, ...updates } : t)),
  })),

  addTimelineEvent: (event) => set((s) => ({
    timeline: [...s.timeline.slice(-200), event],
  })),

  clearTimeline: () => set({ timeline: [] }),

  setSelectedCandleIndex: (idx) => set({ selectedCandleIndex: idx }),
  setShowAIDecisionPanel: (v) => set({ showAIDecisionPanel: v }),
  setShowManualTradingPanel: (v) => set({ showManualTradingPanel: v }),
  setShowExplanationPanel: (v) => set({ showExplanationPanel: v }),
  setShowMissionTimeline: (v) => set({ showMissionTimeline: v }),
  setShowWhaleOverlay: (v) => set({ showWhaleOverlay: v }),
  setShowNewsOverlay: (v) => set({ showNewsOverlay: v }),
  setShowTrainingMode: (v) => set({ showTrainingMode: v }),
  setShowReport: (v) => set({ showReport: v }),
  setShowScenarios: (v) => set({ showScenarios: v }),
  setShowSessions: (v) => set({ showSessions: v }),
  setShowFounderMode: (v) => set({ showFounderMode: v }),
  setLoading: (v) => set({ loading: v }),
  setError: (err) => set({ error: err }),

  reset: () => set({
    state: null, status: null, report: null, candles: [], currentCandle: null,
    decisions: [], trades: [], timeline: [], config: { ...DEFAULT_CONFIG },
    selectedCandleIndex: 0, showReport: false,
  }),
}));
