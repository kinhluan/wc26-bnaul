"""
monte_carlo.py
==============
Monte Carlo Match Simulator for WC2026 AI Prediction Engine
Author: AmirMotefaker
Repo  : https://github.com/AmirMotefaker/ai-football-prediction-engine-world-cup-2026

Runs 10,000 Poisson-sampled match simulations to produce:
  - Win / Draw / Loss probabilities
  - Top 10 most likely scorelines
  - Expected goals with confidence intervals
  - Market indicators (BTTS, Over 2.5, etc.)
  - Upset risk assessment
  - Full confidence & uncertainty quantification
"""

import random
import math
import json
import os
from collections import Counter, defaultdict
from typing import Optional

from poisson_model import (
    compute_match_lambdas,
    analytical_probabilities,
    poisson_pmf,
)
from tsi_calculator import calculate_tsi_from_dict, tsi_gap


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_SIMULATIONS = 10_000
RANDOM_SEED         = 2026          # reproducible results (set None for random)


# ---------------------------------------------------------------------------
# Poisson sampler
# ---------------------------------------------------------------------------

def _poisson_sample(lam: float) -> int:
    """
    Generate a Poisson-distributed random integer with mean λ.
    Uses Knuth's algorithm — suitable for λ up to ~700.
    """
    if lam <= 0:
        return 0
    L = math.exp(-lam)
    k = 0
    p = 1.0
    while p > L:
        k += 1
        p *= random.random()
    return k - 1


# ---------------------------------------------------------------------------
# Core simulation
# ---------------------------------------------------------------------------

def simulate_match(
    lambda_a:   float,
    lambda_b:   float,
    n_sims:     int  = DEFAULT_SIMULATIONS,
    draw_bonus: float = 0.0,
    seed:       Optional[int] = RANDOM_SEED,
) -> dict:
    """
    Run n_sims Monte Carlo match simulations.

    Parameters
    ----------
    lambda_a    : expected goals for Team A
    lambda_b    : expected goals for Team B
    n_sims      : number of iterations (default 10,000)
    draw_bonus  : additive probability bonus applied to draw outcomes
                  (from STAGE_MODIFIERS for knockout rounds)
    seed        : random seed for reproducibility

    Returns
    -------
    dict with probabilities, scorelines, market indicators, confidence
    """
    if seed is not None:
        random.seed(seed)

    wins_a  = 0
    draws   = 0
    wins_b  = 0
    goals_a_total = 0
    goals_b_total = 0
    scoreline_counts = Counter()

    for _ in range(n_sims):
        ga = _poisson_sample(lambda_a)
        gb = _poisson_sample(lambda_b)

        scoreline_counts[(ga, gb)] += 1
        goals_a_total += ga
        goals_b_total += gb

        if ga > gb:
            wins_a += 1
        elif ga == gb:
            draws  += 1
        else:
            wins_b += 1

    total = n_sims

    # Raw probabilities
    p_win_a = wins_a / total
    p_draw  = draws  / total
    p_win_b = wins_b / total

    # Apply draw bonus (re-normalise proportionally from win pools)
    if draw_bonus > 0:
        shift   = draw_bonus / 2          # take equally from both win pools
        p_win_a = max(0, p_win_a - shift)
        p_win_b = max(0, p_win_b - shift)
        p_draw  = min(1, p_draw + draw_bonus)
        # renormalise
        total_p = p_win_a + p_draw + p_win_b
        p_win_a /= total_p
        p_draw  /= total_p
        p_win_b /= total_p

    # Expected goals
    exp_goals_a = goals_a_total / total
    exp_goals_b = goals_b_total / total

    # Top scorelines
    top_scorelines = [
        {"scoreline": f"{sc[0]}-{sc[1]}", "goals_a": sc[0], "goals_b": sc[1],
         "probability": round(cnt / total * 100, 2)}
        for sc, cnt in scoreline_counts.most_common(10)
    ]

    # Market indicators (computed analytically for precision)
    total_lambda = lambda_a + lambda_b
    p_over25 = round((1 - sum(poisson_pmf(k, total_lambda) for k in range(3))) * 100, 1)
    p_over15 = round((1 - sum(poisson_pmf(k, total_lambda) for k in range(2))) * 100, 1)
    p_btts   = round((1 - poisson_pmf(0, lambda_a)) * (1 - poisson_pmf(0, lambda_b)) * 100, 1)
    p_cs_a   = round(poisson_pmf(0, lambda_b) * 100, 1)
    p_cs_b   = round(poisson_pmf(0, lambda_a) * 100, 1)

    # Confidence & uncertainty
    # Agreement = how strongly the model agrees across 3 indicators
    win_margin    = abs(p_win_a - p_win_b)
    max_outcome_p = max(p_win_a, p_draw, p_win_b)

    if max_outcome_p >= 0.55:
        confidence = "HIGH"
    elif max_outcome_p >= 0.40:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    # Standard deviation of goals scored (Poisson: std = sqrt(λ))
    std_a = round(math.sqrt(lambda_a), 3)
    std_b = round(math.sqrt(lambda_b), 3)

    return {
        "simulations":       n_sims,
        "probabilities": {
            "win_a":   round(p_win_a * 100, 1),
            "draw":    round(p_draw  * 100, 1),
            "win_b":   round(p_win_b * 100, 1),
        },
        "expected_goals": {
            "team_a":  round(exp_goals_a, 2),
            "team_b":  round(exp_goals_b, 2),
        },
        "top_scorelines":   top_scorelines,
        "market": {
            "over_2_5":      p_over25,
            "over_1_5":      p_over15,
            "btts":          p_btts,
            "clean_sheet_a": p_cs_a,
            "clean_sheet_b": p_cs_b,
        },
        "confidence": {
            "level":          confidence,
            "max_outcome_p":  round(max_outcome_p * 100, 1),
            "win_margin":     round(win_margin * 100, 1),
            "std_goals_a":    std_a,
            "std_goals_b":    std_b,
        },
    }


