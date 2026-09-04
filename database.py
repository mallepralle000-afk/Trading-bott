import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "agent_memory.db")


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            ticker TEXT,
            hypothesis TEXT,
            target_price REAL,
            status TEXT DEFAULT 'OPEN'
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cash REAL,
            ticker TEXT,
            shares REAL,
            average_buy_price REAL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            action TEXT,
            ticker TEXT,
            shares REAL,
            price REAL,
            total_amount REAL,
            reasoning TEXT
        )
    ''')

    cursor.execute('SELECT COUNT(*) FROM portfolio')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO portfolio (cash, ticker, shares, average_buy_price) 
            VALUES (10000.0, NULL, 0.0, 0.0)
        ''')

    conn.commit()
    conn.close()


def get_portfolio_status():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('SELECT cash FROM portfolio WHERE ticker IS NULL')
    cash_row = cursor.fetchone()
    cash = cash_row[0] if cash_row else 10000.0

    cursor.execute('SELECT ticker, shares, average_buy_price FROM portfolio WHERE ticker IS NOT NULL')
    stocks = cursor.fetchall()

    conn.close()
    return cash, stocks


def update_portfolio_after_buy(ticker: str, shares: float, price: float, total_amount: float):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('SELECT cash FROM portfolio WHERE ticker IS NULL')
    current_cash = cursor.fetchone()[0]
    new_cash = current_cash - total_amount
    cursor.execute('UPDATE portfolio SET cash = ? WHERE ticker IS NULL', (new_cash,))

    cursor.execute('SELECT id, shares, average_buy_price FROM portfolio WHERE ticker = ?', (ticker,))
    existing = cursor.fetchone()

    if existing:
        row_id, old_shares, old_avg_price = existing
        new_shares = old_shares + shares
        new_avg_price = ((old_shares * old_avg_price) + (shares * price)) / new_shares
        cursor.execute('UPDATE portfolio SET shares = ?, average_buy_price = ? WHERE id = ?',
                       (new_shares, new_avg_price, row_id))
    else:
        cursor.execute('INSERT INTO portfolio (cash, ticker, shares, average_buy_price) VALUES (0, ?, ?, ?)',
                       (ticker, shares, price))

    conn.commit()
    conn.close()


def update_portfolio_after_sell(ticker: str, shares_to_sell: float, current_price: float):
    """Verkauft Aktien, gutschreibt das Cash und entfernt die Position bei Totalverkauf."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('SELECT id, shares FROM portfolio WHERE ticker = ?', (ticker,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        return

    row_id, current_shares = existing
    sale_revenue = shares_to_sell * current_price

    # Cash erhöhen
    cursor.execute('SELECT cash FROM portfolio WHERE ticker IS NULL')
    current_cash = cursor.fetchone()[0]
    new_cash = current_cash + sale_revenue
    cursor.execute('UPDATE portfolio SET cash = ? WHERE ticker IS NULL', (new_cash,))

    if shares_to_sell >= current_shares:
        # Alles verkaufen -> Zeile löschen
        cursor.execute('DELETE FROM portfolio WHERE id = ?', (row_id,))
    else:
        # Teilverkauf -> Rest-Anzahl aktualisieren
        remaining_shares = current_shares - shares_to_sell
        cursor.execute('UPDATE portfolio SET shares = ? WHERE id = ?', (remaining_shares, row_id))

    conn.commit()
    conn.close()


def log_transaction(action: str, ticker: str, shares: float, price: float, reasoning: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_amount = shares * price

    cursor.execute('''
        INSERT INTO transactions (timestamp, action, ticker, shares, price, total_amount, reasoning)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (timestamp, action, ticker, shares, price, total_amount, reasoning))

    conn.commit()
    conn.close()


def get_transaction_history():
    """Gibt alle Transaktionen für das Dashboard zurück."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT timestamp, action, ticker, shares, price, total_amount, reasoning FROM transactions ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return rows


def save_prediction(ticker: str, hypothesis: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO predictions (timestamp, ticker, hypothesis, status)
        VALUES (?, ?, ?, 'OPEN')
    ''', (timestamp, ticker, hypothesis))
    conn.commit()
    conn.close()


def get_past_learnings():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT ticker, hypothesis, status FROM predictions ORDER BY id DESC LIMIT 5')
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "Keine historischen Vorhersagen vorhanden."

    learnings = "Bisherige Learnings / Vorhersagen:\n"
    for r in rows:
        learnings += f"- Ticker: {r[0]}, These: {r[1]}, Status: {r[2]}\n"
    return learnings


init_db()