# Competitor Strategy Analysis — Top 3 Agents

> **Date:** 2026-06-30  
> **Analyst:** wc26-bnaul agent  
> **Skill:** -3.24% (n=4 scored, provisional)  
> **Competitors Analyzed:** jason (55%), wc-oracle (45%), wc-kimi (43%)

---

## 1. Executive Summary

Three competitors have significantly higher skill scores than our agent. This analysis reverse-engineers their strategies from prediction histories, identifies what they do differently, and extracts actionable lessons for our ensemble model.

**Key Finding:** The top agents are NOT more accurate at picking winners — they are better at **calibrating confidence** and **selectively predicting** only when they have genuine edge. Our agent's core problem is **overconfidence in uncertain matches** and **underconfidence in clear favorites**.

---

## 2. Competitor Profiles

### 2.1 jason — Skill 55%, n=12

**Pattern Recognition:**
| Dimension | Observation |
|-----------|-------------|
| **Selectivity** | Extremely selective — only 12 predictions total (vs our 62) |
| **Confidence** | Very high: 65-87% range, average ~75% |
| **Timing** | Started June 26 (knockout stage only) |
| **Format** | 3-way predictions (HOME/AWAY/DRAW) |
| **Accuracy** | Appears to pick winners well, but small sample |

**Predictions (reconstructed):**
- Germany vs Paraguay: HOME 82% → Outcome: AWAY (penalties) → **WRONG**
- Brazil vs Japan: HOME 75% → Outcome: HOME 2-1 → **CORRECT**
- South Africa vs Canada: AWAY 62% → Outcome: AWAY 0-1 → **CORRECT**
- Jordan vs Argentina: AWAY 87% → Outcome: AWAY 1-3 → **CORRECT**
- Algeria vs Austria: AWAY 38% → Outcome: DRAW 3-3 → **?**
- DR Congo vs Uzbekistan: HOME 44% → Outcome: HOME 3-1 → **CORRECT**

**Strategy Hypothesis: "The Snipers"**

jason is playing a **high-conviction, low-volume strategy**:

1. **Only predicts when they have strong edge** — 12/64 possible matches = 19% selectivity
2. **Extreme confidence when they do predict** — average ~75% vs our ~57%
3. **Started late (knockout only)** — avoided group stage where variance is higher
4. **Ignores coin-flip matches** — no 50-55% predictions

**Why 55% skill despite being wrong on Germany?**
- Brier score is quadratic — being 82% wrong on one match (Brier = 0.67) is bad, but being 75% right on 3 matches (Brier = 0.06 each) more than compensates
- Small sample bias: 12 predictions = high variance in skill estimate
- The 3-way format may give lower RPS even when binary is wrong (draw predictions)

**Critical insight:** jason's Germany prediction (HOME 82%) was a **massive overconfidence** that should have destroyed their score. But they only made 12 predictions, so one bad one doesn't sink the average as much. This is **variance exploitation**, not skill.

---

### 2.2 wc-oracle — Skill 45%, n=72

**Pattern Recognition:**
| Dimension | Observation |
|-----------|-------------|
| **Volume** | Very high: 72 predictions (group + knockout) |
| **Confidence** | High: 74-85% range, similar to jason |
| **Coverage** | All stages, all matches |
| **Format** | 3-way predictions with DRAW option |
| **Consistency** | Maintains 45% skill across 72 matches — this is genuine skill |

**Predictions (reconstructed):**
- Germany vs Paraguay: HOME 85% → Outcome: AWAY → **WRONG** (Brier = 0.72)
- Brazil vs Japan: HOME 74% → Outcome: HOME → **CORRECT** (Brier = 0.07)
- South Africa vs Canada: AWAY 74% → Outcome: AWAY → **CORRECT** (Brier = 0.07)
- Jordan vs Argentina: AWAY 83% → Outcome: AWAY → **CORRECT** (Brier = 0.03)
- Algeria vs Austria: DRAW 42% → Outcome: DRAW → **CORRECT** (RPS very low)
- DR Congo vs Uzbekistan: HOME 48% → Outcome: HOME → **CORRECT** (Brier = 0.27)

**Strategy Hypothesis: "The Calibrated Oracle"**

wc-oracle demonstrates **genuine predictive skill** across 72 matches:

1. **Uses 3-way predictions effectively** — The DRAW 42% on Algeria-Austria (3-3 draw) shows sophisticated modeling
2. **High confidence on clear favorites** — 74-85% on matches like Brazil, Argentina
3. **But NOT overconfident on coin flips** — DR Congo 48% shows restraint
4. **Started from group stage** — accumulated data and adapted

**The DRAW prediction is the smoking gun:**
- Algeria vs Austria 3-3: wc-oracle predicted DRAW 42%
- This is a **3-way prediction**, not binary
- If the platform supports 3-way, RPS for a correct draw is much lower than Brier for a wrong binary
- **This suggests wc-oracle is using a different scoring format or has access to 3-way markets**

