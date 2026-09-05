Python
import streamlit as st
import sqlite3
import pandas as pd
import os

st.title("🤖 Trading Bot Dashboard")

# --- BEREICH 1: Langzeit-Bot ---
st.header("📈 Langzeit-Bot (Stündlich)")
if os.path.exists("agent_memory.db"):
    try:
        conn_long = sqlite3.connect("agent_memory.db")
        df_long = pd.read_sql("SELECT * FROM trade_history", conn_long)
        conn_long.close()
        st.dataframe(df_long)
    except Exception:
        st.info("Die Tabelle für den Langzeit-Bot existiert noch nicht.")
else:
    st.info("Keine Datenbank 'agent_memory.db' gefunden.")

# --- BEREICH 2: Daytrading-Bot ---
st.header("⚡ Daytrading-Bot (5-Minuten-Takt)")

if os.path.exists("day_memory.db"):
    try:
        conn_day = sqlite3.connect("day_memory.db")

        st.subheader("Aktive Positionen (Daytrade)")
        try:
            df_open = pd.read_sql("SELECT * FROM open_positions", conn_day)
            if not df_open.empty:
                st.dataframe(df_open)
            else:
                st.write("Aktuell keine Positionen offen.")
        except Exception:
            st.write("Tabelle 'open_positions' noch nicht vorhanden.")

        st.subheader("Daytrading-Historie")
        try:
            df_day_history = pd.read_sql("SELECT * FROM trade_history", conn_day)
            if not df_day_history.empty:
                st.dataframe(df_day_history)
            else:
                st.write("Bisher noch keine Trades ausgeführt.")
        except Exception:
            st.write("Tabelle 'trade_history' noch nicht vorhanden.")

        conn_day.close()
    except Exception as e:
        st.error(f"Fehler beim Laden der Daytrading-DB: {e}")
else:
    st.info("Die Daytrading-Datenbank wird beim nächsten Bot-Lauf initialisiert.")