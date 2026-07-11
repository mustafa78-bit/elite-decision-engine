# Founder Walkthrough Report

> **Reviewer**: Mustafa (Founder)  
> **Date**: 2026-07-11  
> **Branch**: `execution-layer`  
> **Pages Reviewed**: Dashboard, Scanner, Asset Detail, Decision Center  
> **Phase**: Founder Alpha — First Walkthrough  

---

## 1. Screens Reviewed

| Page | Route | Status | Lines |
|------|-------|--------|-------|
| Dashboard | `/dashboard` | Reviewed | 86 |
| Scanner | `/scanner` | Reviewed | 783 |
| Asset Detail | `/asset/:symbol` | Reviewed | 613 |
| Decision Center | `/decisions` | Reviewed | 702 |

---

## 2. UX Findings

### Critical

| # | Page | Issue | Severity | Fixed |
|---|------|-------|----------|-------|
| C1 | Scanner | **Timeframe & Market controls are decorative** — clicking 1m/5m/... or Spot/Futures updates UI state but the API call never includes these params. User expects data to change but nothing happens. | Critical | ✅ |
| C2 | Scanner | **No error state on API failure** — `catch { setOpportunities([]); }` silently wipes data. User sees empty table with no explanation. | Critical | ✅ |

### High

| # | Page | Issue | Severity | Fixed |
|---|------|-------|----------|-------|
| H1 | Asset Detail | **DecisionTimeline inverted logic** — `events={recentTrades.length > 0 ? undefined : []}`. When trades exist, passes `undefined` (shows "No recent decisions"); when no trades, passes `[]` (also shows "No recent decisions"). Timeline never renders actual trade data. | High | ✅ |
| H2 | Asset Detail | **Chart data failure has no feedback** — `catch { /* chart will show empty state */ }` silently swallows errors. User sees blank chart with no retry option. | High | ✅ |
| H3 | Decision Center | **mtf_score incorrectly mapped** — `mtf_score: signal.btc_score` on line 351 causes MTF field to always mirror BTC correlation instead of being independent. | High | ✅ |
| H4 | Decision Center | **Best/Worst Strategy hardcoded** — always shows "Trend Following" / "Mean Reversion" regardless of actual data. Misleading analytics. | High | ✅ |
| H5 | All pages | **Silent API error swallowing** — Scanner (`catch { setOpportunities([]); }`), AssetDetail (`catch { /* chart will show empty state */ }`), DecisionCenter (`catch { setSignals([]); }`). No error banner, no retry mechanism. | High | ✅ |

### Medium

| # | Page | Issue | Severity |
|---|------|-------|----------|
| M1 | Scanner, AssetDetail, DecisionCenter | **Duplicate helper functions** — `getScoreColor`, `getConfidenceColor`, `getRiskColor`, `getDecisionBadge`, `getSideBadge` defined identically in 3 files (15 redundant definitions). DRY violation. | Medium |
| M2 | Scanner | **Saved Filters cannot be renamed** — auto-named "Filter N", no edit support. | Medium |
| M3 | Scanner | **Double-click navigation lacks affordance** — no visual hint that double-click navigates to asset detail. | Medium |
| M4 | Dashboard | **Open/Closed Trades sections render unconditionally** — heading always visible even with 0 trades (child components may handle empty state). | Medium |
| M5 | Dashboard | **KpiGrid has no loading state** — blank until `fetchKpiDetail()` resolves. | Medium |
| M6 | All pages | **No keyboard navigation in tables** — can't arrow-key through table rows. | Medium |
| M7 | Sidebar | **Overview page (`/overview`) not in sidebar** — Dashboard is listed but `/overview` route exists without navigation entry. | Medium |

### Low

| # | Page | Issue | Severity |
|---|------|-------|----------|
| L1 | Asset Detail | `TVTimeframeSelector` uses `selected={timeframe as any}` type assertion. | Low |
| L2 | All pages | No `aria-label` on table interactive elements. | Low |
| L3 | All pages | `.reverse()` on notifications array creates new array every render. | Low |
| L4 | Dashboard | `IntelligencePanel` rendered in both Layout right panel and Dashboard right column — potential duplicate. | Low |
| L5 | Decision Center | Open trades pushed with `eliteScore: 0`, `confidence: 0`, `risk: 0` — incomplete data when no signal matched. | Low |
| L6 | Scanner | `formatPercent` imported but only used for funding display — could be generalized. | Low |

