# wc26-bnaul — ClawCup Agent for FIFA World Cup 2026

AI agent dự đoán FIFA World Cup 2026 qua nền tảng [ClawCup](https://clawcup.io).

## 🏗️ Project Structure

```
wc26-bnaul/
├── src/wc26_bnaul/          # Source code
│   ├── __init__.py          # CLI agent chính (me, fixtures, predict, mine)
│   ├── auto_predict.py      # Auto-predict Round of 16+
│   ├── news_monitor.py      # News monitoring + auto-resubmit
│   ├── backtest.py          # Historical World Cup backtest
│   ├── reasoning_analyzer.py # Analyze top agents' public reasonings
│   ├── simulate.py          # Monte Carlo strategy simulation
│   ├── strategy.py          # Mathematical framework (Brier, Kelly)
│   └── edge_finder.py       # Edge case & loophole analysis
├── docs/                     # Documentation
│   ├── 00_OVERVIEW.md       # Tổng quan dự án
│   ├── 01_STRATEGY.md       # Chiến thuật tối ưu
│   ├── 02_RESEARCH_DESIGN.md # Thiết kế nghiên cứu
│   └── 03_BOOKMAKER_VALIDATION.md # Cross-validation với nhà cái
├── research/                 # Research artifacts
│   ├── papers/              # Academic papers & references
│   ├── experiments/         # Experiment logs & results
│   └── findings/            # Key findings & insights
├── tests/                    # Unit tests
├── pyproject.toml           # uv project config
└── uv.lock                  # Dependency lock
```

## 🚀 Quick Start

```bash
# Clone repo
git clone https://github.com/kinhluan/wc26-bnaul.git
cd wc26-bnaul

# Setup with uv
uv sync

# Configure environment
export CLAWCUP_TOKEN="wca_..."
export CLAWCUP_SIGNING_SECRET="wca_sec_..."

# Run CLI
uv run python -m wc26_bnaul me
uv run python -m wc26_bnaul fixtures
uv run python -m wc26_bnaul predict m001 --pick HOME --reasoning "..."
```

## 📊 What We Built

| Component | File | Purpose |
|-----------|------|---------|
| **CLI Agent** | `__init__.py` | Core ClawCup API client with HMAC signing |
| **Auto Predict** | `auto_predict.py` | Auto-generate predictions for upcoming rounds |
| **News Monitor** | `news_monitor.py` | Monitor news & auto-resubmit before cutoff |
| **Backtest** | `backtest.py` | Test strategies on historical World Cup data |
| **Reasoning Analyzer** | `reasoning_analyzer.py` | Analyze top agents' public reasonings |
| **Simulator** | `simulate.py` | Monte Carlo validation of optimal strategy |
| **Strategy Math** | `strategy.py` | Brier score, Kelly criterion, calibration |
| **Edge Finder** | `edge_finder.py` | 8 edge cases analyzed |

## 🎯 Key Findings

1. **Truthful submission optimal** — Brier score is strictly proper scoring rule (proven mathematically + 10,000-run MC)
2. **Early rounds matter most** — Ro32+Ro16 = 66.7% of total weight
3. **Resubmit has value** — +0.4-0.8pp per info quality level
4. **Over-confidence punished** — Max confident worse than naive 50/50!
5. **Bookmaker ≠ ClawCup** — Different games, different optimal strategies

## 📚 Documentation

- [docs/01_STRATEGY.md](docs/01_STRATEGY.md) — Chiến thuật tối ưu chi tiết
- [docs/02_RESEARCH_DESIGN.md](docs/02_RESEARCH_DESIGN.md) — Thiết kế nghiên cứu
- [docs/03_BOOKMAKER_VALIDATION.md](docs/03_BOOKMAKER_VALIDATION.md) — Cross-validation

## 📝 License

MIT — For educational purposes. ClawCup is non-monetary, not betting.
