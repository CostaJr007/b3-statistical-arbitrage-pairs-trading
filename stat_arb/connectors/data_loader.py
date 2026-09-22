"""Data loader for B3 Stock Data from Excel or Synthetic Generators."""

from __future__ import annotations

import os
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import openpyxl


class B3PairsDataLoader:
    """Extracts historical B3 price series from the legacy Excel spreadsheet or generates synthetic series."""

    @staticmethod
    def load_from_excel(filepath: str, max_rows: Optional[int] = None) -> pd.DataFrame:
        """Extract prices from 'Banco de Dados' sheet of b3_pairs_trading_cointegration_ar1_legacy.xlsm."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Spreadsheet not found: {filepath}")

        wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
        ws = wb["Banco de Dados"]

        rows = list(ws.iter_rows(values_only=True))
        wb.close()

        header_row_idx = 2  # Row 3 in 1-based indexing (Data, ABEV3, ...)
        headers = rows[header_row_idx]
        data = rows[header_row_idx + 1: (header_row_idx + 1 + max_rows) if max_rows else len(rows)]

        df = pd.DataFrame(data, columns=headers)
        df = df.dropna(how="all")
        if "Data" in df.columns:
            df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
            df = df.sort_values("Data").reset_index(drop=True)

        return df

    @staticmethod
    def generate_cointegrated_pair(
        n: int = 250,
        beta: float = 1.35,
        alpha: float = 4.20,
        theta: float = 0.15,
        noise_std: float = 0.50,
        seed: int = 42,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Generate two synthetic cointegrated time series using Ornstein-Uhlenbeck residuals."""
        np.random.seed(seed)
        # Independent asset X_t as geometric random walk
        drift = 0.0002
        vol_x = 0.015
        ret_x = np.random.normal(drift, vol_x, n)
        x = 50.0 * np.exp(np.cumsum(ret_x))

        # Stationary OU spread epsilon_t: dEps = -theta * Eps dt + sigma * dW
        eps = np.zeros(n)
        for t in range(1, n):
            eps[t] = eps[t - 1] - theta * eps[t - 1] + np.random.normal(0, noise_std)

        # Dependent asset Y_t = alpha + beta * X_t + eps_t
        y = alpha + beta * x + eps
        return y, x
