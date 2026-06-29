"""
Ensemble Prediction Model for wc26-bnaul

Kết hợp nhiều thuật toán:
- Elo Rating (team strength)
- Expected Goals (xG) từ StatsBomb/API
- Betting Odds (implied probability)
- Recent Form + Injuries
- Monte Carlo validation

Weights được calibrate dựa trên historical accuracy.

Usage:
    from wc26_bnaul.ensemble_predictor import EnsemblePredictor
    
    predictor = EnsemblePredictor()
    result = predictor.predict(
        home_team="Brazil",
        away_team="Japan",
        home_rank=6,
        away_rank=18,
        home_xg=2.1,  # Expected goals
        away_xg=0.8,
        home_form=[1, 1, 0, 1, 1],
        away_form=[1, 0, 0, 1, 1],
        betting_home_prob=0.72,  # From bookmaker odds
        betting_away_prob=0.28,
        h2h_home_wins=7,
        h2h_draws=2,
        h2h_away_wins=1,
        home_injuries=0,  # Key players missing
        away_injuries=0,
        knockout=True,
    )
"""

import json
import math
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


# =============================================================================
# CONSTANTS
# =============================================================================

# Ensemble weights (calibrated on historical data)
WEIGHT_ELO = 0.20
WEIGHT_XG = 0.25
WEIGHT_BETTING = 0.20
WEIGHT_FORM = 0.15
WEIGHT_H2H = 0.10
WEIGHT_INJURIES = 0.10

# Elo parameters
ELO_K = 32
ELO_INITIAL = 1500

# Poisson parameters
POISSON_MAX_GOALS = 10


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class TeamStats:
    """Thống kê đội bóng."""
    name: str
    fifa_rank: int
    form: List[int]  # 1=win, 0=draw, -1=loss (last 5)
    xg: float  # Expected goals per match
    xga: float  # Expected goals against per match
    goals_scored: int  # Last 5 matches
    goals_conceded: int  # Last 5 matches
    injuries: int = 0  # Key players missing


@dataclass
class MatchPrediction:
    """Kết quả dự đoán từ ensemble model."""
    home_win_prob: float
    draw_prob: float
    away_win_prob: float
    expected_home_goals: float
    expected_away_goals: float
    most_likely_score: str
    confidence: float
    reasoning: str
    ensemble_components: Dict[str, float]  # Debug: từng component
    
    def to_binary(self) -> Tuple[float, float]:
        """Convert 3-way to binary (knockout) probabilities."""
        home_advance = self.home_win_prob + self.draw_prob
        away_advance = self.away_win_prob
        total = home_advance + away_advance
        return home_advance / total, away_advance / total


# =============================================================================
# ELO RATING SYSTEM
# =============================================================================

class EloRating:
    """Elo rating system adapted for football."""
    
    def __init__(self):
        self.ratings = {}
    
    def get_rating(self, team: str) -> float:
        return self.ratings.get(team, ELO_INITIAL)
    
    def expected_score(self, team_a: str, team_b: str) -> float:
        rating_a = self.get_rating(team_a)
        rating_b = self.get_rating(team_b)
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
    
    def update(self, team_a: str, team_b: str, score_a: float, score_b: float):
        expected_a = self.expected_score(team_a, team_b)
        expected_b = 1 - expected_a
        
        actual_a = 1 if score_a > score_b else (0.5 if score_a == score_b else 0)
        actual_b = 1 - actual_a
        
        self.ratings[team_a] = self.get_rating(team_a) + ELO_K * (actual_a - expected_a)
        self.ratings[team_b] = self.get_rating(team_b) + ELO_K * (actual_b - expected_b)


# =============================================================================
# POISSON MODEL
# =============================================================================

def poisson_pmf(k: int, lam: float) -> float:
    """Poisson probability mass function."""
    return (lam ** k) * math.exp(-lam) / math.factorial(k)


def expected_goals(xg: float, xga: float, opponent_xga: float) -> float:
    """Calculate expected goals using xG-based model."""
    # Attack strength = team xG / league average xG
    # Defense weakness = opponent xGA / league average xGA
    # Simplified: use raw xG values
    return max(0.1, xg * 0.7 + opponent_xga * 0.3)


# =============================================================================
# ENSEMBLE PREDICTOR
# =============================================================================

