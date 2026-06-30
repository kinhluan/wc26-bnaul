# Methodology — WC2026 AI Prediction Engine

This document explains the statistical and tactical methodology behind the prediction engine in technical detail.

---

## 1. Overview — The 6-Step Pipeline

```
┌─────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│ 1. TSI          │ → │ 2. Poisson xG     │ → │ 3. Monte Carlo   │
│ Team Strength   │   │ Model (λ_A, λ_B)  │   │ Simulation       │
└─────────────────┘   └──────────────────┘   └──────────────────┘
                                                        ↓
┌─────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│ 6. Confidence   │ ← │ 5. Contextual     │ ← │ 4. Tactical      │
│ Quantification  │   │ Modifiers         │   │ Overlay          │
└─────────────────┘   └──────────────────┘   └──────────────────┘
```

---

## 2. Team Strength Index (TSI)

**File:** `engine/tsi_calculator.py`

A composite 0–100 score combining six weighted, normalized components:

| Component | Weight | Source Field | Normalization |
|-----------|--------|--------------|----------------|
| FIFA Ranking | 20% | `fifa_rank` | Inverted min-max (1–90 range) |
| ELO Rating | 25% | `elo_rating` | Min-max (1650–2100 range) |
| xG For (avg) | 15% | `xg_for_avg` | Min-max (0.80–2.50 range) |
| xG Against (avg) | 15% | `xg_against_avg` | Inverted min-max (0.70–1.70 range) |
| Form Score | 15% | `form_score` | Min-max (0–15 range, W=3/D=1/L=0 × 5 games) |
| Squad Depth | 10% | `squad_depth_score` | Min-max (4.0–10.0 range) |

### Formula

```
TSI = 100 × Σ(weight_i × normalized_value_i)
```

### Why these bounds?
The min-max ranges are calibrated to the actual WC2026 field — e.g., FIFA ranks span from #1 (France) to ~#90 (lowest qualified team), and ELO ratings span ~1650–2100 across all 48 qualified nations. This ensures the TSI distribution uses the full 0–100 range meaningfully.

---

## 3. Expected Goals Model (Bivariate Poisson)

**File:** `engine/poisson_model.py`

### Base Lambda Calculation

For Team A facing Team B:

```
base_λ_A = √(xG_for_A × xG_against_B)
```

This geometric mean approach (similar to Dixon-Coles models) balances a team's attacking output against the opponent's defensive solidity.

### Modifiers Applied Multiplicatively

```
λ_A = base_λ_A × altitude_mod × rest_mod × weather_mod × stage_mod × host_mod
```

| Modifier | Trigger | Effect |
|----------|---------|--------|
| **Altitude** | Venue ≥ 2200m (extreme) | ×1.12 |
| | Venue 1500–2199m (high) | ×1.05 |
| | Venue 500–1499m (medium) | ×1.02 |
| | Venue < 500m (low) | ×1.00 |
| **Acclimatization** | Team's home altitude within 200m of venue | Negates altitude effect |
| | Team's home altitude within 800m of venue | Halves altitude effect |
| **Rest** | < 3 days since last match | ×0.90 |
| | 3–5 days | ×0.96 |
| | 6+ days | ×1.00 |
| **Weather** | Hot/humid venues (Miami, Houston, Monterrey) | ×0.94–0.96 |
| | Mild venues (Seattle, Vancouver, Boston) | ×1.00 |
| **Tournament Stage** | Group stage | ×1.00 |
| | Knockout rounds | ×0.91–0.96 (increasingly conservative) |
| **Host Nation** | USA / Canada / Mexico playing | ×1.08 |

A floor of **0.20** is applied to prevent λ from reaching zero (which would make Poisson sampling degenerate).

---

## 4. Monte Carlo Simulation

**File:** `engine/monte_carlo.py`

### Sampling Method
Uses **Knuth's algorithm** for Poisson-distributed random sampling:

```python
def poisson_sample(lam):
    L = exp(-lam)
    k = 0
    p = 1.0
    while p > L:
        k += 1
        p *= random()
    return k - 1
```

