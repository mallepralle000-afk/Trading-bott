import yfinance as yf
from ddgs import DDGS


def get_stock_data(ticker: str) -> str:
    """Holt fundamentale und historische Daten zu einer Aktie via yfinance."""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="6mo")
        info = stock.info

        current_price = info.get('currentPrice', 'Unbekannt')
        pe_ratio = info.get('trailingPE', 'Unbekannt')
        div_yield = info.get('dividendYield', 0)
        if div_yield:
            div_yield = round(div_yield * 100, 2)

        summary = (
            f"Aktie: {ticker}\n"
            f"Aktueller Preis: {current_price}\n"
            f"KGV (PE Ratio): {pe_ratio}\n"
            f"Dividendenrendite: {div_yield}%\n"
            f"Kursverlauf der letzten 6 Monate (Start vs Ende): "
            f"{hist['Close'].iloc[0]:.2f} -> {hist['Close'].iloc[-1]:.2f}\n"
        )
        return summary
    except Exception as e:
        return f"Fehler beim Abrufen der Daten für {ticker}: {str(e)}"


def search_web(query: str) -> str:
    """Durchsucht das Web mit Fehlerbehandlung, damit es nicht hängen bleibt."""
    try:
        results_text = ""
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            for r in results:
                results_text += f"Titel: {r.get('title')}\nInhalt: {r.get('body')}\nURL: {r.get('href')}\n\n"
        return results_text if results_text else "Keine aktuellen Web-Ergebnisse gefunden."
    except Exception as e:
        return f"Websuche temporär nicht erreichbar (Fehler: {str(e)}). Nutze dein internes Wissen."


def evaluate_risk(ticker: str, current_price: float, cash: float, total_portfolio_value: float,
                  proposed_amount: float) -> tuple[bool, str]:
    """
    Die Risiko-Polizei prüft jeden Trade anhand harter Regeln.
    Gibt ein Tuple zurück: (Erlaubt: True/False, Begründung)
    """
    # Regel 1: Keine Pennystocks (Preis unter 5.00)
    if current_price < 5.0:
        return False, f"ABGELEHNT: {ticker} ist ein Pennystock (Kurs: {current_price} < 5.00)."

    # Regel 2: Genug Cash vorhanden?
    if proposed_amount > cash:
        return False, f"ABGELEHNT: Nicht genug Cash. Benötigt: {proposed_amount} €, Verfügbar: {cash} €."

    # Regel 3: Max 20% des Gesamtdepots in eine einzige Aktie
    max_allowed_investment = total_portfolio_value * 0.20
    if proposed_amount > max_allowed_investment:
        return False, f"ABGELEHNT: Position zu groß. Max. 20% erlaubt ({max_allowed_investment:.2f} €), gewollt waren {proposed_amount:.2f} €."

    return True, "GENEHMIGT: Alle Risiko-Guardrails erfolgreich passiert."