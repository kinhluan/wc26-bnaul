import sys
import os
import json

# Add src to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from wc26_bnaul.batch_predict import TEAM_DB
from wc26_bnaul.json_db import save_json_db

def convert():
    teams_db = {}
    matches_db = {}
    
    for team_name, data in TEAM_DB.items():
        if team_name.startswith("W") or team_name.startswith("L"):
            continue # skip placeholders
            
        # 1. Build teams_db entry
        key_players = []
        for p in data.get("key_players", []):
            key_players.append({
                "name": p,
                "position": "UNKNOWN",
                "season_rating": 7.0,
                "is_injured": False,
                "is_suspended": False
            })
            
        teams_db[team_name] = {
            "fifa_rank": data.get("rank"),
            "elo_rating": data.get("elo"),
            "confederation": data.get("confederation"),
            "host_nation": data.get("host_nation"),
            "squad_depth_score": data.get("squad_depth"),
            "xg": data.get("xg"),
            "xga": data.get("xga"),
            "form": data.get("form"),
            "injuries": data.get("injuries"),
            "coach": {
                "name": "Unknown",
                "preferred_formation": data.get("formation"),
                "tactical_style": data.get("tactical_style")
            },
            "key_players": key_players
        }
        
        # 2. Build matches_db (H2H)
        h2h_data = data.get("h2h", {})
        for opponent, stats in h2h_data.items():
            # Create a unique key e.g. "TeamA_vs_TeamB" (alphabetical to avoid duplicates)
            teams_sorted = sorted([team_name, opponent])
            match_key = f"{teams_sorted[0]}_vs_{teams_sorted[1]}"
            
            if match_key not in matches_db:
                # If we are team_name, and we are home in stats, it means home_wins = our wins
                matches_db[match_key] = {
                    "total_matches": stats.get("home_wins", 0) + stats.get("draws", 0) + stats.get("away_wins", 0),
                    "team1": teams_sorted[0],
                    "team2": teams_sorted[1],
                    f"{team_name}_wins": stats.get("home_wins", 0),
                    f"{opponent}_wins": stats.get("away_wins", 0),
                    "draws": stats.get("draws", 0),
                    "meetings": []
                }
                
    save_json_db("teams_db.json", teams_db)
    save_json_db("matches_db.json", matches_db)
    print("✅ Đã chuyển đổi dữ liệu từ batch_predict.py sang teams_db.json và matches_db.json thành công!")

if __name__ == "__main__":
    convert()
