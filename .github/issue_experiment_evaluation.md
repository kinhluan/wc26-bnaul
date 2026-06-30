# Experiment Evaluation: wc26-bnaul Prediction Agent

**Date:** 2026-06-30  
**Author:** @kinhluan  
**Labels:** `experiment-evaluation`, `academic-review`, `rigor-assessment`

---

## Executive Summary

Using the **kinhluan experiment-tracking framework**, we conducted a rigorous academic evaluation of the wc26-bnaul prediction agent. The verdict: **promising prototype, not rigorous research** (2.9/5).

| Aspect | Score (1-5) | Status |
|--------|-------------|--------|
| Research Question | 4 | ✅ Well-motivated |
| Literature Review | 4 | ✅ Good coverage |
| Methodology | 2 | ❌ Basic ensemble, no optimization |
| Experimental Design | 2 | ❌ No train/test split, no CV |
| Results Analysis | 2 | ❌ Shallow analysis |
| Reproducibility | 4 | ✅ Deterministic, logged |
| Contribution | 2 | ❌ Overstated |
| **Overall** | **2.9/5** | **Prototype → needs rigor** |

---

## 1. Experiment Log Entry

```yaml
id: exp_wc26_backtest_001
date: 2026-06-30
status: completed

hypothesis: "An ensemble model combining xG, Elo, Form, H2H, and Injury signals can achieve Skill > 20% in a Brier-score prediction tournament"

method: EnsemblePredictor (weighted average)
variant: full

config:
  dataset: FIFA World Cup 2026 (75 closed matches)
  components:
    - xG: weight=0.25
    - Elo: weight=0.20
    - Form: weight=0.15
    - H2H: weight=0.10
    - Injury: weight=0.10
    - Betting: weight=0.20 (fallback to Elo when unavailable)
  seed: N/A (deterministic model)
  
results:
  mean_brier: 0.2297
  skill_pct: 8.1
  accuracy: 57.3
  matches_tested: 75
  
baseline_comparison:
  random_prediction: 0.2500 (skill=0%)
  delta_brier: -0.0203
  delta_skill: +8.1%
  
observations: "Model is better than random but far from competitive. Top agents achieve 20-55% skill."
next_step: "Rebalance weights (Elo↑, xG↓), remove draw cap, add knockout variance penalty"
```

---

## 2. Experimental Design Rigor

### 2.1 Criterion-by-Criterion Assessment

| Criterion | Status | Notes |
|-----------|--------|-------|
| **Clear hypothesis** | ⚠️ Partial | Hypothesis stated but not falsifiable. "Skill > 20%" is arbitrary — no theoretical justification |
| **Appropriate baseline** | ✅ Yes | Random prediction (Brier=0.25) is the correct baseline for strictly proper scoring rules |
| **Sufficient sample size** | ⚠️ Marginal | 75 matches is adequate for initial evaluation but small for weight optimization |
| **Train/test split** | ❌ **CRITICAL** | **No holdout set. Model evaluated on same data it was implicitly tuned on** |
| **Cross-validation** | ❌ No | No k-fold or time-series CV. Cannot assess generalization |
| **Reproducibility** | ✅ Yes | Code is deterministic, weights are fixed, data is logged |
| **Statistical significance** | ❌ No | No p-values, confidence intervals, or statistical tests vs baseline |

**Verdict:** Experimental design is **exploratory, not rigorous**. Suitable for initial prototype but insufficient for publication.

### 2.2 Metrics Assessment

| Metric | Appropriate? | Notes |
|--------|-------------|-------|
| **Brier Score** | ✅ Yes | Correct for binary knockout predictions. Strictly proper scoring rule |
| **Skill %** | ✅ Yes | Standardized measure: (0.25 - Brier) / 0.25 × 100 |
| **Accuracy** | ⚠️ Partial | Useful but secondary. Brier is the primary metric |
| **Calibration** | ❌ Missing | No reliability diagrams or calibration curves |
| **Discrimination** | ❌ Missing | No ROC-AUC or precision-recall analysis |
| **Component-wise Brier** | ❌ Missing | Cannot identify which component is failing |

**Verdict:** Primary metrics correct, but **missing calibration and discrimination analysis**.

### 2.3 Threats to Validity

| Threat | Severity | Description |
|--------|----------|-------------|
| **Overfitting to weights** | 🔴 High | Weights were likely tuned on same 75 matches. No independent validation |
| **Data leakage** | 🟡 Medium | TEAM_DB includes form arrays that may include future matches |
| **Selection bias** | 🟡 Medium | Only 75 matches available. Earlier/later matches may have different characteristics |
| **Temporal non-stationarity** | 🟡 Medium | Team strength changes over tournament. Model doesn't adapt dynamically |
| **Home advantage assumption** | 🟡 Medium | Fixed +0.05 bonus may not apply to neutral venues |
| **Missing injury data** | 🟡 Medium | Injury counts are estimates, not verified |
| **Small sample for weight tuning** | 🟡 Medium | 75 matches insufficient to optimize 6 weights reliably |
| **Publication bias** | 🟢 Low | Literature review appears comprehensive (15 papers) |

---

## 3. Literature Alignment

| Paper | Our Implementation | Gap |
|-------|-------------------|-----|
| Rezaei (2026) SDR | We use Elo, not SDR | SDR achieved RPS=0.127 vs our ~0.23 |
| Maia.ai (2026) xG | We use xG=25% weight | They found xG most valuable — we underweight it relative to Elo |
| DataCamp (2026) XGBoost | We use weighted average | XGBoost won but by tiny margin; our ensemble approach is valid |
| Tactiq (2026) knockout | We don't model penalties separately | They suggest separate penalty layer — we ignore this |
| Csató (2022) penalties | We cap draws | Mathematical proof says shootout=coin toss — our cap is heuristic |
| Rizopoulos (2024) Super Learning | Fixed weights | They optimize weights via CV — we use fixed weights |

