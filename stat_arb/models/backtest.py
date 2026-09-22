"""Pairs Trading Backtester with Z-Score Bands, PnL, and Sharpe Ratio."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
import numpy as np


@dataclass(frozen=True)
class TradeLog:
    entry_idx: int
    exit_idx: int
    side: str  # "LONG_SPREAD" or "SHORT_SPREAD"
    pnl: float
    holding_period: int
    exit_reason: str  # "MEAN_REVERSION" or "STOP_LOSS"


@dataclass(frozen=True)
class BacktestResult:
    total_pnl: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    profitable_trades: int
    trades: List[TradeLog]
    equity_curve: np.ndarray


class PairsTradingBacktester:
    """Simulates statistical arbitrage trading on cointegrated residuals."""

    @classmethod
    def run(
        cls,
        residuals: np.ndarray,
        entry_z: float = 2.0,
        exit_z: float = 0.0,
        stop_z: float = 3.5,
    ) -> BacktestResult:
        n = len(residuals)
        if n < 20:
            raise ValueError(f"At least 20 observations required for backtesting, got {n}")

        mean_res = np.mean(residuals)
        std_res = np.std(residuals, ddof=1)
        if std_res <= 1e-8:
            raise ValueError("Residual variance is effectively zero.")

        z_scores = (residuals - mean_res) / std_res

        position = 0  # 0: flat, +1: long spread (expecting z to rise), -1: short spread (expecting z to fall)
        entry_idx = 0
        entry_val = 0.0
        trades: List[TradeLog] = []

        equity = np.zeros(n)
        current_equity = 0.0

        for i in range(1, n):
            z = z_scores[i]
            res_val = residuals[i]

            if position == 0:
                if z <= -entry_z:
                    position = 1  # Buy spread
                    entry_idx = i
                    entry_val = res_val
                elif z >= entry_z:
                    position = -1  # Sell spread
                    entry_idx = i
                    entry_val = res_val

            elif position == 1:
                # Long spread: profit when spread increases
                if z >= -exit_z:
                    trade_pnl = res_val - entry_val
                    current_equity += trade_pnl
                    trades.append(TradeLog(entry_idx, i, "LONG_SPREAD", trade_pnl, i - entry_idx, "MEAN_REVERSION"))
                    position = 0
                elif z <= -stop_z:
                    trade_pnl = res_val - entry_val
                    current_equity += trade_pnl
                    trades.append(TradeLog(entry_idx, i, "LONG_SPREAD", trade_pnl, i - entry_idx, "STOP_LOSS"))
                    position = 0

            elif position == -1:
                # Short spread: profit when spread decreases
                if z <= exit_z:
                    trade_pnl = entry_val - res_val
                    current_equity += trade_pnl
                    trades.append(TradeLog(entry_idx, i, "SHORT_SPREAD", trade_pnl, i - entry_idx, "MEAN_REVERSION"))
                    position = 0
                elif z >= stop_z:
                    trade_pnl = entry_val - res_val
                    current_equity += trade_pnl
                    trades.append(TradeLog(entry_idx, i, "SHORT_SPREAD", trade_pnl, i - entry_idx, "STOP_LOSS"))
                    position = 0

            equity[i] = current_equity

        total_trades = len(trades)
        wins = [t for t in trades if t.pnl > 0]
        win_rate = (len(wins) / total_trades * 100.0) if total_trades > 0 else 0.0

        # Max drawdown
        peak = np.maximum.accumulate(equity)
        drawdown = peak - equity
        max_dd = float(np.max(drawdown)) if len(drawdown) > 0 else 0.0

        # Sharpe ratio on daily equity changes
        daily_diffs = np.diff(equity)
        std_diff = np.std(daily_diffs)
        if std_diff > 1e-8:
            sharpe = float(np.mean(daily_diffs) / std_diff * np.sqrt(252))
        else:
            sharpe = 0.0

        return BacktestResult(
            total_pnl=float(current_equity),
            sharpe_ratio=sharpe,
            max_drawdown=max_dd,
            win_rate=win_rate,
            total_trades=total_trades,
            profitable_trades=len(wins),
            trades=trades,
            equity_curve=equity
        )
