import os
import sqlite3
from datetime import datetime
from google import genai
from day_tools import get_intraday_data

# Gemini Client initialisieren
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

TICKER = "AAPL"  # Beispiel-Aktie für den Daytrading-Bot (kannst du anpassen)
STARTING_CASH = 10000.0


def manage_day_trade():
    conn = sqlite3.connect("day_memory.db")
    cursor = conn.cursor()

    # 1. Aktuelle Intraday-Daten holen
    market_data = get_intraday_data(TICKER, interval="5m", period="1d")
    if not market_data:
        print("Keine Marktdaten verfügbar.")
        conn.close()
        return

    current_price = market_data["current_price"]
    print(f"Aktueller Kurs für {TICKER}: {current_price}")

    # 2. Prüfen, ob bereits eine Position offen ist
    cursor.execute("SELECT entry_price, shares, stop_loss, take_profit FROM open_positions WHERE ticker = ?", (TICKER,))
    position = cursor.fetchone()

    if position:
        entry_price, shares, stop_loss, take_profit = position
        print(f"Aktive Position gefunden. Einstieg: {entry_price}, SL: {stop_loss}, TP: {take_profit}")

        # Harte Exit-Regeln (Stop Loss oder Take Profit erreicht?)
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
        # 3. Wenn keine Position offen ist: Gemini nach einem Einstiegssignal fragen
        prompt = f"""
        Du bist ein aggressiver Daytrading-Agent für die Aktie {TICKER}.
        Aktuelle Intraday-Daten (5-Minuten-Kerzen):
        Preis: {current_price}
        SMA 9: {market_data['sma_9']}
        SMA 21: {market_data['sma_21']}
        Volumen: {market_data['volume']}

        Soll ich jetzt sofort LONG einsteigen? Antworte AUSSCHLIESSLICH im Format:
        BUY oder HOLD
        Gefolgt von einem kurzen Stop-Loss-Preis (ca. 1.5% unter aktuellem Kurs) und Take-Profit-Preis (ca. 3% über aktuellem Kurs).
        Beispiel für BUY: BUY | SL: 175.0 | TP: 184.0
        Beispiel für HOLD: HOLD
        """

        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt,
        )
        decision = response.text.strip()
        print(f"Gemini Entscheidung: {decision}")

        if "BUY" in decision:
            shares = int(5000 / current_price)  # Nutze die Hälfte des Kapitals
            stop_loss = current_price * 0.985
            take_profit = current_price * 1.03

            cursor.execute("""
                INSERT INTO open_positions (ticker, entry_price, shares, entry_time, stop_loss, take_profit)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (TICKER, current_price, shares, str(datetime.now()), stop_loss, take_profit))

            cursor.execute("""
                INSERT INTO trade_history (ticker, action, price, shares, timestamp, pnl)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (TICKER, "BUY", current_price, shares, str(datetime.now()), 0.0))

            conn.commit()
            print(f"Kauf ausgeführt: {shares} Aktien zu {current_price}")

    conn.close()


if __name__ == "__main__":
    manage_day_trade()