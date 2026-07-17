from datetime import datetime, timezone

from whale.models import WhaleEvent, WalletActivity, TransferEvent
from whale.timestamp import TimestampHandler, FreshnessValidator
from whale.interfaces import WhaleFeatureExtractor, WhaleDataSource
from whale.logging import WhaleLogger


class TestWhaleModels:

    def test_whale_event_creation(self):
        event = WhaleEvent(
            event_id="test_001",
            wallet_address="0xabc123",
            event_type="LARGE_TRANSFER",
            asset="BTC",
            value_usd=500000.0,
            confidence=0.85,
            detected_at=datetime.now(timezone.utc),
        )
        assert event.event_id == "test_001"
        assert event.value_usd == 500000.0
        assert event.confidence == 0.85
        assert event.source == "whale_module"

    def test_whale_event_default_details(self):
        event = WhaleEvent(
            event_id="test_002",
            wallet_address="0xdef",
            event_type="ACCUMULATION",
            asset="ETH",
            value_usd=1000000.0,
            confidence=0.9,
            detected_at=datetime.now(timezone.utc),
        )
        assert event.details is None

    def test_whale_event_with_details(self):
        details = {"direction": "INFLOW", "tx_count": 5}
        event = WhaleEvent(
            event_id="test_003",
            wallet_address="0xabc",
            event_type="DISTRIBUTION",
            asset="SOL",
            value_usd=750000.0,
            confidence=0.75,
            detected_at=datetime.now(timezone.utc),
            details=details,
        )
        assert event.details["direction"] == "INFLOW"

    def test_wallet_activity_defaults(self):
        activity = WalletActivity(wallet_address="0xdef456")
        assert activity.reputation_score == 50.0
        assert activity.behavior_type == "UNKNOWN"
        assert activity.transfer_count == 0
        assert activity.total_volume_usd == 0.0

    def test_wallet_activity_custom_values(self):
        now = datetime.now(timezone.utc)
        activity = WalletActivity(
            wallet_address="0xcustom",
            total_volume_usd=1000000.0,
            transfer_count=10,
            first_seen=now,
            last_seen=now,
            reputation_score=85.0,
            behavior_type="WHALE",
        )
        assert activity.total_volume_usd == 1000000.0
        assert activity.transfer_count == 10
        assert activity.reputation_score == 85.0
        assert activity.behavior_type == "WHALE"

    def test_transfer_event_defaults(self):
        transfer = TransferEvent(
            tx_id="tx001",
            from_address="0xfrom",
            to_address="0xto",
            asset="ETH",
            amount=100.0,
            value_usd=250000.0,
            timestamp=datetime.now(timezone.utc),
        )
        assert transfer.direction == "UNKNOWN"
        assert transfer.confidence == 0.5
        assert transfer.is_large is False
        assert transfer.is_suspicious is False

    def test_transfer_event_custom_values(self):
        transfer = TransferEvent(
            tx_id="tx002",
            from_address="0xa",
            to_address="0xb",
            asset="BTC",
            amount=50.0,
            value_usd=2500000.0,
            timestamp=datetime.now(timezone.utc),
            direction="EXCHANGE_INFLOW",
            confidence=0.9,
            is_large=True,
            is_suspicious=True,
        )
        assert transfer.direction == "EXCHANGE_INFLOW"
        assert transfer.is_large is True


