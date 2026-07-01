import sys
import os
import json

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from wc26_bnaul.json_db import load_json_db, save_json_db, update_team_injury

def enrich():
    print("🔄 Bắt đầu làm giàu dữ liệu (Enrichment)...")

    # 1. Enrich Referees
    referees = load_json_db("referees_db.json")
    referees["Michael Oliver"] = {
        "nationality": "England",
        "matches_officiated": 180,
        "yellow_cards_per_match": 3.8,
        "red_cards_per_match": 0.12,
        "penalties_per_match": 0.31,
        "home_win_percentage": 45.0
    }
    referees["Anthony Taylor"] = {
        "nationality": "England",
        "matches_officiated": 165,
        "yellow_cards_per_match": 4.0,
        "red_cards_per_match": 0.18,
        "penalties_per_match": 0.25,
        "home_win_percentage": 46.5
    }
    referees["Danny Makkelie"] = {
        "nationality": "Netherlands",
        "matches_officiated": 140,
        "yellow_cards_per_match": 3.9,
        "red_cards_per_match": 0.14,
        "penalties_per_match": 0.22,
        "home_win_percentage": 44.0
    }
    save_json_db("referees_db.json", referees)
    print("✅ Đã làm giàu dữ liệu Trọng tài (Referees).")

    # 2. Enrich Coaches in Teams
    teams = load_json_db("teams_db.json")
    coach_mapping = {
        "Argentina": {"name": "Lionel Scaloni", "preferred_formation": "4-3-3", "tactical_style": "possession_attacking"},
        "England": {"name": "Thomas Tuchel", "preferred_formation": "4-2-3-1", "tactical_style": "direct_attacking"},
        "France": {"name": "Didier Deschamps", "preferred_formation": "4-2-3-1", "tactical_style": "balanced_counter"},
        "Brazil": {"name": "Dorival Júnior", "preferred_formation": "4-2-3-1", "tactical_style": "attacking_flair"},
        "Germany": {"name": "Julian Nagelsmann", "preferred_formation": "4-2-3-1", "tactical_style": "high_press_attacking"},
        "Spain": {"name": "Luis de la Fuente", "preferred_formation": "4-3-3", "tactical_style": "possession_technical"},
        "Portugal": {"name": "Roberto Martínez", "preferred_formation": "4-3-3", "tactical_style": "balanced_attacking"},
        "DR Congo": {"name": "Sébastien Desabre", "preferred_formation": "4-1-4-1", "tactical_style": "organized_counter"}
    }
    
    for team, coach_info in coach_mapping.items():
        if team in teams:
            teams[team]["coach"] = coach_info
    
    # 3. Simulate Injury from News (e.g., Saka is injured, Foden is doubtful)
    if "England" in teams:
        for player in teams["England"].get("key_players", []):
            if player["name"] == "Saka":
                player["is_injured"] = True
    save_json_db("teams_db.json", teams)
    print("✅ Đã làm giàu dữ liệu Huấn luyện viên (Coaches) & Cập nhật Chấn thương (Injuries).")

    # 4. Enrich Betting Odds for m080
    betting = load_json_db("betting_db.json")
    betting["m080"] = {
        "bookmaker": "Pinnacle",
        "odds_opening": {
            "home": 1.40,
            "draw": 4.50,
            "away": 9.00
        },
        "odds_closing": {
            "home": 1.35,  # Odds for England dropped (more favored)
            "draw": 4.80,
            "away": 10.50
        },
        "implied_probability": {
            "home": 0.74,
            "draw": 0.20,
            "away": 0.09
        }
    }
    save_json_db("betting_db.json", betting)
    print("✅ Đã làm giàu dữ liệu Kèo nhà cái (Betting Odds).")
    print("🎉 Hoàn tất quá trình làm giàu dữ liệu giả lập (Enrichment)!")

if __name__ == "__main__":
    enrich()
