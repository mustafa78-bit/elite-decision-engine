import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";

export default function LiquidityPage() {
  return (
    <div className="space-y-4">
      <h2 className="text-xs uppercase tracking-widest text-gray-500">
        Liquidity Analysis
      </h2>
      <Card>
        <CardHeader>
          <CardTitle>Liquidity Map</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="text-3xl mb-4 opacity-30">💧</div>
            <p className="text-xs text-gray-600 font-mono uppercase tracking-widest mb-2">
              Liquidity Heatmap
            </p>
            <p className="text-[10px] text-gray-700 max-w-md">
              Order book depth analysis, liquidity clustering, and support/resistance
              detection across all tracked symbols.
            </p>
            <span className="mt-4 px-2 py-0.5 border border-gray-800 rounded text-[9px] text-gray-700 uppercase tracking-wider font-mono">
              Coming in Batch 5
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
