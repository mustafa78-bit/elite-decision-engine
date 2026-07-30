# Chapter 20: Performance Tuning

## ⚡ High-Throughput System Tuning
To support real-time data visualization on high-density trader HUDs without performance degradation, NEXUS optimizes performance across its database, memory cache, and network broadcast layers.

---

## 🗄️ Database Optimizations & Indexing
The relational database utilizes targeted index configurations in `database.py` to prevent query bottlenecks during active market ticks:
- **`Signal.status` & `Signal.created_at`**: Optimized for high-frequency signal polling and historic performance analysis.
- **`Trade.status` & `Trade.symbol`**: Speeds up position matching, duplicate checks, and open trade calculations.
- **`Notification.read` & `Notification.created_at`**: Accelerates notification feeds on the HUD layout.

---

## 💾 Bounded Memory Caches
To prevent memory leaks and high CPU usage from unbounded historical arrays, NEXUS applies strict size constraints to its in-memory data structures:
- **`DashboardCache`**: Capped at **1000 items**. Automatically evicts older items using a first-in-first-out (FIFO) eviction strategy.
- **`FeatureStore`**: Capped at **5000 records** to prevent historical candle streams from causing memory pressure.
- **`TradeMemory` Cache**: Restricts records to **500 items**, preventing memory growth during active simulation runs.

---

## 📡 Optimized WebSocket Broadcasts
Rather than broadcasting individual data updates as they happen (which can flood client browsers and degrade performance), NEXUS optimizes its network broadcast pipelines:
- **`Event Debouncing`**: Groups multiple transactional events (e.g. notifications) into consolidated websocket pushes.
- **`Scheduled Periodic State Pushes`**: Gathers market pricing, trend classifications, and risk diagnostics, sending them as a single, combined state payload (`MarketEvent` or `RiskEvent`) on a **30-second interval**.
- This reduces network overhead, lowers server CPU usage, and prevents client browser layouts from lagging under rapid price ticks.