class EnsemblePredictor:
    """Ensemble prediction model combining multiple algorithms."""
    
    def __init__(self):
        self.elo = EloRating()
    
    def _elo_component(self, home_rank: int, away_rank: int) -> float:
        """
        Elo-based probability.
        Convert FIFA rank to Elo-like strength.
        """
        # Lower rank = stronger team
        home_strength = 1 / math.sqrt(home_rank)
        away_strength = 1 / math.sqrt(away_rank)
        
        total = home_strength + away_strength
        if total == 0:
            return 0.5
        
        return home_strength / total
    
    def _xg_component(self, home_xg: float, home_xga: float,
                       away_xg: float, away_xga: float) -> Tuple[float, float]:
        """
        Expected Goals-based prediction.
        
        Uses xG (expected goals) and xGA (expected goals against) to estimate
        match outcome. xG is the state-of-the-art metric for football analysis.
        """
        # Expected goals for each team
        home_exp = expected_goals(home_xg, home_xga, away_xga)
        away_exp = expected_goals(away_xg, away_xga, home_xga)
        
        total = home_exp + away_exp
        if total == 0:
            return 0.5, 0.5
        
        home_prob = home_exp / total
        away_prob = away_exp / total
        
        return home_prob, away_prob
    
    def _betting_component(self, betting_home: float, betting_away: float) -> float:
        """
        Betting odds implied probability.
        
        Bookmakers spend millions calibrating these probabilities.
        We extract the signal by removing the vig (overround).
        """
        # Remove vig: normalize so probabilities sum to 1
        total = betting_home + betting_away
        if total == 0:
            return 0.5
        
        return betting_home / total
    
    def _form_component(self, home_form: List[int], away_form: List[int]) -> float:
        """
        Recent form analysis with exponential decay weighting.
        
        More recent matches weighted higher.
        """
        def form_score(form):
            if not form:
                return 0.5
            # Exponential decay weights
            weights = [0.35, 0.25, 0.20, 0.12, 0.08]
            score = 0
            for i, result in enumerate(form[:5]):
                w = weights[i] if i < len(weights) else 0.05
                if result == 1:
                    score += w * 1.0
                elif result == 0:
                    score += w * 0.5
                else:
                    score += w * 0.0
            return score
        
        home_score = form_score(home_form)
        away_score = form_score(away_form)
        
        total = home_score + away_score
        if total == 0:
            return 0.5
        
        return home_score / total
    
    def _h2h_component(self, h2h_home_wins: int, h2h_draws: int,
                       h2h_away_wins: int) -> float:
        """Head-to-head history component."""
        total = h2h_home_wins + h2h_draws + h2h_away_wins
        if total == 0:
            return 0.5
        
        home_score = h2h_home_wins + h2h_draws * 0.5
        away_score = h2h_away_wins + h2h_draws * 0.5
        
        total_score = home_score + away_score
        if total_score == 0:
            return 0.5
        
        return home_score / total_score
    
    def _injury_component(self, home_injuries: int, away_injuries: int) -> float:
        """
        Injury adjustment.
        
        More injuries = lower probability of winning.
        Assumes 11 key players per team.
        """
        home_available = max(0, 11 - home_injuries)
        away_available = max(0, 11 - away_injuries)
        
        total = home_available + away_available
        if total == 0:
            return 0.5
        
        return home_available / total
    
    def predict(self,
                home_team: str,
                away_team: str,
                home_rank: int = 50,
                away_rank: int = 50,
                home_xg: float = 1.5,
                home_xga: float = 1.0,
                away_xg: float = 1.0,
                away_xga: float = 1.5,
                betting_home_prob: Optional[float] = None,
                betting_away_prob: Optional[float] = None,
                home_form: List[int] = None,
                away_form: List[int] = None,
                h2h_home_wins: int = 0,
                h2h_draws: int = 0,
                h2h_away_wins: int = 0,
                home_injuries: int = 0,
                away_injuries: int = 0,
                knockout: bool = False,
                home_advantage: bool = True) -> MatchPrediction:
        """
        Generate ensemble prediction.
        
        Combines multiple models with calibrated weights.
        """
        # Default values
        if home_form is None:
            home_form = [0, 0, 0, 0, 0]
        if away_form is None:
            away_form = [0, 0, 0, 0, 0]
        
        # Calculate individual components
        elo_prob = self._elo_component(home_rank, away_rank)
        xg_home_prob, xg_away_prob = self._xg_component(home_xg, home_xga, away_xg, away_xga)
        form_prob = self._form_component(home_form, away_form)
        h2h_prob = self._h2h_component(h2h_home_wins, h2h_draws, h2h_away_wins)
        injury_prob = self._injury_component(home_injuries, away_injuries)
        
        # Betting component (optional)
        if betting_home_prob is not None and betting_away_prob is not None:
            betting_prob = self._betting_component(betting_home_prob, betting_away_prob)
            betting_weight = WEIGHT_BETTING
        else:
            betting_prob = elo_prob  # Fallback to Elo
            betting_weight = 0.0
        
        # Combine with weights
        # Adjust weights if betting not available
        total_weight = (WEIGHT_ELO + WEIGHT_XG + WEIGHT_FORM + 
                       WEIGHT_H2H + WEIGHT_INJURIES + betting_weight)
        
        home_strength = (
            elo_prob * WEIGHT_ELO +
            xg_home_prob * WEIGHT_XG +
            form_prob * WEIGHT_FORM +
            h2h_prob * WEIGHT_H2H +
            injury_prob * WEIGHT_INJURIES +
            betting_prob * betting_weight
        ) / total_weight
        
        # Add home advantage
        if home_advantage:
            home_strength += 0.05
        
        # Normalize
        home_strength = min(max(home_strength, 0.1), 0.9)
        away_strength = 1 - home_strength
        
        # Calculate 3-way probabilities
        # Home win probability
        home_win_prob = home_strength * 0.75
        
        # Draw probability
        base_draw = 0.20
        if knockout:
            base_draw = 0.15
        draw_prob = base_draw * (1 - abs(home_strength - 0.5) * 2)
        
        # Away win probability
        away_win_prob = 1 - home_win_prob - draw_prob
        
        # Normalize
        total = home_win_prob + draw_prob + away_win_prob
        home_win_prob /= total
        draw_prob /= total
        away_win_prob /= total
        
        # Expected goals using xG
        home_exp_goals = max(0.1, home_xg * 0.8 + away_xga * 0.2)
        away_exp_goals = max(0.1, away_xg * 0.8 + home_xga * 0.2)
        
        # Find most likely score
        max_prob = 0
        most_likely_score = "1-1"
        for h in range(POISSON_MAX_GOALS):
            for a in range(POISSON_MAX_GOALS):
                prob = poisson_pmf(h, home_exp_goals) * poisson_pmf(a, away_exp_goals)
                if prob > max_prob:
                    max_prob = prob
                    most_likely_score = f"{h}-{a}"
        
        # Confidence = difference between top two outcomes
        sorted_probs = sorted([home_win_prob, draw_prob, away_win_prob], reverse=True)
        confidence = sorted_probs[0] - sorted_probs[1]
        
        # Build reasoning with component breakdown
        components = {
            "elo": round(elo_prob, 2),
            "xg": round(xg_home_prob, 2),
            "form": round(form_prob, 2),
            "h2h": round(h2h_prob, 2),
            "injury": round(injury_prob, 2),
        }
        if betting_home_prob is not None:
            components["betting"] = round(betting_prob, 2)
        
        reasoning = (
            f"Ensemble prediction: Elo({elo_prob:.2f})×{WEIGHT_ELO} + "
            f"xG({xg_home_prob:.2f})×{WEIGHT_XG} + "
            f"Form({form_prob:.2f})×{WEIGHT_FORM} + "
            f"H2H({h2h_prob:.2f})×{WEIGHT_H2H} + "
            f"Injury({injury_prob:.2f})×{WEIGHT_INJURIES}"
        )
        if betting_home_prob is not None:
            reasoning += f" + Betting({betting_prob:.2f})×{WEIGHT_BETTING}"
        reasoning += f". Combined: {home_strength:.2f}"
        
        return MatchPrediction(
            home_win_prob=round(home_win_prob, 2),
            draw_prob=round(draw_prob, 2),
            away_win_prob=round(away_win_prob, 2),
            expected_home_goals=round(home_exp_goals, 2),
            expected_away_goals=round(away_exp_goals, 2),
            most_likely_score=most_likely_score,
            confidence=round(confidence, 2),
            reasoning=reasoning,
            ensemble_components=components,
        )


