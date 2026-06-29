#!/usr/bin/env python3
"""
ClawCup Historical Backtest — Test strategy on past World Cup data

Sử dụng kết quả World Cup lịch sử để backtest chiến thuật.
"""

import json
import random
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class HistoricalMatch:
    """Một trận đấu lịch sử với kết quả đã biết."""
    year: int
    round: str
    home_team: str
    away_team: str
    home_goals: int
    away_goals: int
    # True probability (estimated from pre-match odds or ELO)
    estimated_home_prob: float


# Historical World Cup knockout results (simplified dataset)
# Source: FIFA World Cup historical results
# True probabilities estimated from pre-match betting odds
HISTORICAL_KNOCKOUTS = [
    # 2022 Qatar World Cup - Round of 16
    HistoricalMatch(2022, "Round of 16", "Netherlands", "USA", 3, 1, 0.65),
    HistoricalMatch(2022, "Round of 16", "Argentina", "Australia", 2, 1, 0.75),
    HistoricalMatch(2022, "Round of 16", "Japan", "Croatia", 1, 1, 0.45),  # Croatia won on pens
    HistoricalMatch(2022, "Round of 16", "Brazil", "South Korea", 4, 1, 0.80),
    HistoricalMatch(2022, "Round of 16", "England", "Senegal", 3, 0, 0.70),
    HistoricalMatch(2022, "Round of 16", "France", "Poland", 3, 1, 0.72),
    HistoricalMatch(2022, "Round of 16", "Morocco", "Spain", 0, 0, 0.35),  # Morocco won on pens
    HistoricalMatch(2022, "Round of 16", "Portugal", "Switzerland", 6, 1, 0.60),
    
    # 2022 - Quarter-finals
    HistoricalMatch(2022, "Quarter-final", "Croatia", "Brazil", 1, 1, 0.25),  # Croatia won on pens
    HistoricalMatch(2022, "Quarter-final", "Netherlands", "Argentina", 2, 2, 0.40),  # Argentina won on pens
    HistoricalMatch(2022, "Quarter-final", "Morocco", "Portugal", 1, 0, 0.30),
    HistoricalMatch(2022, "Quarter-final", "England", "France", 1, 2, 0.45),
    
    # 2022 - Semi-finals
    HistoricalMatch(2022, "Semi-final", "Argentina", "Croatia", 3, 0, 0.60),
    HistoricalMatch(2022, "Semi-final", "France", "Morocco", 2, 0, 0.65),
    
    # 2022 - Final
    HistoricalMatch(2022, "Final", "Argentina", "France", 3, 3, 0.52),  # Argentina won on pens
    
    # 2018 Russia World Cup - Round of 16
    HistoricalMatch(2018, "Round of 16", "France", "Argentina", 4, 3, 0.55),
    HistoricalMatch(2018, "Round of 16", "Uruguay", "Portugal", 2, 1, 0.50),
    HistoricalMatch(2018, "Round of 16", "Spain", "Russia", 1, 1, 0.65),  # Russia won on pens
    HistoricalMatch(2018, "Round of 16", "Croatia", "Denmark", 1, 1, 0.55),  # Croatia won on pens
    HistoricalMatch(2018, "Round of 16", "Brazil", "Mexico", 2, 0, 0.70),
    HistoricalMatch(2018, "Round of 16", "Belgium", "Japan", 3, 2, 0.60),
    HistoricalMatch(2018, "Round of 16", "Sweden", "Switzerland", 1, 0, 0.45),
    HistoricalMatch(2018, "Round of 16", "Colombia", "England", 1, 1, 0.40),  # England won on pens
    
    # 2018 - Quarter-finals
    HistoricalMatch(2018, "Quarter-final", "Uruguay", "France", 0, 2, 0.40),
    HistoricalMatch(2018, "Quarter-final", "Brazil", "Belgium", 1, 2, 0.55),
    HistoricalMatch(2018, "Quarter-final", "Sweden", "England", 0, 2, 0.35),
    HistoricalMatch(2018, "Quarter-final", "Russia", "Croatia", 2, 2, 0.35),  # Croatia won on pens
    
    # 2018 - Semi-finals
    HistoricalMatch(2018, "Semi-final", "France", "Belgium", 1, 0, 0.50),
    HistoricalMatch(2018, "Semi-final", "Croatia", "England", 2, 1, 0.40),
    
    # 2018 - Final
    HistoricalMatch(2018, "Final", "France", "Croatia", 4, 2, 0.55),
    
    # 2014 Brazil World Cup - Round of 16
    HistoricalMatch(2014, "Round of 16", "Brazil", "Chile", 1, 1, 0.60),  # Brazil won on pens
    HistoricalMatch(2014, "Round of 16", "Colombia", "Uruguay", 2, 0, 0.55),
    HistoricalMatch(2014, "Round of 16", "Netherlands", "Mexico", 2, 1, 0.55),
    HistoricalMatch(2014, "Round of 16", "Costa Rica", "Greece", 1, 1, 0.45),  # Costa Rica won on pens
    HistoricalMatch(2014, "Round of 16", "France", "Nigeria", 2, 0, 0.65),
    HistoricalMatch(2014, "Round of 16", "Germany", "Algeria", 2, 1, 0.70),
    HistoricalMatch(2014, "Round of 16", "Argentina", "Switzerland", 1, 0, 0.60),
    HistoricalMatch(2014, "Round of 16", "Belgium", "USA", 2, 1, 0.55),
    
    # 2014 - Quarter-finals
    HistoricalMatch(2014, "Quarter-final", "France", "Germany", 0, 1, 0.45),
    HistoricalMatch(2014, "Quarter-final", "Brazil", "Colombia", 2, 1, 0.55),
    HistoricalMatch(2014, "Quarter-final", "Argentina", "Belgium", 1, 0, 0.50),
    HistoricalMatch(2014, "Quarter-final", "Netherlands", "Costa Rica", 0, 0, 0.55),  # Netherlands won on pens
    
    # 2014 - Semi-finals
    HistoricalMatch(2014, "Semi-final", "Brazil", "Germany", 1, 7, 0.50),
    HistoricalMatch(2014, "Semi-final", "Netherlands", "Argentina", 0, 0, 0.50),  # Argentina won on pens
    
    # 2014 - Final
    HistoricalMatch(2014, "Final", "Germany", "Argentina", 1, 0, 0.50),
]

