import sqlite3
import os
from datetime import datetime

DB_NAME = "coc_history.db"
DB_PATH = os.path.join("data", DB_NAME) # Speichern in den data/ Ordner

def init_db():
    """Erstellt die SQLite-Datenbank und die Tabellen, falls sie noch nicht existieren."""
    conn = None
    try:
        # Erstellt den data-Ordner, falls nötig (sollte schon da sein)
        os.makedirs("data", exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 1. Tabelle für Spieler-Statistiken (Zeitreihendaten)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_stats (
                timestamp TEXT PRIMARY KEY,
                player_tag TEXT,
                trophies INTEGER,
                best_trophies INTEGER,
                attack_wins INTEGER,
                donations_given INTEGER,
                donations_received INTEGER,
                town_hall INTEGER,
                exp_level INTEGER
            )
        """)

        # 2. Tabelle für Clan-Statistiken (Clan-Level und Punkte)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clan_stats (
                timestamp TEXT PRIMARY KEY,
                clan_tag TEXT,
                clan_level INTEGER,
                clan_points INTEGER,
                member_count INTEGER,
                war_wins INTEGER
            )
        """)
        conn.commit()
        print(f"✅ Datenbankstruktur in '{DB_PATH}' initialisiert.")
    
    except sqlite3.Error as e:
        print(f"Fehler bei der Datenbank-Initialisierung: {e}")
    finally:
        if conn:
            conn.close()


def save_player_snapshot(player_data):
    """Speichert einen neuen Datensatz der Spieler-Statistiken."""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        
        # Daten aus der Pandas Series (oder dem Dictionary) extrahieren
        data_tuple = (
            timestamp,
            player_data.get("tag"),
            player_data.get("trophies"),
            player_data.get("best_trophies"),
            player_data.get("attack_wins"),
            player_data.get("donations_given"),
            player_data.get("donations_received"),
            player_data.get("town_hall"),
            player_data.get("exp_level")
        )

        cursor.execute("""
            INSERT INTO player_stats VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data_tuple)
        
        conn.commit()
        print(f"Spieler-Snapshot erfolgreich in DB gespeichert.")

    except sqlite3.IntegrityError:
        print("Snapshot für heute bereits in DB vorhanden (Überspringe).")
    except sqlite3.Error as e:
        print(f"Fehler beim Speichern der Spielerdaten: {e}")
    finally:
        if conn:
            conn.close()


def save_clan_snapshot(clan_data):
    """Speichert einen neuen Datensatz der Clan-Statistiken."""
    if not clan_data:
        return # Nichts zu speichern
        
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        timestamp = datetime.now().isoformat()
        
        # Sicherstellen, dass die Daten verfügbar sind
        war_wins = clan_data.get("war_wins")
        if war_wins is None: war_wins = 0
        
        data_tuple = (
            timestamp,
            clan_data.get("tag"),
            clan_data.get("level"),
            clan_data.get("points"),
            clan_data.get("members_count"),
            war_wins
        )

        cursor.execute("""
            INSERT INTO clan_stats VALUES (?, ?, ?, ?, ?, ?)
        """, data_tuple)
        
        conn.commit()
        print(f"Clan-Snapshot erfolgreich in DB gespeichert.")

    except sqlite3.IntegrityError:
        print("Clan-Snapshot für heute bereits in DB vorhanden (Überspringe).")
    except sqlite3.Error as e:
        print(f"Fehler beim Speichern der Clan-Daten: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    # Test-Funktion: Kann direkt ausgeführt werden, um die DB zu erstellen
    init_db()