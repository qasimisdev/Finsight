"""Market data tools. Each function returns JSON-serialisable data plus its source."""
from __future__ import annotations

import yfinance as yf

from tools import indicators

SOURCE = "Yahoo Finance via yfinance"


def get_price_history(symbol: str, period: str = "1y") -> dict:
    hist = yf.Ticker(symbol).history(period=period)
    if hist.empty:
        return {"error": f"No data for {symbol}", "source": SOURCE}
    rows = [
        {
            "date": idx.strftime("%Y-%m-%d"),
            "open": round(r.Open, 2),
            "high": round(r.High, 2),
            "low": round(r.Low, 2),
            "close": round(r.Close, 2),
            "volume": int(r.Volume),
        }
        for idx, r in hist.iterrows()
    ]
    return {"symbol": symbol.upper(), "period": period, "rows": rows, "source": SOURCE}


def get_indicators(symbol: str, period: str = "1y") -> dict:
    hist = yf.Ticker(symbol).history(period=period)
    if hist.empty:
        return {"error": f"No data for {symbol}", "source": SOURCE}
    close = hist["Close"]
    m = indicators.macd(close).iloc[-1]
    last = {
        "close": round(float(close.iloc[-1]), 2),
        "sma_20": round(float(indicators.sma(close, 20).iloc[-1]), 2),
        "sma_50": round(float(indicators.sma(close, 50).iloc[-1]), 2),
        "rsi_14": round(float(indicators.rsi(close).iloc[-1]), 1),
        "macd": round(float(m["macd"]), 3),
        "macd_signal": round(float(m["signal"]), 3),
    }
    return {
        "symbol": symbol.upper(),
        "latest": last,
        "assumptions": "SMA 20/50, RSI 14, MACD 12/26/9 on daily closes",
        "source": SOURCE,
    }


def get_fundamentals(symbol: str) -> dict:
    t = yf.Ticker(symbol)
    info = t.info or {}
    keys = [
        "longName", "sector", "marketCap", "trailingPE", "forwardPE", "priceToBook",
        "dividendYield", "profitMargins", "returnOnEquity", "totalRevenue", "trailingEps",
    ]
    out = {k: info.get(k) for k in keys}
    try:
        stmt = t.income_stmt
        out["income_statement_latest"] = {
            str(k): (None if v != v else float(v)) for k, v in stmt.iloc[:, 0].head(8).items()
        }
    except Exception:  # noqa: BLE001
        out["income_statement_latest"] = None
    return {"symbol": symbol.upper(), "fundamentals": out, "source": SOURCE}


def compare_stocks(symbols: list[str], period: str = "1y") -> dict:
    result = {}
    for s in symbols[:5]:
        hist = yf.Ticker(s).history(period=period)
        if hist.empty:
            result[s.upper()] = {"error": "no data"}
            continue
        close = hist["Close"]
        daily = close.pct_change().dropna()
        result[s.upper()] = {
            "return_pct": round(float((close.iloc[-1] / close.iloc[0] - 1) * 100), 2),
            "volatility_pct": round(float(daily.std() * (252**0.5) * 100), 2),
        }
    return {"period": period, "comparison": result, "source": SOURCE}
