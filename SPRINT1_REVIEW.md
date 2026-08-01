# Test Output

```
INFO:execution.pipeline:Pipeline decision for BTCUSDT LONG 1h: REJECT
REJECTED
```

# Git Diff

```diff
diff --git a/core/confidence_engine.py b/core/confidence_engine.py
index c696b5e..3645064 100644
--- a/core/confidence_engine.py
+++ b/core/confidence_engine.py
@@ -16,7 +16,7 @@ class ConfidenceEngine:
             score["risk_score"] * 10
         )
 
-        confidence = max(0, min(100, confidence * 100))
+        confidence = max(0, min(100, confidence))
 
         if confidence >= 90:
             decision = "STRONG_APPROVE"
diff --git a/core/engine.py b/core/engine.py
index da42288..b9b307b 100644
--- a/core/engine.py
+++ b/core/engine.py
@@ -82,6 +82,7 @@ class DecisionEngine:
         decision: str,
     ) -> TradeCandidate:
         return TradeCandidate(
+            id=signal.id,
             symbol=signal.symbol,
             side=signal.side,
             timeframe=signal.timeframe,
diff --git a/execution/execution_loop.py b/execution/execution_loop.py
index d29072f..0da0faf 100644
--- a/execution/execution_loop.py
+++ b/execution/execution_loop.py
@@ -11,6 +11,7 @@ import logging
 from dataclasses import dataclass
 from typing import Any, Iterable, Optional
 
+from database import update_signal_status
 from execution.paper_executor import PaperExecutor, TradeMonitorResult
 from execution.pipeline import DecisionPipeline, TradeCandidate, TradingSignal
 from execution.trade_engine import TradeEngine
@@ -71,6 +72,7 @@ class ExecutionLoop:
                 getattr(signal, "symbol", None),
                 getattr(signal, "side", None),
             )
+            update_signal_status(signal.id, "REJECTED")
             return None
 
         self.logger.info(
@@ -79,7 +81,10 @@ class ExecutionLoop:
             candidate.side,
             candidate.decision,
         )
-        return self._create_trade(candidate)
+        trade = self._create_trade(candidate)
+        if trade is not None:
+            update_signal_status(signal.id, "EXECUTED")
+        return trade
 
     def monitor(self) -> list[TradeMonitorResult]:
         """Monitor all open paper trades."""
diff --git a/execution/pipeline.py b/execution/pipeline.py
index 6843f1d..3142eee 100644
--- a/execution/pipeline.py
+++ b/execution/pipeline.py
@@ -62,6 +62,7 @@ class ConfidenceCalculator(Protocol):
 class TradeCandidate:
     """Approved trade candidate produced by the orchestration pipeline."""
 
+    id: int
     symbol: str
     side: str
     timeframe: str
@@ -124,6 +125,7 @@ class DecisionPipeline:
                 return None
 
             return TradeCandidate(
+                id=signal.id,
                 symbol=signal.symbol,
                 side=signal.side,
                 timeframe=signal.timeframe,
```
