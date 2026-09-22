"""Fisher Transformation and Correlation Hypothesis Testing."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple
import numpy as np
from scipy.stats import t as student_t, norm


@dataclass(frozen=True)
class CorrelationReport:
    pearson_r: float
    t_statistic: float
    p_value: float
    reject_h0_zero_correlation: bool
    ci_95: Tuple[float, float]
    ci_99: Tuple[float, float]
    # Diagnóstico espúrio: correlação em NÍVEL de preços I(1). NÃO usar
    # para inferência — mantido apenas para evidenciar o viés de
    # regressão espúria (Granger & Newbold, 1974).
    r_levels_spurious: float = float("nan")
    n_returns: int = 0


class FisherCorrelationEngine:
    """Pearson correlation + Fisher CI + t-test sobre LOG-RETURNS.

    Por que log-returns e não preços em nível?
    Preços de ações são tipicamente I(1) (passeio aleatório com drift);
    a correlação de Pearson entre duas séries I(1) em nível é espúria:
    tende a ~1 sempre que ambas têm tendência, mesmo sem relação
    econômica (Granger & Newbold, 1974). A planilha legada usa
    log-returns, estacionários I(0), para a correlação oficial.

    Contrato:
      - Entrada ``x`` / ``y``: SÉRIES DE PREÇOS (níveis, valores > 0).
      - Internamente converte para log-returns
        ``r_t = log(p[t] / p[t-1])`` e toda a inferência
        (``pearson_r``, ``p_value``, ``ci_95``/``ci_99``, ``t_statistic``)
        é calculada SOBRE OS RETURNS, nunca sobre níveis.
      - O campo ``r_levels_spurious`` retorna a correlação em nível
        apenas como diagnóstico do viés espúrio. Não usar para decisão.
    """

    @classmethod
    def analyze(cls, x: np.ndarray, y: np.ndarray) -> CorrelationReport:
        """Calcula correlação oficial sobre log-returns a partir de preços.

        Args:
            x: série de preços do ativo X (níveis, todos > 0).
            y: série de preços do ativo Y (níveis, todos > 0).

        Returns:
            CorrelationReport com ``pearson_r``/CIs/p-valor dos RETURNS.
        """
        px = np.asarray(x, dtype=float).ravel()
        py = np.asarray(y, dtype=float).ravel()
        if px.shape != py.shape:
            raise ValueError(f"Length mismatch: x has {px.size} points, y has {py.size} points")
        n_prices = px.size
        if n_prices < 6:
            # Precisamos de >= 5 log-returns => >= 6 preços.
            raise ValueError(
                f"At least 6 price observations required (5 log-returns) "
                f"for Fisher correlation, got {n_prices}"
            )
        if np.any(~np.isfinite(px)) or np.any(~np.isfinite(py)):
            raise ValueError("Price series must be finite (no NaN/inf).")
        if np.any(px <= 0) or np.any(py <= 0):
            raise ValueError("Price series must be strictly positive for log-returns.")

        # Diagnóstico espúrio (nível) — apenas informativo.
        with np.errstate(invalid="ignore"):
            r_levels = float(np.corrcoef(px, py)[0, 1])

        rx = np.log(px[1:] / px[:-1])
        ry = np.log(py[1:] / py[:-1])
        if np.any(~np.isfinite(rx)) or np.any(~np.isfinite(ry)):
            raise ValueError("Log-returns must be finite (check for zeros/gaps in prices).")

        n = rx.size
        if n < 5:
            raise ValueError(f"At least 5 log-return observations required, got {n}")

        r = float(np.corrcoef(rx, ry)[0, 1])
        if not np.isfinite(r):
            raise ValueError("Zero variance in log-returns: correlation is undefined.")
        r_clamped = max(-0.999999, min(0.999999, r))

        # Student's t test for H0: rho = 0
        df = n - 2
        t_stat = abs(r_clamped) * math.sqrt(df) / math.sqrt(max(1e-12, 1.0 - r_clamped**2))
        p_val = float(2.0 * (1.0 - student_t.cdf(t_stat, df=df)))

        # Fisher Transformation: z = arctanh(r)
        z = math.atanh(r_clamped)
        se_z = 1.0 / math.sqrt(n - 3)

        # 95% (z=1.96) and 99% (z=2.58)
        ci_95_low = math.tanh(z - 1.96 * se_z)
        ci_95_high = math.tanh(z + 1.96 * se_z)

        ci_99_low = math.tanh(z - 2.58 * se_z)
        ci_99_high = math.tanh(z + 2.58 * se_z)

        return CorrelationReport(
            pearson_r=r,
            t_statistic=float(t_stat),
            p_value=p_val,
            reject_h0_zero_correlation=(p_val < 0.05),
            ci_95=(float(ci_95_low), float(ci_95_high)),
            ci_99=(float(ci_99_low), float(ci_99_high)),
            r_levels_spurious=r_levels,
            n_returns=int(n),
        )
