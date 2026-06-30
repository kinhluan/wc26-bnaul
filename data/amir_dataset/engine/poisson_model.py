"""
poisson_model.py
================
Expected Goals (xG) Model — Bivariate Poisson for WC2026
Author: AmirMotefaker
Repo  : https://github.com/AmirMotefaker/ai-football-prediction-engine-world-cup-2026

Computes λ_A and λ_B (expected goals per team) using:
  - Base attack / defense from xG stats
  - Altitude modifier
  - Fatigue / rest days modifier
  - Weather modifier
  - Tournament stage modifier (knockout pressure)
  - Host nation modifier
"""

import json
import math
import os
from typing import Optional


# ---------------------------------------------------------------------------
# Modifier tables
# ---------------------------------------------------------------------------

ALTITUDE_MODIFIERS = {
    "low":     1.00,   # < 500m
    "medium":  1.02,   # 500 – 1499m
    "high":    1.05,   # 1500 – 2199m
    "extreme": 1.12,   # >= 2200m  (e.g. Azteca)
}

WEATHER_MODIFIERS = {
    "mild":         1.00,
    "cool_mild":    1.00,
    "warm":         0.99,
    "warm_coastal": 1.00,
    "warm_humid":   0.98,
    "hot":          0.96,
    "hot_humid":    0.94,
    "extreme_heat": 0.94,
    "mild_highland":1.00,
    "warm_highland":1.00,
}

STAGE_MODIFIERS = {
    "group":        {"goal_factor": 1.00, "draw_bonus": 0.00},
    "round_of_32":  {"goal_factor": 0.96, "draw_bonus": 0.02},
    "round_of_16":  {"goal_factor": 0.94, "draw_bonus": 0.03},
    "quarterfinal": {"goal_factor": 0.93, "draw_bonus": 0.04},
    "semifinal":    {"goal_factor": 0.92, "draw_bonus": 0.05},
    "final":        {"goal_factor": 0.91, "draw_bonus": 0.05},
}

