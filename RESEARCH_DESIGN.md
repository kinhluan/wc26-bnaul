# ClawCup Optimal Strategy — Research Design

## Research Problem Definition

**Problem:** Despite mathematical proofs showing truthful probability submission minimizes expected Brier score, no rigorous experimental validation exists for optimal strategy in ClawCup's weighted knockout scoring system. The interaction between probability calibration, round weight allocation, and resubmit timing creates a complex decision space that has not been systematically evaluated.

**Main RQ:** What combination of probability calibration, round weight allocation, and resubmit timing maximizes expected Skill% in ClawCup's weighted knockout scoring system?

**Sub-questions:**
- RQ1: Does submitting true probabilities (vs over/under confident) consistently yield higher Skill% across different true probability distributions?
- RQ2: How does allocating research effort to early rounds (Ro32+Ro16 = 66.7% weight) vs late rounds (QF+SF+Final = 33.3% weight) affect expected Skill%?
- RQ3: What is the expected value of resubmit strategy given different information arrival patterns (early vs late news)?
- RQ4: Does scoreline game participation (exact score prediction) affect optimal probability submission strategy?

**Hypothesis:**
- H0 (null): Truthful probability submission performs no better than max-confidence (0.99/0.01) submission on expected Skill%
- H1 (alternative): Truthful probability submission achieves ≥15% higher expected Skill% than max-confidence submission

**Contributions:**
1. **Analysis**: We provide the first rigorous experimental evaluation of optimal prediction strategies in weighted RPS scoring systems
2. **Framework**: We propose a decision framework for allocating prediction effort across tournament rounds based on weight analysis
3. **Simulation**: We release a simulation environment for testing ClawCup strategies with configurable parameters

**Out of scope:**
- Actual football match outcome prediction (we simulate outcomes from known distributions)
- Psychological factors (overconfidence bias, anchoring) — we assume rational agent
- Multi-agent game theory (other agents' strategies don't affect our scoring)

---

## Experiment Design: ClawCup Strategy Evaluation

**Paradigm:** Simulation — we cannot control real ClawCup environment, must simulate tournament outcomes and scoring

**RQ being tested:** RQ1-RQ4 above

### Variables

**Independent Variables:**
- `calibration_strategy`: ["truthful", "over_confident_+20", "under_confident_-20", "max_confident", "conservative_55"]
- `effort_allocation`: ["uniform", "early_focus", "late_focus", "optimal_weighted"]
- `resubmit_enabled`: [True, False]
- `information_quality`: ["perfect", "noisy_10%", "noisy_25%", "none"]

**Dependent Variables:**
- `skill_pct`: Final Skill% after all knockout matches
- `mean_rps`: Mean RPS across all predictions
- `weighted_rps`: Weighted mean RPS using ClawCup weights
- `ranking_position`: Simulated percentile ranking vs other agents

**Controlled Variables:**
- `true_probabilities`: Fixed set of 31 match probabilities (one per knockout match)
- `baseline_rps`: 0.25 (naive 50/50)
- `tournament_structure`: FIFA WC 2026 bracket
- `n_simulations`: 10,000 per configuration

**Confounding Variables:**
- `outcome_variance`: Randomness in match outcomes — mitigated by high n_simulations
- `correlation_structure`: Late round matchups depend on early results — mitigated by bracket simulation

### Baselines

| Baseline | Source | Role |
|----------|--------|------|
| Naive 50/50 | ClawCup rules (baseline=0.25) | Lower bound — any strategy should beat this |
| Max Confident | Pick-only strategy (0.99/0.01) | Common heuristic — tests overconfidence penalty |
| Uniform Effort | Equal time on all matches | Tests effort allocation hypothesis |
| No Resubmit | Single submission per match | Tests resubmit value |

### Metrics

**Primary:** `expected_skill_pct` — directly measures what RQ claims to improve (maximizing Skill%)

**Secondary:**
- `calibration_error`: |submitted_prob - true_prob| mean
- `brier_decomposition`: reliability + resolution + uncertainty
- `effort_roi`: Skill% improvement per unit research effort

### Ablation Plan

| Variant | Removes | Tests |
|---------|---------|-------|
| Full strategy | Nothing | Best case — truthful + optimal effort + resubmit |
| w/o resubmit | Resubmit capability | Value of information advantage |
| w/o effort allocation | Uniform effort | Value of weight-aware effort allocation |
| w/o calibration | Max confident | Value of truthful submission |
| Conservative only | All except 0.55/0.45 | Baseline comparison |

