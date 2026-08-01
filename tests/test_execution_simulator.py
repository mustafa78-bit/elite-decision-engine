"""Tests for execution simulator."""

from decimal import Decimal

from simulator.execution_simulator import ExecutionSimulator, SimulationConfig


class TestExecutionSimulator:
    def test_simulate_fill_default(self):
        sim = ExecutionSimulator()
        result = sim.simulate_fill(
            order_id="test_1",
            symbol="BTC",
            side="BUY",
            quantity=Decimal("0.1"),
            price=Decimal("50000"),
        )
        assert result.order_id == "test_1"
        assert result.symbol == "BTC"
        assert result.side == "BUY"
        assert result.requested_quantity == Decimal("0.1")
        assert result.fill_price > Decimal("0")
        assert result.fee >= Decimal("0")
        assert result.latency_ms >= 0

    def test_slippage_buy(self):
        sim = ExecutionSimulator(config=SimulationConfig(slippage_bps=10))
        result = sim.simulate_fill(
            order_id="test", symbol="BTC", side="BUY",
            quantity=Decimal("1"), price=Decimal("100"),
        )
        # 10 bps = 0.1%, so fill price should be ~100.1
        assert result.fill_price > Decimal("100")

    def test_slippage_sell(self):
        sim = ExecutionSimulator(config=SimulationConfig(slippage_bps=10))
        result = sim.simulate_fill(
            order_id="test", symbol="BTC", side="SELL",
            quantity=Decimal("1"), price=Decimal("100"),
        )
        assert result.fill_price < Decimal("100")

    def test_partial_fill(self):
        sim = ExecutionSimulator(config=SimulationConfig(partial_fill_probability=1.0))
        result = sim.simulate_fill(
            order_id="test", symbol="BTC", side="BUY",
            quantity=Decimal("1"), price=Decimal("100"),
        )
        assert result.partial is True
        assert result.filled_quantity < Decimal("1")
        assert result.filled_quantity > Decimal("0")

    def test_full_fill_zero_partial_prob(self):
        sim = ExecutionSimulator(config=SimulationConfig(partial_fill_probability=0.0))
        for _ in range(20):
            result = sim.simulate_fill(
                order_id="test", symbol="BTC", side="BUY",
                quantity=Decimal("1"), price=Decimal("100"),
            )
            assert result.partial is False
            assert result.filled_quantity == Decimal("1")

    def test_calculate_net_pnl_long(self):
        sim = ExecutionSimulator(config=SimulationConfig(slippage_bps=0, fee_rate=0))
        entry = sim.simulate_fill("e1", "BTC", "BUY", Decimal("1"), Decimal("100"))
        exit = sim.simulate_fill("e2", "BTC", "SELL", Decimal("1"), Decimal("110"))
        pnl = sim.calculate_net_pnl(entry, exit)
        assert pnl > Decimal("0")

    def test_calculate_net_pnl_with_fees(self):
        sim = ExecutionSimulator(config=SimulationConfig(slippage_bps=0, fee_rate=0.001))
        entry = sim.simulate_fill("e1", "BTC", "BUY", Decimal("1"), Decimal("100"))
        exit = sim.simulate_fill("e2", "BTC", "SELL", Decimal("1"), Decimal("100"))
        pnl = sim.calculate_net_pnl(entry, exit)
        # With 0.1% fee each way, should be negative
        assert pnl < Decimal("0")

    def test_report(self):
        sim = ExecutionSimulator()
        result = sim.simulate_fill("r1", "BTC", "BUY", Decimal("0.1"), Decimal("50000"))
        report = sim.report(result)
        assert "r1" in report
        assert "BTC" in report
        assert "BUY" in report
