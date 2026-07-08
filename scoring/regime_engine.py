class RegimeEngine:
    """Market regime detector.

    Delegates actual detection to ``RegimeAI`` for a single source of truth
    while preserving the simpler ``{"regime", "score"}`` interface.
    """

    def detect(self, values):
        from scoring.regime_ai import RegimeAI
        result = RegimeAI().detect(values)
        return {
            "regime": result.get("regime", "UNKNOWN"),
            "score": result.get("score", 0.0),
        }
