# Example 1 — Group Stage Match
## Brazil 🇧🇷 vs Morocco 🇲🇦

> Demonstrates: high-altitude venue effects, group stage probabilities, upset risk detection

---

### Input Command

```bash
python api/predictor.py --team-a Brazil --team-b Morocco --venue AZT --stage group --rest-a 5 --rest-b 4
```

### Match Context

| | Brazil | Morocco |
|---|---|---|
| FIFA Rank | 6 | 8 |
| ELO Rating | 2008 | 1985 |
| xG For (avg) | 2.28 | 1.62 |
| xG Against (avg) | 1.02 | 0.88 |
| Form (last 5) | W W L W W | W W W D W |
| Formation | 4-2-3-1 | 4-3-3 |
| Tactical Style | Attacking flair | Low block counter |

**Venue:** Estadio Azteca, Mexico City — Altitude **2,200m** (extreme), 18°C

---

## 🏟️ MATCH PREVIEW
**Brazil vs Morocco** | Group Stage | Estadio Azteca, Mexico City

---

## 📊 TEAM STRENGTH ANALYSIS

| Metric | Brazil | Morocco |
|--------|--------|---------|
| TSI Score | 82.86 | 77.07 |
| TSI Gap | 5.79 pts | |
| Favourite | Brazil | |

⚠️ **Gap < 8 points → HIGH UPSET RISK**

---

## 🎯 PREDICTION PROBABILITIES

```
Brazil WIN:    41.4%  ████████░░
DRAW:          24.2%  █████░░░░░
Morocco WIN:   34.4%  ███████░░░
```

**Expected Goals:** Brazil **1.52** — **1.36** Morocco

---

## 🔢 TOP SCORELINES (Monte Carlo, 10,000 sims)

| Scoreline | Probability |
|-----------|-------------|
| 1-1 | 11.95% |
| 2-1 | 8.74% |
| 1-0 | 8.64% |
| 1-2 | 8.36% |
| 0-1 | 7.58% |

---

## 📈 MARKET INDICATORS

- **Both Teams to Score:** 58.6%
- **Over 2.5 Goals:** 55.5%
- **Over 1.5 Goals:** 78.6%
- **Clean Sheet Brazil:** 25.1%

---

## 🌍 ENVIRONMENTAL FACTORS

| Factor | Impact | Applied To |
|--------|--------|-----------|
| Altitude (2200m, extreme) | +12% xG variance | Both teams |
| Rest (Brazil: 5d, Morocco: 4d) | −4% xG | Both |
| Weather (18°C, mild highland) | Neutral | — |

**Analyst Note:** The extreme altitude of Estadio Azteca is the dominant factor here — both teams face the same ~12% xG variance increase, but Morocco's disciplined low-block style is historically well-suited to slower, higher-altitude conditions where pressing intensity drops. With a TSI gap under 8 points, this qualifies as a genuine toss-up despite Brazil's higher ranking. Expect a tight, cagey affair with set-pieces playing an outsized role.

---

## ⚠️ UPSET RISK ASSESSMENT

**Upset Risk Level:** 🔴 HIGH

**Risk Factors:**
- TSI gap of only 5.79 points (threshold: 8)
- Morocco's tactical style historically neutralizes higher-press teams
- Altitude reduces Brazil's high-tempo attacking advantage

---

## 🔮 FINAL VERDICT

> **Most Likely Outcome:** Brazil — 1-1 (most frequent simulated draw)
> **Confidence Level:** MEDIUM
> **Data Quality:** ⭐⭐⭐⭐⭐ (5/5)

---

```
⚠️ This prediction is probabilistic, not deterministic.
Model version: WC2026-v2.0 | Engine: Bivariate Poisson + Monte Carlo 10K iterations
```
