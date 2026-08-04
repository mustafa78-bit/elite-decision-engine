import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, waitFor } from "../test-utils";
import { ChartPanel } from "../../components/trading/chart-panel";
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

    // Check that line series were added for divergence and boundaries
    // 1 candle series + 1 divergence series + 2 channel series = 4 series in total
    expect(mockChart.addSeries).toHaveBeenCalledTimes(4);

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

    // Only the Candlestick series should be added (1 series total)
    expect(mockChart.addSeries).toHaveBeenCalledTimes(1);
  });
});
