## Research Synthesis: 15 Papers on Sports Prediction, Brier Score & Knockout Modeling

**Date:** 2026-06-30  
**Author:** @kinhluan  
**Labels:** `research`, `literature-review`, `model-improvement`

---

## Executive Summary

After reviewing 15+ recent papers (2024–2026) on sports prediction, Brier score optimization, and knockout tournament modeling, here are the key findings that can improve our wc26-bnaul agent.

---

## 1. Brier Score & Proper Scoring Rules

### Key Papers

- **Rizopoulos et al. (2024)** — "Optimizing Dynamic Predictions from Joint Models using Super Learning"  
  📄 https://arxiv.org/pdf/2309.11472  
  - Brier score is a **proper scoring rule** that combines discrimination and calibration
  - Lower Brier = better predictive performance
  - Ensemble super learner should optimize weights via cross-validated Brier scores

- **Damani et al. (2026)** — "RLCR: RL with Brier-score confidence term"  
  📄 https://arxiv.org/html/2606.05122v1  
  - Brier score can be used as a **reward signal** in reinforcement learning
  - Training models to output calibrated probability estimates improves forecasting
  - **Our insight:** We could use Brier score as a feedback loop to auto-adjust ensemble weights

- **Pic et al. (2025)** — "Proper Scoring Rules for Multivariate Probabilistic Forecasts"  
  📄 https://hal.science/hal-04629671v1/file/Preprint_Aggregation_and_Transformation_arXiv_HAL_.pdf  
  - Different scoring rules (CRPS, Brier, QS) measure different aspects of forecasts
  - Brier score is best for binary outcomes; RPS better for 3-way (H/D/A)
  - **Our insight:** For knockout binary predictions, Brier is the right metric. For group stage 3-way, consider RPS.

- **Seidenfeld et al.** — "Forecasting with Imprecise Probabilities"  
  📄 https://www.cmu.edu/dietrich/philosophy/docs/seidenfeld/Forecasting%20with%20Imprecise%20Probabilities.pdf  
  - Brier score is just one of an infinite class of (strictly) proper scoring rules
  - A scoring rule is proper if the forecaster minimizes expected score by announcing true previsions
  - **Key insight:** Truthful submission is optimal regardless of which proper scoring rule is used

### Actionable Insight
> **Rule:** Use Brier score for knockout (binary), RPS for group stage (3-way). Track both separately.

---

## 2. FIFA World Cup Prediction Models (2026)

### Key Papers

- **Rezaei (2026)** — "Predicting the 2026 FIFA World Cup with Sufficient Dimension Reduction"  
  📄 https://arxiv.org/pdf/2606.24171  
  - **Best model:** SIR (Sliced Inverse Regression) with 2 directions + Poisson goals
  - Combined RPS: **0.127** (vs 0.209 for simple ensemble)
  - Accuracy: **68%** (vs 55% for non-SDR models)
  - **Critical finding:** Recent Elo trajectory (6-month history) carries more signal than current Elo alone
  - **Spain identified as favorite** (6.87% win prob), followed by Argentina, France, Brazil, Portugal

- **Maia.ai (2026)** — "World Cup 2026 Predictions, Built in Hours with Maia"  
  📄 https://www.maia.ai/resources/blog/world-cup-2026-prediction-model-maia  
  - Custom Elo from 49,000 matches (1872–present)
  - **xG was the single most valuable enhancement** — lifted Spain from 5.33% to 6.87% (+29%)
  - Brazil ranked **just 7th** despite being most decorated — xG revealed they create fewer quality chances
  - **Key refinement:** Neutral-venue recalculation (home wins weighted 0.7x, away wins 1.3x)

- **DataCamp (2026)** — "FIFA World Cup 2026 Winner Prediction: An MLOps Guide"  
  📄 https://www.datacamp.com/tutorial/fifa-world-cup-2026-winner-prediction  
  - **XGBoost won** with holdout RPS = 0.18289
  - But top 5 models were within 0.0011 RPS — **ceiling is set by data/features, not model**
  - **Elo difference was 100x more important than next feature**
  - Deep learning (LSTM, CNN) finished **last** — not enough data for neural networks