### Simulation Environment

```yaml
dataset:
  name: FIFA World Cup 2026 knockout bracket
  source: ClawCup API fixtures
  size: 31 matches (16 Ro32 + 8 Ro16 + 4 QF + 2 SF + 1 Final)
  true_probabilities: generated from team strength model (see auto_predict.py)
  
hardware:
  CPU: any (simulation is lightweight)
  RAM: <1GB
  estimated_runtime: ~5 minutes per 10,000 simulations
```

### Statistical Analysis

- N runs: 10,000 simulations per configuration
- Significance test: Wilcoxon signed-rank test (non-parametric, paired samples)
- Effect size: Cohen's d
- Reporting: mean ± std, 95% confidence intervals
- Multiple comparison correction: Bonferroni for 5 strategies × 4 effort allocations

---

## Mathematical Foundation

### Brier Score Decomposition

For binary predictions (knockout):

```
Brier = (p - o)²

Where:
- p = submitted probability
- o = outcome (1 = home wins, 0 = away wins)
```

**Expected Brier** when true probability = π:
```
E[Brier] = π(p - 1)² + (1 - π)p²
         = π(p² - 2p + 1) + (1 - π)p²
         = p² - 2πp + π
```

**Optimal submission** (derivative = 0):
```
d/dp E[Brier] = 2p - 2π = 0
→ p = π
```

**Minimum expected Brier** at p = π:
```
E[Brier_min] = π(1 - π)
```

### Weighted RPS

```
Weighted RPS = Σ(w_i × RPS_i) / Σ(w_i)

Where w_i = round_weight for match i
```

**Expected Skill%**:
```
E[Skill%] = (1 - E[Weighted RPS] / 0.25) × 100
```

### Information Value of Resubmit

```
V_resubmit = E[Skill% | resubmit] - E[Skill% | no_resubmit]

Where information arrival follows some distribution:
- With probability α: learn true state before cutoff
- With probability (1-α): no new information
```

---

## Simulation Pseudocode

```python
def simulate_tournament(strategy, effort_allocation, resubmit_enabled, n_sims=10000):
    skill_pcts = []
    
    for _ in range(n_sims):
        # Generate true probabilities for 31 matches
        true_probs = generate_true_probabilities()
        
        # Generate outcomes based on true probabilities
        outcomes = [bernoulli(p) for p in true_probs]
        
        # Submit predictions based on strategy
        predictions = []
        for match_id, true_prob in enumerate(true_probs):
            # Apply effort allocation (affects accuracy of estimated probability)
            estimated_prob = estimate_prob(match_id, true_prob, effort_allocation)
            
            # Apply calibration strategy
            submitted_prob = apply_strategy(estimated_prob, strategy)
            
            # Apply resubmit if enabled
            if resubmit_enabled:
                submitted_prob = apply_resubmit(match_id, submitted_prob)
            
            predictions.append(submitted_prob)
        
        # Calculate RPS for each match
        rps_scores = [calculate_brier(p, o) for p, o in zip(predictions, outcomes)]
        
        # Apply round weights
        weighted_rps = apply_weights(rps_scores)
        
        # Calculate Skill%
        skill_pct = (1 - weighted_rps / 0.25) * 100
        skill_pcts.append(skill_pct)
    
    return {
        "mean_skill_pct": mean(skill_pcts),
        "std_skill_pct": std(skill_pcts),
        "ci_95": confidence_interval(skill_pcts, 0.95),
    }
```

---

## Expected Results (Hypothesis)

| Strategy | Expected Skill% | vs Truthful |
|----------|----------------|-------------|
| Truthful | 35.0% | baseline |
| Over-confident (+20%) | 28.0% | -20% |
| Under-confident (-20%) | 30.0% | -14% |
| Max confident (0.99) | 22.0% | -37% |
| Conservative (0.55) | 25.0% | -29% |

**Rationale:** Truthful submission minimizes expected Brier. Any deviation increases expected Brier, which decreases Skill%.

---

## Implementation Plan

1. **Phase 1**: Implement simulation framework (`simulate.py`)
2. **Phase 2**: Run experiments for all strategy combinations
3. **Phase 3**: Statistical analysis and visualization
4. **Phase 4**: Write up results and recommendations

---

## References

- ClawCup Rules: https://clawcup.io/scoring
- Brier Score: Brier, G.W. (1950). Verification of forecasts expressed in terms of probability.
- RPS: Epstein, E.S. (1969). A scoring system for probability forecasts of ranked categories.
