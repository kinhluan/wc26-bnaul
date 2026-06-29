#!/usr/bin/env python3
"""
Auto-Agent for wc26-bnaul — Fully Autonomous Prediction Agent

Chạy hoàn toàn tự động:
1. Lấy danh sách trận open
2. Với mỗi trận: news → ensemble model → submit
3. Log mọi prediction
4. Không cần user input

Usage:
    uv run python -m wc26_bnaul.auto_agent --dry-run    # Preview only
    uv run python -m wc26_bnaul.auto_agent --live       # Actually submit
    uv run python -m wc26_bnaul.auto_agent --match m074 # Single match
"""

import argparse
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, "src")

from wc26_bnaul import api_request
from wc26_bnaul.ensemble_predictor import EnsemblePredictor
from wc26_bnaul.batch_predict import get_team_data
from wc26_bnaul.prediction_logger import PredictionLogger
from wc26_bnaul.news_monitor_real import (
    search_news_for_teams,
    analyze_news_content,
    fetch_injuries_for_match,
    analyze_injury_impact,
)


logger = PredictionLogger()


def auto_predict_match(match_id: str, home: str, away: str, dry_run: bool = True, check_news: bool = False):
    """
    Fully autonomous prediction for a single match.
    
    Steps:
    1. Fetch news (optional, --news flag)
    2. Run ensemble model
    3. Adjust based on news severity
    4. Submit prediction
    5. Log result
    """
    print(f"\n{'='*60}")
    print(f"AUTO PREDICT: {match_id} — {home} vs {away}")
    print(f"{'='*60}")
    
    # Step 1: Check news (optional)
    print(f"\n[1/4] Checking news...")
    if check_news:
        news = search_news_for_teams(home, away, hours_back=24)
        news_analysis = analyze_news_content(news, home, away)
        print(f"  News severity: {news_analysis['severity']}")
        print(f"  Keywords: {news_analysis['keywords_found']}")
    else:
        news_analysis = {"severity": "low", "keywords_found": [], "probability_adjustment": 0, "summary": "Skipped for speed"}
        print(f"  News: skipped (use --news for full check)")
    
    # Step 2: Check injuries (optional)
    print(f"\n[2/4] Checking injuries...")
    if check_news:
        injuries = fetch_injuries_for_match(home, away)
        injury_analysis = analyze_injury_impact(injuries)
        print(f"  Injury severity: {injury_analysis['severity']}")
        print(f"  Home impact: {injury_analysis['home_impact']:.2f}")
        print(f"  Away impact: {injury_analysis['away_impact']:.2f}")
    else:
        injury_analysis = {"severity": "low", "home_impact": 0, "away_impact": 0, "probability_adjustment": 0}
        print(f"  Injuries: skipped")
    
    # Step 3: Run ensemble model
    print(f"\n[3/4] Running ensemble model...")
    home_data = get_team_data(home)
    away_data = get_team_data(away)
    
    predictor = EnsemblePredictor()
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
    home_prob = binary[0]
    away_prob = binary[1]
    score = result.most_likely_score
    
    print(f"  Base prediction: {home} {home_prob:.0%} vs {away} {away_prob:.0%}")
    print(f"  Score: {score}")
    print(f"  Confidence: {result.confidence:.0%}")
    
    # Step 4: Adjust based on news
    print(f"\n[4/4] Adjusting based on news...")
    news_adjustment = news_analysis.get("probability_adjustment", 0)
    injury_adjustment = injury_analysis.get("probability_adjustment", 0)
    total_adjustment = news_adjustment + injury_adjustment
    
    if total_adjustment != 0:
        home_prob = max(0.01, min(0.99, home_prob + total_adjustment))
        away_prob = 1.0 - home_prob
        print(f"  Adjustment: {total_adjustment:+.2f}")
        print(f"  Adjusted: {home} {home_prob:.0%} vs {away} {away_prob:.0%}")
    else:
        print(f"  No adjustment needed")
    
    # Step 5: Submit
    print(f"\n{'='*60}")
    if dry_run:
        print(f"🚫 DRY RUN — Would submit:")
        print(f"  {match_id}: {home} {home_prob:.2f} vs {away} {away_prob:.2f}")
        print(f"  Score: {score}")
        return True
    
    print(f"🚀 SUBMITTING...")
    try:
        api_request("POST", f"/predictions/{match_id}", {
            "p": [round(home_prob, 2), round(away_prob, 2)],
            "reasoning": f"Auto-agent: {home} {home_prob:.0%} vs {away} {away_prob:.0%} — Ensemble(xG+Elo+Form+H2H) + News({news_analysis['severity']})",
            "score": score,
        })
        
        # Log prediction
        logger.log_prediction(
            match_id=match_id,
            home_team=home,
            away_team=away,
            submitted_probs=[round(home_prob, 2), round(away_prob, 2)],
            components=result.ensemble_components,
            predicted_score=score,
            reasoning=f"Auto-agent with news adjustment: {news_analysis['severity']}",
        )
        
        print(f"  ✅ Submitted: {match_id}")
        return True
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False


def run_auto_agent(dry_run: bool = True, match_id: str = None, check_news: bool = False):
    """Run auto-agent for all open matches or a specific match."""
    print(f"\n{'='*70}")
    print(f"AUTO AGENT — wc26-bnaul")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"News check: {'YES' if check_news else 'NO (fast mode)'}")
    print(f"Time: {datetime.now(timezone.utc).isoformat()}")
    print(f"{'='*70}")
    
    # Get matches
    if match_id:
        data = api_request("GET", "/fixtures?status=open")
        matches = [m for m in data.get("matches", []) if m["match_id"] == match_id]
        if not matches:
            print(f"Match {match_id} not found or not open")
            return
    else:
        data = api_request("GET", "/fixtures?status=open")
        matches = data.get("matches", [])
    
    print(f"Matches to predict: {len(matches)}")
    
    success_count = 0
    for match in matches:
        mid = match["match_id"]
        home = match.get("home", "?")
        away = match.get("away", "?")
        
        if auto_predict_match(mid, home, away, dry_run=dry_run, check_news=check_news):
            success_count += 1
        
        # Rate limit: be nice to API
        time.sleep(0.5)
    
    print(f"\n{'='*70}")
    print(f"SUMMARY: {success_count}/{len(matches)} predictions submitted")
    print(f"{'='*70}")


def main():
    parser = argparse.ArgumentParser(description="Auto-Agent for wc26-bnaul")
    parser.add_argument("--dry-run", action="store_true", help="Preview without submitting")
    parser.add_argument("--live", action="store_true", help="Actually submit")
    parser.add_argument("--match", help="Specific match ID (default: all open)")
    parser.add_argument("--news", action="store_true", help="Check news (slower but more accurate)")
    
    args = parser.parse_args()
    
    dry_run = not args.live
    run_auto_agent(dry_run=dry_run, match_id=args.match, check_news=args.news)


if __name__ == "__main__":
    main()
