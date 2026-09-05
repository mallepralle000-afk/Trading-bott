import sqlite3


def init_db():
    conn = sqlite3.connect("day_memory.db")
    cursor = conn.cursor()

    # Tabelle für offene Positionen
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS open_positions (
            ticker TEXT PRIMARY KEY,
            entry_price REAL,
            shares INTEGER,
            entry_time TEXT,
            stop_loss REAL,
            take_profit REAL
        )
    """)

    # Tabelle für die Historie aller Trades
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trade_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT,
            action TEXT,
            price REAL,
            shares INTEGER,
            timestamp TEXT,
            pnl REAL
        )
    """)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()