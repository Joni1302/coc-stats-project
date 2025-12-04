import coc
import asyncio
from src.config import COC_EMAIL, COC_PASSWORD, MY_PLAYER_TAG

async def fetch_all_data():
    """
    Holt ALLE verfügbaren Daten für Spieler und Clan und gibt sie als
    strukturiertes Dictionary zurück.
    """
    client = coc.Client()
    
    # Ergebnis-Container
    results = {
        "player_info": {},
        "player_troops": [],
        "player_achievements": [],
        "clan_info": {},
        "clan_members": [],
        "clan_capital_raids": [] # Kriegslog wurde entfernt
    }

    try:
        await client.login(email=COC_EMAIL, password=COC_PASSWORD)
        
        # --- TEIL 1: SPIELER DATEN ---
        print(f"Hole Daten für Spieler {MY_PLAYER_TAG}...")
        player = await client.get_player(MY_PLAYER_TAG)
        
        # 1.1 Basis Info
        results["player_info"] = {
            "tag": player.tag,
            "name": player.name,
            "town_hall": player.town_hall,
            "town_hall_weapon": getattr(player, "town_hall_weapon", None),
            "exp_level": player.exp_level,
            "trophies": player.trophies,
            "best_trophies": player.best_trophies,
            "war_stars": player.war_stars,
            "attack_wins": player.attack_wins,
            "defense_wins": player.defense_wins,
            "builder_hall": player.builder_hall,
            "builder_trophies": player.builder_base_trophies,
            "best_builder_trophies": player.best_builder_base_trophies,
            "role": player.role.name if player.role else "None",
            "war_preference": str(player.war_opted_in),
            "donations_given": player.donations,
            "donations_received": player.received,
            "clan_tag": player.clan.tag if player.clan else None
        }

        # 1.2 Truppen, Helden, Zauber, Pets
        all_items = []
        all_items.extend([(x, "Troop") for x in player.troops])
        all_items.extend([(x, "Hero") for x in player.heroes])
        all_items.extend([(x, "Spell") for x in player.spells])
        pets = getattr(player, "hero_pets", []) 
        if pets:
             all_items.extend([(x, "Pet") for x in pets])
        
        for item, type_label in all_items:
            is_home = getattr(item, "is_home_base", True)
            results["player_troops"].append({
                "name": item.name,
                "type": type_label,
                "level": item.level,
                "max_level": item.max_level,
                "is_maxed": item.is_max_for_townhall,
                "village": "Home" if is_home else "Builder"
            })

        # 1.3 Errungenschaften
        for ach in player.achievements:
            results["player_achievements"].append({
                "name": ach.name,
                "stars": ach.stars,
                "value": ach.value,
                "target": ach.target,
                "info": ach.info,
                "completed": ach.is_completed
            })

        # --- TEIL 2: CLAN DATEN ---
        if player.clan:
            print(f"Hole Daten für Clan {player.clan.tag}...")
            clan = await client.get_clan(player.clan.tag)
            
            # Safe Access für Clan Attribute
            capital_league = getattr(clan, "capital_league", None)
            war_league = getattr(clan, "war_league", None)

            results["clan_info"] = {
                "tag": clan.tag,
                "name": clan.name,
                "level": clan.level,
                "points": clan.points,
                "builder_points": clan.builder_base_points,
                "capital_points": getattr(clan, "capital_points", 0),
                "capital_league": capital_league.name if capital_league else "Unranked",
                "war_league": war_league.name if war_league else "Unranked",
                "description": clan.description,
                "type": clan.type,
                "required_trophies": clan.required_trophies,
                "members_count": clan.member_count,
                "war_win_streak": clan.war_win_streak,
                "war_wins": clan.war_wins,
                "war_losses": getattr(clan, "war_losses", None),
                "war_ties": getattr(clan, "war_ties", None),
                "is_war_log_public": clan.public_war_log
            }

            # 2.2 Mitglieder Liste
            async for member in clan.get_detailed_members():
                results["clan_members"].append({
                    "tag": member.tag,
                    "name": member.name,
                    "role": member.role.name,
                    "exp_level": member.exp_level,
                    "town_hall": member.town_hall,
                    "trophies": member.trophies,
                    "builder_trophies": member.builder_base_trophies,
                    "donations_given": member.donations,
                    "donations_received": member.received,
                    "league": member.league.name
                })

            # # 2.3 Kriegslog (AUSGEKLAMMERT)
            # print("Kriegslog-Abruf wegen Fehler temporär deaktiviert.")

            # 2.4 Raid Seasons (Clanstadt)
            try:
                if hasattr(client, "get_raid_log"):
                    raid_log = await client.get_raid_log(clan.tag, limit=5)
                    for raid in raid_log:
                        results["clan_capital_raids"].append({
                            "start_time": raid.start_time.time,
                            "end_time": raid.end_time.time,
                            "total_loot": raid.total_loot,
                            "destroyed_districts": raid.destroyed_district_count,
                            "raid_attacks": raid.attack_count,
                            "offensive_reward": raid.offensive_reward
                        })
                else:
                    print("Raid Log Funktion nicht verfügbar.")
            except Exception as e:
                print(f"Konnte Raid Log nicht laden: {e}")

    except Exception as e:
        print(f"Kritisches Problem beim Datenabruf: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()
        
    return results