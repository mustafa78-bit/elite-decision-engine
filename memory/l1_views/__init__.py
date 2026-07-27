import logging
from memory.l1_views.registry import global_registry
from memory.l1_views.projections.coin_projection import CoinProjection
from memory.l1_views.projections.whale_projection import WhaleProjection
from memory.l1_views.projections.news_projection import NewsProjection
from memory.l1_views.projections.decision_projection import DecisionProjection
from memory.l1_views.projections.portfolio_projection import PortfolioProjection

logger = logging.getLogger(__name__)

# Dynamically register all L1 Projections on initialization
try:
    global_registry.register(CoinProjection())
    global_registry.register(WhaleProjection())
    global_registry.register(NewsProjection())
    global_registry.register(DecisionProjection())
    global_registry.register(PortfolioProjection())
    logger.info("NEXUS L1 views initialized and projections registered successfully.")
except ValueError as e:
    # Handle duplicate registration gracefully in testing/module reload scenarios
    logger.debug("L1 views already initialized: %s", e)
