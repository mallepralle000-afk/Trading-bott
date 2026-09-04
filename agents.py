import os
import re
import time
import yfinance as yf
from google import genai
from database import get_past_learnings, get_portfolio_status, update_portfolio_after_buy, update_portfolio_after_sell, \
    log_transaction, save_prediction
from tools import get_stock_data, search_web, evaluate_risk

# RICHTIG:
import os
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))


def run_trading_cycle():
    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starte automatischen Handels-Durchlauf...")

    cash, held_stocks = get_portfolio_status()

    # Gesamtwert berechnen & Verkaufs-Logik prüfen
    total_stock_value = 0.0
    for ticker, shares, avg_price in held_stocks:
        try:
            yf_t = yf.Ticker(ticker)
            curr = yf_t.info.get('currentPrice') or yf_t.history(period="1d")['Close'].iloc[-1]
            total_stock_value += shares * curr

            # Autonome Verkaufsprüfung: Wenn Gewinn > 15% oder Verlust < -10%, verkaufen!
            profit_loss_pct = ((curr - avg_price) / avg_price) * 100
            if profit_loss_pct >= 15.0 or profit_loss_pct <= -10.0:
                print(
                    f"🚨 [Verkaufs-Alarm] {ticker}: P&L bei {profit_loss_pct:.2f}%. Verkaufe alle {shares:.2f} Anteile!")
                update_portfolio_after_sell(ticker, shares, curr)
                log_transaction("SELL", ticker, shares, curr, f"Automatischer Exit. P&L: {profit_loss_pct:.2f}%")
                return  # Nach einem Verkauf machen wir eine Pause für diesen Zyklus
        except Exception as e:
            total_stock_value += shares * avg_price

    total_portfolio_value = cash + total_stock_value
    print(f"💰 Freies Cash: {cash:.2f} € | Gesamtwert: {total_portfolio_value:.2f} €")

    # Wenn wir bereits voll investiert sind (weniger als 15% Cash), kaufen wir nichts Neues
    if cash < (total_portfolio_value * 0.15):
        print("⏳ Depot ist gut gefüllt. Keine neuen Käufe in diesem Zyklus.")
        return

    past_learnings = get_past_learnings()

    # Scout sucht nach Trends
    web_data = search_web("top performing high potential stocks market trend 2026")
    scout_prompt = f"""
    Du bist der Scout-Agent. Analysiere die Web-Daten und wähle genau EINEN Ticker.
    Bisherige Learnings: {past_learnings}
    Web-Daten: {web_data}
    Antworte klar mit dem Ticker-Symbol (z.B. AAPL, NVDA).
    """

    response = None
    for attempt in range(3):
        try:
            response = client.models.generate_content(model='gemini-3.6-flash', contents=scout_prompt)
            break
        except Exception as e:
            if "503" in str(e) and attempt < 2:
                time.sleep(5)
            else:
                return

    scout_text = response.text
    found_tickers = re.findall(r'\b[A-Z]{2,5}\b', scout_text)
    exclude_words = {"AI", "THE", "AND", "FOR", "BUY", "USD", "CEO"}
    valid_tickers = [t for t in found_tickers if t not in exclude_words]

    if not valid_tickers:
        return

    ticker_to_trade = valid_tickers[0]
    print(f"🎯 Scout wählt: {ticker_to_trade}")

    try:
        yf_ticker = yf.Ticker(ticker_to_trade)
        current_price = yf_ticker.info.get('currentPrice') or yf_ticker.info.get('regularMarketPrice')
        if not current_price:
            current_price = float(yf_ticker.history(period="1d")['Close'].iloc[-1])
    except:
        return

    proposed_amount = min(total_portfolio_value * 0.15, 1500.0)
    shares_to_buy = proposed_amount / current_price

    allowed, reason = evaluate_risk(ticker_to_trade, current_price, cash, total_portfolio_value, proposed_amount)

    if allowed:
        update_portfolio_after_buy(ticker_to_trade, shares_to_buy, current_price, proposed_amount)
        log_transaction("BUY", ticker_to_trade, shares_to_buy, current_price, reason)
        save_prediction(ticker_to_trade, f"Kauf bei {current_price} €.")
        print(f"✅ Gekauft: {ticker_to_trade}")
    else:
        log_transaction("REJECTED_BUY", ticker_to_trade, 0.0, current_price, reason)
        print(f"❌ Abgelehnt: {reason}")


if __name__ == "__main__":
    print("🤖 Autonomer Bot gestartet. Läuft im Stundentakt (Drücke STRG+C zum Beenden).")
    while True:
        try:
            run_trading_cycle()
        except Exception as e:
            print(f"Fehler im Zyklus: {e}")

        # Wache jede Stunde auf (3600 Sekunden)
        print("💤 Warte 1 Stunde bis zum nächsten Check...\n")
        time.sleep(3600)