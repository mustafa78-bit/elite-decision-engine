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
