# Chapter 29: System Roadmap

## 📌 Purpose
The **System Roadmap** provides a realistic, strategic timeline for upgrading the NEXUS platform. It is focused on transitioning the platform from **Founder Alpha** to **Closed Beta**, prioritizing stability, security, and developer efficiency over hypothetical enterprise scale.

---

## 🗺️ Short-Term Engineering Roadmap

```
             Sprint 24: Core Remediation                      Sprint 25: Security & Optimization
       +-------------------------------------+               +--------------------------------------+
       | - Fix Confidence Double-Scaling     |               | - Migrate JWT to HttpOnly Cookies    |
       | - Fix ATRr_14 indicator typo        | ------->      | - Implement Alembic DB Migrations    |
       | - Implement API Rate Limiting       |               | - Optimize Portfolio Memory usage    |
       +-------------------------------------+               +--------------------------------------+
```

---

## 📅 Detailed Release Milestones

### 1. Sprint 24: Core Stability & Metric Remediation (P0 Priorities)
The focus of Sprint 24 is resolving the critical mathematical issues identified during Founder Alpha testing to ensure accurate calculations before entering Closed Beta.
- **Remediate Confidence Double-Scaling (BP2)**: Refactor the scoring engine math inside `core/confidence_engine.py` to ensure scores are scaled correctly, allowing the system to trigger intermediate `APPROVE` and `REJECT` states as intended.
- **Fix Volatility Indicator Typo (BP3)**: Standardize indicator lookups to reference `ATR_14` consistently, restoring accurate volatility metrics across the data collection pipeline.
- **Implement API Rate Limiting**: Configure the slowapi-based limiter globally in `api/main.py` to protect endpoints from rapid, automated requests.
- **Verify with Complete Test Run**: Ensure all 1,325+ tests pass cleanly after applying these fixes.

### 2. Sprint 25: Security Hardening & Migration Foundations (P1 Priorities)
The focus of Sprint 25 is hardening the platform's security and setting up database migrations to support future updates.
- **Implement Alembic Database Migrations**: Integrate the Alembic framework with `database.py` to automate and track database schema changes over time.
- **Migrate Session Tokens to HttpOnly Cookies**: Update the authentication routes and middleware to store JWT session tokens in secure, HttpOnly, SameSite cookies, protecting them from XSS extraction.
- **Optimize Portfolio Engine Memory**: Refactor the portfolio analytics engine to compute performance metrics using paginated queries and incremental caching, preventing memory leaks as the database grows.

### 3. Sprint 26: Closed Beta Onboarding & Telemetry Logging (P2 Priorities)
Prepare the platform to support a limited group of 10-50 external beta testers.
- **Deploy Advanced Closed Beta Telemetry**: Set up detailed audit logging to track user interactions and system performance during beta tests.
- **Incorporate User Feedback Loops**: Build an inline feedback form into the Command Center HUD, allowing testers to submit qualitative feedback directly to the database.
- **Automate Backup Pipelines**: Configure automated, daily database backups to secure trading logs.

---

## 🔄 Future Extension Points
- **Automated Roadmap Audits**: Future versions of the roadmap will link completed features directly to closed milestones in the Release History, providing a clear view of development progress.

---

## 🔗 Related Chapters
- [Chapter 25: Developer Onboarding Guide](25_DEVELOPER_GUIDE.md) - Setting up the development environment.
- [Chapter 27: Release History](27_RELEASE_HISTORY.md) - History of completed milestones.
- [Chapter 28: Technical Debt](28_TECHNICAL_DEBT.md) - Detailed analysis of current issues.
