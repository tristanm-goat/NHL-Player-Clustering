#!/usr/bin/env python3
"""
MoneyPuck NHL Data Downloader
Downloads all available MoneyPuck NHL data and saves to organized folders.
Data source: https://moneypuck.com/data.htm
"""
import os
import urllib.request
import urllib.error

BASE = "https://moneypuck.com"
PETER = "https://peter-tanner.com/moneypuck/downloads"
SEASONS = list(range(2008, 2026))

def dl(url, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    print(f"Downloading {url}")
    try:
        urllib.request.urlretrieve(url, dest)
        print(f"  -> {dest} ({os.path.getsize(dest):,} bytes)")
        return True
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

# Data dictionaries
dl(f"{PETER}/MoneyPuckDataDictionaryForPlayers.csv", "data/data_dictionary/players_dict.csv")
dl(f"{PETER}/MoneyPuck_Shot_Data_Dictionary.csv", "data/data_dictionary/shots_dict.csv")

# Player bios
dl(f"{BASE}/moneypuck/playerData/playerBios/allPlayersLookup.csv", "data/player_bios/allPlayersLookup.csv")

# Season level (one row per player per season) - current 2025-2026
for dtype in ['skaters', 'goalies', 'lines', 'teams']:
    dl(f"{BASE}/moneypuck/playerData/seasonSummary/2025/regular/{dtype}.csv", f"data/season_level/{dtype}/2025-2026_{dtype}.csv")

# Season level - historical seasons 2008-2025
for year in SEASONS:
    s = f"{year}-{year+1}"
    for dtype in ['skaters', 'goalies', 'lines', 'teams']:
        dl(f"{BASE}/moneypuck/playerData/seasonSummary/{year}/regular/{dtype}.csv", f"data/season_level/{dtype}/{s}_{dtype}.csv")

# Season level - all historical combined (ZIPs)
for dtype in ['skaters', 'goalies', 'lines', 'teams']:
    dl(f"{PETER}/historicalOneRowPerSeason/{dtype}_2008_to_2024.zip", f"data/season_level/combined/{dtype}_2008_to_2024.zip")

# Game-by-game - all teams all seasons (120MB CSV)
dl(f"{BASE}/moneypuck/playerData/careers/gameByGame/all_teams.csv", "data/game_by_game/all_teams.csv")

# Game-by-game season ZIPs
for dtype in ['skaters', 'goalies', 'lines']:
    dl(f"{PETER}/seasonPlayersSummary/{dtype}/2025.zip", f"data/game_by_game/{dtype}/2025-2026.zip")
    dl(f"{PETER}/seasonPlayersSummary/{dtype}/2008_to_2024.zip", f"data/game_by_game/{dtype}/2008_to_2024.zip")
    for year in SEASONS:
        dl(f"{PETER}/seasonPlayersSummary/{dtype}/{year}.zip", f"data/game_by_game/{dtype}/{year}-{year+1}.zip")

# Shots - individual seasons 2007-2025
for year in range(2007, 2026):
    dl(f"{PETER}/shots_{year}.zip", f"data/shots/individual/shots_{year}-{year+1}.zip")
dl(f"{PETER}/shots_2007-2024.zip", "data/shots/shots_2007-2024.zip")
dl(f"{PETER}/shots_2018-2024.zip", "data/shots/shots_2018-2024.zip")

print("Download complete!")
