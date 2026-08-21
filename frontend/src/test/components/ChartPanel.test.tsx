import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, waitFor, screen, fireEvent } from "../test-utils";
import { ChartPanel, computeEma } from "../../components/trading/chart-panel";
import * as marketApi from "../../api/market";

// Mock lightweight-charts
const mockCreatePriceLine = vi.fn();
const mockSetData = vi.fn();
const mockRemove = vi.fn();
const mockFitContent = vi.fn();

const mockSeries = {
  setData: mockSetData,
  createPriceLine: mockCreatePriceLine,
};

const mockChart = {
  addSeries: vi.fn().mockReturnValue(mockSeries),
  applyOptions: vi.fn(),
  timeScale: vi.fn().mockReturnValue({
    fitContent: mockFitContent,
  }),
  remove: mockRemove,
};

vi.mock("lightweight-charts", () => ({
  createChart: vi.fn().mockImplementation(() => mockChart),
  ColorType: { Solid: "solid" },
  CandlestickSeries: "CandlestickSeries",
  LineSeries: "LineSeries",
}));

vi.mock("../../api/market", () => ({
  fetchMarketLevels: vi.fn(),
  fetchMarketDivergence: vi.fn(),
  fetchMarketChannel: vi.fn(),
  fetchLiquidityZones: vi.fn().mockResolvedValue([]),
  fetchVolumeProfile: vi.fn().mockResolvedValue({ bins: [], poc_price: null, value_area_high: null, value_area_low: null }),
}));

