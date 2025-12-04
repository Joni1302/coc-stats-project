import asyncio
from src.data_fetcher import fetch_all_data
from src.csv_manager import save_data
from src.database_manager import init_db, save_player_snapshot, save_clan_snapshot

async def main():
    print("--- Clash of Clans Data Mining Gestartet ---")
    
    # NEU: 1. Datenbank initialisieren
    init_db()
    
    # 2. Alle Daten holen (als großes Dictionary)
    all_data = await fetch_all_data()
    
    # Daten für die DB-Speicherung extrahieren
    player_info = all_data["player_info"]
    clan_info = all_data.get("clan_info")

    # NEU: 3. Daten in Datenbank speichern (Historisierung)
    print("\n--- Archivierung in Datenbank ---")
    if player_info:
        save_player_snapshot(player_info)
    
    if clan_info:
        save_clan_snapshot(clan_info)

    # 4. Daten in CSV Dateien speichern (Übersicht)
    print("\n--- Speichere Daten in CSV Dateien ---")
    
    # Speichere alle Pakete, die im Dictionary existieren
    save_data("player_info", all_data["player_info"])
    save_data("player_troops", all_data["player_troops"])
    save_data("player_achievements", all_data["player_achievements"])
    
    if clan_info:
        save_data("clan_info", all_data["clan_info"])
        save_data("clan_members", all_data["clan_members"])
        save_data("clan_capital_raids", all_data["clan_capital_raids"])
    
    print("\nFertig! Daten in CSVs und DB gespeichert.")

if __name__ == "__main__":
    asyncio.run(main())