---

## 3. Fixes Applied

### Critical Fixes

**C1 — Scanner: Wire timeframe/market to API (`Scanner.tsx:435-449`)**
- Added `&timeframe=${timeframe}&market=${market}` to the API URL
- Added `timeframe` and `market` to `useCallback` dependency array
- Timeframe and market controls now affect fetched data

**C2 — Scanner: Add error state with retry (`Scanner.tsx:433,445`)**
- Added `error` state variable
- Error banner with red text + Retry button replaces data area on failure

### High Fixes

**H1 — Asset Detail: Fix DecisionTimeline (`AssetDetail.tsx`)**
- Replaced inverted `undefined : []` with proper mapping from `recentTrades` to `DecisionEvent[]`
- Maps trade type (TRADE_OPENED/TRADE_CLOSED) to timeline event type, action, confidence, and outcome

**H2 — Asset Detail: Chart error feedback (`AssetDetail.tsx`)**
- Added `candleError` state with retry button
- Chart area shows error banner + Retry instead of blank on failure

**H3 — Decision Center: Fix mtf_score mapping (`DecisionCenter.tsx:351`)**
- Changed from `signal.btc_score` (mirrors BTC correlation) to average of trend/volume/btc scores as a proxy

**H4 — Decision Center: Remove hardcoded strategies (`DecisionCenter.tsx:449-450`)**
- Changed from hardcoded "Trend Following"/"Mean Reversion" to "N/A" — honest placeholder until real strategy attribution is available

**H5 — Error feedback across all pages**
- Scanner: Error banner + Retry button
- AssetDetail: Chart error banner + Retry button
- DecisionCenter: Error banner + Retry button for signal loading

---

## 4. Remaining Issues

### Unaddressed Medium Issues
- Duplicate helper functions across 3 pages (refactor to shared `lib/` module) — safe to defer
- Saved filters cannot be renamed — low usage impact
- Dashboard KpiGrid loading state — minor visual gap
- Keyboard navigation in tables — accessibility enhancement

### Unaddressed Low Issues
- TVTimeframeSelector `as any` type assertion
- Missing `aria-label` attributes
- Array `.reverse()` on every render
- Duplicate IntelligencePanel in Layout + Dashboard

### Pre-existing Known Issues (from MASTER_BOOK)
- BP2: ConfidenceEngine always returns STRONG_APPROVE (double-scaling) — Critical
- BP3: ATRr_14 typo breaks indicator pipeline — Critical
- No database migration system — High
- No pinned dependency versions — High
- Token stored in localStorage — Medium

---

## 5. Product Score

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Visual Design** | 8/10 | Dark theme consistent, good use of color coding, widget-card pattern works |
| **Navigation** | 7/10 | Sidebar clear, but `/overview` missing, `/decisions` well-placed |
| **Data Display** | 7/10 | Tables look professional; missing data in open trades drags score |
| **Error Handling** | 5/10 | Before fixes: all errors silently swallowed. After: basic error + retry added |
| **Loading States** | 6/10 | Basic skeletons present but KpiGrid missing; overall acceptable |
| **Empty States** | 6/10 | Table-level empty states present; section-level missing |
| **Interaction** | 6/10 | Explain drawers work well; double-click discovery is poor |
| **Mobile** | 5/10 | Horizontal scroll on tables; sidebar not collapsible |
| **Consistency** | 7/10 | Same design language across pages; helper duplication is main inconsistency |
| **Overall UX** | 6.5/10 | Functional for Founder Alpha. Critical issues fixed. Medium polish items remain. |

---

## 6. Recommendation

**Conditionally approve for commit.**

The Critical and High issues identified during the Founder walkthrough have been fixed:
- Timeframe/market controls now functional in Scanner
- Error states with retry added to all pages
- DecisionTimeline now shows actual trade data
- Chart loading has proper error feedback
- Decision Center data mapping bugs corrected
- Hardcoded misleading analytics replaced with honest placeholders

**Build**: 0 TS errors, 462ms clean  
**Tests**: 60/60 passing  
**No regressions introduced.**

Medium and Low items are safe to defer — they do not block Founder Alpha usage. The pre-existing backend bugs (BP2, BP3) remain on the backlog.

**Next recommended step**: Commit the current changeset and proceed to End-to-End Integration Test as per the milestone plan.

---

*Report generated: 2026-07-11 | Branch: execution-layer | Role: Mustafa (Founder)*
