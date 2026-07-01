# 🏆 wc26-bnaul — ClawCup FIFA World Cup Prediction Agent

> **Skill scope:** Project-specific (wc26-bnaul)
> **Last updated:** 2026-07-01
> **Author:** @kinhluan

---

## 1. Strategic Rules (Hard Rules — Never Break)

- `Rule: Brier score is strictly proper → Always submit TRUE belief probability. (Over/under-confidence punished quadratically).`
- `Rule: Knockout predicted draw (1-1, 0-0) → Cap binary at [0.55, 0.45] max. (Penalties are ~50/50 coin flips).`
- `Rule: Team with 2+ injuries → Reduce home_prob by 3-5% before submit. (Injury weight 15% in current model).`
- `Rule: Early rounds (Ro32=1.0×, Ro16=1.25×) → Focus maximum effort. (These determine 66.7% of final score).`
- `Rule: Always run --news flag before submit. (Last-minute injuries/lineup changes are critical).`
- `Rule: If no clear edge (48-52% normal, 45-55% knockout) → Submit 50/50. (Learned from jason's 55% SKILL).`
- `Rule: Model confidence > 65% in knockout → Cap at 65%. (Overconfidence is devastating).`

---

## 2. Tactical Rules (Context-Dependent)

- `Rule: Static TEAM_DB → Auto-update form + H2H after every match result. (Stale data kills predictions).`
- `Rule: Provisional status (n < 5 scored matches) → Prioritize calibration over bold predictions. (Need to exit provisional ASAP).`
- `Rule: Weight suggestions need 10+ matches → Do NOT adjust weights before Round of 16 ends. (Avoid overfitting to noise).`
- `Rule: Overconfidence (prob > 0.70) → Double-check injury/news data. (High confidence = high Brier risk if wrong).`
- `Rule: Placeholder teams (W74, W75...) → Use default stats but monitor if real team is determined. (Update TEAM_DB immediately).`
- `Rule: Use --cli-mode for automated agents, --ask-agent for interactive copy-paste. (Different stdin handling).`

---

## 3. Operational Checklist (Before Every Submit)

```
□ Run ./wc26.sh auto-agent (with --news, not --fast)
□ Check cutoff_utc — submit BEFORE deadline
□ Verify injury counts for both teams
□ If predicted score is draw → cap binary at [0.55, 0.45]
□ If team has 2+ injuries → reduce favorite's prob by 3-5%
□ If no clear edge (48-52%) → submit 50/50
□ Check round weight — early rounds matter more
□ Log prediction to predictions.jsonl
□ After match ends → log result to results.jsonl
□ Update TEAM_DB form + H2H
□ Update data/advanced_stats.csv if xG/xGA changed
```

---

## 4. Key Metrics & Benchmarks

| Metric | Good | Great | Current (Ours) |
|--------|------|-------|----------------|
| Brier Score | < 0.20 | < 0.15 | ~0.22 (improving) |
| Skill % | > 20% | > 40% | 13.1% (backtest) |
| Accuracy | > 60% | > 70% | 61.3% (Elo component) |
| Calibration | 3+ | 4+ | ? |

**Target:** Reach Skill > 30% after 15 scored matches (top 3 territory).

---

## 5. Common Pitfalls (Learned from m074/m075/Backtest)

1. **m074 Brazil vs Japan (✅):** Brazil dominated every metric → model correct. Lesson: When favorite has zero injuries + superior form, trust the model.
2. **m075 Germany vs Paraguay (❌):** Germany had 3 injuries, Paraguay had better form → model overconfident at 64%. Lesson: Injuries and form can override historical Elo/xG in knockouts.
3. **Backtest 75 matches:** Elo is strongest component (61.3% accuracy), xG is noisy (58.7%). Lesson: Weight Elo higher (30%), xG lower (20%).

---

## 6. CLI Agent Integration (For Automated LLM Agents)

### 6.1 Pipe Mode (Fully Automated)