class TestTimestampHandler:

    def test_utc_now(self):
        now = TimestampHandler.utc_now()
        assert now.tzinfo is not None
        offset = now.tzinfo.utcoffset(now)
        assert offset is not None
        assert offset.total_seconds() == 0

    def test_normalize_naive(self):
        naive = datetime(2024, 1, 1, 12, 0, 0)
        normalized = TimestampHandler.normalize(naive)
        assert normalized.tzinfo is not None
        assert normalized.hour == 12

    def test_normalize_aware(self):
        aware = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        normalized = TimestampHandler.normalize(aware)
        assert normalized == aware

    def test_normalize_none(self):
        assert TimestampHandler.normalize(None) is None

    def test_age_seconds_recent(self):
        recent = datetime.now(timezone.utc)
        age = TimestampHandler.age_seconds(recent)
        assert 0 <= age < 2

    def test_age_seconds_future(self):
        future = datetime(2030, 1, 1, tzinfo=timezone.utc)
        age = TimestampHandler.age_seconds(future)
        assert age < 0

    def test_format_timestamp(self):
        dt = datetime(2024, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
        formatted = TimestampHandler.format_timestamp(dt)
        assert formatted == "2024-06-15T10:30:00Z"

    def test_format_timestamp_naive(self):
        dt = datetime(2024, 6, 15, 10, 30, 0)
        formatted = TimestampHandler.format_timestamp(dt)
        assert formatted.endswith("Z")


class TestFreshnessValidator:

    def test_is_fresh(self):
        recent = datetime.now(timezone.utc)
        assert FreshnessValidator.is_fresh(recent) is True

    def test_is_fresh_custom_threshold(self):
        old = datetime(2020, 1, 1, tzinfo=timezone.utc)
        assert FreshnessValidator.is_fresh(old, max_age_seconds=999999999) is True

    def test_is_stale(self):
        old = datetime(2020, 1, 1, tzinfo=timezone.utc)
        assert FreshnessValidator.is_stale(old) is True

    def test_is_stale_custom_threshold(self):
        recent = datetime.now(timezone.utc)
        assert FreshnessValidator.is_stale(recent, max_age_seconds=1) is False

    def test_freshness_score_fresh(self):
        recent = datetime.now(timezone.utc)
        assert FreshnessValidator.freshness_score(recent) == 1.0

    def test_freshness_score_stale(self):
        old = datetime(2020, 1, 1, tzinfo=timezone.utc)
        assert FreshnessValidator.freshness_score(old) == 0.0

    def test_freshness_score_partial(self):
        oldish = datetime.now(timezone.utc)
        age = TimestampHandler.age_seconds(oldish)
        if age > FreshnessValidator.FRESH_THRESHOLD_SECONDS:
            score = FreshnessValidator.freshness_score(oldish)
            assert 0.0 <= score < 1.0


class TestWhaleInterfaces:

    def test_feature_extractor_default(self):
        extractor = WhaleFeatureExtractor()
        result = extractor.extract(transfer_history=[], whale_signals=[])
        assert result["ok"] is True
        assert result["features"] == {
            "recent_large_transfer_count": 0,
            "total_large_transfer_volume": 0,
            "whale_wallet_count": 0,
            "total_transfers_analyzed": 0,
        }

    def test_feature_extractor_evaluate(self):
        extractor = WhaleFeatureExtractor()
        result = extractor.evaluate()
        assert result["ok"] is True

    def test_feature_extractor_get_feature_names(self):
        extractor = WhaleFeatureExtractor()
        assert extractor.get_feature_names() == [
            "recent_large_transfer_count",
            "total_large_transfer_volume",
            "whale_wallet_count",
            "total_transfers_analyzed",
        ]

    def test_data_source_defaults(self):
        source = WhaleDataSource()
        assert source.connected is False
        assert source.is_available() is False

    def test_data_source_connect(self):
        source = WhaleDataSource()
        assert source.connect() is True
        assert source.is_available() is True

    def test_data_source_fetch_recent(self):
        source = WhaleDataSource()
        source.connect()
        assert source.fetch_recent_transfers() == []
        assert source.fetch_recent_transfers(limit=50) == []


class TestWhaleLogger:

    def test_logger_creation(self):
        logger = WhaleLogger("test_logger")
        assert logger.logger.name == "test_logger"

    def test_logger_levels(self):
        logger = WhaleLogger("test_levels")
        logger.info("info test")
        logger.warning("warning test")
        logger.error("error test")
        logger.debug("debug test")
        assert True

    def test_whale_event_log(self):
        logger = WhaleLogger("test_events")
        logger.whale_event("TEST_EVENT", {"key": "value"})
        assert True

    def test_logger_reuses_handler(self):
        logger = WhaleLogger("test_reuse")
        original_handlers = list(logger.logger.handlers)
        logger._setup_handler()
        assert len(logger.logger.handlers) == len(original_handlers)
