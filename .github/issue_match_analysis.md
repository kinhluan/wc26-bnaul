## Match Analysis: m074 (Brazil vs Japan) & m075 (Germany vs Paraguay)

**Date:** 2026-06-30  
**Author:** @kinhluan  
**Labels:** `analysis`, `performance`, `knockout-stage`

---

### Executive Summary

After the first two knockout matches concluded, our ensemble model achieved **1 correct, 1 incorrect** prediction. This issue provides a detailed post-match analysis to understand what the model got right, what it missed, and how we can improve.

| Match | Prediction | Actual Result | Brier Score | Outcome |
|-------|-----------|---------------|-------------|---------|
| m074 Brazil vs Japan | [0.59, 0.41] | Brazil 2-1 Japan (H) | **0.1681** | ✅ Correct |
| m075 Germany vs Paraguay | [0.64, 0.36] | Germany 1-1 Paraguay (A wins on penalties) | **0.4096** | ❌ Incorrect |

**Mean Brier: 0.2581** (worse than random baseline 0.25, but sample size = 2)

---

### m074: Brazil vs Japan — Why It Was Correct

#### Pre-match Team Data

| Metric | Brazil | Japan | Advantage |
|--------|--------|-------|-----------|
| FIFA Rank | #3 | #16 | Brazil +13 |
| xG (expected goals) | 2.1 | 1.4 | Brazil +0.7 |
| xGA (expected goals against) | 0.8 | 1.3 | Brazil +0.5 |
| Form (last 5) | [1,1,1,0,1] = 80% W | [0,0,1,1,-1] = 40% W | Brazil +40% |
| Injuries | 0 | 0 | Even |

#### Model Components

```
Component     Value    Weight    Contribution
elo           0.70     20%       0.140
xg            0.60     25%       0.150
form          0.60     15%       0.090
h2h           0.50     10%       0.050
injury        0.50     10%       0.050
betting       0.50     20%       0.100  (no betting data available)
─────────────────────────────────────────────
Weighted sum: 0.48
+ Home advantage: +0.05
= Home strength: 0.53 → Binary: [0.59, 0.41]
```

#### Analysis

Brazil dominated on **every single metric**: rank, xG, xGA, and form. The model correctly identified Brazil as the favorite. The 59% probability was well-calibrated — Brazil won 2-1, a narrow victory that reflects the model's "slight favorite" assessment rather than an overwhelming one.

**Key insight:** When the stronger team has **zero injuries** and **superior form**, the model performs as expected.

---

### m075: Germany vs Paraguay — Why It Was Wrong

#### Pre-match Team Data

| Metric | Germany | Paraguay | Advantage |
|--------|---------|----------|-----------|
| FIFA Rank | #6 | #28 | Germany +22 |
| xG | 1.8 | 1.1 | Germany +0.7 |
| xGA | 1.0 | 1.5 | Germany +0.5 |
| Form (last 5) | [1,0,0,1,-1] = 40% W | [1,0,1,0,1] = 60% W | **Paraguay +20%** |
| Injuries | **3** | **1** | **Paraguay -2** ⚠️ |

#### Model Components

```
Component     Value    Weight    Contribution
elo           0.68     20%       0.136
xg            0.62     25%       0.155
form          0.46     15%       0.069
h2h           0.50     10%       0.050
injury        0.44     10%       0.044  ← Germany has 3 injuries!
─────────────────────────────────────────────
Weighted sum: 0.454
+ Home advantage: +0.05
= Home strength: 0.504 → Binary: [0.575, 0.425]
```

*Note: The auto-agent applied additional adjustments, resulting in the submitted [0.64, 0.36].*

#### What the Model Missed

**1. Injury impact was severely underestimated**

Germany had **3 key injuries** vs Paraguay's 1. The injury component only contributed **4.4%** to the final probability (weight = 10%). In reality, losing 3 starters in a knockout match is devastating. The model treated injuries as a minor factor, but they were likely the decisive factor.

