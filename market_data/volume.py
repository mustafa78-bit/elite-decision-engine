class VolumeEngine:

    def score(self, df):

        volume_now = float(df["volume"].iloc[-1])

        volume_avg = float(
            df["volume"].tail(20).mean()
        )

        ratio = volume_now / volume_avg

        if ratio >= 2.0:
            score = 1.0
        elif ratio >= 1.5:
            score = 0.8
        elif ratio >= 1.2:
            score = 0.7
        elif ratio >= 1.0:
            score = 0.5
        else:
            score = 0.3

        return {
            "current_volume": volume_now,
            "average_volume": volume_avg,
            "ratio": round(ratio, 2),
            "score": score,
        }
