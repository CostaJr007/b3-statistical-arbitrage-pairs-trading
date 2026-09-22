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


class FisherCorrelationEngine:
    """Calculates Fisher-transformed correlation confidence intervals and t-test."""

    @classmethod
    def analyze(cls, x: np.ndarray, y: np.ndarray) -> CorrelationReport:
        n = len(x)
        if n < 5:
            raise ValueError(f"At least 5 observations required for Fisher correlation, got {n}")

        r = float(np.corrcoef(x, y)[0, 1])
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
        )
