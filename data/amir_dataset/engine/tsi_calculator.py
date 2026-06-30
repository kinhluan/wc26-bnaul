"""
tsi_calculator.py
=================
Team Strength Index (TSI) Calculator for WC2026 AI Prediction Engine
Author: AmirMotefaker
Repo  : https://github.com/AmirMotefaker/ai-football-prediction-engine-world-cup-2026

Computes a 0-100 composite score per team using:
  - FIFA World Ranking     (20%)
  - ELO Rating             (25%)
  - xG For avg             (15%)
  - xG Against avg         (15%)
  - Form Score last 5      (15%)
  - Squad Depth Score      (10%)
"""

import json
import os
from typing import Union


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

WEIGHTS = {
    "fifa_rank":        0.20,
    "elo_rating":       0.25,
    "xg_for":          0.15,
    "xg_against":      0.15,   # inverted — lower is better
    "form_score":      0.15,
    "squad_depth":     0.10,
}

# Normalization bounds (based on WC2026 field)
BOUNDS = {
    "fifa_rank":    {"min_val": 1,    "max_val": 90},    # lower rank = stronger
    "elo_rating":   {"min_val": 1650, "max_val": 2100},
    "xg_for":       {"min_val": 0.80, "max_val": 2.50},
    "xg_against":   {"min_val": 0.70, "max_val": 1.70},  # lower = better
    "form_score":   {"min_val": 0,    "max_val": 15},
    "squad_depth":  {"min_val": 4.0,  "max_val": 10.0},
}


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def _normalize(value: float, min_val: float, max_val: float,
               invert: bool = False) -> float:
    """Min-max normalization to [0, 1]. Optionally invert (lower is better)."""
    value   = max(min_val, min(max_val, value))          # clamp
    norm    = (value - min_val) / (max_val - min_val)
    return (1.0 - norm) if invert else norm


def calculate_tsi(
    fifa_rank:    int,
    elo_rating:   float,
    xg_for_avg:   float,
    xg_against_avg: float,
    form_score:   int,
    squad_depth_score: float,
) -> dict:
    """
    Calculate Team Strength Index for a single team.

    Returns
    -------
    dict with keys:
        tsi          : float  — composite score 0-100
        components   : dict   — individual normalized scores
        weights      : dict   — weights applied
    """
    components = {
        "fifa_rank":    _normalize(fifa_rank,          **BOUNDS["fifa_rank"],    invert=True),
        "elo_rating":   _normalize(elo_rating,         **BOUNDS["elo_rating"]),
        "xg_for":       _normalize(xg_for_avg,         **BOUNDS["xg_for"]),
        "xg_against":   _normalize(xg_against_avg,     **BOUNDS["xg_against"],  invert=True),
        "form_score":   _normalize(form_score,         **BOUNDS["form_score"]),
        "squad_depth":  _normalize(squad_depth_score,  **BOUNDS["squad_depth"]),
    }

    raw_tsi = sum(components[k] * WEIGHTS[k] for k in WEIGHTS)
    tsi     = round(raw_tsi * 100, 2)

    return {
        "tsi":        tsi,
        "components": {k: round(v, 4) for k, v in components.items()},
        "weights":    WEIGHTS,
    }


def calculate_tsi_from_dict(team: dict) -> dict:
    """Convenience wrapper — accepts a team dict from teams.json."""
    return calculate_tsi(
        fifa_rank         = team["fifa_rank"],
        elo_rating        = team["elo_rating"],
        xg_for_avg        = team["xg_for_avg"],
        xg_against_avg    = team["xg_against_avg"],
        form_score        = team["form_score"],
        squad_depth_score = team["squad_depth_score"],
    )


# ---------------------------------------------------------------------------
# Batch processing
# ---------------------------------------------------------------------------

def calculate_all_teams(teams_json_path: str) -> list:
    """
    Load teams.json and compute TSI for every team.

    Returns list of dicts sorted by TSI descending.
    """
    with open(teams_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = []
    for team in data["teams"]:
        tsi_result = calculate_tsi_from_dict(team)
        results.append({
            "id":    team["id"],
            "name":  team["name"],
            "group": team["group"],
            "tsi":   tsi_result["tsi"],
            "components": tsi_result["components"],
        })

    results.sort(key=lambda x: x["tsi"], reverse=True)
    return results


def tsi_gap(team_a: dict, team_b: dict) -> dict:
    """
    Compare two team dicts and return TSI gap analysis.

    Parameters
    ----------
    team_a, team_b : team dicts from teams.json

    Returns
    -------
    dict with gap, favourite, upset_risk flag
    """
    tsi_a = calculate_tsi_from_dict(team_a)["tsi"]
    tsi_b = calculate_tsi_from_dict(team_b)["tsi"]
    gap   = abs(tsi_a - tsi_b)

    favourite    = team_a["name"] if tsi_a >= tsi_b else team_b["name"]
    underdog     = team_b["name"] if tsi_a >= tsi_b else team_a["name"]
    upset_risk   = gap < 8.0

    return {
        "tsi_a":       tsi_a,
        "tsi_b":       tsi_b,
        "gap":         round(gap, 2),
        "favourite":   favourite,
        "underdog":    underdog,
        "upset_risk":  upset_risk,
        "risk_level":  "HIGH" if gap < 8 else ("MEDIUM" if gap < 18 else "LOW"),
    }


# ---------------------------------------------------------------------------
# CLI / demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
    TEAMS_JSON     = os.path.join(BASE_DIR, "..", "data", "teams.json")

    print("=" * 55)
    print("  WC2026 — Team Strength Index Rankings")
    print("=" * 55)

    try:
        rankings = calculate_all_teams(TEAMS_JSON)
        print(f"{'Rank':<5} {'Team':<25} {'Group':<7} {'TSI':>6}")
        print("-" * 48)
        for i, r in enumerate(rankings, 1):
            bar = "█" * int(r["tsi"] / 5)
            print(f"{i:<5} {r['name']:<25} {r['group']:<7} {r['tsi']:>6.1f}  {bar}")

    except FileNotFoundError:
        print(f"[!] teams.json not found at: {TEAMS_JSON}")
        print("    Running quick demo with sample data instead...\n")

        # Quick demo — France vs Morocco
        france  = {"fifa_rank": 1, "elo_rating": 2045, "xg_for_avg": 2.31,
                   "xg_against_avg": 0.89, "form_score": 13, "squad_depth_score": 9.5,
                   "name": "France"}
        morocco = {"fifa_rank": 8, "elo_rating": 1985, "xg_for_avg": 1.62,
                   "xg_against_avg": 0.88, "form_score": 13, "squad_depth_score": 8.5,
                   "name": "Morocco"}

        for team in [france, morocco]:
            result = calculate_tsi_from_dict(team)
            print(f"{team['name']}: TSI = {result['tsi']}")
            for k, v in result["components"].items():
                print(f"   {k:<20} {v:.4f}")
            print()

        gap = tsi_gap(france, morocco)
        print(f"TSI Gap      : {gap['gap']}")
        print(f"Favourite    : {gap['favourite']}")
        print(f"Upset Risk   : {gap['upset_risk']} ({gap['risk_level']})")
