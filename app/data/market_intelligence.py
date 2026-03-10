from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
import yfinance as yf


@dataclass
class MarketIntelligence:
    def analyze_equity(self, ticker: str, period: str = "1mo") -> dict[str, Any]:
        hist = yf.Ticker(ticker).history(period=period)
        if hist.empty:
            return {"ticker": ticker, "status": "no_data"}
        close = hist["Close"]
        return {
            "ticker": ticker,
            "status": "ok",
            "last_close": float(close.iloc[-1]),
            "mean_close": float(close.mean()),
            "pct_change": float((close.iloc[-1] - close.iloc[0]) / close.iloc[0]),
        }

    def summarize_market_frame(self, frame: pd.DataFrame) -> dict[str, Any]:
        return {
            "rows": int(len(frame)),
            "columns": frame.columns.tolist(),
            "numeric_summary": frame.describe(include="all").fillna(0).to_dict(),
        }

    def discover_trends(self, series: pd.Series, window: int = 7) -> dict[str, Any]:
        rolling = series.rolling(window=window).mean().dropna()
        return {"window": window, "current": float(rolling.iloc[-1]) if not rolling.empty else 0.0}
