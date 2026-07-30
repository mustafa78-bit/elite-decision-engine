# Sprint XI — Experience Engine Documentation

## Core Architectural Vision

The **NEXUS Experience Engine** represents a distinct cognitive layer built upon the principle that **Experience is earned only through chronological living**.

It separates itself entirely from static memory, backtesting, historical replay, or rule-based knowledge. It implements a strict, blind, walk-forward chronological paradigm where the platform develops a continuously evolving instinct state based on chronological feedback.

---

## 1. Subsystems (XI-1 to XI-6)

### XI-1: Experience Substrate
- **Purpose**: A raw, immutable database of chronological lived platform experiences.
- **Model**: `ExperienceSubstrate` (table: `experience_substrates`).
- **Fields**: `id`, `timestamp`, `symbol`, `timeframe`, `state_snapshot` (JSON indicators snapshot), `action_taken` (LONG, SHORT, REJECT), `outcome` (Float PnL), `realized_at` (DateTime outcome known).
- **Service**: `ExperienceSubstrateService` implements absolute walk-forward lookups (`timestamp <= target_time`) ensuring zero lookahead/hindsight leakage.

### XI-2: Instinct State (Incremental $O(1)$ Evolution)
- **Purpose**: Synthesizes a continuously evolving, stateful behavioral disposition vector representing situational intuition.
- **Incrementalism**: Rather than replaying history or performing database scans, the Instinct State is evolved incrementally on the fly inside `update_instinct_incrementally` in $O(1)$ constant time for every newly realized experience.
- **Disposition Vector**:
  - `courage`: Evolving willingness to counter standard rules.
  - `defensiveness`: Active risk-aversion, scaling up dynamically on losses and decaying during wins.
  - `conviction`: Situational certainty based on recent chronological outcomes.
  - `adaptability`: Speed of instinct shifts when experiencing regime transitions.
- **Auxiliary Statistics**: Aggregated fields (win rate, profit factor, total trades, average PnL) contribute to instinct but *do not* define it.

### XI-3: Familiarity Signal (Pre-Distilled, Extensible Design)
- **Purpose**: Determines situational familiarity of current market snapshots.
- **Database Shield**: To avoid turning the engine into a database retrieval scanner, it directly consults the distilled `InstinctState` (single-row lookup) rather than querying the entire `ExperienceSubstrate` history.
- **Extensible Architecture**: Structured using a dynamic evaluator registry (`FamiliaritySignalService.register_evaluator()`) to allow future dimensions (e.g., volatility profile, market structure) to be integrated without structural redesign.

### XI-4: Experience vs Knowledge
- **Purpose**: Contrasts general rule-based pre-trained models (Knowledge: *"What should happen?"*) with lived empirical results (Experience: *"What has actually happened?"*).
- **Principle**: Keeps these dimensions entirely independent without merging them into a single score, maintaining separate axes of decision matching.

### XI-5: Experience Sufficiency (Governance Managed)
- **Purpose**: Prevents premature instinct-based decisions by checking if an environment has logged enough chronological duration and observations.
- **Governance**: Policy thresholds (`MIN_EVENTS`, `MIN_HOURS`) are loaded dynamically from `ExperiencePolicy` and can be adjusted by Governance in real-time without code changes.

### XI-6: Graduation & Governance (Recommendation Only)
- **Purpose**: Unlocks active operational multipliers when an environment becomes highly experienced and proficient.
- **Rule**: Graduation **never self-promotes**. The service may only recommend graduation (`status = "RECOMMENDED"`).
- **Governance**: Only explicit administrative/Governor approval (`approve_graduation`) activates graduation and overrides active position/risk multipliers.

---

## 2. API Design & Routing

All routes are read-oriented by default. Writing to the substrate occurs internally through platform living, with the exception of a controlled simulation utility endpoint:
- `GET /api/v1/experience/substrate`: Chronological substrate entries.
- `GET /api/v1/experience/instinct`: Active distilled Instinct and behavioral disposition vector.
- `POST /api/v1/experience/familiarity`: Distilled instinct familiarity calculation.
- `POST /api/v1/experience/contrast`: Independent Knowledge vs Experience contrast dimensions.
- `GET /api/v1/experience/sufficiency`: Sufficiency thresholds validation.
- `GET /api/v1/experience/graduation/recommendation`: Recommends graduation level.
- `POST /api/v1/experience/governance/approve`: Explicit Governance promotion action.
- `POST /api/v1/experience/governance/reject`: Explicit Governance demotion/revocation action.
- `POST /api/v1/experience/governance/policy`: Dynamic modification of thresholds under Governance.
- `POST /api/v1/experience/test-produce`: Controlled simulation/testing utility. **Watertight Blockade**: Exclusively available when `API_ENV == "development"`, returning `403 Forbidden` in production env.

---

## 3. Experience Visualization HUD

Located at `/experience-engine` in the frontend page `frontend/src/pages/ExperienceEngine.tsx`.
- **Evolving Instinct**: Displays the four key disposition metrics (Courage, Defensiveness, Conviction, Adaptability) as glowing telemetry blocks.
- **Lived Timeline**: Features a vertical glowing walk-forward experience path showing sequential trades.
- **Familiarity**: Visualizes situation familiarity dials.
- **Governance Policy Editor**: Allows dynamic adjustment of `MIN_EVENTS` and `MIN_HOURS` thresholds directly on the UI.
- **Governance Center**: Allows the operator to explicitly approve or reject graduation recommendations, directly modifying governing bounds.
- **Sandbox Experience Simulator**: Conditioned on development mode, displaying a watertight "Inactive in Production" state if not in development.
