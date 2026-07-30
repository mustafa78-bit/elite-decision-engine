import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class EpisodicMemory:
    """
    NEXUS Episodic Memory Layer.
    Models, records, and stores complete decision episodes and cognitive lifecycles,
    preserving full replay traceability linked back to the Blackboard events.
    """
    def __init__(self):
        self.episodes: List[Dict[str, Any]] = []

    def record_episode(
        self,
        signal_id: int,
        symbol: str,
        side: str,
        score: float,
        confidence: float,
        reasoning_chain: List[str],
        guard_status: str,
        event_chain: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        episode = {
            "signal_id": signal_id,
            "symbol": symbol,
            "side": side,
            "score": score,
            "confidence": confidence,
            "reasoning_chain": reasoning_chain,
            "guard_status": guard_status,
            "event_chain": event_chain,
            "replay_reconstructable": True
        }
        self.episodes.append(episode)
        logger.info(f"Recorded new Episodic Memory segment for {symbol} {side}. Replay ready.")
        return episode

    def get_episode_by_signal(self, signal_id: int) -> Dict[str, Any]:
        for ep in self.episodes:
            if ep["signal_id"] == signal_id:
                return ep
        return {"error": f"Signal {signal_id} episode not found."}

    def list_episodes(self) -> List[Dict[str, Any]]:
        return self.episodes
