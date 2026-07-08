from fastapi import APIRouter, Query

from database import Signal, Trade, get_session

router = APIRouter()


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
        trades = (
            session.query(Trade)
            .order_by(Trade.created_at.desc())
            .limit(limit)
            .all()
        )
    finally:
        session.close()

    total_signals = len(signals)
    approved = sum(1 for s in signals if s.approved)
    rejected = total_signals - approved

    total_trades = len(trades)
    closed_trades = [t for t in trades if t.status == "CLOSED"]
    open_trades = [t for t in trades if t.status == "OPEN"] if trades else []

    wins = sum(1 for t in closed_trades if t.pnl and t.pnl > 0)
    losses = sum(1 for t in closed_trades if t.pnl and t.pnl < 0)
    total_pnl = sum(t.pnl or 0 for t in trades)

    roi = 0
    trade_capital = 10000
    if total_trades > 0:
        gross_risk = trade_capital * total_trades * 0.02
        roi = (total_pnl / gross_risk) * 100 if gross_risk > 0 else 0

    win_rate = (wins / len(closed_trades)) * 100 if closed_trades else 0
    avg_win = (
        sum(t.pnl for t in closed_trades if t.pnl and t.pnl > 0) / wins
        if wins > 0
        else 0
    )
    avg_loss = (
        sum(abs(t.pnl) for t in closed_trades if t.pnl and t.pnl < 0) / losses
        if losses > 0
        else 0
    )

    profit_factor = avg_win / avg_loss if avg_loss > 0 else 0

    pnls = [t.pnl for t in closed_trades if t.pnl is not None]
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
