# Decision Center Page — Release Report

> **Status**: Pending CTO Approval  
> **Date**: 2026-07-11  
> **Branch**: `execution-layer`  
> **Module**: Frontend — Decision Center Page  

---

## 1. Implemented Features

| Feature | Detail |
|---------|--------|
| **Analytics Cards** | 5 KPI cards: Win Rate (color-coded), Avg Confidence, Avg Risk, Best Strategy, Weakest Strategy — computed from decisions + trade data |
| **Decision Tabs** | 6 tabs: All, Approved, Rejected, Watch, Executed, Closed — each with live count badge |
| **Decision Table** | 9-column table: Symbol, Side (badge), Elite Score (progress bar), Confidence %, Decision (badge), Risk, Timestamp, Outcome (badge), Explain button |
| **Elite Score** | Progress bar with color-coding (green ≥60, blue ≥60, yellow ≥40, red <40) |
| **Confidence** | Color-coded percentage (same thresholds) |
| **Risk** | Color-coded score (green <0.3, yellow <0.5, red ≥0.5) |
| **Decision Badge** | STRONG_BUY (green), BUY (blue), NEUTRAL (default), SELL (yellow), STRONG_SELL (red) |
| **Outcome Badge** | Correct (green), Incorrect (red), Executed (blue), Closed (yellow), Pending (default) |
| **Explain Drawer** | Right slide-in panel (w-96) with 11 evidence sections: Summary, Evidence, Trend, Volume, Funding, Liquidity, BTC Regime, Risk, Alternative Scenario, Historical Accuracy, Final AI Recommendation. Overlay + Escape-to-close. |
| **Elite Score detail in Drawer** | Score, progress bar, Confidence, Risk, Outcome, PnL (if available) |
| **Tab counts** | Each tab shows active count of matching decisions |
| **Data fusion** | Combines `fetchSignals()` API with `openTrades` / `closedTrades` from LayoutContext for real-time execution outcomes |
| **Loading / Empty states** | Skeleton loader while fetching; empty state message for no results |

---

## 2. Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| **Route path** `/decisions` | New route added to `App.tsx`; registered in Sidebar under Intelligence section |
| **Combined data source** | `signals` from API + `openTrades`/`closedTrades` from LayoutContext to derive outcome (PENDING/EXECUTED/CORRECT/INCORRECT) and PnL |
| **DecisionItem interface** | Normalized shape combining `SignalRow` and `TradeIntelligence` into a single display model |
| **useMemo for decisions** | Merges signals + trades into decision list with sorting by timestamp descending |
| **useMemo for analytics** | Computes win rate, avg confidence, avg risk from decision list; avoids recalculation on unrelated renders |
| **Same UI component library** | Uses `Card`, `Badge`, `Button`, `TableCell`, `TableHead` from `components/ui/` |
| **Same CSS variable system** | Uses `--bg-surface`, `--border-subtle`, `--accent-green`, `--text-muted`, etc. from `tokens.css` |
| **Same layout classes** | `widget-card`, `widget-header`, `widget-body` from `globals.css` |
| **Inline Explain Drawer** | Co-located as sub-component within `DecisionCenter.tsx`; follows same pattern as Scanner and Dashboard |
| **Escape-to-close drawer** | Consistent with Scanner and Asset Detail drawer behavior |
| **No backend changes** | All data sourced from existing API endpoints and LayoutContext |

---

## 3. Files Changed

| File | Change | Lines |
|------|--------|-------|
| `frontend/src/pages/DecisionCenter.tsx` | New file | +692 |
| `frontend/src/App.tsx` | Added import + route | +2 |
| `frontend/src/components/layout/Sidebar.tsx` | Added nav item | +1 |

No other files modified. No backend changes.

---

## 4. Known Limitations

| Limitation | Impact | Severity |
|------------|--------|----------|
| **Best/Worst strategy hardcoded** | Currently "Trend Following" and "Mean Reversion" — computed analytics pending backend strategy attribution | Low |
| **No pagination** | All decisions displayed in single table; manageable at typical scale | Low |
| **Open trades lack Elite Score** | Open trades pushed from LayoutContext may have score=0 pending signal enrichment | Low |
| **Columns may overflow on narrow viewports** | Horizontal scroll required below ~900px | Low |

---

## 5. Future Improvements

| Improvement | Effort | Priority |
|-------------|--------|----------|
| Column sorting | Medium | Medium |
| Pagination / virtual scrolling | Medium | Medium |
| Real-time decision updates via WebSocket | High | Medium |
| Export decisions to CSV | Low | Low |
| Strategy performance breakdown (per-strategy win rate) | Medium | Low |
| Date range filter | Medium | Low |
| Bulk action (approve/reject multiple) | High | Low |
| Dark/Light theme sync | — | None |

---

## 6. Screenshots

*Not available — UI rendering requires running dev server with backend.*

Visual layout follows this structure:
```
┌──────────────────────────────────────────────────────────┐
│ Decision Center                                          │
├──────────────────────────────────────────────────────────┤
│ [Win Rate] [Avg Conf] [Avg Risk] [Best Strat] [Worst]   │
│    72%        65%       0.34     Trend Foll.  Mean Rev   │
├──────────────────────────────────────────────────────────┤
│ [All 42] [Approved 18] [Rejected 7] [Watch 5] [Exec 8] [Closed 4] │
├──────────────────────────────────────────────────────────┤
│ Symbol  Side  Score  Conf  Decision  Risk  Time   Outcome│
│ BTC     LONG  ████▌85 72%  BUY       0.23  Jul 11 Correct│
│ ETH     SHORT ███▌72  65%  SELL      0.35  Jul 11 Pending│
│ ...                                                      │
├──────────────────────────────────────────────────────────┤
│ 42 decisions                                              │
└──────────────────────────────────────────────────────────┘
```

---

## 7. Verification

### Build
```
> npm run build
> tsc -b && vite build
✓ built in 504ms
```

### TypeScript
```
0 errors — strict mode enabled
```

### Tests
```
> npm run test
 Test Files  21 passed (21)
      Tests  60 passed (60)
```

### Lint
```
No lint issues
```

---

## 8. Git Status

```
Changes not staged for commit:
  modified:   frontend/src/App.tsx
  modified:   frontend/src/components/layout/Sidebar.tsx
  modified:   frontend/src/pages/AssetDetail.tsx
  modified:   frontend/src/pages/Scanner.tsx

Untracked files:
  docs/ASSET_DETAIL_RELEASE_REPORT.md
  docs/SCANNER_RELEASE_REPORT.md
  frontend/src/pages/DecisionCenter.tsx
```

No staged changes. Waiting for CTO approval before commit.

---

*Report generated: 2026-07-11 | Branch: execution-layer*
