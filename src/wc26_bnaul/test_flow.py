#!/usr/bin/env python3
"""
Test Flow Script for wc26-bnaul
Mô phỏng toàn bộ pipeline cho 3 trận đấu.

Usage:
    uv run python -m wc26_bnaul.test_flow --dry-run
    uv run python -m wc26_bnaul.test_flow --live m001 m002 m003
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
                if key not in os.environ:
                    os.environ[key] = value.strip('"')

from wc26_bnaul import api_request
from wc26_bnaul.fifa_data import _api_football_request
from wc26_bnaul.predictor import MatchPredictor


def print_header(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def print_step(step, desc):
    print(f"\n{'─'*70}")
    print(f"  STEP {step}: {desc}")
    print(f"{'─'*70}")


def fetch_match_details(match_id: str):
    """Lấy thông tin trận đấu từ ClawCup API."""
    try:
        data = api_request("GET", f"/fixtures?status=open")
        matches = data.get("matches", [])
        for m in matches:
            if m["match_id"] == match_id:
                return m
        return None
    except Exception as e:
        print(f"  ⚠️  Could not fetch match details: {e}")
        return None


def check_news_api(home: str, away: str):
    """Kiểm tra news qua API-Football (player search)."""
    print_step(2, f"Check News & Players: {home} vs {away}")
    
    # Search for key players from both teams
    players_found = []
    for team in [home, away]:
        try:
            data = _api_football_request("football-players-search", {"search": team[:3]})
            suggestions = data.get("response", {}).get("suggestions", [])
            if suggestions:
                top_players = [s["name"] for s in suggestions[:3]]
                players_found.append(f"{team}: {', '.join(top_players)}")
        except Exception as e:
            print(f"  ⚠️  {team} search error: {e}")
    
    if players_found:
        print("  ✅ Key players found:")
        for p in players_found:
            print(f"     • {p}")
    else:
        print("  ℹ️  No player data available")
    
    return players_found


def run_prediction_model(home: str, away: str):
    """Chạy prediction model."""
    print_step(3, f"Run Prediction Model: {home} vs {away}")
    
    predictor = MatchPredictor()
    
    # Default inputs (có thể cải thiện với real data)
    result = predictor.predict(
        home_team=home,
        away_team=away,
        home_rank=6,  # Giả định
        away_rank=18,  # Giả định
        home_form=[1, 1, 0, 1, 1],
        away_form=[1, 0, 0, 1, 1],
        h2h_home_wins=7,
        h2h_draws=2,
        h2h_away_wins=1,
        home_goals_scored=15,
        home_goals_conceded=4,
        away_goals_scored=8,
        away_goals_conceded=3,
        knockout=True,
    )
    
    binary = result.to_binary()
    
    print(f"  📊 Model Output:")
    print(f"     Home win: {result.home_win_prob:.0%}")
    print(f"     Draw: {result.draw_prob:.0%}")
    print(f"     Away win: {result.away_win_prob:.0%}")
    print(f"     Binary (knockout): Home advance {binary[0]:.2f}, Away advance {binary[1]:.2f}")
    print(f"     Expected score: {result.most_likely_score}")
    print(f"     Confidence: {result.confidence:.0%}")
    
    return binary[0], binary[1], result.most_likely_score


def analyze_and_decide(match_id: str, home: str, away: str, home_prob: float, away_prob: float, score: str, dry_run: bool):
    """Phân tích và quyết định submit."""
    print_step(4, "Analyze & Decide")
    
    print(f"  📋 Submission Summary:")
    print(f"     Match: {match_id} — {home} vs {away}")
    print(f"     Probability: {home_prob:.2f} / {away_prob:.2f}")
    print(f"     Score: {score}")
    
    # Strategy check: truthful submission optimal
    print(f"  🧠 Strategy Check:")
    print(f"     • Truthful submission = optimal under Brier score")
    print(f"     • Over-confidence severely punished")
    print(f"     • Round weight: Ro32 (1×) + Ro16 (1.25×) = 66.7% total")
    
    if dry_run:
        print(f"  🚫 DRY RUN — Would submit:")
        print(f"     uv run wc26-bnaul predict {match_id} \\")
        print(f"       --binary {home_prob:.2f} {away_prob:.2f} \\")
        print(f"       --reasoning 'Auto-generated prediction' \\")
        print(f"       --score {score}")
        return False
    
    # Live mode: confirm with user
    print(f"\n  ⚠️  LIVE MODE — This will submit to ClawCup!")
    confirm = input(f"  Submit prediction for {match_id}? (yes/no): ")
    
    if confirm.lower() in ["yes", "y"]:
        try:
            api_request("POST", "/predictions", {
                "match_id": match_id,
                "p": [round(home_prob, 2), round(away_prob, 2)],
                "reasoning": f"Auto-generated: {home} {home_prob:.0%} vs {away} {away_prob:.0%}",
                "score": score,
            })
            print(f"  ✅ Submitted successfully!")
            return True
        except Exception as e:
            print(f"  ❌ Submit failed: {e}")
            return False
    else:
        print(f"  ❌ Cancelled")
        return False


def run_flow_for_match(match_id: str, dry_run: bool = True):
    """Chạy full pipeline cho 1 trận."""
    print_header(f"MATCH: {match_id}")
    
    # Step 1: Fetch match details
    print_step(1, "Fetch Match Details")
    match = fetch_match_details(match_id)
    
    if not match:
        print(f"  ⚠️  Using default teams (BRAZIL vs JAPAN)")
        home, away = "BRAZIL", "JAPAN"
    else:
        home = match.get("home", "UNKNOWN")
        away = match.get("away", "UNKNOWN")
        kickoff = match.get("kickoff_utc", "UNKNOWN")
        print(f"  ✅ {home} vs {away}")
        print(f"  🕐 Kickoff: {kickoff}")
    
    # Step 2: Check news
    check_news_api(home, away)
    
    # Step 3: Run model
    home_prob, away_prob, score = run_prediction_model(home, away)
    
    # Step 4: Decide & submit
    submitted = analyze_and_decide(match_id, home, away, home_prob, away_prob, score, dry_run)
    
    return {
        "match_id": match_id,
        "home": home,
        "away": away,
        "home_prob": home_prob,
        "away_prob": away_prob,
        "score": score,
        "submitted": submitted,
    }


def main():
    parser = argparse.ArgumentParser(description="Test Prediction Flow")
    parser.add_argument("matches", nargs="*", help="Match IDs to process (e.g., m001 m002 m003)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without submitting")
    parser.add_argument("--live", action="store_true", help="Actually submit predictions")
    
    args = parser.parse_args()
    
    dry_run = not args.live
    
    if not args.matches:
        print("Usage: uv run python -m wc26_bnaul.test_flow [--dry-run|--live] m001 m002 m003")
        print("\nExamples:")
        print("  uv run python -m wc26_bnaul.test_flow --dry-run m001 m002 m003")
        print("  uv run python -m wc26_bnaul.test_flow --live m001")
        sys.exit(1)
    
    print_header("WC26-BNAUL TEST FLOW")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"Matches: {', '.join(args.matches)}")
    print(f"Time: {datetime.now(timezone.utc).isoformat()}")
    
    results = []
    for match_id in args.matches:
        result = run_flow_for_match(match_id, dry_run)
        results.append(result)
    
    # Summary
    print_header("SUMMARY")
    for r in results:
        status = "✅ SUBMITTED" if r["submitted"] else "🚫 DRY RUN"
        print(f"  {r['match_id']}: {r['home']} {r['home_prob']:.2f} vs {r['away']} {r['away_prob']:.2f} — {status}")
    
    print(f"\n{'='*70}")
    print("Flow completed. Review results above.")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
