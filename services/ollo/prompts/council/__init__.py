def council_summary(context: dict) -> str:
    council = context.get("council_full") or context.get("council_latest", {})
    regime = context.get("market_regime", {})

    parts = ["Summarize the AI Council status."]
    if council:
        agents = council.get("agents", [])
        parts.append(f"Active agents: {len(agents)} — {', '.join(agents)}.")
    parts.append(f"Market regime: {regime.get('regime', 'UNKNOWN')}.")
    parts.append("Provide a concise summary of the AI Council's current composition, agent activities, and any notable consensus or divergence.")
    return " ".join(parts)
