"""
data_collection.py
-------------------
Fetches NHL men's advanced stats from Natural Stat Trick, MoneyPuck, and the
NHL API for seasons 2018-19 through 2025-26 (regular season + playoffs).

Outputs:
  Data/nst_skaters_raw.csv    — Natural Stat Trick 5v5 on-ice + individual stats
  Data/mp_skaters_raw.csv     — MoneyPuck xG and shot quality metrics
  Data/nhl_players_raw.csv    — NHL API player biographical and positional data
  Data/all_skaters.csv        — Merged, cleaned master dataset

Usage:
  python data_collection.py
"""

import os
import time
import requests
import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SEASONS = [
    "20182019", "20192020", "20202021", "20212022",
    "20222023", "20232024", "20242025", "20252026",
]

SEASON_LABELS = {
    "20182019": "2018-19",
    "20192020": "2019-20",
    "20202021": "2020-21",
    "20212022": "2021-22",
    "20222023": "2022-23",
    "20232024": "2023-24",
    "20242025": "2024-25",
    "20252026": "2025-26",
}

# Natural Stat Trick base URL for skater reports
# Parameters: sit=5v5, score=all, stdoi=Y (standard/on-ice), rate=Y (per-60)
NST_URL = (
    "https://www.naturalstattrick.com/playerteams.php"
    "?fromseason={season}&thruseason={season}&stype={stype}"
    "&sit=5v5&score=all&stdoi={report}&rate=Y&team=ALL&pos=S&loc=B&toi=100&gpfilt=GP&fd=&td=&tgp=410&lines=single&draftteam=ALL"
)

NST_SITETYPE_MAP = {
    "regular": 2,
    "playoffs": 3,
}

# MoneyPuck skaters CSV URL pattern
MP_URL = "https://moneypuck.com/moneypuck/playerData/seasonSummary/{year}/regular/skaters.csv"
MP_PLAYOFF_URL = "https://moneypuck.com/moneypuck/playerData/seasonSummary/{year}/playoffs/skaters.csv"

# NHL API
NHL_API_BASE = "https://api-web.nhle.com/v1"

DATA_DIR = "Data"
os.makedirs(DATA_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Natural Stat Trick — web scraping via requests + pandas HTML parsing
# ---------------------------------------------------------------------------

def fetch_nst_table(season: str, sit_type: str, report: str) -> pd.DataFrame:
    """
    Fetch a Natural Stat Trick skater report table for a given season.
    sit_type: 'regular' or 'playoffs'
    report:   'oi' (on-ice) or 'std' (individual)
    """
    stype = NST_SITETYPE_MAP[sit_type]
    url = NST_URL.format(season=season, stype=stype, report=report)
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": "https://www.naturalstattrick.com/",
    }
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    tables = pd.read_html(resp.text)
    if not tables:
        raise ValueError(f"No tables found for {season} {sit_type} {report}")
    df = tables[0]
    df["Season"] = SEASON_LABELS[season]
    df["SitType"] = sit_type
    return df


def collect_nst_data() -> pd.DataFrame:
    """Collect all NST on-ice and individual tables and merge them."""
    all_frames = []
    for season in SEASONS:
        for sit_type in ["regular", "playoffs"]:
            print(f"  NST on-ice  : {season} {sit_type}")
            try:
                df_oi = fetch_nst_table(season, sit_type, "oi")
                df_oi.columns = [c.strip() for c in df_oi.columns]
                all_frames.append(df_oi)
            except Exception as e:
                print(f"    WARNING: {e}")
            time.sleep(1.5)  # be polite to the server
    if not all_frames:
        return pd.DataFrame()
    combined = pd.concat(all_frames, ignore_index=True)
    return combined


# ---------------------------------------------------------------------------
# MoneyPuck
# ---------------------------------------------------------------------------

def collect_moneypuck_data() -> pd.DataFrame:
    """Download MoneyPuck skater CSVs for all seasons."""
    frames = []
    for season in SEASONS:
        year = int(season[:4])
        for url_template, sit_type in [(MP_URL, "regular"), (MP_PLAYOFF_URL, "playoffs")]:
            url = url_template.format(year=year)
            try:
                print(f"  MoneyPuck: {year} {sit_type}")
                df = pd.read_csv(url)
                df["Season"] = SEASON_LABELS[season]
                df["SitType"] = sit_type
                frames.append(df)
            except Exception as e:
                print(f"    WARNING: {e}")
            time.sleep(0.5)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------------------
# NHL API — player biographical data
# ---------------------------------------------------------------------------