### Default Configuration
- **10,000 iterations** per match (configurable via `--sims`)
- **Fixed seed (2026)** by default for reproducibility — set `seed=None` for true randomness

### Outputs Derived
1. **Win/Draw/Loss probabilities** — direct frequency counts from simulations
2. **Top 10 scorelines** — most frequent (goals_a, goals_b) pairs
3. **Expected goals** — average goals scored across all simulations
4. **Market indicators** — computed *analytically* (not simulated) for precision:
   - Over 2.5 / Over 1.5: `1 - P(total goals ≤ 2 or ≤ 1)` using combined λ
   - BTTS: `(1 - P(0|λ_A)) × (1 - P(0|λ_B))`
   - Clean sheets: `P(0 | opponent's λ)`

### Draw Bonus Adjustment
For knockout stages, a `draw_bonus` (e.g., +5% for semifinals/finals) is applied post-simulation:
- Half the bonus is subtracted proportionally from each win probability
- The full bonus is added to the draw probability
- All three probabilities are renormalized to sum to 100%

This reflects the well-documented phenomenon of more cautious, risk-averse tactics in high-stakes knockout matches.

---

## 5. Tactical Overlay Analysis

This step is performed by the **GPT-4o layer** (via `system_prompt_v2.md`), not the Python engine, since it requires qualitative reasoning about:

- Formation matchups (e.g., 3-5-2 vs 4-3-3 wide overloads)
- Pressing intensity vs. build-up speed
- Set-piece threat assessment
- Identification of the single most decisive individual duel

The Python engine provides the **quantitative grounding** (TSI, λ values, probabilities) which GPT-4o uses as "ground truth" to anchor its tactical narrative — preventing hallucinated statistics.

---

## 6. Contextual & Psychological Modifiers

Applied at the GPT-4o reasoning layer using rules defined in the system prompt:

| Factor | Adjustment |
|--------|-----------|
| Knockout stage pressure | −8% goal expectancy, +5% draw probability (already baked into `STAGE_MODIFIERS`) |
| TSI gap < 8 | Flagged as HIGH UPSET RISK |
| H2H revenge factor | +3% win probability narrative emphasis |
| Recent manager change | −5% tactical cohesion (qualitative flag) |
| "Group of Death" fatigue | −7% xG narrative flag for tired teams |
| Host nation crowd | +5% psychological edge (on top of the +8% λ modifier) |

---

## 7. Confidence & Uncertainty Quantification

**Confidence Level** is determined by the maximum single-outcome probability:

| Max Outcome Probability | Confidence Level |
|--------------------------|-------------------|
| ≥ 55% | HIGH |
| 40% – 54.9% | MEDIUM |
| < 40% | LOW |

**Model Variance**: Since goals follow a Poisson distribution, the standard deviation equals `√λ`. This is reported as `std_goals_a` / `std_goals_b` to communicate the inherent unpredictability even when λ is precisely known.

**Data Quality Score** (1–5 stars) reflects completeness of input data — full marks require: FIFA rank, ELO, xG for/against, form, squad depth, formation, key players, rest days, and venue conditions all present.

---

## 8. Known Limitations

1. **Static xG averages** — real teams' attacking/defensive output varies by opponent quality; this model uses season-wide averages
2. **No live injury feed** — key absences must be manually provided via `--absence-a` / `--absence-b`
3. **No head-to-head history** — the `[COMPARE]` mode in the system prompt relies on GPT-4o's training knowledge, not a structured database
4. **Altitude acclimatization heuristic** — the 200m/800m thresholds are reasonable approximations, not derived from sports-science literature
5. **Fixed random seed** — default seed=2026 means repeated runs with identical inputs produce identical outputs; set `seed=None` for variance across runs

---

## 9. References & Inspiration

- Dixon, M.J. & Coles, S.G. (1997). "Modelling Association Football Scores and Inefficiencies in the Football Betting Market"
- FiveThirtyEight SPI (Soccer Power Index) methodology
- Opta xG modeling principles
- Knuth, D.E. "The Art of Computer Programming, Vol 2" — Poisson sampling algorithm

---

*For implementation details, see the source files in `engine/`. For the AI reasoning layer, see `system-prompt/system_prompt_v2.md`.*
