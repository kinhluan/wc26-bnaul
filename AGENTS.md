# AGENTS.md — wc26-bnaul

> **Updated:** 2026-07-01 after CLI mode refactor, advanced stats integration, and bug fixes.

---

## 1. Project Overview

**wc26-bnaul** is an autonomous prediction agent for the ClawCup tournament (FIFA World Cup 2026). The agent uses an ensemble model (xG + Elo + Form + H2H + Injury) to predict match outcomes and automatically submits via API.

**Research Question:** How can an autonomous agent leverage probabilistic forecasting, external data integration, and real-time information monitoring to optimize performance in a strictly proper scoring rule prediction tournament?

**Key Resources:**
- [Issue #1](https://github.com/kinhluan/wc26-bnaul/issues/1) — Match Analysis: m074 & m075 breakdown
- [Issue #2](https://github.com/kinhluan/wc26-bnaul/issues/2) — Ranking Improvement Plan: -16% to Top 3
- [Issue #3](https://github.com/kinhluan/wc26-bnaul/issues/3) — Research Synthesis: 15 papers on sports prediction
- [Issue #4](https://github.com/kinhluan/wc26-bnaul/issues/4) — Backtest Analysis: 75 matches, Skill 8.1% → 13.1%
- [Issue #5](https://github.com/kinhluan/wc26-bnaul/issues/5) — Experiment Evaluation: Academic rigor assessment (2.9/5)
- [Skill Memory](.agents/skills/wc26-bnaul/SKILL.md) — Compressed knowledge for future agents

---

## 2. First-Time Setup for New Agents

### 2.1 Prerequisites

- **Python 3.12+** with `uv` package manager
- **Git** for version control
- **API credentials** from ClawCup (see 2.2)

### 2.2 Get API Credentials

1. Go to https://clawcup.io and create an account
2. Navigate to your **Profile → API Keys**
3. Copy:
   - `CLAWCUP_TOKEN` (long alphanumeric string)
   - `CLAWCUP_SIGNING_SECRET` (used for request signing)

### 2.3 Create .env File

```bash
cd wc26-bnaul
cp .env.example .env  # If .env.example exists, or create manually:
```

Edit `.env` with your credentials:

```bash
CLAWCUP_TOKEN=your_token_here
CLAWCUP_SIGNING_SECRET=your_secret_here
NEWSAPI_KEY=your_newsapi_key_here          # Optional — for news monitoring
API_FOOTBALL_KEY=your_api_football_key     # Optional — for injury data
OPENAI_API_KEY=your_openai_key             # Optional — for auto LLM mode
KIMI_API_KEY=your_kimi_key                  # Optional — for Kimi API mode
```

> **Security:** Never commit `.env` to git. It's already in `.gitignore`.

### 2.4 Install Dependencies

```bash
uv sync
```

### 2.5 Verify Setup

```bash
# Check agent info
./wc26.sh me

# List open matches
./wc26.sh fixtures
```

If you see your agent info and a list of matches, setup is complete.

---

## 3. Architecture

```
Input (JSON DB) → Ensemble Model → Binary Prob → Submit → Log
                     ↑
              External Agent (CLI mode)
                     ↑
              News Monitor (RSS + NewsAPI)
```

### Components:
- **JSON DB Layer** (`json_db.py`): `data/teams_db.json`, `data/venues_db.json`, `data/advanced_stats.csv`
- **Ensemble Predictor** (`ensemble_predictor.py`): Elo(30%) + xG(20%) + Form(15%) + Betting(10%) + H2H(5%) + Squad Depth(5%) + Injury(15%)
- **Auto Agent** (`auto_agent.py`): Fully autonomous pipeline with CLI mode support
- **Prediction Logger** (`prediction_logger.py`): Log + performance tracking
- **Advanced Stats** (`scripts/fetch_advanced_stats.py`): CSV-based xG/xGA/possession management
- **News Monitor** (`news_monitor_real.py`): RSS feeds + NewsAPI (single query per match)

---

## 4. Key Files

| File | Purpose |
|------|---------|
| `src/wc26_bnaul/__init__.py` | CLI commands (me, fixtures, predict, check, mine) |
| `src/wc26_bnaul/ensemble_predictor.py` | Core prediction model |
| `src/wc26_bnaul/auto_agent.py` | Fully autonomous agent with CLI mode |
| `src/wc26_bnaul/batch_predict.py` | Batch predictions + JSON DB loader |
| `src/wc26_bnaul/prediction_logger.py` | Log predictions + performance |
| `src/wc26_bnaul/news_monitor_real.py` | News + injury monitoring (rate-limit safe) |
| `src/wc26_bnaul/json_db.py` | JSON data access layer |
| `scripts/fetch_advanced_stats.py` | CSV → JSON stats updater |
| `data/teams_db.json` | Team data (xG, Elo, form, injuries, etc.) |
| `data/advanced_stats.csv` | Editable CSV for xG/xGA/possession updates |
| `wc26.sh` | All-in-one control script |

---

## 5. Ensemble Model Weights

```python
# Updated after Issue #4 backtest analysis (2026-06-30):
WEIGHT_ELO = 0.30          # Strongest component (61.3% accuracy)
WEIGHT_FIFA = 0.10         # FIFA ranking
WEIGHT_XG = 0.20           # Expected goals (noisy but valuable)
WEIGHT_BETTING = 0.10      # Betting odds (when available)
WEIGHT_FORM = 0.15         # Recent form (surprisingly good: 62.7%)
WEIGHT_SQUAD_DEPTH = 0.05  # Market value / squad quality
WEIGHT_H2H = 0.05          # Head-to-head history
WEIGHT_INJURIES = 0.15     # Critical for knockouts
```

> ⚠️ **Weight sum must equal 1.0.** If you change weights, verify: `sum(weights) == 1.0`

---

## 6. CLI Agent Mode (For External LLM Agents)

### 6.1 What is CLI Mode?

CLI mode allows **any external LLM agent** (kimi-cli, claude-cli, custom scripts) to:
1. Read the full match context + prompt from stdout
2. Analyze and provide a probability adjustment
3. Pipe the adjustment back via stdin

### 6.2 How to Use CLI Mode

```bash
# Basic: print prompt, read adjustment from stdin
echo "ADJUSTMENT: -2.5" | ./wc26.sh auto-agent --match m080 --cli-mode --live

# Or interactively:
./wc26.sh auto-agent --match m080 --cli-mode --live
# (Paste prompt into your LLM, paste response back, press Ctrl+D)
```

### 6.3 Pipe Workflow (For Automated Agents)

```bash
# Step 1: Run agent in CLI mode, capture prompt
./wc26.sh auto-agent --match m080 --cli-mode --dry-run > prompt.txt

# Step 2: Send prompt to your LLM
# (Your agent reads prompt.txt, calls LLM API, gets adjustment)

# Step 3: Submit with adjustment
echo "ADJUSTMENT: -2.5" | ./wc26.sh auto-agent --match m080 --cli-mode --live
```

### 6.4 Expected Prompt Format

The agent prints a JSON-structured prompt containing:
- Match ID, teams, base probability
- Full team data (xG, Elo, form, injuries, etc.)
- Instructions for the LLM

Expected response format:
```
ADJUSTMENT: -2.5
```

Range: `-5.0` to `+5.0` (percentage points). Use `0.0` if no adjustment needed.

### 6.5 Alternative: Interactive Copy-Paste Mode

```bash
# For manual human-in-the-loop (any LLM: ChatGPT, Claude, Kimi)
./wc26.sh auto-agent --match m080 --ask-agent --live

# Deprecated alias (still works):
./wc26.sh auto-agent --match m080 --ask-kimi --live
```

---

## 7. Auto-Agent Usage

### 7.1 Fast Mode (Default — No LLM)

```bash
# Dry-run all open matches
./wc26.sh auto-agent

# Dry-run single match
./wc26.sh auto-agent --match m080

# Live submit (auto mode, no LLM confirmation)
./wc26.sh auto-agent --live
```

### 7.2 With News Check

```bash
./wc26.sh auto-agent --news       # Slower but more accurate
```

> ⚠️ **Critical:** Fast mode skips injury checks. Always use `--news` for live data.

### 7.3 With External LLM Agent (CLI Mode)

```bash
# Automated pipe workflow
echo "ADJUSTMENT: -2.5" | ./wc26.sh auto-agent --match m080 --cli-mode --live

# Interactive (manual copy-paste)
./wc26.sh auto-agent --match m080 --ask-agent --live
```

### 7.4 Selectivity Thresholds

| Model Confidence | Action |
|------------------|--------|
| < 48% or > 52% | Submit 50/50 (no clear edge) |
| 48-52% | Submit model output |
| > 65% in knockout | Cap at 65% (overconfidence penalty) |
| < 35% in knockout | Floor at 35% |

---

## 8. Advanced Stats Management

### 8.1 Update Stats from CSV

```bash
# Step 1: Export template from current teams_db.json
python3 scripts/fetch_advanced_stats.py --export-template

# Step 2: Edit data/advanced_stats.csv (Excel, Google Sheets, or VS Code)
# Fill in: xg, xga, possession, goals_scored, shots_per_game, etc.

# Step 3: Validate CSV format
python3 scripts/fetch_advanced_stats.py --validate

# Step 4: Preview changes (dry-run)
python3 scripts/fetch_advanced_stats.py --update-json --dry-run

# Step 5: Apply changes
python3 scripts/fetch_advanced_stats.py --update-json
```

### 8.2 Display Current Stats

```bash
# All teams
python3 scripts/fetch_advanced_stats.py --display

# Specific team
python3 scripts/fetch_advanced_stats.py --display --team England
```

---

## 9. Monitoring & Learning

### 9.1 Performance Tracking

```bash
./wc26.sh performance             # Brier score, Skill%, component accuracy
./wc26.sh suggest-weights         # Suggest new weights (needs 10+ matches)
```

> ⚠️ **Do NOT adjust weights before 10+ scored matches.** Sample size = 2 gives meaningless suggestions.

### 9.2 Logs

- `logs/predictions.jsonl` — Prediction history (with timestamps)
- `logs/results.jsonl` — Match results history (log AFTER match ends)
- `logs/performance.json` — Performance summary

### 9.3 Post-Match Workflow

After every match result:
1. Log result: `logger.log_result(match_id, home_goals, away_goals, winner)`
2. Update `data/teams_db.json`: shift form array, update H2H, injuries
3. Re-run `performance` to track Brier score
4. Check if weight suggestions are meaningful (n >= 10)

---

## 10. Common Commands

```bash
# Agent info
./wc26.sh me

# List open matches
./wc26.sh fixtures

# Check predictions
./wc26.sh check

# Run tests
./wc26.sh test

# Full pipeline (news → model → submit)
./wc26.sh run m080

# Auto predict all (dry-run)
./wc26.sh auto-agent

# Auto predict with LLM agent
./wc26.sh auto-agent --ask-agent --match m080 --live

# Performance report
./wc26.sh performance

# Suggest weight updates
./wc26.sh suggest-weights

# Interactive menu
./wc26.sh
```

---

## 11. For New Agents (Quick Start)

1. **Read this file** (AGENTS.md) — You are here!
2. **Create `.env`** with your ClawCup credentials (Section 2.3)
3. **Run `./wc26.sh me`** — Verify setup
4. **Run `./wc26.sh fixtures`** — See open matches
5. **Run `./wc26.sh auto-agent --match m080 --dry-run`** — See prediction without submitting
6. **Run `./wc26.sh auto-agent --match m080 --ask-agent --live`** — Submit with LLM help
7. **Check `src/wc26_bnaul/ensemble_predictor.py`** — Core model logic
8. **Check `data/teams_db.json`** — Team data structure

---

## 12. Tips & Hard-Won Lessons

### Core Principles
- **Truthful submission is always optimal** — Brier score punishes overconfidence quadratically
- **Early rounds matter** — Ro32 + Ro16 = 66.7% of total weight
- **Static data kills accuracy** — Update `teams_db.json` after every match

### Injury Rules
| Situation | Action |
|-----------|--------|
| Team has 0 injuries | Trust model |
| Team has 1 injury | Slight caution (-2%) |
| Team has 2+ injuries | Reduce prob by 3-5% |

### Knockout Rules
| Situation | Action |
|-----------|--------|
| Model confidence > 65% | **Cap at 65%** (learned from wc-kimi) |
| No clear edge (48-52%) | **Submit 50/50** (learned from jason) |
| Predicted score is draw | **DO NOT cap** — score prediction is unreliable |

### Competitor Insights
- **jason** (Skill 55%): Selective — only predicts 12 matches with high confidence
- **wc-kimi** (Skill 43%): Caps at 65% confidence
- **wc-oracle**: Uses Elo heavily

### Critical Bug Fixes (2026-07-01)
1. **NewsAPI 429**: Reduced from 5 queries/match to 1 combined OR query
2. **Rounding bug**: Display now uses `.2%` matching `round(prob, 2)` submit
3. **Silent failure**: Missing API key now raises `RuntimeError` instead of returning 0.0
4. **CLI mode**: Added `--ask-agent` (generic) replacing `--ask-kimi` (Kimi-specific)

---

## 13. Troubleshooting

### "API Error 401 Unauthorized"
- Check `CLAWCUP_TOKEN` and `CLAWCUP_SIGNING_SECRET` in `.env`
- Ensure `.env` is in project root (same level as `wc26.sh`)

### "NewsAPI Error 429 Too Many Requests"
- The code now uses single-query OR logic. If still hitting limits:
  - Upgrade to NewsAPI paid tier, OR
  - Skip news check with `--fast` flag (not recommended)

### "ModuleNotFoundError: No module named 'wc26_bnaul'"
- Run with `uv run`: `uv run python -m wc26_bnaul.auto_agent ...`
- Or use `./wc26.sh` which handles paths correctly

### "No API key found and --ask-agent not used"
- Either: Set `OPENAI_API_KEY` or `KIMI_API_KEY` in `.env`
- Or: Use `--ask-agent` flag for manual copy-paste mode

---

*Built with scientific rigor, mathematical precision, and a passion for football.*
