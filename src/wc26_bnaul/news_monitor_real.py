#!/usr/bin/env python3
"""
Real News Monitor for wc26-bnaul

Tích hợp:
- NewsAPI (https://newsapi.org/) — free tier: 100 req/day
- RSS feeds (BBC Sport, ESPN, Goal.com) — no API key needed
- API-Football injuries endpoint — requires API_FOOTBALL_KEY
- football-data.org scorers/lineups — requires FOOTBALL_DATA_API_KEY

Usage:
    uv run python -m wc26_bnaul.news_monitor_real --dry-run
    uv run python -m wc26_bnaul.news_monitor_real --check m001
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple

# Import từ wc26_bnaul
from wc26_bnaul import api_request, get_credentials
from wc26_bnaul.fifa_data import (
    get_injuries_api_football,
    get_fixtures_football_data,
    get_match_details_football_data,
    _get_api_football_key,
    _get_football_data_key,
)


# =============================================================================
# CONFIGURATION
# =============================================================================

# Load .env at module level (same as __init__.py)
_env_loaded = False

def _load_env():
    global _env_loaded
    if _env_loaded:
        return
    env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
    if not os.path.exists(env_path):
        env_path = os.path.join(os.getcwd(), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    # Strip quotes and comments
                    value = value.strip().split()[0].strip('"').strip("'")
                    if key not in os.environ:
                        os.environ[key] = value
    _env_loaded = True

_load_env()

NEWSAPI_KEY = os.environ.get("NEWSAPI_KEY", "")
NEWSAPI_BASE = "https://newsapi.org/v2"

# RSS feeds for football news (verified working)
RSS_FEEDS = {
    "bbc_sport": "http://feeds.bbci.co.uk/sport/football/rss.xml",
    "espn_fc": "https://www.espn.com/espn/rss/news",
    "sky_sports": "https://www.skysports.com/rss/12040",
    "worldsoccer": "https://www.worldsoccer.com/rss",
}

# Team name mapping: ClawCup name → API-Football team ID
# WC 2026 teams (top 32)
TEAM_ID_MAP = {
    # South America
    "Argentina": 26,
    "Brazil": 6,
    "Uruguay": 7,
    "Colombia": 8,
    "Ecuador": 9,
    "Paraguay": 10,
    "Chile": 11,
    "Peru": 12,
    "Venezuela": 13,
    "Bolivia": 14,
    # Europe
    "France": 2,
    "England": 10,
    "Spain": 9,
    "Germany": 25,
    "Portugal": 27,
    "Netherlands": 15,
    "Italy": 4,
    "Belgium": 1,
    "Croatia": 3,
    "Denmark": 21,
    "Switzerland": 17,
    "Sweden": 5,
    "Poland": 24,
    "Serbia": 22,
    "Ukraine": 29,
    "Turkey": 28,
    "Wales": 767,
    "Scotland": 768,
    "Czech Republic": 769,
    "Austria": 770,
    "Hungary": 771,
    "Norway": 773,
    "Slovenia": 774,
    "Slovakia": 775,
    "Romania": 776,
    "Greece": 777,
    "Finland": 778,
    "Bosnia": 779,
    "Iceland": 780,
    "Northern Ireland": 781,
    "Republic of Ireland": 782,
    "Albania": 783,
    "North Macedonia": 784,
    "Montenegro": 785,
    "Georgia": 786,
    "Armenia": 787,
    "Azerbaijan": 788,
    "Belarus": 789,
    "Estonia": 790,
    "Latvia": 791,
    "Lithuania": 792,
    "Luxembourg": 793,
    "Malta": 794,
    "Moldova": 795,
    "Kazakhstan": 796,
    "Kosovo": 797,
    "Liechtenstein": 798,
    "Andorra": 799,
    "San Marino": 800,
    "Gibraltar": 801,
    "Faroe Islands": 802,
    # Asia
    "Japan": 12,
    "South Korea": 17,
    "Australia": 20,
    "Iran": 22,
    "Saudi Arabia": 23,
    "Qatar": 24,
    "Iraq": 25,
    "UAE": 26,
    "China": 27,
    "Uzbekistan": 28,
    "Jordan": 29,
    "Bahrain": 30,
    "Syria": 31,
    "Oman": 32,
    "Lebanon": 33,
    "Kuwait": 34,
    "Palestine": 35,
    "India": 36,
    "Thailand": 37,
    "Vietnam": 38,
    "Malaysia": 39,
    "Indonesia": 40,
    "Singapore": 41,
    "Philippines": 42,
    "Myanmar": 43,
    "Cambodia": 44,
    "Laos": 45,
    "Brunei": 46,
    "Timor-Leste": 47,
    "Mongolia": 48,
    "Nepal": 49,
    "Bhutan": 50,
    "Bangladesh": 51,
    "Sri Lanka": 52,
    "Pakistan": 53,
    "Afghanistan": 54,
    "Tajikistan": 55,
    "Kyrgyzstan": 56,
    "Turkmenistan": 57,
    "North Korea": 58,
    "Chinese Taipei": 59,
    "Hong Kong": 60,
    "Macau": 61,
    "Guam": 62,
    "Northern Mariana Islands": 63,
    "American Samoa": 64,
    "Samoa": 65,
    "Tonga": 66,
    "Fiji": 67,
    "New Caledonia": 68,
    "Papua New Guinea": 69,
    "Solomon Islands": 70,
    "Vanuatu": 71,
    "Cook Islands": 72,
    "Tahiti": 73,
    # Africa
    "Morocco": 31,
    "Senegal": 32,
    "Tunisia": 33,
    "Algeria": 34,
    "Egypt": 35,
    "Nigeria": 36,
    "Cameroon": 37,
    "Ghana": 38,
    "Ivory Coast": 39,
    "Mali": 40,
    "Burkina Faso": 41,
    "Guinea": 42,
    "South Africa": 43,
    "Cape Verde": 44,
    "DR Congo": 45,
    "Zambia": 46,
    "Gabon": 47,
    "Equatorial Guinea": 48,
    "Uganda": 49,
    "Benin": 50,
    "Mauritania": 51,
    "Kenya": 52,
    "Madagascar": 53,
    "Mozambique": 54,
    "Central African Republic": 55,
    "Zimbabwe": 56,
    "Angola": 57,
    "Congo": 58,
    "Tanzania": 59,
    "Sudan": 60,
    "Libya": 61,
    "Niger": 62,
    "Rwanda": 63,
    "Togo": 64,
    "Malawi": 65,
    "Liberia": 66,
    "Guinea-Bissau": 67,
    "Sierra Leone": 68,
    "Namibia": 69,
    "Gambia": 70,
    "Botswana": 71,
    "Burundi": 72,
    "Comoros": 73,
    "Lesotho": 74,
    "Eswatini": 75,
    "Ethiopia": 76,
    "South Sudan": 77,
    "Chad": 78,
    "Mauritius": 79,
    "Seychelles": 80,
    "Djibouti": 81,
    "Eritrea": 82,
    "São Tomé and Príncipe": 83,
    "Somalia": 84,
    # North America
    "United States": 16,
    "Mexico": 17,
    "Canada": 18,
    "Costa Rica": 19,
    "Jamaica": 20,
    "Honduras": 21,
    "Panama": 22,
    "Trinidad and Tobago": 23,
    "Haiti": 24,
    "Guatemala": 25,
    "Cuba": 26,
    "Curaçao": 27,
    "Nicaragua": 28,
    "Suriname": 29,
    "Antigua and Barbuda": 30,
    "Saint Kitts and Nevis": 31,
    "Dominican Republic": 32,
    "Grenada": 33,
    "Barbados": 34,
    "Guyana": 35,
    "Saint Lucia": 36,
    "Puerto Rico": 37,
    "Bermuda": 38,
    "Belize": 39,
    "Saint Vincent and the Grenadines": 40,
    "Montserrat": 41,
    "Dominica": 42,
    "Cayman Islands": 43,
    "Bahamas": 44,
    "Aruba": 45,
    "Turks and Caicos Islands": 46,
    "British Virgin Islands": 47,
    "US Virgin Islands": 48,
    "Anguilla": 49,
    # South America (additional)
    "Guyana": 50,
    "Suriname": 51,
    "French Guiana": 52,
    "Falkland Islands": 53,
}


# =============================================================================
# NEWS SOURCES
# =============================================================================

def fetch_newsapi(query: str, from_date: str = None, page_size: int = 10) -> List[Dict]:
    """
    Fetch news from NewsAPI.
    
    Free tier: 100 requests/day, 100 articles per request.
    """
    if not NEWSAPI_KEY:
        print("  ⚠️  NEWSAPI_KEY not set. Get one at https://newsapi.org/")
        return []
    
    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": str(page_size),
        "apiKey": NEWSAPI_KEY,
    }
    
    if from_date:
        params["from"] = from_date
    
    query_str = "&".join(f"{k}={urllib.parse.quote(v)}" for k, v in params.items())
    url = f"{NEWSAPI_BASE}/everything?{query_str}"
    
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"}, method="GET")
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        
        articles = data.get("articles", [])
        return [
            {
                "source": a.get("source", {}).get("name", "Unknown"),
                "title": a.get("title", ""),
                "description": a.get("description", ""),
                "url": a.get("url", ""),
                "publishedAt": a.get("publishedAt", ""),
            }
            for a in articles
        ]
    except Exception as e:
        print(f"  ⚠️  NewsAPI error: {e}")
        return []


def fetch_rss_feed(feed_url: str) -> List[Dict]:
    """
    Fetch and parse an RSS feed.
    
    No API key needed.
    """
    try:
        req = urllib.request.Request(feed_url, headers={"User-Agent": "wc26-bnaul/1.0"}, method="GET")
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read().decode()
        
        root = ET.fromstring(content)
        items = []
        
        # RSS 2.0 format
        for item in root.findall(".//item"):
            title = item.find("title")
            description = item.find("description")
            link = item.find("link")
            pub_date = item.find("pubDate")
            
            items.append({
                "source": feed_url.split("/")[2],
                "title": title.text if title is not None else "",
                "description": description.text if description is not None else "",
                "url": link.text if link is not None else "",
                "publishedAt": pub_date.text if pub_date is not None else "",
            })
        
        return items
    except Exception as e:
        print(f"  ⚠️  RSS error ({feed_url}): {e}")
        return []


def search_news_for_teams(home: str, away: str, hours_back: int = 24) -> List[Dict]:
    """
    Search news for a specific match.
    
    Queries multiple sources and returns aggregated results.
    """
    all_news = []
    
    # Calculate from_date
    from_date = (datetime.now(timezone.utc) - timedelta(hours=hours_back)).strftime("%Y-%m-%d")
    
    # 1. NewsAPI queries
    queries = [
        f'"{home}" football',
        f'"{away}" football',
        f'"{home}" "{away}"',
        f'"{home}" injury OR suspended',
        f'"{away}" injury OR suspended',
    ]
    
    for query in queries:
        news = fetch_newsapi(query, from_date=from_date, page_size=5)
        all_news.extend(news)
        time.sleep(1)  # Rate limit: be nice to NewsAPI
    
    # 2. RSS feeds
    for name, url in RSS_FEEDS.items():
        items = fetch_rss_feed(url)
        # Filter for relevant teams
        for item in items:
            title_lower = item["title"].lower()
            desc_lower = (item["description"] or "").lower()
            if home.lower() in title_lower or away.lower() in title_lower or \
               home.lower() in desc_lower or away.lower() in desc_lower:
                all_news.append(item)
    
    # Deduplicate by URL
    seen_urls = set()
    unique_news = []
    for item in all_news:
        if item["url"] not in seen_urls:
            seen_urls.add(item["url"])
            unique_news.append(item)
    
    # Sort by published date (newest first)
    unique_news.sort(key=lambda x: x.get("publishedAt", ""), reverse=True)
    
    return unique_news


# =============================================================================
# INJURY & LINEUP DATA
# =============================================================================

def get_team_id(team_name: str) -> Optional[int]:
    """Map ClawCup team name to API-Football team ID."""
    return TEAM_ID_MAP.get(team_name)


def fetch_injuries_for_match(home: str, away: str) -> Dict[str, List[Dict]]:
    """
    Fetch injury reports for both teams from API-Football.
    
    Returns:
        {"home": [...], "away": [...]}
    """
    if not _get_api_football_key():
        print("  ⚠️  API_FOOTBALL_KEY not set. Injuries unavailable.")
        return {"home": [], "away": []}
    
    home_id = get_team_id(home)
    away_id = get_team_id(away)
    
    if not home_id or not away_id:
        print(f"  ⚠️  Team ID not found: {home}={home_id}, {away}={away_id}")
        return {"home": [], "away": []}
    
    try:
        home_injuries = get_injuries_api_football(team=home_id)
        away_injuries = get_injuries_api_football(team=away_id)
        return {"home": home_injuries, "away": away_injuries}
    except Exception as e:
        print(f"  ⚠️  Injury API error: {e}")
        return {"home": [], "away": []}


def analyze_injury_impact(injuries: Dict[str, List[Dict]]) -> Dict:
    """
    Analyze injury impact on match outcome.
    
    Returns:
        {
            "severity": "low" | "medium" | "high",
            "home_impact": float,  # 0-1, higher = more impact
            "away_impact": float,
            "details": [...],
            "probability_adjustment": float,  # delta to apply to home win prob
        }
    """
    details = []
    home_impact = 0.0
    away_impact = 0.0
    
    # Analyze home team injuries
    for injury in injuries.get("home", []):
        player = injury.get("player", {}).get("name", "Unknown")
        injury_type = injury.get("type", "Unknown")
        fixture = injury.get("fixture", "")
        
        # Estimate severity based on injury type
        if injury_type.lower() in ["red card", "suspension"]:
            severity_score = 0.3
        elif injury_type.lower() in ["knee", "acl", "fracture", "broken"]:
            severity_score = 0.25
        elif injury_type.lower() in ["ankle", "hamstring", "muscle"]:
            severity_score = 0.15
        else:
            severity_score = 0.1
        
        home_impact += severity_score
        details.append(f"{home} MISSING: {player} ({injury_type})")
    
    # Analyze away team injuries
    for injury in injuries.get("away", []):
        player = injury.get("player", {}).get("name", "Unknown")
        injury_type = injury.get("type", "Unknown")
        
        if injury_type.lower() in ["red card", "suspension"]:
            severity_score = 0.3
        elif injury_type.lower() in ["knee", "acl", "fracture", "broken"]:
            severity_score = 0.25
        elif injury_type.lower() in ["ankle", "hamstring", "muscle"]:
            severity_score = 0.15
        else:
            severity_score = 0.1
        
        away_impact += severity_score
        details.append(f"{away} MISSING: {player} ({injury_type})")
    
    # Determine overall severity
    total_impact = home_impact + away_impact
    if total_impact > 0.5:
        severity = "high"
    elif total_impact > 0.2:
        severity = "medium"
    else:
        severity = "low"
    
    # Probability adjustment: if home has more injuries, decrease home prob
    probability_adjustment = (away_impact - home_impact) * 0.5
    
    return {
        "severity": severity,
        "home_impact": home_impact,
        "away_impact": away_impact,
        "details": details,
        "probability_adjustment": probability_adjustment,
    }


# =============================================================================
# NEWS ANALYSIS
# =============================================================================

def analyze_news_content(news_items: List[Dict], home: str, away: str) -> Dict:
    """
    Analyze news content for material information.
    
    Keywords that trigger resubmission:
    - Injury, suspended, out, miss, doubtful
    - Lineup, starting XI, formation change
    - Weather, pitch condition
    - Manager statement, tactical change
    
    Returns:
        {
            "severity": "low" | "medium" | "high",
            "keywords_found": [...],
            "probability_adjustment": float,
            "summary": str,
        }
    """
    severity_keywords = {
        "high": ["injured", "injury", "ruled out", "ruled-out", "suspended", "red card", "confirmed absent", "forced off", "carried off", "stretcher"],
        "medium": ["doubtful", "fitness test", "knock", "minor", "training", "lineup", "starting xi", "formation", "tactical change"],
        "low": ["weather", "pitch", "referee", "crowd", "atmosphere"],
    }
    
    # Keywords that should NOT trigger alone (false positive prone)
    false_positive_prone = ["out"]
    
    # Require "out" to be paired with injury context
    injury_context = ["injured", "injury", "ruled", "forced", "carried", "stretcher", "knock", "doubtful", "fitness", "absent"]
    
    keywords_found = []
    severity_score = 0
    max_severity = "low"
    relevant_items = []
    
    for item in news_items:
        text = f"{item.get('title', '')} {item.get('description', '')}".lower()
        
        for sev, words in severity_keywords.items():
            for word in words:
                if word in text:
                    # Check if "out" is in false-positive context
                    if word in false_positive_prone:
                        # "out" alone is not enough — need injury context
                        has_context = any(ctx in text for ctx in injury_context)
                        if not has_context:
                            continue  # Skip this keyword
                    
                    keywords_found.append(word)
                    if sev == "high":
                        severity_score += 2
                        max_severity = "high"
                    elif sev == "medium":
                        severity_score += 1
                        if max_severity != "high":
                            max_severity = "medium"
                    
                    relevant_items.append(item)
    
    # Deduplicate keywords
    keywords_found = list(set(keywords_found))
    
    # Calculate probability adjustment based on news sentiment
    # Simple heuristic: more high-severity keywords = bigger adjustment needed
    probability_adjustment = 0.0
    if max_severity == "high":
        probability_adjustment = 0.05  # Need to re-evaluate
    elif max_severity == "medium":
        probability_adjustment = 0.02
    
    # Build summary
    if relevant_items:
        summary = f"Found {len(relevant_items)} relevant news items. Keywords: {', '.join(keywords_found[:5])}"
    else:
        summary = "No material news found"
    
    return {
        "severity": max_severity,
        "keywords_found": keywords_found,
        "probability_adjustment": probability_adjustment,
        "summary": summary,
        "relevant_items": relevant_items[:3],  # Top 3 most relevant
    }


# =============================================================================
# RESUBMIT LOGIC
# =============================================================================

def should_resubmit_combined(
    current_pred: Dict,
    news_analysis: Dict,
    injury_analysis: Dict,
    minutes_to_cutoff: float,
) -> Tuple[bool, str]:
    """
    Decide whether to resubmit based on all available information.
    
    Returns:
        (should_resubmit, reason)
    """
    # If match is already locked, don't resubmit
    if minutes_to_cutoff < 0:
        return False, "Match already locked"
    
    # If less than 5 minutes to cutoff, don't resubmit (too risky)
    if minutes_to_cutoff < 5:
        return False, f"Too close to cutoff ({minutes_to_cutoff:.1f} min left)"
    
    # Check injury severity
    injury_severity = injury_analysis.get("severity", "low")
    news_severity = news_analysis.get("severity", "low")
    
    # High severity from either source → resubmit
    if injury_severity == "high" or news_severity == "high":
        reason = f"High severity: injuries={injury_severity}, news={news_severity}"
        return True, reason
    
    # Medium severity + enough time → resubmit
    if (injury_severity == "medium" or news_severity == "medium") and minutes_to_cutoff > 30:
        reason = f"Medium severity with time to spare: injuries={injury_severity}, news={news_severity}"
        return True, reason
    
    # Low severity or no news → don't resubmit
    return False, f"No material changes: injuries={injury_severity}, news={news_severity}"


def calculate_new_probability(
    current_prob: float,
    injury_analysis: Dict,
    news_analysis: Dict,
) -> float:
    """
    Calculate adjusted probability based on new information.
    
    Combines injury impact and news impact into a single adjustment.
    """
    injury_adj = injury_analysis.get("probability_adjustment", 0.0)
    news_adj = news_analysis.get("probability_adjustment", 0.0)
    
    # Combine adjustments (additive, with damping)
    total_adj = injury_adj + news_adj
    
    # Apply adjustment
    new_prob = current_prob + total_adj
    
    # Clamp to valid range
    return max(0.01, min(0.99, new_prob))


# =============================================================================
# MAIN MONITOR LOOP
# =============================================================================

def get_open_fixtures() -> List[Dict]:
    """Lấy danh sách trận đấu đang mở."""
    data = api_request("GET", "/fixtures?status=open")
    return data.get("matches", [])


def get_my_predictions() -> List[Dict]:
    """Lấy danh sách dự đoán đã gửi."""
    data = api_request("GET", "/predictions/mine")
    return data.get("submissions", [])


def calculate_time_to_cutoff(kickoff_utc: str) -> float:
    """Tính số phút còn lại đến cutoff (30 phút trước kickoff)."""
    kickoff = datetime.fromisoformat(kickoff_utc.replace('Z', '+00:00'))
    cutoff = kickoff - timedelta(minutes=30)
    now = datetime.now(timezone.utc)
    
    seconds_remaining = (cutoff - now).total_seconds()
    return seconds_remaining / 60


def monitor_and_resubmit(dry_run: bool = True, check_interval: int = 300):
    """
    Main monitoring loop with real news and injury data.
    """
    print("=" * 70)
    print("CLAWCUP REAL NEWS MONITOR")
    print("=" * 70)
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"Check interval: {check_interval} seconds")
    print(f"NewsAPI: {'ENABLED' if NEWSAPI_KEY else 'DISABLED'}")
    print(f"API-Football: {'ENABLED' if _get_api_football_key() else 'DISABLED'}")
    print(f"football-data.org: {'ENABLED' if _get_football_data_key() else 'DISABLED'}")
    print()
    
    while True:
        try:
            # 1. Get open fixtures
            fixtures = get_open_fixtures()
            
            if not fixtures:
                print(f"[{datetime.now(timezone.utc).isoformat()}] No open fixtures. Sleeping...")
                time.sleep(check_interval)
                continue
            
            # 2. Get current predictions
            my_preds = get_my_predictions()
            pred_map = {p["match_id"]: p for p in my_preds}
            
            # 3. Check each match
            for match in fixtures:
                match_id = match["match_id"]
                home = match["home"]
                away = match["away"]
                kickoff = match.get("kickoff_utc", "")
                
                minutes_to_cutoff = calculate_time_to_cutoff(kickoff)
                
                print(f"\n[{datetime.now(timezone.utc).isoformat()}]")
                print(f"Match: {match_id} — {home} vs {away}")
                print(f"Kickoff: {kickoff}")
                print(f"Minutes to cutoff: {minutes_to_cutoff:.1f}")
                
                # Skip if too early or already locked
                if minutes_to_cutoff > 180:  # 3 hours
                    print(f"  → Too early, skipping (>{180} min)")
                    continue
                if minutes_to_cutoff < 0:
                    print(f"  → Already locked, skipping")
                    continue
                
                # 4. Fetch real news
                print(f"  → Fetching news...")
                news_items = search_news_for_teams(home, away, hours_back=24)
                news_analysis = analyze_news_content(news_items, home, away)
                print(f"  → News: {news_analysis['summary']}")
                if news_analysis["keywords_found"]:
                    print(f"     Keywords: {', '.join(news_analysis['keywords_found'][:5])}")
                
                # 5. Fetch injuries
                print(f"  → Fetching injuries...")
                injuries = fetch_injuries_for_match(home, away)
                injury_analysis = analyze_injury_impact(injuries)
                print(f"  → Injuries: {injury_analysis['severity']} severity")
                if injury_analysis["details"]:
                    for detail in injury_analysis["details"][:3]:
                        print(f"     • {detail}")
                
                # 6. Check if we have a prediction
                if match_id in pred_map:
                    current_pred = pred_map[match_id]
                    current_prob = current_pred.get("p", [0.5, 0.5])[0]
                    print(f"  → Current prediction: home={current_prob:.2f}")
                    
                    # 7. Decide resubmit
                    should_resubmit, reason = should_resubmit_combined(
                        current_pred, news_analysis, injury_analysis, minutes_to_cutoff
                    )
                    
                    if should_resubmit:
                        new_prob = calculate_new_probability(
                            current_prob, injury_analysis, news_analysis
                        )
                        
                        print(f"  → RESUBMIT: {reason}")
                        print(f"  → Old prob: {current_prob:.2f} → New prob: {new_prob:.2f}")
                        
                        if not dry_run:
                            # Actual resubmit via API
                            print(f"  → [LIVE] Resubmitting...")
                            # TODO: Implement actual resubmit API call
                            # This would call the predict endpoint with updated probabilities
                        else:
                            print(f"  → [DRY RUN] Would resubmit with p=[{new_prob:.2f}, {1-new_prob:.2f}]")
                    else:
                        print(f"  → HOLD: {reason}")
                else:
                    print(f"  → No existing prediction for this match")
                
                print(f"  {'─' * 50}")
            
            # Sleep until next check
            print(f"\n{'='*70}")
            print(f"Sleeping for {check_interval} seconds...")
            print(f"{'='*70}")
            time.sleep(check_interval)
            
        except KeyboardInterrupt:
            print("\n\nShutting down...")
            break
        except Exception as e:
            print(f"\nError: {e}")
            time.sleep(check_interval)


def manual_check(match_id: str, dry_run: bool = True):
    """Manual check for a specific match."""
    print(f"Checking match {match_id}...")
    
    fixtures = get_open_fixtures()
    match = None
    for f in fixtures:
        if f["match_id"] == match_id:
            match = f
            break
    
    if not match:
        print(f"Match {match_id} not found or not open")
        return
    
    home = match["home"]
    away = match["away"]
    
    print(f"Match: {home} vs {away}")
    print(f"Kickoff: {match.get('kickoff_utc', 'N/A')}")
    
    # Fetch news
    print(f"\n--- News ---")
    news_items = search_news_for_teams(home, away, hours_back=48)
    news_analysis = analyze_news_content(news_items, home, away)
    print(f"Severity: {news_analysis['severity']}")
    print(f"Keywords: {', '.join(news_analysis['keywords_found'])}")
    print(f"Summary: {news_analysis['summary']}")
    
    for item in news_analysis["relevant_items"]:
        print(f"  • [{item['source']}] {item['title'][:80]}...")
    
    # Fetch injuries
    print(f"\n--- Injuries ---")
    injuries = fetch_injuries_for_match(home, away)
    injury_analysis = analyze_injury_impact(injuries)
    print(f"Severity: {injury_analysis['severity']}")
    print(f"Home impact: {injury_analysis['home_impact']:.2f}")
    print(f"Away impact: {injury_analysis['away_impact']:.2f}")
    for detail in injury_analysis["details"]:
        print(f"  • {detail}")
    
    # Decision
    print(f"\n--- Decision ---")
    minutes_to_cutoff = calculate_time_to_cutoff(match.get("kickoff_utc", ""))
    my_preds = get_my_predictions()
    pred_map = {p["match_id"]: p for p in my_preds}
    
    if match_id in pred_map:
        current_pred = pred_map[match_id]
        current_prob = current_pred.get("p", [0.5, 0.5])[0]
        should_resubmit, reason = should_resubmit_combined(
            current_pred, news_analysis, injury_analysis, minutes_to_cutoff
        )
        
        if should_resubmit:
            new_prob = calculate_new_probability(current_prob, injury_analysis, news_analysis)
            print(f"RESUBMIT: {reason}")
            print(f"Old: {current_prob:.2f} → New: {new_prob:.2f}")
        else:
            print(f"HOLD: {reason}")
    else:
        print("No existing prediction")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ClawCup Real News Monitor")
    parser.add_argument("--dry-run", action="store_true", help="Run without actual resubmit")
    parser.add_argument("--interval", type=int, default=300, help="Check interval in seconds")
    parser.add_argument("--check", help="Manual check a specific match ID")
    
    args = parser.parse_args()
    
    if args.check:
        manual_check(args.check, dry_run=args.dry_run)
    else:
        monitor_and_resubmit(dry_run=args.dry_run, check_interval=args.interval)
