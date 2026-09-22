"""B3 Statistical Arbitrage & Pairs Trading Engine.

Econometric Engle-Granger cointegration, AR(1) Dickey-Fuller unit-root test,
Ornstein-Uhlenbeck half-life estimation, Fisher correlation bounds, and Z-Score execution.
"""

__version__ = "1.0.0"
__author__ = "Costa Junior (CostaJr007)"

from .models.cointegration import CointegrationEngine, CointegrationResult
from .models.dickey_fuller_ar1 import DickeyFullerAR1Test, ADFTestResult
from .models.ornstein_uhlenbeck import OrnsteinUhlenbeckEngine, OUParameters
from .models.fisher_correlation import FisherCorrelationEngine, CorrelationReport
from .models.backtest import PairsTradingBacktester, BacktestResult

__all__ = [
    "CointegrationEngine",
    "CointegrationResult",
    "DickeyFullerAR1Test",
    "ADFTestResult",
    "OrnsteinUhlenbeckEngine",
    "OUParameters",
    "FisherCorrelationEngine",
    "CorrelationReport",
    "PairsTradingBacktester",
    "BacktestResult",
]
