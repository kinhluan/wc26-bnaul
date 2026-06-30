#!/usr/bin/env python3
"""
Auto-Agent for wc26-bnaul — Fully Autonomous Prediction Agent with Multi-Step Reasoning

Chạy hoàn toàn tự động với iterative reasoning loop:
1. Iteration 1: Gather raw data (news, injuries, FIFA reports, environmental factors)
2. Iteration 2: Analyze & synthesize (cross-reference sources, detect contradictions)
3. Iteration 3: Deep reasoning (evaluate edge cases, upset risk, model limitations)
4. Iteration 4+: Meta-analysis (confidence calibration, bias detection, final adjustment)
5. Final: Ensemble prediction → submit → log

Usage:
    uv run python -m wc26_bnaul.auto_agent --dry-run    # Preview only
    uv run python -m wc26_bnaul.auto_agent --live       # Actually submit
    uv run python -m wc26_bnaul.auto_agent --match m074 # Single match
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, "src")

from wc26_bnaul import api_request
from wc26_bnaul.ensemble_predictor import (
    EnsemblePredictor, MatchPrediction,
    KNOCKOUT_CONFIDENCE_CAP, KNOCKOUT_CONFIDENCE_FLOOR,
    SELECTIVITY_THRESHOLD_LOW, SELECTIVITY_THRESHOLD_HIGH,
)
from wc26_bnaul.batch_predict import get_team_data, TEAM_DB, get_venue_data, VENUE_DB
from wc26_bnaul.prediction_logger import PredictionLogger
from wc26_bnaul.news_monitor_real import (
    search_news_for_teams,
    analyze_news_content,
    fetch_injuries_for_match,
    analyze_injury_impact,
)


logger = PredictionLogger()


# =============================================================================
# ENVIRONMENTAL DATA SOURCES
# =============================================================================

# WC 2026 venue data (stadium, city, altitude, typical temperature)
WC2026_VENUES = {
    # USA venues
    "MetLife Stadium": {"city": "New York", "altitude_m": 3, "avg_temp_c": 22, "country": "USA"},
    "SoFi Stadium": {"city": "Los Angeles", "altitude_m": 30, "avg_temp_c": 24, "country": "USA"},
    "AT&T Stadium": {"city": "Dallas", "altitude_m": 170, "avg_temp_c": 28, "country": "USA"},
    "Mercedes-Benz Stadium": {"city": "Atlanta", "altitude_m": 300, "avg_temp_c": 26, "country": "USA"},
    "Hard Rock Stadium": {"city": "Miami", "altitude_m": 3, "avg_temp_c": 29, "country": "USA"},
    "Levi's Stadium": {"city": "San Francisco", "altitude_m": 5, "avg_temp_c": 18, "country": "USA"},
    "Lumen Field": {"city": "Seattle", "altitude_m": 50, "avg_temp_c": 16, "country": "USA"},
    "Gillette Stadium": {"city": "Boston", "altitude_m": 50, "avg_temp_c": 20, "country": "USA"},
    "Lincoln Financial Field": {"city": "Philadelphia", "altitude_m": 12, "avg_temp_c": 23, "country": "USA"},
    "NRG Stadium": {"city": "Houston", "altitude_m": 15, "avg_temp_c": 30, "country": "USA"},
    "Soldier Field": {"city": "Chicago", "altitude_m": 180, "avg_temp_c": 21, "country": "USA"},
    "Bank of America Stadium": {"city": "Charlotte", "altitude_m": 220, "avg_temp_c": 25, "country": "USA"},
    # Canada venues
    "BC Place": {"city": "Vancouver", "altitude_m": 2, "avg_temp_c": 15, "country": "Canada"},
    "BMO Field": {"city": "Toronto", "altitude_m": 77, "avg_temp_c": 19, "country": "Canada"},
    # Mexico venues
    "Estadio Azteca": {"city": "Mexico City", "altitude_m": 2240, "avg_temp_c": 18, "country": "Mexico"},
    "Estadio Akron": {"city": "Guadalajara", "altitude_m": 1545, "avg_temp_c": 22, "country": "Mexico"},
    "Estadio BBVA": {"city": "Monterrey", "altitude_m": 512, "avg_temp_c": 26, "country": "Mexico"},
}

# Team continent mapping (for travel fatigue estimation)
TEAM_CONTINENT = {
    "Argentina": "SA", "Brazil": "SA", "Uruguay": "SA", "Colombia": "SA",
    "Ecuador": "SA", "Paraguay": "SA", "Chile": "SA", "Peru": "SA",
    "France": "EU", "England": "EU", "Spain": "EU", "Germany": "EU",
    "Portugal": "EU", "Netherlands": "EU", "Italy": "EU", "Belgium": "EU",
    "Croatia": "EU", "Switzerland": "EU", "Sweden": "EU", "Austria": "EU",
    "Japan": "AS", "South Korea": "AS", "Australia": "AS", "Iran": "AS",
    "USA": "NA", "Mexico": "NA", "Canada": "NA", "Costa Rica": "NA",
    "Morocco": "AF", "Senegal": "AF", "Egypt": "AF", "Ghana": "AF",
    "Ivory Coast": "AF", "DR Congo": "AF", "Nigeria": "AF", "Algeria": "AF",
}


def get_match_environment(match: Dict) -> Dict:
    """
    Extract environmental factors for a match using VENUE_DB from Amir dataset.
    
    Returns:
        {
            "venue": str,
            "altitude_m": int,
            "temperature_c": int,
            "home_rest_days": int,
            "away_rest_days": int,
            "home_travel_km": int,
            "away_travel_km": int,
            "is_home_continent": bool,
            "venue_xg_modifier": float,
            "weather_category": str,
            "surface": str,
        }
    """
    venue = match.get("venue", "")
    kickoff = match.get("kickoff_utc", "")
    home = match.get("home", "")
    away = match.get("away", "")
    
    # Get venue data from VENUE_DB (Amir dataset with xG modifiers)
    venue_data = get_venue_data(venue)
    
    # Estimate rest days from kickoff time
    home_rest_days = estimate_rest_days(home, kickoff)
    away_rest_days = estimate_rest_days(away, kickoff)
    
    # Estimate travel (simplified: based on continent difference)
    home_continent = TEAM_CONTINENT.get(home, "EU")
    away_continent = TEAM_CONTINENT.get(away, "EU")
    venue_country = venue_data.get("country", "USA")
    
    venue_continent = "NA"
    if venue_country == "Mexico":
        venue_continent = "NA"
    elif venue_country == "Canada":
        venue_continent = "NA"
    
    home_travel_km = 0 if home_continent == venue_continent else 5000
    away_travel_km = 0 if away_continent == venue_continent else 5000
    
    # Temperature: use venue's average temp, adjust for match time
    temp_c = venue_data.get("avg_temp_c", 22)
    if kickoff:
        try:
            kickoff_dt = datetime.fromisoformat(kickoff.replace('Z', '+00:00'))
            hour = kickoff_dt.hour
            # Evening matches are cooler
            if hour >= 20:
                temp_c = max(15, temp_c - 5)
            elif hour <= 14:
                temp_c = min(40, temp_c + 3)
        except:
            pass
    
    return {
        "venue": venue,
        "city": venue_data.get("city", "Unknown"),
        "altitude_m": venue_data.get("altitude_m", 100),
        "temperature_c": temp_c,
        "home_rest_days": home_rest_days,
        "away_rest_days": away_rest_days,
        "home_travel_km": home_travel_km,
        "away_travel_km": away_travel_km,
        "is_home_continent": home_continent == venue_continent,
        "venue_xg_modifier": venue_data.get("xg_modifier", 1.0),
        "weather_category": venue_data.get("weather_category", "mild"),
        "surface": venue_data.get("surface", "natural_grass"),
        "humidity_pct": venue_data.get("humidity_pct", 60),
    }


def estimate_rest_days(team: str, kickoff_utc: str) -> int:
    """Estimate rest days based on team schedule and kickoff time."""
    # In knockout stage, FIFA mandates minimum 3 days rest
    # Top teams that won group stage early get 4-5 days
    # Teams that went to extra time/penalties get minimum 3 days
    
    # Default: assume standard 5 days for teams that advanced normally
    # If we have match history, calculate from last match
    try:
        # Try to get from API
        data = api_request("GET", f"/fixtures?team={team}&status=completed")
        matches = data.get("matches", [])
        if matches:
            last_match = matches[-1]
            last_kickoff = datetime.fromisoformat(last_match.get("kickoff_utc", "").replace('Z', '+00:00'))
            current_kickoff = datetime.fromisoformat(kickoff_utc.replace('Z', '+00:00'))
            rest_hours = (current_kickoff - last_kickoff).total_seconds() / 3600
            rest_days = max(2, int(rest_hours / 24))
            return rest_days
    except:
        pass
    
    # Fallback: assume standard knockout rest
    return 5


# =============================================================================
# MULTI-STEP REASONING LOOP
# =============================================================================

class ReasoningIteration:
    """Single iteration of reasoning with structured output."""
    
    def __init__(self, iteration_num: int, name: str):
        self.iteration_num = iteration_num
        self.name = name
        self.inputs: Dict = {}
        self.analysis: str = ""
        self.key_findings: List[str] = []
        self.confidence_delta: float = 0.0  # How much this iteration changed confidence
        self.recommendation: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "iteration": self.iteration_num,
            "name": self.name,
            "inputs": self.inputs,
            "analysis": self.analysis,
            "key_findings": self.key_findings,
            "confidence_delta": self.confidence_delta,
            "recommendation": self.recommendation,
        }


class AgentReasoningLoop:
    """
    Multi-step reasoning loop for match prediction.
    
    Iteration 1: Data Gathering
    - Fetch news, injuries, environmental data
    - Collect raw statistics from TEAM_DB
    - Identify data gaps and uncertainties
    
    Iteration 2: Cross-Analysis & Synthesis
    - Cross-reference news with statistical data
    - Detect contradictions (e.g., news says "strong form" but xG is low)
    - Weight sources by reliability
    
    Iteration 3: Deep Reasoning & Edge Case Detection
    - Evaluate upset risk (underdog with momentum, favorite with fatigue)
    - Consider model limitations (unknown teams, missing data)
    - Apply knockout-specific adjustments
    
    Iteration 4: Meta-Analysis & Confidence Calibration
    - Review previous iterations for bias
    - Calibrate confidence based on data quality
    - Final probability adjustment with uncertainty bounds
    
    Iteration 5: Final Decision & Rationale
    - Synthesize all iterations into final prediction
    - Generate detailed reasoning string
    - Determine if prediction should be submitted or skipped
    """
    
    def __init__(self, match_id: str, home: str, away: str, match_data: Dict):
        self.match_id = match_id
        self.home = home
        self.away = away
        self.match_data = match_data
        self.iterations: List[ReasoningIteration] = []
        self.final_prediction: Optional[MatchPrediction] = None
        self.final_binary: Tuple[float, float] = (0.5, 0.5)
        self.should_submit: bool = True
        self.uncertainty_bounds: Tuple[float, float] = (0.35, 0.65)
    
    def run(self, check_news: bool = True) -> Dict:
        """Run all reasoning iterations and return final decision."""
        print(f"\n{'='*70}")
        print(f"AGENT REASONING LOOP: {self.match_id} — {self.home} vs {self.away}")
        print(f"{'='*70}")
        
        # Iteration 1: Data Gathering
        self._iteration_1_gather_data(check_news)
        
        # Iteration 2: Cross-Analysis & Synthesis
        self._iteration_2_cross_analysis()
        
        # Iteration 3: Deep Reasoning & Edge Cases
        self._iteration_3_deep_reasoning()
        
        # Iteration 4: Meta-Analysis & Confidence Calibration
        self._iteration_4_meta_analysis()
        
        # Iteration 5: Final Decision
        self._iteration_5_final_decision()
        
        return self._build_final_report()
    
    def _iteration_1_gather_data(self, check_news: bool):
        """Iteration 1: Gather all raw data sources."""
        iter1 = ReasoningIteration(1, "Data Gathering")
        
        print(f"\n[Iteration 1/5] Data Gathering...")
        
        # 1a. Team statistics from TEAM_DB
        home_data = get_team_data(self.home)
        away_data = get_team_data(self.away)
        
        # 1b. Environmental data
        env = get_match_environment(self.match_data)
        
        # 1c. News (if enabled)
        news_analysis = {"severity": "low", "keywords_found": [], "probability_adjustment": 0, "summary": "Skipped"}
        if check_news:
            try:
                news = search_news_for_teams(self.home, self.away, hours_back=24)
                news_analysis = analyze_news_content(news, self.home, self.away)
                print(f"  ✓ News: {news_analysis['severity']} severity, {len(news_analysis['keywords_found'])} keywords")
            except Exception as e:
                print(f"  ⚠ News fetch failed: {e}")
        
        # 1d. Injuries
        injury_analysis = {"severity": "low", "home_impact": 0, "away_impact": 0, "probability_adjustment": 0}
        try:
            injuries = fetch_injuries_for_match(self.home, self.away)
            injury_analysis = analyze_injury_impact(injuries)
            print(f"  ✓ Injuries: {injury_analysis['severity']} severity")
        except Exception as e:
            print(f"  ⚠ Injury fetch failed: {e}")
        
        # Store inputs
        iter1.inputs = {
            "home_data": home_data,
            "away_data": away_data,
            "environment": env,
            "news": news_analysis,
            "injuries": injury_analysis,
        }
        
        # Key findings from raw data
        iter1.key_findings = [
            f"FIFA Rank: {self.home} #{home_data['rank']} vs {self.away} #{away_data['rank']}",
            f"xG: {self.home} {home_data['xg']:.1f} vs {away_data['xg']:.1f}",
            f"Form: {self.home} {home_data['form']} vs {away_data['form']}",
            f"Venue: {env['city']} ({env['altitude_m']}m, {env['temperature_c']}°C)",
            f"Rest: {self.home} {env['home_rest_days']}d, {self.away} {env['away_rest_days']}d",
            f"News: {news_analysis['severity']} severity",
            f"Injuries: {injury_analysis['severity']} severity",
        ]
        
        # Data quality assessment
        data_gaps = []
        if home_data["rank"] > 40 or away_data["rank"] > 40:
            data_gaps.append("Low-ranked team(s) — limited data")
        if not home_data.get("h2h") or not away_data.get("h2h"):
            data_gaps.append("Missing H2H data")
        if env["altitude_m"] > 1500:
            data_gaps.append("High altitude — potential upset factor")
        
        iter1.analysis = f"Data gathering complete. {len(iter1.key_findings)} data points collected. {len(data_gaps)} gaps identified."
        iter1.recommendation = "Proceed to cross-analysis with caution for identified gaps."
        
        self.iterations.append(iter1)
        print(f"  → {iter1.analysis}")
    
    def _iteration_2_cross_analysis(self):
        """Iteration 2: Cross-reference sources and detect contradictions."""
        iter2 = ReasoningIteration(2, "Cross-Analysis & Synthesis")
        iter1 = self.iterations[0]
        
        print(f"\n[Iteration 2/5] Cross-Analysis & Synthesis...")
        
        home_data = iter1.inputs["home_data"]
        away_data = iter1.inputs["away_data"]
        news = iter1.inputs["news"]
        injuries = iter1.inputs["injuries"]
        env = iter1.inputs["environment"]
        
        contradictions = []
        reinforcements = []
        
        # Check 1: News vs Form
        form_home_avg = sum(home_data["form"]) / 5 if home_data["form"] else 0
        form_away_avg = sum(away_data["form"]) / 5 if away_data["form"] else 0
        
        if news["severity"] == "high" and form_home_avg > 0.5:
            contradictions.append("News reports issues but form is strong — verify source reliability")
        elif news["severity"] == "low" and form_home_avg < 0:
            reinforcements.append("Form is poor and no positive news — consistent signal")
        
        # Check 2: Rank vs xG
        rank_diff = home_data["rank"] - away_data["rank"]  # Negative = home favored
        xg_diff = home_data["xg"] - away_data["xg"]  # Positive = home favored
        
        if rank_diff < 0 and xg_diff < 0:
            contradictions.append("Rank favors home but xG favors away — model conflict")
        elif rank_diff < 0 and xg_diff > 0:
            reinforcements.append("Rank and xG both favor home — strong signal")
        
        # Check 3: Injuries vs News
        if injuries["severity"] == "high" and news["severity"] == "low":
            contradictions.append("Injuries detected but no news coverage — possible data lag")
        elif injuries["severity"] == "high" and news["severity"] == "high":
            reinforcements.append("Injuries confirmed by news — high confidence adjustment")
        
        # Check 4: Environmental factors
        env_factors = []
        if env["altitude_m"] > 1500:
            env_factors.append(f"High altitude ({env['altitude_m']}m) — favors acclimated teams")
        if env["temperature_c"] > 32:
            env_factors.append(f"Extreme heat ({env['temperature_c']}°C) — reduces intensity")
        if env["home_rest_days"] < 3 or env["away_rest_days"] < 3:
            env_factors.append("Short rest — fatigue impact")
        if env["home_travel_km"] > 3000 or env["away_travel_km"] > 3000:
            env_factors.append("Long travel — jet lag factor")
        
        iter2.inputs = {
            "contradictions": contradictions,
            "reinforcements": reinforcements,
            "env_factors": env_factors,
        }
        
        iter2.key_findings = contradictions + reinforcements + env_factors
        iter2.analysis = f"Cross-analysis: {len(contradictions)} contradictions, {len(reinforcements)} reinforcements, {len(env_factors)} environmental factors."
        iter2.recommendation = "Resolve contradictions by downweighting conflicting sources. Amplify reinforcements."
        
        self.iterations.append(iter2)
        print(f"  → {iter2.analysis}")
        for finding in iter2.key_findings[:5]:
            print(f"     • {finding}")
    
    def _iteration_3_deep_reasoning(self):
        """Iteration 3: Deep reasoning — upset risk, model limitations, knockout factors."""
        iter3 = ReasoningIteration(3, "Deep Reasoning & Edge Cases")
        iter1 = self.iterations[0]
        iter2 = self.iterations[1]
        
        print(f"\n[Iteration 3/5] Deep Reasoning & Edge Cases...")
        
        home_data = iter1.inputs["home_data"]
        away_data = iter1.inputs["away_data"]
        env = iter1.inputs["environment"]
        
        # Upset risk evaluation
        upset_factors = []
        
        # Factor 1: Rank gap small + underdog has momentum
        rank_gap = abs(home_data["rank"] - away_data["rank"])
        if rank_gap < 10:
            form_home = sum(home_data["form"]) / 5 if home_data["form"] else 0
            form_away = sum(away_data["form"]) / 5 if away_data["form"] else 0
            if form_away > form_home + 0.3:
                upset_factors.append("Small rank gap + away team in better form → upset risk MEDIUM")
        
        # Factor 2: Favorite with fatigue + short rest
        if home_data["rank"] < away_data["rank"]:
            favorite = self.home
            underdog = self.away
        else:
            favorite = self.away
            underdog = self.home
        
        fav_rest = env["home_rest_days"] if favorite == self.home else env["away_rest_days"]
        if fav_rest < 3:
            upset_factors.append(f"Favorite ({favorite}) has only {fav_rest} days rest → upset risk HIGH")
        
        # Factor 3: High altitude favors underdog
        if env["altitude_m"] > 1500:
            # Teams from high altitude countries (Bolivia, Ecuador, Mexico) have advantage
            high_altitude_teams = ["Bolivia", "Ecuador", "Mexico", "Peru", "Colombia"]
            if underdog in high_altitude_teams:
                upset_factors.append(f"High altitude favors {underdog} (altitude-adapted) → upset risk MEDIUM")
        
        # Factor 4: Knockout shootout factor
        # Even 70% favorites only win ~60% in knockouts due to extra time/shootouts
        upset_factors.append("Knockout format: penalty shootouts reduce favorite advantage by ~10%")
        
        # Model limitation flags
        limitations = []
        if self.home.startswith("W") or self.away.startswith("W"):
            limitations.append("Winner placeholder team — no data available, using defaults")
        if home_data["rank"] > 50 or away_data["rank"] > 50:
            limitations.append("Low-ranked team — model confidence reduced")
        if not home_data.get("h2h") or not away_data.get("h2h"):
            limitations.append("Missing H2H data — H2H component unreliable")
        
        iter3.inputs = {
            "upset_factors": upset_factors,
            "limitations": limitations,
        }
        
        iter3.key_findings = upset_factors + limitations
        iter3.analysis = f"Deep reasoning: {len(upset_factors)} upset factors, {len(limitations)} model limitations."
        iter3.recommendation = "Apply knockout shrinkage (-5%), cap confidence at 65%, widen uncertainty bounds."
        iter3.confidence_delta = -0.05  # Reduce confidence due to upset risk
        
        self.iterations.append(iter3)
        print(f"  → {iter3.analysis}")
        for finding in iter3.key_findings[:5]:
            print(f"     • {finding}")
    
    def _iteration_4_meta_analysis(self):
        """Iteration 4: Meta-analysis — review for bias, calibrate confidence."""
        iter4 = ReasoningIteration(4, "Meta-Analysis & Confidence Calibration")
        
        print(f"\n[Iteration 4/5] Meta-Analysis & Confidence Calibration...")
        
        # Review previous iterations for bias patterns
        bias_checks = []
        
        # Bias 1: Recency bias (overweighting last match)
        iter1 = self.iterations[0]
        home_form = iter1.inputs["home_data"]["form"]
        if home_form and home_form[-1] == -1:
            bias_checks.append("Home team lost last match — check for recency bias in form weighting")
        
        # Bias 2: Confirmation bias (only seeing data that supports initial hypothesis)
        iter2 = self.iterations[1]
        if len(iter2.inputs.get("reinforcements", [])) > len(iter2.inputs.get("contradictions", [])) * 2:
            bias_checks.append("Many reinforcements, few contradictions — possible confirmation bias")
        
        # Bias 3: Anchoring bias (overweighting FIFA rank)
        rank_diff = abs(iter1.inputs["home_data"]["rank"] - iter1.inputs["away_data"]["rank"])
        if rank_diff > 15:
            bias_checks.append("Large rank gap — ensure not anchoring too heavily on rank")
        
        # Confidence calibration based on data quality
        data_quality = 5
        if iter1.inputs["home_data"]["rank"] > 40:
            data_quality -= 1
        if not iter1.inputs["home_data"].get("h2h"):
            data_quality -= 1
        if iter1.inputs["news"]["severity"] == "high":
            data_quality -= 1  # High uncertainty from news
        
        data_quality = max(1, min(5, data_quality))
        
        # Map data quality to confidence bounds
        if data_quality >= 4:
            uncertainty_bounds = (0.30, 0.70)
        elif data_quality >= 3:
            uncertainty_bounds = (0.35, 0.65)
        elif data_quality >= 2:
            uncertainty_bounds = (0.40, 0.60)
        else:
            uncertainty_bounds = (0.45, 0.55)  # Very uncertain — near 50/50
        
        iter4.inputs = {
            "bias_checks": bias_checks,
            "data_quality": data_quality,
            "uncertainty_bounds": uncertainty_bounds,
        }
        
        iter4.key_findings = bias_checks + [f"Data quality: {data_quality}/5", f"Uncertainty bounds: {uncertainty_bounds[0]:.0%}-{uncertainty_bounds[1]:.0%}"]
        iter4.analysis = f"Meta-analysis: {len(bias_checks)} bias flags, data quality {data_quality}/5, confidence bounds {uncertainty_bounds[0]:.0%}-{uncertainty_bounds[1]:.0%}."
        iter4.recommendation = f"Set uncertainty bounds to {uncertainty_bounds[0]:.0%}-{uncertainty_bounds[1]:.0%}. Flag {len(bias_checks)} potential biases."
        
        self.uncertainty_bounds = uncertainty_bounds
        self.iterations.append(iter4)
        print(f"  → {iter4.analysis}")
    
    def _iteration_5_final_decision(self):
        """Iteration 5: Final decision — synthesize all iterations."""
        iter5 = ReasoningIteration(5, "Final Decision & Rationale")
        
        print(f"\n[Iteration 5/5] Final Decision & Rationale...")
        
        iter1 = self.iterations[0]
        home_data = iter1.inputs["home_data"]
        away_data = iter1.inputs["away_data"]
        env = iter1.inputs["environment"]
        news = iter1.inputs["news"]
        injuries = iter1.inputs["injuries"]
        
        # Run ensemble model with ALL parameters (ELO, squad_depth, venue)
        predictor = EnsemblePredictor()
        result = predictor.predict(
            home_team=self.home,
            away_team=self.away,
            home_rank=home_data["rank"],
            away_rank=away_data["rank"],
            home_elo=home_data.get("elo", 0),
            away_elo=away_data.get("elo", 0),
            home_xg=home_data["xg"],
            home_xga=home_data["xga"],
            away_xg=away_data["xg"],
            away_xga=away_data["xga"],
            home_form=home_data["form"],
            away_form=away_data["form"],
            home_squad_depth=home_data.get("squad_depth", 5.0),
            away_squad_depth=away_data.get("squad_depth", 5.0),
            knockout=True,
            home_rest_days=env["home_rest_days"],
            away_rest_days=env["away_rest_days"],
            altitude_m=env["altitude_m"],
            temperature_c=env["temperature_c"],
        )
        
        binary = result.to_binary()
        home_prob = binary[0]
        away_prob = binary[1]
        
        # Principle 3: SELECTIVITY — if no clear edge, submit 50/50
        # Learned from jason (55% SKILL): selective submission beats overconfidence
        # Threshold: 48-52% means no meaningful edge — better to admit uncertainty
        # Principle 5: For knockout, extend threshold to 55% (learned from m075, m076)
        # Both wrong predictions were 55-59% → 50/50 would have been better
        effective_selectivity_low = SELECTIVITY_THRESHOLD_LOW
        effective_selectivity_high = SELECTIVITY_THRESHOLD_HIGH
        if is_knockout:
            # Knockout: wider selectivity band (45-55%)
            effective_selectivity_low = 0.45
            effective_selectivity_high = 0.55
        
        if effective_selectivity_low < home_prob < effective_selectivity_high:
            home_prob = 0.50
            away_prob = 0.50
            selectivity_note = f"No clear edge → 50/50 (Principle 3+5: Selectivity, knockout band {effective_selectivity_low:.0%}-{effective_selectivity_high:.0%})"
        else:
            selectivity_note = "Clear edge detected"
        
        # Principle 2: KNOCKOUT CAP 65% — already applied in ensemble_predictor
        # but double-check here for safety
        # All matches in auto-agent are knockout (WC2026 bracket)
        is_knockout = True
        if is_knockout:
            if home_prob > KNOCKOUT_CONFIDENCE_CAP:
                home_prob = KNOCKOUT_CONFIDENCE_CAP
                away_prob = 1.0 - home_prob
                selectivity_note += f" (capped at {KNOCKOUT_CONFIDENCE_CAP:.0%} — Principle 2)"
            elif home_prob < KNOCKOUT_CONFIDENCE_FLOOR:
                home_prob = KNOCKOUT_CONFIDENCE_FLOOR
                away_prob = 1.0 - home_prob
                selectivity_note += f" (floored at {KNOCKOUT_CONFIDENCE_FLOOR:.0%} — Principle 2)"
        
        # Apply uncertainty bounds from meta-analysis (additional safety)
        lower_bound, upper_bound = self.uncertainty_bounds
        if home_prob < lower_bound:
            home_prob = lower_bound
            away_prob = 1.0 - home_prob
            selectivity_note += f" (clamped to lower bound {lower_bound:.0%})"
        elif home_prob > upper_bound:
            home_prob = upper_bound
            away_prob = 1.0 - home_prob
            selectivity_note += f" (clamped to upper bound {upper_bound:.0%})"
        
        # Principle 1: TRUTHFUL SUBMISSION — log the true belief before any adjustment
        # The ensemble model already produces our true belief; we only apply
        # principled adjustments (cap, selectivity) that improve Brier score
        true_belief = binary[0]  # Before any adjustment
        adjustment = home_prob - true_belief
        if abs(adjustment) > 0.01:
            print(f"  → Adjustment: {adjustment:+.1%} (true belief {true_belief:.0%} → submitted {home_prob:.0%})")
        
        # Final decision: should we submit?
        # Skip if uncertainty is too high (bounds are 45-55)
        if self.uncertainty_bounds == (0.45, 0.55):
            self.should_submit = False
            submit_reason = "High uncertainty — recommend skipping or 50/50"
        else:
            self.should_submit = True
            submit_reason = "Confidence sufficient for submission"
        
        self.final_prediction = result
        self.final_binary = (home_prob, away_prob)
        
        # Build comprehensive reasoning string
        iter2 = self.iterations[1]  # Get iteration 2 for cross-analysis data
        reasoning_parts = [
            f"[Iter1] Data: Rank {self.home}#{home_data['rank']} vs {self.away}#{away_data['rank']}, "
            f"xG {home_data['xg']:.1f}vs{away_data['xg']:.1f}, "
            f"Venue {env['city']}({env['altitude_m']}m,{env['temperature_c']}°C)",
            f"[Iter2] Cross-analysis: {len(iter2.inputs.get('contradictions', []))} contradictions, "
            f"{len(iter2.inputs.get('reinforcements', []))} reinforcements",
            f"[Iter3] Upset risk: {len(self.iterations[2].inputs.get('upset_factors', []))} factors, "
            f"Knockout shrinkage applied",
            f"[Iter4] Meta: Data quality {self.iterations[3].inputs['data_quality']}/5, "
            f"bounds {self.uncertainty_bounds[0]:.0%}-{self.uncertainty_bounds[1]:.0%}",
            f"[Iter5] Final: {self.home} {home_prob:.0%} vs {self.away} {away_prob:.0%} — {selectivity_note}",
        ]
        
        final_reasoning = " | ".join(reasoning_parts)
        
        iter5.inputs = {
            "final_prob": [home_prob, away_prob],
            "final_score": result.most_likely_score,
            "selectivity_note": selectivity_note,
        }
        
        iter5.key_findings = [
            f"Final probability: {self.home} {home_prob:.0%} vs {self.away} {away_prob:.0%}",
            f"Most likely score: {result.most_likely_score}",
            f"Selectivity: {selectivity_note}",
            f"Submit: {self.should_submit} ({submit_reason})",
        ]
        
        iter5.analysis = f"Final decision: {self.home} {home_prob:.0%} vs {self.away} {away_prob:.0%}. {submit_reason}."
        iter5.recommendation = "Submit prediction" if self.should_submit else "Skip — too uncertain"
        
        self.iterations.append(iter5)
        print(f"  → {iter5.analysis}")
    
    def _build_final_report(self) -> Dict:
        """Build final report with all iterations."""
        return {
            "match_id": self.match_id,
            "home": self.home,
            "away": self.away,
            "iterations": [i.to_dict() for i in self.iterations],
            "final_prediction": {
                "home_prob": self.final_binary[0],
                "away_prob": self.final_binary[1],
                "score": self.final_prediction.most_likely_score if self.final_prediction else "1-1",
                "confidence": self.final_prediction.confidence if self.final_prediction else 0.1,
                "components": self.final_prediction.ensemble_components if self.final_prediction else {},
            },
            "should_submit": self.should_submit,
            "uncertainty_bounds": self.uncertainty_bounds,
        }


# =============================================================================
# AUTO PREDICT MATCH (with reasoning loop)
# =============================================================================

def auto_predict_match(match_id: str, home: str, away: str, dry_run: bool = True, check_news: bool = True) -> bool:
    """
    Fully autonomous prediction for a single match with multi-step reasoning.
    
    Steps:
    1. Run AgentReasoningLoop (5 iterations)
    2. Get final prediction with environmental parameters
    3. Submit prediction
    4. Log result with full reasoning chain
    """
    print(f"\n{'='*60}")
    print(f"AUTO PREDICT: {match_id} — {home} vs {away}")
    print(f"{'='*60}")
    
    # Get match data from API
    match_data = {"match_id": match_id, "home": home, "away": away, "venue": "", "kickoff_utc": ""}
    try:
        data = api_request("GET", f"/fixtures?match_id={match_id}")
        matches = data.get("matches", [])
        if matches:
            match_data = matches[0]
    except:
        pass
    
    # Run multi-step reasoning loop
    loop = AgentReasoningLoop(match_id, home, away, match_data)
    report = loop.run(check_news=check_news)
    
    if not report["should_submit"]:
        print(f"\n⚠️  SKIPPING: High uncertainty — recommend 50/50 or manual review")
        return False
    
    final = report["final_prediction"]
    home_prob = final["home_prob"]
    away_prob = final["away_prob"]
    score = final["score"]
    confidence = final["confidence"]
    components = final["components"]
    
    # Build reasoning from iterations
    reasoning = " | ".join([
        f"[Iter{i+1}] {loop.iterations[i].name}: {loop.iterations[i].key_findings[0] if loop.iterations[i].key_findings else 'N/A'}"
        for i in range(len(loop.iterations))
    ])
    
    # Truncate if too long
    if len(reasoning) > 500:
        reasoning = reasoning[:497] + "..."
    
    print(f"\n{'='*60}")
    print(f"FINAL: {home} {home_prob:.0%} vs {away} {away_prob:.0%}")
    print(f"Score: {score}")
    print(f"Confidence: {confidence:.0%}")
    print(f"{'='*60}")
    
    # Submit
    if dry_run:
        print(f"🚫 DRY RUN — Would submit:")
        print(f"  {match_id}: {home} {home_prob:.2f} vs {away} {away_prob:.2f}")
        print(f"  Score: {score}")
        return True
    
    print(f"🚀 SUBMITTING...")
    max_retries = 3
    for attempt in range(max_retries):
        try:
            api_request("POST", "/predictions", {
                "match_id": match_id,
                "format": "binary",
                "p": [round(home_prob, 2), round(away_prob, 2)],
                "reasoning": reasoning,
                "score": score,
            })
            
            # Log prediction with full reasoning chain
            logger.log_prediction(
                match_id=match_id,
                home_team=home,
                away_team=away,
                submitted_probs=[round(home_prob, 2), round(away_prob, 2)],
                components=components,
                predicted_score=score,
                reasoning=reasoning,
            )
            
            print(f"  ✅ Submitted: {match_id}")
            return True
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5
                print(f"  ⚠️  Rate limited (429). Retrying in {wait_time}s... ({attempt+1}/{max_retries})")
                time.sleep(wait_time)
            else:
                print(f"  ❌ Failed: {e}")
                return False
    return False


def run_auto_agent(dry_run: bool = True, match_id: str = None, check_news: bool = True):
    """Run auto-agent for all open matches or a specific match."""
    print(f"\n{'='*70}")
    print(f"AUTO AGENT — wc26-bnaul (Multi-Step Reasoning)")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"News check: {'YES' if check_news else 'NO (fast mode)'}")
    print(f"Time: {datetime.now(timezone.utc).isoformat()}")
    print(f"{'='*70}")
    
    # Get matches
    if match_id:
        data = api_request("GET", "/fixtures?status=open")
        matches = [m for m in data.get("matches", []) if m["match_id"] == match_id]
        if not matches:
            print(f"Match {match_id} not found or not open")
            return
    else:
        data = api_request("GET", "/fixtures?status=open")
        matches = data.get("matches", [])
    
    print(f"Matches to predict: {len(matches)}")
    
    success_count = 0
    for match in matches:
        mid = match["match_id"]
        home = match.get("home", "?")
        away = match.get("away", "?")
        
        if auto_predict_match(mid, home, away, dry_run=dry_run, check_news=check_news):
            success_count += 1
        
        # Rate limit: be nice to API (2 seconds between requests)
        time.sleep(2)
    
    print(f"\n{'='*70}")
    print(f"SUMMARY: {success_count}/{len(matches)} predictions submitted")
    print(f"{'='*70}")


def main():
    parser = argparse.ArgumentParser(description="Auto-Agent for wc26-bnaul (Multi-Step Reasoning)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without submitting")
    parser.add_argument("--live", action="store_true", help="Actually submit")
    parser.add_argument("--match", help="Specific match ID (default: all open)")
    parser.add_argument("--fast", action="store_true", help="Skip news check (NOT RECOMMENDED)")
    
    args = parser.parse_args()
    
    dry_run = not args.live
    # Default: check_news = True (always check news unless --fast)
    check_news = not args.fast
    run_auto_agent(dry_run=dry_run, match_id=args.match, check_news=check_news)


if __name__ == "__main__":
    main()
