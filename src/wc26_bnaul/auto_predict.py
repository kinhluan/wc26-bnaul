import json
import os
import sys
from typing import Dict, List, Optional, Tuple
from wc26_bnaul import api_request

# Team strength data based on FIFA rankings, recent form, and squad quality
# Scale: 0-100, higher = stronger
TEAM_STRENGTH = {
    # Top tier (85-95)
    "Argentina": 92,
    "France": 91,
    "Brazil": 90,
    "Spain": 89,
    "England": 88,
    "Portugal": 87,
    "Germany": 86,
    "Netherlands": 85,
    
    # Second tier (75-84)
    "Belgium": 84,
    "Croatia": 82,
    "Italy": 81,  # Not in this WC
    "Uruguay": 80,  # Not in this WC
    "Switzerland": 78,
    "Mexico": 77,
    "USA": 76,
    "Morocco": 75,
    
    # Third tier (65-74)
    "Japan": 74,
    "Senegal": 73,
    "Ecuador": 72,
    "Australia": 71,
    "Colombia": 70,
    "Sweden": 69,
    "Norway": 68,
    "Ivory Coast": 67,
    "Ghana": 66,
    "Egypt": 65,
    
    # Fourth tier (55-64)
    "Bosnia & Herzegovina": 64,
    "Algeria": 63,
    "DR Congo": 62,
    "Cape Verde": 61,
    "Paraguay": 60,
    "Austria": 59,
}

# Home advantage factor (points added to home team)
HOME_ADVANTAGE = 3.0

# Continental advantage (teams playing on their home continent)
CONTINENTAL_ADVANTAGE = {
    "North America": ["Mexico", "USA", "Canada"],
    "South America": ["Brazil", "Argentina", "Colombia", "Ecuador", "Paraguay", "Uruguay"],
    "Europe": ["France", "Germany", "Spain", "England", "Portugal", "Netherlands", "Belgium", "Croatia", "Switzerland", "Sweden", "Norway", "Bosnia & Herzegovina", "Austria"],
    "Africa": ["Morocco", "Senegal", "Ivory Coast", "Ghana", "Egypt", "Algeria", "DR Congo", "Cape Verde"],
    "Asia": ["Japan", "Australia"],
}

# Tournament is in North America (USA, Canada, Mexico)
HOST_CONTINENT = "North America"


def get_continental_advantage(team: str) -> float:
    """Calculate continental advantage for a team playing in North America."""
    for continent, teams in CONTINENTAL_ADVANTAGE.items():
        if team in teams:
            if continent == HOST_CONTINENT:
                return 2.0  # Strong advantage for North American teams
            elif continent in ["South America", "Europe"]:
                return 0.5  # Slight advantage (similar conditions, short travel)
            else:
                return 0.0  # No advantage for Africa/Asia (long travel, different climate)
    return 0.0


def calculate_win_probability(home_strength: float, away_strength: float, 
                               home_continent_bonus: float = 0.0,
                               away_continent_bonus: float = 0.0) -> Tuple[float, float, float]:
    """
    Calculate 1X2 probabilities based on team strength.
    Returns (home_win, draw, away_win) probabilities.
    """
    # Adjust strengths with bonuses
    effective_home = home_strength + home_continent_bonus
    effective_away = away_strength + away_continent_bonus
    
    # Use logistic function to convert strength difference to probability
    strength_diff = effective_home - effective_away
    
    # Base home win probability
    home_win_prob = 1 / (1 + 10 ** (-strength_diff / 20))
    
    # Draw probability decreases as strength difference increases
    # Base draw ~25%, min 10%, max 35%
    draw_prob = max(0.10, min(0.35, 0.25 - abs(strength_diff) / 100))
    
    # Adjust home and away to account for draw
    total = home_win_prob + (1 - home_win_prob)
    home_win_prob = home_win_prob * (1 - draw_prob)
    away_win_prob = (1 - home_win_prob / (1 - draw_prob)) * (1 - draw_prob)
    
    # Normalize to ensure sum = 1
    total = home_win_prob + draw_prob + away_win_prob
    home_win_prob /= total
    draw_prob /= total
    away_win_prob /= total
    
    return round(home_win_prob, 2), round(draw_prob, 2), round(away_win_prob, 2)


