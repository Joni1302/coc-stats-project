import asyncio
from src.data_fetcher import fetch_all_data
from src.csv_manager import save_data

async def main():
    print("--- Clash of Clans Data Mining Gestartet ---")
    
    # 1. Alle Daten holen (als großes Dictionary)
    all_data = await fetch_all_data()
    
    print("\n--- Speichere Daten in CSV Dateien ---")
    
    # 2. Jedes Paket einzeln speichern
    save_data("player_info", all_data["player_info"])
    save_data("player_troops", all_data["player_troops"])
    save_data("player_achievements", all_data["player_achievements"])
    
    # Clan Daten nur speichern, wenn vorhanden
    if all_data.get("clan_info"):
        save_data("clan_info", all_data["clan_info"])
        save_data("clan_members", all_data["clan_members"])
        #save_data("clan_warlog", all_data["clan_warlog"])
        save_data("clan_capital_raids", all_data["clan_capital_raids"])
    
    print("\n✅ Fertig! Schaue im Ordner 'data/' nach.")

if __name__ == "__main__":
    asyncio.run(main())