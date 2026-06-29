#!/usr/bin/env python3
"""
ClawCup Strategy Engine — Optimal prediction calculator

Tính toán xác suất tối ưu, expected value, và calibration metrics.
"""

import json
import math
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class MatchPrediction:
    """Kết quả dự đoán cho một trận đấu."""
    match_id: str
    home: str
    away: str
    round: str
    home_strength: float
    away_strength: float
    home_prob: float
    away_prob: float
    scoreline: str
    reasoning: str
    expected_brier: float
    confidence: float


# Round weights theo ClawCup rules
ROUND_WEIGHTS = {
    "Round of 32": 1.0,
    "Round of 16": 1.25,
    "Quarter-final": 1.5,
    "Semi-final": 2.0,
    "Final": 3.0,
    "Match for third place": 1.5,  # Giả định
}


def calculate_brier(prob: float, outcome: int) -> float:
    """
    Tính Brier score.
    outcome: 1 = home thắng, 0 = away thắng (knockout)
    """
    return (prob - outcome) ** 2


def expected_brier(true_prob: float, submitted_prob: float) -> float:
    """
    Expected Brier score khi gửi submitted_prob nhưng true_prob là thật.
    
    E[Brier] = true_prob * (submitted_prob - 1)^2 + (1 - true_prob) * submitted_prob^2
    """
    return true_prob * (submitted_prob - 1) ** 2 + (1 - true_prob) * submitted_prob ** 2


def optimal_submission_prob(true_prob: float) -> float:
    """
    Xác suất tối ưu để submit = chính xác suất thật.
    
    Proof: d/dq E[Brier] = 2q - 2p = 0 → q = p
    """
    return true_prob


def calculate_binary_probabilities(home_strength: float, away_strength: float,
                                     home_bonus: float = 0.0, away_bonus: float = 0.0) -> Tuple[float, float]:
    """
    Tính xác suất knockout dựa trên strength + bonus.
    
    Sử dụng logistic function: P(home) = 1 / (1 + 10^(-diff/15))
    """
    effective_home = home_strength + home_bonus
    effective_away = away_strength + away_bonus
    
    diff = effective_home - effective_away
    
    # Logistic with scale factor 15
    home_prob = 1.0 / (1.0 + 10 ** (-diff / 15))
    
    # Clamp để đảm bảo >= 0.01
    home_prob = max(0.01, min(0.99, home_prob))
    away_prob = 1.0 - home_prob
    
    return round(home_prob, 2), round(away_prob, 2)


def calculate_1x2_probabilities(home_strength: float, away_strength: float,
                                 home_bonus: float = 0.0, away_bonus: float = 0.0) -> Tuple[float, float, float]:
    """
    Tính xác suất 1X2 cho group stage.
    
    Returns: (home_win, draw, away_win)
    """
    effective_home = home_strength + home_bonus
    effective_away = away_strength + away_bonus
    
    diff = effective_home - effective_away
    
    # Home win probability (logistic)
    home_win = 1.0 / (1.0 + 10 ** (-diff / 20))
    
    # Draw probability: decreases as |diff| increases
    # Base 25%, min 10%, max 35%
    draw = max(0.10, min(0.35, 0.25 - abs(diff) / 100))
    
    # Adjust home and away to account for draw
    remaining = 1.0 - draw
    home_win = home_win * remaining
    away_win = remaining - home_win
    
    # Normalize
    total = home_win + draw + away_win
    home_win /= total
    draw /= total
    away_win /= total
    
    return round(home_win, 2), round(draw, 2), round(away_win, 2)


def calculate_skill_percentage(mean_rps: float, is_knockout: bool = True) -> float:
    """
    Tính Skill % từ mean RPS.
    
    Knockout: Skill % = (1 - meanRPS / 0.25) * 100
    Group: Skill % = (1 - meanRPS / 0.2222) * 100
    """
    baseline = 0.25 if is_knockout else 0.2222
    return (1.0 - mean_rps / baseline) * 100


