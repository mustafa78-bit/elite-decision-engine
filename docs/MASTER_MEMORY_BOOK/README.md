# NEXUS Autonomous Decision Intelligence Platform (ADIP)
## 🏛️ Master Memory Book: The Ultimate Engineering Knowledge Base

Welcome to the **NEXUS Autonomous Decision Intelligence Platform (ADIP) Master Memory Book**.

This repository of knowledge is **not** a basic readme, nor is it a temporary onboarding guide. It is the **permanent engineering memory** of the entire NEXUS ecosystem. Built directly from rigorous codebase analysis and architectural realities, this book stands as the single source of truth (SSoT) for any senior engineer, architect, CTO, or Founder joining the project.

---

## 🗺️ How to Navigate the Memory Book

The knowledge base is structured logically to take you from high-level platform vision down to the exact mathematical mechanics, database relations, API signatures, and deployment runbooks.

### Table of Contents (Chapter Map)

* **Part I: High-Level Foundations & Architecture**
  * [Chapter 01: Project Vision](01_PROJECT_VISION.md) - Why NEXUS exists, the core product philosophy, and target demographics.
  * [Chapter 02: System Architecture](02_SYSTEM_ARCHITECTURE.md) - The macro-scale, high-density component mapping, block diagrams, and system data lifecycle.
  * [Chapter 03: Repository Structure](03_REPOSITORY_STRUCTURE.md) - File organization, module boundaries, and architectural layers.

* **Part II: Subsystem Deep-Dives**
  * [Chapter 04: Backend Architecture](04_BACKEND_ARCHITECTURE.md) - FastAPI design, middleware orchestration, default-deny paradigms, and context boundaries.
  * [Chapter 05: Frontend Architecture](05_FRONTEND_ARCHITECTURE.md) - React 19 + Vite 8 workspace, high-density HUD UI, state structures (Zustand & React Query).
  * [Chapter 06: Database Architecture](06_DATABASE_ARCHITECTURE.md) - SQLAlchemy models, field structures, constraints, relationships, and caching strategies.
  * [Chapter 07: API Reference](07_API_REFERENCE.md) - Detailed catalog of HTTP endpoints, query schemas, and request/response models.
  * [Chapter 08: WebSocket Architecture](08_WEBSOCKET_ARCHITECTURE.md) - Real-time channel multiplexing, token-based socket auth, and periodic broadcast state.

* **Part III: AI & Decision Engines**
  * [Chapter 09: AI Decision Engine](09_AI_DECISION_ENGINE.md) - The multi-stage DecisionPipeline, signal ingestion, filters, scoring components, and confidence calculations.
  * [Chapter 10: Orchestrator](10_ORCHESTRATOR.md) - The ExecutionLoop coordinator and synchronous polling pipeline.
  * [Chapter 11: AI Council](11_AI_COUNCIL.md) - Multi-agent debate systems, consensus direction indexes, and specialized cognitive personas.
  * [Chapter 12: Memory System](12_MEMORY_SYSTEM.md) - Ephemeral caches, permanent JSON stores, and the historical `TradeMemory` feedback loops.
  * [Chapter 13: Evidence Engine](13_EVIDENCE_ENGINE.md) - Cognitive conflict detection, source trace auditability, and structured evidence schemas.

* **Part IV: Risk, Sizing, & Portfolio Operations**
  * [Chapter 14: Risk Engine](14_RISK_ENGINE.md) - 5-rule safety guards, maximum open trade restrictions, and daily loss enforcement.
  * [Chapter 15: Portfolio Engine](15_PORTFOLIO_ENGINE.md) - Portfolio health metrics, Sharpe ratios, win rates, and attribution calculations.
  * [Chapter 16: Execution Engine](16_EXECUTION_ENGINE.md) - The transition from approved signals to active orders, duplicate checks, and persisting trade layers.
  * [Chapter 17: Paper Trading](17_PAPER_TRADING.md) - Zero-risk market simulation, TP/SL monitoring, and stale trade cleanups (7-day rule).

* **Part V: Operational, Security, & Engineering Guides**
  * [Chapter 18: Command Center (CommandDeck)](18_COMMAND_CENTER.md) - The high-density primary workspace React layout, integrations, and telemetry tracking.
  * [Chapter 19: Security Architecture](19_SECURITY.md) - Default-deny middleware, token validation, secure headers, CSP configurations, and password policies.
  * [Chapter 20: Performance Tuning](20_PERFORMANCE.md) - Eviction caches, indexing structures, and memory-safe DB querying.
  * [Chapter 21: Testing Methodology](21_TESTING.md) - Core backend test suite structure, pytest configurations, mock objects, and test runs.
  * [Chapter 22: Deployment Architecture](22_DEPLOYMENT.md) - Production and development setups, Docker configurations, and container environments.
  * [Chapter 23: Operations Runbook](23_OPERATIONS_RUNBOOK.md) - Deployment steps, local seeding commands, diagnostic interfaces, and incident response.

* **Part VI: Onboarding, Decisions, & Roadmap**
  * [Chapter 24: Founder Guide](24_FOUNDER_GUIDE.md) - Principles of Founder Alpha, qualitative feedback systems, and daily workspace loops.
  * [Chapter 25: Developer Onboarding Guide](25_DEVELOPER_GUIDE.md) - Setting up the environment, writing new features, running checks, and repository compliance.
  * [Chapter 26: Architectural Decisions (ADR Register)](26_ARCHITECTURE_DECISIONS.md) - Historic and permanent structural design decisions.
  * [Chapter 27: Release History](27_RELEASE_HISTORY.md) - Architectural milestones from Sprint 17 to Sprint 23 and beyond.
  * [Chapter 28: Technical Debt & Known Limitations](28_TECHNICAL_DEBT.md) - Complete audit of architectural gaps, math discrepancies, and engineering debt.
  * [Chapter 29: System Roadmap](29_ROADMAP.md) - Strategic timeline for future upgrades and enterprise platform additions.
  * [Chapter 30: Glossary of Terms](30_GLOSSARY.md) - Unified nomenclature for the NEXUS platform.

---

## 🧱 The NEXUS Constitution

Every design decision in NEXUS must be measured against a single, absolute core principle:
> **"Will this help the Founder make a better decision today?"**

If a feature, service, or interface does not direct the user toward clear, explainable, and risk-controlled decision-making, it does not belong in the NEXUS system. This platform is not a passive trading bot; it is a high-density, explainable, multi-agent intelligence extension for the human sovereign trader.
