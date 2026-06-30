"""
predictor.py
============
OpenAI API Integration for WC2026 AI Prediction Engine
Author: AmirMotefaker
Repo  : https://github.com/AmirMotefaker/ai-football-prediction-engine-world-cup-2026

Connects the full prediction pipeline to GPT-4o via the OpenAI API.
Loads the system prompt, builds the user message, calls the API,
and returns a structured, narrative-rich prediction report.

Usage
-----
    python predictor.py
    python predictor.py --team-a France --team-b Morocco --stage group --venue AZT

Environment
-----------
    Set OPENAI_API_KEY in your environment or in a .env file:
        export OPENAI_API_KEY=sk-...
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional

try:
    from openai import OpenAI
except ImportError:
    print("[!] openai package not found. Run: pip install openai>=1.30.0")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

BASE_DIR        = Path(__file__).resolve().parent.parent
SYSTEM_PROMPT_PATH = BASE_DIR / "system-prompt" / "system_prompt_v2.md"
TEAMS_JSON_PATH    = BASE_DIR / "data" / "teams.json"
VENUES_JSON_PATH   = BASE_DIR / "data" / "venues.json"
ENGINE_DIR         = BASE_DIR / "engine"

# Add engine/ to path so we can import the local modules
sys.path.insert(0, str(ENGINE_DIR))

try:
    from monte_carlo    import predict_match, print_prediction
    from tsi_calculator import calculate_tsi_from_dict
except ImportError as e:
    print(f"[!] Engine import error: {e}")
    print("    Make sure tsi_calculator.py, poisson_model.py and monte_carlo.py")
    print("    are in the engine/ directory.")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Data loaders
# ---------------------------------------------------------------------------

def load_teams() -> dict:
    """Return dict of team_id -> team_dict from teams.json."""
    with open(TEAMS_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {t["id"]: t for t in data["teams"]}


def load_venues() -> dict:
    """Return dict of venue_id -> venue_dict from venues.json."""
    with open(VENUES_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {v["id"]: v for v in data["venues"]}


def load_system_prompt() -> str:
    """Load the system prompt markdown file."""
    with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def find_team(query: str, teams: dict) -> Optional[dict]:
    """
    Find a team by id or partial name match (case-insensitive).
    Returns None if not found.
    """
    q = query.strip().upper()
    # Exact ID match
    if q in teams:
        return teams[q]
    # Partial name match
    q_lower = query.strip().lower()
    for team in teams.values():
        if q_lower in team["name"].lower():
            return team
    return None


def find_venue(query: str, venues: dict) -> Optional[dict]:
    """Find a venue by id or partial name/city match."""
    q = query.strip().upper()
    if q in venues:
        return venues[q]
    q_lower = query.strip().lower()
    for venue in venues.values():
        if (q_lower in venue["common_name"].lower() or
                q_lower in venue["city"].lower() or
                q_lower in venue.get("fifa_name", "").lower()):
            return venue
    return None


# ---------------------------------------------------------------------------
# User message builder
# ---------------------------------------------------------------------------

def build_user_message(
    team_a:         dict,
    team_b:         dict,
    venue:          dict,
    stage:          str,
    match_date:     str             = "2026-06-XX",
    rest_days_a:    Optional[int]   = None,
    rest_days_b:    Optional[int]   = None,
    absence_a:      str             = "none",
    absence_b:      str             = "none",
    local_stats:    Optional[dict]  = None,
) -> str:
    """
    Build the structured user message for the API call,
    injecting pre-computed engine stats for higher accuracy.
    """
    # Pre-compute stats locally for grounding
    tsi_a = calculate_tsi_from_dict(team_a)["tsi"]
    tsi_b = calculate_tsi_from_dict(team_b)["tsi"]

    stats_block = ""
    if local_stats:
        stats_block = f"""
PRE-COMPUTED ENGINE STATS (use as ground truth):
  TSI {team_a['name']}: {local_stats.get('tsi_a', tsi_a)}
  TSI {team_b['name']}: {local_stats.get('tsi_b', tsi_b)}
  λ_A (expected goals {team_a['name']}): {local_stats.get('lambda_a', 'N/A')}
  λ_B (expected goals {team_b['name']}): {local_stats.get('lambda_b', 'N/A')}
  Monte Carlo Win {team_a['name']}: {local_stats.get('win_a', 'N/A')}%
  Monte Carlo Draw: {local_stats.get('draw', 'N/A')}%
  Monte Carlo Win {team_b['name']}: {local_stats.get('win_b', 'N/A')}%
  Top Scoreline: {local_stats.get('top_scoreline', 'N/A')}
  Over 2.5: {local_stats.get('over_25', 'N/A')}%
  BTTS: {local_stats.get('btts', 'N/A')}%
  Upset Risk: {local_stats.get('upset_risk', 'N/A')}
