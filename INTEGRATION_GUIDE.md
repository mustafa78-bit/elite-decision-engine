# Elite Terminal — Integration Guide

## Overview

The Elite Decision Engine exposes a stateless HTTP API and a real-time WebSocket channel. All responses follow a unified `envelope` format.

## Base URL

```
http://localhost:8000
```

## Authentication

Not implemented. The API is intended to run behind a reverse proxy (nginx, Caddy) that handles auth (Basic, JWT, mTLS). Place the engine on a private network or use a VPN in production.

## Response Envelope

Every endpoint returns:

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "version": "1.0.0",
  "timestamp": "2026-07-09T12:00:00.000Z"
}
```

On error:

```json
{
  "success": false,
  "data": null,
  "error": { "code": "NOT_FOUND", "message": "Signal 999 not found", "details": null },
  "version": "1.0.0",
  "timestamp": "2026-07-09T12:00:00.000Z"
}
```

Error codes: `NOT_FOUND` (404), `VALIDATION_ERROR` (422), `SERVICE_UNAVAILABLE` (503), `UNEXPECTED_ERROR` (500).

## Endpoints

### Health

```
GET /health
```

```json
{
  "data": {
    "status": "healthy",
    "modules": { "whale": true, "liquidity": true, "orderflow": true, "market_structure": true, "news": true, "sentiment": true, "macro": true },
    "database": "connected",
    "uptime_seconds": 1234.56,
    "version": "1.0.0",
    "timestamp": "2026-07-09T12:00:00.000Z"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `healthy`, `degraded`, or `unhealthy` |
| `modules` | object | Per-module boolean health |
| `database` | string | `connected`, `degraded`, `error`, or `unknown` |

### Readiness & Liveness

```
GET /ready   → { "data": { "ready": true, "status": "ready" } }
GET /live    → { "data": { "alive": true, "status": "alive" } }
```

### Metrics

```
GET /metrics
```

```json
{
  "data": {
    "evaluate_calls": 42,
    "modules_active": 4,
    "decisions_made": 15,
    "signals_processed": 15,
    "uptime_seconds": 1234.56,
    "memory_entries": 0
  }
}
```

### Decisions

```
GET /decisions?page=1&page_size=10&decision=APPROVED
```

Query params: `page` (int, default 1), `page_size` (int, default 10), `decision` (string, optional filter: `APPROVED` or `REJECTED`).

```json
{
  "data": {
    "items": [
      {
        "signal_id": 1,
        "decision": "APPROVED",
        "score": 88.5,
        "confidence": 75.0,
        "confidence_label": "HIGH",
        "reasons": { "approval": ["whale accumulation detected"], "rejection": [] },
        "timestamp": "2026-07-09T12:00:00.000Z"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 10,
    "total_pages": 1
  }
}
```

```
GET /decisions/42
```

Returns `{ "success": true, "data": { "signal_id": 42, ... } }` or `404`.

### Intelligence

```
GET /intelligence
```

```json
{
  "data": {
    "unified_score": 72.3,
    "module_scores": { "whale": 85.0, "liquidity": 60.0, "orderflow": 45.0, "market_structure": 78.0, "news": 90.0, "sentiment": 55.0, "macro": 65.0 },
    "health": { "whale": true, "liquidity": false, "orderflow": false, "market_structure": true, "news": true, "sentiment": true, "macro": true },
    "report": { ... }
  }
}
```

### Features & Modules

```
GET /features    → { "data": { "whale": [...], "liquidity": [...], ... } }
GET /modules     → { "data": { "module_name": { "enabled": true, "healthy": true, ... }, ... } }
```

## WebSocket

### Connection

```
ws://localhost:8000/ws
```

### Event Format

```json
{
  "event_type": "decision",
  "data": { "signal_id": 1, "decision": "APPROVED", "score": 88.5 },
  "version": "1.0",
  "timestamp": "2026-07-09T12:00:00.000Z"
}
```

### Event Types

| Type | Description |
|------|-------------|
| `decision` | New decision produced |
| `signal` | Raw signal received |
| `intelligence` | Intelligence bundle updated |
| `health` | Health status changed |
| `metrics` | Runtime metrics updated |
| `trade` | Trade lifecycle event |
| `error` | Error event |

### Client Example (JavaScript)

```javascript
const ws = new WebSocket("ws://localhost:8000/ws");
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  switch (msg.event_type) {
    case "decision":
      console.log("Decision:", msg.data);
      break;
    case "health":
      console.log("Health status:", msg.data);
      break;
  }
};
```

## Dashboard DTO (Composite)

The dashboard pulls portfolio, intelligence, risk, and monitoring into one payload. You can construct it on the frontend using `/intelligence`, `/metrics`, and `/decisions`, or call the engine's aggregation layer directly.

```json
{
  "portfolio": {
    "total_trades": 42,
    "win_rate": 68.5,
    "total_pnl": 15230.0,
    "average_pnl_pct": 3.2,
    "open_trades": 2,
    "largest_win": 5200.0,
    "largest_loss": -1800.0
  },
  "intelligence": { "unified_score": 72.3, "module_scores": {...}, "health": {...}, "contribution_report": {...} },
  "risk": { "risk_score": 0.0, "max_drawdown": 0.0, "volatility": 0.0, "sharpe_ratio": 0.0, "at_risk_trades": 0 },
  "monitoring": { "evaluate_calls": 42, "modules_active": 4, "decisions_today": 15, "uptime_hours": 0.34, "last_evaluation": "...", "memory_usage_mb": 0.0 },
  "recent_decisions": [ ... ],
  "recent_notifications": [ { "type": "info", "title": "Module restored", "message": "Liquidity module is healthy again", "severity": "low", "timestamp": "..." } ]
}
```

## Error Handling

All errors follow the envelope format. Handle by checking `success === false`, then inspect `error.code`.

| Code | HTTP Status | Meaning |
|------|-------------|---------|
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 422 | Invalid parameters |
| `SERVICE_UNAVAILABLE` | 503 | Service degraded |
| `UNEXPECTED_ERROR` | 500 | Internal error |

## Tips

- **Polling**: Use `/health` every 30s, `/intelligence` every 60s, `/decisions` on page load + refresh.
- **Real-time**: For live updates, use the WebSocket (`/ws`) instead of polling.
- **CORS**: The engine does not set CORS headers. Add a reverse proxy or configure CORS middleware if calling from a browser.
- **Rate limiting**: Not built in. Add at the reverse proxy layer.
