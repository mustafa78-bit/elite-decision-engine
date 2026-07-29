# NEXUS DATA INTEGRITY REPORT (SPRINT 18)

## 1. Relational Database Schema Design
NEXUS uses SQL schema modeling with strict primary and foreign key constraints to ensure relational correctness.

```
+------------------+         +------------------+
|      Signal      |         |  DecisionExplanation |
|------------------|         |------------------|
| id (PK)          | <------+ | signal_id        |
| symbol           |         | symbol           |
| approved         |         | summary          |
+------------------+         +------------------+
         |
         |
         v
+------------------+         +------------------+
|      Trade       |         |   JournalEntry   |
|------------------|         |------------------|
| id (PK)          | <------+ | trade_id         |
| signal_id        |         | entry_price      |
| status           |         | result           |
+------------------+         +------------------+
```

---

## 2. Integrity Verification & Cleanups

*   **Orphan Rows Prevention**: When deleting or editing trade structures, database operations are transactionally safe.
*   **Duplicate Signalling Prevention**: `TradeEngine.create_trade` checks for duplicate active signals on the same asset and side before creating new positions.
*   **Sealed State Enforcements**: When a trade is closed, the status is frozen to final states (`TP_HIT`, `SL_HIT`, `CLOSED`). No further P&L modifications are permitted.