def calculate_binary_probability(home_strength: float, away_strength: float,
                                  home_continent_bonus: float = 0.0,
                                  away_continent_bonus: float = 0.0) -> Tuple[float, float]:
    """
    Calculate binary (knockout) advance probabilities.
    Returns (home_advance, away_advance).
    """
    effective_home = home_strength + home_continent_bonus
    effective_away = away_strength + away_continent_bonus
    
    strength_diff = effective_home - effective_away
    
    # In knockouts, draw goes to extra time/penalties (50/50 roughly)
    home_advance = 1 / (1 + 10 ** (-strength_diff / 15))
    
    # Ensure minimum 0.01 and maximum 0.99
    home_advance = max(0.01, min(0.99, home_advance))
    away_advance = 1.0 - home_advance
    
    return round(home_advance, 2), round(away_advance, 2)


def generate_reasoning(home: str, away: str, home_prob: float, away_prob: float,
                       is_knockout: bool = True) -> str:
    """Generate reasoning text for a prediction."""
    home_strength = TEAM_STRENGTH.get(home, 70)
    away_strength = TEAM_STRENGTH.get(away, 70)
    
    if home_prob > 0.6:
        confidence = "strongly favored"
    elif home_prob > 0.5:
        confidence = "slightly favored"
    else:
        confidence = "evenly matched"
    
    if is_knockout:
        if home_prob > 0.6:
            return (f"{home} is {confidence} to advance against {away}. "
                    f"With superior squad depth (strength {home_strength} vs {away_strength}) and "
                    f"tournament experience, {home} should control the match tempo and create "
                    f"more quality chances. {away} will need to be compact defensively and "
                    f"capitalise on set pieces or counter-attacks to have a chance.")
        elif home_prob > 0.5:
            return (f"{home} is {confidence} to advance against {away}. "
                    f"The match is expected to be tight given similar squad quality "
                    f"(strength {home_strength} vs {away_strength}), but {home} has "
                    f"slight advantages in key areas. Extra time or penalties are possible "
                    f"if {away} can frustrate {home}'s attack.")
        else:
            return (f"This is a very evenly matched knockout tie between {home} and {away}. "
                    f"Both teams have similar squad strength (around {home_strength}), "
                    f"making this a coin-flip encounter that could go to extra time or penalties. "
                    f"Small margins and individual brilliance will likely decide the outcome.")
    else:
        # Group stage reasoning
        pass


def predict_match(match_id: str, home: str, away: str, 
                  is_knockout: bool = True, verbose: bool = True) -> Optional[Dict]:
    """
    Generate prediction for a match and submit to ClawCup API.
    """
    home_strength = TEAM_STRENGTH.get(home, 70)
    away_strength = TEAM_STRENGTH.get(away, 70)
    
    home_continent = get_continental_advantage(home)
    away_continent = get_continental_advantage(away)
    
    if is_knockout:
        home_prob, away_prob = calculate_binary_probability(
            home_strength, away_strength, home_continent, away_continent
        )
        
        # Ensure minimum 0.01 for each
        if home_prob < 0.01:
            home_prob = 0.01
            away_prob = 0.99
        if away_prob < 0.01:
            away_prob = 0.01
            home_prob = 0.99
        
        reasoning = generate_reasoning(home, away, home_prob, away_prob, is_knockout=True)
        
        # Estimate scoreline based on probabilities
        if home_prob > 0.65:
            score = "2-0"
        elif home_prob > 0.55:
            score = "2-1"
        elif home_prob > 0.45:
            score = "1-1"
        elif home_prob > 0.35:
            score = "1-2"
        else:
            score = "0-2"
        
        payload = {
            "match_id": match_id,
            "format": "binary",
            "p": [home_prob, away_prob],
            "reasoning": reasoning,
            "exact_score": score,
        }
    else:
        # Group stage 1X2
        home_win, draw, away_win = calculate_win_probability(
            home_strength, away_strength, home_continent, away_continent
        )
        
        reasoning = generate_reasoning(home, away, home_win, away_win, is_knockout=False)
        
        payload = {
            "match_id": match_id,
            "p": [home_win, draw, away_win],
            "reasoning": reasoning,
        }
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"Match: {home} vs {away} ({match_id})")
        print(f"Home strength: {home_strength} + {home_continent:.1f} (continent)")
        print(f"Away strength: {away_strength} + {away_continent:.1f} (continent)")
        if is_knockout:
            print(f"Predicted: HOME advance {home_prob:.0%} vs AWAY advance {away_prob:.0%}")
        else:
            print(f"Predicted: HOME {home_win:.0%} | DRAW {draw:.0%} | AWAY {away_win:.0%}")
        print(f"Scoreline: {payload.get('exact_score', 'N/A')}")
        print(f"{'='*60}")
    
    return payload