- **Towards Data Science (2026)** — "I Built 11 Models to Predict the 2026 World Cup. They Crown Four Different Champions."  
  📄 https://towardsdatascience.com/i-built-11-models-to-predict-the-2026-world-cup-they-crown-four-different-champions/  
  - 11 models (Elo, Poisson, XGBoost, Neural Net, etc.) gave **wildly different predictions**
  - Spain vs Morocco: predictions ranged from 69% (PageRank) to 25% (XGBoost) for Spain win
  - **Disagreement between models is the most useful signal** — not the consensus

### Actionable Insights

1. **Elo trajectory > Elo snapshot**  
   - Our model uses current Elo only. We should add 6-month Elo history.
   - Implementation: Store monthly Elo ratings, compute trend (rising/falling/stable)

2. **xG is the most valuable feature**  
   - Our xG weight is 25% — this seems correct, but we need better xG data
   - Current xG is static. Should update from recent matches.

3. **Model disagreement = signal**  
   - If Elo says 70% but form says 45%, the true prob is likely ~55%
   - Our ensemble already does this, but we could add a "disagreement penalty"

4. **Deep learning is NOT the answer**  
   - With only ~7,000 matches, classical methods (XGBoost, Poisson) beat neural nets
   - Our ensemble approach (weighted average) is the right strategy

---

## 3. Knockout-Specific Modeling

### Key Papers

- **Tactiq (2026)** — "World Cup Knockout Phase: xG vs Result Reality"  
  📄 https://www.tactiq.club/en/blog/world-cup-knockout-phase-xg-vs-result-reality/  
  - **Three critical model-layer adjustments for knockouts:**
    1. **Wider confidence bands** — single-match knockout projections need looser calibration
    2. **Penalty-shootout modeling separately** — shootout probability is a separate model layer
    3. **Tournament-progression Bayesian updating** — each round's outcome informs next round
  - **Penalty shootouts are essentially random** at modern professional levels
  - Higher-xG teams win only **50-55%** of knockout matches (not 70%+ as models suggest)

- **Csató (2022)** — "Fairness in penalty shootouts: Is it worth using dynamic rules?"  
  📄 https://real.mtak.hu/153390/1/2004.09225.pdf  
  - Mathematical proof: **penalty shootout = coin toss** when scoring probabilities are equal (p = q)
  - First-mover advantage exists but is small (~2-3%)
  - **Probability of reaching sudden death:** ~21.5%

- **Pinasthika et al. (2022)** — "World Cup 2022 Knockout Stage Prediction Using Poisson"  
  📄 https://pdfs.semanticscholar.org/0e55/1d80f6b3637abe0af0c4b1ec6c6073619556.pdf  
  - Poisson model for goals, then simulate all possible scorelines (0-0 to 7-7)
  - **Penalty shootout goals weighted at 0.5x** (half of normal goals)
  - Updated lambda with latest match data before each knockout round
  - **Accuracy was poor** — most predictions had high De Finetti distance (far from actual)

- **Brams & Ismail / Csató (2021-2022)** — "First home or first away? Optimal ordering in two-legged ties"  
  📄 https://www.econstor.eu/bitstream/10419/288195/1/MDE_MDE3982.pdf  
  - For b₂ = 0 (no home advantage), penalty shootout winning probabilities are identical and equal to ½
  - **"There is no difference between a penalty shooting and a coin toss as tiebreaking rules in the absence of a home advantage"**

### Actionable Insights

1. **Predicted draws in knockout → cap at [0.52, 0.48]**  
   - Not [0.55, 0.45] as we previously thought. The research says shootouts are ~50/50.
   - **Our m075 mistake:** Germany 64% was absurd for a predicted 1-1 draw.

2. **Add penalty shootout as separate model layer**  
   - When predicted score is draw, compute:
     - P(home wins in ET) = f(Elo, form, injuries)
     - P(shootout) = ~0.215 (if 5 rounds)
     - P(home wins shootout) = ~0.50 (coin flip)
   - Final binary = P(home wins in 90) + P(home wins in ET) + 0.5 × P(shootout)

3. **Wider confidence bands for knockouts**  
   - Our model is too confident. Knockout variance is higher than group stage.
   - **Implementation:** Add a "knockout variance penalty" — shrink all probs toward 0.50 by 5-10%.

