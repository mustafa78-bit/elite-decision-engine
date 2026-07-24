import { useCallback, useEffect, useState } from "react";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import { Skeleton } from "../components/ui/skeleton";
import { addGlobalToast } from "../components/layout/toast-provider";
import { PageHeader } from "../components/ui/PageHeader";
import { EmptyState } from "../components/ui/EmptyState";
import {
  fetchWatchlists,
  createWatchlist,
  deleteWatchlist,
  addWatchlistSymbol,
  removeWatchlistSymbol,
} from "../api/watchlists";
import type { WatchlistDTO } from "../types/api/watchlist";

export default function WatchlistsPage() {
  const [watchlists, setWatchlists] = useState<WatchlistDTO[]>([]);
  const [loading, setLoading] = useState(true);
  const [newName, setNewName] = useState("");
  const [newSymbol, setNewSymbol] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetchWatchlists();
      setWatchlists(res.watchlists);
    } catch {
      addGlobalToast("Failed to load watchlists", "error");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function handleCreate() {
    if (!newName.trim()) return;
    try {
      const wl = await createWatchlist(newName.trim());
      setWatchlists((prev) => [...prev, wl]);
      setNewName("");
      addGlobalToast("Watchlist created", "success");
    } catch {
      addGlobalToast("Failed to create watchlist", "error");
    }
  }

  async function handleDelete(id: number) {
    try {
      await deleteWatchlist(id);
      setWatchlists((prev) => prev.filter((w) => w.id !== id));
      addGlobalToast("Watchlist deleted", "success");
    } catch {
      addGlobalToast("Failed to delete watchlist", "error");
    }
  }

  async function handleAddSymbol(id: number) {
    if (!newSymbol.trim()) return;
    try {
      const wl = await addWatchlistSymbol(id, newSymbol.trim().toUpperCase());
      setWatchlists((prev) => prev.map((w) => (w.id === id ? wl : w)));
      setNewSymbol("");
      addGlobalToast(`Added ${newSymbol.toUpperCase()}`, "success");
    } catch {
      addGlobalToast("Failed to add symbol", "error");
    }
  }

  async function handleRemoveSymbol(wlId: number, symbol: string) {
    try {
      const wl = await removeWatchlistSymbol(wlId, symbol);
      setWatchlists((prev) => prev.map((w) => (w.id === wlId ? wl : w)));
    } catch {
      addGlobalToast("Failed to remove symbol", "error");
    }
  }

  const headerActions = (
    <div className="flex items-center gap-2">
      <Input
        placeholder="New watchlist name..."
        value={newName}
        onChange={(e) => setNewName(e.target.value)}
        className="w-48 h-7 text-xs"
      />
      <Button size="sm" variant="primary" onClick={handleCreate}>
        Create
      </Button>
    </div>
  );

  return (
    <div className="space-y-4">
      <PageHeader
        title="Watchlists"
        subtitle="Monitor, tracks, and group your high-conviction digital assets"
        actions={headerActions}
      />

      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
        </div>
      ) : watchlists.length === 0 ? (
        <EmptyState
          title="Build Your Tactical Watchlist"
          description="Watchlists allow you to monitor specific market sectors, custom portfolios, or target assets. Track real-time prices, volume breakout flags, and multi-agent AI consensus on customized dashboards."
          icon={
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="w-8 h-8 text-[var(--text-muted)] opacity-60"
            >
              <path d="M3 12h.01" />
              <path d="M3 18h.01" />
              <path d="M3 6h.01" />
              <path d="M8 12h13" />
              <path d="M8 18h13" />
              <path d="M8 6h13" />
            </svg>
          }
          actionButton={{
            label: "Initialize Default Watchlist",
            onClick: () => {
              createWatchlist("Default Watchlist")
                .then((wl) => {
                  setWatchlists((prev) => [...prev, wl]);
                  setNewName("");
                  addGlobalToast("Default Watchlist created", "success");
                })
                .catch(() => {
                  addGlobalToast("Failed to create watchlist", "error");
                });
            },
          }}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {watchlists.map((wl) => (
            <Card key={wl.id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>{wl.name}</CardTitle>
                  <Button
                    size="sm"
                    variant="danger"
                    onClick={() => handleDelete(wl.id)}
                  >
                    Delete
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-1 mb-3">
                  {wl.symbols.map((sym) => (
                    <Badge key={sym} variant="info">
                      {sym}
                      <button
                        onClick={() => handleRemoveSymbol(wl.id, sym)}
                        className="ml-1 opacity-60 hover:opacity-100"
                      >
                        ×
                      </button>
                    </Badge>
                  ))}
                </div>
                <div className="flex items-center gap-2">
                  <Input
                    placeholder="Add symbol..."
                    value={newSymbol}
                    onChange={(e) => setNewSymbol(e.target.value)}
                    className="flex-1"
                  />
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleAddSymbol(wl.id)}
                  >
                    Add
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
