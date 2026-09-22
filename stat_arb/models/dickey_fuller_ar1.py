"""AR(1) Dickey-Fuller Unit Root Test on Cointegration Residuals."""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from typing import Dict, Optional
import numpy as np


@dataclass(frozen=True)
class ADFTestResult:
    phi: float  # Slope (rho - 1)
    rho: float  # AR(1) autoregressive parameter (1 + phi)
    std_error_phi: float
    t_stat: float
    is_cointegrated_90: bool
    is_cointegrated_95: bool
    is_cointegrated_99: bool
    critical_values: Dict[str, float]
    conclusion: str


class DickeyFullerAR1Test:
    """Tests for mean-reversion and absence of unit root in cointegration residuals (Delta eps = phi * eps_{t-1}).

    Limitação conhecida dos valores críticos (MacKinnon):
      - ``CRITICAL_VALUES_*`` são valores FIXOS inspirados em
        MacKinnon (1991) para o teste de Engle-Granger com 2 variáveis,
        calibrados para amostras assintóticas / n ≈ 200, SEM ajuste pelo
        tamanho amostral T.
      - A superfície de resposta completa de MacKinnon
        (critical value = f(T, nº de variáveis, trend)) NÃO está
        implementada aqui. Resultado: com T pequeno o teste é LENIENTE,
        i.e. tem viés pró-cointegração (rejeita H0 de raiz unitária com
        mais facilidade do que deveria), aumentando o risco de regressão
        espúria ser classificada como cointegrada.
      - NÃO foi adicionada dependência de ``statsmodels`` de propósito
        (pacote deve permanecer leve/sem dependência extra).
      - Mitigação mínima: o parâmetro opcional ``nobs`` registra o T
        efetivo e um ``warnings.warn`` é emitido quando n < 100 para
        sinalizar a fragilidade dos thresholds.
    """

    # MacKinnon (1991) asymptotic critical values for Engle-Granger 2-variable test
    CRITICAL_VALUES_NO_TREND = {"90%": -2.60, "95%": -3.22, "99%": -3.58}
    CRITICAL_VALUES_WITH_TREND = {"90%": -3.28, "95%": -3.67, "99%": -4.32}

    @classmethod
    def test(
        cls,
        residuals: np.ndarray,
        has_trend: bool = False,
        nobs: Optional[int] = None,
    ) -> ADFTestResult:
        """Run the AR(1) Dickey-Fuller regression on residuals.

        Args:
            residuals: spread/resíduos da cointegração (I(0) sob H1).
            has_trend: usa tabela com tendência determinística.
            nobs: tamanho amostral efetivo (opcional, documentacional).
                Se omitido, usa ``len(residuals)``. Existe para futura
                correção por T (superfície de MacKinnon) sem quebrar a API;
                hoje NENHUM ajuste por T é aplicado — ver docstring da classe.

        Warns:
            UserWarning: se n < 100, pois os thresholds fixos (n≈200,
                assintóticos) são lenientes nesse regime.
        """
        eps = np.asarray(residuals, dtype=float)
        n = len(eps)
        if n < 10:
            raise ValueError(f"Need at least 10 residual observations, got {n}")
        if nobs is None:
            nobs = n
        if n < 100:
            warnings.warn(
                f"Dickey-Fuller AR(1): n={n} < 100. Fixed MacKinnon thresholds "
                f"(calibrated for n≈200/asymptotic, no sample-size adjustment) "
                f"are lenient in small samples and biased toward finding "
                f"cointegration. Interpret with caution.",
                UserWarning,
                stacklevel=2,
            )

        # Delta eps_t = eps_t - eps_{t-1}
        delta_eps = eps[1:] - eps[:-1]
        lagged_eps = eps[:-1]

        # Regress delta_eps on lagged_eps (without intercept, as residuals mean ~ 0)
        # OLS slope: phi = sum(delta_eps * lagged_eps) / sum(lagged_eps^2)
        denom = np.sum(lagged_eps ** 2)
        if denom <= 1e-12:
            raise ValueError("Zero variance in lagged residuals.")

        phi = float(np.sum(delta_eps * lagged_eps) / denom)
        rho = float(1.0 + phi)

        # Residuals of AR(1) equation: u_t = delta_eps - phi * lagged_eps
        u_t = delta_eps - phi * lagged_eps
        var_u = float(np.sum(u_t ** 2) / (n - 2))
        se_phi = math.sqrt(max(1e-12, var_u / denom))

        t_stat = float(phi / se_phi)

        crit = cls.CRITICAL_VALUES_WITH_TREND if has_trend else cls.CRITICAL_VALUES_NO_TREND

        c90 = t_stat <= crit["90%"]
        c95 = t_stat <= crit["95%"]
        c99 = t_stat <= crit["99%"]

        if c99:
            conclusion = "Cointegration Confirmed (p < 0.01) - Spread is Stationary I(0)"
        elif c95:
            conclusion = "Cointegration Confirmed (p < 0.05) - Spread is Stationary I(0)"
        elif c90:
            conclusion = "Weak Cointegration (p < 0.10) - Potential Mean-Reversion"
        else:
            conclusion = "Fail to Reject Unit Root - No Cointegration (Spurious Regression)"

        return ADFTestResult(
            phi=phi,
            rho=rho,
            std_error_phi=se_phi,
            t_stat=t_stat,
            is_cointegrated_90=c90,
            is_cointegrated_95=c95,
            is_cointegrated_99=c99,
            critical_values=crit,
            conclusion=conclusion
        )
