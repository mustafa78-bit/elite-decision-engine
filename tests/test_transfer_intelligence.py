from datetime import datetime, timezone

from whale.models import TransferEvent
from whale.analyzer import TransferAnalyzer


class TestTransferAnalyzer:

    def make_transfer(
        self,
        tx_id="tx1",
        from_addr="0xa",
        to_addr="0xb",
        asset="BTC",
        amount=1.0,
        value_usd=50000.0,
    ):
        return TransferEvent(
            tx_id=tx_id,
            from_address=from_addr,
            to_address=to_addr,
            asset=asset,
            amount=amount,
            value_usd=value_usd,
            timestamp=datetime.now(timezone.utc),
        )

    def test_is_large_transfer(self):
        analyzer = TransferAnalyzer()
        assert analyzer.is_large_transfer(100000.0) is True
        assert analyzer.is_large_transfer(99999.99) is False
        assert analyzer.is_large_transfer(1000000.0) is True
        assert analyzer.is_large_transfer(0) is False

    def test_classify_direction_wallet_to_wallet(self):
        analyzer = TransferAnalyzer()
        direction = analyzer.classify_direction("0xalice", "0xbob")
        assert direction == "WALLET_TO_WALLET"

    def test_classify_direction_case_insensitive(self):
        analyzer = TransferAnalyzer()
        direction = analyzer.classify_direction("0xALICE", "0xBOB")
        assert direction == "WALLET_TO_WALLET"

    def test_calculate_confidence_base(self):
        analyzer = TransferAnalyzer()
        transfer = self.make_transfer()
        confidence = analyzer.calculate_confidence(transfer)
        assert 0.0 <= confidence <= 1.0
        assert confidence >= 0.4

    def test_calculate_confidence_large(self):
        analyzer = TransferAnalyzer()
        transfer = self.make_transfer(value_usd=500000.0)
        transfer.is_large = True
        confidence = analyzer.calculate_confidence(transfer)
        assert confidence >= 0.6

    def test_detect_suspicious_clean(self):
        analyzer = TransferAnalyzer()
        transfer = self.make_transfer()
        flags = analyzer.detect_suspicious(transfer)
        assert isinstance(flags, list)
        assert len(flags) == 0

    def test_detect_suspicious_large_wallet_to_wallet(self):
        analyzer = TransferAnalyzer()
        transfer = self.make_transfer(value_usd=1000000.0)
        transfer.direction = "WALLET_TO_WALLET"
        transfer.is_large = True
        flags = analyzer.detect_suspicious(transfer)
        assert "LARGE_WALLET_TO_WALLET" in flags

    def test_analyze_transfer_small(self):
        analyzer = TransferAnalyzer()
        transfer = self.make_transfer(value_usd=1000.0)
        event = analyzer.analyze_transfer(transfer)
        assert event.event_type == "TRANSFER"
        assert transfer.direction == "WALLET_TO_WALLET"
        assert transfer.is_large is False

    def test_analyze_transfer_large(self):
        analyzer = TransferAnalyzer()
        transfer = self.make_transfer(value_usd=5000000.0)
        event = analyzer.analyze_transfer(transfer)
        assert event.event_type == "LARGE_TRANSFER"
        assert transfer.is_large is True
        assert event.details["direction"] == "WALLET_TO_WALLET"

    def test_analyze_transfer_sets_confidence(self):
        analyzer = TransferAnalyzer()
        transfer = self.make_transfer(value_usd=5000000.0)
        analyzer.analyze_transfer(transfer)
        assert transfer.confidence >= 0.0
        assert transfer.confidence <= 1.0

    def test_estimate_usd_value(self):
        analyzer = TransferAnalyzer()
        value = analyzer.estimate_usd_value(10.0, 50000.0)
        assert value == 500000.0

    def test_estimate_usd_value_zero(self):
        analyzer = TransferAnalyzer()
        value = analyzer.estimate_usd_value(0, 50000.0)
        assert value == 0.0

    def test_get_recent_large_transfers(self):
        analyzer = TransferAnalyzer()
        analyzer.analyze_transfer(self.make_transfer(value_usd=200000.0))
        analyzer.analyze_transfer(self.make_transfer(value_usd=30000.0))
        large = analyzer.get_recent_large_transfers()
        assert len(large) == 1
        assert large[0].value_usd == 200000.0

    def test_get_recent_large_transfers_custom_threshold(self):
        analyzer = TransferAnalyzer()
        analyzer.analyze_transfer(self.make_transfer(value_usd=1000.0))
        small = analyzer.get_recent_large_transfers(min_value=500.0)
        assert len(small) == 1
        empty = analyzer.get_recent_large_transfers(min_value=999999.0)
        assert len(empty) == 0

    def test_transfer_summary_empty(self):
        analyzer = TransferAnalyzer()
        summary = analyzer.get_transfer_summary()
        assert summary["total"] == 0
        assert summary["large"] == 0

    def test_transfer_summary_with_data(self):
        analyzer = TransferAnalyzer()
        analyzer.analyze_transfer(self.make_transfer(value_usd=100000.0))
        summary = analyzer.get_transfer_summary()
        assert summary["total"] == 1
        assert summary["large"] == 1

    def test_multiple_transfers_history(self):
        analyzer = TransferAnalyzer()
        for i in range(5):
            analyzer.analyze_transfer(
                self.make_transfer(tx_id=f"tx{i}", value_usd=100000.0 + i)
            )
        assert len(analyzer.transfer_history) == 5
        summary = analyzer.get_transfer_summary()
        assert summary["total"] == 5

    def test_analyze_returns_event(self):
        analyzer = TransferAnalyzer()
        transfer = self.make_transfer()
        event = analyzer.analyze_transfer(transfer)
        assert event.wallet_address == "0xa"
        assert event.asset == "BTC"
        assert event.source == "whale_module"
