"""Unit tests for statistical arbitrage models."""

import pytest
import math
import numpy as np
from stat_arb.models.cointegration import CointegrationEngine
from stat_arb.models.dickey_fuller_ar1 import DickeyFullerAR1Test
from stat_arb.models.ornstein_uhlenbeck import OrnsteinUhlenbeckEngine
from stat_arb.models.fisher_correlation import FisherCorrelationEngine
from stat_arb.models.backtest import PairsTradingBacktester
from stat_arb.connectors.data_loader import B3PairsDataLoader


def test_cointegration_engine():
    y, x = B3PairsDataLoader.generate_cointegrated_pair(n=200, beta=1.5, alpha=2.0)
    res = CointegrationEngine.fit(y, x, include_time_trend=False)

    # Beta hedge ratio should be close to 1.5
    assert math.isclose(res.beta_hedge_ratio, 1.5, abs_tol=0.20)
    assert res.r_squared > 0.85
    assert len(res.residuals) == 200
    # Mean of OLS residuals is always approximately 0
    assert math.isclose(float(np.mean(res.residuals)), 0.0, abs_tol=1e-5)


def test_dickey_fuller_ar1_and_ou():
    y, x = B3PairsDataLoader.generate_cointegrated_pair(n=300, theta=0.20)
    coint = CointegrationEngine.fit(y, x)
    adf = DickeyFullerAR1Test.test(coint.residuals)

    assert adf.t_stat < -2.60
    assert adf.is_cointegrated_90 is True
    assert -1.0 < adf.phi < 0.0

    ou = OrnsteinUhlenbeckEngine.estimate_from_residuals(coint.residuals, adf.phi)
    assert ou.is_mean_reverting is True
    assert 2.0 < ou.half_life_days < 30.0


def test_fisher_correlation():
    np.random.seed(42)
    x = np.linspace(10, 50, 100)
    y = 2.0 * x + np.random.normal(0, 5, 100)
    rep = FisherCorrelationEngine.analyze(x, y)

    assert rep.pearson_r > 0.90
    assert rep.reject_h0_zero_correlation is True
    assert rep.ci_95[0] > 0.85


def test_pairs_trading_backtest():
    y, x = B3PairsDataLoader.generate_cointegrated_pair(n=400, theta=0.15, noise_std=1.0)
    coint = CointegrationEngine.fit(y, x)
    res = PairsTradingBacktester.run(coint.residuals, entry_z=2.0, exit_z=0.0)

    assert res.total_trades > 0
    assert len(res.equity_curve) == 400
