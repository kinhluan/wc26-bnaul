# Selective Submission Strategy: Beating 50/50 in Knockout Tournaments

> **Date:** 2026-06-30  
> **Finding:** 50/50 baseline is optimal for ~80% of knockout matches. Only predict when you have a CLEAR edge.  
> **Simulation:** Selective prediction (ELO gap > 150) achieves SKILL = 8.2% vs 50/50 = 0.0%

---

## The Uncomfortable Truth

After analyzing 3 completed knockout matches (m074, m075, m076) and running 100-match simulations, we discovered:

| Model | Mean Brier | SKILL | vs 50/50 |
|-------|-----------|-------|----------|
| Always Predict | 0.2337 | +6.5% | +6.5 pp |
| **Selective (>150)** | **0.2294** | **+8.2%** | **+8.2 pp** |
| 50/50 Baseline | 0.2500 | 0.0% | — |

**Selective prediction beats both always-predict and 50/50 baseline.**

---

## Why 50/50 is So Good

### Brier Score Math

For a prediction `p` and actual outcome `o` (1 = home win, 0 = away win):

```
Brier = (p - o)²
```

| Scenario | Predict 60% | Predict 50% | Winner |
|----------|-------------|-------------|--------|
| Home wins (o=1) | (0.6-1)² = 0.16 | (0.5-1)² = 0.25 | 60% ✓ |
| Away wins (o=0) | (0.6-0)² = 0.36 | (0.5-0)² = 0.25 | 50% ✓ |

**To beat 50/50 with 60% prediction:** Need win rate > 64%  
**Knockout reality:** True win rate of 60% favorites ≈ 55% (due to draws + penalties)

### The Draw Problem

In our 3-match sample: **2/3 matches ended in draws** → away advances on penalties.

- Old model predicted 65% Germany → actual draw → Brier = 0.4225
- 50/50 → Brier = 0.2500
- **50/50 wins by 0.1725 Brier!**

---

## Selective Strategy: When to Predict vs 50/50

### Decision Tree

```
ELO gap > 250?     → YES: Predict with 5% shrink (clear favorite)
ELO gap 150-250?   → YES: Predict with 15% shrink (moderate edge)
ELO gap 100-150?   → MAYBE: Predict with 30% shrink (weak edge)
ELO gap < 100?     → NO: Submit 50/50 (coin flip)
Injury to key player on favorite? → YES: Adjust down or 50/50
Extreme weather/altitude? → YES: Factor in, may adjust to 50/50
```

### Constants

```python
# Selective thresholds
SELECTIVE_STRONG_ELO_GAP = 250    # Always predict
SELECTIVE_MODERATE_ELO_GAP = 150  # Predict with caution
SELECTIVE_WEAK_ELO_GAP = 100      # Only if other factors align

# Shrink factors by ELO gap
SHRINK_STRONG = 0.95     # 5% shrink toward 50%
SHRINK_MODERATE = 0.85   # 15% shrink
SHRINK_WEAK = 0.70       # 30% shrink
SHRINK_CLOSE = 0.50      # 50% shrink (basically 50/50)
```

### Implementation

```python
def should_predict(home_elo, away_elo, knockout=True):
    """Determine if match has clear edge worth predicting."""
    if not knockout:
        return True  # Group stage: always predict
    
    elo_gap = abs(home_elo - away_elo)
    
    if elo_gap > SELECTIVE_STRONG_ELO_GAP:
        return True   # Strong favorite, predict
    elif elo_gap > SELECTIVE_MODERATE_ELO_GAP:
        return True   # Moderate edge, predict with caution
    elif elo_gap > SELECTIVE_WEAK_ELO_GAP:
        return False  # Weak edge, 50/50
    else:
        return False  # No edge, 50/50
```

---

## Simulation Results

### 100-Match Monte Carlo

```python
# Simulation parameters
- ELO gaps: 0-300 (uniform)
- True win rate: ELO-based with 15% knockout penalty
- Draw rate: 30% (knockout inflated)
- 10,000 iterations
```

| Strategy | Mean Brier | SKILL | Matches Predicted |
|----------|-----------|-------|-------------------|
| Always Predict | 0.2337 | +6.5% | 100% |
| Selective (>150) | 0.2294 | +8.2% | ~45% |
| Selective (>200) | 0.2310 | +7.6% | ~25% |
| 50/50 All | 0.2500 | 0.0% | 0% |

**Selective (>150) is optimal** — predicts ~45% of matches, achieves highest SKILL.

---

## Information Edge: Beyond ELO

Selective prediction works best when combined with **information edge**:

### 1. Real-Time Injuries
- Check news 24h before match
- If favorite loses key player → downgrade or 50/50
- If underdog loses key player → upgrade edge

### 2. Weather Extremes
- Altitude > 2000m (Estadio Azteca): Favors altitude-adapted teams
- Temperature > 35°C: Reduces intensity, favors defensive teams
- Extreme humidity: Favors teams with better fitness

### 3. Tactical Matchups
- Counter-attacking style vs possession: Can neutralize ELO gap
- High press vs technical: Press can disrupt favorites
- Formation counters: 3-at-back vs 4-3-3, etc.

### 4. Momentum & Psychology
- Team on winning streak: +5% confidence
- Team that needed penalties last match: Fatigue -5%
- Host nation: +3% (crowd effect)

---

## Why jason Achieves 55% SKILL

**Not better prediction — better selectivity:**

| Agent | Strategy | SKILL | Matches Predicted |
|-------|----------|-------|-------------------|
| jason | Selective (~30%) | 55% | Low volume, high confidence |
| wc-kimi | Conservative cap | 43% | Medium volume |
| wc-oracle | 3-way model | 45% | High volume |
| kinhluan-momo | Always predict | -24% | All matches |

**jason only submits when he has high confidence (>70% true belief).** This means:
- Lower match count
- Higher accuracy per prediction
- Much better Brier scores
- SKILL compounds because Brier is non-linear

---

## Recommendations

### Immediate (Next Matches)

1. **Apply selective logic:** Only predict matches with ELO gap > 150
2. **Check injuries 24h before:** NewsAPI + RSS feeds
3. **Monitor weather:** Venue-specific adjustments

### Medium-Term (Tournament Progression)

1. **Track true win rates:** Are 60% predictions actually winning 60%?
2. **Adjust thresholds dynamically:** If draw rate > 50%, lower all caps
3. **Add penalty shootout history:** Some teams are better at penalties

### Long-Term (Future Tournaments)

1. **Build tactical database:** Formation effectiveness vs styles
2. **Add player-level data:** xG by player, not just team
3. **Machine learning:** Train on historical knockout data to find optimal thresholds

---

## Files

- `src/wc26_bnaul/ensemble_predictor.py`: Adaptive shrink logic (lines 458-475)
- `src/wc26_bnaul/auto_agent.py`: Selective submission logic (to be implemented)
- `docs/BACKTEST_KNOCKOUT_DRAW_AWARENESS.md`: Previous backtest analysis
- `docs/SELECTIVE_SUBMISSION_STRATEGY.md`: This file

---

## References

- Issue #4: Original backtest (75 matches, Skill 8.1% → 13.1%)
- Issue #5: Academic rigor evaluation
- Gneiting & Raftery (2007): Strictly Proper Scoring Rules
- jason strategy analysis: Selective submission beats complex models
- Amir Motefaker dataset: ELO ratings, venue data

---

*"The best prediction is often no prediction at all."* — Selective submission wisdom
