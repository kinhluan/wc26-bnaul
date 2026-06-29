#!/usr/bin/env python3
"""
ClawCup Reasoning Analyzer — Phân tích reasoning của top agents sau khi public

Chiến thuật: Reasoning Pattern Analysis
- Thu thập reasoning của top agents sau mỗi round
- Phân tích patterns và logic
- Tích hợp insights vào model của mình
"""

import argparse
import json
import os
import re
from typing import Dict, List, Optional, Tuple
from collections import Counter, defaultdict

from wc26_bnaul import api_request


def fetch_public_reasonings(match_id: str) -> List[Dict]:
    """
    Fetch public reasonings cho một trận đấu.
    
    API endpoint giả định: /api/v1/predictions/public?match_id=xxx
    Hoặc có thể là: /api/v1/matches/{match_id}/reasonings
    
    TODO: Cập nhật endpoint chính xác khi biết.
    """
    try:
        # Thử các endpoint khác nhau
        endpoints = [
            f"/predictions/public?match_id={match_id}",
            f"/matches/{match_id}/reasonings",
            f"/reasonings?match_id={match_id}",
        ]
        
        for endpoint in endpoints:
            try:
                data = api_request("GET", endpoint)
                if data and "reasonings" in data:
                    return data["reasonings"]
            except Exception:
                continue
        
        return []
    except Exception as e:
        print(f"Error fetching reasonings: {e}")
        return []


def analyze_sentiment(reasoning: str) -> Dict:
    """Phân tích sentiment và keywords trong reasoning."""
    # Positive/negative indicators
    positive_words = ["strong", "superior", "advantage", "favored", "win", "victory", 
                     "dominant", "control", "quality", "depth", "experience"]
    negative_words = ["weak", "inferior", "disadvantage", "underdog", "lose", "defeat",
                      "struggle", "vulnerable", "lack", "limited"]
    
    reasoning_lower = reasoning.lower()
    
    pos_count = sum(1 for w in positive_words if w in reasoning_lower)
    neg_count = sum(1 for w in negative_words if w in reasoning_lower)
    
    # Extract key phrases (2-3 word combinations)
    words = reasoning_lower.split()
    phrases = []
    for i in range(len(words) - 1):
        phrases.append(f"{words[i]} {words[i+1]}")
    
    return {
        "positive_score": pos_count,
        "negative_score": neg_count,
        "sentiment": "positive" if pos_count > neg_count else "negative" if neg_count > pos_count else "neutral",
        "length": len(reasoning),
        "word_count": len(words),
        "key_phrases": phrases[:10],  # Top 10 bigrams
    }


def extract_factors(reasoning: str) -> List[str]:
    """Extract các yếu tố được đề cập trong reasoning."""
    factors = {
        "home_advantage": ["home", "host", "crowd", "fan", "stadium"],
        "form": ["form", "recent", "last match", "unbeaten", "streak"],
        "injury": ["injury", "injured", "suspension", "missing", "absent"],
        "tactics": ["tactical", "formation", "strategy", "coach", "system"],
        "history": ["history", "previous", "past", "record", "head to head"],
        "weather": ["weather", "condition", "rain", "heat", "wind"],
        "motivation": ["motivation", "desire", "pressure", "expectation"],
        "quality": ["quality", "talent", "skill", "ability", "class"],
    }
    
    found_factors = []
    reasoning_lower = reasoning.lower()
    
    for factor, keywords in factors.items():
        if any(kw in reasoning_lower for kw in keywords):
            found_factors.append(factor)
    
    return found_factors


def analyze_top_agents(match_id: str, top_n: int = 10) -> Dict:
    """Phân tích reasoning của top agents cho một trận đấu."""
    reasonings = fetch_public_reasonings(match_id)
    
    if not reasonings:
        print(f"No public reasonings found for {match_id}")
        return {}
    
    # Sort by some metric (e.g., Skill% or accuracy)
    # Assuming each reasoning has a "score" or "rank" field
    top_reasonings = sorted(reasonings, 
                           key=lambda x: x.get("score", 0) or x.get("rank", 999),
                           reverse=True)[:top_n]
    
    analysis = {
        "match_id": match_id,
        "total_reasonings": len(reasonings),
        "top_n": top_n,
        "agents": [],
        "common_factors": Counter(),
        "sentiment_distribution": Counter(),
        "avg_length": 0,
        "consensus_probability": 0.0,
    }
    
    total_prob = 0
    total_length = 0
    
    for r in top_reasonings:
        reasoning_text = r.get("reasoning", "")
        agent = r.get("agent", "unknown")
        prob = r.get("probability", 0.5)
        
        # Analyze
        sentiment = analyze_sentiment(reasoning_text)
        factors = extract_factors(reasoning_text)
        
        analysis["agents"].append({
            "agent": agent,
            "probability": prob,
            "sentiment": sentiment["sentiment"],
            "factors": factors,
            "length": sentiment["length"],
        })
        
        # Aggregate
        for f in factors:
            analysis["common_factors"][f] += 1
        analysis["sentiment_distribution"][sentiment["sentiment"]] += 1
        total_prob += prob
        total_length += sentiment["length"]
    
    if top_reasonings:
        analysis["consensus_probability"] = total_prob / len(top_reasonings)
        analysis["avg_length"] = total_length / len(top_reasonings)
    
    return analysis


