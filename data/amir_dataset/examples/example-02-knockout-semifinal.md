# Example 2 — Semi-Final Knockout Match
## Argentina 🇦🇷 vs England 🏴󠁧󠁢󠁥󠁮󠁧󠁿

> Demonstrates: knockout stage modifiers, near-even matchups, LOW confidence handling

---

### Input Command

```bash
python api/predictor.py --team-a Argentina --team-b England --venue MET --stage semifinal --rest-a 5 --rest-b 4
```

### Match Context

| | Argentina | England |
|---|---|---|
| FIFA Rank | 3 | 4 |
| ELO Rating | 2031 | 2019 |
| xG For (avg) | 2.09 | 2.02 |
| xG Against (avg) | 0.95 | 0.91 |
| Form (last 5) | W W W W D | W W D W W |
| Formation | 4-2-3-1 | 4-3-3 |

**Venue:** MetLife Stadium, New Jersey — Sea level, 26°C, warm/humid

---

## 🏟️ MATCH PREVIEW
**Argentina vs England** | Semi-Final | MetLife Stadium, New Jersey

---

## 📊 TEAM STRENGTH ANALYSIS

| Metric | Argentina | England |
|--------|-----------|---------|
| TSI Score | 85.02 | 83.94 |
| TSI Gap | 1.08 pts | |
| Favourite | Argentina (marginal) | |

🔴 **Gap < 8 points → HIGH UPSET RISK** — this is essentially a coin-flip on paper

---

## 🎯 PREDICTION PROBABILITIES

```
Argentina WIN:  33.3%  ██████░░░░
DRAW:           33.4%  ██████░░░░
England WIN:    33.3%  ██████░░░░
```

**Expected Goals:** Argentina **1.19** — **1.19** England

> Note: Knockout stage modifier reduced goal expectancy by ~8% and added a draw probability bonus, reflecting the historically more cautious, risk-averse approach teams take in semi-finals.

---

## 🔢 TOP SCORELINES (Monte Carlo, 10,000 sims)

| Scoreline | Probability |
|-----------|-------------|
| 1-1 | 13.96% |
| 0-1 | 11.27% |
| 1-0 | 11.17% |
| 0-0 | 8.96% |
| 2-1 | 8.28% |

---

## 📈 MARKET INDICATORS

- **Both Teams to Score:** 48.7%
- **Over 2.5 Goals:** 42.8%
- **Over 1.5 Goals:** 69.0%
- **Clean Sheet Argentina:** 30.1%
- **Clean Sheet England:** 30.3%

---

## ⚔️ TACTICAL BREAKDOWN

**Formation Clash:** 4-2-3-1 (Argentina) vs 4-3-3 (England)

**Key Tactical Dynamics:**
1. Argentina's double pivot (De Paul/Mac Allister) vs England's front-three press — midfield control will be the deciding battleground
2. England's wide overloads (Saka/Foden) against Argentina's narrow back four could create the game's clearest chances
3. Both teams favor patient build-up — expect a slow first half with tempo increasing after 60'
4. Set-piece danger: Argentina ⭐⭐⭐⭐⭐⭐⭐/10 | England ⭐⭐⭐⭐⭐⭐⭐⭐/10

**Critical Individual Duel:**
> Messi vs Bellingham — the two most influential players on the pitch operating in overlapping zones between midfield and attack. Whoever's team controls this zone likely controls the game's tempo.

---

## ⚠️ UPSET RISK ASSESSMENT

**Upset Risk Level:** 🔴 HIGH

**Risk Factors:**
- TSI gap of just 1.08 points — statistically a dead heat
- Both teams equally rested at elite fitness levels
- Knockout pressure historically produces unpredictable results between closely-matched sides

---

## 🔮 FINAL VERDICT

> **Most Likely Outcome:** Draw — 1-1 (highest single-scoreline probability at 13.96%, though all three outcomes are statistically equal)
> **Confidence Level:** LOW
> **Data Quality:** ⭐⭐⭐⭐⭐ (5/5)

**Analyst Note:** This is the textbook definition of a 50/50 match — three-way probabilities within 0.1% of each other. The model's LOW confidence rating isn't a weakness here; it's an honest reflection of genuine uncertainty. Expect this game to be decided by individual moments of brilliance, set-pieces, or penalties rather than tactical superiority. If forced to pick, slight historical edge goes to Argentina's experience in high-stakes knockout football.

---

```
⚠️ This prediction is probabilistic, not deterministic.
Model version: WC2026-v2.0 | Engine: Bivariate Poisson + Monte Carlo 10K iterations
```
