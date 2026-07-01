#!/usr/bin/env python3
"""
Prediction Logger & Performance Tracker

Lưu lại mọi prediction và kết quả để:
1. Tính Brier score / RPS sau mỗi trận
2. Theo dõi calibration accuracy
3. Cập nhật ensemble weights cho các lần chơi sau
4. Phân tích which components work best

Usage:
    from wc26_bnaul.prediction_logger import PredictionLogger
    
    logger = PredictionLogger()
    logger.log_prediction(match_id, home, away, submitted_probs, components, score)
    # After match ends:
    logger.log_result(match_id, actual_home_goals, actual_away_goals, winner)
    # Analyze:
    logger.analyze_performance()
"""

import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple


class PredictionLogger:
    """Logger for predictions and results."""
    
    def __init__(self, log_dir: str = None):
        if log_dir is None:
            # Default: project_root/logs/
            self.log_dir = os.path.join(
                os.path.dirname(__file__), "..", "..", "logs"
            )
        else:
            self.log_dir = log_dir
        
        os.makedirs(self.log_dir, exist_ok=True)
        
        self.predictions_file = os.path.join(self.log_dir, "predictions.jsonl")
        self.results_file = os.path.join(self.log_dir, "results.jsonl")
        self.performance_file = os.path.join(self.log_dir, "performance.json")
    
    def log_prediction(
        self,
        match_id: str,
        home_team: str,
        away_team: str,
        submitted_probs: List[float],
        components: Dict[str, float],
        predicted_score: str,
        reasoning: str = "",
        round_name: str = "",
        weight: float = 1.0,
    ):
        """Log a prediction at submission time."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "match_id": match_id,
            "home_team": home_team,
            "away_team": away_team,
            "submitted_probs": submitted_probs,
            "components": components,
            "predicted_score": predicted_score,
            "reasoning": reasoning,
            "round": round_name,
            "round_weight": weight,
        }
        
        with open(self.predictions_file, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        
        print(f"📝 Logged prediction: {match_id} {home_team} vs {away_team}")
    
    def log_result(
        self,
        match_id: str,
        actual_home_goals: int,
        actual_away_goals: int,
        winner: str,  # "home", "away", "draw"
        home_team: str = None,
        away_team: str = None,
    ):
        """Log match result after it ends."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "match_id": match_id,
            "actual_home_goals": actual_home_goals,
            "actual_away_goals": actual_away_goals,
            "winner": winner,
            "home_team": home_team,
            "away_team": away_team,
        }
        
        with open(self.results_file, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        
        print(f"⚽ Logged result: {match_id} — {actual_home_goals}-{actual_away_goals} ({winner})")
    
    def load_predictions(self) -> List[Dict]:
        """Load all predictions."""
        if not os.path.exists(self.predictions_file):
            return []
        
        predictions = []
        with open(self.predictions_file, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    predictions.append(json.loads(line))
        return predictions
    
    def load_results(self) -> List[Dict]:
        """Load all results."""
        if not os.path.exists(self.results_file):
            return []
        
        results = []
        with open(self.results_file, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    results.append(json.loads(line))
        return results
    
    def get_prediction(self, match_id: str) -> Optional[Dict]:
        """Get prediction for a specific match."""
        for p in self.load_predictions():
            if p["match_id"] == match_id:
                return p
        return None
    
    def get_result(self, match_id: str) -> Optional[Dict]:
        """Get result for a specific match."""
        for r in self.load_results():
            if r["match_id"] == match_id:
                return r
        return None
    
    def calculate_brier(self, submitted_prob: float, outcome: int) -> float:
        """
        Calculate Brier score for binary prediction.
        submitted_prob: probability of home win (or home advance in knockout)
        outcome: 1 if home won, 0 if away won
        """
        return (submitted_prob - outcome) ** 2
    
    def calculate_rps(self, probs: List[float], outcome: int) -> float:
        """
        Calculate Ranked Probability Score for 3-way prediction.
        probs: [P_home, P_draw, P_away]
        outcome: 0=home, 1=draw, 2=away
        """
        cum_probs = [probs[0], probs[0] + probs[1], 1.0]
        cum_outcomes = [1 if outcome == 0 else 0, 1 if outcome in [0, 1] else 0, 1]
        
        rps = 0.0
        for i in range(3):
            rps += (cum_probs[i] - cum_outcomes[i]) ** 2
        
        return rps / 2  # RPS normalization
    
    def analyze_performance(self) -> Dict:
        """
        Analyze prediction performance across all logged matches.
        Returns dict with metrics.
        """
        predictions = self.load_predictions()
        results = self.load_results()
        
        if not predictions or not results:
            print("No data to analyze.")
            return {}
        
        # Build result lookup
        result_map = {r["match_id"]: r for r in results}
        
        metrics = {
            "total_predictions": len(predictions),
            "total_results": len(results),
            "matches_with_results": 0,
            "brier_scores": [],
            "rps_scores": [],
            "weighted_rps": [],
            "by_round": {},
            "by_component": {},
        }
        
        for pred in predictions:
            match_id = pred["match_id"]
            if match_id not in result_map:
                continue
            
            result = result_map[match_id]
            metrics["matches_with_results"] += 1
            
            # Determine outcome
            winner = result["winner"]
            if winner == "home":
                outcome_binary = 1
                outcome_3way = 0
            elif winner == "draw":
                # In knockout, draw goes to penalties. We need to know who actually advances.
                # If result has "advancing_team" field, use it. Otherwise skip this match.
                advancing = result.get("advancing_team", "")
                if advancing == result.get("home_team", ""):
                    outcome_binary = 1
                elif advancing == result.get("away_team", ""):
                    outcome_binary = 0
                else:
                    # Cannot determine who advanced — skip Brier for this match
                    outcome_binary = None
                outcome_3way = 1
            else:
                outcome_binary = 0
                outcome_3way = 2
            
            # Skip if we can't determine binary outcome (draw without advancing_team info)
            if outcome_binary is None:
                continue
            
            # Brier score (binary)
            submitted_probs = pred["submitted_probs"]
            if len(submitted_probs) >= 2:
                home_prob = submitted_probs[0]
                brier = self.calculate_brier(home_prob, outcome_binary)
                metrics["brier_scores"].append(brier)
            
            # RPS (3-way) — if we have 3 probs
            if len(submitted_probs) == 3:
                rps = self.calculate_rps(submitted_probs, outcome_3way)
                weight = pred.get("round_weight", 1.0)
                metrics["rps_scores"].append(rps)
                metrics["weighted_rps"].append(rps * weight)
            
            # By round
            round_name = pred.get("round", "unknown")
            if round_name not in metrics["by_round"]:
                metrics["by_round"][round_name] = {
                    "count": 0, "brier_sum": 0, "rps_sum": 0
                }
            metrics["by_round"][round_name]["count"] += 1
            if "brier" in locals():
                metrics["by_round"][round_name]["brier_sum"] += brier
            if "rps" in locals():
                metrics["by_round"][round_name]["rps_sum"] += rps
            
            # Component analysis — which components predicted correctly?
            components = pred.get("components", {})
            for comp_name, comp_prob in components.items():
                # Skip non-numeric component fields
                if not isinstance(comp_prob, (int, float)):
                    continue
                if comp_name not in metrics["by_component"]:
                    metrics["by_component"][comp_name] = {
                        "correct": 0, "total": 0, "brier_sum": 0
                    }
                metrics["by_component"][comp_name]["total"] += 1
                comp_brier = self.calculate_brier(comp_prob, outcome_binary)
                metrics["by_component"][comp_name]["brier_sum"] += comp_brier
                
                # Check if component predicted correctly (prob > 0.5 and home won, or < 0.5 and away won)
                if (comp_prob > 0.5 and outcome_binary == 1) or (comp_prob < 0.5 and outcome_binary == 0):
                    metrics["by_component"][comp_name]["correct"] += 1
        
        # Calculate averages
        if metrics["brier_scores"]:
            metrics["mean_brier"] = sum(metrics["brier_scores"]) / len(metrics["brier_scores"])
            metrics["skill_pct"] = (1 - metrics["mean_brier"] / 0.25) * 100
        
        if metrics["rps_scores"]:
            metrics["mean_rps"] = sum(metrics["rps_scores"]) / len(metrics["rps_scores"])
            metrics["mean_weighted_rps"] = sum(metrics["weighted_rps"]) / len(metrics["weighted_rps"])
        
        # Round averages
        for round_name, data in metrics["by_round"].items():
            if data["count"] > 0:
                data["mean_brier"] = data["brier_sum"] / data["count"]
                data["mean_rps"] = data["rps_sum"] / data["count"] if data["rps_sum"] > 0 else 0
        
        # Component accuracy
        for comp_name, data in metrics["by_component"].items():
            if data["total"] > 0:
                data["accuracy"] = data["correct"] / data["total"]
                data["mean_brier"] = data["brier_sum"] / data["total"]
        
        # Save performance summary
        with open(self.performance_file, "w") as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        
        return metrics
    
    def print_performance(self):
        """Print formatted performance report."""
        metrics = self.analyze_performance()
        if not metrics:
            print("No performance data available.")
            return
        
        print("\n" + "=" * 60)
        print("PREDICTION PERFORMANCE REPORT")
        print("=" * 60)
        print(f"Total predictions: {metrics['total_predictions']}")
        print(f"Matches with results: {metrics['matches_with_results']}")
        
        if "mean_brier" in metrics:
            print(f"\nMean Brier Score: {metrics['mean_brier']:.4f}")
            print(f"Skill %: {metrics['skill_pct']:.2f}%")
            print(f"  (Baseline Brier = 0.25, Skill% = (1 - Brier/0.25) * 100)")
        
        if "mean_rps" in metrics:
            print(f"\nMean RPS: {metrics['mean_rps']:.4f}")
            print(f"Mean Weighted RPS: {metrics['mean_weighted_rps']:.4f}")
        
        # By round
        if metrics.get("by_round"):
            print(f"\n{'Round':<15} {'Count':<8} {'Mean Brier':<12} {'Mean RPS':<12}")
            print("-" * 50)
            for round_name, data in sorted(metrics["by_round"].items()):
                mean_brier = data.get("mean_brier", 0)
                mean_rps = data.get("mean_rps", 0)
                print(f"{round_name:<15} {data['count']:<8} {mean_brier:<12.4f} {mean_rps:<12.4f}")
        
        # Component accuracy
        if metrics.get("by_component"):
            print(f"\n{'Component':<15} {'Accuracy':<10} {'Mean Brier':<12} {'Count':<8}")
            print("-" * 50)
            for comp_name, data in sorted(
                metrics["by_component"].items(),
                key=lambda x: x[1].get("accuracy", 0),
                reverse=True
            ):
                accuracy = data.get("accuracy", 0)
                mean_brier = data.get("mean_brier", 0)
                print(f"{comp_name:<15} {accuracy:<10.2%} {mean_brier:<12.4f} {data['total']:<8}")
        
        print("=" * 60)
    
    def suggest_weight_updates(self) -> Dict[str, float]:
        """
        Suggest new ensemble weights based on component performance.
        Lower Brier = better = higher weight.
        """
        metrics = self.analyze_performance()
        if not metrics or "by_component" not in metrics:
            return {}
        
        component_data = metrics["by_component"]
        if not component_data:
            return {}
        
        # Calculate inverse Brier (lower Brier = higher score)
        scores = {}
        for comp_name, data in component_data.items():
            mean_brier = data.get("mean_brier", 0.25)
            # Avoid division by zero
            if mean_brier <= 0:
                mean_brier = 0.001
            scores[comp_name] = 1 / mean_brier
        
        # Normalize to sum to 1
        total_score = sum(scores.values())
        if total_score == 0:
            return {}
        
        suggested_weights = {
            comp: score / total_score for comp, score in scores.items()
        }
        
        return suggested_weights
    
    def print_weight_suggestions(self):
        """Print suggested weight updates."""
        suggestions = self.suggest_weight_updates()
        if not suggestions:
            print("Not enough data to suggest weight updates.")
            return
        
        print("\n" + "=" * 60)
        print("SUGGESTED WEIGHT UPDATES")
        print("(Based on component Brier scores — lower Brier = higher weight)")
        print("=" * 60)
        print(f"{'Component':<15} {'Current':<10} {'Suggested':<12} {'Change':<10}")
        print("-" * 50)
        
        # Current weights from ensemble_predictor (FIXED: match actual weights)
        current_weights = {
            "elo": 0.30,
            "fifa": 0.10,
            "xg": 0.20,
            "betting": 0.10,
            "form": 0.15,
            "squad_depth": 0.05,
            "h2h": 0.05,
            "injury": 0.05,
        }
        
        for comp, new_weight in sorted(suggestions.items(), key=lambda x: x[1], reverse=True):
            current = current_weights.get(comp, 0)
            change = new_weight - current
            change_str = f"+{change:+.2f}" if change > 0 else f"{change:+.2f}"
            print(f"{comp:<15} {current:<10.2f} {new_weight:<12.2f} {change_str:<10}")
        
        print("=" * 60)
        print("To apply: Edit WEIGHT_* constants in ensemble_predictor.py")


def main():
    """CLI for prediction logger."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Prediction Logger & Performance Tracker")
    parser.add_argument("--analyze", action="store_true", help="Analyze performance")
    parser.add_argument("--suggest-weights", action="store_true", help="Suggest weight updates")
    parser.add_argument("--log-dir", default=None, help="Log directory")
    
    args = parser.parse_args()
    
    logger = PredictionLogger(log_dir=args.log_dir)
    
    if args.analyze:
        logger.print_performance()
    elif args.suggest_weights:
        logger.print_weight_suggestions()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