def calculate_weighted_rps(predictions: List[Dict]) -> float:
    """
    Tính weighted mean RPS cho knockout predictions.
    
    predictions: list of {match_id, round, brier_score}
    """
    total_weight = 0.0
    weighted_sum = 0.0
    
    for pred in predictions:
        round_name = pred.get("round", "Round of 32")
        weight = ROUND_WEIGHTS.get(round_name, 1.0)
        brier = pred.get("brier_score", 0.25)
        
        weighted_sum += brier * weight
        total_weight += weight
    
    return weighted_sum / total_weight if total_weight > 0 else 0.25


def calibration_analysis(true_probs: List[float], submitted_probs: List[float],
                         outcomes: List[int]) -> Dict:
    """
    Phân tích calibration của model.
    
    Tính:
    - Calibration curve: so sánh predicted vs actual win rate
    - Brier score decomposition: reliability + resolution + uncertainty
    """
    n = len(true_probs)
    if n == 0:
        return {}
    
    # Brier score
    briers = [calculate_brier(sub, out) for sub, out in zip(submitted_probs, outcomes)]
    mean_brier = sum(briers) / n
    
    # Reliability (how close predicted to actual)
    # Group predictions into bins
    bins = {}
    for pred, out in zip(submitted_probs, outcomes):
        bin_idx = int(pred * 10) / 10  # 0.0, 0.1, 0.2, ..., 0.9, 1.0
        if bin_idx not in bins:
            bins[bin_idx] = {"predicted": [], "actual": []}
        bins[bin_idx]["predicted"].append(pred)
        bins[bin_idx]["actual"].append(out)
    
    reliability = 0.0
    for bin_idx, data in bins.items():
        avg_pred = sum(data["predicted"]) / len(data["predicted"])
        avg_actual = sum(data["actual"]) / len(data["actual"])
        reliability += (avg_pred - avg_actual) ** 2 * len(data["predicted"]) / n
    
    # Resolution (how much predictions vary from base rate)
    base_rate = sum(outcomes) / n
    resolution = 0.0
    for bin_idx, data in bins.items():
        avg_actual = sum(data["actual"]) / len(data["actual"])
        resolution += (avg_actual - base_rate) ** 2 * len(data["predicted"]) / n
    
    # Uncertainty (base rate variance)
    uncertainty = base_rate * (1 - base_rate)
    
    return {
        "mean_brier": mean_brier,
        "reliability": reliability,
        "resolution": resolution,
        "uncertainty": uncertainty,
        "base_rate": base_rate,
        "bins": {k: {
            "count": len(v["predicted"]),
            "avg_predicted": sum(v["predicted"]) / len(v["predicted"]),
            "avg_actual": sum(v["actual"]) / len(v["actual"])
        } for k, v in bins.items()}
    }


def generate_optimal_reasoning(home: str, away: str, home_prob: float, away_prob: float,
                                is_knockout: bool = True) -> str:
    """
    Generate reasoning text tối ưu cho submission.
    """
    if is_knockout:
        if home_prob > 0.7:
            return (f"{home} is strongly favored to advance. With a significant "
                    f"strength advantage and higher probability of controlling match "
                    f"tempo, {home} should create more quality chances. "
                    f"Submitted probability {home_prob:.0%} reflects calibrated "
                    f"assessment based on squad quality and tactical matchup.")
        elif home_prob > 0.55:
            return (f"{home} holds a slight edge over {away}. The match is "
                    f"competitive but {home}'s advantages in key areas tilt the "
                    f"balance. Submitted probability {home_prob:.0%} accounts for "
                    f"potential extra time or penalties if {away} defends well.")
        elif home_prob > 0.45:
            return (f"Very evenly matched encounter between {home} and {away}. "
                    f"Either team could advance with small margins deciding. "
                    f"Submitted probability {home_prob:.0%} reflects near "
                    f"coin-flip assessment with slight lean toward {home}.")
        else:
            return (f"{away} is favored despite {home} having home side designation. "
                    f"{away}'s superior squad strength and tactical flexibility give "
                    f"them the edge. Submitted probability {home_prob:.0%} reflects "
                    f"this assessment with {away} more likely to advance.")
    else:
        # Group stage reasoning
        pass


