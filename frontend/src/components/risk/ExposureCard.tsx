interface Props {
  symbolExposure: Record<string, number>;
  maxSymbolExposure: number;
  portfolioExposure: number;
  maxPortfolioExposure: number;
}

function barWidth(value: number, max: number): string {
  const pct = max > 0 ? Math.min((value / max) * 100, 100) : 0;
  return `${pct}%`;
}

export default function ExposureCard({
  symbolExposure,
  maxSymbolExposure,
  portfolioExposure,
  maxPortfolioExposure,
}: Props) {
  const portPct = maxPortfolioExposure > 0
    ? Math.min((portfolioExposure / maxPortfolioExposure) * 100, 100)
    : 0;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-3">
      <h3 className="text-[10px] uppercase tracking-widest text-gray-500 mb-3">
        Exposure
      </h3>

      <div className="mb-3">
        <div className="flex justify-between text-xs mb-1">
          <span className="text-gray-500">Portfolio</span>
          <span className={`tabular-nums ${portPct > 80 ? "text-red-400" : "text-gray-200"}`}>
            ${portfolioExposure.toFixed(2)} / ${maxPortfolioExposure.toFixed(2)}
          </span>
        </div>
        <div className="h-1.5 bg-gray-950 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${portPct > 80 ? "bg-red-500" : "bg-green-600"}`}
            style={{ width: barWidth(portfolioExposure, maxPortfolioExposure) }}
          />
        </div>
      </div>

      {Object.entries(symbolExposure).length > 0 && (
        <div className="space-y-2">
          <div className="text-[10px] text-gray-500 uppercase tracking-wider">By Symbol</div>
          {Object.entries(symbolExposure).map(([sym, val]) => {
            const pct = maxSymbolExposure > 0
              ? Math.min((val / maxSymbolExposure) * 100, 100)
              : 0;
            return (
              <div key={sym}>
                <div className="flex justify-between text-xs mb-0.5">
                  <span className="text-gray-300">{sym}</span>
                  <span className={`tabular-nums ${pct > 80 ? "text-red-400" : "text-gray-200"}`}>
                    ${val.toFixed(2)}
                  </span>
                </div>
                <div className="h-1 bg-gray-950 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${pct > 80 ? "bg-red-500" : "bg-blue-600"}`}
                    style={{ width: barWidth(val, maxSymbolExposure) }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}

      {Object.entries(symbolExposure).length === 0 && (
        <div className="text-gray-600 text-xs text-center py-2">No open exposure</div>
      )}
    </div>
  );
}
