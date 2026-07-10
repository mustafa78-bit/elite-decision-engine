# Component Tree — Elite Terminal

## UI Components (14)
```
components/ui/
├── avatar.tsx        - User avatar display
├── badge.tsx         - Status badge (7 variants)
├── button.tsx        - Action button (6 variants, 3 sizes)
├── card.tsx          - Card container (Card, CardHeader, CardTitle, CardContent)
├── dialog.tsx        - Modal dialog
├── dropdown-menu.tsx - Context/popup menu
├── EmptyState.tsx    - Empty data placeholder
├── ErrorRetry.tsx    - Error with retry button
├── form.tsx          - Form input component
├── input.tsx         - Text input
├── kbd.tsx           - Keyboard shortcut display
├── progress.tsx      - Progress bar
├── scroll-area.tsx   - Custom scrollable container
├── separator.tsx     - Visual divider
├── skeleton.tsx      - Loading skeleton
├── slider.tsx        - Range slider
├── switch.tsx        - Toggle switch
├── table.tsx         - Data table
├── tabs.tsx          - Tab navigation
└── tooltip.tsx       - Hover tooltip
```

## AI Intelligence Components (17)
```
components/ai/
├── ai-chat.tsx              - AI assistant chat
├── ai-summary-card.tsx      - AI analysis summary
├── alert-generator.tsx      - Alert rule creator
├── analysis-dashboard.tsx   - Full AI analysis view
├── anomaly-detection.tsx    - Market anomaly detection
├── confidence-breakdown.tsx - Score breakdown by factor
├── decision-timeline.tsx    - Decision history timeline
├── explainable-ai-panel.tsx - Explainable AI with factors
├── feature-importance.tsx   - Feature importance chart
├── funding-widget.tsx       - Funding rate display
├── liquidity-widget.tsx     - Liquidity context
├── macro-widget.tsx         - Macro economic data
├── memory-widget.tsx        - Agent memory/context
├── news-widget.tsx          - News sentiment widget
├── open-interest-widget.tsx - Open interest data
├── whale-widget.tsx         - Whale activity tracker
└── signal-feed.tsx          - Real-time signal feed
```

## Dashboard Widgets (38)
```
components/dashboard/
├── KPICard.tsx / KpiGrid         - Key performance indicators
├── PortfolioSummaryCard.tsx      - Portfolio summary
├── MonitoringStatus.tsx          - System monitoring
├── NotificationPanel.tsx         - Notification list
├── MarketRegimeWidget.tsx        - Market regime badge
├── [30+ widget components]       - Extensible widget system
└── widget-registry.tsx           - Widget registration system
```

## Trading Components (15)
```
components/trading/
├── chart-panel.tsx        - Lightweight chart (lazy loaded)
├── order-panel.tsx        - Order entry form
├── order-book.tsx         - Order book depth
├── position-tracker.tsx   - Open position tracking
├── trade-journal.tsx      - Trade journal entries
├── risk-reward.tsx        - Risk/reward calculator
├── symbol-search.tsx      - Symbol search
├── position-sizing.tsx    - Position size calculator
├── multi-chart-layout.tsx - Multi-chart grid
└── [7 TV-style components] - TradingView-like features
```

## Layout Components (13)
```
components/layout/
├── Layout.tsx           - Root layout with 3-column structure
├── Sidebar.tsx          - Navigation sidebar
├── Header.tsx           - Top header with WebSocket status
├── topbar.tsx           - Secondary toolbar (search, symbols)
├── shell.tsx            - Alternative layout shell
├── ErrorBoundary.tsx    - React error boundary
├── LoadingScreen.tsx    - Full-page loading state
├── ToastProvider.tsx    - Toast notification provider
├── ConnectionStatus.tsx - WebSocket connection indicator
├── CommandPalette.tsx   - ⌘K command palette
├── NotificationCenter.tsx - Notification dropdown
└── PageTransition.tsx   - Framer Motion page transitions
```

## Total: ~110+ components across 14 categories
