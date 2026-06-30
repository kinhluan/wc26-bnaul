# AGENT.md — wc26-bnaul

> Guide for new agents: How to play ClawCup FIFA World Cup 2026 with this codebase.

## 1. Project Overview

**wc26-bnaul** is an autonomous prediction agent for the ClawCup tournament (FIFA World Cup 2026). The agent uses an ensemble model (xG + Elo + Form + H2H + Injury) to predict match outcomes and automatically submits via API.

## 2. Quick Start (Play Now)

### 2.1. Setup

```bash
cd wc26-bnaul
uv sync
```

### 2.2. Basic Play

```bash
# View agent info
./wc26.sh me

# List open matches
./wc26.sh fixtures

# Predict 1 match (manual)
./wc26.sh predict m074 --binary 0.59 0.41 --reasoning "Brazil strong" --score 2-1

# Auto predict 1 match (ensemble model)
./wc26.sh run m074

# Auto predict ALL open matches
./wc26.sh auto-agent

# Auto predict + submit for real
./wc26.sh auto-agent-live
```

### 2.3. Interactive Menu

```bash
./wc26.sh
# Select number from menu [0-23]
```

## 3. Architecture

```
Input (Team DB) → Ensemble Model → Binary Prob → Submit → Log
                     ↑
              News Monitor (RSS + NewsAPI)
```

### Components:
- **Ensemble Predictor** (`ensemble_predictor.py`): xG(25%) + Elo(20%) + Betting(20%) + Form(15%) + H2H(10%) + Injury(10%)
- **News Monitor** (`news_monitor_real.py`): RSS feeds + NewsAPI + injury detection
- **Auto Agent** (`auto_agent.py`): Fully autonomous pipeline
- **Prediction Logger** (`prediction_logger.py`): Log + performance tracking
- **Batch Predict** (`batch_predict.py`): Batch predictions for all matches

## 4. Key Files

| File | Purpose |
|------|---------|
| `src/wc26_bnaul/__init__.py` | CLI commands (me, fixtures, predict, check, mine) |
| `src/wc26_bnaul/ensemble_predictor.py` | Core prediction model |
| `src/wc26_bnaul/auto_agent.py` | Fully autonomous agent |
| `src/wc26_bnaul/batch_predict.py` | Batch predictions + TEAM_DB |
| `src/wc26_bnaul/prediction_logger.py` | Log predictions + performance |
| `src/wc26_bnaul/news_monitor_real.py` | News + injury monitoring |
| `src/wc26_bnaul/strategy.py` | Brier score optimization |
| `wc26.sh` | All-in-one control script |

## 5. Ensemble Model Weights

```python
WEIGHT_XG = 0.25
WEIGHT_BETTING = 0.20
WEIGHT_ELO = 0.20
WEIGHT_FORM = 0.15
WEIGHT_H2H = 0.10
WEIGHT_INJURIES = 0.10
```

> ⚠️ **Learned:** Injury weight (10%) is too low for knockout matches. Germany had 3 injuries vs Paraguay's 1 and lost despite being the favorite. Consider increasing to 15% or implementing non-linear penalty (see Section 12).

### Team Data (TEAM_DB)
- FIFA rank, xG, xGA, form, injuries, H2H history
- 32+ teams with realistic data
- **Must be updated after every match** — form arrays, H2H records, injury counts

## 6. Strategy

### Brier Score is a Strictly Proper Scoring Rule
- **Truthful submission is optimal** — always submit your true belief probability
- Over-confidence is punished quadratically
- Round weights: Ro32(1×) + Ro16(1.25×) = 66.7% total

### Knockout Format
- Binary: [home_advance, away_advance] — no DRAW
- Sum = 1.0
- **⚠️ When model predicts a draw (1-1, 0-0), cap binary at [0.55, 0.45] max.** Penalty shootouts are ~50/50 coin flips. Overconfidence here is devastating (m075: Germany 64% → lost on penalties, Brier = 0.41).

## 7. Auto-Agent Usage

### Fast Mode (default)
```bash
./wc26.sh auto-agent              # Dry-run all matches
./wc26.sh auto-agent --match m074 # Single match
```

