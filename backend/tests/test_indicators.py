import pandas as pd

from tools import indicators


def test_sma_window():
    s = pd.Series([1, 2, 3, 4, 5], dtype=float)
    assert indicators.sma(s, 3).iloc[-1] == 4.0


def test_rsi_rising_series_is_high():
    s = pd.Series(range(1, 60), dtype=float)
    assert indicators.rsi(s).iloc[-1] > 90


def test_macd_columns():
    s = pd.Series(range(1, 80), dtype=float)
    out = indicators.macd(s)
    assert list(out.columns) == ["macd", "signal", "hist"]
