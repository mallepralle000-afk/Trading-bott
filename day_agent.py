import os
import sqlite3
from datetime import datetime
from day_tools import get_intraday_data

TICKER = "AAPL"
STARTING_CASH = 10000.0


def manage_day_trade():
    conn = sqlite3.connect("day_memory.db")
    cursor = conn.cursor()

    # 1. Intraday-Daten holen
    market_data = get_intraday_data(TICKER, interval="5m", period="1d")
    if not market_data:
        print("Keine Marktdaten verfügbar.")
        conn.close()
        return

    current_price = market_data["current_price"]
    sma_9 = market_data["sma_9"]
    sma_21 = market_data["sma_21"]

    print(f"Aktueller Kurs für {TICKER}: {current_price} | SMA 9: {sma_9} | SMA 21: {sma_21}")

    # 2. Prüfen, ob bereits eine Position offen ist
    cursor.execute("SELECT entry_price, shares, stop_loss, take_profit FROM open_positions WHERE ticker = ?", (TICKER,))
    position = cursor.fetchone()

    if position:
        entry_price, shares, stop_loss, take_profit = position
        print(f"Aktive Position gefunden. Einstieg: {entry_price}, SL: {stop_loss}, TP: {take_profit}")

        # Stop Loss oder Take Profit erreicht?
        if current_price <= stop_loss or current_price >= take_profit:
            pnl = (current_price - entry_price) * shares
            print(f"Verkauf ausgelöst! PnL: {pnl}")

            cursor.execute("DELETE FROM open_positions WHERE ticker = ?", (TICKER,))
            cursor.execute("""
                INSERT INTO trade_history (ticker, action, price, shares, timestamp, pnl)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (TICKER, "SELL", current_price, shares, str(datetime.now()), pnl))
            conn.commit()
        else:
            print("Halte Position. Weder Stop-Loss noch Take-Profit erreicht.")

    else:
        # 3. Mathematisches Momentum-Signal (SMA 9 kreuzt SMA 21 nach oben = BUY)
        if sma_9 > sma_21:
            shares = int(5000 / current_price)
            stop_loss = current_price * 0.985  # 1.5% Stop Loss
            take_profit = current_price * 1.03  # 3% Take Profit

            cursor.execute("""
                INSERT INTO open_positions (ticker, entry_price, shares, entry_time, stop_loss, take_profit)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (TICKER, current_price, shares, str(datetime.now()), stop_loss, take_profit))

            cursor.execute("""
                INSERT INTO trade_history (ticker, action, price, shares, timestamp, pnl)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (TICKER, "BUY", current_price, shares, str(datetime.now()), 0.0))

            conn.commit()
            print(f"Kauf ausgeführt (SMA-Crossover): {shares} Aktien zu {current_price}")
        else:
            print("Kein Signal (SMA 9 unter SMA 21). Halte still.")

    conn.close()


if __name__ == "__main__":
    manage_day_trade()