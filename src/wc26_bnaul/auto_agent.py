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
    uv run python -m wc26_bnaul.auto_agent --cli-mode     # CLI mode: print prompt, read stdin
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
from wc26_bnaul.batch_predict import get_team_data, get_venue_data
from wc26_bnaul.json_db import load_json_db
from wc26_bnaul.prediction_logger import PredictionLogger
from wc26_bnaul.news_monitor_real import (
    search_news_for_teams,
    analyze_news_content,
    fetch_injuries_for_match,
    analyze_injury_impact,
)
from wc26_bnaul.json_db import gather_match_context


logger = PredictionLogger()


# =============================================================================
# AI PROBABILITY ADJUSTMENT (LLM-powered data enrichment)
# =============================================================================

def call_llm_api(prompt: str, dry_run: bool = False, cli_mode: bool = False) -> float:
    """
    Gọi LLM API để lấy điều chỉnh xác suất dựa trên context.

    Hỗ trợ 3 chế độ:
    - dry_run=True: In preview prompt, trả về 0.0 (không gọi API).
    - cli_mode=True: In toàn bộ prompt ra stdout, đọc ADJUSTMENT từ stdin
      (dùng khi chạy với kimi-cli hoặc agent CLI bên ngoài).
    - Mặc định (dry_run=False, cli_mode=False): Gọi API thật (nếu đã cài
      openai/kimi client), nếu chưa có thì fallback về 0.0.
    """
    if cli_mode:
        # In toàn bộ prompt ra stdout để CLI agent (kimi-cli, v.v.) đọc
        print(f"\n{'='*60}")
        print("LLM PROMPT (cli_mode — output for external CLI agent):")
        print(f"{'='*60}")
        print(prompt)
        print(f"{'='*60}")
        print("\n[CLI MODE] Waiting for ADJUSTMENT from stdin...")
        print("Format: ADJUSTMENT: [value]  (e.g., ADJUSTMENT: -2.5)")
        print("Enter adjustment and press Ctrl+D (Unix) or Ctrl+Z (Windows) when done:")
        print("-" * 60)

        # Đọc toàn bộ stdin
        try:
            raw_input = sys.stdin.read()
        except KeyboardInterrupt:
            print("\n[CLI MODE] Interrupted. Returning 0.0")
            return 0.0

        # Parse ADJUSTMENT từ input
        adjustment = _parse_adjustment_from_text(raw_input)
        print(f"[CLI MODE] Parsed adjustment: {adjustment:+.1f}%")
        return adjustment

    if dry_run:
        print(f"\n{'='*60}")
        print("LLM PROMPT (dry_run — would send to API):")
        print(f"{'='*60}")
        # In 500 chars đầu để không quá dài
        preview = prompt[:500] + "..." if len(prompt) > 500 else prompt
        print(preview)
        print(f"\n[DRY RUN] Would call LLM API. Returning default adjustment: 0.0")
        return 0.0

    # --- Real API call mode (production or interactive) ---
    # Thử gọi API nếu đã cài thư viện openai
    try:
        import os
        # Nếu có cờ --ask-agent (hoặc --ask-kimi cũ), dùng cơ chế Copy-Paste thủ công (Human-in-the-loop)
        import sys
        if "--ask-agent" in sys.argv or "--ask-kimi" in sys.argv:
            print(f"\n{'='*60}")
            print(f"🤖 LLM PROMPT (Hãy copy nội dung dưới đây dán vào ChatGPT/Kimi/Claude):")
            print(f"{'='*60}")
            print(prompt)
            print(f"{'='*60}")
            
            while True:
                print("\n📝 Dán câu trả lời của AI vào đây (Nhấn Ctrl+D / Ctrl+Z ở dòng mới khi dán xong):")
                try:
                    raw_input = sys.stdin.read()
                    # Reset stdin để có thể dùng input() ở bước sau
                    sys.stdin = open('/dev/tty')
                except KeyboardInterrupt:
                    print("\n[ASK AGENT] Interrupted. Returning 0.0")
                    return 0.0
                except Exception:
                    pass
                
                adjustment = _parse_adjustment_from_text(raw_input)
                
                print(f"\n{'='*60}")
                print(f"🎯 HỆ THỐNG ĐỌC ĐƯỢC:")
                print(f"  AI tư vấn điều chỉnh: {adjustment:+.1f}%")
                print(f"{'='*60}")
                
                while True:
                    try:
                        val = input(f"👉 Bạn có chốt con số {adjustment:+.1f}% này không? [Nhập số khác để Override / Nhấn Enter để Đồng ý]: ").strip()
                        if not val:
                            print(f"✅ Đã chốt: {adjustment:+.1f}%")
                            return adjustment
                        override_adj = float(val.replace("%", ""))
                        print(f"✅ Đã ghi đè thành: {override_adj:+.1f}%")
                        return override_adj
                    except ValueError:
                        print("❌ Lỗi: Vui lòng nhập một số hợp lệ (ví dụ: -2.5 hoặc 1.0)")
                        
        # Nếu có API Key, dùng chế độ API tự động (Production / --interactive)
        api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("KIMI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "[LLM API] CRITICAL ERROR: No API key found and --ask-agent not used.\n"
                "To use manual copy-paste mode, run with --ask-agent flag.\n"
                "To use auto mode, set OPENAI_API_KEY or KIMI_API_KEY in .env"
            )
        
        # Gọi API thật (giả lập import openai)
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url="https://api.moonshot.cn/v1" if "KIMI" in os.environ else None)
        
        print("\n⏳ Đang lấy tư vấn từ AI Agent...")
        response = client.chat.completions.create(
            model="moonshot-v1-8k" if "KIMI" in os.environ else "gpt-4o",
            messages=[
                {"role": "system", "content": "You are a football prediction assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        llm_response = response.choices[0].message.content
        adjustment = _parse_adjustment_from_text(llm_response)
        
        # Nếu có cờ --interactive (được truyền ngầm qua sys.argv hoặc biến môi trường)
        if "--interactive" in sys.argv:
            print(f"\n{'='*60}")
            print(f"🤖 AI TƯ VẤN:")
            print(f"{'='*60}")
            print(llm_response)
            print(f"{'='*60}")
            
            while True:
                try:
                    val = input(f"\n👉 Bạn có đồng ý với điều chỉnh {adjustment:+.1f}% không? [Nhập số khác để Override / Nhấn Enter để Đồng ý]: ").strip()
                    if not val:
                        return adjustment
                    # Nếu user tự nhập số
                    override_adj = float(val.replace("%", ""))
                    print(f"✅ Đã ghi đè thành: {override_adj:+.1f}%")
                    return override_adj
                except ValueError:
                    print("❌ Lỗi: Vui lòng nhập một số hợp lệ (ví dụ: -2.5 hoặc 1.0)")
                except KeyboardInterrupt:
                    print("\n[INTERACTIVE] Interrupted. Returning 0.0")
                    return 0.0
                    
        return adjustment

    except ImportError:
        print("\n[LLM API] openai library not found. Please run: pip install openai")
        raise
    except Exception as e:
        print(f"\n[LLM API] Error calling API: {e}")
        raise




def _parse_adjustment_from_text(text: str) -> float:
    """
    Parse giá trị ADJUSTMENT từ text.
    Tìm pattern 'ADJUSTMENT: [value]' hoặc '[+-]number'.
    """
    import re
    # Tìm pattern ADJUSTMENT: [value]
    match = re.search(r"ADJUSTMENT:\s*([+-]?\d+\.?\d*)", text, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass

    # Fallback: tìm bất kỳ số nào có dấu + hoặc - trong text
    match = re.search(r"([+-]?\d+\.?\d*)", text)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass

    # Nếu không parse được, trả về 0.0
    print(f"[LLM API] Could not parse adjustment from: {text[:100]}... Returning 0.0")
    return 0.0


def get_ai_probability_adjustment(
    match_id: str,
    home: str,
    away: str,
    base_prob: float,
    ref_name: str = "Szymon Marciniak",
    dry_run: bool = False,
    cli_mode: bool = False,
) -> float:
    """
    Tích hợp LLM để điều chỉnh xác suất dựa trên dữ liệu JSON context.
    
    Args:
        match_id: ID trận đấu (e.g., "m080")
        home: Tên đội nhà
        away: Tên đội khách
        base_prob: Xác suất gốc từ ensemble model (0.0 - 1.0)
        ref_name: Tên trọng tài (default: Szymon Marciniak)
        dry_run: Nếu True, chỉ in prompt ra màn hình, không gọi API thật
        cli_mode: Nếu True, in prompt ra stdout và đọc ADJUSTMENT từ stdin
                 (dùng khi chạy với kimi-cli hoặc agent CLI bên ngoài)
    
    Returns:
        Xác suất cuối cùng sau khi áp dụng điều chỉnh từ LLM (đã clamp 0.01-0.99)
    """
    print(f"\n{'='*60}")
    print(f"AI PROBABILITY ADJUSTMENT: {match_id} — {home} vs {away}")
    print(f"{'='*60}")
    
    # Step 1: Gather match context from JSON databases
    print(f"[Step 1] Gathering match context from JSON databases...")
    context = gather_match_context(match_id, home, away, ref_name)
    
    # Step 2: Build LLM prompt with full context
    print(f"[Step 2] Building LLM prompt...")
    
    prompt = f"""You are a football match prediction expert with access to real-time web search.

TASK: Analyze the following match data and provide a PROBABILITY ADJUSTMENT for the home team's win probability.

MATCH: {home} vs {away} (Match ID: {match_id})
BASE HOME PROBABILITY: {base_prob:.1%}

--- FULL MATCH CONTEXT (JSON) ---
{json.dumps(context, indent=2, ensure_ascii=False)}
--- END CONTEXT ---

INSTRUCTIONS:
1. Use your web search capability to find the LATEST news about:
   - Injuries or suspensions for either team (especially key players)
   - Recent form changes (last 24-48 hours)
   - Betting odds movements (significant shifts)
   - Weather conditions at the venue
   - Any tactical or lineup announcements

2. Compare the JSON context above with real-time data. Identify any discrepancies.

3. Provide a SINGLE NUMERIC ADJUSTMENT in percentage points:
   - Use POSITIVE values to INCREASE home probability (e.g., +2.5, +1.0)
   - Use NEGATIVE values to DECREASE home probability (e.g., -3.0, -1.5)
   - Use 0.0 if no adjustment is needed
   - Range: typically -5.0 to +5.0

4. Your response MUST contain the adjustment in this exact format:
   ADJUSTMENT: [value]
   
   Example: "ADJUSTMENT: -2.5" or "ADJUSTMENT: +1.0" or "ADJUSTMENT: 0.0"

5. Briefly explain your reasoning in 1-2 sentences after the adjustment.

IMPORTANT: Be conservative. Small adjustments are better than large ones. When in doubt, use 0.0.
"""
    
    # Step 3: Call LLM API (or dry_run, or cli_mode)
    print(f"[Step 3] Calling LLM API...")
    adjustment = call_llm_api(prompt, dry_run=dry_run, cli_mode=cli_mode)
    
    # Step 4: Apply adjustment to base_prob
    print(f"[Step 4] Applying adjustment...")
    
    # Convert adjustment from percentage points to decimal
    adjustment_decimal = adjustment / 100.0
    adjusted_prob = base_prob + adjustment_decimal
    
    # Clamp to valid range [0.01, 0.99]
    final_prob = max(0.01, min(0.99, adjusted_prob))
    
    # Step 5: Log the adjustment
    print(f"\n{'='*60}")
    print(f"ADJUSTMENT RESULT")
    print(f"{'='*60}")
    print(f"  Base probability:     {base_prob:.2%}")
    print(f"  AI adjustment:        {adjustment:+.1f}%")
    print(f"  Adjusted probability: {adjusted_prob:.2%}")
    if final_prob != adjusted_prob:
        print(f"  Clamped to:           {final_prob:.2%} (out of valid range)")
    print(f"{'='*60}")
    
    return final_prob


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
        
        # Run ensemble model with ALL parameters (ELO, squad_depth, venue, INJURIES)
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
            home_injuries=home_data.get("injuries", 0),
            away_injuries=away_data.get("injuries", 0),
            knockout=True,
            home_rest_days=env["home_rest_days"],
            away_rest_days=env["away_rest_days"],
            altitude_m=env["altitude_m"],
            temperature_c=env["temperature_c"],
        )
        
        binary = result.to_binary()
        home_prob = binary[0]
        away_prob = binary[1]
        
        # SELECTIVE SUBMISSION: Only predict when there's a CLEAR edge
        # Learned from simulation: selective prediction (ELO gap > 150) 
        # achieves SKILL = 8.2% vs always-predict = 6.5% vs 50/50 = 0.0%
        # 
        # Decision tree:
        #   ELO gap > 250 → Predict with 5% shrink (strong edge)
        #   ELO gap 150-250 → Predict with 15% shrink (moderate edge)
        #   ELO gap 100-150 → 50/50 (weak edge, not worth the risk)
        #   ELO gap < 100 → 50/50 (no edge, coin flip)
        #
        # This is how jason achieves 55% SKILL — not better prediction,
        # but only predicting when confidence is very high.
        
        home_elo = home_data.get("elo", 0)
        away_elo = away_data.get("elo", 0)
        elo_gap = abs(home_elo - away_elo) if home_elo > 0 and away_elo > 0 else 0
        
        SELECTIVE_STRONG_GAP = 250
        SELECTIVE_MODERATE_GAP = 150
        SELECTIVE_WEAK_GAP = 100
        
        # Determine if we should predict or submit 50/50
        if elo_gap >= SELECTIVE_STRONG_GAP:
            # Strong edge: predict with minimal shrink
            selectivity_note = f"Strong edge (ELO gap {elo_gap}) → Predict"
            should_predict = True
        elif elo_gap >= SELECTIVE_MODERATE_GAP:
            # Moderate edge: predict with caution
            selectivity_note = f"Moderate edge (ELO gap {elo_gap}) → Predict with caution"
            should_predict = True
        elif elo_gap >= SELECTIVE_WEAK_GAP:
            # Weak edge: 50/50 (not worth the risk)
            home_prob = 0.50
            away_prob = 0.50
            selectivity_note = f"Weak edge (ELO gap {elo_gap}) → 50/50 (selective strategy)"
            should_predict = False
        else:
            # No edge: 50/50
            home_prob = 0.50
            away_prob = 0.50
            selectivity_note = f"No edge (ELO gap {elo_gap}) → 50/50 (selective strategy)"
            should_predict = False
        
        # If we decided to predict, apply additional safety checks
        if should_predict:
            # Principle 3: SELECTIVITY — if no clear edge after model, submit 50/50
            # Principle 5: For knockout, extend threshold to 55%
            effective_selectivity_low = SELECTIVITY_THRESHOLD_LOW
            effective_selectivity_high = SELECTIVITY_THRESHOLD_HIGH
            if True:  # All matches in auto-agent are knockout
                effective_selectivity_low = 0.45
                effective_selectivity_high = 0.55
            
            if effective_selectivity_low < home_prob < effective_selectivity_high:
                home_prob = 0.50
                away_prob = 0.50
                selectivity_note += f" → Model uncertain ({home_prob:.0%}) → 50/50"
                should_predict = False
            
            # Principle 2: KNOCKOUT CAP 65%
            if True:  # All matches in auto-agent are knockout
                if home_prob > KNOCKOUT_CONFIDENCE_CAP:
                    home_prob = KNOCKOUT_CONFIDENCE_CAP
                    away_prob = 1.0 - home_prob
                    selectivity_note += f" (capped at {KNOCKOUT_CONFIDENCE_CAP:.0%})"
                elif home_prob < KNOCKOUT_CONFIDENCE_FLOOR:
                    home_prob = KNOCKOUT_CONFIDENCE_FLOOR
                    away_prob = 1.0 - home_prob
                    selectivity_note += f" (floored at {KNOCKOUT_CONFIDENCE_FLOOR:.0%})"
            
            # Apply uncertainty bounds from meta-analysis
            lower_bound, upper_bound = self.uncertainty_bounds
            if home_prob < lower_bound:
                home_prob = lower_bound
                away_prob = 1.0 - home_prob
                selectivity_note += f" (clamped to {lower_bound:.0%})"
            elif home_prob > upper_bound:
                home_prob = upper_bound
                away_prob = 1.0 - home_prob
                selectivity_note += f" (clamped to {upper_bound:.0%})"
        
        # Principle 1: TRUTHFUL SUBMISSION — log the true belief before adjustment
        true_belief = binary[0]
        adjustment = home_prob - true_belief
        if abs(adjustment) > 0.01:
            print(f"  → Adjustment: {adjustment:+.1%} (true belief {true_belief:.0%} → submitted {home_prob:.0%})")
        
        # Final decision: should we submit?
        # Selective strategy: only submit if we have clear edge (ELO gap > 150)
        # or if uncertainty bounds allow meaningful prediction
        if not should_predict:
            self.should_submit = True  # Still submit 50/50 (optimal for no-edge matches)
            submit_reason = "Selective 50/50 — no clear edge"
        elif self.uncertainty_bounds == (0.45, 0.55):
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

def auto_predict_match(match_id: str, home: str, away: str, dry_run: bool = True, check_news: bool = True, cli_mode: bool = False) -> bool:
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
    
    # AI Probability Adjustment (LLM-powered data enrichment)
    # Only apply for real teams (not placeholders)
    # In CLI mode, skip the reasoning loop and go straight to LLM prompt
    if cli_mode and not home.startswith("W") and not away.startswith("W") and not home.startswith("L") and not away.startswith("L"):
        # Build context directly for CLI mode (skip reasoning loop)
        from wc26_bnaul.json_db import gather_match_context
        print(f"\n{'='*60}")
        print(f"AI PROBABILITY ADJUSTMENT: {match_id} — {home} vs {away}")
        print(f"{'='*60}")
        print(f"[Step 1] Gathering match context from JSON databases...")
        context = gather_match_context(match_id, home, away)
        print(f"[Step 2] Building LLM prompt...")
        
        prompt = f"""You are a football match prediction expert with access to real-time web search.

TASK: Analyze the following match data and provide a PROBABILITY ADJUSTMENT for the home team's win probability.

MATCH: {home} vs {away} (Match ID: {match_id})
BASE HOME PROBABILITY: {home_prob:.1%}

--- FULL MATCH CONTEXT (JSON) ---
{json.dumps(context, indent=2, ensure_ascii=False)}
--- END CONTEXT ---

INSTRUCTIONS:
1. Use your web search capability to find the LATEST news about:
   - Injuries or suspensions for either team (especially key players)
   - Recent form changes (last 24-48 hours)
   - Betting odds movements (significant shifts)
   - Weather conditions at the venue
   - Any tactical or lineup announcements

2. Compare the JSON context above with real-time data. Identify any discrepancies.

3. Provide a SINGLE NUMERIC ADJUSTMENT in percentage points:
   - Use POSITIVE values to INCREASE home probability (e.g., +2.5, +1.0)
   - Use NEGATIVE values to DECREASE home probability (e.g., -3.0, -1.5)
   - Use 0.0 if no adjustment is needed
   - Range: typically -5.0 to +5.0

4. Your response MUST contain the adjustment in this exact format:
   ADJUSTMENT: [value]
   
   Example: "ADJUSTMENT: -2.5" or "ADJUSTMENT: +1.0" or "ADJUSTMENT: 0.0"

5. Briefly explain your reasoning in 1-2 sentences after the adjustment.

IMPORTANT: Be conservative. Small adjustments are better than large ones. When in doubt, use 0.0.
"""
        
        print(f"[Step 3] Calling LLM API...")
        adjustment = call_llm_api(prompt, dry_run=dry_run, cli_mode=cli_mode)
        
        print(f"[Step 4] Applying adjustment...")
        adjustment_decimal = adjustment / 100.0
        adjusted_prob = home_prob + adjustment_decimal
        final_prob = max(0.01, min(0.99, adjusted_prob))
        
        print(f"\n{'='*60}")
        print(f"ADJUSTMENT RESULT")
        print(f"{'='*60}")
        print(f"  Base probability:     {home_prob:.2%}")
        print(f"  AI adjustment:        {adjustment:+.1f}%")
        print(f"  Adjusted probability: {adjusted_prob:.2%}")
        if final_prob != adjusted_prob:
            print(f"  Clamped to:           {final_prob:.2%} (out of valid range)")
        print(f"{'='*60}")
        
        home_prob = final_prob
        away_prob = 1.0 - home_prob
        
        # Skip the rest of the function (reasoning loop, etc.)
        # BUT still submit if not dry_run
        if dry_run:
            print(f"\n{'='*60}")
            print(f"FINAL: {home} {home_prob:.2%} vs {away} {away_prob:.2%}")
            print(f"{'='*60}")
            print(f"🚫 DRY RUN — Would submit:")
            print(f"  {match_id}: {home} {home_prob:.2f} vs {away} {away_prob:.2f}")
            print(f"{'='*60}")
            return True
        
        # LIVE mode: submit the prediction
        print(f"\n{'='*60}")
        print(f"FINAL: {home} {home_prob:.2%} vs {away} {away_prob:.2%}")
        print(f"{'='*60}")
        print(f"🚀 SUBMITTING...")
        max_retries = 3
        for attempt in range(max_retries):
            try:
                api_request("POST", "/predictions", {
                    "match_id": match_id,
                    "format": "binary",
                    "p": [round(home_prob, 2), round(away_prob, 2)],
                    "reasoning": f"CLI mode adjustment: {adjustment:+.1f}% | Base: {home_prob:.2%}",
                })
                
                # Log prediction
                logger.log_prediction(
                    match_id=match_id,
                    home_team=home,
                    away_team=away,
                    submitted_probs=[round(home_prob, 2), round(away_prob, 2)],
                    components={"cli_adjustment": adjustment, "base_prob": home_prob},
                    predicted_score="1-0",
                    reasoning=f"CLI mode adjustment: {adjustment:+.1f}%",
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
        return True
    
    if not home.startswith("W") and not away.startswith("W") and not home.startswith("L") and not away.startswith("L"):
        home_prob = get_ai_probability_adjustment(
            match_id=match_id,
            home=home,
            away=away,
            base_prob=home_prob,
            dry_run=dry_run,
            cli_mode=cli_mode,
        )
        away_prob = 1.0 - home_prob
    
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
    print(f"FINAL: {home} {home_prob:.2%} vs {away} {away_prob:.2%}")
    print(f"Score: {score}")
    print(f"Confidence: {confidence:.2%}")
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


def run_auto_agent(dry_run: bool = True, match_id: str = None, check_news: bool = True, cli_mode: bool = False):
    """Run auto-agent for all open matches or a specific match."""
    print(f"\n{'='*70}")
    print(f"AUTO AGENT — wc26-bnaul (Multi-Step Reasoning)")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"News check: {'YES' if check_news else 'NO (fast mode)'}")
    print(f"CLI mode: {'YES' if cli_mode else 'NO'}")
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
        
        # P2: Skip placeholder teams (W74, W75, L101, etc.)
        if home.startswith("W") or away.startswith("W") or home.startswith("L") or away.startswith("L"):
            print(f"Skipping {mid}: {home} vs {away} — placeholder teams")
            continue
        
        if auto_predict_match(mid, home, away, dry_run=dry_run, check_news=check_news, cli_mode=cli_mode):
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
    parser.add_argument("--cli-mode", action="store_true", help="Enable CLI mode: print full LLM prompt to stdout and read ADJUSTMENT from stdin (for kimi-cli or other external agent CLI)")
    parser.add_argument("--ask-agent", action="store_true", help="Manual copy-paste mode: ask any LLM agent (Kimi/ChatGPT/Claude) in browser and paste response back")
    parser.add_argument("--ask-kimi", action="store_true", help=argparse.SUPPRESS)  # deprecated alias, still works
    parser.add_argument("--fast", action="store_true", help="Skip news check (NOT RECOMMENDED)")
    
    args = parser.parse_args()
    
    dry_run = not args.live
    # Default: check_news = True (always check news unless --fast)
    check_news = not args.fast
    # Support both --ask-agent and deprecated --ask-kimi
    cli_mode = args.cli_mode or args.ask_agent or args.ask_kimi
    run_auto_agent(dry_run=dry_run, match_id=args.match, check_news=check_news, cli_mode=cli_mode)


if __name__ == "__main__":
    main()
