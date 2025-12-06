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

# Achievement, das ignoriert werden soll
ACHIEVEMENT_TO_IGNORE = "Keep Your Account Safe!"

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
    # 1. Historie laden (Bleibt gleich)
    conn = get_db_connection()
    try:
        historical_data = conn.execute('SELECT timestamp, trophies FROM player_stats ORDER BY timestamp ASC').fetchall()
    except sqlite3.OperationalError:
        historical_data = [] 
    finally:
        conn.close()
    
    chart_labels = []
    chart_values = []
    seen_dates = set()

    for row in historical_data:
        try:
            dt = datetime.strptime(row['timestamp'], '%Y-%m-%dT%H:%M:%S.%f')
            day_key = dt.strftime('%Y-%m-%d')
            if day_key not in seen_dates:
                seen_dates.add(day_key)
                chart_labels.append(dt.strftime('%d.%m.'))
                chart_values.append(row['trophies'])
        except: continue

    # 2. Player Info & Legenden Stats laden (ERWEITERT)
    player_info = {
        "name": "Chief", "tag": "#...", "town_hall": 1, 
        "trophies": 0, "exp_level": 0, "war_stars": 0, 
        "attack_wins": 0, "role": "member", "best_trophies": 0,
        "current_season_rank": None # Default
    }
    
    # Basis Info laden
    info_path = os.path.join("data", "player_info.csv")
    if os.path.exists(info_path):
        try:
            df_i = pd.read_csv(info_path)
            if not df_i.empty:
                player_info.update(df_i.iloc[0].to_dict())
        except: pass

    # NEU: Legenden Stats laden
    legend_path = os.path.join("data", "player_legend_stats.csv")
    if os.path.exists(legend_path):
        try:
            df_l = pd.read_csv(legend_path)
            if not df_l.empty:
                # Füge die Legenden-Daten zum player_info Dictionary hinzu
                player_info.update(df_l.iloc[0].to_dict())
        except: pass

    # NEU: Liga Logik & Bild
    th_image = get_asset_url(player_info.get('town_hall', 1), "town_hall")
    
    # Logik für Legend League
    if player_info.get('trophies', 0) > 4800:
        player_info['league_name'] = "Legend League"
        # Dateiname aus deinem Upload (Legenden_League.png)
        player_info['league_image'] = "/static/assets/league/Legend_League.png"
    else:
        player_info['league_name'] = "Unranked" # Oder Logik für Titan etc. erweitern
        player_info['league_image'] = None


    # 3. Truppen Kategorisieren (Bleibt gleich)
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
        except: pass

    # 4. Fortschritt (Bleibt gleich)
    progress = {}
    for key, items in categories.items():
        if not items:
            progress[key] = 0
            continue
        total_curr = sum(item['level'] for item in items)
        total_max = sum(item['max_level'] for item in items)
        progress[key] = round((total_curr / total_max) * 100, 1) if total_max > 0 else 0

    # 5. Erfolge (Bleibt gleich)
    achievements = []
    ach_path = os.path.join("data", "player_achievements.csv")
    if os.path.exists(ach_path):
        try:
            df_a = pd.read_csv(ach_path)
            filtered_df = df_a[df_a['name'] != ACHIEVEMENT_TO_IGNORE]
            achievements = filtered_df.to_dict(orient='records')
        except Exception as e:
            print(f"Achievements Error: {e}")

    return render_template("stats.html", 
                           labels=json.dumps(chart_labels), 
                           values=json.dumps(chart_values),
                           data=categories,
                           progress=progress,
                           player=player_info,
                           th_image=th_image,
                           achievements=achievements)

@app.route("/clan")
def clan():
    # 1. Clan Info laden
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

    # 2. Mitglieder laden
    csv_members = os.path.join("data", "clan_members.csv")
    members_data = []
    if os.path.exists(csv_members):
        try:
            df_m = pd.read_csv(csv_members)
            df_m = df_m.sort_values(by='trophies', ascending=False)
            members_data = df_m.to_dict(orient='records')
        except: pass

    # 3. NEU: Aktuellen Krieg laden
    war_data = {}
    csv_war = os.path.join("data", "current_war.csv")
    if os.path.exists(csv_war):
        try:
            df_w = pd.read_csv(csv_war)
            if not df_w.empty:
                war_data = df_w.iloc[0].to_dict()
        except: pass

    # 4. NEU: CWL Gruppe laden
    cwl_data = {}
    csv_cwl = os.path.join("data", "cwl_group.csv")
    if os.path.exists(csv_cwl):
        try:
            df_c = pd.read_csv(csv_cwl)
            if not df_c.empty:
                # Wir nehmen hier nur Metadaten aus der ersten Zeile für die Anzeige
                first_row = df_c.iloc[0]
                cwl_data = {
                    "season": first_row.get("season"),
                    "state": first_row.get("state"),
                    "clans": df_c.to_dict(orient='records') # Liste aller Clans
                }
        except: pass

    return render_template("clan.html", 
                           clan=clan_data, 
                           members=members_data, 
                           war=war_data, 
                           cwl=cwl_data)

if __name__ == "__main__":
    app.run(debug=True)