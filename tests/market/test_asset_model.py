"""Tests for the unified Asset model."""

from market.models import Asset, AssetMetadata, OHLCVData
import pandas as pd


class TestAssetModel:

    def test_create_default(self):
        asset = Asset.create("BTC")
        assert asset.symbol == "BTC"
        assert asset.metadata.symbol == "BTC"
        assert asset.price == 0.0
        assert asset.is_empty

    def test_create_with_price(self):
        asset = Asset.create("ETH", price=2500.0)
        assert asset.symbol == "ETH"
        assert asset.price == 2500.0
        assert not asset.is_empty

    def test_asset_not_empty_with_ohlcv(self):
        df = pd.DataFrame({"close": [100.0]})
        asset = Asset(symbol="BTC", metadata=AssetMetadata(symbol="BTC"), ohlcv=df)
        assert not asset.is_empty

    def test_asset_metadata_defaults(self):
        meta = AssetMetadata(symbol="SOL")
        assert meta.quote_asset == "USDT"
        assert meta.exchange == "hyperliquid"
        assert meta.decimals == 8


class TestOHLCVData:

    def test_from_empty_dataframe(self):
        df = pd.DataFrame()
        data = OHLCVData.from_dataframe(df, symbol="BTC", timeframe="1h")
        assert data.empty
        assert data.latest_price == 0.0

    def test_from_dataframe(self):
        df = pd.DataFrame({"close": [100.0, 101.0, 102.0]})
        data = OHLCVData.from_dataframe(df, symbol="BTC", timeframe="1h")
        assert not data.empty
        assert data.latest_price == 102.0
        assert len(data) == 3
