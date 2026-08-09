import asyncio
import logging

from config import CHECK_INTERVAL
from database import Signal, get_session, update_signal_status
from execution.execution_loop import ExecutionLoop

logger = logging.getLogger(__name__)


class DecisionEngine:

    def __init__(self, execution_loop=None):
        logger.info("Decision Engine initialized")
        self.execution_loop = execution_loop or ExecutionLoop()

    def get_open_signals(self):
        session = get_session()
        try:
            return session.query(Signal).filter(Signal.status == "OPEN").all()
        finally:
            session.close()

    def process_signal(self, signal):

        try:
            logger.info("Processing signal %s %s %s", signal.symbol, signal.side, signal.timeframe)
            update_signal_status(signal.id, "PROCESSING")

            self.execution_loop.run_once([signal])
        except Exception as e:
            logger.exception("Signal processing failed: %s", e)
            update_signal_status(signal.id, "REJECTED")

    def _process_open_signals(self):
        """Synchronous, blocking pass: fetch OPEN signals and process each.

        Every signal is processed individually (a rejection on one signal
        must not block the rest), but existing open trades still need their
        TP/SL/staleness monitored on every tick -- run_once() always does
        that as its last step, so it must run even when there are zero open
        signals, not only as a side effect of processing a new one.
        """
        signals = self.get_open_signals()

        if len(signals) == 0:
            logger.info("No open signals found.")
        else:
            logger.info("Found %s open signal(s).", len(signals))

            for signal in signals:
                self.process_signal(signal)

        if len(signals) == 0:
            self.execution_loop.run_once([])

    async def run(self):

        while True:
            try:
                await asyncio.to_thread(self._process_open_signals)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("DecisionEngine run loop iteration failed")

            await asyncio.sleep(CHECK_INTERVAL)
