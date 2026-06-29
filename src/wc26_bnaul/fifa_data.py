"""
FIFA Data Integration Module for wc26-bnaul

Tích hợp dữ liệu từ:
- football-data.org (free tier)
- API-Football (via RapidAPI)
- FIFA Training Centre (PDF scraping)
- StatsBomb Open Data (offline dataset)

Usage:
    from wc26_bnaul.fifa_data import (
        get_fixtures_football_data,
        get_player_stats_api_football,
        get_injuries_api_football,
        get_match_predictions_api_football,
    )
"""

import os
import json
import time
import urllib.request
from typing import Optional, Dict, List
from datetime import datetime, timezone


# =============================================================================
# CONFIGURATION
# =============================================================================

# API Keys - set via environment variables
FOOTBALL_DATA_API_KEY = os.environ.get("FOOTBALL_DATA_API_KEY", "")
API_FOOTBALL_KEY = os.environ.get("API_FOOTBALL_KEY", "")

# Base URLs
FOOTBALL_DATA_BASE = "https://api.football-data.org/v4"
API_FOOTBALL_BASE = "https://v3.football.api-sports.io"

# World Cup IDs
WC_COMPETITION_ID = "WC"  # football-data.org
WC_LEAGUE_ID = 1  # API-Football
WC_SEASON = 2026

# Rate limiting
_last_football_data_call = 0
_last_api_football_call = 0


# =============================================================================
# RATE LIMITING
# =============================================================================

def _rate_limit_football_data():
    """Ensure max 10 req/min for football-data.org free tier."""
    global _last_football_data_call
    elapsed = time.time() - _last_football_data_call
    if elapsed < 6:  # 60s / 10 req = 6s between calls
        time.sleep(6 - elapsed)
    _last_football_data_call = time.time()


def _rate_limit_api_football():
    """Ensure max 100 req/day for API-Football free tier."""
    global _last_api_football_call
    # Simple delay: spread 100 requests over 24 hours
    # 24*3600 / 100 = 864s between calls
    elapsed = time.time() - _last_api_football_call
    if elapsed < 864:
        time.sleep(864 - elapsed)
    _last_api_football_call = time.time()


# =============================================================================
# football-data.org API
# =============================================================================

def _football_data_request(endpoint: str) -> dict:
    """Make authenticated request to football-data.org."""
    _rate_limit_football_data()
    
    url = f"{FOOTBALL_DATA_BASE}/{endpoint}"
    headers = {
        "X-Auth-Token": FOOTBALL_DATA_API_KEY,
        "Accept": "application/json",
    }
    
    req = urllib.request.Request(url, headers=headers, method="GET")
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        raise RuntimeError(f"football-data.org API Error {e.code}: {error_body}")


def get_fixtures_football_data(competition: str = "WC") -> List[Dict]:
    """
    Get all fixtures for a competition.
    
    Returns list of matches with:
    - id, utcDate, status, matchday
    - homeTeam, awayTeam (name, shortName, tla)
    - score (fullTime, halfTime)
    - group (for group stage)
    """
    data = _football_data_request(f"competitions/{competition}/matches")
    return data.get("matches", [])


def get_standings_football_data(competition: str = "WC") -> List[Dict]:
    """Get group standings."""
    data = _football_data_request(f"competitions/{competition}/standings")
    return data.get("standings", [])


def get_top_scorers_football_data(competition: str = "WC") -> List[Dict]:
    """Get top scorers."""
    data = _football_data_request(f"competitions/{competition}/scorers")
    return data.get("scorers", [])


def get_match_details_football_data(match_id: str) -> Dict:
    """Get detailed match info including scorers, bookings."""
    return _football_data_request(f"matches/{match_id}")


# =============================================================================
# API-Football (via RapidAPI)
# =============================================================================

def _api_football_request(endpoint: str, params: dict = None) -> dict:
    """Make authenticated request to API-Football."""
    _rate_limit_api_football()
    
    # Build URL with query params
    query = ""
    if params:
        query = "?" + "&".join(f"{k}={v}" for k, v in params.items())
    
    url = f"{API_FOOTBALL_BASE}/{endpoint}{query}"
    headers = {
        "x-apisports-key": API_FOOTBALL_KEY,
        "Accept": "application/json",
    }
    
    req = urllib.request.Request(url, headers=headers, method="GET")
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        raise RuntimeError(f"API-Football Error {e.code}: {error_body}")