# Round weights theo ClawCup rules
ROUND_WEIGHTS = {
    "Round of 16": 1.25,
    "Quarter-final": 1.5,
    "Semi-final": 2.0,
    "Final": 3.0,
}


def get_match_outcome(match: HistoricalMatch) -> int:
    """
    Xác định kết quả cho knockout (binary).
    1 = home team advances (win or draw+win on pens)
    0 = away team advances
    
    Lưu ý: Trong lịch sử, có thể hòa sau 90 phút nhưng vẫn có đội đi tiếp.
    Đơn giản hóa: team ghi nhiều bàn hơn (hoặc hòa = home team đi tiếp trong dataset này).
    """
    if match.home_goals > match.away_goals:
        return 1
    elif match.home_goals < match.away_goals:
        return 0
    else:
        # Draw - trong dataset này, đánh dấu đội nào thực sự đi tiếp
        # Đơn giản hóa: giả sử home team đi tiếp nếu họ là favorite
        return 1 if match.estimated_home_prob > 0.5 else 0


def apply_strategy(true_prob: float, strategy: str) -> float:
    """Apply calibration strategy giống như trong simulate.py."""
    if strategy == "truthful":
        return true_prob
    elif strategy == "over_confident":
        if true_prob > 0.5:
            return min(0.99, true_prob + 0.15)
        else:
            return max(0.01, true_prob - 0.15)
    elif strategy == "under_confident":
        return 0.5 + 0.7 * (true_prob - 0.5)
    elif strategy == "max_confident":
        return 0.99 if true_prob > 0.5 else 0.01
    elif strategy == "conservative":
        return 0.55 if true_prob > 0.5 else 0.45
    else:
        raise ValueError(f"Unknown strategy: {strategy}")


def calculate_brier(submitted_prob: float, outcome: int) -> float:
    """Tính Brier score."""
    return (submitted_prob - outcome) ** 2


def calculate_skill_percentage(weighted_rps: float) -> float:
    """Tính Skill% theo ClawCup formula."""
    return (1 - weighted_rps / 0.25) * 100


