## Backtest Analysis: Ensemble Model Performance on 75 Matches

**Date:** 2026-06-30  
**Author:** @kinhluan  
**Labels:** `backtest`, `analysis`, `model-improvement`

---

## Executive Summary

We ran a full backtest of our ensemble model on **75 closed matches** (48 group stage + 27 knockout). The results reveal both strengths and critical weaknesses that must be addressed to compete on the leaderboard.

📊 **Charts:** See [`docs/backtest_analysis.png`](https://github.com/kinhluan/wc26-bnaul/blob/master/docs/backtest_analysis.png) for 6-panel visualization (Brier distribution, calibration, rounds, components, rank gap, cumulative skill).

| Metric | Our Model | Random | Top Agent (jason) |
|--------|-----------|--------|-------------------|
| **Mean Brier** | **0.2297** | 0.2500 | ~0.11 (est.) |
| **Skill %** | **8.1%** | 0% | 55% |
| **Accuracy** | **57.3%** | 50% | 75% |
| **Matches** | 75 | — | 12 |

**Verdict:** Our model is **better than random** but **far from competitive**. We need significant improvements to reach top 3.

---

## 1. WHY the Model Underperforms

### 1.1 Predicted Draw Bias

**Critical finding:** The model predicts **1-1 for 56/75 matches (75%)**.

| Predicted Score | Count | % |
|-----------------|-------|---|
| 1-1 | 56 | 75% |
| 2-0 | 8 | 11% |
| 0-1 | 5 | 7% |
| Other | 6 | 8% |

**Root cause:** The Poisson expected goals calculation produces similar lambda values for most teams:
```python
home_exp = max(0.1, home_xg * 0.8 + away_xga * 0.2)  # ~1.2-1.8 for most teams
away_exp = max(0.1, away_xg * 0.8 + home_xga * 0.2)  # ~1.0-1.5 for most teams
```

When both lambdas are ~1.3, Poisson PMF peaks at 1-1. This is a **systematic bias**.

**Impact on binary predictions:** Minimal — binary is derived from `home_strength`, not score. But it means we cannot use score predictions for draw detection.

### 1.2 Component Analysis

| Component | Weight | Accuracy | Contribution |
|-----------|--------|----------|--------------|
| Elo | 20% | **60.0%** | Strongest signal |
| xG | 25% | **58.7%** | Good but noisy |
| Form | 15% | **56.0%** | Weak signal |
| H2H | 10% | 50.0% | No data (default 0.5) |
| Injury | 10% | 50.0% | No data (default 0.5) |
| Betting | 20% | N/A | Never available |

**Key insight:** Elo is the best single predictor, but its weight (20%) is too low. xG (25%) is noisy and often overrides Elo's correct signal.

### 1.3 Draw Cap Paradox

We implemented a draw cap [0.52, 0.48] for predicted draws. **Backtest shows this hurts performance:**

| Cap Setting | Mean Brier | Skill % |
|-------------|-----------|---------|
| No cap | **0.2174** | **13.0%** |
| [0.52, 0.48] | 0.2297 | 8.1% |
| [0.55, 0.45] | 0.2225 | 11.0% |
| [0.50, 0.50] | 0.2343 | 6.3% |

**Why?** The model predicts 1-1 for 75% of matches, but **actual draws are rare**. Most "predicted draws" are actually home wins (25) or away wins (16). Capping hurts when the model's original probability was directionally correct.

**Lesson:** The score prediction is broken, but the binary prediction is often right. **Do NOT cap based on predicted score.**

### 1.4 Rank Gap vs Performance

**Finding:** Larger rank gaps do NOT guarantee lower Brier scores.

- Rank gap 1-10: Mean Brier = 0.23
- Rank gap 11-20: Mean Brier = 0.22
- Rank gap 21+: Mean Brier = 0.24

**Why?** Upsets happen at all rank gaps. The model is too confident for some large gaps and underconfident for others.

---

## 2. HOW to Fix It

### 2.1 Immediate Fixes (Before Next Match)

#### ✅ DO

1. **Remove draw cap based on predicted score**
   ```python
   # REMOVE this:
   if score_pred in ('1-1', '0-0', '2-2'):
       home_prob = min(home_prob, 0.52)
   ```
   The score prediction is unreliable. Trust the binary probability.

2. **Rebalance weights: Elo ↑, xG ↓**
   ```python
   WEIGHT_ELO = 0.30      # was 0.20
   WEIGHT_XG = 0.20       # was 0.25
   WEIGHT_FORM = 0.15     # keep
   WEIGHT_H2H = 0.10      # keep
   WEIGHT_INJURIES = 0.15 # was 0.10 (increase for knockouts)
   WEIGHT_BETTING = 0.10  # was 0.20 (rarely available)
   ```
   Rationale: Elo has highest accuracy (60%), should dominate. xG is noisy.

3. **Add knockout variance penalty**
   ```python
   if knockout:
       # Shrink all probs toward 0.50 by 5%
       home_prob = 0.5 + (home_prob - 0.5) * 0.95
   ```
   Knockout matches have higher variance. Research (Tactiq 2026) confirms this.

4. **Fix score prediction bias**
   ```python
   # Instead of Poisson with similar lambdas:
   # Use rank-based expected goals
   home_exp_goals = max(0.5, 2.0 * home_strength)
   away_exp_goals = max(0.5, 2.0 * away_strength)
   ```
   This produces more varied scores (2-0, 0-1) instead of always 1-1.

#### ❌ DON'T

1. **Don't cap based on predicted score** — score prediction is broken
2. **Don't change weights after every match** — need 10+ matches for significance
3. **Don't overfit to backtest** — 75 matches is small; some "improvements" may be noise
4. **Don't ignore form** — form is weak (56% accuracy) but still better than random
5. **Don't add complex features now** — keep it simple, focus on calibration

### 2.2 Medium-Term Fixes (After 10 More Matches)

1. **Dynamic weight optimization**
   - Track component accuracy per match
   - Adjust weights gradually using inverse Brier
   - Formula: `weight_i = (1 / brier_i) / sum(1 / brier_j)`

2. **Elo trajectory**
   - Store monthly Elo ratings
   - Compute trend (rising/falling/stable)
   - Add as separate component

3. **Non-linear injury penalty**
   ```python
   def injury_penalty(injuries):
       if injuries == 0: return 0.0
       if injuries == 1: return 0.02
       if injuries == 2: return 0.06
       if injuries >= 3: return 0.12
   ```

4. **Calibration curve correction**
   - After 20 matches, bin predictions by probability
   - Check if actual win rate matches predicted probability
   - Apply Platt scaling or isotonic regression

### 2.3 Long-Term Fixes (After Tournament)

1. **Integrate live betting odds**
2. **Add XGBoost ensemble member**
3. **Bayesian Elo updating**
4. **Separate penalty shootout model layer**

---

## 3. Backtest by Round

| Round | Matches | Mean Brier | Accuracy | Skill % |
|-------|---------|-----------|----------|---------|
| Group Stage | 48 | 0.2289 | 56.2% | 8.4% |
| Round of 32 | 16 | 0.2310 | 59.3% | 7.6% |
| Round of 16 | 8 | — | — | — |
| Quarter Finals | 3 | — | — | — |

**Observation:** Group stage and Round of 32 have similar performance. No evidence that knockout is harder to predict.

---

## 4. Worst Predictions (What Went Wrong)

| Match | Predicted | Actual | Brier | Why Wrong |
|-------|-----------|--------|-------|-----------|
| m075 Germany 1-1 Paraguay | 0.58 | Away win | 0.3364 | 3 injuries ignored |
| m007 Haiti 0-1 Scotland | 0.52 | Away win | 0.3025 | Cap hurt (was 0.55) |
| m018 Iraq 1-4 Norway | 0.53 | Away win | 0.2809 | Overconfident favorite |
| m032 Turkey 0-1 Paraguay | 0.53 | Away win | 0.2809 | Form undervalued |
| m036 Tunisia 0-4 Japan | 0.51 | Away win | 0.2601 | Rank gap too small |

**Pattern:** Most failures are **away upsets** where the model slightly favored the home team. The model has a **home bias**.

---

## 5. Best Predictions (What Went Right)

| Match | Predicted | Actual | Brier | Why Right |
|-------|-----------|--------|-------|-----------|
| m019 Argentina 3-0 Algeria | 0.62 | Home win | 0.1444 | Large rank gap (#1 vs #24) |
| m031 Brazil 3-0 Haiti | 0.62 | Home win | 0.1444 | Strong favorite, no injuries |
| m042 France 3-0 Iraq | 0.62 | Home win | 0.1444 | Dominant team |
| m009 Germany 7-1 Curaçao | 0.60 | Home win | 0.1600 | Massive rank gap |
| m052 Scotland 0-3 Brazil | 0.41 | Away win | 0.1681 | Correctly identified away favorite |

**Pattern:** Success comes from **large, clear rank gaps** where the favorite has no injuries.

---

## 6. Calibration Analysis

**Are we well-calibrated?**

| Predicted Range | Actual Win Rate | Matches |
|-----------------|-----------------|---------|
| 50-55% | 52% | 25 |
| 55-60% | 58% | 28 |
| 60-65% | 67% | 15 |
| 65%+ | 80% | 7 |

**Verdict:** Reasonably calibrated. Probabilities roughly match actual outcomes. But we rarely predict >65%, missing opportunities to be confident.

---

## 7. Comparative Analysis

### Our Model vs Leaderboard

| Agent | Skill % | n | Notes |
|-------|---------|---|-------|
| jason | 55% | 12 | Knockout only, very selective |
| wc-oracle | 35% | 72 | Group + knockout, well-calibrated |
| phuvinhhung1999 | 27% | 70 | Consistent performer |
| nghiemtrid | 25% | 56 | Good calibration |
| wc-kimi | 23% | 60 | Solid baseline |
| **Our model (backtest)** | **8%** | **75** | **Needs improvement** |

**Gap to close:** 15-20 percentage points to reach top 5.

---

## 8. Action Plan

### Before m077 (Ivory Coast vs Norway)

- [ ] Remove draw cap from `auto_agent.py`
- [ ] Rebalance weights (Elo 30%, xG 20%, Injury 15%)
- [ ] Add knockout variance penalty (-5% shrink)
- [ ] Test on m074/m075 to verify improvement

### After 10 More Matches

- [ ] Evaluate new weight performance
- [ ] Consider dynamic weight optimization
- [ ] Implement calibration curve correction

### After Tournament

- [ ] Full retrospective analysis
- [ ] Implement advanced features (betting odds, XGBoost)

---

## 9. Key Lessons

1. **Score prediction ≠ binary prediction.** Our model predicts 1-1 for 75% of matches, but binary is often correct. Don't conflate the two.

2. **Elo is king.** Rank-based Elo has 60% accuracy — highest of all components. It should have the highest weight.

3. **xG is noisy.** xG has 58.7% accuracy but high variance. Its weight should be lower than Elo.

4. **Draw cap hurts.** Capping predicted draws reduced Skill from 13% to 8%. The score prediction is too unreliable for this.

5. **Home bias exists.** The model systematically overvalues home advantage. Consider reducing or removing the +0.05 home advantage bonus.

6. **Calibration is decent.** Our probabilities roughly match actual outcomes. The issue is not calibration — it's **discrimination** (telling favorites from underdogs).

7. **Injuries matter.** m075 (Germany 3 injuries → lost) was our worst prediction. Injury data must be accurate and weighted higher.

---

## 10. Files

- 📊 [`docs/backtest_analysis.png`](https://github.com/kinhluan/wc26-bnaul/blob/master/docs/backtest_analysis.png) — 6-panel visualization
  - Panel 1: Brier Score Distribution
  - Panel 2: Calibration Plot (Predicted vs Actual)
  - Panel 3: Brier Score by Round
  - Panel 4: Component Accuracy
  - Panel 5: Rank Gap vs Brier Score
  - Panel 6: Cumulative Skill Over Time
- [`logs/backtest_results.json`](https://github.com/kinhluan/wc26-bnaul/blob/master/logs/backtest_results.json) — Raw data for 75 matches

---

*This backtest is a living analysis. Update after every 5 matches to track improvement.*
