"""FastAPI Microservice for B3 Statistical Arbitrage & Pairs Trading."""

from __future__ import annotations

from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import numpy as np

from ..models.cointegration import CointegrationEngine
from ..models.dickey_fuller_ar1 import DickeyFullerAR1Test
from ..models.ornstein_uhlenbeck import OrnsteinUhlenbeckEngine
from ..models.fisher_correlation import FisherCorrelationEngine
from ..models.backtest import PairsTradingBacktester
from ..connectors.data_loader import B3PairsDataLoader


app = FastAPI(
    title="B3 Statistical Arbitrage & Pairs Trading API",
    description="Engle-Granger cointegration, AR(1) Dickey-Fuller test, Ornstein-Uhlenbeck half-life & Z-Score execution",
    version="1.0.0"
)


class PairAnalysisRequest(BaseModel):
    y_dependent_prices: List[float] = Field(..., min_length=20)
    x_independent_prices: List[float] = Field(..., min_length=20)
    include_time_trend: bool = Field(False)


class BacktestRequest(BaseModel):
    y_dependent_prices: List[float] = Field(..., min_length=20)
    x_independent_prices: List[float] = Field(..., min_length=20)
    entry_z: float = Field(2.0, ge=0.5, le=4.0)
    exit_z: float = Field(0.0, ge=0.0, le=2.0)
    stop_z: float = Field(3.5, ge=2.0, le=6.0)


@app.get("/health")
def health():
    return {"status": "ok", "service": "b3-statistical-arbitrage", "version": "1.0.0"}


@app.post("/api/v1/analyze-pair")
def analyze_pair(req: PairAnalysisRequest):
    try:
        y = np.array(req.y_dependent_prices)
        x = np.array(req.x_independent_prices)

        coint = CointegrationEngine.fit(y, x, include_time_trend=req.include_time_trend)
        adf = DickeyFullerAR1Test.test(coint.residuals, has_trend=req.include_time_trend)
        ou = OrnsteinUhlenbeckEngine.estimate_from_residuals(coint.residuals, adf.phi)
        correl = FisherCorrelationEngine.analyze(x, y)

        return {
            "beta_hedge_ratio": coint.beta_hedge_ratio,
            "intercept_alpha": coint.intercept,
            "time_trend_gamma": coint.time_trend_gamma,
            "r_squared": coint.r_squared,
            "residuals_std": coint.std_residuals,
            "dickey_fuller": {
                "t_stat": adf.t_stat,
                "phi": adf.phi,
                "rho": adf.rho,
                "is_cointegrated_95": adf.is_cointegrated_95,
                "is_cointegrated_99": adf.is_cointegrated_99,
                "conclusion": adf.conclusion,
                "critical_values": adf.critical_values,
            },
            "ornstein_uhlenbeck": {
                "theta_speed": ou.theta_speed,
                "half_life_days": ou.half_life_days,
                "asymptotic_volatility": ou.asymptotic_volatility,
                "is_mean_reverting": ou.is_mean_reverting,
            },
            "correlation": {
                "pearson_r": correl.pearson_r,
                "p_value": correl.p_value,
                "ci_95": correl.ci_95,
                "ci_99": correl.ci_99,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/backtest")
def backtest_pair(req: BacktestRequest):
    try:
        y = np.array(req.y_dependent_prices)
        x = np.array(req.x_independent_prices)
        coint = CointegrationEngine.fit(y, x)
        res = PairsTradingBacktester.run(coint.residuals, entry_z=req.entry_z, exit_z=req.exit_z, stop_z=req.stop_z)

        return {
            "total_pnl": res.total_pnl,
            "sharpe_ratio": res.sharpe_ratio,
            "max_drawdown": res.max_drawdown,
            "win_rate": res.win_rate,
            "total_trades": res.total_trades,
            "profitable_trades": res.profitable_trades,
            "trades_count": len(res.trades),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
