from datetime import datetime, timezone
from typing import Optional


class TimestampHandler:

    @staticmethod
    def utc_now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def normalize(dt: Optional[datetime]) -> Optional[datetime]:
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    @staticmethod
    def age_seconds(dt: datetime) -> float:
        now = TimestampHandler.utc_now()
        normalized = TimestampHandler.normalize(dt)
        if normalized is None:
            return float("inf")
        return (now - normalized).total_seconds()

    @staticmethod
    def format_timestamp(dt: datetime) -> str:
        normalized = TimestampHandler.normalize(dt)
        return normalized.strftime("%Y-%m-%dT%H:%M:%SZ")


class FreshnessValidator:

    FRESH_THRESHOLD_SECONDS = 3600
    STALE_THRESHOLD_SECONDS = 86400

    @classmethod
    def is_fresh(cls, dt: datetime, max_age_seconds: Optional[int] = None) -> bool:
        threshold = max_age_seconds or cls.FRESH_THRESHOLD_SECONDS
        return TimestampHandler.age_seconds(dt) <= threshold

    @classmethod
    def is_stale(cls, dt: datetime, max_age_seconds: Optional[int] = None) -> bool:
        threshold = max_age_seconds or cls.STALE_THRESHOLD_SECONDS
        return TimestampHandler.age_seconds(dt) > threshold

    @classmethod
    def freshness_score(cls, dt: datetime) -> float:
        age = TimestampHandler.age_seconds(dt)
        if age <= cls.FRESH_THRESHOLD_SECONDS:
            return 1.0
        if age >= cls.STALE_THRESHOLD_SECONDS:
            return 0.0
        return 1.0 - (age - cls.FRESH_THRESHOLD_SECONDS) / (cls.STALE_THRESHOLD_SECONDS - cls.FRESH_THRESHOLD_SECONDS)
