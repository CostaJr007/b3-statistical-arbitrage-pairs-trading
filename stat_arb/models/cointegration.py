"""OLS Cointegration Regression Engine with optional Deterministic Time Trend."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Union
import numpy as np


@dataclass(frozen=True)
class CointegrationResult:
    beta_hedge_ratio: float
    intercept: float
    time_trend_gamma: float
    residuals: np.ndarray
    r_squared: float
    std_residuals: float
    has_trend: bool


class CointegrationEngine:
    """Estimates the equilibrium relationship between dependent and independent asset prices."""

    @classmethod
    def fit(
        cls,
        y_dependent: Union[Sequence[float], np.ndarray],
        x_independent: Union[Sequence[float], np.ndarray],
        include_time_trend: bool = False,
    ) -> CointegrationResult:
        """Estimate OLS: Y_t = alpha + beta * X_t (+ gamma * t) + epsilon_t."""
        y = np.asarray(y_dependent, dtype=float)
        x = np.asarray(x_independent, dtype=float)
        n = len(y)
        if n != len(x):
            raise ValueError(f"Length mismatch: y has {n} points, x has {len(x)} points")
        if n < 10:
            raise ValueError(f"At least 10 observations required, got {n}")

        # Construct design matrix
        t_index = np.arange(1, n + 1, dtype=float)
        if include_time_trend:
            # Columns: [1, x, t]
            X_mat = np.column_stack([np.ones(n), x, t_index])
        else:
            # Columns: [1, x]
            X_mat = np.column_stack([np.ones(n), x])

        # OLS closed-form solver: beta_vec = (X'X)^(-1) X'Y
        coeffs, _, _, _ = np.linalg.lstsq(X_mat, y, rcond=None)

        if include_time_trend:
            alpha = float(coeffs[0])
            beta = float(coeffs[1])
            gamma = float(coeffs[2])
            y_pred = alpha + beta * x + gamma * t_index
        else:
            alpha = float(coeffs[0])
            beta = float(coeffs[1])
            gamma = 0.0
            y_pred = alpha + beta * x

        residuals = y - y_pred
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        ss_res = np.sum(residuals ** 2)
        r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        std_res = float(np.std(residuals, ddof=2 if not include_time_trend else 3))

        return CointegrationResult(
            beta_hedge_ratio=beta,
            intercept=alpha,
            time_trend_gamma=gamma,
            residuals=residuals,
            r_squared=float(r2),
            std_residuals=std_res,
            has_trend=include_time_trend
        )
