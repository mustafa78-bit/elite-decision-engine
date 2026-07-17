# DTO Inventory

## API Schemas (`api/schemas.py`)

| DTO | Fields | Used By |
|-----|--------|---------|
| APIResponse | success, data, error, version, timestamp, request_id | All routes |
| APIError | code, message, details | Error responses |
| PaginatedResponse | items, total, page, page_size, total_pages, has_next, has_prev, next_page, prev_page | GET /decisions |
| SortParam | field, order | Sort configuration |
| HealthStatus | status, modules, database, uptime_seconds, version, timestamp | GET /health |
| MetricsResponse | evaluate_calls, modules_active, decisions_made, signals_processed, uptime_seconds, memory_entries | GET /metrics |
| DecisionResponse | signal_id, decision, score, confidence, confidence_label, reasons, timestamp | GET /decisions |
| IntelligenceResponse | unified_score, module_scores, health, report | GET /intelligence |

## WebSocket Payloads (`api/websocket.py`)

| DTO | Fields | Description |
|-----|--------|-------------|
| WSEvent | event_type, data, version, timestamp, event_id | Generic WS event |
| WSNotificationPayload | type, title, message, severity | Notification payload |
| WSDashboardPayload | portfolio, intelligence, risk, monitoring | Dashboard snapshot |

## DTO Models (`dto/models.py`)

| DTO | Fields | Extends |
|-----|--------|---------|
| PortfolioDTO | total_trades, win_rate, total_pnl, average_pnl_pct, open_trades, largest_win, largest_loss | SerializableMixin |
| TradeDTO | id, symbol, side, entry_price, exit_price, pnl, pnl_pct, status, created_at | SerializableMixin |
| IntelligenceDTO | unified_score, *health fields, module_scores, contribution_report | SerializableMixin |
| RiskDTO | risk_score, max_drawdown, volatility, sharpe_ratio, at_risk_trades | SerializableMixin |
| MonitoringDTO | evaluate_calls, modules_active, decisions_today, uptime_hours, last_evaluation, memory_usage_mb | SerializableMixin |
| NotificationDTO | type, title, message, severity, timestamp | SerializableMixin |
| WebSocketDTO | event, data, version | SerializableMixin |
| DashboardDTO | portfolio, intelligence, risk, monitoring, recent_decisions, recent_notifications | - |