**Verdict:** Literature review is **good** but implementation **lags behind SOTA**.

---

## 4. Contribution Clarity

**Claimed contribution:** "An autonomous agent leveraging probabilistic forecasting, external data integration, and real-time information monitoring"

**Actual contribution:**
- ✅ Probabilistic forecasting: Yes (ensemble model)
- ⚠️ External data integration: Partial (xG, Elo, form are static; betting never available)
- ❌ Real-time information monitoring: No (news check is manual, not automated)
- ❌ Optimization: No (weights are fixed, not optimized)

**Verdict:** Contribution is **overstated**. The agent is a basic ensemble with static weights, not an optimized autonomous system.

---

## 5. Recommendations for Improvement

### 5.1 Immediate (Before Next Match)

#### ✅ DO

1. **Remove draw cap** — Backtest shows it hurts performance (Skill 13% → 8%)
2. **Rebalance weights** — Elo 30%, xG 20%, Injury 15%, Form 15%, H2H 10%, Betting 10%
3. **Add knockout variance penalty** — Shrink probs toward 0.50 by 5%
4. **Log component-wise Brier** — Track which component is failing per match

#### ❌ DON'T

1. **Don't cap based on predicted score** — score prediction is unreliable
2. **Don't change weights after every match** — need 10+ matches for significance
3. **Don't overfit to backtest** — 75 matches is small; some "improvements" may be noise
4. **Don't ignore form** — form is weak (56% accuracy) but still better than random
5. **Don't add complex features now** — keep it simple, focus on calibration

### 5.2 Short-term (Next 10 Matches)

1. **Implement cross-validation** — Time-series CV on completed matches to validate weight changes
2. **Add calibration curves** — Bin predictions by probability, check actual win rates
3. **Statistical testing** — Wilcoxon signed-rank test vs random baseline
4. **Dynamic weight updates** — Use inverse Brier to adjust weights gradually

### 5.3 Long-term (After Tournament)

1. **Proper train/test split** — Reserve 20% of historical matches for final evaluation
2. **Grid search for weights** — Systematic search over weight space with CV
3. **XGBoost ensemble member** — Add as additional component
4. **Separate penalty model** — Model shootout probability explicitly
5. **Bayesian Elo updating** — Update team strength after each match

---

## 6. Additional Experiments Needed

| Experiment | Purpose | Priority |
|------------|---------|----------|
| **Ablation study** — Remove each component | Identify which components matter | 🔴 High |
| **Weight sweep** — Grid search over 6 weights | Find optimal weight combination | 🔴 High |
| **Calibration analysis** — Reliability diagram | Check if probabilities are well-calibrated | 🟡 Medium |
| **Time-series CV** — 5-fold CV on match history | Assess generalization | 🟡 Medium |
| **Bootstrap confidence intervals** — 1000 resamples | Quantify uncertainty in Skill estimate | 🟡 Medium |
| **Sensitivity analysis** — Vary injury penalty | Test robustness to injury assumptions | 🟢 Low |
| **Ensemble diversity** — Correlation between components | Check if ensemble is truly diverse | 🟢 Low |

---

## 7. Paper-Writing Readiness

| Section | Status | Notes |
|---------|--------|-------|
| **Introduction/RQ** | ✅ Ready | Clear RQ, well-motivated |
| **Related Work** | ✅ Ready | 15 papers reviewed, well-synthesized |
| **Methodology** | ⚠️ Partial | Ensemble described but no theoretical justification for weights |
| **Experiments** | ❌ Needs work | No train/test split, no statistical tests, no CV |
| **Results** | ⚠️ Partial | Brier scores reported but no calibration/discrimination analysis |
| **Discussion** | ❌ Missing | No comparison with theoretical optimum |
| **Conclusion** | ❌ Missing | No clear contribution statement |

**Verdict:** Not ready for submission. Needs:
1. Rigorous experimental design (train/test split, CV)
2. Statistical testing
3. Calibration analysis
4. Clearer contribution statement

---

## 8. Path to Publication

To make this publishable, the work needs:

1. **Novelty**: Dynamic weight optimization or real-time adaptation mechanism
2. **Rigor**: Proper train/test split, cross-validation, statistical testing
3. **Scale**: Test on multiple tournaments (not just World Cup 2026)
4. **Comparison**: Compare against 3+ baselines (random, Elo-only, betting odds)
5. **Theory**: Theoretical analysis of why ensemble works (e.g., bias-variance decomposition)

**Estimated effort:** 2-3 months of focused work to reach conference-ready quality.

---

## 9. Overall Assessment

| Aspect | Score (1-5) | Notes |
|--------|-------------|-------|
| Research Question | 4 | Clear and well-motivated |
| Literature Review | 4 | Good coverage, could be deeper |
| Methodology | 2 | Basic ensemble, no optimization |
| Experimental Design | 2 | No train/test split, no CV |
| Results Analysis | 2 | Metrics correct but analysis shallow |
| Reproducibility | 4 | Code is deterministic and logged |
| Contribution | 2 | Overstated relative to actual innovation |
| **Overall** | **2.9/5** | **Promising prototype, not rigorous research** |

---

*Evaluation conducted using the kinhluan experiment-tracking framework. Recommend re-evaluating after implementing CV and weight optimization.*
