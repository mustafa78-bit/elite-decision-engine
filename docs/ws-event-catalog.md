# WebSocket Event Catalog

## Connection
```
ws://<host>:<port>/ws
```

## Event Envelope
```json
{
  "event_type": "string",
  "data": {},
  "version": "2.0",
  "timestamp": "ISO 8601",
  "event_id": "string"
}
```

## Event Types

### decision
Fired when the engine produces a new decision.
```json
{
  "signal_id": 1,
  "decision": "APPROVED",
  "score": 88.5,
  "confidence": 75.0,
  "confidence_label": "HIGH",
  "reasons": {"approval": [], "rejection": []},
  "timestamp": "2026-07-09T12:00:00Z"
}
```

### signal
Fired when a new raw signal is received.
```json
{
  "signal_id": 1,
  "symbol": "BTC",
  "side": "LONG",
  "timeframe": "1h",
  "score": 85.0
}
```

### intelligence
Fired when the intelligence bundle is evaluated.
```json
{
  "unified_score": 72.3,
  "module_scores": {"whale": 85.0, "liquidity": 60.0},
  "health": {"whale": true, "liquidity": false}
}
```

### health
Fired when system health status changes.
```json
{
  "status": "healthy",
  "modules": {"whale": true},
  "database": "connected",
  "uptime_seconds": 3600.0
}
```

### metrics
Fired when runtime metrics update.
```json
{
  "evaluate_calls": 42,
  "modules_active": 4,
  "decisions_made": 15,
  "uptime_seconds": 3600.0
}
```

### trade
Fired when a trade lifecycle event occurs.
```json
{
  "symbol": "BTC",
  "side": "LONG",
  "entry_price": 50000,
  "exit_price": 55000,
  "pnl": 5000,
  "status": "CLOSED"
}
```

### notification
Fired when a system notification is generated.
```json
{
  "type": "info",
  "title": "Module restored",
  "message": "Liquidity module healthy again",
  "severity": "low"
}
```

### dashboard
Fired with a periodic dashboard snapshot.
```json
{
  "portfolio": {"total_trades": 42, "win_rate": 68.5},
  "intelligence": {"unified_score": 72.3},
  "risk": {"risk_score": 25.0},
  "monitoring": {"evaluate_calls": 42}
}
```

### error
Fired when an error occurs.
```json
{
  "code": "SERVICE_UNAVAILABLE",
  "message": "Whale module unhealthy",
  "details": {}
}
```
