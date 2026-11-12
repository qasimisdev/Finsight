"""Tool schemas shown to the model, plus the dispatcher (the harness permission layer)."""
from __future__ import annotations

import os

import requests

from tools import market

TOOLS = [
    {
        "name": "get_price_history",
        "description": "Daily OHLCV price history for a ticker (for candlestick charts).",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "period": {"type": "string", "enum": ["1mo", "3mo", "6mo", "1y", "5y"]},
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "get_indicators",
        "description": "Latest SMA, RSI and MACD values for a ticker.",
        "input_schema": {
            "type": "object",
            "properties": {"symbol": {"type": "string"}, "period": {"type": "string"}},
            "required": ["symbol"],
        },
    },
    {
        "name": "get_fundamentals",
        "description": "Valuation ratios and latest income statement for a ticker.",
        "input_schema": {
            "type": "object",
            "properties": {"symbol": {"type": "string"}},
            "required": ["symbol"],
        },
    },
    {
        "name": "compare_stocks",
        "description": "Compare return and volatility of up to 5 tickers.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbols": {"type": "array", "items": {"type": "string"}},
                "period": {"type": "string"},
            },
            "required": ["symbols"],
        },
    },
    {
        "name": "run_python",
        "description": (
            "Run Python in an isolated sandbox (no network, 10s limit). Use for projections, "
            "what-if scenarios and custom calculations. Print the result."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"code": {"type": "string"}},
            "required": ["code"],
        },
    },
]


def _run_python(code: str) -> dict:
    url = os.getenv("SANDBOX_URL", "http://sandbox:9000")
    try:
        r = requests.post(f"{url}/run", json={"code": code}, timeout=20)
        return r.json()
    except Exception as exc:  # noqa: BLE001
        return {"error": f"sandbox unavailable: {exc}"}


def dispatch(name: str, args: dict) -> dict:
    allowed = {
        "get_price_history": market.get_price_history,
        "get_indicators": market.get_indicators,
        "get_fundamentals": market.get_fundamentals,
        "compare_stocks": market.compare_stocks,
        "run_python": lambda **kw: _run_python(kw["code"]),
    }
    if name not in allowed:
        return {"error": f"tool {name} is not permitted"}
    try:
        return allowed[name](**args)
    except Exception as exc:  # noqa: BLE001
        return {"error": f"{type(exc).__name__}: {exc}"}