def simulate_scenario(true_prob: float, submitted_prob: float, n_simulations: int = 1000) -> Dict:
    """
    Monte Carlo simulation để so sánh strategies.
    """
    import random
    
    briers = []
    for _ in range(n_simulations):
        outcome = 1 if random.random() < true_prob else 0
        brier = calculate_brier(submitted_prob, outcome)
        briers.append(brier)
    
    return {
        "true_prob": true_prob,
        "submitted_prob": submitted_prob,
        "expected_brier": expected_brier(true_prob, submitted_prob),
        "simulated_mean_brier": sum(briers) / n_simulations,
        "simulated_std_brier": (sum((b - sum(briers)/n_simulations)**2 for b in briers) / n_simulations) ** 0.5,
    }


def compare_strategies(true_prob: float) -> List[Dict]:
    """
    So sánh các strategies khác nhau cho cùng một true_prob.
    """
    strategies = [
        ("Optimal (truthful)", true_prob),
        ("Over-confident (+20%)", min(0.99, true_prob + 0.20)),
        ("Under-confident (-20%)", max(0.01, true_prob - 0.20)),
        ("Max confident (0.99)", 0.99),
        ("Conservative (0.55)", 0.55),
        ("Coin flip (0.50)", 0.50),
    ]
    
    results = []
    for name, submitted in strategies:
        sim = simulate_scenario(true_prob, submitted, n_simulations=10000)
        results.append({
            "strategy": name,
            "submitted_prob": submitted,
            "expected_brier": sim["expected_brier"],
            "simulated_mean_brier": sim["simulated_mean_brier"],
        })
    
    return results


if __name__ == "__main__":
    print("=" * 70)
    print("CLAWCUP STRATEGY ANALYSIS")
    print("=" * 70)
    
    # 1. Demonstrate optimal submission
    print("\n1. OPTIMAL SUBMISSION PROOF")
    print("-" * 70)
    print("If true probability = 0.70, expected Brier for different submissions:")
    for q in [0.50, 0.60, 0.70, 0.80, 0.90, 0.99]:
        eb = expected_brier(0.70, q)
        print(f"  Submit {q:.2f} → Expected Brier = {eb:.4f}")
    print(f"  → Optimal: submit 0.70 (minimum expected Brier)")
    
    # 2. Compare strategies
    print("\n2. STRATEGY COMPARISON (true_prob = 0.70)")
    print("-" * 70)
    results = compare_strategies(0.70)
    for r in results:
        print(f"  {r['strategy']:25s} | Brier: {r['expected_brier']:.4f}")
    
    # 3. Round weights analysis
    print("\n3. ROUND WEIGHTS ANALYSIS")
    print("-" * 70)
    rounds = [
        ("Round of 32", 16, 1.0),
        ("Round of 16", 8, 1.25),
        ("Quarter-final", 4, 1.5),
        ("Semi-final", 2, 2.0),
        ("Final", 1, 3.0),
    ]
    total_weight = sum(n * w for _, n, w in rounds)
    for name, n_matches, weight in rounds:
        contribution = n_matches * weight / total_weight * 100
        print(f"  {name:20s} | {n_matches:2d} matches × {weight:.2f} = {n_matches*weight:5.1f} weight ({contribution:5.1f}%)")
    print(f"  {'Total':20s} | {sum(n for _, n, _ in rounds):2d} matches    = {total_weight:5.1f} weight (100.0%)")
    
    # 4. Skill % calculation
    print("\n4. SKILL % EXAMPLES")
    print("-" * 70)
    for rps in [0.10, 0.15, 0.20, 0.2222, 0.25]:
        skill = calculate_skill_percentage(rps, is_knockout=True)
        print(f"  Mean RPS = {rps:.4f} → Skill % = {skill:6.1f}%")
    
    print("\n" + "=" * 70)
