from flask import Flask, render_template
import pandas as pd
import os
import sqlite3 
import json
from datetime import datetime

app = Flask(__name__)

# --- KONFIGURATION FÜR KATEGORIEN ---
DARK_TROOPS_LIST = [
    'Minion', 'Hog Rider', 'Valkyrie', 'Golem', 'Witch', 'Lava Hound', 
    'Bowler', 'Ice Golem', 'Headhunter', 'Apprentice Warden', 'Druid', 'Furnace'
]

SIEGE_MACHINES_LIST = [
    'Wall Wrecker', 'Battle Blimp', 'Stone Slammer', 'Siege Barracks', 
    'Log Launcher', 'Flame Flinger', 'Battle Drill', 'Troop Launcher'
]

SUPER_TROOPS_KEYWORDS = ['Super ', 'Sneaky ', 'Rocket ', 'Inferno ', 'Ice Hound']

@app.context_processor
def inject_navbar_stats():
    csv_path = os.path.join("data", "player_info.csv")
    default_data = {"name": "Chief", "town_hall": "??", "trophies": "0"}
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            if not df.empty:
                player = df.iloc[0]
                return dict(navbar_data={
                    "name": player['name'],
                    "town_hall": player['town_hall'],
                    "trophies": player['trophies']
                })
        except: pass
    return dict(navbar_data=default_data)

def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'coc_history.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row 
    return conn

@app.route("/")
def index():
    return render_template("index.html")

def get_asset_url(name, category):
    s_name = str(name).replace(" ", "_").replace(".", "") 
    filename = f"{s_name}.png"
    
    folder_map = {
        "heroes": "heroes",
        "pets": "pets",
        "siege": "siege_machines",
        "super": "super_troops",
        "dark": "dark_troops",
        "spells": "spells",
        "elixir": "troops",
        "town_hall": "town_hall"
    }
    
    folder = folder_map.get(category, "troops")
    
    if category == "town_hall":
        clean_th = str(name).replace(" ", "_")
        filename = f"Town_Hall_{clean_th}.png"

    return f"/static/assets/{folder}/{filename}"

@app.route("/stats")
def stats():
    # 1. Historie laden
    conn = get_db_connection()
    try:
        historical_data = conn.execute('SELECT timestamp, trophies FROM player_stats ORDER BY timestamp ASC').fetchall()
    except sqlite3.OperationalError:
        historical_data = [] 
    finally:
        conn.close()
    
    chart_labels = []
    chart_values = []
    for row in historical_data:
        try:
            dt = datetime.strptime(row['timestamp'], '%Y-%m-%dT%H:%M:%S.%f')
            chart_labels.append(dt.strftime('%d.%m.'))
            chart_values.append(row['trophies'])
        except: continue

    # 2. Player Info & Rathaus Bild laden
    # Default Werte (verhindert Fehler, wenn CSV fehlt)
    player_info = {
        "name": "Chief", "tag": "#...", "town_hall": 1, 
        "trophies": 0, "exp_level": 0, "war_stars": 0, 
        "attack_wins": 0, "role": "member"
    }
    th_image = ""
    
    info_path = os.path.join("data", "player_info.csv")
    if os.path.exists(info_path):
        try:
            df_i = pd.read_csv(info_path)
            if not df_i.empty:
                # Echte Daten in das Info-Objekt laden
                player_info.update(df_i.iloc[0].to_dict())
                th_image = get_asset_url(player_info.get('town_hall', 1), "town_hall")
        except Exception as e:
            print(f"Info Error: {e}")

    # 3. Truppen Kategorisieren
    categories = {
        "heroes": [], "pets": [], "siege": [], "super": [], 
        "dark": [], "spells": [], "elixir": []
    }
    
    troops_path = os.path.join("data", "player_troops.csv")
    if os.path.exists(troops_path):
        try:
            df = pd.read_csv(troops_path)
            df = df[df['village'] == 'Home']
            items = df.to_dict(orient='records')
            
            for item in items:
                name = item['name']
                dtype = item['type']
                cat_key = "elixir"
                
                if dtype == 'Hero': cat_key = "heroes"
                elif dtype == 'Pet': cat_key = "pets"
                elif dtype == 'Spell': cat_key = "spells"
                elif dtype == 'Troop':
                    if name in SIEGE_MACHINES_LIST: cat_key = "siege"
                    elif name in DARK_TROOPS_LIST: cat_key = "dark"
                    elif any(name.startswith(prefix) for prefix in SUPER_TROOPS_KEYWORDS) or name == 'Ice Hound':
                        cat_key = "super"
                    else: cat_key = "elixir"
                
                item['image_url'] = get_asset_url(name, cat_key)
                categories[cat_key].append(item)
        except Exception as e: print(f"Sort Error: {e}")

    # 4. Fortschritt berechnen
    progress = {}
    for key, items in categories.items():
        if not items:
            progress[key] = 0
            continue
        total_curr = sum(item['level'] for item in items)
        total_max = sum(item['max_level'] for item in items)
        progress[key] = round((total_curr / total_max) * 100, 1) if total_max > 0 else 0

    # HIER WAR DER FEHLER: 'player=player_info' muss übergeben werden
    return render_template("stats.html", 
                           labels=json.dumps(chart_labels), 
                           values=json.dumps(chart_values),
                           data=categories,
                           progress=progress,
                           player=player_info, # WICHTIG: Das fehlte beim Rendern!
                           th_image=th_image)

@app.route("/clan")
def clan():
    csv_info = os.path.join("data", "clan_info.csv")
    clan_data = {}
    if os.path.exists(csv_info):
        try:
            df = pd.read_csv(csv_info)
            if not df.empty:
                clan_data = df.iloc[0].to_dict()
                if isinstance(clan_data.get('description'), str):
                     clan_data['description'] = clan_data['description'].replace('\n', '<br>')
        except: pass

    csv_members = os.path.join("data", "clan_members.csv")
    members_data = []
    if os.path.exists(csv_members):
        try:
            df_m = pd.read_csv(csv_members)
            df_m = df_m.sort_values(by='trophies', ascending=False)
            members_data = df_m.to_dict(orient='records')
        except: pass

    return render_template("clan.html", clan=clan_data, members=members_data)

@app.route("/blog")
def blog():
    posts = [
        {"title": "Dashboard V1.0", "date": "04.12.2025", "category": "Update", "content": "Live!", "author": "Joni"},
        {"title": "Clan Level 16", "date": "01.12.2025", "category": "Clan", "content": "Level Up!", "author": "Leader"}
    ]
    return render_template("blog.html", posts=posts)

if __name__ == "__main__":
    app.run(debug=True)