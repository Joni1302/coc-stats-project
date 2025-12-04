import os
from dotenv import load_dotenv

# Lädt die Variablen aus der .env Datei
load_dotenv() 

# --- COC AUTHENTIFIZIERUNG ---
# Wichtig: Wir prüfen, ob die Variablen existieren, andernfalls wird ein Fehler ausgelöst.
COC_EMAIL = os.getenv("COC_EMAIL")
if not COC_EMAIL:
    raise ValueError("COC_EMAIL fehlt in der .env Datei.")

COC_PASSWORD = os.getenv("COC_PASSWORD")
if not COC_PASSWORD:
    raise ValueError("COC_PASSWORD fehlt in der .env Datei.")

# --- PERSÖNLICHE KONFIGURATION ---
# Wir holen den Spieler-Tag
MY_PLAYER_TAG = os.getenv("MY_PLAYER_TAG")
if not MY_PLAYER_TAG:
    raise ValueError("MY_PLAYER_TAG fehlt in der .env Datei.")