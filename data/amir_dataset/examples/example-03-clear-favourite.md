# Example 3 — Clear Favourite Scenario
## Senegal 🇸🇳 vs Iraq 🇮🇶

> Demonstrates: large TSI gap, LOW upset risk classification, neutral venue conditions

---

### Input Command

```bash
python api/predictor.py --team-a Senegal --team-b Iraq --venue BOS --stage group --rest-a 6 --rest-b 6
```

### Match Context

| | Senegal | Iraq |
|---|---|---|
| FIFA Rank | 14 | 56 |
| ELO Rating | 1939 | 1765 |
| xG For (avg) | 1.68 | 1.12 |
| xG Against (avg) | 1.09 | 1.32 |
| Form (last 5) | W D W W D | W D W D D |
| Tactical Style | Physical pressing | Defensive counter |

**Venue:** Gillette Stadium, Foxborough — Sea level, 23°C, mild conditions

---

## 🏟️ MATCH PREVIEW
**Senegal vs Iraq** | Group Stage | Gillette Stadium, Foxborough

---

## 📊 TEAM STRENGTH ANALYSIS

| Metric | Senegal | Iraq |
|--------|---------|------|
| TSI Score | 67.22 | 34.05 |
| TSI Gap | 33.17 pts | |
| Favourite | Senegal | |

🟢 **Gap > 18 points → LOW UPSET RISK**

---

## 🎯 PREDICTION PROBABILITIES

```
Senegal WIN:   45.6%  █████████░
DRAW:          26.7%  █████░░░░░
Iraq WIN:      27.7%  █████░░░░░
```

**Expected Goals:** Senegal **1.47** — **1.10** Iraq

> Notice: even with a 33-point TSI gap, Senegal's win probability is only ~46%. This reflects football's inherent low-scoring variance — Poisson-distributed outcomes mean even heavy favourites draw or lose more often than in higher-scoring sports.

---

## 🔢 TOP SCORELINES (Monte Carlo, 10,000 sims)

| Scoreline | Probability |
|-----------|-------------|
| 1-1 | 12.92% |
| 1-0 | 11.32% |
| 2-1 | 9.70% |
| 0-1 | 8.42% |
| 2-0 | 8.09% |

---

## 📈 MARKET INDICATORS

- **Both Teams to Score:** 51.8%
- **Over 2.5 Goals:** 48.0%
- **Over 1.5 Goals:** 73.1%
- **Clean Sheet Senegal:** 33.1%
- **Clean Sheet Iraq:** 22.6%

---

## 🌍 ENVIRONMENTAL FACTORS

| Factor | Impact | Applied To |
|--------|--------|-----------|
| Altitude (26m, low) | None | — |
| Weather (23°C, mild) | None | — |
| Rest (both 6 days) | None — fully fresh | Both |

**Analyst Note:** Mild New England weather and full rest for both sides means this prediction is driven almost entirely by underlying squad quality (TSI gap of 33 points — one of the largest in the group stage). Senegal's physical pressing style should disrupt Iraq's defensive structure early, but Iraq's low block has historically frustrated stronger African sides. Senegal is the clear favourite, but a draw remains a live possibility — note that 1-1 is still the single most probable scoreline.

---

## ⚠️ UPSET RISK ASSESSMENT

**Upset Risk Level:** 🟢 LOW

**Risk Factors:**
- TSI gap of 33.17 points is well above the 18-point "low risk" threshold
- Senegal enters with stronger recent form (11 vs 9 form points)
- No environmental factors favour the underdog

---

## 🔮 FINAL VERDICT

> **Most Likely Outcome:** Senegal — 1-1 (most frequent scoreline) / Senegal favoured overall at 45.6%
> **Confidence Level:** MEDIUM
> **Data Quality:** ⭐⭐⭐⭐⭐ (5/5)

---

```
⚠️ This prediction is probabilistic, not deterministic.
Model version: WC2026-v2.0 | Engine: Bivariate Poisson + Monte Carlo 10K iterations
```