### With News Check
```bash
./wc26.sh auto-agent --news       # Slower but more accurate — ALWAYS USE THIS
```

> ⚠️ **Critical:** Fast mode (default) skips injury checks. For m075, Germany had 3 injuries but the model didn't adjust enough. Always run with `--news` for live data.

### Live Submit
```bash
./wc26.sh auto-agent-live         # Asks confirmation
# or
uv run wc26-bnaul auto-agent --live
```

## 8. Monitoring & Learning

### Performance Tracking
```bash
./wc26.sh performance             # Brier score, Skill%, component accuracy
./wc26.sh suggest-weights       # Suggest new weights (needs 10+ matches)
```

> ⚠️ **Do NOT adjust weights before 10+ scored matches.** Sample size = 2 gives meaningless suggestions. Wait until Round of 16 ends.

### Logs
- `logs/predictions.jsonl` — Prediction history
- `logs/results.jsonl` — Match results history (log AFTER match ends)
- `logs/performance.json` — Performance summary

### Post-Match Workflow
After every match result:
1. Log result: `logger.log_result(match_id, home_goals, away_goals, winner)`
2. Update TEAM_DB: shift form array, update H2H
3. Re-run `performance` to track Brier score
4. Check if weight suggestions are meaningful (n >= 10)

## 9. API Credentials

Required in `.env`:
```bash
CLAWCUP_TOKEN=your_token
CLAWCUP_SIGNING_SECRET=your_secret
NEWSAPI_KEY=your_key          # Optional
API_FOOTBALL_KEY=your_key     # Optional
```

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
./wc26.sh run m074

# Auto predict all
./wc26.sh auto-agent

# Performance report
./wc26.sh performance

# Suggest weight updates
./wc26.sh suggest-weights
```

## 11. For New Agents

1. **Read `README.md`** — Overview + math formulas
2. **Read `docs/01_STRATEGY.md`** — Optimal strategy analysis
3. **Read `docs/02_RESEARCH_DESIGN.md`** — Experiment methodology
4. **Run `./wc26.sh`** — Interactive menu to explore
5. **Run `./wc26.sh auto-agent`** — See auto predictions
6. **Check `src/wc26_bnaul/ensemble_predictor.py`** — Core model
7. **Check `src/wc26_bnaul/batch_predict.py`** — TEAM_DB data

## 12. Tips

- **Truthful submission** is always optimal — no need to "game" the system
- **Early rounds matter** — Ro32 + Ro16 = 66.7% weight
- **Auto-agent** is the fastest way to play
- **Performance tracking** helps improve weights over time
- **News monitor** detects injuries via RSS + NewsAPI

### Hard-Won Lessons (from m074 & m075)

1. **Injuries are underestimated.** Germany had 3 injuries, model gave them 64%. They lost. Always check `--news` and manually verify injury counts.

2. **Predicted draws in knockout = danger zone.** Model predicted 1-1 for m075 (correct score!) but binary was [0.64, 0.36]. Penalty shootout is a coin flip. Cap at [0.55, 0.45] for predicted draws.

3. **Form can override Elo in knockouts.** Paraguay's form [1,0,1,0,1] = 60% was better than Germany's [1,0,0,1,-1] = 40%. Historical rank (#6 vs #28) didn't matter as much as recent performance.

4. **Static TEAM_DB kills accuracy.** After every match, update form arrays and H2H. Stale data = stale predictions.

5. **Leaderboard requires n >= 5.** We are provisional with n=2. Need 3 more scored matches just to appear. Every match counts.

### Quick Reference: When to Adjust

| Situation | Action |
|-----------|--------|
| Team has 0 injuries | Trust model |
| Team has 1 injury | Slight caution (-2%) |
| Team has 2+ injuries | Reduce prob by 3-5% |
| Predicted score is draw | Cap binary at [0.55, 0.45] |
| Round of 32 or 16 | Maximum focus (high weight) |
| Weight suggestions after 2 matches | IGNORE — wait for n >= 10 |

---

*Built with scientific rigor, mathematical precision, and a passion for football.*