"""

    rest_a_str = f"{rest_days_a} days" if rest_days_a is not None else "unknown"
    rest_b_str = f"{rest_days_b} days" if rest_days_b is not None else "unknown"

    return f"""Predict: {team_a['name']} vs {team_b['name']}
Stage: {stage.replace('_', ' ').title()}
Venue: {venue['common_name']}, {venue['city']}
Date: {match_date}

TEAM DATA:
  {team_a['name']} — FIFA Rank: {team_a['fifa_rank']} | ELO: {team_a['elo_rating']} | xG For: {team_a['xg_for_avg']} | xG Against: {team_a['xg_against_avg']} | Form (last 5): {' '.join(team_a['form_last5'])} | TSI: {tsi_a}
  {team_b['name']} — FIFA Rank: {team_b['fifa_rank']} | ELO: {team_b['elo_rating']} | xG For: {team_b['xg_for_avg']} | xG Against: {team_b['xg_against_avg']} | Form (last 5): {' '.join(team_b['form_last5'])} | TSI: {tsi_b}

Formation A: {team_a.get('typical_formation', 'N/A')} | Tactical Style: {team_a.get('tactical_style', 'N/A')}
Formation B: {team_b.get('typical_formation', 'N/A')} | Tactical Style: {team_b.get('tactical_style', 'N/A')}

Key Players A: {', '.join(team_a.get('key_players', []))}
Key Players B: {', '.join(team_b.get('key_players', []))}

Key Absence A: {absence_a}
Key Absence B: {absence_b}

Days Rest A: {rest_a_str}
Days Rest B: {rest_b_str}

VENUE CONDITIONS:
  Altitude: {venue['altitude_meters']}m ({venue['altitude_category']})
  Weather: {venue['weather_category']} | Avg Temp: {venue.get('avg_temp_june_july_c', 'N/A')}°C | Humidity: {venue.get('avg_humidity_pct', 'N/A')}%
  Surface: {venue.get('surface', 'N/A')} | Roof: {venue.get('roof', 'N/A')}
  Host Nation Venue: {team_a.get('host_nation', False) or team_b.get('host_nation', False)}
{stats_block}
Please produce the full structured prediction report as defined in your system prompt."""


# ---------------------------------------------------------------------------
# API caller
# ---------------------------------------------------------------------------

def call_gpt(
    system_prompt:  str,
    user_message:   str,
    model:          str   = "gpt-4o",
    temperature:    float = 0.3,
    max_tokens:     int   = 2500,
) -> str:
    """
    Call the OpenAI Chat Completions API and return the response text.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "[!] OPENAI_API_KEY not set.\n"
            "    Run: export OPENAI_API_KEY=sk-...\n"
            "    Or add it to a .env file in the project root."
        )

    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model       = model,
        temperature = temperature,
        max_tokens  = max_tokens,
        messages    = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
    )

    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# Main prediction function
# ---------------------------------------------------------------------------