describe("ChartPanel Overlays", () => {
  const dummyCandles = [
    { time: 1000, open: 100, high: 110, low: 90, close: 105 },
    { time: 2000, open: 105, high: 115, low: 95, close: 110 },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("draws S/R levels, RSI divergence and trend channels when returned", async () => {
    // 1. Mock S/R levels
    vi.mocked(marketApi.fetchMarketLevels).mockResolvedValue([
      { price: 100, type: "support", strength: 3, touches: 2 },
      { price: 115, type: "resistance", strength: 2, touches: 1 },
    ]);

    // 2. Mock RSI divergence
    vi.mocked(marketApi.fetchMarketDivergence).mockResolvedValue({
      found: true,
      type: "bullish",
      p1: { time: 1000, price: 90, rsi: 30 },
      p2: { time: 2000, price: 95, rsi: 40 },
    });

    // 3. Mock trend channel
    vi.mocked(marketApi.fetchMarketChannel).mockResolvedValue({
      found: true,
      direction: "up",
      upper: {
        start: { time: 1000, price: 110 },
        end: { time: 2000, price: 115 },
      },
      lower: {
        start: { time: 1000, price: 90 },
        end: { time: 2000, price: 95 },
      },
    });

    render(<ChartPanel data={dummyCandles} timeframe="1h" />);

    // Wait for the asynchronous fetch & rendering to complete
    await waitFor(() => {
      // Check that createPriceLine was called once per returned level (2 levels)
      expect(mockCreatePriceLine).toHaveBeenCalledTimes(2);
    });

    // Assert S/R props are sensible
    expect(mockCreatePriceLine).toHaveBeenNthCalledWith(
      1,
      expect.objectContaining({
        price: 100,
        color: "rgba(34, 197, 94, 0.7)",
      })
    );
    expect(mockCreatePriceLine).toHaveBeenNthCalledWith(
      2,
      expect.objectContaining({
        price: 115,
        color: "rgba(239, 68, 68, 0.7)",
      })
    );

    // Check that line series were added for EMAs, divergence and boundaries
    // 1 candle + 2 EMA (20/50) + 1 divergence + 2 channel = 6 series in total
    expect(mockChart.addSeries).toHaveBeenCalledTimes(6);

    // Assert divergence/channel gets the correct points
    expect(mockSetData).toHaveBeenCalledWith(
      expect.arrayContaining([
        { time: 1000, value: 90 },
        { time: 2000, value: 95 },
      ])
    );
  });

  it("does not draw overlays when endpoints return none found", async () => {
    vi.mocked(marketApi.fetchMarketLevels).mockResolvedValue([]);
    vi.mocked(marketApi.fetchMarketDivergence).mockResolvedValue({
      found: false,
      type: "none",
      p1: null,
      p2: null,
    });
    vi.mocked(marketApi.fetchMarketChannel).mockResolvedValue({
      found: false,
      direction: "none",
      upper: null,
      lower: null,
    });

    render(<ChartPanel data={dummyCandles} timeframe="1h" />);

    await waitFor(() => {
      expect(marketApi.fetchMarketLevels).toHaveBeenCalled();
    });

    // No S/R price lines drawn
    expect(mockCreatePriceLine).not.toHaveBeenCalled();

    // Candlestick + EMA20 + EMA50 -- these draw unconditionally from the
    // candle data itself, independent of the (empty here) overlay fetches
    expect(mockChart.addSeries).toHaveBeenCalledTimes(3);
  });

  it("draws entry/stop/target lines for a passed-in open trade", async () => {
    vi.mocked(marketApi.fetchMarketLevels).mockResolvedValue([]);
    vi.mocked(marketApi.fetchMarketDivergence).mockResolvedValue({
      found: false,
      type: "none",
      p1: null,
      p2: null,
    });
    vi.mocked(marketApi.fetchMarketChannel).mockResolvedValue({
      found: false,
      direction: "none",
      upper: null,
      lower: null,
    });

    render(
      <ChartPanel
        data={dummyCandles}
        timeframe="1h"
        openTrades={[
          {
            trade_id: 1,
            symbol: "BTC",
            side: "LONG",
            entry: 100,
            stop: 90,
            tp1: 120,
            status: "OPEN",
          },
        ]}
      />
    );

    await waitFor(() => {
      expect(marketApi.fetchMarketLevels).toHaveBeenCalled();
    });

    // entry + stop + tp1 drawn, tp2 skipped (not set on this trade)
    expect(mockCreatePriceLine).toHaveBeenCalledTimes(3);
    expect(mockCreatePriceLine).toHaveBeenCalledWith(
      expect.objectContaining({ price: 100, title: "ENTRY" })
    );
    expect(mockCreatePriceLine).toHaveBeenCalledWith(
      expect.objectContaining({ price: 90, title: "STOP" })
    );
    expect(mockCreatePriceLine).toHaveBeenCalledWith(
      expect.objectContaining({ price: 120, title: "TP1" })
    );
  });

  it("does not draw a price line for a null/zero stop or target", async () => {
    vi.mocked(marketApi.fetchMarketLevels).mockResolvedValue([]);
    vi.mocked(marketApi.fetchMarketDivergence).mockResolvedValue({
      found: false,
      type: "none",
      p1: null,
      p2: null,
    });
    vi.mocked(marketApi.fetchMarketChannel).mockResolvedValue({
      found: false,
      direction: "none",
      upper: null,
      lower: null,
    });

    render(
      <ChartPanel
        data={dummyCandles}
        timeframe="1h"
        openTrades={[
          { trade_id: 2, symbol: "BTC", side: "LONG", entry: 100, stop: 0, status: "OPEN" },
        ]}
      />
    );

    await waitFor(() => {
      expect(marketApi.fetchMarketLevels).toHaveBeenCalled();
    });

    // Only entry drawn -- stop=0, tp1/tp2 unset are all skipped
    expect(mockCreatePriceLine).toHaveBeenCalledTimes(1);
    expect(mockCreatePriceLine).toHaveBeenCalledWith(
      expect.objectContaining({ price: 100, title: "ENTRY" })
    );
  });

  it("draws OPP entry/stop/tp1 lines for a passed-in scanner opportunity", async () => {
    vi.mocked(marketApi.fetchMarketLevels).mockResolvedValue([]);
    vi.mocked(marketApi.fetchMarketDivergence).mockResolvedValue({
      found: false,
      type: "none",
      p1: null,
      p2: null,
    });
    vi.mocked(marketApi.fetchMarketChannel).mockResolvedValue({
      found: false,
      direction: "none",
      upper: null,
      lower: null,
    });

    render(
      <ChartPanel
        data={dummyCandles}
        timeframe="1h"
        opportunities={[
          {
            rank: 1,
            symbol: "BTC",
            side: "LONG",
            strategy: "trend",
            score: 0.8,
            probability: 75,
            risk_score: 0.3,
            confidence: 80,
            price: 100,
            stop: 90,
            tp1: 120,
            signals: [],
          },
        ]}
      />
    );

    await waitFor(() => {
      expect(marketApi.fetchMarketLevels).toHaveBeenCalled();
    });

    expect(mockCreatePriceLine).toHaveBeenCalledTimes(3);
    expect(mockCreatePriceLine).toHaveBeenCalledWith(
      expect.objectContaining({ price: 100, title: "OPP ENTRY" })
    );
    expect(mockCreatePriceLine).toHaveBeenCalledWith(
      expect.objectContaining({ price: 90, title: "OPP STOP" })
    );
    expect(mockCreatePriceLine).toHaveBeenCalledWith(
      expect.objectContaining({ price: 120, title: "OPP TP1" })
    );
  });

  it("expands to fullscreen on click and exits on a second click or Escape", async () => {
    vi.mocked(marketApi.fetchMarketLevels).mockResolvedValue([]);
    vi.mocked(marketApi.fetchMarketDivergence).mockResolvedValue({
      found: false,
      type: "none",
      p1: null,
      p2: null,
    });
    vi.mocked(marketApi.fetchMarketChannel).mockResolvedValue({
      found: false,
      direction: "none",
      upper: null,
      lower: null,
    });

    const { container } = render(<ChartPanel data={dummyCandles} timeframe="1h" />);

    await waitFor(() => {
      expect(marketApi.fetchMarketLevels).toHaveBeenCalled();
    });

    const toggle = screen.getByRole("button", { name: /tam ekran aç|open fullscreen/i });
    const card = container.firstElementChild as HTMLElement;
    expect(card.className).not.toContain("fixed");

    fireEvent.click(toggle);
    expect(card.className).toContain("fixed");
    expect(card.className).toContain("inset-0");
    screen.getByRole("button", { name: /tam ekrandan çık|exit fullscreen/i });

    fireEvent.keyDown(window, { key: "Escape" });
    await waitFor(() => {
      expect(card.className).not.toContain("fixed");
    });
  });

  it("draws EMA20/EMA50 series from the candle data alone, before any overlay fetch resolves", async () => {
    vi.mocked(marketApi.fetchMarketLevels).mockResolvedValue([]);
    vi.mocked(marketApi.fetchMarketDivergence).mockResolvedValue({
      found: false, type: "none", p1: null, p2: null,
    });
    vi.mocked(marketApi.fetchMarketChannel).mockResolvedValue({
      found: false, direction: "none", upper: null, lower: null,
    });

    render(<ChartPanel data={dummyCandles} timeframe="1h" />);

    await waitFor(() => {
      expect(mockChart.addSeries).toHaveBeenCalledWith(
        "LineSeries", expect.objectContaining({ title: "EMA20" })
      );
    });
    expect(mockChart.addSeries).toHaveBeenCalledWith(
      "LineSeries", expect.objectContaining({ title: "EMA50" })
    );
    // 2 candles of data -> 2 EMA points per series
    expect(mockSetData).toHaveBeenCalledWith([
      { time: 1000, value: 105 },
      { time: 2000, value: expect.any(Number) },
    ]);
  });
});

describe("computeEma", () => {
  it("seeds with the first close, then applies exponential smoothing", () => {
    const closes = [100, 110, 105, 120];
    const result = computeEma(closes, 3);

    expect(result).toHaveLength(4);
    expect(result[0]).toBe(100);
    // k = 2/(3+1) = 0.5 -> ema1 = 110*0.5 + 100*0.5 = 105
    expect(result[1]).toBeCloseTo(105, 6);
    // ema2 = 105*0.5 + 105*0.5 = 105
    expect(result[2]).toBeCloseTo(105, 6);
    // ema3 = 120*0.5 + 105*0.5 = 112.5
    expect(result[3]).toBeCloseTo(112.5, 6);
  });

  it("returns an empty array for empty input", () => {
    expect(computeEma([], 20)).toEqual([]);
  });

  it("tracks a constant series exactly", () => {
    const result = computeEma([50, 50, 50, 50], 10);
    expect(result).toEqual([50, 50, 50, 50]);
  });
});