def generate_insights(analysis: Dict) -> List[str]:
    """Generate insights từ phân tích."""
    insights = []
    
    if not analysis:
        return insights
    
    # Consensus analysis
    consensus = analysis.get("consensus_probability", 0.5)
    insights.append(f"Consensus probability: {consensus:.0%}")
    
    # Factor analysis
    common_factors = analysis.get("common_factors", Counter())
    if common_factors:
        top_factors = common_factors.most_common(3)
        insights.append(f"Top factors mentioned: {', '.join(f[0] for f in top_factors)}")
    
    # Sentiment analysis
    sentiments = analysis.get("sentiment_distribution", Counter())
    if sentiments:
        total = sum(sentiments.values())
        pos_pct = sentiments.get("positive", 0) / total * 100
        insights.append(f"Positive sentiment: {pos_pct:.0f}% of top agents")
    
    # Length analysis
    avg_length = analysis.get("avg_length", 0)
    insights.append(f"Average reasoning length: {avg_length:.0f} chars")
    
    return insights


def compare_with_my_reasoning(match_id: str, my_reasoning: str, analysis: Dict) -> Dict:
    """So sánh reasoning của mình với top agents."""
    my_factors = extract_factors(my_reasoning)
    my_sentiment = analyze_sentiment(my_reasoning)
    
    top_factors = set(analysis.get("common_factors", Counter()).keys())
    
    # Factors I missed
    missed_factors = top_factors - set(my_factors)
    
    # Factors I have that others don't
    unique_factors = set(my_factors) - top_factors
    
    return {
        "my_factors": my_factors,
        "top_factors": list(top_factors),
        "missed_factors": list(missed_factors),
        "unique_factors": list(unique_factors),
        "my_sentiment": my_sentiment["sentiment"],
        "my_length": my_sentiment["length"],
        "avg_top_length": analysis.get("avg_length", 0),
    }


def save_analysis(match_id: str, analysis: Dict, output_dir: str = "reasoning_analysis"):
    """Lưu analysis vào file."""
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"{output_dir}/{match_id}.json"
    with open(filename, "w") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    
    print(f"Analysis saved to {filename}")


def batch_analyze_matches(match_ids: List[str], output_dir: str = "reasoning_analysis"):
    """Phân tích hàng loạt các trận đấu."""
    print("=" * 70)
    print("BATCH REASONING ANALYSIS")
    print("=" * 70)
    
    all_analyses = {}
    
    for match_id in match_ids:
        print(f"\nAnalyzing {match_id}...")
        analysis = analyze_top_agents(match_id)
        
        if analysis:
            insights = generate_insights(analysis)
            print("\n".join(f"  → {i}" for i in insights))
            
            save_analysis(match_id, analysis, output_dir)
            all_analyses[match_id] = analysis
        else:
            print(f"  → No data available")
    
    # Aggregate analysis
    print("\n" + "=" * 70)
    print("AGGREGATE INSIGHTS")
    print("=" * 70)
    
    all_factors = Counter()
    all_sentiments = Counter()
    
    for analysis in all_analyses.values():
        for factor, count in analysis.get("common_factors", Counter()).items():
            all_factors[factor] += count
        for sentiment, count in analysis.get("sentiment_distribution", Counter()).items():
            all_sentiments[sentiment] += count
    
    print(f"\nMost common factors across all matches:")
    for factor, count in all_factors.most_common(10):
        print(f"  {factor}: {count} mentions")
    
    print(f"\nSentiment distribution:")
    total = sum(all_sentiments.values())
    for sentiment, count in all_sentiments.most_common():
        print(f"  {sentiment}: {count}/{total} ({count/total:.1%})")
    
    return all_analyses


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ClawCup Reasoning Analyzer")
    parser.add_argument("--match", help="Analyze a specific match ID")
    parser.add_argument("--batch", nargs="+", help="Analyze multiple match IDs")
    parser.add_argument("--output", default="reasoning_analysis", help="Output directory")
    parser.add_argument("--my-reasoning", help="Compare with your reasoning text")
    
    args = parser.parse_args()
    
    if args.match:
        analysis = analyze_top_agents(args.match)
        if analysis:
            insights = generate_insights(analysis)
            print("\n".join(insights))
            
            if args.my_reasoning:
                comparison = compare_with_my_reasoning(args.match, args.my_reasoning, analysis)
                print("\nComparison with your reasoning:")
                print(json.dumps(comparison, indent=2))
            
            save_analysis(args.match, analysis, args.output)
    
    elif args.batch:
        batch_analyze_matches(args.batch, args.output)
    
    else:
        print("Usage:")
        print("  python reasoning_analyzer.py --match m001")
        print("  python reasoning_analyzer.py --batch m001 m002 m003")
        print("  python reasoning_analyzer.py --match m001 --my-reasoning 'your reasoning here'")
