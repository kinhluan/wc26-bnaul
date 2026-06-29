# ClawCup FIFA World Cup 2026 — Research Findings

Tổng hợp các phát hiện nghiên cứu từ dự án wc26-bnaul.

---

## 1. Optimal Strategy (Đã được chứng minh)

### 1.1 Mathematical Proof

**Brier Score là Strictly Proper Scoring Rule:**

```
E[Brier] = π(p - 1)² + (1 - π)p²
         = p² - 2πp + π

Đạo hàm theo p:
d/dp E[Brier] = 2p - 2π = 0
→ p = π (true probability)

Minimum expected Brier: π(1 - π)
```

**Source:** Gneiting & Raftery (2007), 8,317 citations. Berkeley Statistics, TUM Munich.

### 1.2 Monte Carlo Validation (10,000 runs)

| Strategy | Mean Skill% | vs Truthful |
|----------|------------|-------------|
| **Truthful** | **18.61%** | baseline ✅ |
| Over-confident | 16.00% | -2.61% ❌ |
| Max-confident | **-24.52%** | **-43.13%** ❌❌ |
| Random | -32.41% | -51.01% ❌❌ |

**Conclusion:** Truthful submission optimal. Over-confidence catastrophic.

---

## 2. Round Weight Analysis

| Round | Matches | Weight | Contribution |
|-------|---------|--------|-------------|
| Ro32 | 16 | 1× | **41.0%** |
| Ro16 | 8 | 1.25× | **25.6%** |
| QF | 4 | 1.5× | 15.4% |
| SF | 2 | 2× | 10.3% |
| Final | 1 | 3× | 7.7% |

**Key Insight:** Ro32 + Ro16 = **66.7%** total weight. Early rounds matter most.

---

## 3. Resubmit Value

| Info Quality | Skill% Gain |
|-------------|------------|
| 30% | +0.06% |
| 50% | **+0.36%** |
| 70% | **+0.44%** |
| 100% | **+0.78%** |

**Linear relationship:** More info → more value from resubmit.

---

## 4. Edge Cases (8 Found)

| # | Edge | Severity | Actionable |
|---|------|----------|------------|
| 1 | Resubmit Info Advantage | Medium | ✅ Implement news monitoring |
| 2 | Group Stage Calibration | Low | ✅ Use as sandbox |
| 3 | Volume vs Precision | Low | ✅ Predict all matches |
| 4 | Late Round Weight | Low | ✅ Balance effort |
| 5 | Scoreline Disconnect | Info | ❌ No exploit |
| 6 | Provisional Gaming | Info | ❌ No exploit |
| 7 | Reasoning Pattern Analysis | Low | ✅ Learn from top agents |
| 8 | Signing Protection | Info | ❌ Security feature |

---

## 5. Historical Backtest Caveats

**Dataset:** 45 matches (2014, 2018, 2022)

**Surprising result:** Over-confident beat truthful (39.22% vs 23.52%)

**Why:**
- Hindsight bias in estimated probabilities
- Small sample → high variance
- Many favorites won → over-confidence "lucky"

**Lesson:** Historical backtest ≠ future performance. True probabilities unknowable ex-ante.

---

## 6. Bookmaker vs ClawCup

| Aspect | Bookmaker | ClawCup |
|--------|-----------|---------|
| Incentive | Profit margin | Calibration accuracy |
| Optimal strategy | True prob + margin | True prob (no margin) |
| Over-confidence | Irrelevant | Severely punished |
| Scoring | Payout odds | Brier/RPS |

**Key Insight:** Two different games with different optimal strategies.

---

## 7. Academic Foundations

### Papers

| Paper | Author | Citations | Relevance |
|-------|--------|-----------|-----------|
| Strictly Proper Scoring Rules | Gneiting & Raftery | 8,317 | Core proof |
| IARPA ACE Tournament | Tetlock et al. | — | Real-world validation |
| Superforecasting | Tetlock | — | Human forecasting |
| Forecaster Evaluation | Merkle | 1 | Model-based scoring |
| Agentic Forecasting | Hsieh et al. | — | AI forecasting |
| Foresight Learning | Turtel et al. | — | RL + proper scoring |

### Industry Sources

| Source | Type | Insight |
|--------|------|---------|
| GammaStack | Bookmaker tech | Overround mechanics |
| Sports-AI.dev | AI betting | Miscalibration effects |
| MetricGate | ML metrics | Proper scoring rules |
| MyBookie | Sportsbook | Vig explanation |

---

## 8. Tools Built

| Tool | File | Status |
|------|------|--------|
| CLI Agent | `src/wc26_bnaul/__init__.py` | ✅ Working |
| Auto Predict | `src/wc26_bnaul/auto_predict.py` | ✅ Working |
| News Monitor | `src/wc26_bnaul/news_monitor.py` | ⚠️ Placeholder |
| Backtest | `src/wc26_bnaul/backtest.py` | ✅ Working |
| Reasoning Analyzer | `src/wc26_bnaul/reasoning_analyzer.py` | ⚠️ Placeholder |
| Simulator | `src/wc26_bnaul/simulate.py` | ✅ Working |
| Strategy Math | `src/wc26_bnaul/strategy.py` | ✅ Working |
| Edge Finder | `src/wc26_bnaul/edge_finder.py` | ✅ Working |

---

## 9. Recommendations for Future Work

1. **Integrate real news APIs** (NewsAPI, RSS, Twitter/X)
2. **Expand historical dataset** (2010, 2006, 2002, 1998...)
3. **Write unit tests** for all modules
4. **Monitor actual ClawCup results** and compare
5. **Publish findings** — blog post or paper

---

*Generated: 2026-06-29*
*Repository: https://github.com/kinhluan/wc26-bnaul*
