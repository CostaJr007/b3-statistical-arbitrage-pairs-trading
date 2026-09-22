"""Ornstein-Uhlenbeck (OU) Stochastic Process and Half-Life Estimation."""

from __future__ import annotations

import math
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class OUParameters:
    theta_speed: float        # Mean-reversion speed (annualized or daily)
    half_life_days: float     # Days to revert 50% toward mean
    equilibrium_mean: float   # Long-term mean level
    asymptotic_volatility: float
    is_mean_reverting: bool


class OrnsteinUhlenbeckEngine:
    """Estimates Ornstein-Uhlenbeck diffusion parameters: dX_t = theta * (mu - X_t) dt + sigma * dW_t."""

    @classmethod
    def estimate_from_residuals(
        cls,
        residuals: np.ndarray,
        phi: float,
        dt: float = 1.0,  # 1 day
    ) -> OUParameters:
        """Derive continuous OU parameters from discrete AR(1) coefficient phi = rho - 1."""
        rho = 1.0 + phi
        eps_mean = float(np.mean(residuals))
        eps_std = float(np.std(residuals, ddof=1))

        # Mean reversion requires 0 < rho < 1 (i.e. -1 < phi < 0)
        if rho <= 0 or rho >= 1.0:
            return OUParameters(
                theta_speed=0.0,
                half_life_days=float("inf"),
                equilibrium_mean=eps_mean,
                asymptotic_volatility=eps_std,
                is_mean_reverting=False
            )

        # Continuous speed theta = -ln(rho) / dt
        theta = -math.log(rho) / dt
        # Half life = ln(2) / theta
        half_life = math.log(2.0) / theta

        # Asymptotic volatility formula used in the spreadsheet:
        # sigma_OU = sigma_eps * sqrt( ln(1 + phi) / ((1 + phi)^2 - 1) )
        try:
            factor = math.log(rho) / (rho**2 - 1.0)
            ou_vol = eps_std * math.sqrt(max(0.0, factor))
        except (ValueError, ZeroDivisionError):
            ou_vol = eps_std

        return OUParameters(
            theta_speed=float(theta),
            half_life_days=float(half_life),
            equilibrium_mean=eps_mean,
            asymptotic_volatility=float(ou_vol),
            is_mean_reverting=True
        )
