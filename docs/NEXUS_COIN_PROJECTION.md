# NEXUS Coin Projection Specification (v1.0.0)

This document describes the design, schema, lifecycle, APIs, and recovery strategies for the **CoinProjection** business projection. It represents the first business-specific projection deployed on top of the NEXUS Layer 1 (Materialized Views) Projection Framework.

---

## 1. Multi-Layer Architecture

The Coin Projection behaves as a deterministic, pure projection layer. It continuously consumes immutable chronological event sequences from the L0 Event Log and materializes the latest aggregate state for every asset inside the `l1_coin_views` database table.

```
┌──────────────────────────────────────────────┐
│              L0: EVENT LOG                   │
│   PriceUpdated, NewsPublished, etc. (Store)  │
└──────────────────────┬───────────────────────┘
                       │
                       │ Sequential Read
                       ▼
┌──────────────────────────────────────────────┐
│         L1 PROJECTION FRAMEWORK              │
│   EventDispatcher & ProjectionRunner         │
└──────────────────────┬───────────────────────┘
                       │
                       │ Routing & Execution
                       ▼
┌──────────────────────────────────────────────┐
│         BUSINESS COINPROJECTION              │
│   Applies changes and tracks progress        │
└──────────────────────┬───────────────────────┘
                       │
                       │ Database Commits
                       ▼
┌──────────────────────────────────────────────┐
│            COINVIEW TABLE (L1 DB)            │
│   Single, optimized latest record per coin   │
└──────────────────────────────────────────────┘
```

---

## 2. L1 CoinView Data Model

The `l1_coin_views` table keeps exactly **one current record per tracked asset**, indexed by its unique asset symbol.

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `coin_id` | String(36) | Primary Key (UUID format). |
| `symbol` | String(20) | Unique Asset Symbol (e.g. "BTC", "ETH"), Indexed. |
| `latest_price` | Float | The last processed trading price from the price feeds. |
| `last_price_timestamp` | DateTime | Timestamp of the event that updated `latest_price`. |
| `market_regime` | String(50) | Detected trend regime (e.g., BULLISH, RANGE, BEARISH). |
| `trust_score` | Float | Post-mortem learning trust score. |
| `confidence_score` | Float | AI council consensus or indicator confidence score. |
| `latest_news_id` | String(36) | UUID reference of the latest news intelligence event. |
| `latest_news_timestamp` | DateTime | Release timestamp of the latest news event. |
| `latest_whale_activity`| JSON | Dictionary payload describing the latest transaction details. |
| `active_patterns` | JSON | List of currently active technical indicators or chart patterns. |
| `calibration_version` | String(20) | Adaptive learning version representing the current model. |
| `trust_version` | String(20) | Version metadata of the active trust scorer. |
| `replay_seq_id` | Integer | High-watermark sequence ID of the last event applied to this record. |
| `updated_at` | DateTime | ISO-8601 timestamp of when the view record was last written. |

---

## 3. Supported L0 Events & Mapping Rules

Each incoming event is parsed and updates **only the fields directly relevant** to that event.

1. **`PriceUpdated`**:
   - Updates `latest_price` and `last_price_timestamp`.
2. **`TradeExecuted`**:
   - Updates `updated_at` and system metrics.
3. **`WhaleActivity`**:
   - Updates `latest_whale_activity` structure with the latest transaction metrics.
4. **`NewsPublished`**:
   - Resolves all listed symbols inside `related_assets`. For each symbol, updates `latest_news_id` and `latest_news_timestamp`.
5. **`CalibrationUpdated`**:
   - Updates `calibration_version` metadata.
6. **`TrustUpdated`**:
   - Updates `trust_score` and `trust_version`.
7. **`PatternDetected`**:
   - Adds the new pattern to the coin's list of `active_patterns` (guaranteeing uniqueness).
8. **`MarketRegimeChanged`**:
   - Updates `market_regime` and `confidence_score` of the coin.

*Any event type not present in this list is skipped gracefully.*

---

## 4. Replay and Rebuild Lifecycle

The Projection Framework guarantees **100% determinism** and **exact idempotency** across all rebuild actions:

- **Idempotency**: Every record maintains a `replay_seq_id`. If an event with `seq_id <= record.replay_seq_id` is processed, it is automatically discarded as a duplicate/out-of-order event, preventing data regression.
- **Incremental Rebuild**: Reads only from `last_processed_seq_id + 1` up to the max seq_id in the event log, minimizing processing costs.
- **Full Rebuild**: Truncates the `l1_coin_views` table, resets all runner metrics to 0, and replays all events starting sequentially from sequence `1`.
- **Snapshot Recovery**:
  1. The projection dumps its state as a serialized JSON blob using `snapshot()`.
  2. To restore, `restore_snapshot()` clears the active database, loads the blob, and writes it directly.
  3. The runner updates the `ProjectionState` checkpoint sequence ID.
  4. Subsequent replays resume exactly after the snapshot checkpoint.

---

## 5. API Reference

All routes are prefix-isolated under `/nexus/l1/coin` to maintain complete separation from general routing.

- **`POST /nexus/l1/coin/rebuild`**: Triggers a clean full rebuild of the view from sequence 1.
- **`POST /nexus/l1/coin/replay`**: Triggers a manual sequential range replay with optional `start_seq_id` and `end_seq_id`.
- **`GET /nexus/l1/coin/state`**: Lists the current materialized view state of all coins.
- **`GET /nexus/l1/coin/lookup/{symbol}`**: Returns the latest state for a single coin.
- **`GET /nexus/l1/coin/statistics`**: Exposes processing metrics: total materialized coins, processed events, ignored events, and failed updates.
- **`GET /nexus/l1/coin/health`**: Returns the framework checkpoint sequence, health status, and update latency diagnostics of CoinProjection.

---

## 6. Recovery and Failure Strategy

In production, database connections can experience temporary network lag or lockups. The Coin Projection implements the following resilience patterns:
1. **Transient Failure Retries**: If an event application fails, the runner performs up to 3 immediate retries with a small backoff.
2. **Crash Recovery**: If execution is permanently interrupted, the runner records a `FAILED` rebuild status and a `DEGRADED` health state with the corresponding error message in the `ProjectionState` table.
3. **Safe Resume**: Because progress checkpoints are stored permanently in the database, when the system restarts, it reads the checkpoint and resumes incremental processing from the last successfully processed event sequence, guaranteeing zero data drift.
