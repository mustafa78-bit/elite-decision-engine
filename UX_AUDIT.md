# UX Audit — Elite Platform

## Critical Issues

### C1. Duplicate ToastProvider (2 implementations, both active)
- `components/layout/toast-provider.tsx` (zustand-based)
- `components/layout/ToastProvider.tsx` (useSyncExternalStore-based)
- `main.tsx` imports `ToastProvider.tsx`, `shell.tsx` imports `toast-provider.tsx`
- Two toast systems competing — user may see toasts from only one system

### C2. Duplicate Layout Shells
- `layout/Layout.tsx` AND `layout/shell.tsx` both serve as route wrapper with `<Outlet>`
- Only `Layout.tsx` is used in App.tsx — `shell.tsx` is dead code
- Increases bundle size, maintenance burden

### C3. Duplicate Connection Status
- `layout/connection-indicator.tsx` AND `layout/ConnectionStatus.tsx`
- Both display WebSocket status — different visual style, different data sources

### C4. 40+ Components Use Hardcoded Colors Instead of CSS Variables
- Pages: ALL 30+ pages use hardcoded `text-gray-*`, `bg-gray-*`, `border-gray-*`
- Components: `SkeletonCard`, `EmptyState`, `ErrorRetry`, `Header`, `ConnectionStatus`, `LoadingScreen`, `ErrorBoundary`
- Mixing patterns means theme changes require editing every file
- **No dark/light mode support** — `ThemeProvider.setMode()` is a no-op

### C5. No Loading States on 20+ Components
- Pages like Signals, Portfolio, Risk, Analytics fetch data inline without Skeleton
- No `loading` prop pattern — each page reinvents loading display

### C6. No Empty States on List Components
- SignalTable, PositionTable, TradeJournal show blank table headers when data is empty
- No "No data" message for empty lists

---

## Inconsistencies

### Typography
| Location | Font Size | Family | Case |
|----------|-----------|--------|------|
| CardTitle (ui/card.tsx) | `text-xs` (12px) | sans-serif | uppercase |
| Widget headers (globals.css) | `--font-size-xs` (12px) | sans-serif | uppercase |
| Page headings (Dashboard) | `text-xs uppercase` | sans-serif | — |
| Page headings (Signals) | `text-xs uppercase` | sans-serif | — |
| Sidebar labels | `text-xs` | — | — |
| IntelligencePanel | `text-[11px]` | sans-serif | — |
| SignalTable cells | `text-xs` | — | — |
| Badge text | `text-[11px]` | `font-mono` | — |
| Metric values | `text-sm` | `font-mono` | — |
| Scanner cards | `text-xs` / `text-[10px]` | mixed | — |

**Problem**: 6 different text sizes used instead of the 7 defined in tokens.

### Spacing
| Pattern | Locations |
|---------|-----------|
| `p-4` + `gap-3` | Dashboard, Signals, AssetDetail |
| `p-4` + `space-y-4` | Portfolio, PaperTrading |
| `p-4` + `gap-4` | Analytics |
| `p-5` | shell.tsx outlet |
| `p-6` | signal score card |
| `px-3 py-2` | IntelligencePanel |

**Problem**: 5+ different spacing patterns, no consistent page layout template.

### Button Usage
| Variant | Pages | Context |
|---------|-------|---------|
| `primary` | Scanner category tabs | Category selection |
| `secondary` | Various | Secondary actions |
| `danger` | OrderPanel | SELL button |
| `glass` | Dashboard builder | Toggle |
| `ghost` | Dialog close | Close action |
| `outline` | ErrorRetry, NotFound, Preferences, Watchlists | Retry, nav |

**Problem**: `outline` variant visually similar to `secondary` — no clear distinction.

---

## Accessibility Issues

### A1. Missing ARIA Roles
- `Tabs` — no `role="tablist"`, `role="tab"`, `role="tabpanel"`
- `DropdownMenu` — no `role="menu"`, `role="menuitem"`
- `Dialog` — dialog role present but no `aria-modal`, no focus trap
- `Slider` — no `role="slider"`, `aria-valuenow`, `aria-valuemin`, `aria-valuemax`
- `Progress` — no `role="progressbar"`, `aria-valuenow`

### A2. Missing Keyboard Navigation
- `Tabs` — arrow keys don't switch tabs
- `DropdownMenu` — arrow keys don't navigate items
- `Slider` — no arrow key adjustment
- `Dialog` — focus not trapped inside dialog

### A3. Color Contrast
- `text-gray-500` on `bg-gray-900` = ~4.0:1 ratio (fails WCAG AA for normal text)
- `text-gray-600` on `bg-gray-950` = ~3.5:1 ratio (fails)

### A4. Missing `lang` Attribute
- `<html>` element has no `lang` attribute

### A5. Screen Reader Support
- `useFocusTrap` from `lib/accessibility.ts` is never used
- `announceToScreenReader` from `lib/accessibility.ts` is never called

---

## Mobile Responsiveness

### M1. No Mobile Navigation
- Sidebar is fixed 224px wide with no collapse on mobile
- No hamburger menu or bottom navigation
- Right Intelligence Panel is hidden (`hidden xl:block`) — correct, but no mobile alternative

### M2. Fixed-Width Grids
- Dashboard uses `lg:grid-cols-4` with no mobile fallback for some sections
- Scanner cards assume 1-2 column layout but have no breakpoints below `md`

### M3. No Touch Support
- Slider uses `mousedown`/`mousemove`/`mouseup` — no `touchstart`/`touchmove`/`touchend`
- Tooltip uses `mouseEnter`/`mouseLeave` — no touch equivalent

---

## Missing States

### Loading States
- [ ] Signals page: no skeleton
- [ ] Portfolio page: no skeleton
- [ ] Risk page: no skeleton
- [ ] Market page: no skeleton
- [ ] Analytics page: no skeleton
- [ ] Backtest page: no skeleton
- [ ] Journal page: no skeleton

### Empty States
- [ ] SignalTable: empty table headers with no rows
- [ ] PositionTable: empty table headers
- [ ] TradeJournal: "Journal" heading with blank content
- [ ] Watchlists: list area shows nothing when empty

### Error States
- [ ] Most API calls have try/catch but no retry UI
- [ ] Network errors show as generic text, not ErrorRetry component
