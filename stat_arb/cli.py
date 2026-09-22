"""Command-line interface for B3 Statistical Arbitrage & Pairs Trading."""

from __future__ import annotations

import argparse
import uvicorn
import numpy as np
from .models.cointegration import CointegrationEngine
from .models.dickey_fuller_ar1 import DickeyFullerAR1Test
from .models.ornstein_uhlenbeck import OrnsteinUhlenbeckEngine
from .models.fisher_correlation import FisherCorrelationEngine
from .models.backtest import PairsTradingBacktester
from .connectors.data_loader import B3PairsDataLoader


def main():
    parser = argparse.ArgumentParser(
        prog="stat-arb",
        description="B3 Statistical Arbitrage & Pairs Trading CLI"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: analyze
    p_analyze = subparsers.add_parser("analyze", help="Analyze cointegration and OU half-life between two assets")
    p_analyze.add_argument("--trend", action="store_true", help="Include deterministic time trend")
    p_analyze.add_argument("--samples", type=int, default=250, help="Number of points in synthetic pair")

    # Subcommand: backtest
    p_bt = subparsers.add_parser("backtest", help="Run pairs trading backtest simulation")
    p_bt.add_argument("--entry-z", type=float, default=2.0)
    p_bt.add_argument("--stop-z", type=float, default=3.5)

    # Subcommand: serve
    p_serve = subparsers.add_parser("serve", help="Launch FastAPI REST server")
    p_serve.add_argument("--host", type=str, default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8003)

    args = parser.parse_args()

    if args.command == "analyze":
        y, x = B3PairsDataLoader.generate_cointegrated_pair(n=args.samples)
        coint = CointegrationEngine.fit(y, x, include_time_trend=args.trend)
        adf = DickeyFullerAR1Test.test(coint.residuals, has_trend=args.trend)
        ou = OrnsteinUhlenbeckEngine.estimate_from_residuals(coint.residuals, adf.phi)
        # analyze() takes PRICES and computes r/p-value/CI on LOG-RETURNS;
        # r_levels is only a spurious diagnostic (do not use for inference).
        correl = FisherCorrelationEngine.analyze(x, y)

        print("=" * 65)
        print("ENGLE-GRANGER COINTEGRATION & ORNSTEIN-UHLENBECK ANALYSIS")
        print("=" * 65)
        print(f"Hedge Ratio (Beta):      {coint.beta_hedge_ratio:.4f}")
        print(f"Intercept (Alpha):        {coint.intercept:.4f}")
        if args.trend:
            print(f"Time Trend (Gamma):       {coint.time_trend_gamma:.6f}")
        print(f"R-Squared:                {coint.r_squared*100:.2f}%")
        print(f"Residuals Std Dev:        {coint.std_residuals:.4f}")
        print("-" * 65)
        print(f"Dickey-Fuller t-stat:     {adf.t_stat:.4f} (Phi = {adf.phi:+.4f})")
        print(f"Cointegrated (95% crit):  {adf.is_cointegrated_95} (threshold {adf.critical_values['95%']})")
        print(f"Cointegrated (99% crit):  {adf.is_cointegrated_99} (threshold {adf.critical_values['99%']})")
        print(f"Conclusion:               {adf.conclusion}")
        print("-" * 65)
        print(f"OU Mean-Reversion Speed:  {ou.theta_speed:.4f} / day")
        print(f"Half-Life:                {ou.half_life_days:.1f} business days")
        print(f"Asymptotic Volatility:    {ou.asymptotic_volatility:.4f}")
        print("-" * 65)
        print(f"Pearson Correlation (r, log-returns):  {correl.pearson_r:.4f} (p-value: {correl.p_value:.4e})")
        print(f"Fisher 95% CI (returns):            [{correl.ci_95[0]:.4f}, {correl.ci_95[1]:.4f}]")
        print(f"Fisher 99% CI (returns):            [{correl.ci_99[0]:.4f}, {correl.ci_99[1]:.4f}]")
        print(f"Levels r (SPURIOUS diagnostic):     {correl.r_levels_spurious:.4f} (n_ret={correl.n_returns})")
        print("=" * 65)

    elif args.command == "backtest":
        y, x = B3PairsDataLoader.generate_cointegrated_pair(n=500)
        coint = CointegrationEngine.fit(y, x)
        res = PairsTradingBacktester.run(coint.residuals, entry_z=args.entry_z, stop_z=args.stop_z)

        print("=" * 65)
        print("PAIRS TRADING BACKTEST RESULTS")
        print("=" * 65)
        print(f"Total Net PnL:            ${res.total_pnl:,.2f}")
        print(f"Sharpe Ratio:             {res.sharpe_ratio:.2f}")
        print(f"Max Drawdown:             ${res.max_drawdown:,.2f}")
        print(f"Win Rate:                 {res.win_rate:.1f}%")
        print(f"Total Trades:             {res.total_trades} ({res.profitable_trades} wins)")
        print("=" * 65)

    elif args.command == "serve":
        print(f"Starting Stat-Arb API at http://{args.host}:{args.port}")
        uvicorn.run("stat_arb.api.server:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
