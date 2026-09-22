# Legacy Workbook Provenance

The original macro-enabled workbook (`L_S_aluno_testeAR1.xlsm`) was **reverse-engineered and then removed from version control**.
Binaries with VBA macros are intentionally not shipped: they bloat clones, trigger
security warnings, and redistribute third-party material. The audited logic lives on
as extracted text in `vba_legacy/` and as the Python engine in `stat_arb/`.

| Item | Detail |
|---|---|
| Original file | `L_S_aluno_testeAR1.xlsm` |
| Sanitized copy (removed) | `excel_legacy/b3_pairs_trading_cointegration_ar1_legacy.xlsm` |
| Sheets | `Banco de Dados` (B3 prices, no formulas), `Resumo` (2 broken `#REF!` cells), `Coint-Temp-2` (engine, ~13k formulas, pair ITSA4 x ITUB4) |
| VBA | Chart-axis scalers only (`Chart_Scaler_Module1/2/3.bas`) — no math in VBA |

## Formula map (`Coint-Temp-2`)

- **Hedge OLS:** array `LINEST` → `[gamma, beta, alpha]`; Python `cointegration.py` reproduces bit-for-bit.
- **Dickey-Fuller AR(1):** `SLOPE/INTERCEPT` + t-stat; Python uses textbook through-origin OLS (divergence < 0.3%, same conclusion).
- **OU half-life:** workbook used `2/theta` (wrong by 2/ln2); Python correctly uses `ln(2)/theta`.
- **Correlation/Fisher:** workbook uses **log-returns**; Python `analyze()` takes prices and derives log-returns internally (levels `r` kept only as a labelled spurious diagnostic).
- **Bands:** 2.58 sigma; **PnL:** nominal only (no Sharpe in workbook — Python adds annualized Sharpe, max drawdown).

## Runtime note

`B3PairsDataLoader.load_from_excel(path)` accepts any user-supplied workbook with a
`Banco de Dados` sheet. Without a file, the CLI/API run on OU-based synthetic pairs.
No legacy binary is required to run or test this repo.