def get_fixtures_api_football(
    league: int = WC_LEAGUE_ID,
    season: int = WC_SEASON,
    live: bool = False,
) -> List[Dict]:
    """
    Get fixtures from API-Football.
    
    Args:
        live: If True, get only live matches
    """
    params = {"league": league, "season": season}
    if live:
        params["live"] = "all"
    
    data = _api_football_request("fixtures", params)
    return data.get("response", [])


def get_player_stats_api_football(fixture_id: int) -> List[Dict]:
    """
    Get player statistics for a specific match.
    
    Returns list of player stats including:
    - minutes, shots, goals, assists
    - passes, tackles, duels, dribbles
    - rating (0-10)
    """
    data = _api_football_request("fixtures/players", {"fixture": fixture_id})
    return data.get("response", [])


def get_injuries_api_football(
    league: int = WC_LEAGUE_ID,
    season: int = WC_SEASON,
    team: int = None,
) -> List[Dict]:
    """
    Get injury reports.
    
    Args:
        team: Filter by team ID (optional)
    """
    params = {"league": league, "season": season}
    if team:
        params["team"] = team
    
    data = _api_football_request("injuries", params)
    return data.get("response", [])


def get_match_predictions_api_football(fixture_id: int) -> Dict:
    """
    Get AI predictions for a match.
    
    Returns:
        - winner: predicted winner
        - win_or_draw: boolean
        - under_over: predicted total goals
        - advice: text recommendation
        - percent: {home, draw, away}
    """
    data = _api_football_request("predictions", {"fixture": fixture_id})
    return data.get("response", [{}])[0]


def get_team_statistics_api_football(
    team_id: int,
    league: int = WC_LEAGUE_ID,
    season: int = WC_SEASON,
) -> Dict:
    """
    Get team statistics for a season.
    
    Returns:
        - form (last 5: W/D/L)
        - fixtures (wins, draws, losses)
        - goals (for, against)
        - biggest (streaks, wins, losses)
        - clean_sheet
        - failed_to_score
        - penalty (scored, missed)
    """
    data = _api_football_request(
        "teams/statistics",
        {"team": team_id, "league": league, "season": season}
    )
    return data.get("response", {})


def get_head_to_head_api_football(team_a: int, team_b: int) -> List[Dict]:
    """Get head-to-head history between two teams."""
    data = _api_football_request("fixtures/headtohead", {"h2h": f"{team_a}-{team_b}"})
    return data.get("response", [])


# =============================================================================
# FIFA Training Centre (PDF Scraping)
# =============================================================================

def get_fifa_training_centre_url(match_id: str) -> Optional[str]:
    """
    Build URL for FIFA Training Centre EFI PDF.
    
    Note: FIFA publishes EFI PDFs after matches at:
    https://www.fifatrainingcentre.com/en/fwc2022/efi-metrics/
    
    For WC 2026, URLs may change. This is a placeholder.
    """
    # WC 2022 format: https://www.fifatrainingcentre.com/en/fwc2022/efi-metrics/efi-metrics-pdfs.php
    # WC 2026 format TBD
    return None


# =============================================================================
# StatsBomb Open Data (Offline Dataset)
# =============================================================================

def load_statsbomb_data(competition: str = "FIFA World Cup", season: str = "2022") -> Optional[Dict]:
    """
    Load StatsBomb open data from local cache.
    
    Requires downloading data from:
    https://github.com/statsbomb/open-data
    
    Data includes:
    - Event data (passes, shots, tackles, etc.)
    - 360 data (player positions)
    - xG values
    """
    cache_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "statsbomb")
    
    # Look for cached data
    cache_file = os.path.join(cache_dir, f"{competition.replace(' ', '_')}_{season}.json")
    
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    print(f"StatsBomb data not found at {cache_file}")
    print("Download from: https://github.com/statsbomb/open-data")
    return None


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def calculate_form_index(team_stats: Dict) -> float:
    """
    Calculate a form index from team statistics.
    
    Returns a score between 0 and 1 based on:
    - Win rate
    - Goal difference
    - Clean sheet rate
    """
    fixtures = team_stats.get("fixtures", {})
    wins = fixtures.get("wins", {}).get("total", 0)
    draws = fixtures.get("draws", {}).get("total", 0)
    losses = fixtures.get("loses", {}).get("total", 0)
    total = wins + draws + losses
    
    if total == 0:
        return 0.5
    
    goals = team_stats.get("goals", {})
    goals_for = goals.get("for", {}).get("total", {}).get("total", 0)
    goals_against = goals.get("against", {}).get("total", {}).get("total", 0)
    
    clean_sheets = team_stats.get("clean_sheet", {}).get("total", 0)
    
    # Calculate components
    win_rate = wins / total
    draw_rate = draws / total
    goal_diff = (goals_for - goals_against) / max(total, 1)
    clean_sheet_rate = clean_sheets / max(total, 1)
    
    # Weighted form index
    form_index = (
        win_rate * 0.4 +
        draw_rate * 0.2 +
        min(max(goal_diff / 3, -1), 1) * 0.2 +  # normalize to [-1, 1]
        clean_sheet_rate * 0.2
    )
    
    return min(max(form_index, 0), 1)


