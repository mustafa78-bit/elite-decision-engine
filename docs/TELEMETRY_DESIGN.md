# NEXUS Telemetry Architecture Design (Sprint 15)

## 1. Executive Summary
This document specifies the architecture, data contracts, and implementation strategy for the internal NEXUS Telemetry Engine. In alignment with the **NEXUS Constitution** and the **Sprint 13 Core Architecture Freeze**, this telemetry system is designed to be minimal, high-utility, and self-contained. It is built entirely using internal services, avoiding any dependency on external third-party tracking services or complex message brokers.

---

## 2. Telemetry Scope & Event Taxonomy
NEXUS telemetry separates structural product workflows (Founder journey metrics) from system operational status (diagnostic events).

### 2.1 Product Workflow Events (Founder Journey)
These events capture high-value stages of the daily continuous Founder workflow:
- `morning_brief_opened` — Tracking the start of the 30-Second Morning.
- `scanner_filters_changed` — Tracking engagement with the discovery engine.
- `signal_viewed` — Tracking individual signal analysis.
- `decision_opened` — Tracking the inspection of decision explanations.
- `evidence_expanded` — Capturing deep audit interactions.
- `trade_executed` — Tracking progression from decision to execution.
- `journal_written` — Capturing post-execution documentation and emotional state logging.
- `replay_viewed` — Tracking cognitive debugging and learning.
- `end_of_day_completed` — Tracking daily workflow sealing.
- `weekly_review_completed` — Tracking executive weekly reviews.
- `personal_insights_viewed` — Tracking systemic learning widget visits.

### 2.2 Product Analytics vs. Diagnostic Events
- **Product Analytics Events**: High-fidelity events focusing on user flow completion, interaction latency, and decision paths. These are persisted to the telemetry stream database.
- **Diagnostic Events**: Low-level exception traces, memory footprints, and raw connection states. These are generated as structured logs on the server side and exposed via the engineering dashboard, avoiding database bloating.

---

## 3. Telemetry Event Schema Contract
The database schema for telemetry is kept extremely lean to prevent performance overhead.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | Integer | No | Primary Key |
| `timestamp` | DateTime(TZ) | No | When the event occurred (server-logged or client-reported) |
| `screen` | String(100) | No | The active screen / workspace (e.g. `command_deck`, `decision_center`) |
| `action` | String(100) | No | The event verb / interaction type (e.g. `opened`, `executed`) |
| `duration` | Float | Yes | Time spent on the screen or performing the action (in seconds) |
| `outcome` | String(100) | Yes | Success/failure/status or selected recommendation classification |

### 3.1 Privacy and Data Protection
No personal notes, raw API credentials, trade balances, trade IDs, or emotional text entries are captured. Only structured metrics (e.g., `duration: 45.2`, `outcome: "success"`) are stored.

---

## 4. Operational Metrics & Sizing Estimations
- **Expected Volume**: An active Founder generates ~50–150 telemetry events per day.
- **Data Footprint**: At ~200 bytes per row, 150 events/day equals **~30 KB/day** or **~11 MB/year**.
- **Retention Policy**: Stored in the active DB for **90 days**. After 90 days, old telemetry events are pruned or rolled up into daily aggregate metrics (Daily Active Founder, Daily Workflows).
- **Required Indexes**:
  - Index on `timestamp` (for temporal aggregation and time-range queries).
  - Composite Index on `(screen, action)` (to accelerate screen-specific drop-off queries).

---

## 5. Architectural Alignment & Freeze Compliance
This telemetry engine operates entirely within the constraints of the **Core Architecture Freeze**:
- No new external ports, message queues (Kafka, Redis), or external agents are introduced.
- Telemetry logging uses non-blocking backend processing or clean async API endpoints.
- Database storage leverages the existing SQLAlchemy engine via a simple table.
