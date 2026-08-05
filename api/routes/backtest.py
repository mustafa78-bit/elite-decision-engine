from fastapi import APIRouter, Query

from database import FINAL_STATUSES, PaperTrade, Signal, Trade, get_session

router = APIRouter()


def _dollar_pnl(trade: Trade, paper_trade: PaperTrade | None) -> float | None:
    """Real dollar pnl (price delta x real quantity), falling back to the raw
    per-unit value when no matching PaperTrade exists."""

    if trade.pnl is None:
        return None
    if paper_trade is not None and paper_trade.quantity is not None:
        return paper_trade.quantity * trade.pnl
    return trade.pnl


@router.get("/backtest")
def run_backtest(limit: int = Query(200, ge=1, le=1000)):
    session = get_session()
    try:
        signals = (
            session.query(Signal)
            .order_by(Signal.created_at.desc())
            .limit(limit)
            .all()
        )
        trade_results = (
            session.query(Trade, PaperTrade)
            .outerjoin(PaperTrade, PaperTrade.position_id == Trade.id)
            .order_by(Trade.created_at.desc())
            .limit(limit)
            .all()
        )
    finally:
        session.close()

    total_signals = len(signals)
    approved = sum(1 for s in signals if s.approved)
    rejected = total_signals - approved

    trades = [t for t, _ in trade_results]
    total_trades = len(trades)
    closed_trades = [t for t in trades if t.status in FINAL_STATUSES]
    open_trades = [t for t in trades if t.status == "OPEN"] if trades else []

    closed_results_perf = [
        (t, pt) for t, pt in trade_results
        if t.status in FINAL_STATUSES and t.status != "CANCEL"
    ]
    closed_trades_perf = [t for t, _ in closed_results_perf]

    wins = sum(1 for t in closed_trades_perf if t.pnl and t.pnl > 0)
    losses = sum(1 for t in closed_trades_perf if t.pnl and t.pnl < 0)
    total_pnl = sum(_dollar_pnl(t, pt) or 0 for t, pt in trade_results)

    roi = 0
    trade_capital = 10000
    if total_trades > 0:
        gross_risk = trade_capital * total_trades * 0.02
        roi = (total_pnl / gross_risk) * 100 if gross_risk > 0 else 0

    win_rate = (wins / len(closed_trades_perf)) * 100 if closed_trades_perf else 0
    win_dollar_pnls = [_dollar_pnl(t, pt) for t, pt in closed_results_perf if t.pnl and t.pnl > 0]
    loss_dollar_pnls = [_dollar_pnl(t, pt) for t, pt in closed_results_perf if t.pnl and t.pnl < 0]
    avg_win = sum(win_dollar_pnls) / wins if wins > 0 else 0
    avg_loss = sum(abs(p) for p in loss_dollar_pnls) / losses if losses > 0 else 0

    profit_factor = avg_win / avg_loss if avg_loss > 0 else 0

    pnls = [_dollar_pnl(t, pt) for t, pt in closed_results_perf if t.pnl is not None]
    running_max = 0
    max_drawdown = 0
    cumulative = 0
    for p in pnls:
        cumulative += p
        if cumulative > running_max:
            running_max = cumulative
        drawdown = running_max - cumulative
        if drawdown > max_drawdown:
            max_drawdown = drawdown

    sharpe = 0
    if len(pnls) > 1:
        import statistics
        mean = statistics.mean(pnls)
        std = statistics.stdev(pnls)
        sharpe = (mean / std) if std > 0 else 0

    return {
        "summary": {
            "total_signals": total_signals,
            "approved_signals": approved,
            "rejected_signals": rejected,
            "approval_rate": round((approved / total_signals) * 100, 1) if total_signals else 0,
        },
        "trades": {
            "total": total_trades,
            "open": len(open_trades),
            "closed": len(closed_trades),
            "wins": wins,
            "losses": losses,
        },
        "performance": {
            "total_pnl": round(total_pnl, 2),
            "roi_pct": round(roi, 2),
            "win_rate_pct": round(win_rate, 1),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "profit_factor": round(profit_factor, 2),
            "max_drawdown": round(max_drawdown, 2),
            "sharpe_ratio": round(sharpe, 4),
        },
    }
