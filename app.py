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
    # 1. Historie laden
    conn = get_db_connection()
    try:
        historical_data = conn.execute('SELECT timestamp, trophies FROM player_stats ORDER BY timestamp ASC').fetchall()
    except sqlite3.OperationalError:
        historical_data = [] 
    finally:
        conn.close()
    
    # --- NEU: Intelligentes Filtern für 06:00 Uhr ---
    daily_data = {}
    
    for row in historical_data:
        try:
            # Wir versuchen verschiedene Formate, um robust gegen kleine Änderungen zu sein
            try:
                dt = datetime.strptime(row['timestamp'], '%Y-%m-%dT%H:%M:%S.%f')
            except ValueError:
                # Fallback, falls keine Mikrosekunden gespeichert wurden
                dt = datetime.strptime(row['timestamp'], '%Y-%m-%dT%H:%M:%S')
            
            day_key = dt.strftime('%Y-%m-%d')
            
            if day_key not in daily_data:
                daily_data[day_key] = []
            
            # Wir sammeln erst mal ALLE Einträge pro Tag
            daily_data[day_key].append({
                'dt': dt,
                'trophies': row['trophies']
            })
        except Exception as e:
            continue

    chart_labels = []
    chart_values = []
    
    # Jetzt gehen wir jeden Tag durch und suchen den "besten" Eintrag (nahe 6 Uhr)
    for day in sorted(daily_data.keys()):
        entries = daily_data[day]
        
        best_entry = None
        min_diff = 24 * 3600 # Startwert: riesige Differenz
        
        target_hour = 6 # Hier stellen wir 6 Uhr ein
        
        for entry in entries:
            # Wir erstellen ein Vergleichsdatum für diesen Tag um exakt 06:00 Uhr
            target_time = entry['dt'].replace(hour=target_hour, minute=0, second=0, microsecond=0)
            
            # Wie weit ist dieser Eintrag von 6 Uhr entfernt? (in Sekunden)
            diff = abs((entry['dt'] - target_time).total_seconds())
            
            # Wenn dieser Eintrag näher an 6 Uhr ist als der bisher beste -> merken!
            if diff < min_diff:
                min_diff = diff
                best_entry = entry
        
        if best_entry:
            chart_labels.append(best_entry['dt'].strftime('%d.%m.'))
            chart_values.append(best_entry['trophies'])

    # 2. Player Info & Legenden Stats laden (Bleibt wie vorher)
    player_info = {
        "name": "Chief", "tag": "#...", "town_hall": 1, 
        "trophies": 0, "exp_level": 0, "war_stars": 0, 
        "attack_wins": 0, "role": "member", "best_trophies": 0,
        "current_season_rank": None
    }
    
    info_path = os.path.join("data", "player_info.csv")
    if os.path.exists(info_path):
        try:
            df_i = pd.read_csv(info_path)
            if not df_i.empty:
                player_info.update(df_i.iloc[0].to_dict())
        except: pass

    legend_path = os.path.join("data", "player_legend_stats.csv")
    if os.path.exists(legend_path):
        try:
            df_l = pd.read_csv(legend_path)
            if not df_l.empty:
                player_info.update(df_l.iloc[0].to_dict())
        except: pass

    th_image = get_asset_url(player_info.get('town_hall', 1), "town_hall")
    
    if player_info.get('trophies', 0) > 4800:
        player_info['league_name'] = "Legend League"
        player_info['league_image'] = "/static/assets/league/Legend_League.png"
    else:
        player_info['league_name'] = "Unranked"
        player_info['league_image'] = None

    # 3. Truppen (Bleibt wie vorher)
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

    # 4. Fortschritt (Bleibt wie vorher)
    progress = {}
    for key, items in categories.items():
        if not items:
            progress[key] = 0
            continue
        total_curr = sum(item['level'] for item in items)
        total_max = sum(item['max_level'] for item in items)
        progress[key] = round((total_curr / total_max) * 100, 1) if total_max > 0 else 0

    # 5. Erfolge (Bleibt wie vorher)
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

        # 5. NEU: Clan Capital Raids laden
    raids_data = []
    csv_raids = os.path.join("data", "clan_capital_raids.csv")
    if os.path.exists(csv_raids):
        try:
            df_r = pd.read_csv(csv_raids)
            if not df_r.empty:
                # In Dictionary umwandeln
                raids_data = df_r.to_dict(orient='records')
                
                # Datum schön formatieren für die Anzeige
                for raid in raids_data:
                    try:
                        # Wir parsen das Datum (Format aus deiner CSV)
                        dt_start = datetime.strptime(str(raid['start_time']), '%Y-%m-%d %H:%M:%S')
                        dt_end = datetime.strptime(str(raid['end_time']), '%Y-%m-%d %H:%M:%S')
                        # Erstellt String wie "05.12. - 08.12."
                        raid['date_label'] = f"{dt_start.strftime('%d.%m.')} - {dt_end.strftime('%d.%m.')}"
                    except Exception:
                        raid['date_label'] = "Unbekannt"
        except Exception as e:
            print(f"Raid Error: {e}")

            # 6. NEU: Kriegs-Historie aus der Datenbank laden
    war_history = []
    try:
        conn = get_db_connection()
        # Wir holen die letzten 20 Kriege, sortiert nach Datum (neueste zuerst)
        rows = conn.execute('SELECT * FROM war_history ORDER BY end_time DESC LIMIT 20').fetchall()
        conn.close()
        
        for row in rows:
            # SQLite Row in normales Dictionary umwandeln
            war = dict(row)
            
            # Datum schön formatieren (z.B. "10.12.2025")
            try:
                # Wir entfernen evtl. vorhandene Zeitzonen-Infos für einfaches Parsing
                clean_time = war['end_time'].split('+')[0] 
                dt = datetime.strptime(clean_time, '%Y-%m-%dT%H:%M:%S.%f')
            except ValueError:
                try:
                    # Fallback für Format ohne Millisekunden
                    dt = datetime.strptime(clean_time, '%Y-%m-%dT%H:%M:%S')
                except:
                    dt = datetime.now() # Fallback

            war['date_label'] = dt.strftime('%d.%m.%Y')
            
            # Ergebnis für die Anzeige aufbereiten (Farbe & Text)
            if war['result'] == 'win':
                war['result_badge'] = 'bg-success'
                war['result_text'] = 'SIEG'
            elif war['result'] == 'lose':
                war['result_badge'] = 'bg-danger'
                war['result_text'] = 'NIEDERLAGE'
            elif war['result'] == 'tie':
                war['result_badge'] = 'bg-secondary'
                war['result_text'] = 'REMIS'
            else:
                war['result_badge'] = 'bg-dark border border-secondary'
                war['result_text'] = 'UNKNOWN'
                
            war_history.append(war)
            
    except Exception as e:
        print(f"Fehler beim Laden der War History: {e}")

    return render_template("clan.html", 
                           clan=clan_data, 
                           members=members_data, 
                           war=war_data, 
                           cwl=cwl_data,
                           raids=raids_data,
                           war_history=war_history) # <--- HIER DAS NEUE ARGUMENT EINFÜGEN

@app.route("/blog")
def blog():
    posts = [
        {"title": "Dashboard V1.0", "date": "04.12.2025", "category": "Update", "content": "Live!", "author": "Joni"},
        {"title": "Clan Level 16", "date": "01.12.2025", "category": "Clan", "content": "Level Up!", "author": "Leader"}
    ]
    return render_template("blog.html", posts=posts)

if __name__ == "__main__":
    app.run(debug=True)