REST_MODIFIERS = {
    # days_since_last_match -> xG multiplier
    "lt3":  0.90,   # < 3 days rest
    "3_5":  0.96,   # 3-5 days rest
    "6+":   1.00,   # 6+ days rest (fully fresh)
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rest_modifier(days: Optional[int]) -> float:
    if days is None:
        return 1.0
    if days < 3:
        return REST_MODIFIERS["lt3"]
    if days <= 5:
        return REST_MODIFIERS["3_5"]
    return REST_MODIFIERS["6+"]


def _altitude_category(altitude_meters: int) -> str:
    if altitude_meters >= 2200:
        return "extreme"
    if altitude_meters >= 1500:
        return "high"
    if altitude_meters >= 500:
        return "medium"
    return "low"


def _altitude_modifier_for_team(altitude_meters: int, team_usual_altitude: int = 0) -> float:
    """
    Only penalise a visiting team if they come from lower altitude.
    If team_usual_altitude is close to venue altitude, effect is reduced.
    """
    venue_cat = _altitude_category(altitude_meters)
    base_mod  = ALTITUDE_MODIFIERS[venue_cat]

    # Acclimatisation discount: if team trains at high altitude natively
    altitude_diff = altitude_meters - team_usual_altitude
    if altitude_diff <= 200:
        return 1.0   # negligible effect
    if altitude_diff <= 800:
        return 1.0 + (base_mod - 1.0) * 0.5   # half effect

    return base_mod


# ---------------------------------------------------------------------------
# Core model
# ---------------------------------------------------------------------------

def compute_lambda(
    xg_for_avg:        float,
    xg_against_avg_opp: float,
    altitude_meters:   int    = 0,
    team_altitude:     int    = 0,
    rest_days:         Optional[int] = None,
    weather_category:  str    = "mild",
    is_host_nation:    bool   = False,
    stage:             str    = "group",
) -> dict:
    """
    Compute expected goals (λ) for ONE team in ONE match.

    Parameters
    ----------
    xg_for_avg          : team's average xG scored per game
    xg_against_avg_opp  : opponent's average xG conceded per game
    altitude_meters     : venue altitude in metres
    team_altitude       : team's home/training altitude (default 0 = sea level)
    rest_days           : days since team's last match
    weather_category    : venue weather string key
    is_host_nation      : True for USA / Canada / Mexico
    stage               : tournament stage string key

    Returns
    -------
    dict with lambda and applied modifiers
    """
    # Base lambda: geometric mean of attack vs opponent defense
    base_lambda = math.sqrt(xg_for_avg * xg_against_avg_opp)

    # Apply modifiers
    alt_mod     = _altitude_modifier_for_team(altitude_meters, team_altitude)
    rest_mod    = _rest_modifier(rest_days)
    weather_mod = WEATHER_MODIFIERS.get(weather_category, 1.0)
    stage_mod   = STAGE_MODIFIERS.get(stage, STAGE_MODIFIERS["group"])["goal_factor"]
    host_mod    = 1.08 if is_host_nation else 1.0

    final_lambda = base_lambda * alt_mod * rest_mod * weather_mod * stage_mod * host_mod
    final_lambda = max(0.20, round(final_lambda, 4))   # floor at 0.20

    return {
        "lambda":       final_lambda,
        "base_lambda":  round(base_lambda, 4),
        "modifiers": {
            "altitude":     round(alt_mod, 4),
            "rest":         round(rest_mod, 4),
            "weather":      round(weather_mod, 4),
            "stage":        round(stage_mod, 4),
            "host_nation":  round(host_mod, 4),
        },
    }


def compute_match_lambdas(
    team_a: dict,
    team_b: dict,
    venue:  dict,
    stage:  str           = "group",
    rest_days_a: Optional[int] = None,
    rest_days_b: Optional[int] = None,
) -> dict:
    """
    High-level wrapper: compute λ_A and λ_B for a full match.

    Parameters
    ----------
    team_a, team_b : team dicts from teams.json
    venue          : venue dict from venues.json
    stage          : tournament stage
    rest_days_a/b  : days since last match for each team

    Returns
    -------
    dict with lambda_a, lambda_b, draw_probability_bonus, and full breakdown
    """
    altitude  = venue.get("altitude_meters", 0)
    weather   = venue.get("weather_category", "mild")

    # Team's home altitude (rough heuristic: host nations assumed near sea level)
    home_alt_a = 2200 if team_a["id"] in ["MEX"] else 0
    home_alt_b = 2200 if team_b["id"] in ["MEX"] else 0

    result_a = compute_lambda(
        xg_for_avg           = team_a["xg_for_avg"],
        xg_against_avg_opp   = team_b["xg_against_avg"],
        altitude_meters      = altitude,
        team_altitude        = home_alt_a,
        rest_days            = rest_days_a,
        weather_category     = weather,
        is_host_nation       = team_a.get("host_nation", False),
        stage                = stage,
    )

    result_b = compute_lambda(
        xg_for_avg           = team_b["xg_for_avg"],
        xg_against_avg_opp   = team_a["xg_against_avg"],
        altitude_meters      = altitude,
        team_altitude        = home_alt_b,
        rest_days            = rest_days_b,
        weather_category     = weather,
        is_host_nation       = team_b.get("host_nation", False),
        stage                = stage,
    )

    draw_bonus = STAGE_MODIFIERS.get(stage, {}).get("draw_bonus", 0.0)

    return {
        "lambda_a":     result_a["lambda"],
        "lambda_b":     result_b["lambda"],
        "draw_bonus":   draw_bonus,
        "team_a":       team_a["name"],
        "team_b":       team_b["name"],
        "venue":        venue.get("common_name", "Unknown"),
        "stage":        stage,
        "detail_a":     result_a,
        "detail_b":     result_b,
    }


# ---------------------------------------------------------------------------
# Poisson probability helpers (used by monte_carlo.py)
# ---------------------------------------------------------------------------

def poisson_pmf(k: int, lam: float) -> float:
    """P(X = k) for Poisson distribution with mean λ."""
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


def scoreline_matrix(lambda_a: float, lambda_b: float,
                     max_goals: int = 8) -> list:
    """
    Return a (max_goals+1) x (max_goals+1) matrix of scoreline probabilities.
    Entry [i][j] = P(Team_A scores i, Team_B scores j).
    """
    matrix = []
    for i in range(max_goals + 1):
        row = []
        for j in range(max_goals + 1):
            row.append(poisson_pmf(i, lambda_a) * poisson_pmf(j, lambda_b))
        matrix.append(row)
    return matrix


def analytical_probabilities(lambda_a: float, lambda_b: float,
                              max_goals: int = 8) -> dict:
    """
    Compute win/draw/loss and market probabilities analytically
    from the Poisson score matrix (no simulation needed).
    """
    matrix = scoreline_matrix(lambda_a, lambda_b, max_goals)

    p_win_a = p_draw = p_win_b = 0.0
    scorelines = []

    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            p = matrix[i][j]
            scorelines.append(((i, j), round(p * 100, 3)))
            if i > j:
                p_win_a += p
            elif i == j:
                p_draw  += p
            else:
                p_win_b += p

    scorelines.sort(key=lambda x: -x[1])

    # Market indicators
    total = lambda_a + lambda_b
    p_over25 = 1 - sum(
        poisson_pmf(k, total) for k in range(3)
    )
    p_over15 = 1 - sum(
        poisson_pmf(k, total) for k in range(2)
    )
    p_btts = (1 - poisson_pmf(0, lambda_a)) * (1 - poisson_pmf(0, lambda_b))
    p_cs_a = poisson_pmf(0, lambda_b)
    p_cs_b = poisson_pmf(0, lambda_a)

    return {
        "win_a":         round(p_win_a * 100, 1),
        "draw":          round(p_draw  * 100, 1),
        "win_b":         round(p_win_b * 100, 1),
        "expected_goals_a": round(lambda_a, 2),
        "expected_goals_b": round(lambda_b, 2),
        "top_scorelines":   scorelines[:10],
        "over_2_5":      round(p_over25 * 100, 1),
        "over_1_5":      round(p_over15 * 100, 1),
        "btts":          round(p_btts   * 100, 1),
        "clean_sheet_a": round(p_cs_a   * 100, 1),
        "clean_sheet_b": round(p_cs_b   * 100, 1),
    }


# ---------------------------------------------------------------------------
# CLI / demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 55)
    print("  WC2026 — Poisson xG Model Demo")
    print("  France vs Morocco — Group I — Estadio Azteca")
    print("=" * 55)

    france  = {"id": "FRA", "name": "France",  "xg_for_avg": 2.31,
               "xg_against_avg": 0.89, "host_nation": False}
    morocco = {"id": "MAR", "name": "Morocco", "xg_for_avg": 1.62,
               "xg_against_avg": 0.88, "host_nation": False}
    azteca  = {"altitude_meters": 2200, "weather_category": "mild_highland",
               "common_name": "Estadio Azteca"}

    result = compute_match_lambdas(
        team_a      = france,
        team_b      = morocco,
        venue       = azteca,
        stage       = "group",
        rest_days_a = 5,
        rest_days_b = 5,
    )

    print(f"\nλ {result['team_a']:<12} = {result['lambda_a']}")
    print(f"λ {result['team_b']:<12} = {result['lambda_b']}")
    print(f"Draw bonus      = +{result['draw_bonus'] * 100:.1f}%")

    probs = analytical_probabilities(result["lambda_a"], result["lambda_b"])
    print(f"\n{'France WIN':<18}: {probs['win_a']}%")
    print(f"{'Draw':<18}: {probs['draw']}%")
    print(f"{'Morocco WIN':<18}: {probs['win_b']}%")
    print(f"\nExpected Goals  : {probs['expected_goals_a']} — {probs['expected_goals_b']}")
    print(f"Over 2.5        : {probs['over_2_5']}%")
    print(f"BTTS            : {probs['btts']}%")
    print(f"\nTop 5 Scorelines:")
    for sc, p in probs["top_scorelines"][:5]:
        print(f"  {sc[0]}-{sc[1]}  →  {p}%")
