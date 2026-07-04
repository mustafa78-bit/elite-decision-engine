import requests
import pandas as pd


class HyperliquidCollector:
    BASE_URL = "https://api.hyperliquid.xyz/info"

    def get_ohlcv(self, symbol="BTC", timeframe="1h", limit=500):

        payload = {
            "type": "candleSnapshot",
            "req": {
                "coin": symbol,
                "interval": timeframe,
                "startTime": 0,
            },
        }

        response = requests.post(
            self.BASE_URL,
            json=payload,
            timeout=20,
        )

        response.raise_for_status()

        candles = response.json()

        if not candles:
            return pd.DataFrame()

        df = pd.DataFrame(candles)

        df = df.rename(columns={
            "t": "timestamp",
            "o": "open",
            "h": "high",
            "l": "low",
            "c": "close",
            "v": "volume",
        })

        df = df[
            [
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "volume",
            ]
        ]

        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(float)

        return df.tail(limit).reset_index(drop=True)
