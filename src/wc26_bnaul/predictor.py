"""
Prediction Model for wc26-bnaul

Xây dựng mô hình dự đoán dựa trên dữ liệu lịch sử và các chỉ số FIFA.

Các yếu tố đầu vào:
- FIFA Ranking
- Phong độ gần đây (last 5 matches)
- Head-to-head history
- Player stats (goals, assists, xG)
- Team stats (goals scored/conceded, clean sheets)
- Injuries/suspensions
- Home advantage (nếu có)
- Tournament progression (group stage vs knockout)

Mô hình:
- Elo-based rating adjustment
- Poisson distribution cho goals
- Monte Carlo simulation
- Brier score optimization

Usage:
    from wc26_bnaul.predictor import MatchPredictor
    
    predictor = MatchPredictor()
    result = predictor.predict(
        home_team="Brazil",
        away_team="Japan",
        home_rank=6,
        away_rank=18,
        home_form=[1, 1, 0, 1, 1],  # 1=win, 0=draw, -1=loss
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
"""

import json
import math
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


# =============================================================================
# CONSTANTS
# =============================================================================

FIFA_RANK_WEIGHT = 0.25
FORM_WEIGHT = 0.20
H2H_WEIGHT = 0.15
GOALS_WEIGHT = 0.20
HOME_ADVANTAGE = 0.05
KNOCKOUT_DRAW_ADJUSTMENT = 0.15  # Draw probability lower in knockout

# Elo parameters
ELO_K = 32  # K-factor for rating updates
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
    goals_scored: int  # Last 5 matches
    goals_conceded: int  # Last 5 matches
    clean_sheets: int  # Last 5 matches
    key_players_available: int = 11  # Số cầu thủ chủ chốt có thể ra sân
    injuries: List[str] = None
    
    def __post_init__(self):
        if self.injuries is None:
            self.injuries = []


@dataclass
class MatchPrediction:
    """Kết quả dự đoán."""
    home_win_prob: float
    draw_prob: float
    away_win_prob: float
    expected_home_goals: float
    expected_away_goals: float
    most_likely_score: str
    confidence: float
    reasoning: str
    
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
        self.ratings = {}  # team_name -> rating
    
    def get_rating(self, team: str) -> float:
        return self.ratings.get(team, ELO_INITIAL)
    
    def expected_score(self, team_a: str, team_b: str) -> float:
        """Expected score for team_a vs team_b."""
        rating_a = self.get_rating(team_a)
        rating_b = self.get_rating(team_b)
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
    
    def update(self, team_a: str, team_b: str, score_a: float, score_b: float):
        """Update ratings after match. score: 1=win, 0.5=draw, 0=loss."""
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

def poisson_cdf(k: int, lam: float) -> float:
    """Poisson cumulative distribution function."""
    return sum(poisson_pmf(i, lam) for i in range(k + 1))


def expected_goals(goals_scored: int, goals_conceded: int, matches: int = 5) -> float:
    """Calculate expected goals per match."""
    if matches == 0:
        return 1.0
    attack_strength = goals_scored / matches
    defense_weakness = goals_conceded / matches
    return (attack_strength + defense_weakness) / 2


# =============================================================================
# PREDICTION MODEL
# =============================================================================

