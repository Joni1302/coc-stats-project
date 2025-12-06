import coc
import asyncio
import traceback
from src.config import COC_EMAIL, COC_PASSWORD, MY_PLAYER_TAG

async def fetch_all_data():
    """
    Holt Daten für Spieler (inkl. Legenden-Stats), Clan und erweiterte CWL-Infos.
    Kriegslog wurde entfernt.
    """
    client = coc.Client()
    
    # Ergebnis-Container
    results = {
        "player_info": {},
        "player_legend_stats": [],
        "player_troops": [],
        "player_achievements": [],
        "clan_info": {},
        "clan_members": [],
        "clan_war_log": [], # Bleibt leer, da deaktiviert
        "current_war": {},
        "cwl_group": [],
        "clan_capital_raids": []
    }

    try:
        # Login
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

        # 1.2 Legenden-Liga Statistiken
        if player.legend_statistics:
            ls = player.legend_statistics
            legend_data = {
                "legend_trophies": ls.legend_trophies,
                "current_season_trophies": ls.current_season.trophies if ls.current_season else 0,
                "current_season_rank": ls.current_season.rank if ls.current_season else 0,
                "best_season_id": ls.best_season.id if ls.best_season else None,
                "best_season_rank": ls.best_season.rank if ls.best_season else 0,
                "best_season_trophies": ls.best_season.trophies if ls.best_season else 0,
                "previous_season_id": ls.previous_season.id if ls.previous_season else None,
                "previous_season_rank": ls.previous_season.rank if ls.previous_season else 0,
                "previous_season_trophies": ls.previous_season.trophies if ls.previous_season else 0
            }
            results["player_legend_stats"].append(legend_data)

        # 1.3 Truppen, Helden, Zauber, Pets
        all_items = []
        all_items.extend([(x, "Troop") for x in player.troops])
        all_items.extend([(x, "Hero") for x in player.heroes])
        all_items.extend([(x, "Spell") for x in player.spells])
        pets = getattr(player, "pets", []) or getattr(player, "hero_pets", [])
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

        # 1.4 Errungenschaften
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
            
            capital_league = getattr(clan, "capital_league", None)
            war_league = getattr(clan, "war_league", None)

            results["clan_info"] = {
                "tag": clan.tag,
                "name": clan.name,
                "badge_url": clan.badge.medium,
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
                "war_losses": getattr(clan, "war_losses", 0),
                "war_ties": getattr(clan, "war_ties", 0),
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

            # --- TEIL 3: KRIEGE & CWL ---
            
            # 3.1 Aktueller Krieg
            try:
                war = await client.get_clan_war(clan.tag)
                if war:
                    results["current_war"] = {
                        "state": war.state,
                        "battle_modifier": war.battle_modifier.name if war.battle_modifier else "None",
                        "team_size": war.team_size,
                        "start_time": str(war.start_time),
                        "end_time": str(war.end_time),
                        "opponent_name": war.opponent.name if war.opponent else "Unknown",
                        "opponent_tag": war.opponent.tag if war.opponent else "Unknown",
                        "clan_stars": war.clan.stars,
                        "clan_destruction": war.clan.destruction,
                        "opponent_stars": war.opponent.stars,
                        "opponent_destruction": war.opponent.destruction
                    }
            except coc.PrivateWarLog:
                print("Aktueller Krieg nicht abrufbar (Kriegslog ist privat).")
            except Exception as e:
                print(f"Info: Kein aktiver Krieg gefunden ({e})")

            # 3.2 Kriegslog WURDE ENTFERNT

            # 3.3 CWL Gruppe (Erweitert)
            try:
                group = await client.get_league_group(clan.tag)
                if group:
                    for clan_in_group in group.clans:
                        results["cwl_group"].append({
                            "season": group.season,
                            "state": group.state,
                            "rounds_count": len(group.rounds),
                            "clan_tag": clan_in_group.tag,
                            "clan_name": clan_in_group.name,
                            "clan_level": clan_in_group.level,
                            "badge_url": clan_in_group.badge.medium,
                            "roster_size": len(clan_in_group.members)
                        })
            except coc.NotFound:
                print("Keine aktive CWL-Gruppe gefunden (Nicht CWL Woche?).")
            except Exception as e:
                print(f"CWL Fehler: {e}")

            # 3.4 Raid Log (Clanstadt)
            try:
                if hasattr(client, "get_raid_log"):
                    raid_log = await client.get_raid_log(clan.tag, limit=5)
                    for raid in raid_log:
                        results["clan_capital_raids"].append({
                            "start_time": str(raid.start_time.time),
                            "end_time": str(raid.end_time.time),
                            "total_loot": raid.total_loot,
                            "destroyed_districts": raid.destroyed_district_count,
                            "raid_attacks": raid.attack_count,
                            "offensive_reward": raid.offensive_reward
                        })
            except Exception as e:
                print(f"Raid Log Fehler: {e}")

    except Exception as e:
        print(f"Kritisches Problem beim Datenabruf: {e}")
        traceback.print_exc()
    finally:
        await client.close()
        
    return results