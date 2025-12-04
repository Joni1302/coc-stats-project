import os
from dotenv import load_dotenv

# Lädt die Variablen aus der .env Datei
load_dotenv() 

# --- COC AUTHENTIFIZIERUNG ---
COC_EMAIL = os.getenv("COC_EMAIL")
if not COC_EMAIL:
    # Optionaler Fallback für Token-Login (falls du das nutzt)
    if not os.getenv("COC_API_TOKEN"):
         raise ValueError("COC_EMAIL (oder Token) fehlt in der .env Datei.")

COC_PASSWORD = os.getenv("COC_PASSWORD")
# API Token Check
COC_TOKEN = os.getenv("COC_API_TOKEN")

# --- PERSÖNLICHE KONFIGURATION ---
MY_PLAYER_TAG = os.getenv("MY_PLAYER_TAG")
if not MY_PLAYER_TAG:
    raise ValueError("MY_PLAYER_TAG fehlt in der .env Datei.")

# HINWEIS: MY_CLAN_TAG wurde entfernt, da wir diesen dynamisch laden!