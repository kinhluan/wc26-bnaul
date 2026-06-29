# wc26-bnaul: ClawCup Agent for FIFA World Cup 2026

> Autonomous prediction agent with multi-factor modeling (Elo + Poisson + Monte Carlo), real-time FIFA data, and automated news monitoring.

**Research Question:** How can an autonomous agent leverage probabilistic forecasting, external data integration, and real-time information monitoring to optimize performance in a strictly proper scoring rule prediction tournament?

---

## Quick Start

```bash
# Clone & install
git clone https://github.com/kinhluan/wc26-bnaul.git && cd wc26-bnaul
uv sync

# Configure credentials
cp .env.example .env  # Edit with your tokens

# Play
./wc26.sh run m001     # Full pipeline: news → model → submit
./wc26.sh me           # Agent info
./wc26.sh fixtures     # List open matches
./wc26.sh monitor      # Auto news monitor (dry-run)
```

---

## What It Does

| Feature | Description |
|---------|-------------|
| **Multi-factor Model** | Elo rating + Poisson goals + Monte Carlo validation |
| **FIFA Data** | football-data.org + API-Football integration |
| **News Monitor** | NewsAPI + RSS feeds + injury tracking with auto-resubmit |
| **Math Proof** | Truthful submission optimal under Brier score (Gneiting & Raftery, 2007) |
| **CLI + Script** | `uv run` commands or `./wc26.sh` interactive menu |

**Key Insight:** Brier score is a strictly proper scoring rule — expected score is maximized iff you report your true belief. Over-confidence is punished.

---

## Project Structure

```
wc26-bnaul/
├── src/wc26_bnaul/          # Core modules
│   ├── __init__.py          # CLI agent (me, predict, check)
│   ├── predictor.py         # Elo + Poisson + Monte Carlo model
│   ├── fifa_data.py         # football-data.org + API-Football
│   ├── news_monitor_real.py # Real news + injury monitoring
│   ├── strategy.py          # Brier optimization framework
│   └── ...
├── docs/                     # Research docs
│   ├── 01_STRATEGY.md       # Optimal strategy analysis
│   ├── 02_RESEARCH_DESIGN.md # Experiment methodology
│   └── 03_BOOKMAKER_VALIDATION.md
├── research/                 # Match analyses & findings
├── tests/                    # 25 unit tests
├── wc26.sh                   # All-in-one control script
├── pyproject.toml           # uv configuration
└── README.md                # This file
```

---

## CLI Usage

### Agent Commands (Play the Game)

```bash
uv run wc26-bnaul me                          # Agent info
uv run wc26-bnaul fixtures --status=open      # List fixtures
uv run wc26-bnaul predict m001 \
  --prob 0.65 0.20 0.15 \
  --reasoning "Brazil 65% based on FIFA #6" \
  --score "2-1"                               # Submit prediction
uv run wc26-bnaul check                       # View predictions
uv run wc26-bnaul fifa-data --source api-football --live
```

### Full Pipeline (One Command)

```bash
./wc26.sh run m001   # 1. Fetch news → 2. Run model → 3. Prompt prob → 4. Submit
```

### Monitoring

```bash
./wc26.sh monitor         # Dry-run news monitor
./wc26.sh monitor-live    # Live auto-resubmit
uv run python -m wc26_bnaul.news_monitor_real --check m001 --dry-run
```

### Development

```bash
uv run pytest tests/              # Run tests
uv run wc26-bnaul strategy-demo    # Math proof demo
uv run wc26-bnaul backtest-demo    # Historical backtest
```

> **Note:** `python3 -m wc26-bnaul` (hyphen) doesn't work. Use `python -m wc26_bnaul` (underscore) or `uv run wc26-bnaul`.

---

## Core Components

### Prediction Model (`predictor.py`)

| Factor | Weight | Source |
|--------|--------|--------|
| FIFA Rank | 0.25 | football-data.org |
| Recent Form | 0.20 | API-Football |
| H2H History | 0.15 | API-Football |
| Goals | 0.20 | football-data.org |
| Injuries | 0.10 | API-Football |
| Home Advantage | 0.05 | Fixed |

### Strategy Framework (`strategy.py`)

```
E[Brier] = π(p-1)² + (1-π)p² = p² - 2πp + π
d/dp E[Brier] = 2p - 2π = 0 → p = π (optimal)
```

**Round weights:** Ro32 (1×) + Ro16 (1.25×) = **66.7%** of total weight.

### News Monitor (`news_monitor_real.py`)

| Source | Data | Key |
|--------|------|-----|
| NewsAPI | Real-time articles | `NEWSAPI_KEY` |
| RSS (BBC/ESPN/Goal) | News feeds | None |
| API-Football | Injuries, lineups | `API_FOOTBALL_KEY` |

---

## Key Results

| Strategy | Mean Skill% | vs Truthful |
|----------|-------------|-------------|
| **Truthful** | **18.61%** | baseline ✅ |
| Over-confident | 16.00% | -2.61% ❌ |
| Max-confident | **-24.52%** | **-43.13%** ❌ |

---

## Documentation

| Document | Content |
|----------|---------|
| [docs/01_STRATEGY.md](docs/01_STRATEGY.md) | Optimal strategy, edge cases, meta-strategy |
| [docs/02_RESEARCH_DESIGN.md](docs/02_RESEARCH_DESIGN.md) | Experiment design, baselines, metrics |
| [docs/03_BOOKMAKER_VALIDATION.md](docs/03_BOOKMAKER_VALIDATION.md) | Cross-validation with bookmaker industry |
| [research/FINDINGS.md](research/FINDINGS.md) | Consolidated findings |
| [research/LESSONS_LEARNED.md](research/LESSONS_LEARNED.md) | Development insights |

---

## Citation

```bibtex
@misc{wc26-bnaul,
  title={wc26-bnaul: An Autonomous Prediction Agent for FIFA World Cup 2026},
  author={Bùi, Huỳnh Kinh Luân},
  year={2026},
  url={https://github.com/kinhluan/wc26-bnaul}
}
```

**Key References:**
- Gneiting & Raftery (2007). Strictly proper scoring rules. *JASA*, 102(477), 359-378.
- Tetlock & Gardner (2015). *Superforecasting*. Crown Publishers.

---

**MIT License** — For educational and research purposes. Not gambling or financial advice.

*Built with scientific rigor, mathematical precision, and a passion for football.*
