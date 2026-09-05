import streamlit as st
import sqlite3
import pandas as pd

st.title("🤖 Trading Bot Dashboard")

# --- BEREICH 1: Langzeit-Bot ---
st.header("📈 Langzeit-Bot (Stündlich)")
try:
    conn_long = sqlite3.connect("agent_memory.db")
    df_long = pd.read_sql("SELECT * FROM trade_history", conn_long)
    conn_long.close()
    st.dataframe(df_long)
except Exception as e:
    st.info("Noch keine Daten für den Langzeit-Bot vorhanden.")

---

# --- BEREICH 2: Daytrading-Bot ---
st.header("⚡ Daytrading-Bot (5-Minuten-Takt)")

try:
    conn_day = sqlite3.connect("day_memory.db")

    # Offene Positionen anzeigen
    st.subheader("Aktive Positionen (Daytrade)")
    df_open = pd.read_sql("SELECT * FROM open_positions", conn_day)
    if not df_open.empty:
        st.dataframe(df_open)
    else:
        st.write("Aktuell keine Positionen offen.")

    # Trade-Historie des Daytrading-Bots anzeigen
    st.subheader("Daytrading-Historie")
    df_day_history = pd.read_sql("SELECT * FROM trade_history", conn_day)
    if not df_day_history.empty:
        st.dataframe(df_day_history)
    else:
        st.write("Bisher noch keine Trades ausgeführt.")

    conn_day.close()
except Exception as e:
    st.info("Die Daytrading-Datenbank wird beim nächsten Bot-Lauf initialisiert.")