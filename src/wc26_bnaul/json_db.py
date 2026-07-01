import json
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")

def load_json_db(filename: str) -> dict:
    """Đọc dữ liệu từ file JSON."""
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json_db(filename: str, data: dict):
    """Ghi dữ liệu vào file JSON."""
    os.makedirs(DATA_DIR, exist_ok=True)
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def update_team_injury(team_name: str, player_name: str, is_injured: bool):
    """Cập nhật trạng thái chấn thương của cầu thủ."""
    teams = load_json_db("teams_db.json")
    if team_name in teams:
        for player in teams[team_name].get("key_players", []):
            if player["name"] == player_name:
                player["is_injured"] = is_injured
                print(f"🏥 Đã cập nhật chấn thương cho {player_name} ({team_name}): {is_injured}")
                break
        save_json_db("teams_db.json", teams)

def gather_match_context(match_id: str, home: str, away: str, ref_name: str = "Szymon Marciniak") -> dict:
    """Gom dữ liệu từ các JSON files để tạo context cho Kimi hoặc Auto Agent."""
    teams = load_json_db("teams_db.json")
    referees = load_json_db("referees_db.json")
    betting = load_json_db("betting_db.json")
    matches = load_json_db("matches_db.json")
    
    context = {
        "match_id": match_id,
        "home": teams.get(home, {}),
        "away": teams.get(away, {}),
        "referee": referees.get(ref_name, {}),
        "betting": betting.get(match_id, {}),
        "h2h": matches.get(f"{home}_vs_{away}", {"total_matches": 0, "home_wins": 0, "draws": 0, "away_wins": 0})
    }
    
    return context
