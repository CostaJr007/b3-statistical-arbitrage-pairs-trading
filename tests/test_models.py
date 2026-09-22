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
    # OFFICIAL correlation is on log-returns: build prices from
    # correlated (I(0)) returns instead of deterministic level trends.
    np.random.seed(42)
    n = 200
    rx = np.random.normal(0.0002, 0.015, n)
    ry = 0.9 * rx + np.random.normal(0.0, 0.005, n)
    x = 50.0 * np.exp(np.cumsum(rx))
    y = 30.0 * np.exp(np.cumsum(ry))
    rep = FisherCorrelationEngine.analyze(x, y)

    # Official r must reflect returns (~0.94), not the spurious level (~1.0).
    # Note: analyze() derives returns from prices via log(p[1:]/p[:-1]),
    # hence it recovers rx[1:]/ry[1:] (the 1st cumsum obs. is absorbed in the level).
    expected_ret_r = float(np.corrcoef(rx[1:], ry[1:])[0, 1])
    assert rep.pearson_r == pytest.approx(expected_ret_r, abs=1e-9)
    assert rep.pearson_r > 0.85
    assert rep.reject_h0_zero_correlation is True
    assert rep.ci_95[0] > 0.80
    assert rep.n_returns == n - 1
    # Level diagnostic kept separately and labelled as spurious
    assert np.isfinite(rep.r_levels_spurious)

    # Classic spurious-regression case: level trends have r_levels ~ 1
    # but returns r ~ 0 - proof that level inference is invalid.
    xs = np.linspace(10, 50, 100)
    ys = 2.0 * xs + np.random.normal(0, 5, 100)
    spurious = FisherCorrelationEngine.analyze(xs, ys)
    assert spurious.r_levels_spurious > 0.95
    assert abs(spurious.pearson_r) < 0.30

    # Prices must be strictly positive for log-returns
    with pytest.raises(ValueError):
        FisherCorrelationEngine.analyze(np.array([1.0, 0.0, 2.0, 3.0, 4.0, 5.0, 6.0]),
                                        np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]))


def test_pairs_trading_backtest():
    y, x = B3PairsDataLoader.generate_cointegrated_pair(n=400, theta=0.15, noise_std=1.0)
    coint = CointegrationEngine.fit(y, x)
    res = PairsTradingBacktester.run(coint.residuals, entry_z=2.0, exit_z=0.0)

    assert res.total_trades > 0
    assert len(res.equity_curve) == 400

    # New transaction_cost parameter: deducted per round-trip, reduces PnL
    # by exactly n_trades * cost (default 0.0 preserves legacy result).
    res_cost = PairsTradingBacktester.run(
        coint.residuals, entry_z=2.0, exit_z=0.0, transaction_cost=0.5
    )
    assert res_cost.total_trades == res.total_trades
    assert res_cost.total_pnl == pytest.approx(
        res.total_pnl - 0.5 * res.total_trades, abs=1e-9
    )

    # Sharpe uses ddof=1 + configurable annualization: replicate the formula
    # over daily diffs to lock the behavior.
    diffs = np.diff(res.equity_curve)
    expected_sharpe = (
        float(np.mean(diffs) / np.std(diffs, ddof=1) * np.sqrt(252))
        if diffs.size >= 2 and float(np.std(diffs, ddof=1)) > 1e-8 else 0.0
    )
    assert res.sharpe_ratio == pytest.approx(expected_sharpe, rel=1e-9)
    res_ann = PairsTradingBacktester.run(
        coint.residuals, entry_z=2.0, exit_z=0.0, annualization=126
    )
    assert res_ann.sharpe_ratio == pytest.approx(
        res.sharpe_ratio * np.sqrt(126 / 252), rel=1e-9
    )

    # risk_free shifts the diffs mean before annualization.
    res_rf = PairsTradingBacktester.run(
        coint.residuals, entry_z=2.0, exit_z=0.0, risk_free=0.01
    )
    assert res_rf.total_pnl == pytest.approx(res.total_pnl, abs=1e-9)
    assert res_rf.sharpe_ratio != pytest.approx(res.sharpe_ratio, rel=1e-6)


def test_dickey_fuller_warns_on_small_sample():
    # Fixed thresholds (n~200) are lenient with n<100: requires UserWarning.
    rng = np.random.default_rng(7)
    with pytest.warns(UserWarning, match="n=50 < 100"):
        DickeyFullerAR1Test.test(rng.normal(0, 1, 50), nobs=50)
