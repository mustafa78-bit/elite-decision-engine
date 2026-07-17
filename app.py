from database import create_tables
from core.engine import DecisionEngine
from core.intelligence import IntelligenceBundle
from whale.integration import WhaleIntegration
from liquidity.integration import LiquidityIntegration
from orderflow.integration import OrderFlowIntegration
from market_structure.integration import MarketStructureIntegration
from config import (
    WHALE_ENABLED,
    LIQUIDITY_ENABLED,
    ORDERFLOW_ENABLED,
    MARKET_STRUCTURE_ENABLED,
)


def main():

    create_tables()

    print("Elite Decision Engine Started")

    intelligence = IntelligenceBundle()

    if WHALE_ENABLED:
        whale = WhaleIntegration()
        intelligence.enable_whale(whale)
        print("Whale intelligence enabled")

    if LIQUIDITY_ENABLED:
        liquidity = LiquidityIntegration()
        intelligence.enable_liquidity(liquidity)
        print("Liquidity intelligence enabled")

    if ORDERFLOW_ENABLED:
        orderflow = OrderFlowIntegration()
        intelligence.enable_orderflow(orderflow)
        print("Order flow intelligence enabled")

    if MARKET_STRUCTURE_ENABLED:
        ms = MarketStructureIntegration()
        intelligence.enable_market_structure(ms)
        print("Market structure intelligence enabled")

    engine = DecisionEngine(intelligence=intelligence)

    engine.run()


if __name__ == "__main__":
    main()