def fetch_nhl_roster(team_abbr: str, season: str) -> list:
    """Fetch roster for a team from the NHL API."""
    url = f"{NHL_API_BASE}/roster/{team_abbr}/{season}"
    resp = requests.get(url, timeout=15)
    if resp.status_code != 200:
        return []
    data = resp.json()
    players = []
    for group in ["forwards", "defensemen", "goalies"]:
        for p in data.get(group, []):
            players.append({
                "playerId": p.get("id"),
                "firstName": p.get("firstName", {}).get("default", ""),
                "lastName": p.get("lastName", {}).get("default", ""),
                "sweaterNumber": p.get("sweaterNumber"),
                "positionCode": p.get("positionCode"),
                "heightInInches": p.get("heightInInches"),
                "weightInPounds": p.get("weightInPounds"),
                "birthDate": p.get("birthDate"),
                "birthCountry": p.get("birthCountry"),
                "teamAbbr": team_abbr,
                "Season": season,
            })
    return players


def fetch_nhl_teams() -> list:
    """Fetch current NHL team list from the API."""
    url = f"{NHL_API_BASE}/standings/now"
    resp = requests.get(url, timeout=15)
    data = resp.json()
    teams = []
    for entry in data.get("standings", []):
        abbr = entry.get("teamAbbrev", {}).get("default")
        if abbr:
            teams.append(abbr)
    return list(set(teams))


def collect_nhl_player_data() -> pd.DataFrame:
    """Collect player biographical info for all teams and seasons."""
    teams = fetch_nhl_teams()
    all_players = []
    for season in SEASONS:
        for team in teams:
            try:
                players = fetch_nhl_roster(team, season)
                all_players.extend(players)
            except Exception as e:
                print(f"    WARNING {team} {season}: {e}")
        time.sleep(0.2)
    if not all_players:
        return pd.DataFrame()
    df = pd.DataFrame(all_players)
    df["Player"] = df["firstName"] + " " + df["lastName"]
    df = df.drop_duplicates(subset=["playerId", "Season"])
    return df


# ---------------------------------------------------------------------------
# Merge and clean
# ---------------------------------------------------------------------------

def merge_datasets(df_nst: pd.DataFrame, df_mp: pd.DataFrame, df_nhl: pd.DataFrame) -> pd.DataFrame:
    """
    Merge Natural Stat Trick, MoneyPuck, and NHL API data.
    Align on Player name + Season + SitType.
    """
    # Standardize player name columns
    if "Player" not in df_nst.columns and "Name" in df_nst.columns:
        df_nst = df_nst.rename(columns={"Name": "Player"})

    # MoneyPuck uses 'name' column
    if "name" in df_mp.columns:
        df_mp = df_mp.rename(columns={"name": "Player"})
    if "situation" in df_mp.columns:
        df_mp = df_mp[df_mp["situation"] == "5on5"]

    # Merge NST + MP
    merge_keys = ["Player", "Season", "SitType"]
    if not df_nst.empty and not df_mp.empty:
        merged = pd.merge(df_nst, df_mp, on=merge_keys, how="outer", suffixes=("_nst", "_mp"))
    elif not df_nst.empty:
        merged = df_nst
    else:
        merged = df_mp

    # Merge in NHL biographical data
    if not df_nhl.empty and not merged.empty:
        merged = pd.merge(
            merged,
            df_nhl[["Player", "Season", "positionCode", "birthCountry", "birthDate"]].drop_duplicates(subset=["Player", "Season"]),
            on=["Player", "Season"],
            how="left",
        )

    return merged


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=== Collecting Natural Stat Trick data ===")
    df_nst = collect_nst_data()
    nst_path = os.path.join(DATA_DIR, "nst_skaters_raw.csv")
    df_nst.to_csv(nst_path, index=False)
    print(f"  Saved {len(df_nst)} rows -> {nst_path}")

    print("\n=== Collecting MoneyPuck data ===")
    df_mp = collect_moneypuck_data()
    mp_path = os.path.join(DATA_DIR, "mp_skaters_raw.csv")
    df_mp.to_csv(mp_path, index=False)
    print(f"  Saved {len(df_mp)} rows -> {mp_path}")

    print("\n=== Collecting NHL API biographical data ===")
    df_nhl = collect_nhl_player_data()
    nhl_path = os.path.join(DATA_DIR, "nhl_players_raw.csv")
    df_nhl.to_csv(nhl_path, index=False)
    print(f"  Saved {len(df_nhl)} rows -> {nhl_path}")

    print("\n=== Merging datasets ===")
    df_all = merge_datasets(df_nst, df_mp, df_nhl)
    all_path = os.path.join(DATA_DIR, "all_skaters.csv")
    df_all.to_csv(all_path, index=False)
    print(f"  Saved {len(df_all)} rows -> {all_path}")
    print("\nData collection complete.")


if __name__ == "__main__":
    main()