class MatchPredictor:
    """Main prediction model for football matches."""
    
    def __init__(self):
        self.elo = EloRating()
    
    def _calculate_fifa_factor(self, home_rank: int, away_rank: int) -> float:
        """
        Calculate strength factor based on FIFA ranking.
        Lower rank = stronger team.
        """
        # Convert rank to strength (inverse, with diminishing returns)
        home_strength = 1 / math.sqrt(home_rank)
        away_strength = 1 / math.sqrt(away_rank)
        
        total = home_strength + away_strength
        if total == 0:
            return 0.5
        
        return home_strength / total
    
    def _calculate_form_factor(self, home_form: List[int], away_form: List[int]) -> float:
        """
        Calculate strength factor based on recent form.
        """
        def form_score(form):
            if not form:
                return 0.5
            # Weight recent matches more
            weights = [0.35, 0.25, 0.20, 0.12, 0.08]  # Most recent first
            score = 0
            for i, result in enumerate(form[:5]):
                w = weights[i] if i < len(weights) else 0.05
                # Convert result to score: win=1, draw=0.5, loss=0
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
    
    def _calculate_h2h_factor(
        self,
        h2h_home_wins: int,
        h2h_draws: int,
        h2h_away_wins: int
    ) -> float:
        """
        Calculate strength factor based on head-to-head history.
        """
        total = h2h_home_wins + h2h_draws + h2h_away_wins
        if total == 0:
            return 0.5
        
        # Draws count as 0.5 for each side
        home_score = h2h_home_wins + h2h_draws * 0.5
        away_score = h2h_away_wins + h2h_draws * 0.5
        
        total_score = home_score + away_score
        if total_score == 0:
            return 0.5
        
        return home_score / total_score
    
    def _calculate_goals_factor(
        self,
        home_goals_scored: int,
        home_goals_conceded: int,
        away_goals_scored: int,
        away_goals_conceded: int,
        matches: int = 5,
    ) -> float:
        """
        Calculate strength factor based on goals scored/conceded.
        """
        if matches == 0:
            return 0.5
        
        home_attack = home_goals_scored / matches
        home_defense = home_goals_conceded / matches
        away_attack = away_goals_scored / matches
        away_defense = away_goals_conceded / matches
        
        # Expected goals when home attacks vs away defense
        home_xg = (home_attack + away_defense) / 2
        away_xg = (away_attack + home_defense) / 2
        
        total = home_xg + away_xg
        if total == 0:
            return 0.5
        
        return home_xg / total
    
    def _calculate_injury_factor(
        self,
        home_key_players: int,
        away_key_players: int,
    ) -> float:
        """
        Adjust for key player availability.
        """
        total = home_key_players + away_key_players
        if total == 0:
            return 0.5
        return home_key_players / total
    
    def predict(
        self,
        home_team: str,
        away_team: str,
        home_rank: int = 50,
        away_rank: int = 50,
        home_form: List[int] = None,
        away_form: List[int] = None,
        h2h_home_wins: int = 0,
        h2h_draws: int = 0,
        h2h_away_wins: int = 0,
        home_goals_scored: int = 5,
        home_goals_conceded: int = 5,
        away_goals_scored: int = 5,
        away_goals_conceded: int = 5,
        home_key_players: int = 11,
        away_key_players: int = 11,
        knockout: bool = False,
        home_advantage: bool = True,
    ) -> MatchPrediction:
        """
        Generate match prediction.
        
        Args:
            home_team: Name of home team
            away_team: Name of away team
            home_rank: FIFA ranking of home team (lower = better)
            away_rank: FIFA ranking of away team
            home_form: Last 5 results for home team [1, 0, -1, ...]
            away_form: Last 5 results for away team
            h2h_home_wins: Head-to-head home wins
            h2h_draws: Head-to-head draws
            h2h_away_wins: Head-to-head away wins
            home_goals_scored: Goals scored in last 5 matches
            home_goals_conceded: Goals conceded in last 5 matches
            away_goals_scored: Goals scored in last 5 matches
            away_goals_conceded: Goals conceded in last 5 matches
            home_key_players: Number of key players available
            away_key_players: Number of key players available
            knockout: True if knockout stage (no draw in binary)
            home_advantage: True if home team has advantage
        
        Returns:
            MatchPrediction with probabilities and expected scores
        """
        # Default values
        if home_form is None:
            home_form = [0, 0, 0, 0, 0]
        if away_form is None:
            away_form = [0, 0, 0, 0, 0]
        
        # Calculate individual factors
        fifa_factor = self._calculate_fifa_factor(home_rank, away_rank)
        form_factor = self._calculate_form_factor(home_form, away_form)
        h2h_factor = self._calculate_h2h_factor(h2h_home_wins, h2h_draws, h2h_away_wins)
        goals_factor = self._calculate_goals_factor(
            home_goals_scored, home_goals_conceded,
            away_goals_scored, away_goals_conceded,
        )
        injury_factor = self._calculate_injury_factor(home_key_players, away_key_players)
        
        # Combine factors with weights
        home_strength = (
            fifa_factor * FIFA_RANK_WEIGHT +
            form_factor * FORM_WEIGHT +
            h2h_factor * H2H_WEIGHT +
            goals_factor * GOALS_WEIGHT +
            injury_factor * 0.10  # Injury weight
        )
        
        # Add home advantage
        if home_advantage:
            home_strength += HOME_ADVANTAGE
        
        # Normalize to probability space
        home_strength = min(max(home_strength, 0.1), 0.9)
        away_strength = 1 - home_strength
        
        # Calculate 3-way probabilities
        # Home win probability
        home_win_prob = home_strength * 0.75  # 75% of strength goes to win
        
        # Draw probability (reduced in knockout)
        base_draw = 0.20
        if knockout:
            base_draw = KNOCKOUT_DRAW_ADJUSTMENT
        draw_prob = base_draw * (1 - abs(home_strength - 0.5) * 2)  # Less draw when teams are mismatched
        
        # Away win probability
        away_win_prob = 1 - home_win_prob - draw_prob
        
        # Normalize
        total = home_win_prob + draw_prob + away_win_prob
        home_win_prob /= total
        draw_prob /= total
        away_win_prob /= total
        
        # Calculate expected goals using Poisson
        home_xg = expected_goals(home_goals_scored, home_goals_conceded)
        away_xg = expected_goals(away_goals_scored, away_goals_conceded)
        
        # Adjust for opponent strength
        home_xg *= home_strength / 0.5
        away_xg *= away_strength / 0.5
        
        # Find most likely score
        max_prob = 0
        most_likely_score = "1-1"
        for h in range(POISSON_MAX_GOALS):
            for a in range(POISSON_MAX_GOALS):
                prob = poisson_pmf(h, home_xg) * poisson_pmf(a, away_xg)
                if prob > max_prob:
                    max_prob = prob
                    most_likely_score = f"{h}-{a}"
        
        # Confidence = difference between top two outcomes
        sorted_probs = sorted([home_win_prob, draw_prob, away_win_prob], reverse=True)
        confidence = sorted_probs[0] - sorted_probs[1]
        
        # Build reasoning
        reasoning = (
            f"Prediction based on: "
            f"FIFA rank #{home_rank} vs #{away_rank} (weight {FIFA_RANK_WEIGHT}), "
            f"Recent form (weight {FORM_WEIGHT}), "
            f"H2H history {h2h_home_wins}-{h2h_draws}-{h2h_away_wins} (weight {H2H_WEIGHT}), "
            f"Goals scored/conceded (weight {GOALS_WEIGHT}). "
            f"Home strength: {home_strength:.2f}. "
            f"{'Knockout stage - no draw in binary.' if knockout else 'Group stage - draw possible.'}"
        )
        
        return MatchPrediction(
            home_win_prob=round(home_win_prob, 2),
            draw_prob=round(draw_prob, 2),
            away_win_prob=round(away_win_prob, 2),
            expected_home_goals=round(home_xg, 2),
            expected_away_goals=round(away_xg, 2),
            most_likely_score=most_likely_score,
            confidence=round(confidence, 2),
            reasoning=reasoning,
        )
    
    def predict_from_api_data(
        self,
        home_team: str,
        away_team: str,
        home_stats: Dict,
        away_stats: Dict,
        h2h_history: List[Dict] = None,
        knockout: bool = False,
    ) -> MatchPrediction:
        """
        Generate prediction from API-fetched data.
        
        Args:
            home_stats: Team statistics from API-Football
            away_stats: Team statistics from API-Football
            h2h_history: Head-to-head match history
            knockout: True if knockout stage
        """
        # Extract form from API data
        home_form_str = home_stats.get("form", "")  # e.g., "WWDLW"
        away_form_str = away_stats.get("form", "")
        
        def parse_form(form_str):
            mapping = {"W": 1, "D": 0, "L": -1}
            return [mapping.get(c, 0) for c in form_str.upper()]
        
        home_form = parse_form(home_form_str)
        away_form = parse_form(away_form_str)
        
        # Extract goals from API data
        home_goals = home_stats.get("goals", {})
        away_goals = away_stats.get("goals", {})
        
        home_goals_scored = home_goals.get("for", {}).get("total", {}).get("total", 0)
        home_goals_conceded = home_goals.get("against", {}).get("total", {}).get("total", 0)
        away_goals_scored = away_goals.get("for", {}).get("total", {}).get("total", 0)
        away_goals_conceded = away_goals.get("against", {}).get("total", {}).get("total", 0)
        
        # Extract fixtures from API data
        home_fixtures = home_stats.get("fixtures", {})
        away_fixtures = away_stats.get("fixtures", {})
        
        home_played = home_fixtures.get("played", {}).get("total", 1)
        away_played = away_fixtures.get("played", {}).get("total", 1)
        
        # Calculate H2H
        h2h_home_wins = 0
        h2h_draws = 0
        h2h_away_wins = 0
        
        if h2h_history:
            for match in h2h_history:
                home_goals_h2h = match.get("goals", {}).get("home", 0)
                away_goals_h2h = match.get("goals", {}).get("away", 0)
                if home_goals_h2h > away_goals_h2h:
                    h2h_home_wins += 1
                elif home_goals_h2h < away_goals_h2h:
                    h2h_away_wins += 1
                else:
                    h2h_draws += 1
        
        # FIFA ranking (use team ID as proxy if not available)
        home_rank = home_stats.get("fifa_rank", 50)
        away_rank = away_stats.get("fifa_rank", 50)
        
        return self.predict(
            home_team=home_team,
            away_team=away_team,
            home_rank=home_rank,
            away_rank=away_rank,
            home_form=home_form,
            away_form=away_form,
            h2h_home_wins=h2h_home_wins,
            h2h_draws=h2h_draws,
            h2h_away_wins=h2h_away_wins,
            home_goals_scored=home_goals_scored,
            home_goals_conceded=home_goals_conceded,
            away_goals_scored=away_goals_scored,
            away_goals_conceded=away_goals_conceded,
            knockout=knockout,
        )