**Suggested fix:** Consider increasing `WEIGHT_INJURIES` from 0.10 to **0.15–0.20**, or implement a non-linear injury penalty (e.g., exponential decay: 1 injury = small impact, 3+ injuries = massive impact).

**2. Paraguay's form advantage was ignored**

Paraguay's form [1,0,1,0,1] = 60% win rate was **better** than Germany's [1,0,0,1,-1] = 40%. However, the form component (weight 15%) was drowned out by Elo (20%) and xG (25%), which both heavily favored Germany based on historical data.

**Suggested fix:** In knockout matches, recent form may be more predictive than historical Elo. Consider a "knockout mode" that boosts form weight and reduces Elo weight for single-elimination matches.

**3. The match was a 1-1 draw — the model predicted 1-1 correctly!**

The model's most likely score was **1-1**, which was exactly the 90-minute result. The issue was that in knockout format, a draw goes to penalties, and the model's binary prediction [0.64, 0.36] assumed Germany would advance. Penalty shootouts are essentially **coin flips** (~50/50), so predicting the knockout winner from a drawn match is inherently uncertain.

**Key insight:** The model was actually **correct about the scoreline** but wrong about the knockout outcome because it couldn't account for penalty luck.

---

### Comparative Analysis: Why the Two Matches Differed

| Factor | m074 (✅) | m075 (❌) | Impact |
|--------|-----------|-----------|--------|
| Rank gap | #3 vs #16 (large) | #6 vs #28 (larger) | Favored Germany more → wrong |
| Form gap | Brazil +40% | Paraguay +20% | Model ignored Paraguay's form |
| Injury gap | 0 vs 0 (even) | 3 vs 1 (Germany disadvantaged) | Model underweighted injuries |
| Match went to penalties? | No | Yes | Unpredictable variance |
| Model confidence | 59% (moderate) | 64% (overconfident) | Higher confidence → bigger miss |

**The critical difference:** m074 was a straightforward match where the stronger team performed. m075 was an **upset** where the underdog (Paraguay) had better form and the favorite (Germany) was crippled by injuries — but the model's weights didn't reflect this.

---

### Recommendations for Model Improvement

1. **Increase injury weight for knockout matches**
   - Current: `WEIGHT_INJURIES = 0.10`
   - Proposed: `WEIGHT_INJURIES = 0.15` (or dynamic based on injury count)

2. **Implement non-linear injury penalty**
   - 0 injuries: no penalty
   - 1 injury: -2% strength
   - 2 injuries: -6% strength
   - 3+ injuries: -12% strength (exponential)

3. **Add a "knockout mode" that rebalances weights**
   - Elo: 20% → 15% (historical rank matters less in single-elimination)
   - Form: 15% → 20% (recent performance matters more)
   - Injury: 10% → 15% (squad availability is critical)

4. **Better handle drawn knockout matches**
   - When model predicts a draw (1-1, 0-0), acknowledge that knockout advancement is ~50/50
   - Cap confidence at 55% for predicted draws to avoid overconfidence

5. **Collect more data before adjusting weights**
   - Current sample: 2 matches
   - Minimum needed: 10-15 matches for statistically meaningful weight suggestions
   - Re-evaluate after Round of 16 completes

---

### Files Modified

- `logs/results.jsonl` — Added match results for m074, m075
- `logs/predictions.jsonl` — Added 29 new predictions for open matches
- `src/wc26_bnaul/batch_predict.py` — Updated TEAM_DB form and H2H for Brazil, Japan, Germany, Paraguay

---

### Next Steps

- [ ] Monitor m076–m078 (Netherlands vs Morocco, Ivory Coast vs Norway, France vs Sweden)
- [ ] After 10+ matches, re-run `suggest-weights` to get data-driven weight recommendations
- [ ] Consider implementing non-linear injury penalty in `ensemble_predictor.py`
- [ ] Evaluate whether a separate "knockout weight set" improves accuracy

---

*This analysis is part of our continuous learning loop: predict → observe → analyze → improve.*
