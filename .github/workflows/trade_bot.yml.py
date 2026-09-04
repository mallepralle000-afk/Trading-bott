name: Autonomous Trading Bot

on:
  schedule:
    - cron: '0 * * * *' # Läuft automatisch jede volle Stunde
  workflow_dispatch: # Erlaubt den manuellen Start per Klick direkt auf GitHub

jobs:
  run-bot:
    runs-on: ubuntu-latest
    permissions:
      contents: write # Erlaubt dem Bot, die aktualisierte Datenbank in dein Repository zurückzuspeichern
    steps:
      - name: Code herunterladen
        uses: actions/checkout@v4

      - name: Python einrichten
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Abhängigkeiten installieren
        run: |
          pip install google-genai yfinance duckduckgo_search pandas

      - name: Bot ausführen
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: |
          python agents.py

      - name: Datenbank-Stand in GitHub sichern
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "github-actions[bot]@users.noreply.github.com"
          git add agent_memory.db
          git diff --staged --quiet || git commit -m "Auto-update database after trade cycle"
          git push