def predict_from_api_data(
    home_team_stats: Dict,
    away_team_stats: Dict,
    h2h_history: List[Dict] = None,
) -> Dict:
    """
    Generate prediction probabilities from API data.
    
    Returns:
        {
            "home_win": float,
            "draw": float,
            "away_win": float,
            "confidence": float,
            "reasoning": str,
        }
    """
    home_form = calculate_form_index(home_team_stats)
    away_form = calculate_form_index(away_team_stats)
    
    # H2H adjustment
    h2h_home_wins = 0
    h2h_total = 0
    if h2h_history:
        for match in h2h_history:
            h2h_total += 1
            # Determine winner (simplified)
            home_goals = match.get("goals", {}).get("home", 0)
            away_goals = match.get("goals", {}).get("away", 0)
            if home_goals > away_goals:
                h2h_home_wins += 1
    
    h2h_factor = 0.5
    if h2h_total > 0:
        h2h_factor = h2h_home_wins / h2h_total
    
    # Combine factors
    # Base: form comparison
    home_strength = home_form * 0.6 + h2h_factor * 0.4
    away_strength = away_form * 0.6 + (1 - h2h_factor) * 0.4
    
    # Normalize to probabilities
    total_strength = home_strength + away_strength
    if total_strength == 0:
        return {"home_win": 0.33, "draw": 0.34, "away_win": 0.33, "confidence": 0.0}
    
    home_prob = home_strength / total_strength * 0.8  # 80% for win/loss
    away_prob = away_strength / total_strength * 0.8
    draw_prob = 0.2  # Fixed 20% for draw
    
    # Normalize
    total = home_prob + draw_prob + away_prob
    home_prob /= total
    draw_prob /= total
    away_prob /= total
    
    confidence = abs(home_prob - away_prob)
    
    reasoning = (
        f"Home form: {home_form:.2f}, Away form: {away_form:.2f}. "
        f"H2H factor: {h2h_factor:.2f} ({h2h_home_wins}/{h2h_total}). "
        f"Combined strength: Home {home_strength:.2f}, Away {away_strength:.2f}."
    )
    
    return {
        "home_win": round(home_prob, 2),
        "draw": round(draw_prob, 2),
        "away_win": round(away_prob, 2),
        "confidence": round(confidence, 2),
        "reasoning": reasoning,
    }


# =============================================================================
# TESTING
# =============================================================================

def test_apis():
    """Test all API integrations."""
    print("=" * 70)
    print("FIFA DATA API TEST")
    print("=" * 70)
    
    # Test football-data.org
    if FOOTBALL_DATA_API_KEY:
        print("\n--- football-data.org ---")
        try:
            fixtures = get_fixtures_football_data()
            print(f"✅ Got {len(fixtures)} fixtures")
            if fixtures:
                print(f"   Sample: {fixtures[0].get('homeTeam', {}).get('name')} vs {fixtures[0].get('awayTeam', {}).get('name')}")
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print("\n--- football-data.org ---")
        print("⚠️  FOOTBALL_DATA_API_KEY not set")
    
    # Test API-Football
    if API_FOOTBALL_KEY:
        print("\n--- API-Football ---")
        try:
            fixtures = get_fixtures_api_football()
            print(f"✅ Got {len(fixtures)} fixtures")
            if fixtures:
                print(f"   Sample: {fixtures[0].get('teams', {}).get('home', {}).get('name')} vs {fixtures[0].get('teams', {}).get('away', {}).get('name')}")
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print("\n--- API-Football ---")
        print("⚠️  API_FOOTBALL_KEY not set")
    
    print("\n" + "=" * 70)
    print("Set environment variables to test:")
    print("  export FOOTBALL_DATA_API_KEY='your_key'")
    print("  export API_FOOTBALL_KEY='your_key'")
    print("=" * 70)


if __name__ == "__main__":
    test_apis()
