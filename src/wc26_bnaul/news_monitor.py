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
    
    return None


def should_resubmit(current_pred: Dict, news: Dict) -> bool:
    """
    Quyết định có nên resubmit không dựa trên thông tin mới.
    
    Logic:
    - Chấn thương key player → điều chỉnh xác suất
    - Thay đổi đội hình đáng kể → điều chỉnh
    - Thời tiết xấu → có thể ảnh hưởng
    """
    if not news:
        return False
    
    # Kiểm tra mức độ nghiêm trọng của tin tức
    severity = news.get("severity", "low")
    
    if severity == "high":
        # Key player injured, formation change, etc.
        return True
    elif severity == "medium":
        # Minor injury, weather change
        # Resubmit nếu thời gian còn nhiều (> 60 phút)
        return True
    
    return False


def adjust_probability(current_prob: float, news: Dict) -> float:
    """Điều chỉnh xác suất dựa trên tin tức."""
    adjustment = news.get("probability_adjustment", 0.0)
    new_prob = current_prob + adjustment
    return max(0.01, min(0.99, new_prob))


def monitor_and_resubmit(dry_run: bool = True, check_interval: int = 300):
    """
    Main loop: monitor open matches và resubmit khi cần.
    
    Args:
        dry_run: Nếu True, chỉ log không thực sự resubmit
        check_interval: Số giây giữa các lần check (default: 5 phút)
    """
    print("=" * 70)
    print("CLAWCUP NEWS MONITOR")
    print("=" * 70)
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"Check interval: {check_interval} seconds")
    print()
    
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
                
                if news:
                    print(f"  → News found: {news.get('headline', 'N/A')}")
                    print(f"  → Severity: {news.get('severity', 'low')}")
                    
                    # 5. Kiểm tra xem đã có dự đoán chưa
                    if match_id in pred_map:
                        current_pred = pred_map[match_id]
                        print(f"  → Current prediction: {current_pred}")
                        
                        # 6. Quyết định resubmit
                        if should_resubmit(current_pred, news):
                            new_prob = adjust_probability(
                                current_pred.get("p", [0.5, 0.5])[0],
                                news
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
                else:
                    print(f"  → No news")
            
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
    
    args = parser.parse_args()
    
    if args.check:
        manual_check(args.check, dry_run=args.dry_run)
    else:
        monitor_and_resubmit(dry_run=args.dry_run, check_interval=args.interval)