# ---------------------------------------------------------------------------
# Full match prediction (end-to-end)
# ---------------------------------------------------------------------------

def predict_match(
    team_a:      dict,
    team_b:      dict,
    venue:       dict,
    stage:       str            = "group",
    rest_days_a: Optional[int]  = None,
    rest_days_b: Optional[int]  = None,
    n_sims:      int            = DEFAULT_SIMULATIONS,
) -> dict:
    """
    Full end-to-end match prediction pipeline.

    Steps:
        1. Compute TSI for both teams
        2. Compute λ_A and λ_B via Poisson model
        3. Run Monte Carlo simulation
        4. Combine into structured output

    Parameters
    ----------
    team_a, team_b : team dicts from teams.json
    venue          : venue dict from venues.json
    stage          : tournament stage
    rest_days_a/b  : days since last match (None = assume 6+)
    n_sims         : Monte Carlo iterations

    Returns
    -------
    Comprehensive prediction dict ready for formatting / API response
    """
    # Step 1 — TSI
    tsi_a   = calculate_tsi_from_dict(team_a)["tsi"]
    tsi_b   = calculate_tsi_from_dict(team_b)["tsi"]
    gap     = tsi_gap(team_a, team_b)

    # Step 2 — Lambdas
    lambda_data = compute_match_lambdas(
        team_a      = team_a,
        team_b      = team_b,
        venue       = venue,
        stage       = stage,
        rest_days_a = rest_days_a,
        rest_days_b = rest_days_b,
    )

    # Step 3 — Monte Carlo
    sim = simulate_match(
        lambda_a    = lambda_data["lambda_a"],
        lambda_b    = lambda_data["lambda_b"],
        n_sims      = n_sims,
        draw_bonus  = lambda_data["draw_bonus"],
    )

    # Step 4 — Assemble
    favourite      = team_a["name"] if tsi_a >= tsi_b else team_b["name"]
    underdog       = team_b["name"] if tsi_a >= tsi_b else team_a["name"]
    most_likely_sc = sim["top_scorelines"][0]["scoreline"] if sim["top_scorelines"] else "N/A"

    probs     = sim["probabilities"]
    if probs["win_a"] > probs["win_b"] and probs["win_a"] > probs["draw"]:
        verdict = team_a["name"]
    elif probs["win_b"] > probs["win_a"] and probs["win_b"] > probs["draw"]:
        verdict = team_b["name"]
    else:
        verdict = "Draw"

    return {
        "match": {
            "team_a":  team_a["name"],
            "team_b":  team_b["name"],
            "stage":   stage,
            "venue":   venue.get("common_name", ""),
            "city":    venue.get("city", ""),
        },
        "tsi": {
            "team_a":       tsi_a,
            "team_b":       tsi_b,
            "gap":          gap["gap"],
            "favourite":    gap["favourite"],
            "underdog":     gap["underdog"],
            "upset_risk":   gap["upset_risk"],
            "risk_level":   gap["risk_level"],
        },
        "lambdas": {
            "team_a":   lambda_data["lambda_a"],
            "team_b":   lambda_data["lambda_b"],
            "modifiers_a": lambda_data["detail_a"]["modifiers"],
            "modifiers_b": lambda_data["detail_b"]["modifiers"],
        },
        "probabilities":   sim["probabilities"],
        "expected_goals":  sim["expected_goals"],
        "top_scorelines":  sim["top_scorelines"],
        "market":          sim["market"],
        "confidence":      sim["confidence"],
        "verdict": {
            "most_likely_winner":   verdict,
            "most_likely_scoreline": most_likely_sc,
            "confidence_level":     sim["confidence"]["level"],
        },
        "environmental": {
            "altitude_m":        venue.get("altitude_meters", 0),
            "altitude_category": venue.get("altitude_category", "low"),
            "weather":           venue.get("weather_category", "mild"),
            "avg_temp_c":        venue.get("avg_temp_june_july_c", 20),
        },
        "simulations_run": n_sims,
    }