# =============================================================================
# MONTE CARLO SIMULATION
# =============================================================================

def monte_carlo_simulation(
    predictor: MatchPredictor,
    home_team: str,
    away_team: str,
    n_simulations: int = 10000,
    **kwargs
) -> Dict:
    """
    Run Monte Carlo simulation to validate prediction.
    
    Returns:
        Dict with simulation statistics
    """
    prediction = predictor.predict(home_team, away_team, **kwargs)
    
    home_wins = 0
    draws = 0
    away_wins = 0
    
    home_goals_list = []
    away_goals_list = []
    
    for _ in range(n_simulations):
        # Simulate goals using Poisson (numpy or manual)
        # Using numpy.random.poisson if available, else manual
        try:
            import numpy as np
            home_goals = np.random.poisson(prediction.expected_home_goals)
            away_goals = np.random.poisson(prediction.expected_away_goals)
        except ImportError:
            # Manual Poisson sampling using inverse CDF
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

def test_predictor():
    """Test the prediction model with sample data."""
    print("=" * 70)
    print("MATCH PREDICTOR TEST")
    print("=" * 70)
    
    predictor = MatchPredictor()
    
    # Test 1: Brazil vs Japan (Round of 32)
    print("\n--- Test 1: Brazil vs Japan (Knockout) ---")
    result = predictor.predict(
        home_team="Brazil",
        away_team="Japan",
        home_rank=6,
        away_rank=18,
        home_form=[1, 1, 0, 1, 1],  # W W D W W
        away_form=[1, 0, 0, 1, 1],  # W D D W W
        h2h_home_wins=7,
        h2h_draws=2,
        h2h_away_wins=1,
        home_goals_scored=15,
        home_goals_conceded=4,
        away_goals_scored=8,
        away_goals_conceded=3,
        knockout=True,
    )
    
    print(f"Home win: {result.home_win_prob:.2%}")
    print(f"Draw: {result.draw_prob:.2%}")
    print(f"Away win: {result.away_win_prob:.2%}")
    print(f"Expected score: {result.most_likely_score}")
    print(f"Confidence: {result.confidence:.2%}")
    
    binary = result.to_binary()
    print(f"Binary (knockout): Home advance {binary[0]:.2%}, Away advance {binary[1]:.2%}")
    print(f"Reasoning: {result.reasoning[:100]}...")
    
    # Test 2: Netherlands vs Morocco (Knockout, close match)
    print("\n--- Test 2: Netherlands vs Morocco (Knockout, close) ---")
    result2 = predictor.predict(
        home_team="Netherlands",
        away_team="Morocco",
        home_rank=7,
        away_rank=11,
        home_form=[0, 1, 0, 1, 1],  # D W D W W
        away_form=[0, 1, 0, 1, 1],  # D W D W W
        h2h_home_wins=2,
        h2h_draws=0,
        h2h_away_wins=1,
        home_goals_scored=10,
        home_goals_conceded=3,
        away_goals_scored=7,
        away_goals_conceded=1,
        knockout=True,
    )
    
    print(f"Home win: {result2.home_win_prob:.2%}")
    print(f"Draw: {result2.draw_prob:.2%}")
    print(f"Away win: {result2.away_win_prob:.2%}")
    print(f"Expected score: {result2.most_likely_score}")
    print(f"Confidence: {result2.confidence:.2%}")
    
    binary2 = result2.to_binary()
    print(f"Binary (knockout): Home advance {binary2[0]:.2%}, Away advance {binary2[1]:.2%}")
    
    # Test 3: Monte Carlo validation
    print("\n--- Test 3: Monte Carlo Validation (Brazil vs Japan) ---")
    mc_result = monte_carlo_simulation(
        predictor,
        "Brazil",
        "Japan",
        n_simulations=10000,
        home_rank=6,
        away_rank=18,
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
    
    print(f"MC Home win: {mc_result['home_win_prob']:.2%}")
    print(f"MC Draw: {mc_result['draw_prob']:.2%}")
    print(f"MC Away win: {mc_result['away_win_prob']:.2%}")
    print(f"MC Expected home goals: {mc_result['expected_home_goals']:.2f}")
    print(f"MC Expected away goals: {mc_result['expected_away_goals']:.2f}")
    
    print("\n" + "=" * 70)
    print("All tests completed!")
    print("=" * 70)


if __name__ == "__main__":
    test_predictor()