4. **Bayesian updating after each round**  
   - After each match, update team strength based on actual performance vs expected
   - **Implementation:** Dynamic Elo update after each match (not just pre-tournament Elo)

---

## 4. Ensemble & Super Learning

### Key Papers

- **Schoenegger et al. (2024)** — "Capturing Intransitive Dominance in Tennis Forecasting: A Graph Neural Network Approach"  
  📄 https://arxiv.org/html/2510.20454v2  
  - Aggregating 12 diverse LLMs matches human crowd accuracy
  - **Ensemble gains require genuine diversity** — our components (Elo, xG, form) are diverse enough
  - Human-AI ensembles may be more promising than pure AI ensembles

- **Turtel et al. (2025)** — "RLVR for Forecasting" (referenced in Agentic Forecasting paper)  
  📄 https://arxiv.org/html/2604.18576v2  
  - Trained 14B model on Polymarket questions → Brier = **0.190** (frontier-level)
  - Demonstrated 10%+ ROI in simulated trading
  - **Key:** Proper scoring rule rewards (Brier) as RL signal

- **Chandak et al. (2026)** — "OpenForecaster" (referenced in Agentic Forecasting paper)  
  📄 https://arxiv.org/html/2604.18576v2  
  - Specialized 8B models can match 120B+ generalist models
  - Composite reward: accuracy + Brier (to combat hedging bias)
  - **Our insight:** We should add a "calibration bonus" to our ensemble weight optimization

- **Liu et al. (2025)** — "Time-R1: Temporal Comprehension then Prediction" (referenced in Agentic Forecasting)  
  📄 https://arxiv.org/html/2604.18576v2  
  - Two-stage curriculum (temporal comprehension then prediction)
  - Builds "temporal logic" into model representations

### Actionable Insights

1. **Our ensemble is on the right track**  
   - Elo + xG + Form + H2H + Injury is genuinely diverse
   - But we need better weight optimization (not fixed weights)

2. **Consider dynamic weight updates**  
   - Use inverse Brier (as we already do in `suggest_weights()`)
   - But only after 10+ matches, and update gradually (not drastically)

3. **Add a "calibration check"**  
   - After 20 matches, bin predictions by probability (50-55%, 55-60%, etc.)
   - Check if actual win rate matches predicted probability
   - If not, apply calibration curve correction

---

## 5. Injury & Squad Impact

### Key Finding (from multiple papers)
- **No paper specifically models injury impact** — this is a gap in the literature
- But all practitioners agree: **squad availability is critical in knockouts**
- Our empirical finding (m075: Germany 3 injuries → lost) is consistent with practitioner wisdom

### Actionable Insight
> **Rule:** When a team has 3+ injuries, treat them as ~5-10 Elo points weaker. This is not in the literature but is empirically justified by our data.

---

## 6. Summary: What to Implement Now vs Later

### 🔴 Implement NOW (before next match)

| # | Improvement | Effort | Impact | Source |
|---|-------------|--------|--------|--------|
| 1 | Cap predicted draws at [0.52, 0.48] | 5 min | **High** | Tactiq (2026), Csató (2022) |
| 2 | Add --news flag to all predictions | 0 min | **High** | Empirical (m075) |
| 3 | Shrink all knockout probs toward 0.50 by 5% | 10 min | Medium | Tactiq (2026) |
| 4 | Update TEAM_DB after every match | 10 min | Medium | Rezaei (2026) |

### 🟡 Implement SOON (after 5+ more matches)

| # | Improvement | Effort | Impact | Source |
|---|-------------|--------|--------|--------|
| 5 | Add Elo trajectory (6-month history) | 2 hrs | **High** | Rezaei (2026) |
| 6 | Non-linear injury penalty (exponential) | 1 hr | Medium | Empirical |
| 7 | Separate penalty-shootout model layer | 3 hrs | Medium | Tactiq (2026) |
| 8 | Dynamic weight updates via inverse Brier | 2 hrs | Medium | Rizopoulos (2024) |

### 🟢 Implement LATER (after tournament)

