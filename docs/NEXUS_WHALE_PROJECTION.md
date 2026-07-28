# NEXUS Whale Projection Specification (v1.0.0)

This document describes the design, schema, lifecycle, APIs, and recovery strategies for the **WhaleProjection** business projection. It tracks on-chain wallet metrics and portfolio structures on top of the NEXUS Layer 1 (Materialized Views) Projection Framework.

---

## 1. Multi-Layer Architecture

The Whale Projection behaves as a deterministic, pure projection layer. It continuously consumes immutable chronological event sequences from the L0 Event Log and materializes the latest aggregate state for every tracked whale wallet inside the `l1_whale_views` database table.

```
┌──────────────────────────────────────────────┐
│              L0: EVENT LOG                   │
│   WhaleActivity, WhaleTransaction (Store)    │
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
│        BUSINESS WHALEPROJECTION              │
│   Applies changes and tracks progress        │
└──────────────────────┬───────────────────────┘
                       │
                       │ Database Commits
                       ▼
┌──────────────────────────────────────────────┐
│           WHALEVIEW TABLE (L1 DB)            │
│   Single, optimized latest record per wallet │
└──────────────────────────────────────────────┘
```

---

## 2. L1 WhaleView Data Model

The `l1_whale_views` table keeps exactly **one current record per wallet**, indexed by the unique blockchain address/id of the wallet.

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `wallet_id` | String(100) | Primary Key (blockchain address or identifier). |
| `total_events` | Integer | Total number of L0 events processed for this wallet. |
| `accumulation_score` | Float | Percentage score representing token accumulation. |
| `distribution_score` | Float | Percentage score representing token distribution. |
| `realized_accuracy` | Float | Historically tracked transaction prediction accuracy. |
| `trust_score` | Float | Post-mortem learning trust score assigned by AI Council. |
| `last_activity` | DateTime | Timestamp of the event that updated this wallet. |
| `exchange_distribution`| JSON | Distributing of tokens across exchanges. |
| `active_positions` | JSON | List of currently active token assets/positions held. |
| `replay_seq_id` | Integer | High-watermark sequence ID of the last event applied to this record. |

---

## 3. Supported L0 Events & Mapping Rules

Each incoming event is parsed and updates **only the fields directly relevant** to that event.

1. **`WhaleActivity`**:
   - Updates `accumulation_score`, `distribution_score`, `trust_score`, `exchange_distribution`.
2. **`WhaleTransaction`**:
   - Updates `realized_accuracy`.
   - Appends/removes token symbols inside `active_positions` list dynamically based on `action="BUY"` or `action="SELL"`.

*Any event type not present in this list is skipped gracefully.*

---

## 4. Replay and Rebuild Lifecycle

The Projection Framework guarantees **100% determinism** and **exact idempotency** across all rebuild actions:

- **Idempotency**: Every record maintains a `replay_seq_id`. If an event with `seq_id <= record.replay_seq_id` is processed, it is automatically discarded as a duplicate/out-of-order event, preventing data regression.
- **Incremental Rebuild**: Reads only from `last_processed_seq_id + 1` up to the max seq_id in the event log, minimizing processing costs.
- **Full Rebuild**: Truncates the `l1_whale_views` table, resets all runner metrics to 0, and replays all events starting sequentially from sequence `1`.
- **Snapshot Recovery**:
  1. The projection dumps its state as a serialized JSON blob using `snapshot()`.
  2. To restore, `restore_snapshot()` clears the active database, loads the blob, and writes it directly.
  3. The runner updates the `ProjectionState` checkpoint sequence ID.
  4. Subsequent replays resume exactly after the snapshot checkpoint.

---

## 5. API Reference

All routes are prefix-isolated under `/nexus/l1/whale` to maintain complete separation from general routing.

- **`POST /nexus/l1/whale/rebuild`**: Triggers a clean full rebuild of the view from sequence 1.
- **`POST /nexus/l1/whale/replay`**: Triggers a manual sequential range replay with optional `start_seq_id` and `end_seq_id`.
- **`GET /nexus/l1/whale/state`**: Lists the current materialized view state of all wallets.
- **`GET /nexus/l1/whale/lookup/{wallet_id}`**: Returns the latest state for a single wallet.
- **`GET /nexus/l1/whale/statistics`**: Exposes processing metrics: total materialized wallets, processed events, ignored events, and failed updates.
- **`GET /nexus/l1/whale/health`**: Returns the framework checkpoint sequence, health status, and update latency diagnostics of WhaleProjection.

---

## 6. Recovery and Failure Strategy

In production, database connections can experience temporary network lag or lockups. The Whale Projection implements the following resilience patterns:
1. **Transient Failure Retries**: If an event application fails, the runner performs up to 3 immediate retries with a small backoff.
2. **Crash Recovery**: If execution is permanently interrupted, the runner records a `FAILED` rebuild status and a `DEGRADED` health state with the corresponding error message in the `ProjectionState` table.
3. **Safe Resume**: Because progress checkpoints are stored permanently in the database, when the system restarts, it reads the checkpoint and resumes incremental processing from the last successfully processed event sequence, guaranteeing zero data drift.
