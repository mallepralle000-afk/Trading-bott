import yfinance as yf
import pandas as pd
from datetime import datetime


def get_intraday_data(ticker_symbol, interval="5m", period="5d"):
    """
    Holt Intraday-Kerzen (Candles) von Yahoo Finance.
    Erlaubte Intervalle für Daytrading: '1m', '5m', '15m'.
    """
    stock = yf.Ticker(ticker_symbol)
    df = stock.history(period=period, interval=interval)

    if df.empty:
        return None

    # Berechne einfache gleitende Durchschnitte (EMA/SMA) und RSI für den Trend
    df['SMA_9'] = df['Close'].rolling(window=9).mean()
    df['SMA_21'] = df['Close'].rolling(window=21).mean()

    # Letzte bekannte Kerze extrahieren
    latest = df.iloc[-1]
    prev = df.iloc[-2]

    data_summary = {
        "ticker": ticker_symbol,
        "current_price": float(latest['Close']),
        "volume": int(latest['Volume']),
        "sma_9": float(latest['SMA_9']),
        "sma_21": float(latest['SMA_21']),
        "timestamp": str(df.index[-1])
    }
    return data_summary