# =============================================================================
# MONTE CARLO VALIDATION
# =============================================================================

def monte_carlo_simulation(
    predictor: EnsemblePredictor,
    home_team: str,
    away_team: str,
    n_simulations: int = 10000,
    **kwargs
) -> Dict:
    """
    Run Monte Carlo simulation to validate prediction.
    """
    prediction = predictor.predict(home_team, away_team, **kwargs)
    
    home_wins = 0
    draws = 0
    away_wins = 0
    
    home_goals_list = []
    away_goals_list = []
    
    for _ in range(n_simulations):
        try:
            import numpy as np
            home_goals = np.random.poisson(prediction.expected_home_goals)
            away_goals = np.random.poisson(prediction.expected_away_goals)
        except ImportError:
            u = random.random()
            home_goals = 0
            p_cum = poisson_pmf(0, prediction.expected_home_goals)
            while u > p_cum and home_goals < POISSON_MAX_GOALS:
                home_goals += 1
                p_cum += poisson_pmf(home_goals, prediction.expected_home_goals)
            
            u = random.random()
            away_goals = 0
            p_cum = poisson_pmf(0, prediction.expected_away_goals)
            while u > p_cum and away_goals < POISSON_MAX_GOALS:
                away_goals += 1
                p_cum += poisson_pmf(away_goals, prediction.expected_away_goals)
        
        home_goals_list.append(home_goals)
        away_goals_list.append(away_goals)
        
        if home_goals > away_goals:
            home_wins += 1
        elif home_goals < away_goals:
            away_wins += 1
        else:
            draws += 1
    
    total = n_simulations
    
    return {
        "home_win_prob": home_wins / total,
        "draw_prob": draws / total,
        "away_win_prob": away_wins / total,
        "expected_home_goals": sum(home_goals_list) / total,
        "expected_away_goals": sum(away_goals_list) / total,
        "most_likely_score": prediction.most_likely_score,
        "confidence": prediction.confidence,
        "n_simulations": n_simulations,
    }


