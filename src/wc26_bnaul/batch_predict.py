#!/usr/bin/env python3
"""
Batch Ensemble Predictions for all open ClawCup matches.

Usage:
    uv run python -m wc26_bnaul.batch_predict --dry-run    # Preview only
    uv run python -m wc26_bnaul.batch_predict --live         # Actually submit
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

# Load .env
env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                value = value.strip().strip('"').strip("'")
                if key not in os.environ:
                    os.environ[key] = value

from wc26_bnaul import api_request
from wc26_bnaul.ensemble_predictor import EnsemblePredictor
from wc26_bnaul.prediction_logger import PredictionLogger
from wc26_bnaul.json_db import load_json_db, save_json_db

# Initialize logger
logger = PredictionLogger()


# =============================================================================
# TEAM DATA DATABASE — MIGRATED TO JSON
# =============================================================================
# Data moved to data/teams_db.json for easier LLM integration and maintenance.
# TEAM_DB and VENUE_DB are now loaded dynamically from JSON files.
# =============================================================================

def get_team_data(team_name: str) -> dict:
    """Get team data from JSON database."""
    teams = load_json_db("teams_db.json")
    
    if team_name in teams:
        data = teams[team_name]
        # Normalize field names to match what ensemble_predictor expects
        return {
            "rank": data.get("fifa_rank", 50),
            "elo": data.get("elo_rating", 1800),
            "xg": data.get("xg", 1.0),
            "xga": data.get("xga", 1.5),
            "form": data.get("form", [0, 0, 0, 0, 0]),
            "form_score": sum(data.get("form", [0, 0, 0, 0, 0])),
            "squad_depth": data.get("squad_depth_score", 5.0),
            "key_players": [p["name"] for p in data.get("key_players", [])],
            "formation": data.get("coach", {}).get("preferred_formation", "4-3-3"),
            "tactical_style": data.get("coach", {}).get("tactical_style", "balanced"),
            "host_nation": data.get("host_nation", False),
            "confederation": data.get("confederation", "UEFA"),
            "injuries": data.get("injuries", 0),
            "h2h": data.get("h2h", {}),
        }
    
    # Fallback for placeholder teams (W74, W75, etc.)
    if team_name.startswith("W") or team_name.startswith("L"):
        return {
            "rank": 50, "elo": 1800, "xg": 1.0, "xga": 1.5,
            "form": [0, 0, 0, 0, 0], "form_score": 0,
            "squad_depth": 5.0, "key_players": [],
            "formation": "4-3-3", "tactical_style": "balanced",
            "host_nation": False, "confederation": "UEFA",
            "injuries": 0, "h2h": {},
        }
    
    # Unknown team
    print(f"Warning: Team '{team_name}' not found in teams_db.json")
    return {
        "rank": 50, "elo": 1800, "xg": 1.0, "xga": 1.5,
        "form": [0, 0, 0, 0, 0], "form_score": 0,
        "squad_depth": 5.0, "key_players": [],
        "formation": "4-3-3", "tactical_style": "balanced",
        "host_nation": False, "confederation": "UEFA",
        "injuries": 0, "h2h": {},
    }


# =============================================================================
# VENUE DATABASE — MIGRATED TO JSON
# =============================================================================
# Data moved to data/venues_db.json for easier maintenance.
# =============================================================================

def get_venue_data(venue_name: str) -> dict:
    """Get venue data from JSON database."""
    venues = load_json_db("venues_db.json")
    
    # Try exact match first
    if venue_name in venues:
        return venues[venue_name]
    
    # Try partial match
    for vname, vdata in venues.items():
        if vname.lower() in venue_name.lower() or vdata.get("city", "").lower() in venue_name.lower():
            return vdata
    
    # Default fallback
    return {
        "city": "Unknown", "country": "USA",
        "altitude_m": 100, "altitude_category": "low",
        "xg_modifier": 1.0, "avg_temp_c": 22, "humidity_pct": 60,
        "weather_category": "mild", "weather_modifier": 1.0,
        "surface": "natural_grass", "roof": "open", "capacity": 50000,
        "host_nation_venue": True,
    }


def predict_match(match_id: str, home: str, away: str, predictor: EnsemblePredictor, venue: str = ""):
    """Run ensemble prediction for a match with H2H, injury, and venue data."""
    home_data = get_team_data(home)
    away_data = get_team_data(away)
    venue_data = get_venue_data(venue) if venue else get_venue_data("")
    
    # Get H2H and injury data from TEAM_DB
    h2h = home_data.get("h2h", {})
    h2h_key = f"{away}"
    h2h_record = h2h.get(h2h_key, {"home_wins": 0, "draws": 0, "away_wins": 0})
    
    # P0: Debug injury data
    home_injuries = home_data.get("injuries", 0)
    away_injuries = away_data.get("injuries", 0)
    print(f"  [DEBUG] Injuries: {home}={home_injuries}, {away}={away_injuries}")
    
    result = predictor.predict(
        home_team=home,
        away_team=away,
        home_rank=home_data["rank"],
        away_rank=away_data["rank"],
        home_elo=home_data.get("elo", 1800),
        away_elo=away_data.get("elo", 1800),
        home_xg=home_data["xg"],
        home_xga=home_data["xga"],
        away_xg=away_data["xg"],
        away_xga=away_data["xga"],
        home_form=home_data["form"],
        away_form=away_data["form"],
        h2h_home_wins=h2h_record["home_wins"],
        h2h_draws=h2h_record["draws"],
        h2h_away_wins=h2h_record["away_wins"],
        home_injuries=home_injuries,
        away_injuries=away_injuries,
        home_squad_depth=home_data.get("squad_depth", 5.0),
        away_squad_depth=away_data.get("squad_depth", 5.0),
        knockout=True,
        altitude_m=venue_data.get("altitude_m", 0),
        temperature_c=venue_data.get("avg_temp_c", 20),
    )
    
    binary = result.to_binary()
    
    return {
        "match_id": match_id,
        "home": home,
        "away": away,
        "home_prob": binary[0],
        "away_prob": binary[1],
        "score": result.most_likely_score,
        "confidence": result.confidence,
        "components": result.ensemble_components,
    }


def submit_prediction(match_id: str, home_prob: float, away_prob: float, score: str, 
                       dry_run: bool, home: str = "", away: str = "", 
                       components: dict = None, round_name: str = "", weight: float = 1.0):
    """Submit prediction to ClawCup API and log it."""
    if dry_run:
        print(f"  🚫 DRY RUN — Would submit: {match_id} — {home_prob:.2f} / {away_prob:.2f}")
        return True
    
    try:
        api_request("POST", "/predictions", {
            "match_id": match_id,
            "format": "binary",
            "p": [round(home_prob, 2), round(away_prob, 2)],
            "reasoning": f"Ensemble model: ELO + xG + Form + H2H + Squad Depth + Venue",
            "score": score,
        })
        print(f"  ✅ Submitted: {match_id}")
        
        # Log the prediction
        logger.log_prediction(
            match_id=match_id,
            home_team=home,
            away_team=away,
            submitted_probs=[round(home_prob, 2), round(away_prob, 2)],
            components=components or {},
            predicted_score=score,
            reasoning="Ensemble model: ELO + xG + Form + H2H + Squad Depth + Venue",
            round_name=round_name,
            weight=weight,
        )
        
        return True
    except Exception as e:
        print(f"  ❌ Failed: {match_id} — {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Batch ensemble predictions")
    parser.add_argument("--dry-run", action="store_true", help="Preview without submitting")
    parser.add_argument("--live", action="store_true", help="Actually submit")
    
    args = parser.parse_args()
    
    dry_run = not args.live
    
    print("=" * 70)
    print("BATCH ENSEMBLE PREDICTIONS")
    print("=" * 70)
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"Time: {datetime.now(timezone.utc).isoformat()}")
    print()
    
    # Get open fixtures
    try:
        data = api_request("GET", "/fixtures?status=open")
        matches = data.get("matches", [])
    except Exception as e:
        print(f"Error fetching fixtures: {e}")
        return
    
    if not matches:
        print("No open fixtures found")
        return
    
    print(f"Found {len(matches)} open matches")
    print()
    
    predictor = EnsemblePredictor()
    
    for match in matches:
        match_id = match["match_id"]
        home = match.get("home", "?")
        away = match.get("away", "?")
        venue = match.get("venue", "")
        
        # P2: Skip placeholder teams (W74, W75, etc.)
        if home.startswith("W") or away.startswith("W") or home.startswith("L") or away.startswith("L"):
            print(f"Skipping {match_id}: {home} vs {away} — placeholder teams")
            continue
        
        print(f"Predicting {match_id}: {home} vs {away}")
        if venue:
            print(f"  Venue: {venue}")
        
        result = predict_match(match_id, home, away, predictor, venue)
        
        # P0: Selective submission — only submit if there's a clear edge
        home_data = get_team_data(home)
        away_data = get_team_data(away)
        home_elo = home_data.get("elo", 0)
        away_elo = away_data.get("elo", 0)
        elo_gap = abs(home_elo - away_elo) if home_elo > 0 and away_elo > 0 else 0
        
        # Check if match is too close to call (no clear edge)
        prob = result["home_prob"]
        is_close_match = (0.48 <= prob <= 0.52) or elo_gap < 150
        
        if is_close_match:
            print(f"  → CLOSE MATCH: ELO gap={elo_gap}, prob={prob:.2f} — submitting 50/50")
            submit_prediction(
                match_id=match_id,
                home_prob=0.5,
                away_prob=0.5,
                score="1-1",
                dry_run=dry_run,
                home=home,
                away=away,
                components=result["components"],
            )
        else:
            print(f"  Prediction: {home} {result['home_prob']:.0%} vs {away} {result['away_prob']:.0%}")
            print(f"  Score: {result['score']}")
            print(f"  Confidence: {result['confidence']:.0%}")
            
            # Submit
            submit_prediction(
                match_id=match_id,
                home_prob=result["home_prob"],
                away_prob=result["away_prob"],
                score=result["score"],
                dry_run=dry_run,
                home=home,
                away=away,
                components=result["components"],
            )
        
        print()
    
    print("=" * 70)
    print("Batch predictions complete")
    print("=" * 70)


if __name__ == "__main__":
    main()