```bash
# Submit with pre-calculated adjustment
echo "ADJUSTMENT: -2.5" | ./wc26.sh auto-agent-cli m080 --live

# Full workflow: capture prompt → analyze → submit
./wc26.sh auto-agent-cli m080 --dry-run > /tmp/prompt.txt
# (Your agent reads /tmp/prompt.txt, calls LLM API, extracts adjustment)
echo "ADJUSTMENT: -1.5" | ./wc26.sh auto-agent-cli m080 --live
```

### 6.2 Expected Prompt Format

The agent prints JSON-structured context containing:
- Match ID, teams, base probability
- Full team data (xG, Elo, form, injuries, H2H, squad depth)
- Venue data, referee info, betting odds
- Instructions for the LLM

### 6.3 Expected Response Format

```
ADJUSTMENT: -2.5

Brief reasoning here (optional)...
```

Range: `-5.0` to `+5.0` (percentage points). Use `0.0` if no adjustment needed.

### 6.4 Command Reference

| Command | Purpose | For |
|---------|---------|-----|
| `auto-agent` | Dry-run all matches | Human review |
| `auto-agent-live` | Submit without LLM | Fast automation |
| `auto-agent-ask` | Interactive copy-paste | Any LLM (ChatGPT, Kimi, Claude) |
| `auto-agent-cli` | Pipe mode for scripts | External CLI agents |

---

## 7. Advanced Stats Management

```bash
# Export CSV template from teams_db.json
python3 scripts/fetch_advanced_stats.py --export-template

# Edit data/advanced_stats.csv with xG, xGA, possession, etc.
# Then validate and apply
python3 scripts/fetch_advanced_stats.py --validate
python3 scripts/fetch_advanced_stats.py --update-json --dry-run
python3 scripts/fetch_advanced_stats.py --update-json
```

---

## 8. Self-Improvement Loop (For Autonomous Agents)

```
1. Run predictions → Submit → Log to predictions.jsonl
2. Wait for match results
3. Log results → Calculate Brier score (./wc26.sh performance)
4. Compare predicted vs actual (component-level accuracy)
5. If n >= 10: suggest weight adjustments (./wc26.sh suggest-weights)
6. If n >= 20: consider model retraining
7. Update data/teams_db.json with new form, H2H, injuries
8. Update data/advanced_stats.csv if needed
9. Repeat
```

---

## 9. Quick Commands

```bash
# Check status
./wc26.sh me
./wc26.sh performance
./wc26.sh suggest-weights

# Predict with news check
./wc26.sh auto-agent --live

# Interactive with any LLM
./wc26.sh auto-agent-ask m080 --live

# Pipe mode for automated agents
echo "ADJUSTMENT: -2.5" | ./wc26.sh auto-agent-cli m080 --live

# Check fixtures
./wc26.sh fixtures --status open
./wc26.sh fixtures --status closed

# Update results (manual)
uv run python -c "from wc26_bnaul.prediction_logger import PredictionLogger; \
  logger = PredictionLogger(); logger.log_result('MATCH_ID', H, A, 'winner')"

# Display team stats
python3 scripts/fetch_advanced_stats.py --display --team England
```

---

## 10. Critical Bug Fixes (2026-07-01)

1. **NewsAPI 429**: Reduced from 5 queries/match to 1 combined OR query
2. **Rounding bug**: Display uses `.2%` matching `round(prob, 2)` submit
3. **Silent failure**: Missing API key raises `RuntimeError` instead of returning 0.0
4. **CLI mode**: `--ask-agent` (generic) replaces `--ask-kimi` (Kimi-specific)
5. **Unicode arrows**: Replaced `→` with `->` in Python source to prevent SyntaxError

---

## 11. Related Issues

- **#1** — Match Analysis: m074 & m075 breakdown (why 1 correct, 1 wrong)
- **#2** — Ranking Improvement Plan: From -16% to Top 3
- **#4** — Backtest Analysis: 75 matches, Skill 8.1% → 13.1%
- **#5** — Experiment Evaluation: Academic rigor assessment (2.9/5)

---

*This skill is a living document. Update after every round of matches.*
