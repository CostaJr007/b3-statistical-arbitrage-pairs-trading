# B3 Statistical Arbitrage & Pairs Trading Engine

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests: Pytest](https://img.shields.io/badge/Tests-7%20Passed-brightgreen.svg)](https://pytest.org)

Research-grade Quantitative Pairs Trading and Statistical Arbitrage engine tailored for Brazilian equities traded on B3. Reverse-engineered and formalized from legacy trading workbooks (`excel_legacy/b3_pairs_trading_cointegration_ar1_legacy.xlsm`), modernizing Excel formulas into a modular Python engine with Docker, interactive CLI, and pytest suites.

---

## Mathematical & Statistical Foundations

### 1. Engle-Granger Two-Step Cointegration
We test for long-run equilibrium relationships between asset pair $Y_t$ (dependent) and $X_t$ (independent):

$$Y_t = \alpha + \beta X_t + \epsilon_t \quad \text{or} \quad Y_t = \alpha + \gamma t + \beta X_t + \epsilon_t$$

Where:
- $\beta$ is the cointegration hedge ratio (number of units of $X$ per unit of $Y$).
- $\alpha$ is the intercept (spread baseline level).
- $\epsilon_t$ is the residual spread series: $\epsilon_t = Y_t - (\alpha + \beta X_t)$.

### 2. Dickey-Fuller Unit Root Test on AR(1) Spread
To verify whether the spread $\epsilon_t$ is stationary ($I(0)$), we estimate the auxiliary autoregressive model:

$$\Delta \epsilon_t = \rho \epsilon_{t-1} + u_t$$

The $t$-statistic for the null hypothesis $H_0: \rho = 0$ (unit root / non-stationary) against $H_1: \rho < 0$ (mean-reverting / stationary) is:

$$t_{\text{stat}} = \frac{\hat{\rho}}{\text{SE}(\hat{\rho})}$$

The calculated $t$-statistic is evaluated against **MacKinnon (1991)** finite-sample critical value surfaces:

| Confidence Level | No Trend ($T \approx 100-250$) | With Linear Trend ($T \approx 100-250$) |
| :--- | :---: | :---: |
| **90% Confidence** ($\alpha = 0.10$) | $-2.57$ | $-3.13$ |
| **95% Confidence** ($\alpha = 0.05$) | $-2.88$ | $-3.43$ |
| **99% Confidence** ($\alpha = 0.01$) | $-3.46$ | $-3.99$ |

### 3. Ornstein-Uhlenbeck (OU) Mean-Reversion Dynamics
The stationary spread is modeled as a continuous-time Ornstein-Uhlenbeck process:

$$dX_t = \theta (\mu - X_t) dt + \sigma dW_t$$

Discretizing via Euler-Maruyama over step $\Delta t$:

$$X_t = a + b X_{t-1} + \eta_t, \quad b = e^{-\theta \Delta t}$$

From which we derive:
- **Speed of mean reversion**: $\theta = -\frac{\ln(b)}{\Delta t}$
- **Long-term equilibrium mean**: $\mu = \frac{a}{1 - b}$
- **Equilibrium variance**: $\sigma_{eq}^2 = \frac{\text{Var}(\eta)}{1 - b^2}$
- **Empirical Half-Life**:
  $$t_{1/2} = \frac{\ln(2)}{\theta}$$
  *(The expected time for the spread deviation to decay by 50% toward equilibrium).*

### 4. Fisher Z-Transformation & Correlation Inference
For rolling Pearson correlation $r_{xy}$, we perform the variance-stabilizing Fisher transformation:

$$z = \frac{1}{2} \ln \left( \frac{1 + r}{1 - r} \right) = \text{arctanh}(r)$$

With standard error $\text{SE}(z) = \frac{1}{\sqrt{N - 3}}$, allowing rigorous computation of:
- Two-tailed Student-$t$ significance $p$-values against $H_0: \rho = 0$.
- Asymmetric 95% and 99% confidence intervals: $[\tanh(z - z_{\alpha/2} \text{SE}), \tanh(z + z_{\alpha/2} \text{SE})]$.

### 5. Z-Score Mean-Reversion Execution Model
Normalized spread tracking:

$$Z_t = \frac{\epsilon_t - \mu_{\epsilon}}{\sigma_{\epsilon}}$$

- **Long Spread Entry**: $Z_t \le -Z_{\text{entry}}$ (Buy $Y$, Short $\beta X$).
- **Short Spread Entry**: $Z_t \ge +Z_{\text{entry}}$ (Short $Y$, Buy $\beta X$).
- **Exit / Take-Profit**: $|Z_t| \le Z_{\text{exit}}$ (Close positions at equilibrium).
- **Stop-Loss Protection**: $|Z_t| \ge Z_{\text{stop}}$.

Performance analytics computed:
- Cumulative & Period Return
- Maximum Drawdown (MDD)
- Annualized Sharpe Ratio (252-day basis): $\text{Sharpe} = \sqrt{252} \cdot \frac{\bar{R}_p}{\sigma_p}$
- Win Rate (%) and Total Closed Round-Trip Trades

---

## Architecture & Project Layout

```
b3-statistical-arbitrage-pairs-trading/
├── stat_arb/
│   ├── models/
│   │   ├── cointegration.py       # Engle-Granger OLS regression with/without trend
│   │   ├── dickey_fuller_ar1.py   # AR(1) unit root test with MacKinnon critical values
│   │   ├── ornstein_uhlenbeck.py  # OU drift, diffusion, theta, and half-life
│   │   ├── fisher_correlation.py  # Fisher z-transform and Student-t confidence intervals
│   │   └── backtest.py            # Z-Score execution, PnL tracking, Sharpe, MDD
│   ├── connectors/
│   │   └── data_loader.py         # Multi-asset Excel loader & synthetic pair generator
│   ├── api/
│   │   └── server.py              # FastAPI service with Swagger OpenAPI specs
│   └── cli.py                     # Typer + Rich interactive terminal interface
├── vba_legacy/                    # Reverse-engineered VBA modules from Excel
│   ├── Chart_Scaler_Module1.bas
│   ├── Chart_Scaler_Module2.bas
│   └── Chart_Scaler_Module3.bas
├── excel_legacy/                  # Original Excel workbook reference
│   └── b3_pairs_trading_cointegration_ar1_legacy.xlsm   # Sanitized legacy workbook (metadata stripped)
├── tests/
│   ├── test_models.py             # Quantitative mathematical assertions
│   └── test_api.py                # REST API endpoint tests
├── Dockerfile
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## Quick Start

### 1. Installation

```bash
git clone https://github.com/CostaJr007/b3-statistical-arbitrage-pairs-trading.git
cd b3-statistical-arbitrage-pairs-trading
pip install -r requirements.txt
```

### 2. Run Test Suite

```bash
python -m pytest tests/ -v
```

Expected output:
```
tests/test_api.py::test_health_endpoint PASSED                           [ 14%]
tests/test_api.py::test_analyze_pair_endpoint PASSED                     [ 28%]
tests/test_api.py::test_backtest_endpoint PASSED                         [ 42%]
tests/test_models.py::test_cointegration_ols PASSED                      [ 57%]
tests/test_models.py::test_dickey_fuller_ar1 PASSED                      [ 71%]
tests/test_models.py::test_ornstein_uhlenbeck_halflife PASSED            [ 85%]
tests/test_models.py::test_fisher_correlation PASSED                     [100%]
======= 7 passed in 1.68s =======
```

### 3. Interactive CLI Commands

```bash
# Analyze a synthetic mean-reverting pair (PETR4 vs VALE3)
python -m stat_arb.cli analyze --ticker-y PETR4 --ticker-x VALE3 --periods 252

# Run full Z-score backtest with PnL & Sharpe metrics
python -m stat_arb.cli backtest --ticker-y PETR4 --ticker-x VALE3 --entry-z 2.0 --exit-z 0.5
```

### 4. Launch FastAPI REST Server

```bash
python -m uvicorn stat_arb.api.server:app --host 0.0.0.0 --port 8000 --reload
```

Interactive documentation is available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

#### Example REST API Request:
```bash
curl -X POST "http://localhost:8000/analyze" \
     -H "Content-Type: application/json" \
     -d '{
       "series_y": [28.5, 28.2, 28.9, 29.1, 28.7, 28.4],
       "series_x": [65.2, 64.8, 66.0, 66.5, 65.9, 65.1],
       "include_trend": false
     }'
```

---

## Docker Deployment

```bash
# Build image
docker build -t b3-statistical-arbitrage .

# Run container
docker run -d -p 8000:8000 --name stat-arb b3-statistical-arbitrage
```

---

## Reverse Engineering Legacy VBA
The original spreadsheet contained custom VBA chart scalers and RTD dynamic updates:
- Extracted and archived in [`vba_legacy/`](vba_legacy/).
- Replaced with vectorised NumPy/SciPy linear algebra and an automated FastAPI service.

---

## License
MIT License. Developed by Adeilson Costa ([CostaJr007](https://github.com/CostaJr007)).
