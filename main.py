import asyncio
from src.data_fetcher import fetch_all_data
from src.csv_manager import save_data
from src.database_manager import init_db, save_player_snapshot, save_clan_snapshot, save_war_log_to_db

async def main():
    print("--- Clash of Clans Data Mining Gestartet ---")
    
    # 1. Datenbank initialisieren
    init_db()
    
    # 2. Alle Daten holen (als großes Dictionary)
    all_data = await fetch_all_data()
    
    # Daten für die DB-Speicherung extrahieren
    player_info = all_data.get("player_info")
    clan_info = all_data.get("clan_info")

    # 3. Daten in Datenbank speichern (Historisierung)
    print("\n--- Archivierung in Datenbank ---")
    if player_info:
        save_player_snapshot(player_info)
    
    if clan_info:
        save_clan_snapshot(clan_info)

    if clan_info:
        save_clan_snapshot(clan_info)
        
        # NEU: War Log speichern
        war_log_data = all_data.get("clan_war_log")
        if war_log_data:
            save_war_log_to_db(war_log_data)

    # 4. Daten in CSV Dateien speichern (Übersicht)
    print("\n--- Speichere Daten in CSV Dateien ---")
    
    # Standard Daten
    save_data("player_info", all_data["player_info"])
    
    # NEU: Legenden Statistiken separat speichern
    save_data("player_legend_stats", all_data["player_legend_stats"])
    
    save_data("player_troops", all_data["player_troops"])
    save_data("player_achievements", all_data["player_achievements"])
    
    # Clan Daten
    if clan_info:
        save_data("clan_info", all_data["clan_info"])
        save_data("clan_members", all_data["clan_members"])
        save_data("clan_capital_raids", all_data["clan_capital_raids"])
        
        # Kriegsdaten
        save_data("current_war", all_data["current_war"])
        save_data("cwl_group", all_data["cwl_group"])
    
    print("\nFertig! Daten in CSVs und DB gespeichert.")

if __name__ == "__main__":
    asyncio.run(main())