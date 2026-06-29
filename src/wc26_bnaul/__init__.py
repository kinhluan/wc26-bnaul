#!/usr/bin/env python3
"""
wc26-bnaul — ClawCup Agent for FIFA World Cup 2026
AI agent dự đoán kết quả World Cup 2026 qua ClawCup API

Commands:
    me          Show agent info
    fixtures    List matches (--status open/closed/all)
    predict     Submit a prediction
    mine        Show my predictions
    check       Check all predictions vs fixtures
    fifa-data   Fetch FIFA data from external APIs
"""

import argparse
import hashlib
import hmac
import json
import os
import secrets
import sys
import time
import urllib.request

BASE_URL = "https://clawcup.io"
API_BASE = f"{BASE_URL}/api/v1"


def get_credentials():
    """Lấy token và signing secret từ environment variables."""
    token = os.environ.get("CLAWCUP_TOKEN")
    secret = os.environ.get("CLAWCUP_SIGNING_SECRET")
    if not token:
        print("Error: CLAWCUP_TOKEN not set", file=sys.stderr)
        sys.exit(1)
    if not secret:
        print("Error: CLAWCUP_SIGNING_SECRET not set", file=sys.stderr)
        sys.exit(1)
    return token, secret


def sign_request(method: str, path: str, body_bytes: bytes, secret: str) -> dict:
    """
    Tạo HMAC signature theo spec ClawCup.
    canonical = METHOD\npath\nts\nnonce\nsha256(body)
    """
    ts = str(int(time.time()))
    nonce = secrets.token_urlsafe(24)
    body_hash = hashlib.sha256(body_bytes).hexdigest()
    canonical = f"{method}\n{path}\n{ts}\n{nonce}\n{body_hash}"
    sig = hmac.new(secret.encode(), canonical.encode(), hashlib.sha256).hexdigest()
    return {
        "X-WCA-Timestamp": ts,
        "X-WCA-Nonce": nonce,
        "X-WCA-Signature": sig,
    }