def submit_prediction(match_id: str, home: str, away: str, 
                      is_knockout: bool = True, dry_run: bool = False) -> Optional[Dict]:
    """Generate and submit a prediction."""
    payload = predict_match(match_id, home, away, is_knockout, verbose=True)
    
    if payload is None:
        return None
    
    if dry_run:
        print("[DRY RUN] Would submit:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return payload
    
    try:
        # Sort payload for consistent signing
        payload = dict(sorted(payload.items()))
        result = api_request("POST", "/predictions", payload)
        print(f"✅ Submitted successfully: {result.get('match_id')}")
        return result
    except Exception as e:
        print(f"❌ Failed to submit: {e}")
        return None


def auto_predict_round_of_16(dry_run: bool = True):
    """
    Auto-predict all Round of 16 matches based on Round of 32 results.
    
    Round of 16 matchups (depend on R32 winners):
    m089: W73 (Canada/Netherlands/Morocco winner) vs W75 (Germany/Paraguay winner)
    m090: W74 (Brazil/Japan winner) vs W77 (Ivory Coast/Norway winner)
    m091: W76 (Netherlands/Morocco winner) vs W78 (France/Sweden winner)
    m092: W79 (Mexico/Ecuador winner) vs W80 (England/DR Congo winner)
    m093: W83 (Spain/Austria winner) vs W84 (Portugal/Croatia winner)
    m094: W81 (Belgium/Senegal winner) vs W82 (USA/Bosnia winner)
    m095: W86 (Australia/Egypt winner) vs W88 (Colombia/Ghana winner)
    m096: W85 (Switzerland/Algeria winner) vs W87 (Argentina/Cape Verde winner)
    """
    
    # Our predictions for R32 (what we submitted)
    r32_predictions = {
        "m074": ("Brazil", "Japan"),      # We picked Brazil
        "m075": ("Germany", "Paraguay"),  # We picked Germany
        "m076": ("Netherlands", "Morocco"), # We picked Netherlands
        "m077": ("Ivory Coast", "Norway"),  # We picked Ivory Coast
        "m078": ("France", "Sweden"),       # We picked France
        "m079": ("Mexico", "Ecuador"),      # We picked Mexico
        "m080": ("England", "DR Congo"),    # We picked England
        "m081": ("Belgium", "Senegal"),     # We picked Belgium
        "m082": ("USA", "Bosnia & Herzegovina"), # We picked USA
        "m083": ("Spain", "Austria"),       # We picked Spain
        "m084": ("Portugal", "Croatia"),    # We picked Portugal
        "m085": ("Switzerland", "Algeria"), # We picked Switzerland
        "m086": ("Australia", "Egypt"),     # We picked 50/50
        "m087": ("Argentina", "Cape Verde"), # We picked Argentina
        "m088": ("Colombia", "Ghana"),      # We picked Colombia
    }
    
    # Map R32 winners to R16 matchups
    # Format: match_id -> (home_team_source, away_team_source)
    r16_matchups = {
        "m089": ("W73", "W75"),  # Canada vs Germany/Paraguay
        "m090": ("W74", "W77"),  # Brazil/Japan vs Ivory Coast/Norway
        "m091": ("W76", "W78"),  # Netherlands/Morocco vs France/Sweden
        "m092": ("W79", "W80"),  # Mexico/Ecuador vs England/DR Congo
        "m093": ("W83", "W84"),  # Spain/Austria vs Portugal/Croatia
        "m094": ("W81", "W82"),  # Belgium/Senegal vs USA/Bosnia
        "m095": ("W86", "W88"),  # Australia/Egypt vs Colombia/Ghana
        "m096": ("W85", "W87"),  # Switzerland/Algeria vs Argentina/Cape Verde
    }
    
    # Winner mapping from R32 to R16
    # Based on our predictions:
    winner_map = {
        "W73": "Canada",           # Canada won their R32 match (m073 - not in our list, but they advanced)
        "W74": "Brazil",           # We picked Brazil (m074)
        "W75": "Germany",          # We picked Germany (m075)
        "W76": "Netherlands",      # We picked Netherlands (m076)
        "W77": "Ivory Coast",      # We picked Ivory Coast (m077)
        "W78": "France",           # We picked France (m078)
        "W79": "Mexico",           # We picked Mexico (m079)
        "W80": "England",          # We picked England (m080)
        "W81": "Belgium",          # We picked Belgium (m081)
        "W82": "USA",              # We picked USA (m082)
        "W83": "Spain",            # We picked Spain (m083)
        "W84": "Portugal",         # We picked Portugal (m084)
        "W85": "Switzerland",      # We picked Switzerland (m085)
        "W86": "Australia",        # We picked Australia (m086 - 50/50 but we'll use them)
        "W87": "Argentina",        # We picked Argentina (m087)
        "W88": "Colombia",         # We picked Colombia (m088)
    }
    
    print("\n" + "="*70)
    print("ROUND OF 16 AUTO-PREDICTIONS")
    print("Based on our Round of 32 predictions")
    print("="*70)
    
    predictions = []
    
    for match_id, (home_code, away_code) in r16_matchups.items():
        home = winner_map.get(home_code, "Unknown")
        away = winner_map.get(away_code, "Unknown")
        
        print(f"\n{'='*70}")
        print(f"Match {match_id}: {home} vs {away}")
        print(f"{'='*70}")
        
        payload = submit_prediction(match_id, home, away, is_knockout=True, dry_run=dry_run)
        if payload:
            predictions.append({
                "match_id": match_id,
                "home": home,
                "away": away,
                "payload": payload,
            })
    
    return predictions


def analyze_remaining_r32():
    """Analyze remaining Round of 32 matches (m077-m088)."""
    
    matches = [
        ("m077", "Ivory Coast", "Norway"),
        ("m078", "France", "Sweden"),
        ("m079", "Mexico", "Ecuador"),
        ("m080", "England", "DR Congo"),
        ("m081", "Belgium", "Senegal"),
        ("m082", "USA", "Bosnia & Herzegovina"),
        ("m083", "Spain", "Austria"),
        ("m084", "Portugal", "Croatia"),
        ("m085", "Switzerland", "Algeria"),
        ("m086", "Australia", "Egypt"),
        ("m087", "Argentina", "Cape Verde"),
        ("m088", "Colombia", "Ghana"),
    ]
    
    print("\n" + "="*70)
    print("ROUND OF 32 - REMAINING MATCHES ANALYSIS")
    print("="*70)
    
    for match_id, home, away in matches:
        predict_match(match_id, home, away, is_knockout=True, verbose=True)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Auto-predict World Cup matches")
    parser.add_argument("--dry-run", action="store_true", help="Show predictions without submitting")
    parser.add_argument("--round", choices=["r32", "r16"], default="r16", help="Which round to predict")
    parser.add_argument("--analyze", action="store_true", help="Analyze remaining R32 matches")
    
    args = parser.parse_args()
    
    if args.analyze:
        analyze_remaining_r32()
    elif args.round == "r16":
        auto_predict_round_of_16(dry_run=args.dry_run)
    elif args.round == "r32":
        analyze_remaining_r32()
