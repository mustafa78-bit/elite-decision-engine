# NEXUS Core Identity Unification Documentation

## Overview
This document outlines the transition from the legacy **OLLO** identity to the unified **NEXUS** Core platform identity, executing Sprint A: NEXUS Core Identity.

## Identity Definitions
NEXUS serves three key functions:
1. **AI Commander** — Real-time headquarters system operator overseeing all subsystems.
2. **Chief Investment Officer (CIO)** — Top-tier investment decision advisor.
3. **Decision Intelligence Core** — Single source of truth for market analytics, council consensus, and risk assessment.

## Backward Compatibility & Deprecation
To preserve 100% backend compatibility for external clients and integrated services, all legacy `/ollo/*` REST endpoints remain active and fully supported as deprecated compatibility aliases.
- **Legacy Endpoint:** `/ollo/query` -> **New Alias Endpoint:** `/nexus/query` (mapped in `api/routes/ollo.py` and registered in `api/main.py`).
- **Unified Health Endpoint:** `/health/ai` has been implemented to aggregate status indicators for both components.

## Unified Frontend Architecture
All visual elements, labels, and widgets have been migrated to NEXUS. The central breathing orb and layout status indicators now refer strictly to the NEXUS Guide/Commander.
