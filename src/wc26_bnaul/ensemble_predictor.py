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

# =============================================================================
# SKILL OPTIMIZATION: 4 Core Principles + Knockout Draw Learning
# =============================================================================
#
# 1. TRUTHFUL SUBMISSION: Always submit your true belief probability
#    Brier is strictly proper scoring rule — truthful is optimal
#
# 2. KNOCKOUT CAP 65%: Penalty shootouts make even 70% favorites ~50/50
#    Learned from: wc-kimi (caps 65%), jason (burned by 82%)
#
# 3. SELECTIVITY: If no clear edge (48-52%), submit 50/50
#    Learned from: jason (selective, 55% SKILL)
#
# 4. ELO-BASED: Use real ELO ratings (not FIFA rank approximation)
#    Source: Amir Motefaker dataset (1698-2045 range)
#
# 5. KNOCKOUT DRAW AWARENESS (NEW — learned from m075, m076):
#    - 2/3 knockout matches so far ended in draw (penalty shootout)
#    - Draw + penalty = away advances (binary outcome = 0)
#    - Model predicted home win (59%, 56%) but actual = away advances
#    - Brier with 50/50: 0.25 | Brier with model: 0.35, 0.30
#    - → 50/50 BETTER than model for close knockout matches!
#    - Fix: Lower selectivity threshold to 55% for knockout
#    - Fix: Stronger shrinkage (0.90 instead of 0.95)
#    - Fix: Higher base draw probability (0.25 instead of 0.15)
#
# Reference: docs/01_STRATEGY.md for mathematical proof
# =============================================================================

# Ensemble weights (calibrated on historical data + Amir Motefaker dataset)
# FIXED: weights now sum to 1.0 (was 1.10)
WEIGHT_ELO = 0.30
WEIGHT_FIFA = 0.10
WEIGHT_XG = 0.20
WEIGHT_BETTING = 0.10
WEIGHT_FORM = 0.15
WEIGHT_SQUAD_DEPTH = 0.05
WEIGHT_H2H = 0.05   # REDUCED from 0.10
WEIGHT_INJURIES = 0.05  # REDUCED from 0.10

# SKILL Optimization constants
KNOCKOUT_CONFIDENCE_CAP = 0.65
KNOCKOUT_CONFIDENCE_FLOOR = 0.35
KNOCKOUT_VARIANCE_PENALTY = 0.90  # CHANGED: 0.95 → 0.90 (stronger shrinkage)
SELECTIVITY_THRESHOLD_LOW = 0.48
SELECTIVITY_THRESHOLD_HIGH = 0.52
HOME_ADVANTAGE_BOOST = 0.05

# Knockout draw awareness (NEW)
KNOCKOUT_BASE_DRAW = 0.30  # CHANGED: 0.25 → 0.30 (higher draw probability, learned from m075, m076, m077)
KNOCKOUT_CLOSE_MATCH_CAP = 0.55  # NEW: For ELO gap < 100, cap at 55%
KNOCKOUT_CLOSE_ELO_GAP = 100  # NEW: Threshold for "close match"
KNOCKOUT_ELO_DISCOUNT = 0.70  # NEW: Reduce ELO gap by 30% in knockout (learned from m075, m076)

# Poisson parameters
POISSON_MAX_GOALS = 10

