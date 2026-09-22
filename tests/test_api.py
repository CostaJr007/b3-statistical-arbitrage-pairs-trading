"""Unit tests for stat arb FastAPI endpoints."""

from fastapi.testclient import TestClient
from stat_arb.api.server import app
from stat_arb.connectors.data_loader import B3PairsDataLoader

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["service"] == "b3-statistical-arbitrage"


def test_analyze_pair_endpoint():
    y, x = B3PairsDataLoader.generate_cointegrated_pair(n=100)
    payload = {
        "y_dependent_prices": y.tolist(),
        "x_independent_prices": x.tolist(),
        "include_time_trend": False
    }
    res = client.post("/api/v1/analyze-pair", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "beta_hedge_ratio" in data
    assert "dickey_fuller" in data
    assert "ornstein_uhlenbeck" in data
    assert "half_life_days" in data["ornstein_uhlenbeck"]


def test_backtest_endpoint():
    y, x = B3PairsDataLoader.generate_cointegrated_pair(n=100)
    payload = {
        "y_dependent_prices": y.tolist(),
        "x_independent_prices": x.tolist(),
        "entry_z": 2.0,
        "exit_z": 0.0,
        "stop_z": 3.5
    }
    res = client.post("/api/v1/backtest", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "total_pnl" in data
    assert "win_rate" in data
