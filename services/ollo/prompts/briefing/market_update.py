def market_update_briefing(context: dict) -> str:
    regime = context.get("market_regime", {})
    scanner = context.get("scanner_signals", {})
    whale = context.get("whale_activity", {})

    parts = ["Prepare a Market Update."]
    parts.append(f"Current regime: {regime.get('regime', 'UNKNOWN')}. Trend: {regime.get('trend', 'NEUTRAL')} ({regime.get('trend_strength', 'UNKNOWN')}). Volatility: {regime.get('volatility_class', 'UNKNOWN')}.")
    if scanner:
        parts.append(f"Active signals: {scanner.get('signal_count', 0)}.")
    if whale:
        parts.append("Whale intelligence is available.")
    parts.append("Provide a concise intraday market update focusing on regime changes, notable scanner activity, and key levels.")
    return " ".join(parts)