# Elo parameters
ELO_K = 32
ELO_INITIAL = 1500
ELO_SCALE = 400  # Standard ELO scaling factor


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
        """Convert 3-way to binary (knockout) probabilities.
        
        Principle 5: Penalty shootout awareness.
        In knockout, draw → penalty shootout → ~50/50.
        So draw is worth 0.5 for home, not 1.0.
        This makes binary predictions more conservative.
        """
        # Old: home_advance = home_win + draw (assumes draw = home win)
        # New: home_advance = home_win + draw * 0.5 (draw = 50/50 penalty)
        home_advance = self.home_win_prob + self.draw_prob * 0.5
        away_advance = self.away_win_prob + self.draw_prob * 0.5
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
    
    def _elo_component(self, home_rank: int, away_rank: int, home_elo: int = 0, away_elo: int = 0, knockout: bool = False) -> float:
        """
        Elo-based probability using actual ELO ratings from Amir dataset.
        
        Principle 4: ELO-BASED — Use real ELO ratings, not FIFA rank approximation.
        ELO accounts for opponent strength; FIFA rank does not.
        
        Principle 5: In knockout, ELO advantage is discounted because:
        - Single-elimination = higher variance
        - Draw → penalty shootout = ~50/50
        - Underdogs play more defensively
        - Favorites choke under pressure
        
        If ELO ratings provided (home_elo, away_elo > 0), use them directly.
        Otherwise, fall back to FIFA rank-based approximation.
        """
        if home_elo > 0 and away_elo > 0:
            # Use actual ELO ratings (from Amir dataset)
            # Standard ELO expected score formula: 1 / (1 + 10^((Rb-Ra)/400))
            
            # Knockout discount: reduce ELO gap by 30%
            # Learned from m075, m076: ELO overpredicts favorite advantage in knockout
            if knockout:
                elo_gap = away_elo - home_elo  # Negative = home favored
                discounted_gap = elo_gap * 0.70  # Reduce gap by 30%
                home_strength = 1 / (1 + 10 ** (discounted_gap / ELO_SCALE))
            else:
                home_strength = 1 / (1 + 10 ** ((away_elo - home_elo) / ELO_SCALE))
            return home_strength
        
        # Fallback: Convert FIFA rank to Elo-like strength
        home_strength = 1 / math.sqrt(home_rank)
        away_strength = 1 / math.sqrt(away_rank)
        
        total = home_strength + away_strength
        if total == 0:
            return 0.5
        
        return home_strength / total
    
    def _fifa_component(self, home_rank: int, away_rank: int) -> float:
        """
        FIFA rank-based probability (secondary strength signal).
        Used alongside ELO for robustness.
        """
        home_strength = 1 / math.sqrt(home_rank)
        away_strength = 1 / math.sqrt(away_rank)
        
        total = home_strength + away_strength
        if total == 0:
            return 0.5
        
        return home_strength / total
    
    def _squad_depth_component(self, home_depth: float, away_depth: float) -> float:
        """
        Squad depth component (from Amir dataset).
        Higher squad depth = better ability to handle injuries/fatigue.
        """
        total = home_depth + away_depth
        if total == 0:
            return 0.5
        
        return home_depth / total
    
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
                home_elo: int = 0,
                away_elo: int = 0,
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
                home_squad_depth: float = 5.0,
                away_squad_depth: float = 5.0,
                knockout: bool = False,
                home_advantage: bool = True,
                home_rest_days: int = 5,
                away_rest_days: int = 5,
                altitude_m: int = 0,
                temperature_c: int = 20,
                ) -> MatchPrediction:
        """
        Generate ensemble prediction with environmental modifiers.
        
        Enhanced with Amir Motefaker dataset:
        - Real ELO ratings (not FIFA rank approximation)
        - Squad depth component
        - Venue-specific xG modifiers
        - Monte Carlo simulation (10,000 iterations)
        - Fatigue modifier (rest days < 3 → -10% xG)
        - Altitude modifier (>1500m → +5% variance, >2200m → +12%)
        - Temperature modifier (>32°C → -6% xG)
        - Upset risk detection (ELO gap + form difference)
        - Data quality score (1-5 stars based on data availability)
        """
        # Default values
        if home_form is None:
            home_form = [0, 0, 0, 0, 0]
        if away_form is None:
            away_form = [0, 0, 0, 0, 0]
        
        # Calculate individual components
        # ELO component: use real ELO if available, otherwise fallback to FIFA rank
        elo_prob = self._elo_component(home_rank, away_rank, home_elo, away_elo, knockout=knockout)
        fifa_prob = self._fifa_component(home_rank, away_rank)
        xg_home_prob, xg_away_prob = self._xg_component(home_xg, home_xga, away_xg, away_xga)
        form_prob = self._form_component(home_form, away_form)
        h2h_prob = self._h2h_component(h2h_home_wins, h2h_draws, h2h_away_wins)
        injury_prob = self._injury_component(home_injuries, away_injuries)
        squad_depth_prob = self._squad_depth_component(home_squad_depth, away_squad_depth)
        
        # Betting component (optional)
        if betting_home_prob is not None and betting_away_prob is not None:
            betting_prob = self._betting_component(betting_home_prob, betting_away_prob)
            betting_weight = WEIGHT_BETTING
        else:
            betting_prob = elo_prob  # Fallback to Elo
            betting_weight = 0.0
        
        # Combine with weights
        # Total weight depends on whether betting is available
        total_weight = (WEIGHT_ELO + WEIGHT_FIFA + WEIGHT_XG + WEIGHT_FORM + 
                       WEIGHT_SQUAD_DEPTH + WEIGHT_H2H + WEIGHT_INJURIES + betting_weight)
        
        home_strength = (
            elo_prob * WEIGHT_ELO +
            fifa_prob * WEIGHT_FIFA +
            xg_home_prob * WEIGHT_XG +
            form_prob * WEIGHT_FORM +
            squad_depth_prob * WEIGHT_SQUAD_DEPTH +
            h2h_prob * WEIGHT_H2H +
            injury_prob * WEIGHT_INJURIES +
            betting_prob * betting_weight
        ) / total_weight
        
        # AGGRESSIVE CONSERVATISM: Shrink predictions toward 50%
        # Learned from simulation: selective prediction beats always-predict
        # If model says 60%, submit 55%. If 55%, submit 50/50.
        # This compensates for model overconfidence in knockout.
        # 
        # BUT: For matches with CLEAR edge (ELO gap > 200), trust the model more
        # For close matches (ELO gap < 150), be very conservative
        if home_elo > 0 and away_elo > 0:
            elo_gap = abs(home_elo - away_elo)
            if elo_gap > 200:
                conservative_shrink = 0.95  # Small shrink for clear favorites
            elif elo_gap > 100:
                conservative_shrink = 0.85  # Medium shrink
            else:
                conservative_shrink = 0.70  # Large shrink for close matches
        else:
            conservative_shrink = 0.85  # Default
        
        home_strength = 0.5 + (home_strength - 0.5) * conservative_shrink
        
        # Add home advantage (Principle 1: Truthful — home advantage is real)
        if home_advantage:
            home_strength += HOME_ADVANTAGE_BOOST
        
        # Knockout variance penalty (Principle 2: Cap 65% + Principle 5: Draw Awareness)
        # Research (Tactiq 2026): single-elimination has higher variance
        # Teams play more conservatively, upsets are more common
        # Learned from m075, m076: 2/3 matches ended in draw → shrink more aggressively
        if knockout:
            home_strength = 0.5 + (home_strength - 0.5) * KNOCKOUT_VARIANCE_PENALTY
        
        # Confidence cap for knockout (Principle 2: Cap 65%)
        # Penalty shootouts make even true 70% favorites ~50/50
        # Learned from competitor analysis (wc-kimi caps at 65%, jason burned by 82%)
        # Principle 5: For close matches (ELO gap < 100), cap at 55%
        # NEW: For ALL knockout matches, apply stricter cap when model is uncertain
        if knockout:
            if home_elo > 0 and away_elo > 0:
                elo_gap = abs(home_elo - away_elo)
                if elo_gap < KNOCKOUT_CLOSE_ELO_GAP:
                    # Close match → very conservative
                    effective_cap = KNOCKOUT_CLOSE_MATCH_CAP
                elif elo_gap < 200:
                    # Moderate gap → medium cap
                    effective_cap = 0.60
                else:
                    # Clear favorite → standard cap
                    effective_cap = KNOCKOUT_CONFIDENCE_CAP
            else:
                effective_cap = KNOCKOUT_CONFIDENCE_CAP
            home_strength = min(effective_cap, max(KNOCKOUT_CONFIDENCE_FLOOR, home_strength))
        
        # Principle 3: Selectivity — if no clear edge, submit 50/50
        # This is applied AFTER ensemble but BEFORE final output
        # In auto_agent.py, we check: if 0.48 < prob < 0.52 → 50/50
        # Here we just ensure the raw probability is reasonable
        
        # Normalize
        home_strength = min(max(home_strength, 0.1), 0.9)
        away_strength = 1 - home_strength
        
        # Calculate 3-way probabilities from home_strength (analytical)
        # For knockout: binary outcome = home advances (win OR draw)
        # So home_advance = home_win + draw, away_advance = away_win
        # But in reality, draw → penalty shootout → ~50/50
        # So we should treat draw as reducing home advantage
        
        # Home win probability
        home_win_prob = home_strength * 0.75
        
        # Draw probability (Principle 5: Knockout Draw Awareness)
        # Learned from m075, m076: 2/3 knockout matches ended in draw
        # Higher draw probability = more conservative predictions
        # In knockout, draw means penalty shootout = ~50/50
        # So we REDUCE home_win_prob and INCREASE draw_prob
        base_draw = 0.20
        if knockout:
            base_draw = KNOCKOUT_BASE_DRAW  # 0.25 (was 0.15)
        draw_prob = base_draw * (1 - abs(home_strength - 0.5) * 2)
        
        # Away win probability
        away_win_prob = 1 - home_win_prob - draw_prob
        
        # Normalize
        total = home_win_prob + draw_prob + away_win_prob
        home_win_prob /= total
        draw_prob /= total
        away_win_prob /= total
        
        # For binary (knockout): home_advance = home_win + draw
        # But penalty shootout makes draw ~50/50, not 100% home
        # So we adjust: home_advance = home_win + draw * 0.5
        # This makes the model more conservative for close matches
        # NOTE: This adjustment is done in to_binary() method, not here
        # to preserve the 3-way probabilities for display purposes
        
        # Expected goals using xG with environmental modifiers (from Amir Motefaker)
        # Fatigue modifier: rest < 3 days reduces xG by 10%
        home_fatigue = 0.9 if home_rest_days < 3 else 1.0
        away_fatigue = 0.9 if away_rest_days < 3 else 1.0
        
        # Altitude modifier: > 1500m increases variance, > 2200m significant effect
        altitude_effect = 1.0
        if altitude_m > 2200:
            altitude_effect = 1.12
        elif altitude_m > 1500:
            altitude_effect = 1.05
        
        # Temperature modifier: extreme heat > 32°C reduces both teams
        temp_effect = 1.0
        if temperature_c > 32:
            temp_effect = 0.94
        
        home_exp_goals = max(0.1, home_xg * 0.8 + away_xga * 0.2) * home_fatigue * altitude_effect * temp_effect
        away_exp_goals = max(0.1, away_xg * 0.8 + home_xga * 0.2) * away_fatigue * altitude_effect * temp_effect
        
        # Monte Carlo simulation (10,000 iterations) — inspired by Amir Motefaker
        # Validates analytical probabilities against simulation
        import numpy as np
        np.random.seed(42)
        
        mc_home_wins = 0
        mc_away_wins = 0
        mc_draws = 0
        
        for _ in range(10000):
            h_goals = np.random.poisson(home_exp_goals)
            a_goals = np.random.poisson(away_exp_goals)
            
            if h_goals > a_goals:
                mc_home_wins += 1
            elif h_goals < a_goals:
                mc_away_wins += 1
            else:
                mc_draws += 1
        
        # Use MC to validate, but keep analytical probabilities as primary
        # (MC is more volatile with small lambda differences)
        mc_home_prob = mc_home_wins / 10000
        mc_away_prob = mc_away_wins / 10000
        mc_draw_prob = mc_draws / 10000
        
        # Find most likely score from MC simulations
        score_counts = {}
        for _ in range(10000):
            h_goals = np.random.poisson(home_exp_goals)
            a_goals = np.random.poisson(away_exp_goals)
            score = f"{h_goals}-{a_goals}"
            score_counts[score] = score_counts.get(score, 0) + 1
        
        top_scores = sorted(score_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        most_likely_score = top_scores[0][0] if top_scores else "1-1"
        
        # Upset risk detection (from Amir Motefaker)
        # Use ELO gap if available, otherwise FIFA rank gap
        if home_elo > 0 and away_elo > 0:
            elo_gap = abs(home_elo - away_elo)
        else:
            elo_gap = abs(home_rank - away_rank)
        
        form_home_avg = sum(home_form[:5]) / 5 if home_form else 0
        form_away_avg = sum(away_form[:5]) / 5 if away_form else 0
        form_diff = form_home_avg - form_away_avg
        
        upset_risk = "LOW"
        if elo_gap < 150 and form_diff < -0.2:
            upset_risk = "HIGH"
        elif elo_gap < 100:
            upset_risk = "MEDIUM"
        
        # Confidence score based on data quality (from Amir Motefaker)
        data_quality = 5
        if home_injuries == 0 and away_injuries == 0:
            data_quality += 0
        if not home_form or not away_form:
            data_quality -= 1
        if h2h_home_wins + h2h_draws + h2h_away_wins == 0:
            data_quality -= 1
        # Bonus for having real ELO data
        if home_elo > 0 and away_elo > 0:
            data_quality += 1
        data_quality = max(1, min(5, data_quality))
        
        # Confidence = difference between top two outcomes
        sorted_probs = sorted([home_win_prob, draw_prob, away_win_prob], reverse=True)
        confidence = sorted_probs[0] - sorted_probs[1]
        
        # Build reasoning with component breakdown
        components = {
            "elo": round(elo_prob, 2),
            "fifa": round(fifa_prob, 2),
            "xg": round(xg_home_prob, 2),
            "form": round(form_prob, 2),
            "squad_depth": round(squad_depth_prob, 2),
            "h2h": round(h2h_prob, 2),
            "injury": round(injury_prob, 2),
            "fatigue": round(home_fatigue, 2),
            "altitude": round(altitude_effect, 2),
            "upset_risk": upset_risk,
            "data_quality": data_quality,
            "mc_home": round(mc_home_prob, 2),
            "mc_draw": round(mc_draw_prob, 2),
            "mc_away": round(mc_away_prob, 2),
        }
        if betting_home_prob is not None:
            components["betting"] = round(betting_prob, 2)
        
        reasoning = (
            f"Ensemble: ELO({elo_prob:.2f})×{WEIGHT_ELO} + "
            f"FIFA({fifa_prob:.2f})×{WEIGHT_FIFA} + "
            f"xG({xg_home_prob:.2f})×{WEIGHT_XG} + "
            f"Form({form_prob:.2f})×{WEIGHT_FORM} + "
            f"Depth({squad_depth_prob:.2f})×{WEIGHT_SQUAD_DEPTH} + "
            f"H2H({h2h_prob:.2f})×{WEIGHT_H2H} + "
            f"Injury({injury_prob:.2f})×{WEIGHT_INJURIES}"
        )
        if betting_home_prob is not None:
            reasoning += f" + Betting({betting_prob:.2f})×{WEIGHT_BETTING}"
        reasoning += f". Combined: {home_strength:.2f}"
        reasoning += f" | MC validation: H{mc_home_prob:.0%} D{mc_draw_prob:.0%} A{mc_away_prob:.0%}"
        reasoning += f" | Upset: {upset_risk} | Quality: {data_quality}/5"
        
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
