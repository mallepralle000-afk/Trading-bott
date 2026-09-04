import streamlit as st
import pandas as pd
import yfinance as yf
from database import get_portfolio_status, get_transaction_history

st.set_page_config(page_title="Autonomous Trading Dashboard", page_icon="📈", layout="wide")


# --- PASSWORT-SCHUTZ ---
def check_password():
    """Gibt True zurück, wenn das Passwort korrekt eingegeben wurde."""

    def password_entered():
        if st.session_state["password"] == "geheim123":  # Ändere hier dein Passwort!
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Passwort nicht im State behalten
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Passwort eingeben:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Passwort eingeben:", type="password", on_change=password_entered, key="password")
        st.error("😕 Falsches Passwort")
        return False
    else:
        return True


if not check_password():
    st.stop()

# --- DASHBOARD HAUPTTEIL ---
st.title("🤖 Autonomer Paper-Trading Bot")
st.markdown("Echtzeit-Überwachung des virtuellen 10.000 € Portfolios.")

# Daten aus DB laden
cash, held_stocks = get_portfolio_status()

# Live-Werte berechnen
total_stock_value = 0.0
portfolio_details = []

for ticker, shares, avg_price in held_stocks:
    try:
        yf_t = yf.Ticker(ticker)
        curr_price = yf_t.info.get('currentPrice') or yf_t.history(period="1d")['Close'].iloc[-1]
    except:
        curr_price = avg_price

    current_val = shares * curr_price
    total_stock_value += current_val
    profit_loss = ((curr_price - avg_price) / avg_price) * 100

    portfolio_details.append({
        "Ticker": ticker,
        "Anteile": round(shares, 4),
        "Ø Kaufpreis (€)": round(avg_price, 2),
        "Live-Kurs (€)": round(curr_price, 2),
        "Gesamtwert (€)": round(current_val, 2),
        "Gewinn/Verlust (%)": f"{profit_loss:+.2f}%"
    })

total_portfolio_value = cash + total_stock_value

# Metriken anzeigen
col1, col2, col3 = st.columns(3)
col1.metric("Gesamtwert des Depots", f"{total_portfolio_value:,.2f} €", f"{(total_portfolio_value - 10000):+.2f} €")
col2.metric("Freies Cash", f"{cash:,.2f} €")
col3.metric("Aktienwert", f"{total_stock_value:,.2f} €")

st.divider()

# Gehaltene Aktien Tabelle
st.subheader("📦 Aktuelles Aktien-Portfolio")
if portfolio_details:
    st.dataframe(pd.DataFrame(portfolio_details), use_container_width=True)
else:
    st.info("Aktuell keine Aktien im Depot gehalten.")

# Transaktions-Historie (Kassenbuch)
st.subheader("📜 Kassenbuch & Transaktionen")
transactions = get_transaction_history()
if transactions:
    tx_list = []
    for t in transactions:
        tx_list.append({
            "Zeitpunkt": t[0],
            "Aktion": t[1],
            "Ticker": t[2],
            "Anteile": t[3],
            "Preis (€)": t[4],
            "Summe (€)": t[5],
            "Begründung": t[6]
        })
    st.dataframe(pd.DataFrame(tx_list), use_container_width=True)
else:
    st.write("Noch keine Transaktionen aufgezeichnet.")

# Button zum manuellen Aktualisieren der Ansicht
if st.button("🔄 Ansicht aktualisieren"):
    st.rerun()