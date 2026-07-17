from datetime import datetime, timezone

from whale.models import TransferEvent
from whale.smart_money import (
    SmartMoneyDetector,
    WalletReputation,
    SmartMoneyWallet,
)


class TestSmartMoneyWallet:

    def test_defaults(self):
        w = SmartMoneyWallet(address="0xabc")
        assert w.reputation_score == 50.0
        assert w.total_volume_usd == 0.0
        assert w.total_transfers == 0
        assert w.behavior_type == "UNKNOWN"
        assert w.tags == []

    def test_custom_values(self):
        now = datetime.now(timezone.utc)
        w = SmartMoneyWallet(
            address="0xcustom",
            reputation_score=90.0,
            total_volume_usd=5000000.0,
            total_transfers=20,
            first_seen=now,
            last_seen=now,
            behavior_type="WHALE",
            tags=["large", "frequent"],
        )
        assert w.reputation_score == 90.0
        assert w.total_transfers == 20
        assert "large" in w.tags


class TestWalletReputation:

    def test_get_or_create_new(self):
        rep = WalletReputation()
        wallet = rep.get_or_create_wallet("0xabc")
        assert wallet.address == "0xabc"
        assert wallet.reputation_score == 50.0

    def test_get_or_create_existing(self):
        rep = WalletReputation()
        w1 = rep.get_or_create_wallet("0xabc")
        w2 = rep.get_or_create_wallet("0xabc")
        assert w1 is w2

    def test_update_from_transfer(self):
        rep = WalletReputation()
        transfer = TransferEvent(
            tx_id="tx1",
            from_address="0xfrom",
            to_address="0xto",
            asset="BTC",
            amount=1.0,
            value_usd=100000.0,
            timestamp=datetime.now(timezone.utc),
        )
        transfer.is_large = True
        rep.update_from_transfer(transfer)
        wallet = rep.wallets["0xfrom"]
        assert wallet.total_volume_usd == 100000.0
        assert wallet.total_transfers == 1
        assert wallet.reputation_score > 50.0

    def test_update_multiple_transfers(self):
        rep = WalletReputation()
        for i in range(3):
            transfer = TransferEvent(
                tx_id=f"tx{i}",
                from_address="0xfrom",
                to_address="0xto",
                asset="BTC",
                amount=1.0,
                value_usd=100000.0,
                timestamp=datetime.now(timezone.utc),
            )
            if i > 0:
                transfer.is_large = True
            rep.update_from_transfer(transfer)
        wallet = rep.wallets["0xfrom"]
        assert wallet.total_transfers == 3
        assert wallet.total_volume_usd == 300000.0

    def test_calculate_score_no_wallet(self):
        rep = WalletReputation()
        score = rep.calculate_score("0xnonexistent")
        assert score == 50.0

    def test_calculate_score_existing(self):
        rep = WalletReputation()
        rep.get_or_create_wallet("0xabc").reputation_score = 75.0
        score = rep.calculate_score("0xabc")
        assert score == 75.0


