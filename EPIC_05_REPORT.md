# Epic 5: Decision Intelligence — Report

## Objective
Create Probability Engine, Decision Aggregator, Confidence Engine v2, Signal Explanation, Decision Timeline, Reason Builder, Risk Explanation, and human-readable AI reasoning — all consuming Asset.

## Changes

### New files (7 files, +417 lines)

| File | Purpose |
|------|---------|
| `decision/__init__.py` | Package init |
| `decision/models.py` | `DecisionResult`, `DecisionEvent` dataclasses |
| `decision/timeline.py` | `DecisionTimeline` — record/retrieve events per symbol |
| `decision/confidence_v2.py` | `ConfidenceEngineV2` — enhanced using full Asset intelligence |
| `decision/explanation.py` | `ReasonBuilder`, `SignalExplanation`, `RiskExplanation` |
| `decision/aggregator.py` | `DecisionAggregator` — orchestrates scanner + MIP + confidence into decisions |
| `tests/test_decision.py` | 23 tests covering all modules |

## Architecture

```
DecisionAggregator.analyze(symbol)
  ├── MarketDataService.get_asset()    → Asset (fully enriched)
  ├── OpportunityScanner.scan()        → Opportunity
  ├── ConfidenceEngineV2.evaluate()    → confidence (0-100)
  ├── ReasonBuilder.build()            → reasons + warnings
  ├── DecisionTimeline.record()        → decision events
  └── DecisionResult (output)
        ├── decision: STRONG_APPROVE / APPROVE / WATCH / REJECT
        ├── reasons (human-readable list)
        ├── warnings (human-readable list)
        ├── timeline (DecisionEvent list)
        ├── intelligence_summary
        └── feature_summary
```

### Decision thresholds

| Confidence | Decision |
|------------|----------|
| >= 80      | STRONG_APPROVE |
| >= 65      | APPROVE |
| >= 50      | WATCH |
| < 50       | REJECT |

### ConfidenceEngineV2 inputs
- Opportunity score, probability, risk, confidence
- Asset intelligence (Fear & Greed, BTC trend, market session)
- Feature-based adjustments (RSI, trend alignment, momentum, risk class)

## Test Results

**111/111 tests pass** (23 decision + 20 scanner + 39 PRO + 29 intelligence)

## Commit

`pending`