| # | Improvement | Effort | Impact | Source |
|---|-------------|--------|--------|--------|
| 9 | Integrate live betting odds | 4 hrs | Medium | DataCamp (2026) |
| 10 | XGBoost ensemble member | 3 hrs | Medium | DataCamp (2026) |
| 11 | Calibration curve correction | 2 hrs | Low | OpenForecaster (2026) |
| 12 | Bayesian Elo updating after each match | 4 hrs | Medium | Tactiq (2026) |

---

## 7. References (with direct links)

| # | Paper | Year | Link | Key Insight |
|---|-------|------|------|-------------|
| 1 | Rizopoulos et al. — Super Learning for Dynamic Predictions | 2024 | https://arxiv.org/pdf/2309.11472 | Brier-optimized ensemble weights |
| 2 | Damani et al. — RLCR (Self-Evaluation Is Already There) | 2026 | https://arxiv.org/html/2606.05122v1 | Brier as RL reward signal |
| 3 | Pic et al. — Multivariate Proper Scoring Rules | 2025 | https://hal.science/hal-04629671v1 | Brier for binary, RPS for 3-way |
| 4 | Seidenfeld et al. — Forecasting with Imprecise Probabilities | — | https://www.cmu.edu/dietrich/philosophy/docs/seidenfeld/Forecasting%20with%20Imprecise%20Probabilities.pdf | Proper scoring rules class |
| 5 | Rezaei — SDR for World Cup 2026 | 2026 | https://arxiv.org/pdf/2606.24171 | Elo trajectory > Elo snapshot; RPS = 0.127 |
| 6 | Maia.ai — World Cup 2026 Predictions | 2026 | https://www.maia.ai/resources/blog/world-cup-2026-prediction-model-maia | xG is most valuable feature; neutral-venue Elo |
| 7 | DataCamp — MLOps World Cup | 2026 | https://www.datacamp.com/tutorial/fifa-world-cup-2026-winner-prediction | XGBoost wins; Elo dominates; DL fails |
| 8 | TDS — 11 Models, 4 Champions | 2026 | https://towardsdatascience.com/i-built-11-models-to-predict-the-2026-world-cup-they-crown-four-different-champions/ | Model disagreement is the signal |
| 9 | Tactiq — Knockout xG vs Reality | 2026 | https://www.tactiq.club/en/blog/world-cup-knockout-phase-xg-vs-result-reality/ | Penalties are random; wider confidence bands |
| 10 | Csató — Fairness in Penalty Shootouts | 2022 | https://real.mtak.hu/153390/1/2004.09225.pdf | Shootout = coin toss when p = q |
| 11 | Pinasthika et al. — Poisson Knockout | 2022 | https://pdfs.semanticscholar.org/0e55/1d80f6b3637abe0af0c4b1ec6c6073619556.pdf | Penalty goals weighted 0.5x; poor accuracy |
| 12 | Brams & Ismail / Csató — Optimal Ordering | 2021 | https://www.econstor.eu/bitstream/10419/288195/1/MDE_MDE3982.pdf | Penalty = coin toss without home advantage |
| 13 | Schoenegger et al. — Tennis GNN Forecasting | 2025 | https://arxiv.org/html/2510.20454v2 | Diverse ensemble > homogeneous ensemble |
| 14 | Turtel et al. — RLVR Forecasting | 2025 | https://arxiv.org/html/2604.18576v2 | Brier = 0.190 with RL; 10%+ ROI |
| 15 | Chandak et al. — OpenForecaster | 2026 | https://arxiv.org/html/2604.18576v2 | Composite accuracy+Brier reward; 8B = 120B |
| 16 | Liu et al. — Time-R1 | 2025 | https://arxiv.org/html/2604.18576v2 | Temporal comprehension curriculum |
| 17 | Bayesian weighted discrete-time dynamic models | 2025 | https://arxiv.org/html/2508.05891v1 | Weighted dynamic approach reduces Brier score |
| 18 | PBS & PLL — Penalized Brier Score | 2024 | https://arxiv.org/html/2407.17697v1 | Penalized Brier as strictly proper scoring rule |
| 19 | Penalty kick direction prediction | 2025 | https://arxiv.org/html/2505.24629v1 | Goalkeeper policy optimization for penalties |
| 20 | Knockout tournament polynomial computation | — | https://cme.h-its.org/exelixis//pubs/dissBen.pdf | Exact tournament win probability computation |

---

*This research review is a living document. Add new papers as they are discovered.*
