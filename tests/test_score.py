from scoring.scoring_engine import ScoringEngine


class DummySignal:
    symbol = "BTCUSDT"
    side = "LONG"
    timeframe = "1h"


engine = ScoringEngine()

result = engine.score(DummySignal())

print(result)