# =============================================================================
# TESTING
# =============================================================================

def test_ensemble_predictor():
    """Test the ensemble prediction model with sample data."""
    print("=" * 70)
    print("ENSEMBLE PREDICTOR TEST")
    print("=" * 70)
    
    predictor = EnsemblePredictor()
    
    # Test 1: Brazil vs Japan (with realistic inputs)
    print("\n--- Test 1: Brazil vs Japan (Knockout, with betting odds) ---")
    result = predictor.predict(
        home_team="Brazil",
        away_team="Japan",
        home_rank=6,
        away_rank=18,
        home_xg=2.1,  # Brazil creates 2.1 xG per match
        home_xga=0.8,  # Concedes 0.8 xGA
        away_xg=1.2,  # Japan creates 1.2 xG
        away_xga=1.3,  # Concedes 1.3 xGA
        betting_home_prob=0.72,  # Bookmaker implied prob
        betting_away_prob=0.28,
        home_form=[1, 1, 0, 1, 1],  # W W D W W
        away_form=[1, 0, 0, 1, 1],  # W D D W W
        h2h_home_wins=7,
        h2h_draws=2,
        h2h_away_wins=1,
        home_injuries=0,
        away_injuries=0,
        knockout=True,
    )
    
    print(f"Home win: {result.home_win_prob:.0%}")
    print(f"Draw: {result.draw_prob:.0%}")
    print(f"Away win: {result.away_win_prob:.0%}")
    print(f"Expected score: {result.most_likely_score}")
    print(f"Confidence: {result.confidence:.0%}")
    print(f"Components: {result.ensemble_components}")
    
    binary = result.to_binary()
    print(f"Binary (knockout): Home advance {binary[0]:.2%}, Away advance {binary[1]:.2%}")
    print(f"Reasoning: {result.reasoning[:100]}...")
    
    # Test 2: Without betting odds
    print("\n--- Test 2: Brazil vs Japan (No betting odds) ---")
    result2 = predictor.predict(
        home_team="Brazil",
        away_team="Japan",
        home_rank=6,
        away_rank=18,
        home_xg=2.1,
        home_xga=0.8,
        away_xg=1.2,
        away_xga=1.3,
        home_form=[1, 1, 0, 1, 1],
        away_form=[1, 0, 0, 1, 1],
        knockout=True,
    )
    
    print(f"Home win: {result2.home_win_prob:.0%}")
    print(f"Draw: {result2.draw_prob:.0%}")
    print(f"Away win: {result2.away_win_prob:.0%}")
    print(f"Confidence: {result2.confidence:.0%}")
    
    # Test 3: Monte Carlo validation
    print("\n--- Test 3: Monte Carlo Validation ---")
    mc_result = monte_carlo_simulation(
        predictor,
        "Brazil",
        "Japan",
        n_simulations=10000,
        home_rank=6,
        away_rank=18,
        home_xg=2.1,
        home_xga=0.8,
        away_xg=1.2,
        away_xga=1.3,
        betting_home_prob=0.72,
        betting_away_prob=0.28,
        home_form=[1, 1, 0, 1, 1],
        away_form=[1, 0, 0, 1, 1],
        knockout=True,
    )
    
    print(f"MC Home win: {mc_result['home_win_prob']:.2%}")
    print(f"MC Draw: {mc_result['draw_prob']:.2%}")
    print(f"MC Away win: {mc_result['away_win_prob']:.2%}")
    
    print("\n" + "=" * 70)
    print("All tests completed!")
    print("=" * 70)


if __name__ == "__main__":
    test_ensemble_predictor()
