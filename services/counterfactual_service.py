from __future__ import annotations

import logging
from typing import Any, Callable, Optional, List

from database import CounterfactualAnalysis, Trade, Signal, get_session
from services.dna_service import DecisionDNAService

logger = logging.getLogger(__name__)


class CounterfactualService:
    def __init__(self, session_factory: Optional[Callable[[], Any]] = None):
        self.session_factory = session_factory or get_session
        self.is_test = session_factory is not None
        self.dna_service = DecisionDNAService(session_factory=self.session_factory)

    def _to_dict(self, analysis: CounterfactualAnalysis) -> dict[str, Any]:
        return {
            "id": analysis.id,
            "trade_id": analysis.trade_id,
            "actual_pnl": analysis.actual_pnl,
            "no_trade_delta": analysis.no_trade_delta,
            "half_size_pnl": analysis.half_size_pnl,
            "tight_stop_pnl": analysis.tight_stop_pnl,
            "split_tp_pnl": analysis.split_tp_pnl,
            "delayed_entry_pnl": analysis.delayed_entry_pnl,
            "optimal_scenario": analysis.optimal_scenario,
            "optimal_potential_pnl": analysis.optimal_potential_pnl
        }

    def analyze_counterfactuals(self, trade_id: int, user_id: int = 1) -> dict[str, Any]:
        session = self.session_factory()
        try:
            # Retrieve completed trade
            trade = session.query(Trade).filter(Trade.id == trade_id).first()
            if not trade:
                raise ValueError(f"Trade {trade_id} not found")

            # Check if analysis already exists
            existing = session.query(CounterfactualAnalysis).filter(CounterfactualAnalysis.trade_id == trade_id).first()
            if existing:
                return self._to_dict(existing)

            actual_pnl = trade.pnl or 0.0

            # Calculate alternative outcomes
            no_trade_delta = -actual_pnl # if we didn't trade, we wouldn't have made/lost the actual PnL
            half_size_pnl = actual_pnl * 0.5

            # Simulating alternate scenarios relative to actual outcome
            if actual_pnl < 0:
                # Tighter stop loss would have capped losses!
                tight_stop_pnl = actual_pnl * 0.4
                split_tp_pnl = actual_pnl
                delayed_entry_pnl = actual_pnl * 0.2 # better entry price
                optimal_scenario = "TIGHT_STOP_LOSS"
                optimal_potential_pnl = tight_stop_pnl
            else:
                # Winning trade: Tighter stop loss might have been stopped out early
                tight_stop_pnl = -actual_pnl * 0.2
                # Split TP captures profits earlier
                split_tp_pnl = actual_pnl * 0.75
                delayed_entry_pnl = actual_pnl * 1.2 # entered higher but still won
                optimal_scenario = "DELAYED_ENTRY"
                optimal_potential_pnl = delayed_entry_pnl

            analysis = CounterfactualAnalysis(
                trade_id=trade_id,
                actual_pnl=actual_pnl,
                no_trade_delta=round(no_trade_delta, 2),
                half_size_pnl=round(half_size_pnl, 2),
                tight_stop_pnl=round(tight_stop_pnl, 2),
                split_tp_pnl=round(split_tp_pnl, 2),
                delayed_entry_pnl=round(delayed_entry_pnl, 2),
                optimal_scenario=optimal_scenario,
                optimal_potential_pnl=round(optimal_potential_pnl, 2)
            )

            session.add(analysis)
            if not self.is_test:
                session.commit()
                session.refresh(analysis)
            else:
                session.flush()

            # Telemetry
            logger.info(
                "TELEMETRY: [Counterfactual] Analyzed counterfactuals for trade %s. Actual: $%s. Optimal: %s ($%s)",
                trade_id, actual_pnl, optimal_scenario, optimal_potential_pnl
            )

            return self._to_dict(analysis)
        except Exception as e:
            if not self.is_test:
                session.rollback()
            logger.error("Failed to run counterfactual analysis on trade %s: %s", trade_id, e)
            raise
        finally:
            if not self.is_test:
                session.close()
