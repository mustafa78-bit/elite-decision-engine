class BTCHealthFilter:
    def __init__(self):
        pass

    def is_healthy(self):
        return True

    def evaluate(self, data=None):
        return {
            "ok": True,
            "score": 1.0,
            "reason": "placeholder btc filter active"
        }
