# API Report — Elite Decision Engine

## Overview

The API exposes 10 endpoints for health monitoring, decision history, intelligence, and module diagnostics. All responses follow a standardized envelope format with support for pagination, filtering, sorting, and request tracking.

## Endpoint Inventory

| # | Method | Path | Description | Parameters |
|---|--------|------|-------------|------------|
| 1 | GET | `/health` | Health status (modules, database, uptime) | None |
| 2 | GET | `/ready` | Readiness probe | None |
| 3 | GET | `/live` | Liveness probe | None |
| 4 | GET | `/metrics` | Runtime metrics | None |
| 5 | GET | `/decisions` | Paginated decision history | page, page_size, decision, sort_by, sort_order, score_min, score_max, status, date_from, date_to |
| 6 | GET | `/decisions/:id` | Single decision by signal ID | signal_id (path) |
| 7 | GET | `/intelligence` | Unified intelligence score + module scores | None |
| 8 | GET | `/features` | All module features | None |
| 9 | GET | `/modules` | Module diagnostics | None |
| 10 | GET | `/app` | Application metadata | None |

## Response Envelope

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "version": "1.0.0",
  "timestamp": "2026-07-09T12:00:00.000Z",
  "request_id": "a1b2c3d4e5f6"
}
```

## Pagination

| Field | Type | Description |
|-------|------|-------------|
| items | array | Page items |
| total | int | Total matching items |
| page | int | Current page (1-indexed) |
| page_size | int | Items per page (1-100) |
| total_pages | int | Total pages |
| has_next | bool | More pages available |
| has_prev | bool | Previous page exists |
| next_page | int or null | Next page number |
| prev_page | int or null | Previous page number |

## Filtering (GET /decisions)

| Parameter | Type | Description |
|-----------|------|-------------|
| decision | string | Filter by: APPROVED, REJECTED |
| score_min | float | Minimum score |
| score_max | float | Maximum score |
| status | string | Status filter |
| date_from | string | Start timestamp (ISO 8601) |
| date_to | string | End timestamp (ISO 8601) |

## Sorting (GET /decisions)

| Parameter | Type | Default | Values |
|-----------|------|---------|--------|
| sort_by | string | timestamp | score, confidence, timestamp, signal_id, decision |
| sort_order | string | desc | asc, desc |

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| BAD_REQUEST | 400 | Invalid parameters |
| NOT_FOUND | 404 | Resource not found |
| CONFLICT | 409 | Resource conflict |
| VALIDATION_ERROR | 422 | Validation failure |
| RATE_LIMITED | 429 | Rate limit exceeded |
| INTERNAL_ERROR | 500 | Internal server error |
| SERVICE_UNAVAILABLE | 503 | Service degraded |

## WebSocket Events

| Event Type | Description |
|------------|-------------|
| decision | New decision produced |
| signal | Raw signal received |
| intelligence | Intelligence bundle updated |
| health | Health status changed |
| metrics | Runtime metrics updated |
| trade | Trade lifecycle event |
| notification | Notification event |
| dashboard | Dashboard snapshot |
| error | Error event |

## Backward Compatibility

All existing response shapes are preserved. New fields (request_id, pagination navigation) are additive. New error types inherit from the existing APIException hierarchy. All existing 521 tests continue to pass (now 555 total).
