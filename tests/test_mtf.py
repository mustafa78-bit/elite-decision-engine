from unittest.mock import MagicMock

import pandas as pd
import pytest

from market_data.mtf import MTFEngine


class TestMTFEngine:
    def test_imports_and_instantiation(self):
        mtf = MTFEngine()
        assert mtf is not None
        assert hasattr(mtf, "score")

    @pytest.mark.skip(reason="Requires live market data")
    def test_score_btc_long(self):
        mtf = MTFEngine()
        result = mtf.score("BTCUSDT", "LONG")
        assert isinstance(result, (int, float))

    def test_score_passes_the_full_ticker_symbol_to_the_collector(self):
        # Regression: MTFEngine used to strip "USDT" before calling
        # self.collector.get_ohlcv() -- self.collector is MultiProvider,
        # which needs the FULL ticker to look up SYMBOL_PROVIDER_ASSIGNMENT
        # and route to the right exchange. A bare "TAO" is never a key in
        # that table, so every call silently fell through to the
        # "hyperliquid" default regardless of the symbol's real assignment.
        mock_collector = MagicMock()
        mock_collector.get_ohlcv.return_value = pd.DataFrame({
            "close": [1.0, 2.0, 3.0],
        })
        mtf = MTFEngine()
        mtf.collector = mock_collector
        mtf.indicators = MagicMock()
        mtf.indicators.calculate.return_value = {"ema20": 3, "ema50": 2, "ema200": 1}

        mtf.score("TAOUSDT", "LONG")

        for call in mock_collector.get_ohlcv.call_args_list:
            assert call.kwargs["symbol"] == "TAOUSDT"
