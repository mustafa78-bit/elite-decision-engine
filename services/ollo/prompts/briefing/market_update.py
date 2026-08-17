def market_update_briefing(context: dict) -> str:
    regime = context.get("market_regime", {})
    scanner = context.get("scanner_signals", {})
    whale = context.get("whale_activity", {})
    news = context.get("news_headlines", {})

    parts = ["Prepare a Market Update."]
    parts.append(f"Current regime: {regime.get('regime', 'UNKNOWN')}. Trend: {regime.get('trend', 'NEUTRAL')} ({regime.get('trend_strength', 'UNKNOWN')}). Volatility: {regime.get('volatility_class', 'UNKNOWN')}.")
    if scanner:
        parts.append(f"Active signals: {scanner.get('signal_count', 0)}.")
    if whale:
        parts.append("Whale intelligence is available.")
    headlines = news.get("headlines") if news else None
    if headlines:
        # Only headlines that genuinely moved the needle -- routine news
        # (score well below 50, same calibration services/news_job_service.py
        # gates Telegram alerts on) would just be noise in a briefing.
        notable = [h for h in headlines if h.get("score", 0) >= 40]
        if notable:
            titles = "; ".join(f"{h['headline']} ({h['sentiment']}, impact {h['score']}/100)" for h in notable[:3])
            parts.append(f"Notable news since last update: {titles}.")
    parts.append("Provide a concise intraday market update focusing on regime changes, notable scanner activity, key levels, and any notable news impact.")
    return " ".join(parts)