class TestSmartMoneyDetector:

    def make_transfer(
        self, from_addr="0xa", to_addr="0xb", value=100000.0
    ):
        return TransferEvent(
            tx_id=f"tx_{from_addr[:4]}_{to_addr[:4]}",
            from_address=from_addr,
            to_address=to_addr,
            asset="BTC",
            amount=value / 50000,
            value_usd=value,
            timestamp=datetime.now(timezone.utc),
        )

    def test_process_small_transfer(self):
        detector = SmartMoneyDetector()
        transfer = self.make_transfer(value=100.0)
        event = detector.process_transfer(transfer)
        assert event is None

    def test_process_transfer_tracks_both_addresses(self):
        detector = SmartMoneyDetector()
        transfer = self.make_transfer("0xalice", "0xbob", 500000.0)
        detector.process_transfer(transfer)
        assert "0xalice" in detector.wallet_activities
        assert "0xbob" in detector.wallet_activities
        assert detector.wallet_activities["0xalice"].transfer_count == 1
        assert detector.wallet_activities["0xbob"].transfer_count == 1

    def test_detect_accumulation(self):
        detector = SmartMoneyDetector()
        addr = "0xaccumulator"
        for i in range(4):
            t = self.make_transfer(f"0xother{i}", addr, 200000.0)
            detector.process_transfer(t)
        event = detector.detect_accumulation(addr)
        assert event is not None
        assert event.event_type == "ACCUMULATION"
        assert event.value_usd >= 500000

    def test_detect_accumulation_insufficient(self):
        detector = SmartMoneyDetector()
        event = detector.detect_accumulation("0xunknown")
        assert event is None

    def test_detect_distribution(self):
        detector = SmartMoneyDetector()
        addr = "0xdistributor"
        for i in range(4):
            t = self.make_transfer(addr, f"0xother{i}", 200000.0)
            detector.process_transfer(t)
        event = detector.detect_distribution(addr)
        assert event is not None
        assert event.event_type == "DISTRIBUTION"

    def test_detect_distribution_insufficient(self):
        detector = SmartMoneyDetector()
        event = detector.detect_distribution("0xunknown")
        assert event is None

    def test_track_repeated_activity(self):
        detector = SmartMoneyDetector()
        transfer = self.make_transfer("0xalice", "0xbob", 100000.0)
        last_event = None
        for _ in range(4):
            last_event = detector.track_repeated_activity(transfer)
        assert last_event is not None
        assert last_event.event_type == "REPEATED_ACTIVITY"

    def test_track_repeated_below_threshold(self):
        detector = SmartMoneyDetector()
        transfer = self.make_transfer("0xa", "0xb", 100000.0)
        event = detector.track_repeated_activity(transfer)
        assert event is None

    def test_classify_behavior_unknown(self):
        detector = SmartMoneyDetector()
        assert detector.classify_behavior("0xnonexistent") == "UNKNOWN"

    def test_classify_behavior_whale(self):
        detector = SmartMoneyDetector()
        addr = "0xwhale"
        for i in range(12):
            t = self.make_transfer(f"0xother{i}", addr, 200000.0)
            detector.process_transfer(t)
        assert detector.classify_behavior(addr) == "WHALE"

    def test_classify_behavior_smart_money(self):
        detector = SmartMoneyDetector()
        addr = "0xsmart"
        for i in range(6):
            t = self.make_transfer(f"0xother{i}", addr, 100000.0)
            detector.process_transfer(t)
        assert detector.classify_behavior(addr) == "SMART_MONEY"

    def test_classify_behavior_active(self):
        detector = SmartMoneyDetector()
        addr = "0xactive"
        for i in range(3):
            t = self.make_transfer(f"0xother{i}", addr, 10000.0)
            detector.process_transfer(t)
        assert detector.classify_behavior(addr) == "ACTIVE"

    def test_get_whale_signals(self):
        detector = SmartMoneyDetector()
        addr = "0xbigwhale"
        for i in range(12):
            t = self.make_transfer(f"0xother{i}", addr, 200000.0)
            detector.process_transfer(t)
        signals = detector.get_whale_signals()
        assert isinstance(signals, list)
        signal_types = [s.event_type for s in signals]
        assert "WHALE_DETECTED" in signal_types

    def test_get_whale_signals_empty(self):
        detector = SmartMoneyDetector()
        assert detector.get_whale_signals() == []

    def test_process_transfer_accumulation_event(self):
        detector = SmartMoneyDetector()
        addr = "0xacc"
        events = []
        for i in range(4):
            t = self.make_transfer(f"0xsrc{i}", addr, 200000.0)
            e = detector.process_transfer(t)
            if e:
                events.append(e)
        types = [e.event_type for e in events]
        assert "ACCUMULATION" in types


class TestSmartMoneyDetectorIntegration:

    def test_full_detection_pipeline(self):
        detector = SmartMoneyDetector()
        for i in range(15):
            t = TransferEvent(
                tx_id=f"tx_full_{i}",
                from_address=f"0xsender{i}",
                to_address="0xwhale_main",
                asset="BTC",
                amount=10.0,
                value_usd=500000.0,
                timestamp=datetime.now(timezone.utc),
            )
            detector.process_transfer(t)
        assert detector.classify_behavior("0xwhale_main") == "WHALE"
        signals = detector.get_whale_signals()
        assert len(signals) >= 1
