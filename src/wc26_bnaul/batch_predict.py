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


# Team data database (FIFA rank, xG, xGA, typical form)
TEAM_DB = {
    # Top teams
    "Brazil": {"rank": 6, "xg": 2.1, "xga": 0.8, "form": [1, 1, 0, 1, 1]},
    "Argentina": {"rank": 1, "xg": 2.0, "xga": 0.7, "form": [1, 1, 1, 0, 1]},
    "France": {"rank": 2, "xg": 1.9, "xga": 0.9, "form": [1, 0, 1, 1, 1]},
    "Germany": {"rank": 16, "xg": 1.7, "xga": 1.1, "form": [1, 1, 0, 0, 1]},
    "England": {"rank": 5, "xg": 1.8, "xga": 0.9, "form": [1, 1, 1, 0, 1]},
    "Spain": {"rank": 8, "xg": 1.8, "xga": 0.9, "form": [1, 0, 1, 1, 0]},
    "Portugal": {"rank": 7, "xg": 1.7, "xga": 1.0, "form": [1, 1, 0, 1, 0]},
    "Netherlands": {"rank": 7, "xg": 1.6, "xga": 1.0, "form": [0, 1, 0, 1, 1]},
    "Belgium": {"rank": 4, "xg": 1.7, "xga": 1.1, "form": [0, 1, 1, 0, 1]},
    "Italy": {"rank": 9, "xg": 1.6, "xga": 1.0, "form": [1, 0, 1, 0, 1]},
    "USA": {"rank": 11, "xg": 1.4, "xga": 1.2, "form": [1, 0, 1, 1, 0]},
    "Mexico": {"rank": 12, "xg": 1.4, "xga": 1.2, "form": [1, 1, 0, 0, 1]},
    "Switzerland": {"rank": 14, "xg": 1.3, "xga": 1.2, "form": [0, 1, 1, 0, 0]},
    "Croatia": {"rank": 15, "xg": 1.3, "xga": 1.2, "form": [0, 1, 0, 1, 0]},
    "Japan": {"rank": 18, "xg": 1.2, "xga": 1.3, "form": [1, 0, 0, 1, 1]},
    "Senegal": {"rank": 20, "xg": 1.2, "xga": 1.3, "form": [1, 1, 0, 0, 1]},
    "Morocco": {"rank": 11, "xg": 1.1, "xga": 1.3, "form": [0, 1, 0, 1, 1]},
    "Australia": {"rank": 24, "xg": 1.1, "xga": 1.4, "form": [1, 0, 1, 0, 0]},
    "Colombia": {"rank": 17, "xg": 1.3, "xga": 1.2, "form": [1, 0, 1, 1, 0]},
    "Ghana": {"rank": 60, "xg": 0.9, "xga": 1.6, "form": [0, 1, 0, 0, 1]},
    "Ivory Coast": {"rank": 39, "xg": 1.0, "xga": 1.5, "form": [1, 0, 0, 1, 0]},
    "Norway": {"rank": 43, "xg": 1.1, "xga": 1.4, "form": [0, 1, 0, 0, 1]},
    "Sweden": {"rank": 23, "xg": 1.2, "xga": 1.3, "form": [0, 0, 1, 1, 0]},
    "DR Congo": {"rank": 65, "xg": 0.8, "xga": 1.7, "form": [0, 1, 0, 0, 0]},
    "Paraguay": {"rank": 48, "xg": 1.0, "xga": 1.5, "form": [0, 1, 0, 1, 0]},
    "Ecuador": {"rank": 32, "xg": 1.1, "xga": 1.4, "form": [1, 0, 1, 0, 0]},
    "Bosnia & Herzegovina": {"rank": 57, "xg": 0.9, "xga": 1.6, "form": [0, 0, 1, 0, 1]},
    "Austria": {"rank": 25, "xg": 1.2, "xga": 1.3, "form": [1, 0, 0, 1, 1]},
    "Algeria": {"rank": 34, "xg": 1.0, "xga": 1.5, "form": [0, 1, 0, 0, 1]},
    "Egypt": {"rank": 36, "xg": 1.0, "xga": 1.5, "form": [1, 0, 0, 1, 0]},
    "Cape Verde": {"rank": 73, "xg": 0.7, "xga": 1.8, "form": [0, 0, 1, 0, 0]},
    "Canada": {"rank": 38, "xg": 1.0, "xga": 1.5, "form": [1, 1, 0, 0, 0]},
    # Placeholder for unknown teams (W74, W75, etc.)
    "W74": {"rank": 50, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0]},
    "W75": {"rank": 50, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0]},
    "W76": {"rank": 50, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0]},
    "W77": {"rank": 50, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0]},
    "W78": {"rank": 50, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0]},
    "W79": {"rank": 50, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0]},
    "W80": {"rank": 50, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0]},
    "W81": {"rank": 50, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0]},
    "W82": {"rank": 50, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0]},
    "W83": {"rank": 50, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0]},
    "W84": {"rank": 50, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0]},
    "W85": {"rank": 50, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0]},
    "W86": {"rank": 50, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0]},
    "W87": {"rank": 50, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0]},
    "W88": {"rank": 50, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0]},
    "W89": {"rank": 50, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0]},
    "W90": {"rank": 50, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0]},
    "W91": {"rank": 50, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0]},
    "W92": {"rank": 50, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0]},
    "W93": {"rank": 50, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0]},
    "W94": {"rank": 50, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0]},
    "W95": {"rank": 50, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0]},
    "W96": {"rank": 50, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0]},
    "W97": {"rank": 50, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0]},
    "W98": {"rank": 50, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0]},
    "W99": {"rank": 50, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0]},
    "W100": {"rank": 50, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0]},
    "W101": {"rank": 50, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0]},
    "W102": {"rank": 50, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0]},
    "L101": {"rank": 50, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0]},
    "L102": {"rank": 50, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0]},
}