def backtest_strategy(strategy: str, matches: List[HistoricalMatch]) -> Dict:
    """
    Backtest một strategy trên historical data.
    
    Returns:
        Dict với metrics: skill_pct, mean_rps, weighted_rps, etc.
    """
    briers = []
    weights = []
    predictions = []
    outcomes = []
    
    for match in matches:
        # Submit probability theo strategy
        submitted_prob = apply_strategy(match.estimated_home_prob, strategy)
        
        # Get actual outcome
        outcome = get_match_outcome(match)
        
        # Calculate Brier
        brier = calculate_brier(submitted_prob, outcome)
        weight = ROUND_WEIGHTS.get(match.round, 1.0)
        
        briers.append(brier)
        weights.append(weight)
        predictions.append(submitted_prob)
        outcomes.append(outcome)
    
    # Calculate metrics
    total_weight = sum(weights)
    weighted_rps = sum(b * w for b, w in zip(briers, weights)) / total_weight
    mean_rps = sum(briers) / len(briers)
    skill_pct = calculate_skill_percentage(weighted_rps)
    
    # Accuracy (how often we picked the right team)
    correct_picks = sum(1 for p, o in zip(predictions, outcomes) 
                       if (p > 0.5 and o == 1) or (p < 0.5 and o == 0))
    accuracy = correct_picks / len(outcomes)
    
    return {
        "strategy": strategy,
        "n_matches": len(matches),
        "skill_pct": skill_pct,
        "mean_rps": mean_rps,
        "weighted_rps": weighted_rps,
        "accuracy": accuracy,
        "correct_picks": correct_picks,
        "total_matches": len(matches),
    }


def run_backtest():
    """Chạy backtest cho tất cả strategies."""
    print("=" * 70)
    print("CLAWCUP HISTORICAL BACKTEST")
    print("=" * 70)
    print(f"Dataset: {len(HISTORICAL_KNOCKOUTS)} historical World Cup knockout matches")
    print(f"Years: 2014, 2018, 2022")
    print(f"Rounds: Round of 16, Quarter-final, Semi-final, Final")
    print()
    
    strategies = [
        "truthful",
        "over_confident",
        "under_confident",
        "max_confident",
        "conservative",
    ]
    
    print("-" * 70)
    print(f"{'Strategy':<20} {'Skill%':<10} {'Mean RPS':<12} {'Accuracy':<10} {'Correct'}")
    print("-" * 70)
    
    results = []
    for strategy in strategies:
        result = backtest_strategy(strategy, HISTORICAL_KNOCKOUTS)
        results.append(result)
        
        print(f"{strategy:<20} {result['skill_pct']:>7.2f}%   {result['mean_rps']:>8.4f}    {result['accuracy']:>7.1%}   {result['correct_picks']}/{result['total_matches']}")
    
    # Analysis by round
    print("\n" + "=" * 70)
    print("BREAKDOWN BY ROUND (Truthful strategy)")
    print("=" * 70)
    
    for round_name in ["Round of 16", "Quarter-final", "Semi-final", "Final"]:
        round_matches = [m for m in HISTORICAL_KNOCKOUTS if m.round == round_name]
        if round_matches:
            result = backtest_strategy("truthful", round_matches)
            print(f"{round_name:<20} {result['skill_pct']:>7.2f}%   {result['mean_rps']:>8.4f}    {result['accuracy']:>7.1%}   {result['correct_picks']}/{result['total_matches']}")
    
    # Upset analysis
    print("\n" + "=" * 70)
    print("UPSET ANALYSIS")
    print("=" * 70)
    
    upsets = []
    for match in HISTORICAL_KNOCKOUTS:
        outcome = get_match_outcome(match)
        expected = 1 if match.estimated_home_prob > 0.5 else 0
        if outcome != expected:
            upsets.append(match)
    
    print(f"Total upsets: {len(upsets)}/{len(HISTORICAL_KNOCKOUTS)} ({len(upsets)/len(HISTORICAL_KNOCKOUTS):.1%})")
    print("\nNotable upsets:")
    for match in upsets[:10]:
        outcome = get_match_outcome(match)
        winner = match.home_team if outcome == 1 else match.away_team
        loser = match.away_team if outcome == 1 else match.home_team
        print(f"  {match.year} {match.round}: {winner} beat {loser} ({match.home_goals}-{match.away_goals})")
    
    return results


if __name__ == "__main__":
    run_backtest()
