from flask import Flask, render_template
import pandas as pd 
import os

app = Flask(__name__)
# from src.config import SECRET_KEY  <-- Wenn du soweit bist
# app.config['SECRET_KEY'] = SECRET_KEY

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

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/stats")
def stats():
    # Hier werden wir später die Daten aus der DB holen!
    return render_template("stats.html")

if __name__ == "__main__":
    app.run(debug=True)