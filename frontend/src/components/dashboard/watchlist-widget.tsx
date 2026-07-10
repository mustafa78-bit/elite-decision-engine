import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Skeleton } from "../ui/skeleton";
import { fetchWatchlists } from "../../api/watchlists";
import { useTerminalStore } from "../../stores/terminal-store";

export function WatchlistWidget() {
  const { data, isLoading } = useQuery({
    queryKey: ["watchlists"],
    queryFn: fetchWatchlists,
    refetchInterval: 30_000,
  });
  const { setSymbol } = useTerminalStore();

  const first = data?.watchlists?.[0];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Watchlist</CardTitle>
        {first && (
          <span className="text-[10px] text-[var(--text-muted)] font-mono">
            {first.name}
          </span>
        )}
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-12 w-full" />
        ) : !first || first.symbols.length === 0 ? (
          <div className="text-sm text-[var(--text-muted)] text-center py-4">
            No watchlist symbols
          </div>
        ) : (
          <div className="flex flex-wrap gap-1.5">
            {first.symbols.map((sym) => (
              <button
                key={sym}
                onClick={() => setSymbol(sym)}
                className="px-2 py-1 rounded-md bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-[10px] font-mono text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-default)] transition-all"
              >
                {sym}
              </button>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
