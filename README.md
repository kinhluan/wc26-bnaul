# wc26-bnaul: Autonomous Prediction Agent for FIFA World Cup 2026

> **Rank #1 on ClawCup.io knockout leaderboard (Provisional)**
> A robust, dual-layer (Quantitative Ensemble + Qualitative LLM) autonomous prediction agent designed for strictly proper scoring rule competitions (Brier Score).

---

## 📑 Table of Contents (Index)
1. [Abstract & Research Question](#1-abstract--research-question)
2. [Dual-Layer Architecture](#2-dual-layer-architecture)
   - [2.1 Quantitative Layer (Ensemble Model)](#21-quantitative-layer-ensemble-model)
   - [2.2 Qualitative Layer (LLM / Human-in-the-loop)](#22-qualitative-layer-llm--human-in-the-loop)
3. [Data Ingestion & Big Data Management](#3-data-ingestion--big-data-management)
4. [Mathematical Framework: Brier Score Optimization](#4-mathematical-framework-brier-score-optimization)
5. [Codebase Structure](#5-codebase-structure)
6. [Quick Start & CLI Usage](#6-quick-start--cli-usage)
7. [Backtest Results & Competitor Analysis](#7-backtest-results--competitor-analysis)
8. [References & Citation](#8-references--citation)

---

## 1. Abstract & Research Question

**Research Question:** *How can an autonomous agent leverage probabilistic forecasting, flat JSON data integration, Large Language Models (LLM), and strict risk management to optimize expected performance under a Brier scoring rule in sports prediction?*

**wc26-bnaul** solves this by decoupling the prediction into a mathematical baseline (Elo, xG, Form, Squad Value) and a dynamic NLP layer (Kimi/ChatGPT) that detects "the edge" from unstructured text (injuries, coaching news, betting market drift). This dual approach effectively mitigates LLM hallucinations while maximizing prediction accuracy.

---

## 2. Dual-Layer Architecture

### 2.1 Quantitative Layer (Ensemble Model)
The baseline probability is calculated mathematically in `ensemble_predictor.py` using calibrated weights:
- **Elo Rating (30%)**: Dynamic historical performance.
- **Expected Goals - xG (20%)**: Core attacking/defensive metric.
- **Recent Form (15%)**: Exponential decay weighted performance in last 5 matches.
- **Betting Market (10%)**: Implied probability from bookmakers (Wisdom of Crowds).
- **Head-to-Head (5%)**: Historical matchup bias.
- **Injuries (5%)**: Direct mathematical deduction based on absent key players.
- **Squad Depth (5%)**: Market value normalization (e.g., Transfermarkt Euro valuation).

### 2.2 Qualitative Layer (LLM / Human-in-the-loop)
The system injects JSON-structured match context into a Large Language Model (via CLI `--ask-kimi` or API). The LLM acts as an **expert qualitative approver**, outputting a marginal adjustment (e.g., `-2.5%` or `+1.5%`) to account for variables the rigid math cannot see (e.g., *squad morale, weather, unquantifiable tactical shifts*).

---

## 3. Data Ingestion & Big Data Management

The database architecture has been fully decoupled from the source code, utilizing lightweight, flat JSON databases managed by `json_db.py`:
- `data/teams_db.json`: Core team metrics, historical xG, and squad values.
- `data/matches_db.json`: Real-time tracking of match states and scores.
- `data/betting_db.json`: Live bookmaker odds.
- `data/referees_db.json`: Umpire strictness metrics.

**Advanced Analytics Script:** 
The script `scripts/fetch_advanced_stats.py` automatically fetches raw datasets (like `dcaribou/transfermarkt-datasets` on GitHub/Kaggle) and updates `teams_db.json` dynamically with normalized Squad Depth scores.

---

## 4. Mathematical Framework: Brier Score Optimization

Brier score is a **strictly proper scoring rule**. Expected score is mathematically proven to be maximized if and only if you report your true belief.

$$E[\text{Brier}] = \pi(p-1)^2 + (1-\pi)p^2$$
$$\frac{d}{dp} E[\text{Brier}] = 2p - 2\pi = 0 \implies \boxed{p = \pi \text{ (optimal)}}$$

However, in Knockout formats (penalty shootouts), variance skyrockets. The agent utilizes **Risk-Averse Mechanics**:
1. **Selectivity (50/50 Threshold):** If Elo gap < 150, the model refuses to risk points and submits a mathematically safe `50/50`.
2. **Knockout Confidence Cap:** Strict ceiling of `65%`. Submitting 85% and losing on penalties yields a devastating `0.7225` penalty. Submitting `65%` acts as defensive armor.
3. **Draw Awareness:** Brier scoring for knockout draws ignores extra-time. The `prediction_logger.py` cleanly separates binary advancing status to calculate accurate backtesting.

---

## 5. Codebase Structure

```text
wc26-bnaul/
├── data/                    # JSON Databases (teams_db, matches_db, betting_db)
├── src/wc26_bnaul/          
│   ├── __init__.py          # Entry point & CLI router
│   ├── auto_agent.py        # Central Hub: LLM prompting & pipeline coordination
│   ├── ensemble_predictor.py# Core Math & Probability Engine
│   ├── json_db.py           # I/O handler for JSON databases
│   ├── prediction_logger.py # Brier backtesting & component analytics
├── scripts/                 
│   └── fetch_advanced_stats.py # Big Data ingestion (Transfermarkt/FBref)
├── wc26.sh                  # Shell wrapper for fast execution
└── README.md                # This document
```

---

## 6. Quick Start & CLI Usage

**Installation:**
```bash
git clone https://github.com/kinhluan/wc26-bnaul.git && cd wc26-bnaul
uv sync
```

**Interactive Human-in-the-loop Prediction:**
Generates a prompt payload, pauses for your LLM (Kimi/ChatGPT) analysis, and applies the adjustment.
```bash
./wc26.sh auto-agent --match m080 --ask-kimi
```

**Automated Pipeline:**
```bash
# Auto-predict all open matches based on Math Ensemble
./wc26.sh auto-agent

# Backtest performance & Auto-calibrate Weights
./wc26.sh performance
```

---

## 7. Backtest Results & Competitor Analysis

**Backtest (75 matches):**
| Metric | Baseline | Optimized Architecture | Δ |
|--------|----------|------------------------|---|
| Mean Brier | 0.2297 | **0.2174** | -5.4% |
| Skill % | 8.1% | **13.1%** | +5.0pp |

**Market Strategy:** 
The bot frequently deviates from public betting markets (e.g., submitting 57% when the market says 75%). This is an intended feature to avoid the *Underdog Upset Devastation* mathematically inherent to quadratic scoring rules.

---

## 8. References & Citation

```bibtex
@misc{wc26-bnaul,
  title={wc26-bnaul: An Autonomous Prediction Agent for FIFA World Cup 2026},
  author={Bùi, Huỳnh Kinh Luân},
  year={2026},
  url={https://github.com/kinhluan/wc26-bnaul}
}
```
- Gneiting & Raftery (2007). Strictly proper scoring rules, prediction, and estimation. *Journal of the American Statistical Association*, 102(477), 359-378.
- Tetlock & Gardner (2015). *Superforecasting: The Art and Science of Prediction*. Crown Publishers.

---
*Built with scientific rigor, mathematical precision, and an academic approach to football analytics.*
