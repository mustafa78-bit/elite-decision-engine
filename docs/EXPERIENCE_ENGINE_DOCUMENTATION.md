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

### XI-2: Instinct State
- **Purpose**: Synthesizes a continuously evolving behavioral disposition vector representing situational intuition.
- **Disposition Vector**:
  - `courage`: Willingness to act when General Knowledge is highly divergent.
  - `defensiveness`: Active risk-aversion, scaling up on consecutive losses and decaying during winning streaks.
  - `conviction`: Situational certainty based on recent chronological outcomes.
  - `adaptability`: Speed of instinct shifts when experiencing regime transitions.
- **Service**: `InstinctStateService` recalculates and evolves these stateful multipliers chronologically. Auxiliar statistics (win rate, profit factor) contribute to but do not define the instinct.

### XI-3: Familiarity Signal
- **Purpose**: Determines the situational familiarity of current market snapshots.
- **Optimization**: To avoid turning the signal into a costly database retrieval engine, `FamiliaritySignalService` directly consults the distilled `InstinctState` and its active disposition vectors rather than scanning the raw `ExperienceSubstrate` on every request.

### XI-4: Experience vs Knowledge
- **Purpose**: Contrats general rule-based pre-trained models (Knowledge: *"What should happen?"*) with lived empirical results (Experience: *"What has actually happened?"*).
- **Principle**: Keeps these dimensions entirely independent without merging them into a single score, allowing multi-dimensional cognitive decision matching.
- **Service**: `ExperienceVsKnowledgeService` exposes an independent contrast matrix of the two separate axes.

### XI-5: Experience Sufficiency
- **Purpose**: Prevents premature instinct-based decisions by checking if an environment has logged enough chronological duration and observations.
- **Thresholds**: Evaluates minimum logged events (minimum 5) and exposure duration (minimum 24 hours of chronological living).

### XI-6: Graduation & Governance
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
- `POST /api/v1/experience/test-produce`: Controlled simulation/testing utility.

---

## 3. Experience Visualization HUD

Located at `/experience-engine` in the frontend page `frontend/src/pages/ExperienceEngine.tsx`.
- **Evolving Instinct**: Displays the four key disposition metrics (Courage, Defensiveness, Conviction, Adaptability) as glowing telemetry blocks.
- **Lived Timeline**: Features a vertical glowing walk-forward experience path showing sequential trades.
- **Familiarity**: Visualizes situation familiarity dials.
- **Governance Center**: Allows the operator to explicitly approve or reject graduation recommendations, directly modifying governing bounds.
- **Sandbox Experience Simulator**: Contains an interactive trigger allowing developers/operators to manually inject experiences into the chronological substrate and witness instinct and sufficiency states evolve in real-time.