def get_team_data(team_name: str):
    """Get team data from database."""
    return TEAM_DB.get(team_name, {"rank": 50, "xg": 1.0, "xga": 1.5, "form": [0, 0, 0, 0, 0]})


def predict_match(match_id: str, home: str, away: str, predictor: EnsemblePredictor):
    """Run ensemble prediction for a match."""
    home_data = get_team_data(home)
    away_data = get_team_data(away)
    
    result = predictor.predict(
        home_team=home,
        away_team=away,
        home_rank=home_data["rank"],
        away_rank=away_data["rank"],
        home_xg=home_data["xg"],
        home_xga=home_data["xga"],
        away_xg=away_data["xg"],
        away_xga=away_data["xga"],
        home_form=home_data["form"],
        away_form=away_data["form"],
        knockout=True,
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


def submit_prediction(match_id: str, home_prob: float, away_prob: float, score: str, dry_run: bool):
    """Submit prediction to ClawCup API."""
    if dry_run:
        print(f"  🚫 DRY RUN — Would submit: {match_id} — {home_prob:.2f} / {away_prob:.2f}")
        return True
    
    try:
        api_request("POST", f"/predictions/{match_id}", {
            "p": [round(home_prob, 2), round(away_prob, 2)],
            "reasoning": f"Ensemble model: xG + Elo + Betting + Form + H2H + Injury",
            "score": score,
        })
        print(f"  ✅ Submitted: {match_id}")
        return True
    except Exception as e:
        print(f"  ❌ Failed: {match_id} — {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Batch ensemble predictions")
    parser.add_argument("--dry-run", action="store_true", help="Preview without submitting")
    parser.add_argument("--live", action="store_true", help="Actually submit")
    parser.add_argument("--matches", nargs="*", help="Specific match IDs (default: all open)")
    
    args = parser.parse_args()
    
    dry_run = not args.live
    
    print("=" * 70)
    print("BATCH ENSEMBLE PREDICTIONS")
    print("=" * 70)
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"Time: {datetime.now(timezone.utc).isoformat()}")
    print()
    
    # Get matches
    if args.matches:
        match_ids = args.matches
        # Fetch details for each
        data = api_request("GET", "/fixtures?status=open")
        all_matches = {m["match_id"]: m for m in data.get("matches", [])}
        matches = []
        for mid in match_ids:
            if mid in all_matches:
                matches.append(all_matches[mid])
            else:
                print(f"⚠️  Match {mid} not found")
    else:
        data = api_request("GET", "/fixtures?status=open")
        matches = data.get("matches", [])
    
    print(f"Matches to predict: {len(matches)}")
    print()
    
    predictor = EnsemblePredictor()
    results = []
    
    for match in matches:
        match_id = match["match_id"]
        home = match["home"]
        away = match["away"]
        
        print(f"{match_id}: {home} vs {away}")
        
        # Predict
        pred = predict_match(match_id, home, away, predictor)
        
        print(f"  → Ensemble: {pred['home_prob']:.0%} / {pred['away_prob']:.0%}")
        print(f"  → Score: {pred['score']}, Confidence: {pred['confidence']:.0%}")
        
        # Submit
        submitted = submit_prediction(
            match_id,
            pred["home_prob"],
            pred["away_prob"],
            pred["score"],
            dry_run,
        )
        
        results.append({
            **pred,
            "submitted": submitted,
        })
        
        print()
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    submitted_count = sum(1 for r in results if r["submitted"])
    print(f"Total: {len(results)} matches")
    print(f"Submitted: {submitted_count}")
    print(f"Skipped: {len(results) - submitted_count}")
    
    print()
    print("Predictions:")
    for r in results:
        status = "✅" if r["submitted"] else "🚫"
        print(f"  {status} {r['match_id']}: {r['home']} {r['home_prob']:.0%} vs {r['away']} {r['away_prob']:.0%}")
    
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
