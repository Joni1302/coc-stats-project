from flask import Flask, render_template
import pandas as pd
import os
import sqlite3 
from datetime import datetime
app = Flask(__name__)
# from src.config import SECRET_KEY  <-- Wenn du soweit bist
# app.config['SECRET_KEY'] = SECRET_KEY

app = Flask(__name__)

@app.context_processor
def inject_navbar_stats():
    """
    Liest die wichtigsten Spieler-Infos aus der CSV für die Navbar.
    Diese Funktion macht die Variable 'navbar_data' in ALLEN Templates verfügbar.
    """
    csv_path = os.path.join("data", "player_info.csv")
    
    # Standardwerte, falls die Datei noch nicht existiert
    default_data = {
        "name": "Chief",
        "town_hall": "??",
        "trophies": "0"
    }

    if os.path.exists(csv_path):
        try:
            # Wir lesen nur die erste Zeile, da es nur einen Spieler gibt
            df = pd.read_csv(csv_path)
            if not df.empty:
                player = df.iloc[0]
                return dict(navbar_data={
                    "name": player['name'],
                    "town_hall": player['town_hall'],
                    "trophies": player['trophies']
                })
        except Exception as e:
            print(f"Fehler beim Laden der Navbar-Daten: {e}")
    
    return dict(navbar_data=default_data)

def get_db_connection():
    # Wir stellen sicher, dass wir vom richtigen Pfad aus auf die DB zugreifen,
    # egal von wo die App gestartet wird.
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'coc_history.db')
    conn = sqlite3.connect(db_path)
    # Stellt sicher, dass wir Spalten als Namen abrufen können
    conn.row_factory = sqlite3.Row 
    return conn

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/stats")
def stats():
    conn = get_db_connection()
    
    # KORREKTUR: Der Tabellenname muss 'player_stats' lauten!
    historical_data = conn.execute(
        'SELECT timestamp, trophies FROM player_stats ORDER BY timestamp DESC'
    ).fetchall()
    
    conn.close()

    trophy_history = []
    for row in historical_data:
        
        # KORREKTUR: Parsing des ISO-Strings mit strptime anstelle von fromtimestamp
        dt_object = datetime.strptime(row['timestamp'], '%Y-%m-%dT%H:%M:%S.%f')
        date_str = dt_object.strftime('%d.%m.%Y %H:%M')
        
        trophy_history.append({
            'date': date_str,
            'trophies': row['trophies'] # Korrekter Spaltenname
        })
        
    return render_template("stats.html", trophy_history=trophy_history)

@app.route("/clan")
def clan():
    """Zeigt die Clan-Übersicht UND die Mitgliederliste."""
    
    # 1. Clan Info laden (wie bisher)
    csv_path_info = os.path.join("data", "clan_info.csv")
    clan_data = {}
    if os.path.exists(csv_path_info):
        try:
            df_info = pd.read_csv(csv_path_info)
            if not df_info.empty:
                clan_data = df_info.iloc[0].to_dict()
                if 'description' in clan_data and isinstance(clan_data['description'], str):
                     clan_data['description'] = clan_data['description'].replace('\n', '<br>')
        except Exception as e:
            print(f"Fehler beim Laden der Clan-Info: {e}")

    # 2. NEU: Mitglieder laden und sortieren
    csv_path_members = os.path.join("data", "clan_members.csv")
    members_data = []
    if os.path.exists(csv_path_members):
        try:
            df_members = pd.read_csv(csv_path_members)
            # Wir sortieren nach Trophäen absteigend (Höchste zuerst)
            df_members = df_members.sort_values(by='trophies', ascending=False)
            members_data = df_members.to_dict(orient='records')
        except Exception as e:
            print(f"Fehler beim Laden der Mitglieder: {e}")

    # Wir übergeben BEIDES an das Template: clan und members
    return render_template("clan.html", clan=clan_data, members=members_data)

@app.route("/blog")
def blog():
    """Zeigt die Blog/News-Seite."""
    # Hier könnten später echte Blog-Einträge aus einer Datenbank oder JSON-Datei kommen.
    # Für jetzt nutzen wir statische Platzhalter-Daten.
    posts = [
        {
            "title": "Dashboard V1.0 Release",
            "date": "04.12.2025",
            "category": "Update",
            "content": "Willkommen auf Joni's CoC Dashboard! Die erste Version ist live. Wir ziehen jetzt echte Daten über die Supercell API und speichern die Historie.",
            "author": "Joni"
        },
        {
            "title": "Zenit Clan erreicht Level 16",
            "date": "01.12.2025",
            "category": "Clan",
            "content": "Ein großer Meilenstein für unseren Clan! Dank der harten Arbeit in den Clankriegen haben wir endlich das nächste Level erreicht.",
            "author": "Leader"
        }
    ]
    return render_template("blog.html", posts=posts)

if __name__ == "__main__":
    app.run(debug=True)