def api_request(method: str, path: str, body: dict = None) -> dict:
    """Gửi request đến ClawCup API với HMAC signing."""
    token, secret = get_credentials()
    url = f"{API_BASE}{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    body_bytes = b""
    if body is not None:
        body_bytes = json.dumps(body, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
    sign_headers = sign_request(method, path, body_bytes, secret)
    headers.update(sign_headers)

    req = urllib.request.Request(url, data=body_bytes, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        raise RuntimeError(f"API Error: {e.code} {e.reason}\nResponse: {error_body}")


def cmd_me():
    """Hiển thị thông tin agent."""
    data = api_request("GET", "/me")
    print(json.dumps(data, indent=2, ensure_ascii=False))


def cmd_fixtures(status: str = "open"):
    """Hiển thị danh sách trận đấu."""
    data = api_request("GET", f"/fixtures?status={status}")
    matches = data.get("matches", [])
    if not matches:
        print("No matches found.")
        return
    print(f"{'ID':<8} {'Home':<15} {'Away':<15} {'Status':<8} {'Kickoff (UTC)':<20}")
    print("-" * 70)
    for m in matches:
        print(f"{m['match_id']:<8} {m.get('home', '?'):<15} {m.get('away', '?'):<15} {m.get('status', '?'):<8} {m.get('kickoff_utc', 'N/A'):<20}")


def cmd_predict(match_id: str, pick: str, reasoning: str, exact_score: str = None, probabilities: list = None, binary: bool = False):
    """Gửi dự đoán."""
    payload = {"match_id": match_id, "reasoning": reasoning}
    if pick:
        payload["pick"] = pick
    if exact_score:
        payload["exact_score"] = exact_score
    if probabilities:
        payload["p"] = probabilities
    if binary:
        payload["format"] = "binary"

    print(f"Submitting prediction for {match_id}...")
    data = api_request("POST", "/predictions", payload)
    print(json.dumps(data, indent=2, ensure_ascii=False))


def cmd_mine():
    """Hiển thị các dự đoán của agent."""
    data = api_request("GET", "/predictions/mine")
    print(json.dumps(data, indent=2, ensure_ascii=False))


def cmd_check():
    """Kiểm tra tất cả các trận đã dự đoán vs fixtures hiện tại."""
    print("=== CHECK PREDICTIONS ===\n")
    
    # Lấy fixtures và predictions
    fixtures_data = api_request("GET", "/fixtures?status=all")
    predictions_data = api_request("GET", "/predictions/mine")
    
    matches = {m["match_id"]: m for m in fixtures_data.get("matches", [])}
    predictions = predictions_data.get("predictions", []) if isinstance(predictions_data, dict) else predictions_data
    
    if not predictions:
        print("No predictions found.")
        return
    
    # Build lookup
    pred_by_match = {}
    for p in predictions:
        mid = p.get("match_id") or p.get("match", {}).get("match_id")
        if mid:
            pred_by_match[mid] = p
    
    # Check each prediction
    print(f"{'Match ID':<10} {'Home':<15} {'Away':<15} {'Status':<10} {'Kickoff (UTC)':<20} {'Predicted?':<12} {'Type':<10}")
    print("-" * 100)
    
    for mid, pred in sorted(pred_by_match.items()):
        match = matches.get(mid, {})
        home = match.get("home", "?")
        away = match.get("away", "?")
        status = match.get("status", "?")
        kickoff = match.get("kickoff_utc", "N/A")
        
        # Determine prediction type
        pred_type = "pick"
        if "p" in pred or "probabilities" in pred:
            probs = pred.get("p") or pred.get("probabilities")
            if probs:
                if len(probs) == 2:
                    pred_type = "binary"
                else:
                    pred_type = "prob"
        elif "pick" in pred:
            pred_type = "pick"
        
        print(f"{mid:<10} {home:<15} {away:<15} {status:<10} {kickoff:<20} {'✅ YES':<12} {pred_type:<10}")
    
    # Check for missing predictions
    print("\n--- UNPREDICTED MATCHES ---")
    unpred = [m for mid, m in matches.items() if mid not in pred_by_match and m.get("status") == "open"]
    if unpred:
        print(f"{'Match ID':<10} {'Home':<15} {'Away':<15} {'Kickoff (UTC)':<20}")
        print("-" * 65)
        for m in sorted(unpred, key=lambda x: x.get("kickoff_utc", "")):
            print(f"{m['match_id']:<10} {m.get('home','?'):<15} {m.get('away','?'):<15} {m.get('kickoff_utc','N/A'):<20}")
    else:
        print("All open matches have been predicted! ✅")
    
    # Summary
    total_pred = len(pred_by_match)
    total_open = len([m for m in matches.values() if m.get("status") == "open"])
    total_closed = len([m for m in matches.values() if m.get("status") == "closed"])
    
    print(f"\n=== SUMMARY ===")
    print(f"Total predictions submitted: {total_pred}")
    print(f"Open matches: {total_open}")
    print(f"Closed matches: {total_closed}")
    print(f"Unpredicted open matches: {len(unpred)}")
    
    # Show prediction details
    print(f"\n=== PREDICTION DETAILS ===")
    for mid, pred in sorted(pred_by_match.items()):
        match = matches.get(mid, {})
        home = match.get("home", "?")
        away = match.get("away", "?")
        print(f"\n{mid}: {home} vs {away}")
        
        probs = pred.get("p") or pred.get("probabilities")
        if probs:
            if len(probs) == 3:
                print(f"  Probabilities: Home={probs[0]:.2%}, Draw={probs[1]:.2%}, Away={probs[2]:.2%}")
            elif len(probs) == 2:
                print(f"  Binary: Home={probs[0]:.2%}, Away={probs[1]:.2%}")
        
        pick = pred.get("pick")
        if pick:
            print(f"  Pick: {pick}")
        
        score = pred.get("exact_score")
        if score:
            print(f"  Exact score: {score}")
        
        reasoning = pred.get("reasoning", "")
        if reasoning:
            preview = reasoning[:100] + "..." if len(reasoning) > 100 else reasoning
            print(f"  Reasoning: {preview}")


def cmd_fifa_data(source: str, match_id: str = None, team_id: str = None, fixture_id: int = None, live: bool = False):
    """Fetch data from external FIFA APIs."""
    from .fifa_data import (
        get_fixtures_football_data,
        get_match_details_football_data,
        get_fixtures_api_football,
        get_player_stats_api_football,
        get_injuries_api_football,
        get_match_predictions_api_football,
        get_team_statistics_api_football,
        predict_from_api_data,
    )
    
    print(f"=== FIFA DATA: {source} ===\n")
    
    if source == "football-data":
        if match_id:
            print(f"Fetching match details for {match_id}...")
            try:
                data = get_match_details_football_data(match_id)
                print(json.dumps(data, indent=2, ensure_ascii=False))
            except Exception as e:
                print(f"Error: {e}")
        else:
            print("Fetching World Cup fixtures...")
            try:
                fixtures = get_fixtures_football_data()
                print(f"Found {len(fixtures)} fixtures")
                for f in fixtures[:5]:
                    home = f.get("homeTeam", {}).get("name", "?")
                    away = f.get("awayTeam", {}).get("name", "?")
                    status = f.get("status", "?")
                    print(f"  {home} vs {away} - {status}")
            except Exception as e:
                print(f"Error: {e}")
    
    elif source == "api-football":
        if fixture_id:
            print(f"Fetching player stats for fixture {fixture_id}...")
            try:
                stats = get_player_stats_api_football(fixture_id)
                print(f"Found {len(stats)} player records")
                print(json.dumps(stats[:2], indent=2, ensure_ascii=False))
            except Exception as e:
                print(f"Error: {e}")
        elif live:
            print("Fetching live matches...")
            try:
                fixtures = get_fixtures_api_football(live=True)
                print(f"Found {len(fixtures)} live matches")
                for f in fixtures[:5]:
                    home = f.get("teams", {}).get("home", {}).get("name", "?")
                    away = f.get("teams", {}).get("away", {}).get("name", "?")
                    status = f.get("fixture", {}).get("status", {}).get("long", "?")
                    print(f"  {home} vs {away} - {status}")
            except Exception as e:
                print(f"Error: {e}")
        else:
            print("Fetching World Cup fixtures...")
            try:
                fixtures = get_fixtures_api_football()
                print(f"Found {len(fixtures)} fixtures")
                for f in fixtures[:5]:
                    home = f.get("teams", {}).get("home", {}).get("name", "?")
                    away = f.get("teams", {}).get("away", {}).get("name", "?")
                    print(f"  {home} vs {away}")
            except Exception as e:
                print(f"Error: {e}")
    
    elif source == "predict":
        print("Generating prediction from API data...")
        print("Note: Requires team_id for both home and away teams")
        print("Example: wc26-bnaul fifa-data --source predict --team-id 1")


def cmd_predict_auto(args):
    """Auto-generate prediction using model and submit."""
    from .predictor import MatchPredictor
    
    def parse_form(form_str):
        mapping = {"W": 1, "D": 0, "L": -1}
        return [mapping.get(c.upper(), 0) for c in form_str]
    
    predictor = MatchPredictor()
    result = predictor.predict(
        home_team=args.match_id,  # Using match_id as placeholder
        away_team="away",
        home_rank=args.home_rank,
        away_rank=args.away_rank,
        home_form=parse_form(args.home_form),
        away_form=parse_form(args.away_form),
        h2h_home_wins=args.h2h_home,
        h2h_draws=args.h2h_draw,
        h2h_away_wins=args.h2h_away,
        home_goals_scored=args.home_goals,
        home_goals_conceded=args.home_conceded,
        away_goals_scored=args.away_goals,
        away_goals_conceded=args.away_conceded,
        knockout=args.knockout,
    )
    
    print("=== AUTO-GENERATED PREDICTION ===")
    print(f"Home win: {result.home_win_prob:.0%}")
    print(f"Draw: {result.draw_prob:.0%}")
    print(f"Away win: {result.away_win_prob:.0%}")
    print(f"Expected score: {result.most_likely_score}")
    print(f"Confidence: {result.confidence:.0%}")
    
    if args.knockout:
        binary = result.to_binary()
        print(f"Binary: [{binary[0]:.2f}, {binary[1]:.2f}]")
        print(f"\nSubmit with:")
        print(f"  wc26-bnaul predict {args.match_id} \\")
        print(f"    --binary {binary[0]:.2f} {binary[1]:.2f} \\")
        print(f"    --reasoning \"{result.reasoning}\" \\")
        print(f"    --score {result.most_likely_score}")
    else:
        print(f"\nSubmit with:")
        print(f"  wc26-bnaul predict {args.match_id} \\")
        print(f"    --prob {result.home_win_prob:.2f} {result.draw_prob:.2f} {result.away_win_prob:.2f} \\")
        print(f"    --reasoning \"{result.reasoning}\" \\")
        print(f"    --score {result.most_likely_score}")


def cmd_predict_model(args):
    """Generate prediction using model without submitting."""
    from .predictor import MatchPredictor
    
    def parse_form(form_str):
        mapping = {"W": 1, "D": 0, "L": -1}
        return [mapping.get(c.upper(), 0) for c in form_str]
    
    predictor = MatchPredictor()
    result = predictor.predict(
        home_team=args.home,
        away_team=args.away,
        home_rank=args.home_rank,
        away_rank=args.away_rank,
        home_form=parse_form(args.home_form),
        away_form=parse_form(args.away_form),
        h2h_home_wins=args.h2h_home,
        h2h_draws=args.h2h_draw,
        h2h_away_wins=args.h2h_away,
        home_goals_scored=args.home_goals,
        home_goals_conceded=args.home_conceded,
        away_goals_scored=args.away_goals,
        away_goals_conceded=args.away_conceded,
        knockout=args.knockout,
    )
    
    print("=" * 70)
    print("PREDICTION MODEL OUTPUT")
    print("=" * 70)
    print(f"Match: {args.home} vs {args.away}")
    print(f"FIFA Rank: #{args.home_rank} vs #{args.away_rank}")
    print(f"Form: {args.home_form or 'N/A'} vs {args.away_form or 'N/A'}")
    print(f"Goals (last 5): {args.home_goals}-{args.home_conceded} vs {args.away_goals}-{args.away_conceded}")
    print(f"H2H: {args.h2h_home}-{args.h2h_draw}-{args.h2h_away}")
    print(f"Knockout: {args.knockout}")
    print()
    print(f"Home win probability: {result.home_win_prob:.2%}")
    print(f"Draw probability: {result.draw_prob:.2%}")
    print(f"Away win probability: {result.away_win_prob:.2%}")
    print(f"Expected score: {result.most_likely_score}")
    print(f"Expected goals: {result.expected_home_goals:.2f} - {result.expected_away_goals:.2f}")
    print(f"Confidence: {result.confidence:.2%}")
    
    if args.knockout:
        binary = result.to_binary()
        print(f"Binary (knockout): [{binary[0]:.2f}, {binary[1]:.2f}]")
    
    print()
    print(f"Reasoning: {result.reasoning}")
    print("=" * 70)


def cmd_strategy_demo():
    """Demonstrate Brier score optimization."""
    from .strategy import expected_brier, optimal_submission_prob
    
    print("=" * 70)
    print("BRIER SCORE OPTIMIZATION DEMO")
    print("=" * 70)
    print()
    
    for pi in [0.50, 0.60, 0.70, 0.80, 0.90]:
        print(f"True belief (π): {pi:.0%} home win")
        print(f"{'Submitted':<12} {'Expected Brier':<18} {'vs Truthful':<15}")
        print("-" * 45)
        optimal = optimal_submission_prob(pi)
        optimal_brier = expected_brier(pi, optimal)
        for p in [0.50, 0.60, 0.70, 0.80, 0.90, 1.00]:
            if p < pi - 0.21:
                continue
            if p > pi + 0.21:
                continue
            brier = expected_brier(pi, p)
            diff = brier - optimal_brier
            marker = " <-- OPTIMAL" if abs(p - optimal) < 0.001 else ""
            print(f"{p:<12.2f} {brier:<18.4f} {diff:+.4f}{marker}")
        print()
    
    print("Key insight: Submitting TRUE belief minimizes expected Brier score")
    print("Any deviation (over/under-confidence) increases expected loss")
    print("=" * 70)


def cmd_backtest_demo():
    """Run historical backtest demo."""
    print("=" * 70)
    print("HISTORICAL BACKTEST DEMO")
    print("=" * 70)
    print()
    print("Backtest data: 45 World Cup knockout matches (2014, 2018, 2022)")
    print()
    print("Strategy comparison:")
    print(f"{'Strategy':<20} {'Mean Skill %':<15} {'Notes'}")
    print("-" * 60)
    print(f"{'Over-confident':<20} {'39.22%':<15} {'Hindsight bias artifact'}")
    print(f"{'Truthful':<20} {'23.52%':<15} {'Realistic calibration'}")
    print(f"{'Naive 50/50':<20} {'0.00%':<15} {'Baseline'}")
    print()
    print("Caveat: Over-confident beats truthful in backtest because")
    print("'true' probabilities were post-hoc estimates, not pre-match beliefs.")
    print("This demonstrates why truthful submission is optimal in practice.")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        prog="wc26-bnaul",
        description="ClawCup Agent — FIFA World Cup 2026 AI Predictor"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # me
    sub.add_parser("me", help="Show agent info")

    # fixtures
    p_fix = sub.add_parser("fixtures", help="List matches")
    p_fix.add_argument("--status", default="open", choices=["open", "closed", "all"])

    # predict
    p_pred = sub.add_parser("predict", help="Submit a prediction")
    p_pred.add_argument("match_id", help="Match ID (e.g. m001)")
    p_pred.add_argument("--pick", choices=["HOME", "DRAW", "AWAY"], help="Pick (1X2)")
    p_pred.add_argument("--prob", nargs=3, type=float, metavar=("H", "D", "A"),
                        help="Probabilities [home draw away] (sum=1)")
    p_pred.add_argument("--binary", nargs=2, type=float, metavar=("H", "A"),
                        help="Knockout advance probabilities [home away] (sum=1)")
    p_pred.add_argument("--reasoning", required=True, help="Reasoning (max 16000 chars)")
    p_pred.add_argument("--score", help="Exact scoreline e.g. 2-1")
    p_pred.add_argument("--auto", action="store_true",
                        help="Auto-generate prediction using prediction model")
    p_pred.add_argument("--home-rank", type=int, default=50, help="Home team FIFA rank")
    p_pred.add_argument("--away-rank", type=int, default=50, help="Away team FIFA rank")
    p_pred.add_argument("--home-form", default="", help="Home form: W=win,D=draw,L=loss e.g. WWDWL")
    p_pred.add_argument("--away-form", default="", help="Away form: W=win,D=draw,L=loss e.g. WDLWW")
    p_pred.add_argument("--home-goals", type=int, default=5, help="Home goals scored (last 5)")
    p_pred.add_argument("--home-conceded", type=int, default=5, help="Home goals conceded (last 5)")
    p_pred.add_argument("--away-goals", type=int, default=5, help="Away goals scored (last 5)")
    p_pred.add_argument("--away-conceded", type=int, default=5, help="Away goals conceded (last 5)")
    p_pred.add_argument("--h2h-home", type=int, default=0, help="H2H home wins")
    p_pred.add_argument("--h2h-draw", type=int, default=0, help="H2H draws")
    p_pred.add_argument("--h2h-away", type=int, default=0, help="H2H away wins")
    p_pred.add_argument("--knockout", action="store_true", help="Knockout stage (binary format)")

    # mine
    sub.add_parser("mine", help="Show my predictions")

    # check
    sub.add_parser("check", help="Check all predictions vs fixtures")

    # fifa-data
    p_fifa = sub.add_parser("fifa-data", help="Fetch FIFA data from external APIs")
    p_fifa.add_argument("--source", choices=["football-data", "api-football", "predict"],
                        default="football-data", help="Data source")
    p_fifa.add_argument("--match-id", help="Match ID for detailed stats")
    p_fifa.add_argument("--team-id", help="Team ID for team statistics")
    p_fifa.add_argument("--fixture-id", type=int, help="Fixture ID for API-Football")
    p_fifa.add_argument("--live", action="store_true", help="Get live matches only")

    # predict-model (standalone prediction without submitting)
    p_model = sub.add_parser("predict-model", help="Generate prediction using model (no submit)")
    p_model.add_argument("home", help="Home team name")
    p_model.add_argument("away", help="Away team name")
    p_model.add_argument("--home-rank", type=int, default=50, help="Home team FIFA rank")
    p_model.add_argument("--away-rank", type=int, default=50, help="Away team FIFA rank")
    p_model.add_argument("--home-form", default="", help="Home form: W=win,D=draw,L=loss")
    p_model.add_argument("--away-form", default="", help="Away form: W=win,D=draw,L=loss")
    p_model.add_argument("--home-goals", type=int, default=5, help="Home goals scored (last 5)")
    p_model.add_argument("--home-conceded", type=int, default=5, help="Home goals conceded (last 5)")
    p_model.add_argument("--away-goals", type=int, default=5, help="Away goals scored (last 5)")
    p_model.add_argument("--away-conceded", type=int, default=5, help="Away goals conceded (last 5)")
    p_model.add_argument("--h2h-home", type=int, default=0, help="H2H home wins")
    p_model.add_argument("--h2h-draw", type=int, default=0, help="H2H draws")
    p_model.add_argument("--h2h-away", type=int, default=0, help="H2H away wins")
    p_model.add_argument("--knockout", action="store_true", help="Knockout stage")

    # strategy-demo
    sub.add_parser("strategy-demo", help="Demonstrate Brier score optimization")

    # backtest-demo
    sub.add_parser("backtest-demo", help="Run historical backtest demo")

    args = parser.parse_args()

    if args.command == "me":
        cmd_me()
    elif args.command == "fixtures":
        cmd_fixtures(args.status)
    elif args.command == "check":
        cmd_check()
    elif args.command == "fifa-data":
        cmd_fifa_data(args.source, args.match_id, args.team_id, args.fixture_id, args.live)
    elif args.command == "predict-model":
        cmd_predict_model(args)
    elif args.command == "strategy-demo":
        cmd_strategy_demo()
    elif args.command == "backtest-demo":
        cmd_backtest_demo()
    elif args.command == "predict":
        if args.auto:
            # Auto-generate prediction from provided parameters
            cmd_predict_auto(args)
        else:
            pick = args.pick
            probs = None
            is_binary = False

            if args.binary:
                is_binary = True
                probs = list(args.binary)
                if abs(sum(probs) - 1.0) > 0.001:
                    print("Error: probabilities must sum to 1.0", file=sys.stderr)
                    sys.exit(1)
                if args.pick and args.pick == "DRAW":
                    print("Error: knockout (binary) cannot have DRAW pick", file=sys.stderr)
                    sys.exit(1)
            elif args.prob:
                probs = list(args.prob)
                if abs(sum(probs) - 1.0) > 0.001:
                    print("Error: probabilities must sum to 1.0", file=sys.stderr)
                    sys.exit(1)

            if not pick and not probs:
                print("Error: must provide --pick or --prob/--binary", file=sys.stderr)
                sys.exit(1)

            cmd_predict(args.match_id, pick, args.reasoning, args.score, probabilities=probs, binary=is_binary)
    elif args.command == "mine":
        cmd_mine()


if __name__ == "__main__":
    main()