# ---------------------------------------------------------------------------
# Pretty printer
# ---------------------------------------------------------------------------

def print_prediction(result: dict) -> None:
    """Print a formatted match prediction to stdout."""
    m   = result["match"]
    t   = result["tsi"]
    p   = result["probabilities"]
    eg  = result["expected_goals"]
    mkt = result["market"]
    v   = result["verdict"]
    c   = result["confidence"]
    env = result["environmental"]

    def bar(pct, width=20):
        filled = int(pct / 100 * width)
        return "█" * filled + "░" * (width - filled)

    print("\n" + "=" * 60)
    print(f"  🏟️  {m['team_a']} vs {m['team_b']}")
    print(f"  📍 {m['venue']}, {m['city']}")
    print(f"  🏆 Stage: {m['stage'].replace('_', ' ').title()}")
    print("=" * 60)

    print(f"\n📊 TEAM STRENGTH INDEX")
    print(f"  {m['team_a']:<20} TSI: {t['team_a']}")
    print(f"  {m['team_b']:<20} TSI: {t['team_b']}")
    print(f"  Gap: {t['gap']} pts  |  Favourite: {t['favourite']}")
    print(f"  Upset Risk: {t['risk_level']}")

    print(f"\n🎯 PROBABILITIES")
    print(f"  {m['team_a']:<18} {p['win_a']:>5}%  {bar(p['win_a'])}")
    print(f"  {'Draw':<18} {p['draw']:>5}%  {bar(p['draw'])}")
    print(f"  {m['team_b']:<18} {p['win_b']:>5}%  {bar(p['win_b'])}")

    print(f"\n⚽ EXPECTED GOALS")
    print(f"  {m['team_a']}: {eg['team_a']}  |  {m['team_b']}: {eg['team_b']}")

    print(f"\n🔢 TOP SCORELINES")
    for sc in result["top_scorelines"][:5]:
        print(f"  {sc['scoreline']}  →  {sc['probability']}%")

    print(f"\n📈 MARKET INDICATORS")
    print(f"  Over 2.5 Goals    : {mkt['over_2_5']}%")
    print(f"  Over 1.5 Goals    : {mkt['over_1_5']}%")
    print(f"  Both Teams Score  : {mkt['btts']}%")
    print(f"  Clean Sheet {m['team_a'][:3]} : {mkt['clean_sheet_a']}%")
    print(f"  Clean Sheet {m['team_b'][:3]} : {mkt['clean_sheet_b']}%")

    print(f"\n🌍 ENVIRONMENT")
    print(f"  Altitude : {env['altitude_m']}m ({env['altitude_category']})")
    print(f"  Weather  : {env['weather']}  ({env['avg_temp_c']}°C)")

    print(f"\n🔮 VERDICT")
    print(f"  Most Likely Winner    : {v['most_likely_winner']}")
    print(f"  Most Likely Scoreline : {v['most_likely_scoreline']}")
    print(f"  Confidence            : {v['confidence_level']}")
    print(f"  Model Variance (σ_A)  : ±{c['std_goals_a']} goals")

    print(f"\n  {'─' * 50}")
    print(f"  ⚠️  Probabilistic model — not betting advice")
    print(f"  Simulations: {result['simulations_run']:,}  |  Engine: WC2026-v2.0")
    print("=" * 60 + "\n")


# ---------------------------------------------------------------------------
# CLI / demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Demo: France vs Morocco at Azteca — Group I
    france  = {
        "id": "FRA", "name": "France",  "group": "I",
        "fifa_rank": 1, "elo_rating": 2045,
        "xg_for_avg": 2.31, "xg_against_avg": 0.89,
        "form_score": 13, "squad_depth_score": 9.5,
        "host_nation": False,
    }
    morocco = {
        "id": "MAR", "name": "Morocco", "group": "C",
        "fifa_rank": 8, "elo_rating": 1985,
        "xg_for_avg": 1.62, "xg_against_avg": 0.88,
        "form_score": 13, "squad_depth_score": 8.5,
        "host_nation": False,
    }
    azteca  = {
        "id": "AZT", "common_name": "Estadio Azteca",
        "city": "Mexico City",
        "altitude_meters": 2200, "altitude_category": "extreme",
        "weather_category": "mild_highland", "avg_temp_june_july_c": 18,
    }

    result = predict_match(
        team_a      = france,
        team_b      = morocco,
        venue       = azteca,
        stage       = "group",
        rest_days_a = 5,
        rest_days_b = 5,
        n_sims      = 10_000,
    )

    print_prediction(result)
