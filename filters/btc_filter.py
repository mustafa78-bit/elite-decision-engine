class BTCHealthFilter:
    def __init__(self):
        pass

    def evaluate(self, data=None):
        return {
            "ok": True,
            "score": 1.0,
            "reason": "placeholder btc filter active"
        }