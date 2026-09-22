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
    """Simulates statistical arbitrage trading on cointegrated residuals.

    Limitações conhecidas (documentadas de propósito):
      - Z-score IN-SAMPLE: ``mean``/``std`` são calculados sobre TODA a
        amostra de resíduos (look-ahead bias). Em produção, usar média/std
        expandidos ou rolantes estimados só com dados até t-1.
      - Sem mark-to-market intradiário: o PnL só é realizado no fechamento
        do trade; a curva de equity é constante entre entry e exit (step
        function), de modo que o drawdown intradiário é subestimado.
      - Dias flat INCLUÍDOS por padrão no Sharpe (``include_flat_days=True``):
        ``np.diff(equity)`` contém zeros nos dias sem trade, o que dilui a
        média e o desvio. Passe ``exclude_flat_days=True`` para excluir os
        diffs nulos do cálculo (não muda o default).
      - Sharpe usa ``ddof=1`` (desvio amostral) e fator ``sqrt(annualization)``.
      - ``transaction_cost`` é um custo fixo por round-trip (nas mesmas
        unidades do spread/resíduo), deduzido do PnL de cada trade.
        Default 0.0 preserva o comportamento histórico.
      - ``risk_free`` é a taxa livre de risco POR PERÍODO (diária por padrão),
        subtraída da média dos diffs diários antes da anualização.
        Default 0.0 preserva o comportamento histórico.
    """

    @classmethod
    def run(
        cls,
        residuals: np.ndarray,
        entry_z: float = 2.0,
        exit_z: float = 0.0,
        stop_z: float = 3.5,
        risk_free: float = 0.0,
        transaction_cost: float = 0.0,
        annualization: int = 252,
        exclude_flat_days: bool = False,
    ) -> BacktestResult:
        """Run the Z-score band backtest.

        Args:
            residuals: spread da cointegração.
            entry_z: |z| de entrada. exit_z: |z| de saída. stop_z: |z| de stop.
            risk_free: taxa livre de risco por período (default 0.0).
            transaction_cost: custo fixo por round-trip trade (default 0.0).
            annualization: fator de anualização do Sharpe (default 252).
            exclude_flat_days: se True, exclui diffs diários == 0 do Sharpe.
                Default False (mantém comportamento histórico).

        Returns:
            BacktestResult com PnL líquido de custos e Sharpe com ddof=1.
        """
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
                # Long spread: profit when spread increases (net of costs)
                if z >= -exit_z:
                    trade_pnl = (res_val - entry_val) - transaction_cost
                    current_equity += trade_pnl
                    trades.append(TradeLog(entry_idx, i, "LONG_SPREAD", trade_pnl, i - entry_idx, "MEAN_REVERSION"))
                    position = 0
                elif z <= -stop_z:
                    trade_pnl = (res_val - entry_val) - transaction_cost
                    current_equity += trade_pnl
                    trades.append(TradeLog(entry_idx, i, "LONG_SPREAD", trade_pnl, i - entry_idx, "STOP_LOSS"))
                    position = 0

            elif position == -1:
                # Short spread: profit when spread decreases (net of costs)
                if z <= exit_z:
                    trade_pnl = (entry_val - res_val) - transaction_cost
                    current_equity += trade_pnl
                    trades.append(TradeLog(entry_idx, i, "SHORT_SPREAD", trade_pnl, i - entry_idx, "MEAN_REVERSION"))
                    position = 0
                elif z >= stop_z:
                    trade_pnl = (entry_val - res_val) - transaction_cost
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

        # Sharpe ratio on daily equity changes (ddof=1, sample std).
        # NOTE: daily_diffs includes flat days (zeros) by default.
        daily_diffs = np.diff(equity)
        if exclude_flat_days:
            daily_diffs = daily_diffs[daily_diffs != 0.0]
        if daily_diffs.size >= 2:
            std_diff = float(np.std(daily_diffs, ddof=1))
            if std_diff > 1e-8:
                excess_mean = float(np.mean(daily_diffs) - risk_free)
                sharpe = float(excess_mean / std_diff * np.sqrt(float(annualization)))
            else:
                sharpe = 0.0
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
