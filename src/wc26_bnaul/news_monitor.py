#!/usr/bin/env python3
"""
ClawCup News Monitor — Tự động theo dõi tin tức và resubmit khi có thông tin mới

Chiến thuật: Resubmit Information Advantage
- Gửi dự đoán sớm với xác suất conservative
- Monitor news (chấn thương, đội hình, thời tiết) 30 phút trước match
- Resubmit nếu có thông tin material thay đổi assessment
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

# Import từ wc26_bnaul
from wc26_bnaul import api_request, get_credentials


def get_open_fixtures() -> List[Dict]:
    """Lấy danh sách trận đấu đang mở."""
    data = api_request("GET", "/fixtures?status=open")
    return data.get("matches", [])


def get_my_predictions() -> List[Dict]:
    """Lấy danh sách dự đoán đã gửi."""
    data = api_request("GET", "/predictions/mine")
    return data.get("submissions", [])


def calculate_time_to_cutoff(kickoff_utc: str) -> float:
    """Tính số phút còn lại đến cutoff (30 phút trước kickoff)."""
    kickoff = datetime.fromisoformat(kickoff_utc.replace('Z', '+00:00'))
    cutoff = kickoff - timedelta(minutes=30)
    now = datetime.now(timezone.utc)
    
    seconds_remaining = (cutoff - now).total_seconds()
    return seconds_remaining / 60  # Convert to minutes


def check_news_for_match(match_id: str, home: str, away: str) -> Optional[Dict]:
    """
    Kiểm tra tin tức cho một trận đấu.
    
    Trong thực tế, đây sẽ:
    1. Gọi news API (NewsAPI, RSS feeds, Twitter/X API)
    2. Parse thông tin chấn thương, đội hình
    3. Trả về dict với thông tin mới
    
    Hiện tại: placeholder — cần implement với real news sources.
    """
    # TODO: Implement real news monitoring
    # Ví dụ:
    # - NewsAPI: https://newsapi.org/
    # - RSS feeds từ BBC Sport, ESPN, Goal.com
    # - Twitter/X API cho real-time updates
    # - SofaScore API cho chấn thương/đội hình
    # - API-Football injuries endpoint
    
    return None


def analyze_player_impact(match_id: str, home: str, away: str) -> Dict:
    """
    Phân tích tác động của cầu thủ và phát biểu trước trận.
    
    Trả về dict với:
    - key_players: danh sách cầu thủ chủ chốt và tình trạng
    - injuries: chấn thương ảnh hưởng đến xác suất
    - statements: phát biểu HLV/cầu thủ có thể tác động
    - probability_adjustment: điều chỉnh xác suất dựa trên phân tích
    """
    # Đọc từ research files nếu có
    research_dir = os.path.join(os.path.dirname(__file__), "..", "..", "research")
    
    # Tìm file phân tích phù hợp
    match_key = f"{home.upper().replace(' ', '_')}_{away.upper().replace(' ', '_')}"
    analysis_file = os.path.join(research_dir, f"{match_key}_ANALYSIS.md")
    
    result = {
        "match_id": match_id,
        "home": home,
        "away": away,
        "has_research": False,
        "key_players": {},
        "injuries": [],
        "statements": [],
        "probability_adjustment": 0.0,
        "notes": []
    }
    
    if os.path.exists(analysis_file):
        result["has_research"] = True
        result["notes"].append(f"Found research file: {analysis_file}")
        
        # Parse research file để extract thông tin cầu thủ
        try:
            with open(analysis_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract injury information
            if "chấn thương" in content.lower() or "injured" in content.lower() or "vắng" in content.lower():
                result["notes"].append("Injury information found in research")
                
            # Extract key player mentions
            key_players_home = []
            key_players_away = []
            
            # Simple extraction based on common patterns
            if home == "Brazil":
                key_players_home = ["Vinícius Júnior", "Matheus Cunha", "Neymar", "Casemiro"]
            elif home == "Argentina":
                key_players_home = ["Messi", "Lautaro Martinez", "Enzo Fernandez", "Emiliano Martinez"]
            elif home == "France":
                key_players_home = ["Mbappé", "Griezmann", "Tchouaméni", "Maignan"]
            
            if away == "Japan":
                key_players_away = ["Kubo", "Ueda", "Kamada", "Mitoma"]
            elif away == "Italy":
                key_players_away = ["Barella", "Chiesa", "Donnarumma", "Bastoni"]
            elif away == "Sweden":
                key_players_away = ["Isak", "Kulusevski", "Lindelöf"]
            
            result["key_players"] = {
                "home": key_players_home,
                "away": key_players_away
            }
            
        except Exception as e:
            result["notes"].append(f"Error parsing research: {e}")
    else:
        result["notes"].append(f"No research file found: {analysis_file}")
    
    return result


def should_resubmit(current_pred: Dict, news: Dict, player_analysis: Dict = None) -> bool:
    """
    Quyết định có nên resubmit không dựa trên thông tin mới.
    
    Logic:
    - Chấn thương key player → điều chỉnh xác suất
    - Thay đổi đội hình đáng kể → điều chỉnh
    - Thời tiết xấu → có thể ảnh hưởng
    - Phân tích cầu thủ từ research files → điều chỉnh
    """
    if not news and not player_analysis:
        return False
    
    # Kiểm tra mức độ nghiêm trọng của tin tức
    severity = news.get("severity", "low") if news else "low"
    
    # Kiểm tra phân tích cầu thủ
    if player_analysis:
        has_research = player_analysis.get("has_research", False)
        injuries = player_analysis.get("injuries", [])
        
        if injuries:
            severity = "high"
            print(f"  → Player analysis: {len(injuries)} injuries found")
        elif has_research:
            print(f"  → Player analysis: Research file available")
    
    if severity == "high":
        # Key player injured, formation change, etc.
        return True
    elif severity == "medium":
        # Minor injury, weather change
        # Resubmit nếu thời gian còn nhiều (> 60 phút)
        return True
    
    return False


def adjust_probability(current_prob: float, news: Dict, player_analysis: Dict = None) -> float:
    """Điều chỉnh xác suất dựa trên tin tức và phân tích cầu thủ."""
    adjustment = news.get("probability_adjustment", 0.0) if news else 0.0
    
    # Thêm điều chỉnh từ phân tích cầu thủ
    if player_analysis:
        player_adj = player_analysis.get("probability_adjustment", 0.0)
        adjustment += player_adj
    
    new_prob = current_prob + adjustment
    return max(0.01, min(0.99, new_prob))


def monitor_and_resubmit(dry_run: bool = True, check_interval: int = 300, use_fifa_data: bool = False):
    """
    Main loop: monitor open matches và resubmit khi cần.
    
    Args:
        dry_run: Nếu True, chỉ log không thực sự resubmit
        check_interval: Số giây giữa các lần check (default: 5 phút)
        use_fifa_data: Nếu True, tích hợp dữ liệu FIFA để cải thiện dự đoán
    """
    print("=" * 70)
    print("CLAWCUP NEWS MONITOR")
    print("=" * 70)
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"Check interval: {check_interval} seconds")
    print(f"FIFA data: {'ENABLED' if use_fifa_data else 'DISABLED'}")
    print()
    
    # Import FIFA data modules nếu cần
    fifa_data = None
    predictor = None
    if use_fifa_data:
        try:
            from .fifa_data import get_team_statistics_api_football, get_injuries_api_football
            from .predictor import MatchPredictor
            predictor = MatchPredictor()
            fifa_data = {
                "get_team_stats": get_team_statistics_api_football,
                "get_injuries": get_injuries_api_football,
            }
            print("✅ FIFA data modules loaded")
        except ImportError as e:
            print(f"⚠️  Could not load FIFA data modules: {e}")
            use_fifa_data = False
    
    while True:
        try:
            # 1. Lấy danh sách trận đấu mở
            fixtures = get_open_fixtures()
            
            if not fixtures:
                print(f"[{datetime.now(timezone.utc).isoformat()}] No open fixtures. Sleeping...")
                time.sleep(check_interval)
                continue
            
            # 2. Lấy dự đoán hiện tại
            my_preds = get_my_predictions()
            pred_map = {p["match_id"]: p for p in my_preds}
            
            # 3. Kiểm tra từng trận
            for match in fixtures:
                match_id = match["match_id"]
                home = match["home"]
                away = match["away"]
                kickoff = match.get("kickoff_utc", "")
                
                # Tính thời gian còn lại
                minutes_to_cutoff = calculate_time_to_cutoff(kickoff)
                
                print(f"\n[{datetime.now(timezone.utc).isoformat()}]")
                print(f"Match: {match_id} — {home} vs {away}")
                print(f"Kickoff: {kickoff}")
                print(f"Minutes to cutoff: {minutes_to_cutoff:.1f}")
                
                # Chỉ monitor trận sắp đến hạn (trong vòng 2 giờ)
                if minutes_to_cutoff > 120:
                    print(f"  → Too early, skipping (>{120} min)")
                    continue
                
                if minutes_to_cutoff < 0:
                    print(f"  → Already locked, skipping")
                    continue
                
                # 4. Check news
                news = check_news_for_match(match_id, home, away)
                
                # 5. Phân tích cầu thủ
                player_analysis = analyze_player_impact(match_id, home, away)
                
                # 6. Tích hợp dữ liệu FIFA (nếu enabled)
                fifa_analysis = None
                if use_fifa_data and fifa_data and predictor:
                    try:
                        print(f"  → Fetching FIFA data...")
                        # TODO: Map team names to API IDs
                        # This requires a mapping from ClawCup team names to API-Football team IDs
                        # For now, skip actual API calls
                        fifa_analysis = {
                            "has_data": False,
                            "notes": ["FIFA data integration requires team ID mapping"]
                        }
                    except Exception as e:
                        print(f"  → FIFA data error: {e}")
                
                if player_analysis.get("has_research"):
                    print(f"  → Player analysis: Research file found")
                    key_players = player_analysis.get("key_players", {})
                    if key_players:
                        home_players = key_players.get("home", [])
                        away_players = key_players.get("away", [])
                        print(f"  → Key players: {home} ({', '.join(home_players[:3])}) vs {away} ({', '.join(away_players[:3])})")
                
                if news:
                    print(f"  → News found: {news.get('headline', 'N/A')}")
                    print(f"  → Severity: {news.get('severity', 'low')}")
                
                if fifa_analysis and fifa_analysis.get("has_data"):
                    print(f"  → FIFA data: Available")
                
                # 7. Kiểm tra xem đã có dự đoán chưa
                if match_id in pred_map:
                    current_pred = pred_map[match_id]
                    print(f"  → Current prediction: {current_pred}")
                    
                    # 8. Quyết định resubmit
                    if should_resubmit(current_pred, news, player_analysis):
                        new_prob = adjust_probability(
                            current_pred.get("p", [0.5, 0.5])[0],
                            news,
                            player_analysis
                        )
                        
                        print(f"  → RESUBMIT RECOMMENDED")
                        print(f"  → New probability: {new_prob:.2f}")
                        
                        if not dry_run:
                            # Thực hiện resubmit
                            # TODO: Implement actual resubmit
                            print(f"  → [LIVE] Resubmitting...")
                        else:
                            print(f"  → [DRY RUN] Would resubmit with p=[{new_prob:.2f}, {1-new_prob:.2f}]")
                    else:
                        print(f"  → No resubmit needed")
                else:
                    print(f"  → No existing prediction for this match")
                    
                    # Nếu chưa có dự đoán và FIFA data available, tạo dự đoán mới
                    if use_fifa_data and fifa_analysis and fifa_analysis.get("has_data"):
                        print(f"  → Would generate prediction from FIFA data")
            
            # Sleep until next check
            print(f"\n{'='*70}")
            print(f"Sleeping for {check_interval} seconds...")
            print(f"{'='*70}")
            time.sleep(check_interval)
            
        except KeyboardInterrupt:
            print("\n\nShutting down...")
            break
        except Exception as e:
            print(f"\nError: {e}")
            time.sleep(check_interval)


def manual_check(match_id: str, dry_run: bool = True):
    """Kiểm tra thủ công một trận đấu."""
    print(f"Checking match {match_id}...")
    
    # Lấy thông tin trận đấu
    fixtures = get_open_fixtures()
    match = None
    for f in fixtures:
        if f["match_id"] == match_id:
            match = f
            break
    
    if not match:
        print(f"Match {match_id} not found or not open")
        return
    
    print(f"Match: {match['home']} vs {match['away']}")
    print(f"Kickoff: {match.get('kickoff_utc', 'N/A')}")
    
    # Check news
    news = check_news_for_match(match_id, match["home"], match["away"])
    
    # Phân tích cầu thủ
    player_analysis = analyze_player_impact(match_id, match["home"], match["away"])
    
    print(f"\nPlayer Analysis:")
    print(json.dumps(player_analysis, indent=2, ensure_ascii=False))
    
    if news:
        print(f"\nNews found:")
        print(json.dumps(news, indent=2))
    else:
        print("\nNo news found")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ClawCup News Monitor")
    parser.add_argument("--dry-run", action="store_true", help="Run without actual resubmit")
    parser.add_argument("--interval", type=int, default=300, help="Check interval in seconds")
    parser.add_argument("--check", help="Manual check a specific match ID")
    parser.add_argument("--fifa-data", action="store_true", help="Enable FIFA data integration")
    
    args = parser.parse_args()
    
    if args.check:
        manual_check(args.check, dry_run=args.dry_run)
    else:
        monitor_and_resubmit(dry_run=args.dry_run, check_interval=args.interval, use_fifa_data=args.fifa_data)