def run_prediction(
    team_a_query:   str,
    team_b_query:   str,
    venue_query:    str             = "MET",
    stage:          str             = "group",
    match_date:     str             = "2026-06-XX",
    rest_days_a:    Optional[int]   = None,
    rest_days_b:    Optional[int]   = None,
    absence_a:      str             = "none",
    absence_b:      str             = "none",
    use_api:        bool            = True,
    n_sims:         int             = 10_000,
) -> None:
    """
    End-to-end prediction runner.

    1. Loads team and venue data
    2. Runs local Python engine (Monte Carlo)
    3. Optionally calls GPT-4o for narrative analysis
    4. Prints results
    """
    print("\n⚙️  Loading data...")
    teams  = load_teams()
    venues = load_venues()

    # Resolve teams
    team_a = find_team(team_a_query, teams)
    team_b = find_team(team_b_query, teams)
    venue  = find_venue(venue_query, venues)

    if not team_a:
        print(f"[!] Team not found: '{team_a_query}'")
        print(f"    Available IDs: {', '.join(sorted(teams.keys()))}")
        return
    if not team_b:
        print(f"[!] Team not found: '{team_b_query}'")
        return
    if not venue:
        print(f"[!] Venue not found: '{venue_query}'")
        print(f"    Available IDs: {', '.join(sorted(venues.keys()))}")
        return

    print(f"✅  Teams: {team_a['name']} vs {team_b['name']}")
    print(f"✅  Venue: {venue['common_name']} ({venue['city']})")
    print(f"✅  Stage: {stage}")

    # ── Step 1: Local Engine ──────────────────────────────────────────────
    print("\n🔢  Running Monte Carlo simulation (10,000 iterations)...")
    local_result = predict_match(
        team_a      = team_a,
        team_b      = team_b,
        venue       = venue,
        stage       = stage,
        rest_days_a = rest_days_a,
        rest_days_b = rest_days_b,
        n_sims      = n_sims,
    )

    print_prediction(local_result)

    # ── Step 2: GPT-4o Narrative (optional) ──────────────────────────────
    if not use_api:
        print("ℹ️  GPT-4o narrative skipped (use_api=False).")
        return

    print("🤖  Calling GPT-4o for tactical narrative analysis...")

    try:
        system_prompt = load_system_prompt()
    except FileNotFoundError:
        print(f"[!] system_prompt_v2.md not found at: {SYSTEM_PROMPT_PATH}")
        print("    Skipping GPT-4o call.")
        return

    probs = local_result["probabilities"]
    mkt   = local_result["market"]
    top_sc = local_result["top_scorelines"][0]["scoreline"] if local_result["top_scorelines"] else "1-1"

    local_stats = {
        "tsi_a":        local_result["tsi"]["team_a"],
        "tsi_b":        local_result["tsi"]["team_b"],
        "lambda_a":     local_result["lambdas"]["team_a"],
        "lambda_b":     local_result["lambdas"]["team_b"],
        "win_a":        probs["win_a"],
        "draw":         probs["draw"],
        "win_b":        probs["win_b"],
        "top_scoreline": top_sc,
        "over_25":      mkt["over_2_5"],
        "btts":         mkt["btts"],
        "upset_risk":   local_result["tsi"]["risk_level"],
    }

    user_message = build_user_message(
        team_a      = team_a,
        team_b      = team_b,
        venue       = venue,
        stage       = stage,
        match_date  = match_date,
        rest_days_a = rest_days_a,
        rest_days_b = rest_days_b,
        absence_a   = absence_a,
        absence_b   = absence_b,
        local_stats = local_stats,
    )

    try:
        gpt_response = call_gpt(
            system_prompt = system_prompt,
            user_message  = user_message,
            temperature   = 0.3,
            max_tokens    = 2500,
        )
        print("\n" + "=" * 60)
        print("  🤖  GPT-4o TACTICAL ANALYSIS")
        print("=" * 60)
        print(gpt_response)
        print("=" * 60)

    except EnvironmentError as e:
        print(e)
    except Exception as e:
        print(f"[!] API call failed: {e}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="WC2026 AI Match Predictor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python predictor.py
  python predictor.py --team-a France --team-b Morocco --venue AZT --stage group
  python predictor.py --team-a ARG --team-b ENG --venue MET --stage semifinal
  python predictor.py --team-a Brazil --team-b Germany --venue LAX --stage final --no-api
        """
    )
    parser.add_argument("--team-a",     default="France",   help="Team A name or ID")
    parser.add_argument("--team-b",     default="Morocco",  help="Team B name or ID")
    parser.add_argument("--venue",      default="AZT",      help="Venue ID or name")
    parser.add_argument("--stage",      default="group",
                        choices=["group", "round_of_32", "round_of_16",
                                 "quarterfinal", "semifinal", "final"],
                        help="Tournament stage")
    parser.add_argument("--date",       default="2026-06-XX", help="Match date YYYY-MM-DD")
    parser.add_argument("--rest-a",     type=int, default=None, help="Rest days Team A")
    parser.add_argument("--rest-b",     type=int, default=None, help="Rest days Team B")
    parser.add_argument("--absence-a",  default="none", help="Key absences Team A")
    parser.add_argument("--absence-b",  default="none", help="Key absences Team B")
    parser.add_argument("--no-api",     action="store_true",
                        help="Run local engine only, skip GPT-4o call")
    parser.add_argument("--sims",       type=int, default=10_000,
                        help="Number of Monte Carlo simulations")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    run_prediction(
        team_a_query = args.team_a,
        team_b_query = args.team_b,
        venue_query  = args.venue,
        stage        = args.stage,
        match_date   = args.date,
        rest_days_a  = args.rest_a,
        rest_days_b  = args.rest_b,
        absence_a    = args.absence_a,
        absence_b    = args.absence_b,
        use_api      = not args.no_api,
        n_sims       = args.sims,
    )
