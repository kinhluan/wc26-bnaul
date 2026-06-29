# wc26-bnaul: A ClawCup Prediction Agent for FIFA World Cup 2026

> **Research Question:** How can an autonomous agent leverage probabilistic forecasting, external data integration, and real-time information monitoring to optimize performance in a strictly proper scoring rule prediction tournament?

---

## 1. Abstract

We present **wc26-bnaul**, an autonomous prediction agent designed for the [ClawCup](https://clawcup.io) FIFA World Cup 2026 forecasting tournament. The agent integrates a multi-factor prediction model (Elo rating, Poisson distribution, Monte Carlo simulation), external FIFA data feeds (football-data.org, API-Football), and automated news monitoring with HMAC-signed API communication. Through mathematical analysis and historical backtesting, we demonstrate that truthful probability calibration under the Brier score strictly proper scoring rule yields optimal expected returns, while information-advantage resubmission provides marginal but positive edge. The system is implemented as a Python CLI with modular components for strategy simulation, match analysis, and automated decision-making.

---

## 2. Project Overview

### 2.1 Problem Formulation

ClawCup is a non-monetary prediction tournament where agents submit probabilistic forecasts for FIFA World Cup 2026 matches. Scoring follows the **Brier score**:

$$BS = \frac{1}{N} \sum_{i=1}^{N} (p_i - o_i)^2$$

where $p_i$ is the submitted probability and $o_i \in \{0,1\}$ is the observed outcome. The Brier score is a **strictly proper scoring rule**, meaning the expected score is maximized iff the agent reports its true belief $\pi$ (Gneiting & Raftery, 2007).

### 2.2 Research Objectives

1. **Mathematical Proof:** Demonstrate that truthful submission is optimal under Brier scoring
2. **Empirical Validation:** Validate strategy through Monte Carlo simulation (10,000 runs)
3. **Information Edge:** Quantify the value of news monitoring and resubmission
4. **External Data Integration:** Leverage FIFA APIs to improve prediction accuracy
5. **Automation:** Build a fully autonomous agent for real-time tournament participation

---

## 3. System Architecture

```
wc26-bnaul/
├── src/wc26_bnaul/              # Core source modules
│   ├── __init__.py              # CLI agent (me, fixtures, predict, check)
│   ├── predictor.py             # Elo + Poisson + Monte Carlo prediction model
│   ├── fifa_data.py             # External API integration (football-data.org, API-Football)
│   ├── news_monitor.py          # News monitoring + auto-resubmit logic
│   ├── backtest.py              # Historical World Cup backtesting (45 matches)
│   ├── simulate.py              # Monte Carlo strategy simulation framework
│   ├── strategy.py              # Mathematical framework (Brier, Kelly, calibration)
│   ├── reasoning_analyzer.py    # Analysis of top agents' public reasonings
│   └── edge_finder.py           # Edge case and loophole analysis
├── docs/                         # Research documentation
│   ├── 00_OVERVIEW.md           # Project overview
│   ├── 01_STRATEGY.md           # Optimal strategy analysis
│   ├── 02_RESEARCH_DESIGN.md    # Research methodology
│   └── 03_BOOKMAKER_VALIDATION.md # Cross-validation with bookmaker industry
├── research/                     # Research artifacts
│   ├── BRAZIL_JAPAN_DETAILED.md      # Match analysis: Brazil vs Japan
│   ├── GERMANY_PARAGUAY_DETAILED.md  # Match analysis: Germany vs Paraguay
│   ├── NETHERLANDS_MOROCCO_DETAILED.md # Match analysis: Netherlands vs Morocco
│   ├── ARGENTINA_ITALY_ANALYSIS.md   # Match analysis: Argentina vs Italy
│   ├── FRANCE_SWEDEN_ANALYSIS.md     # Match analysis: France vs Sweden
│   ├── FIFA_DATA_SOURCES.md          # FIFA data API research
│   ├── FINDINGS.md                   # Key research findings
│   └── LESSONS_LEARNED.md            # Lessons and insights
├── tests/                        # Unit tests (25 tests)
│   ├── __init__.py
│   └── test_core.py             # Test suite: HMAC, strategy, predictor, credentials
├── pyproject.toml               # uv project configuration
├── uv.lock                      # Dependency lock file
├── .env                         # Environment variables (not in git)
├── .gitignore
└── README.md                    # This file
```

---

## 4. Quick Start

### 4.1 Prerequisites

- **Python** >= 3.12
- **uv** — the fast Python package manager ([install guide](https://docs.astral.sh/uv/getting-started/installation/))

### 4.2 Installation

```bash
# Clone repository
git clone https://github.com/kinhluan/wc26-bnaul.git
cd wc26-bnaul

# Create virtual environment and install dependencies
uv sync
```

### 4.3 Configuration

Create a `.env` file in the project root (or export variables):

```bash
# Required: ClawCup API credentials
CLAWCUP_TOKEN="wca_..."
CLAWCUP_SIGNING_SECRET="wca_sec_..."

# Optional: External data APIs
FOOTBALL_DATA_API_KEY="your_key"    # football-data.org
API_FOOTBALL_KEY="your_key"          # API-Football (RapidAPI)
```

> **Note:** The agent auto-loads `.env` at startup. No manual `source` needed.

---

## 5. CLI Usage (via `uv run`)

All commands are run through `uv run`, which uses the project's virtual environment automatically.

### 5.1 Agent Commands

```bash
# Agent info
uv run wc26-bnaul me

# List fixtures
uv run wc26-bnaul fixtures --status=open

# Submit prediction (group stage - 3-way)
uv run wc26-bnaul predict m001 \
  --prob 0.65 0.20 0.15 \
  --reasoning "Brazil 65% based on FIFA #6 vs #18..." \
  --score "2-1"

# Submit prediction (knockout - binary)
uv run wc26-bnaul predict m074 \
  --binary 0.88 0.12 \
  --reasoning "Brazil advance 88%..." \
  --score "2-0"

# Check all predictions
uv run wc26-bnaul check

# Fetch FIFA data
uv run wc26-bnaul fifa-data --source api-football --live
```

### 5.2 Model & Strategy Commands

```bash
# Run prediction model on a match
uv run wc26-bnaul predict-model BRAZIL JAPAN \
  --fifa-rank-home 6 --fifa-rank-away 18 \
  --form-home 4 --form-away 3

# Run strategy demonstration
uv run wc26-bnaul strategy-demo

# Run backtest demonstration
uv run wc26-bnaul backtest-demo
```

### 5.3 Development Commands

```bash
# Run tests
uv run pytest tests/

# Run specific test
uv run pytest tests/test_core.py -v

# Run news monitor (with FIFA data integration)
uv run python -m wc26_bnaul.news_monitor --fifa-data

# Run in dry-run mode (no actual API calls)
uv run python -m wc26_bnaul.news_monitor --dry-run
```

### 5.4 Alternative: `python -m`

If you prefer not to use the `wc26-bnaul` entry point:

```bash
# Ensure you're in the project root with uv environment activated
uv run python -m wc26_bnaul me
uv run python -m wc26_bnaul fixtures
uv run python -m wc26_bnaul check
```

> **Note:** `python3 -m wc26-bnaul` (with a hyphen) does **not** work because Python module names cannot contain hyphens. Use `python -m wc26_bnaul` (with underscore) or the `uv run wc26-bnaul` entry point.

---

## 6. Core Components

### 6.1 Prediction Model (`predictor.py`)

A multi-factor probabilistic model combining:

| Component | Method | Purpose |
|-----------|--------|---------|
| **Elo Rating** | Dynamic rating system | Team strength estimation |
| **Poisson Distribution** | $\lambda = \text{expected goals}$ | Goal scoring modeling |
| **Monte Carlo** | 10,000-run simulation | Probability validation |
| **Form Analysis** | Weighted recent results (last 5) | Momentum capture |
| **H2H History** | Historical match outcomes | Direct comparison |
| **Injury Adjustment** | Key player availability | Squad strength |

**Input features:** FIFA rank, recent form, head-to-head, goals scored/conceded, injuries, home advantage, knockout stage.

**Output:** 3-way probabilities (home win / draw / away win) with confidence score and expected goals.

### 6.2 FIFA Data Integration (`fifa_data.py`)

| API | Free Tier | Data Provided |
|-----|-----------|---------------|
| **football-data.org** | 12 competitions, 10 req/min | Fixtures, results, standings, scorers |
| **API-Football** | 100 req/day | Player stats, injuries, lineups, predictions, live scores |
| **FIFA Training Centre** | Free PDFs | EFI (Enhanced Football Intelligence) post-match |
| **StatsBomb Open Data** | GitHub dataset | Event-level data with xG (WC 2022) |

### 6.3 News Monitor (`news_monitor.py`)

Automated monitoring workflow:

1. **Pre-match scan:** Check for injuries, lineup changes, weather 30 min before cutoff
2. **Research file analysis:** Parse detailed match analysis documents
3. **FIFA data polling:** Query external APIs for real-time updates
4. **Resubmit decision:** Adjust probabilities if material information emerges
5. **HMAC-signed submission:** Secure API communication with ClawCup

### 6.4 Strategy Framework (`strategy.py`)

Mathematical foundations:

- **Brier Score:** $E[BS(p, \pi)] = p^2 - 2p\pi + \pi$ — minimized at $p = \pi$
- **Kelly Criterion:** $f^* = \frac{p(b+1) - 1}{b}$ — optimal bet sizing
- **Calibration:** Reliability diagrams and expected calibration error

---

## 7. Key Research Findings

### 7.1 Mathematical Results

| Finding | Evidence | Implication |
|---------|----------|-------------|
| **Truthful submission optimal** | Theorem + 10,000-run MC | Always report true belief $\pi$ |
| **Early rounds dominate** | Ro32 + Ro16 = 66.7% weight | Focus effort on initial rounds |
| **Resubmit value** | +0.4–0.8 pp per info level | Monitor news, resubmit on material changes |
| **Over-confidence punished** | Max-confident: -24.52% skill | Avoid extreme probabilities unless certain |
| **Bookmaker ≠ ClawCup** | Different incentive structures | Don't copy betting odds directly |

### 7.2 Empirical Validation

Monte Carlo simulation results (10,000 runs, 15 matches, 3 rounds):

| Strategy | Mean Skill % | Std Dev | 95% CI |
|----------|-------------|---------|--------|
| **Truthful** | **18.61%** | 11.2% | [0%, 40.6%] |
| Over-confident | 16.00% | 14.8% | [-13.0%, 45.0%] |
| Max-confident | **-24.52%** | 18.4% | [-60.6%, 11.6%] |

### 7.3 Historical Backtest

45 World Cup knockout matches (2014, 2018, 2022):

| Strategy | Mean Skill % | Notes |
|----------|-------------|-------|
| Over-confident | 39.22% | **Artifact:** Hindsight bias in estimated probabilities |
| Truthful | 23.52% | Lower but more realistic |
| Naive 50/50 | 0.00% | Baseline |

> **Caveat:** Over-confident beats truthful in backtest due to hindsight bias — the "true" probabilities used were actually post-hoc estimates, not pre-match beliefs.

---

## 8. Documentation

| Document | Content |
|----------|---------|
| [docs/00_OVERVIEW.md](docs/00_OVERVIEW.md) | Project overview and architecture |
| [docs/01_STRATEGY.md](docs/01_STRATEGY.md) | Optimal strategy: mathematical proof and simulation |
| [docs/02_RESEARCH_DESIGN.md](docs/02_RESEARCH_DESIGN.md) | Research methodology: MC design, baselines, metrics |
| [docs/03_BOOKMAKER_VALIDATION.md](docs/03_BOOKMAKER_VALIDATION.md) | Cross-validation with bookmaker industry |
| [research/FIFA_DATA_SOURCES.md](research/FIFA_DATA_SOURCES.md) | FIFA data API research and recommendations |
| [research/FINDINGS.md](research/FINDINGS.md) | Consolidated research findings |
| [research/LESSONS_LEARNED.md](research/LESSONS_LEARNED.md) | Insights and lessons from development |

---

## 9. Research Methodology

### 9.1 Experimental Design

We follow the **MLOps experimental protocol** (Sculley et al., 2015) adapted for prediction tournaments:

1. **Hypothesis:** Truthful probability calibration maximizes expected Brier score
2. **Baselines:** Truthful, over-confident, max-confident, naive 50/50
3. **Metrics:** Mean skill percentage, standard deviation, 95% confidence interval
4. **Validation:** 10,000-run Monte Carlo with bootstrapped confidence intervals

### 9.2 Data Sources

| Source | Type | Coverage | License |
|--------|------|----------|---------|
| FIFA World Cup 2022 | Historical results | 64 matches | Public |
| FIFA World Cup 2018 | Historical results | 64 matches | Public |
| FIFA World Cup 2014 | Historical results | 64 matches | Public |
| StatsBomb Open Data | Event-level + xG | WC 2022 | CC BY 4.0 |
| API-Football | Real-time API | 1,200+ leagues | Commercial |

### 9.3 Limitations

1. **Hindsight bias in backtest:** Historical "true" probabilities are post-hoc estimates
2. **External API dependency:** Real-time data requires paid API keys for production use
3. **News monitoring placeholder:** Real news APIs (NewsAPI, Twitter/X) not yet integrated
4. **Team ID mapping:** FIFA API team IDs need manual mapping to ClawCup team names

---

## 10. Future Work

1. **Weight Calibration:** Grid search optimal weights on historical data
2. **Live Model:** Real-time prediction adjustment during matches
3. **Ensemble Methods:** Combine multiple prediction models (Elo, xG, betting odds)
4. **NLP Integration:** Parse news articles and social media for sentiment analysis
5. **Transfer Learning:** Apply model to other prediction tournaments (Euro, Champions League)

---

## 11. Citation

If you use this project for research, please cite:

```bibtex
@misc{wc26-bnaul,
  title={wc26-bnaul: An Autonomous Prediction Agent for FIFA World Cup 2026},
  author={Bùi, Huỳnh Kinh Luân},
  year={2026},
  url={https://github.com/kinhluan/wc26-bnaul}
}
```

### Key References

- Gneiting, T., & Raftery, A. E. (2007). Strictly proper scoring rules, prediction, and estimation. *Journal of the American Statistical Association*, 102(477), 359-378.
- Tetlock, P. E., & Gardner, D. (2015). *Superforecasting: The Art and Science of Prediction*. Crown Publishers.
- Kelly, J. L. (1956). A new interpretation of information rate. *Bell System Technical Journal*, 35(4), 917-926.
- Sculley, D., et al. (2015). Hidden technical debt in machine learning systems. *NeurIPS*.

---

## 12. License

**MIT License** — For educational and research purposes.

> **Disclaimer:** ClawCup is a non-monetary prediction tournament. This project is not gambling, betting, or financial advice. The agent participates in a skill-based forecasting competition for academic and entertainment purposes.

---

*Built with scientific rigor, mathematical precision, and a passion for football.*
*Agent: wc26-bnaul | Tournament: FIFA World Cup 2026 | Platform: ClawCup*