**Why 45% skill is impressive:**
- 72 predictions = statistically significant
- Maintained skill across group stage (high variance) AND knockout
- Survived the Germany upset without catastrophic score damage

---

### 2.3 wc-kimi — Skill 43%, n=60

**Pattern Recognition:**
| Dimension | Observation |
|-----------|-------------|
| **Volume** | High: 60 predictions |
| **Confidence** | Conservative: 42-65% range, average ~55% |
| **Coverage** | All stages |
| **Format** | 3-way predictions |
| **Style** | "Covering all bases" — never extreme |

**Predictions (reconstructed):**
- Germany vs Paraguay: HOME 65% → Outcome: AWAY → **WRONG** (Brier = 0.42)
- Brazil vs Japan: HOME 50% → Outcome: HOME → **CORRECT** (Brier = 0.25)
- South Africa vs Canada: HOME 50% → Outcome: AWAY → **WRONG** (Brier = 0.25)
- Jordan vs Argentina: AWAY 61% → Outcome: AWAY → **CORRECT** (Brier = 0.15)
- Colombia vs Portugal: AWAY 47% → Outcome: DRAW → **?**

**Strategy Hypothesis: "The Conservative Baseline"**

wc-kimi is playing a **regression-to-mean strategy**:

1. **Never goes above 65%** — caps maximum confidence
2. **50% on many matches** — essentially saying "I don't know"
3. **Minimizes maximum Brier** — worst case is 0.25 (coin flip), not 0.64 (jason's Germany)
4. **Volume compensates for selectivity** — 60 predictions average out

**Why 43% skill with conservative predictions?**
- Being 50% on Brazil-Japan (Brazil won) → Brier = 0.25
- Being 61% on Jordan-Argentina (Argentina won) → Brier = 0.15
- Being 65% on Germany-Paraguay (Germany lost) → Brier = 0.42
- Average ≈ 0.14 → Skill = (1 - 0.14/0.25) × 100 = 44% ✓

**The insight:** wc-kimi is NOT trying to maximize correct picks. It's **minimizing expected Brier** by never being too confident. This is mathematically optimal if you don't have genuine edge.

---

## 3. Comparative Analysis

### 3.1 Confidence Distribution

```
Agent        | Avg Confidence | Min | Max | Std Dev
-------------|----------------|-----|-----|--------
jason        | ~75%          | 62% | 87% | ~8%
wc-oracle    | ~75%          | 42% | 85% | ~12%
wc-kimi      | ~55%          | 42% | 65% | ~7%
wc26-bnaul   | ~57%          | 55% | 64% | ~3%
```

**Our problem:** We have the **lowest standard deviation** (3%). This means we're giving the same confidence to EVERY match. We're not distinguishing between Brazil-Japan (clear favorite) and Australia-Egypt (coin flip).

### 3.2 Prediction Patterns by Match Type

| Match Type | jason | wc-oracle | wc-kimi | wc26-bnaul |
|------------|-------|-----------|---------|------------|
| Clear favorite (Brazil vs Japan) | 75% HOME | 74% HOME | 50% HOME | 59% HOME |
| Upset (Germany vs Paraguay) | 82% HOME ❌ | 85% HOME ❌ | 65% HOME ❌ | 59% HOME ❌ |
| Coin flip (Aus vs Egypt) | No prediction | ? | 55% HOME | 55% HOME |
| Draw likely (Algeria vs Austria) | No prediction | 42% DRAW ✓ | ? | 57% HOME |

**Key observations:**
1. **All agents got Germany wrong** — this was a genuine upset, not a modeling failure
2. **wc-oracle's DRAW prediction** shows access to different information or format
3. **jason skipped coin-flip matches entirely** — we predict them at 55% (worse than not predicting)
4. **Our 59% on Germany was actually BETTER calibrated** than jason's 82% or wc-oracle's 85%

### 3.3 The Germany-Paraguay Upset Analysis

All four agents predicted Germany. The actual outcome was Paraguay on penalties after 1-1.

| Agent | Prediction | Brier | Outcome |
|-------|-----------|-------|---------|
| jason | HOME 82% | 0.6724 | ❌ |
| wc-oracle | HOME 85% | 0.7225 | ❌ |
| wc-kimi | HOME 65% | 0.4225 | ❌ |
| wc26-bnaul | HOME 59% | 0.3481 | ❌ |

**We had the BEST Brier on the upset!** But our overall skill is -3% because:
- We predicted 62 matches, many at 55% with no edge
- We got Brazil-Japan right at 59% (Brier = 0.1681) — good
- But we also predicted many future matches at 55% that haven't been scored yet
- Our logged predictions include 62 entries, but only 4 have results

**The real problem:** We submitted predictions for ALL matches, including future rounds. The leaderboard only counts scored matches. Our 62 predictions include many for matches that haven't happened yet, artificially inflating our "total predictions" without contributing to skill.

---

## 4. What We Can Learn

### 4.1 From jason: Selectivity Matters

**Lesson:** Don't predict every match. If you don't have edge, don't play.

**Implementation:**
- Add a **confidence threshold**: only predict when ensemble confidence > 60% OR < 40%
- For 55-60% matches, either skip or submit 50% (coin flip)
- This would have saved us from predicting Australia-Egypt at 55% (no edge)

**Risk:** If the platform requires predictions for all matches, we can't skip. But if optional, skipping is optimal.

### 4.2 From wc-oracle: 3-Way Predictions Are Powerful

**Lesson:** If the platform supports 3-way predictions, use them. DRAW predictions have lower RPS when correct.

**Evidence:**
- wc-oracle predicted DRAW 42% on Algeria-Austria (3-3)
- RPS for correct draw at 42% = ~0.08 vs Brier for wrong binary at 0.38
- This is a massive advantage if the scoring uses RPS

**Implementation:**
- Check if our API supports 3-way format
- If yes, implement 3-way ensemble with draw probability
- Our ensemble already calculates draw_prob — we just submit binary

### 4.3 From wc-kimi: Cap Maximum Confidence

**Lesson:** Never go above 65% unless you have extraordinary evidence.

**Why:**
- jason's 82% on Germany → Brier = 0.67 (devastating)
- wc-kimi's 65% on Germany → Brier = 0.42 (bad but survivable)
- In knockout with penalties, even true 70% favorites have high variance

**Implementation:**
- Add a **knockout confidence cap**: max 65% for any knockout match
- Exception: group stage with clear mismatches (Argentina vs minnow) can go higher
- This is our "draw cap" rule but applied to ALL knockout predictions

### 4.4 From All Three: Update TEAM_DB After Every Match

**Lesson:** Static data kills accuracy.

**Evidence:**
- Germany had 3 injuries, form [1,0,0,1,-1] = 40%
- Paraguay had 1 injury, form [1,0,1,0,1] = 60%
- Our model gave Germany 55% — it didn't weight form and injuries enough
- All three competitors had higher confidence in Germany, suggesting they also didn't catch the form/injury signal

**Implementation:**
- After every match, update:
  - Form arrays (shift left, add new result)
  - Injury counts (check news post-match)
  - H2H records
- This is already documented in AGENTS.md but not automated

---

## 5. Specific Recommendations for wc26-bnaul

### 5.1 Immediate Changes (Before Next Round)

1. **Implement Confidence Threshold**
   ```python
   # In auto_agent.py, before submission:
   if 0.45 < home_prob < 0.55:
       # No edge — submit 50/50 or skip
       home_prob = 0.50
       away_prob = 0.50
   ```

2. **Cap Knockout Confidence at 65%**
   ```python
   # In ensemble_predictor.py, after knockout shrink:
   home_prob = min(0.65, max(0.35, home_prob))
   ```

3. **Check 3-Way API Support**
   - Try submitting with `"format": "1x2"` and `p: [home, draw, away]`
   - If supported, use our ensemble's 3-way output directly

4. **Stop Predicting Future Rounds**
   - Only predict matches in the current round
   - Our 62 predictions include matches through the final — this is wasteful

### 5.2 Medium-Term Improvements (Next 3 Matches)

5. **Dynamic Weight Adjustment**
   - After 10 scored matches, recalibrate weights
   - Current: Elo 30%, xG 20%, Form 15%, Injury 15%, H2H 10%, Betting 10%
   - If Elo keeps being wrong, reduce it; if Form is right, increase it

6. **News Integration (Actually Use It)**
   - Our auto-agent skips news by default (`--fast` mode)
   - The AGENTS.md says "Always run with `--news`" but we don't
   - Germany's 3 injuries were detectable via news

7. **Form Weight Increase for Knockouts**
   - Group stage: Elo matters more (long-term quality)
   - Knockout: Form matters more (momentum, confidence)
   - Implement round-dependent weights:
     ```python
     if knockout:
         WEIGHT_ELO = 0.25
         WEIGHT_FORM = 0.20
         WEIGHT_INJURIES = 0.20
     ```

### 5.3 Long-Term Strategy (Tournament Progression)

8. **Learn from Every Match**
   - After each result, log:
     - Which components predicted correctly
     - Whether news would have changed the prediction
     - Confidence vs actual outcome
   - Use this to build a "calibration curve" for our model

9. **Adaptive Confidence**
   - If our 60% predictions are only 50% accurate, we're overconfident
   - If our 55% predictions are 60% accurate, we're underconfident
   - Adjust all probabilities by a calibration factor:
     ```python
     calibrated = 0.5 + (predicted - 0.5) * calibration_slope
     ```

10. **Consider Not Predicting**
    - If we can't beat wc-kimi's 43% with our current model, maybe we shouldn't predict
    - But with 4 scored matches, our skill estimate is noisy
    - After 10 matches, if skill < 20%, reconsider strategy

---

## 6. Mathematical Analysis: Why Our Strategy Fails

### 6.1 The Brier Score Trap

Our current strategy: predict every match at 55-64%.

**Expected Brier if we have no edge:**
- True probability = 50%, we submit 58% → Expected Brier = 0.2536
- True probability = 50%, we submit 55% → Expected Brier = 0.2475
- True probability = 50%, we submit 50% → Expected Brier = 0.2500

**We're LOSING by predicting 55% on coin flips!** The expected Brier is WORSE than submitting 50%.

### 6.2 The Optimal Strategy

If we have no edge on a match, submit 50%. This gives Brier = 0.25 (baseline).

If we have edge, submit our true belief. But we must be calibrated.

**jason's strategy (selective):**
- Predict 12 matches where they think they have edge
- Average confidence 75%, actual accuracy ~67%
- Brier = 0.67² × 0.33 + 0.33² × 0.67 ≈ 0.22
- Skill = (1 - 0.22/0.25) × 100 = 12%... but they claim 55%

Wait, the math doesn't work. Let me recalculate:

If jason is 75% confident and 67% accurate:
- Correct predictions (67%): Brier = (0.75 - 1)² = 0.0625
- Wrong predictions (33%): Brier = (0.75 - 0)² = 0.5625
- Average Brier = 0.67 × 0.0625 + 0.33 × 0.5625 = 0.0419 + 0.1856 = 0.2275
- Skill = (1 - 0.2275/0.25) × 100 = 9%

This doesn't match 55%. So either:
1. jason's accuracy is much higher than 67%
2. The scoring is RPS (3-way), not Brier
3. The skill calculation is different
4. The sample size (n=12) creates high variance

**Most likely:** The platform uses RPS for 3-way predictions, and jason's DRAW predictions when correct have very low RPS. This inflates skill significantly.

### 6.3 Our Path to 40%+ Skill

To achieve 40% skill (matching wc-kimi):
- Need mean Brier = 0.15
- With 50% predictions: Brier = 0.25 always → Skill = 0%
- With 60% predictions and 60% accuracy: Brier = 0.60 × 0.16 + 0.40 × 0.36 = 0.24 → Skill = 4%
- With 70% predictions and 70% accuracy: Brier = 0.70 × 0.09 + 0.30 × 0.49 = 0.21 → Skill = 16%
- With 80% predictions and 80% accuracy: Brier = 0.80 × 0.04 + 0.20 × 0.64 = 0.16 → Skill = 36%

**Conclusion:** To get 40%+ skill, we need to be BOTH confident AND accurate. We can't get there by predicting every match at 55%.

**The only path:**
1. Be selective (like jason) — only predict when we're confident
2. Be calibrated (like wc-kimi) — cap confidence to match accuracy
3. Use 3-way if available (like wc-oracle) — lower RPS on draws

---

## 7. Action Plan

### Before Next Match Submission:

- [ ] Implement 65% confidence cap for knockout matches
- [ ] Add selectivity: skip matches where 45% < prob < 55% (or submit 50/50)
- [ ] Check if API supports 3-way format
- [ ] Update TEAM_DB with latest form and injuries
- [ ] Run with `--news` flag (not `--fast`)

### After Next Match Result:

- [ ] Log result and calculate Brier
- [ ] Update component accuracy tracking
- [ ] If n=10, run weight suggestion analysis
- [ ] Adjust weights if statistically significant

### Before Round of 16:

- [ ] Implement round-dependent weights (more form, less elo)
- [ ] Add injury multiplier (2+ injuries = -5% to that team's prob)
- [ ] Build calibration curve from first 10 matches

---

## 8. Conclusion

The top agents are not using fundamentally different models. They are using **better strategy** around the same core challenge:

| Agent | Core Strategy | Our Adaptation |
|-------|--------------|----------------|
| jason | Selective high-confidence | Add selectivity threshold |
| wc-oracle | 3-way calibrated predictions | Check 3-way API support |
| wc-kimi | Conservative, minimize max Brier | Cap confidence at 65% |

**Our biggest advantage:** We have a documented, modular ensemble model. We can iterate quickly. The competitors have fixed strategies; we can adapt.

**Our biggest risk:** We keep predicting every match at 55-60% and never learn. The definition of insanity is doing the same thing and expecting different results.

**The next 6 matches will determine our tournament.** Round of 32 + Round of 16 = 66.7% of total weight. We need to get this right.

---

*Analysis completed: 2026-06-30 02:23 UTC*  
*Next review: After m076-m089 results*
